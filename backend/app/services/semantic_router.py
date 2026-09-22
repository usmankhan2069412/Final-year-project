import time
import os
import json
import hashlib
import threading
from pathlib import Path
import numpy as np
from typing import Optional, Dict, List, Any, Tuple
from app.services.embedding import embedding_service
from app.core.config import resolve_openrouter_key
from app.models.conversation import MessageRole
import logging

logger = logging.getLogger(__name__)

# --- Constants ---
MEMORY_THRESHOLD = 6        # Don't summarize until this many messages exist
MEMORY_REFRESH_INTERVAL = 4 # Re-summarize every N new turns after threshold

class SemanticRouter:
    """
    A multi-tier intent router that classifies user messages.

    Tier 1: Fast keyword short-circuit (AGENT_HANDOFF + history transforms)
    Tier 2: LLM-based classification using persona + conversation context
    Tier 3: Embedding cosine similarity fallback (when LLM unavailable)
    """
    ROUTES = {
        "AGENT_HANDOFF": [
            "talk to human",
            "speak with an agent",
            "connect to a person",
            "i need human support",
            "human representative",
            "talk to support team",
            "transfer to human",
            "mujhe insan se baat karni hai",
            "agent se connect karo",
            "customer care se baat karni hai",
            "human se baat karao",
            "help desk",
            "i want to talk to an admin",
            "can i speak to a real person",
            "representative please"
        ],
        "FRUSTRATION": [
            "this is useless",
            "you are not helping",
            "bakwas",
            "fazool",
            "you don't understand",
            "this bot is stupid",
            "i am angry",
            "terrible service",
            "stop replying like a bot",
            "nonsense"
        ],
        "CONVERSATIONAL": [
            "hi",
            "hello",
            "hey",
            "good morning",
            "good evening",
            "how are you",
            "thanks",
            "thank you",
            "bye",
            "goodbye",
            "assalam o alaikum",
            "salam",
            "kya haal hai",
            "shukriya",
            "allah hafiz",
            "ok",
            "okay"
        ]
    }

    _encoded_routes: Dict[str, np.ndarray] = {}
    _initialized = False
    _init_lock = threading.Lock()

    _typesafe_classifier = None
    _typesafe_lock = threading.Lock()

    EXACT_GREETINGS = {
        "hi", "hello", "hey", "salam", "assalam o alaikum", "assalam-o-alaikum",
        "aoa", "good morning", "good evening", "good afternoon", "kya haal hai",
        "kya hal hai", "kaise ho", "kaise hain", "bye", "goodbye", "allah hafiz",
        "shukriya", "thanks", "thank you", "ok", "okay"
    }

    GREETING_PREFIXES = (
        "hi ", "hello ", "salam", "assalam", "hey ", "shukriya", "thanks", "thank you"
    )

    HISTORY_TRANSFORM_CONTEXT_MARKERS = {
        "it", "this", "that", "them", "these", "those", "above", "previous", "last",
        "answer", "response", "reply", "message", "content", "text",
        "isay", "ise", "isko", "usko", "inko", "inhe", "upar", "pehle", "pichla",
        "pichlay", "jawab", "ans", "baat", "msg",
    }

    HISTORY_TRANSFORM_VERBS = {
        "summarize", "summarise", "summary", "shorten", "rewrite", "rephrase",
        "translate", "simplify", "explain", "convert",
    }

    HISTORY_TRANSFORM_PHRASES = [
        "make it shorter",
        "make this shorter",
        "make them shorter",
        "make it concise",
        "make this concise",
        "bullet points",
        "bullet point",
        "key points",
        "roman urdu",
        "urdu mein",
        "urdu me",
        "roman urdu mein",
        "roman urdu me",
        "dobara likho",
        "short kar",
        "short karo",
        "mukhtasar",
        "khulasa",
        "tarjuma",
        "translate them",
        "translate this",
        "translate it",
        "summarize above",
        "summarise above",
        "rewrite above",
    ]

    @classmethod
    def _get_routes_hash(cls) -> str:
        from app.core.config import settings
        # Generate a stable hash incorporating the embedding model, dimension, and routes
        routes_str = f"{settings.EMBEDDING_MODEL}:{settings.EMBEDDING_DIM}:" + json.dumps(cls.ROUTES, sort_keys=True)
        return hashlib.sha256(routes_str.encode("utf-8")).hexdigest()

    @classmethod
    def _matches_history_transform(cls, message: str) -> bool:
        msg_lower = message.lower().strip()
        if not msg_lower:
            return False

        words = msg_lower.split()
        word_set = set(words)
        has_context_marker = bool(word_set & cls.HISTORY_TRANSFORM_CONTEXT_MARKERS)

        if any(phrase in msg_lower for phrase in cls.HISTORY_TRANSFORM_PHRASES):
            if "roman urdu" in msg_lower and not has_context_marker and len(words) > 5:
                return False
            return True

        has_transform_verb = any(word in cls.HISTORY_TRANSFORM_VERBS for word in words)
        if not has_transform_verb:
            return False

        if has_context_marker:
            return True

        # Short imperative messages usually refer to the previous answer:
        # "summarize", "rewrite in bullets", "short kar do".
        return len(words) <= 4 and not any(ch in message for ch in ['"', "'", ":"])

    @classmethod
    def _initialize(cls):
        if cls._initialized:
            return

        with cls._init_lock:
            # Double-check inside lock
            if cls._initialized:
                return

            logger.info("Initializing Semantic Router...")
            try:
                from app.core.config import settings

                current_hash = cls._get_routes_hash()
                cache_path = Path("data/semantic_router_cache.json")

                loaded_from_cache = False
                if cache_path.exists():
                    try:
                        with open(cache_path, "r", encoding="utf-8") as f:
                            cache_data = json.load(f)
                        if cache_data.get("hash") == current_hash:
                            logger.info("Loading Semantic Router embeddings from local cache...")
                            for intent, list_of_vectors in cache_data.get("embeddings", {}).items():
                                cls._encoded_routes[intent] = np.array(list_of_vectors, dtype=np.float32)
                            loaded_from_cache = True
                            logger.info("Semantic Router embeddings loaded successfully from cache.")
                    except Exception as cache_err:
                        logger.warning(f"Failed to read semantic router cache: {cache_err}. Falling back to API.")

                if not loaded_from_cache:
                    logger.info("Semantic Router cache miss or invalid. Generating embeddings from API...")
                    cache_embeddings = {}
                    for intent, utterances in cls.ROUTES.items():
                        vectors = embedding_service.encode(utterances)
                        if vectors.size > 0:
                            # Normalize vectors for cosine similarity (dot product)
                            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
                            norms[norms == 0] = 1e-10
                            normalized_vectors = vectors / norms
                            cls._encoded_routes[intent] = normalized_vectors
                            cache_embeddings[intent] = normalized_vectors.tolist()

                    if cls._encoded_routes:
                        try:
                            cache_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(cache_path, "w", encoding="utf-8") as f:
                                json.dump({
                                    "hash": current_hash,
                                    "embeddings": cache_embeddings
                                }, f, indent=2)
                            logger.info(f"Saved Semantic Router embeddings cache to {cache_path}")
                        except Exception as write_err:
                            logger.warning(f"Failed to write semantic router cache: {write_err}")

                cls._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize Semantic Router: {e}")
                # Mark as initialized even on failure to prevent a thundering herd of
                # re-initialization attempts on every subsequent chat message.
                cls._initialized = True

    @classmethod
    def _get_typesafe_classifier(cls):
        """Get or initialize the TypeSafeClassifier singleton instance."""
        if cls._typesafe_classifier is None:
            with cls._typesafe_lock:
                if cls._typesafe_classifier is None:
                    from app.core.config import settings
                    api_key = getattr(settings, "TYPESAFE_API_KEY", "") or os.getenv("TYPESAFE_API_KEY", "")
                    if not api_key:
                        return None
                    try:
                        from langchain_typesafe import TypeSafeClassifier
                        timeout = getattr(settings, "TYPESAFE_TIMEOUT_SECS", 5.0)
                        cls._typesafe_classifier = TypeSafeClassifier(
                            api_key=api_key,
                            timeout=timeout,
                        )
                        logger.info("TypeSafeClassifier initialized successfully with Jev model.")
                    except Exception as e:
                        logger.warning(f"Failed to initialize TypeSafeClassifier: {e}")
                        return None
        return cls._typesafe_classifier

    @classmethod
    def _get_jev_questions(cls) -> dict:
        """Construct typed questions for Jev System One model with layered priority rules."""
        from langchain_typesafe import Choice, Noul

        instructions = (
            "Classify the user's latest message into exactly ONE intent using these PRIORITY RULES:\n"
            "1. EXPLICIT HUMAN REQUEST: If the user explicitly asks to speak with a human agent, representative, "
            "or person (e.g., 'mujhe insan se baat karni hai', 'talk to human'), ALWAYS classify as AGENT_HANDOFF, "
            "regardless of bot persona.\n"
            "2. COMPOUND MESSAGES: If a message begins with a greeting but contains an underlying request "
            "(e.g., 'Hi, refund policy kya hai?'), the substantive intent (RAG_LOOKUP or HISTORY_TRANSFORM) "
            "takes precedence over CONVERSATIONAL.\n"
            "3. PERSONA-SENSITIVE DISTRESS / COMPLAINTS: When user expresses sadness, distress, or mild dissatisfaction "
            "without explicitly demanding a human:\n"
            "   - If the bot persona is Technical Support or Escalation, route to AGENT_HANDOFF.\n"
            "   - If the bot persona is Sales or Friendly/Empathetic, route to CONVERSATIONAL.\n"
            "4. BOT HOSTILITY / ABUSE: If the user insults or expresses anger toward the bot itself "
            "(e.g., 'tum bakwas ho', 'stupid bot'), classify as FRUSTRATION."
        )

        return {
            "intent": Choice(
                instructions=instructions,
                criteria={
                    "CONVERSATIONAL": (
                        "Greetings, small talk, rapport building, thanks, social chitchat, or emotional distress "
                        "when interacting with a sales/friendly persona. Does NOT apply if user asks for factual info, "
                        "history transformation, or a human agent."
                    ),
                    "RAG_LOOKUP": (
                        "Questions or requests seeking factual information from the knowledge base — policies, products, "
                        "fees, admission, how-to, troubleshooting details. Takes precedence over greetings in mixed queries."
                    ),
                    "HISTORY_TRANSFORM": (
                        "Requests to transform prior conversation text or previous assistant answers — summarize, translate, "
                        "shorten, rewrite in bullets, explain again, convert to Roman Urdu. Takes precedence over greetings in mixed queries."
                    ),
                    "AGENT_HANDOFF": (
                        "User explicitly asks for a human/agent/representative, OR expresses distress/unresolved issue when "
                        "interacting with an Escalation or Support persona."
                    ),
                    "FRUSTRATION": (
                        "User expresses strong anger, insults, sarcasm, or hostility directed at the bot itself (e.g., 'tum bakwas ho', 'useless bot')."
                    ),
                },
            ),
            "is_frustrated": Noul(
                instructions="Does the user express strong anger, insults, or hostility toward the bot itself?"
            ),
        }

    @classmethod
    async def classify_with_details(
        cls,
        message: str,
        persona: Any = None,
        traits: Optional[List[str]] = None,
        history: Optional[List[Any]] = None,
        conversation_memory: Optional[dict] = None,
        api_key: Optional[str] = None,
        threshold: float = 0.65,
    ) -> Tuple[str, float, Dict[str, float], str]:
        """
        Classifies intent with full metadata (intent, confidence, probabilities, method).
        1. Exact greeting gate (<1ms)
        2. Jev Model (TypeSafeClassifier) with persona + context + Noul frustration
        3. Graceful fallback on timeout/error
        """
        from app.core.metrics import intent_classification_method, intent_classification_latency
        from app.core.config import settings

        t0 = time.monotonic()
        msg_lower = message.lower().strip()
        normalized_msg = msg_lower.strip(" .!?,")

        # 1. Exact Greetings & Short Prefix Gate (prevents latency regression for simple small talk)
        if (
            normalized_msg in cls.EXACT_GREETINGS
            or (any(msg_lower.startswith(p) for p in cls.GREETING_PREFIXES) and len(message.split()) <= 4)
        ):
            latency = time.monotonic() - t0
            intent_classification_latency.observe(latency)
            intent_classification_method.labels(method="keyword_exact").inc()
            logger.info("intent_classified", extra={"intent": "CONVERSATIONAL", "method": "keyword_exact", "latency_ms": round(latency * 1000, 2)})
            return "CONVERSATIONAL", 1.0, {"CONVERSATIONAL": 1.0}, "keyword_exact"

        # 2. TypeSafe Jev Model
        classifier = cls._get_typesafe_classifier()
        if classifier:
            try:
                context = cls._build_classifier_context(history or [], conversation_memory)
                persona_name = getattr(persona, "name", "Assistant") or "Assistant"
                persona_desc = getattr(persona, "description", "") or ""
                traits_str = ", ".join(traits) if traits else "General purpose"

                jev_state = {
                    "message": message,
                    "persona_name": persona_name,
                    "persona_role": persona_desc,
                    "traits": traits_str,
                    "conversation_context": context,
                }

                response = await classifier.ainvoke({
                    "state": jev_state,
                    "questions": cls._get_jev_questions(),
                })

                intent_answer = response.choices.get("intent")
                is_frustrated_answer = response.nouls.get("is_frustrated")

                frustrated_prob = is_frustrated_answer.noul if is_frustrated_answer else 0.0
                confidence = intent_answer.confidence if intent_answer else 0.0
                raw_intent = intent_answer.choice if intent_answer else "RAG_LOOKUP"
                probabilities = intent_answer.probabilities if intent_answer else {}

                confidence_threshold = getattr(settings, "TYPESAFE_CONFIDENCE_THRESHOLD", 0.70)

                # If frustration detected via Noul or Choice
                if raw_intent == "FRUSTRATION":
                    final_intent = "FRUSTRATION"
                elif frustrated_prob >= 0.80:
                    final_intent = "FRUSTRATION"
                elif confidence < confidence_threshold:
                    final_intent = "RAG_LOOKUP"
                else:
                    final_intent = raw_intent

                latency = time.monotonic() - t0
                intent_classification_latency.observe(latency)
                intent_classification_method.labels(method="jev").inc()

                logger.info("jev_intent_classified", extra={
                    "intent": final_intent,
                    "raw_choice": raw_intent,
                    "confidence": confidence,
                    "probabilities": probabilities,
                    "frustration_prob": frustrated_prob,
                    "latency_ms": round(latency * 1000, 2),
                    "user_message": message[:100],
                })

                return final_intent, confidence, probabilities, "jev"

            except Exception as e:
                latency = time.monotonic() - t0
                intent_classification_latency.observe(latency)
                intent_classification_method.labels(method="error_fallback").inc()
                logger.warning(f"TypeSafe Jev classification failed or timed out: {e}. Falling back to RAG_LOOKUP.")
                return "RAG_LOOKUP", 0.0, {}, "error_fallback"

        # 3. Fallback if TypeSafe API Key is not configured: use LLM / embedding
        if api_key:
            llm_result = await cls._classify_with_llm(
                message=message,
                persona=persona,
                traits=traits or [],
                history=history or [],
                conversation_memory=conversation_memory,
                api_key=api_key,
            )
            if llm_result:
                latency = time.monotonic() - t0
                intent_classification_latency.observe(latency)
                intent_classification_method.labels(method="llm").inc()
                return llm_result, 0.85, {llm_result: 0.85}, "llm"

        emb_intent, emb_score = await cls._classify_with_embeddings(message, threshold)
        if emb_score >= threshold and emb_intent:
            latency = time.monotonic() - t0
            intent_classification_latency.observe(latency)
            intent_classification_method.labels(method="embedding_fallback").inc()
            return emb_intent, emb_score, {emb_intent: emb_score}, "embedding_fallback"

        return "RAG_LOOKUP", 0.0, {}, "default"

    @classmethod
    async def classify(
        cls,
        message: str,
        persona: Any = None,
        traits: Optional[List[str]] = None,
        history: Optional[List[Any]] = None,
        conversation_memory: Optional[dict] = None,
        api_key: Optional[str] = None,
        threshold: float = 0.65,
    ) -> Optional[str]:
        """
        Public classification method returning intent label.
        Maintains backward compatibility with all existing pipeline callers.
        """
        intent, _, _, _ = await cls.classify_with_details(
            message=message,
            persona=persona,
            traits=traits,
            history=history,
            conversation_memory=conversation_memory,
            api_key=api_key,
            threshold=threshold,
        )
        return intent

    @classmethod
    async def _classify_with_llm(
        cls,
        message: str,
        persona: Any,
        traits: List[str],
        history: List[Any],
        conversation_memory: Optional[dict],
        api_key: str,
    ) -> Optional[str]:
        """Use gpt-4o-mini to classify intent with persona and conversation context."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage

            effective_key, base_url = resolve_openrouter_key(api_key)
            if not effective_key:
                return None

            llm_kwargs = {
                "api_key": effective_key,
                "model": "openai/gpt-4o-mini" if base_url else "gpt-4o-mini",
                "temperature": 0.0,
                "max_tokens": 10,
            }
            if base_url:
                llm_kwargs["base_url"] = base_url

            llm = ChatOpenAI(**llm_kwargs)

            # Build conversation context (raw for short convos, summary+recent for long)
            context = cls._build_classifier_context(history, conversation_memory)

            # Build persona info
            persona_name = getattr(persona, "name", "Assistant") or "Assistant"
            persona_desc = getattr(persona, "description", "") or ""
            traits_str = ", ".join(traits) if traits else "General purpose"

            sys_prompt = (
                "You are an intent classifier for a chatbot.\n\n"
                f"PERSONA: {persona_name}\n"
                f"ROLE: {persona_desc}\n"
                f"TRAITS: {traits_str}\n"
                f"CONVERSATION CONTEXT: {context}\n\n"
                "Classify the user's latest message into exactly ONE intent:\n\n"
                "- CONVERSATIONAL: Greetings, small talk, rapport building, thanks, compliments, "
                "farewells, acknowledgments, social chitchat, emotional expressions, or any "
                "message where the user is relating socially rather than seeking factual "
                "information. Consider the persona's role â€” some personas should handle "
                "emotional messages conversationally rather than escalating.\n"
                "- RAG_LOOKUP: Questions or requests that need factual information from the "
                "knowledge base â€” topics, policies, products, services, how-to, explanations.\n"
                "- HISTORY_TRANSFORM: The user wants to transform prior chat content, especially "
                "the previous assistant answer. Examples: translate this/them, make it shorter, "
                "summarize above, rewrite this, make bullet points, explain again, or convert to "
                "Roman Urdu. Do not classify these as RAG_LOOKUP unless the user asks for new "
                "facts from the knowledge base.\n"
                "- AGENT_HANDOFF: User explicitly and directly asks to speak with a human agent, "
                "representative, or real person.\n"
                "- FRUSTRATION: User expresses strong anger, dissatisfaction, or hostility "
                "toward the bot itself (not general life frustration).\n\n"
                "Reply with ONLY the intent label. No explanation."
            )

            result_msg = await llm.ainvoke([
                SystemMessage(content=sys_prompt),
                HumanMessage(content="User message: " + message + "\n\nIntent:")
            ])
            result = result_msg.content.strip().upper()

            # Validate the LLM returned a known intent
            valid_intents = {"CONVERSATIONAL", "RAG_LOOKUP", "HISTORY_TRANSFORM", "AGENT_HANDOFF", "FRUSTRATION"}
            if result in valid_intents:
                logger.info(f"LLM intent classified: {result} (message: {message[:50]})")
                return result

            logger.warning(f"LLM intent invalid response: '{result}' (message: {message[:50]})")
            return None

        except Exception as e:
            logger.warning(f"LLM intent classification failed, falling back to embeddings: {e}")
            return None

    @staticmethod
    def _format_history_line(m: Any) -> str:
        if hasattr(m, "role"):
            role_label = "USER" if m.role == MessageRole.USER else "BOT"
        elif getattr(m, "type", "") == "human" or type(m).__name__ == "HumanMessage":
            role_label = "USER"
        elif isinstance(m, dict):
            role_label = "USER" if m.get("role") in ("user", "human") else "BOT"
        else:
            role_label = "BOT"
        content = getattr(m, "content", "") or (m.get("content", "") if isinstance(m, dict) else str(m))
        return f"{role_label}: {content}"

    @classmethod
    def _build_classifier_context(cls, history: List[Any], memory: Optional[dict]) -> str:
        from app.services.semantic_router import MEMORY_THRESHOLD

        if not history:
            return "No previous conversation."

        if len(history) <= MEMORY_THRESHOLD:
            # Short conversation — raw history is small enough
            lines = [cls._format_history_line(m) for m in history[-6:]]
            return "Recent messages:\n" + "\n".join(lines)

        # Long conversation — use summary + recent raw messages
        if memory and memory.get("summary"):
            summary = memory.get("summary", "")
            mood = memory.get("user_mood", "unknown")
            phase = memory.get("phase", "unknown")

            lines = [cls._format_history_line(m) for m in history[-4:]]

            return (
                f"Summary: {summary}\n"
                f"User mood: {mood}, Phase: {phase}\n"
                f"Recent:\n" + "\n".join(lines)
            )

        # Long conversation but no summary yet — use last 6 raw
        lines = [cls._format_history_line(m) for m in history[-6:]]
        return "Recent messages:\n" + "\n".join(lines)

    @classmethod
    async def _classify_with_embeddings(cls, message: str, threshold: float = 0.82) -> Tuple[Optional[str], float]:
        """Original embedding-based classification â€” used as fallback when LLM is unavailable."""
        if not cls._initialized:
            cls._initialize()

        if not cls._initialized or not cls._encoded_routes:
            return None, 0.0

        try:
            # Encode user message symmetrically as raw text (matching stored route prototype embeddings)
            query_vectors = await embedding_service.aencode([message], is_query=False)
            if query_vectors.size == 0:
                return None, 0.0
            query_vector = query_vectors[0]
            query_norm = np.linalg.norm(query_vector)
            if query_norm == 0:
                return None, 0.0

            normalized_query = query_vector / query_norm

            best_intent = None
            best_score = -1.0

            for intent, route_vectors in cls._encoded_routes.items():
                # Compute cosine similarities
                similarities = np.dot(route_vectors, normalized_query)
                max_sim = np.max(similarities)

                if max_sim > best_score:
                    best_score = max_sim
                    best_intent = intent

            if best_score >= threshold:
                logger.info(f"Semantic Router matched '{best_intent}' with score {best_score:.3f}")
                return best_intent, float(best_score)
            else:
                logger.info(f"Semantic Router fallback. Highest score was {best_score:.3f} for '{best_intent}'")
                return best_intent, float(best_score)

        except Exception as e:
            logger.error(f"Semantic classification error: {e}")
            return None, 0.0
