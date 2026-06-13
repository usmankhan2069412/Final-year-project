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
        # Generate a stable hash of the static routes dictionary
        routes_str = json.dumps(cls.ROUTES, sort_keys=True)
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
    def classify(
        cls,
        message: str,
        persona: Any = None,
        traits: Optional[List[str]] = None,
        history: Optional[List[Any]] = None,
        conversation_memory: Optional[dict] = None,
        api_key: Optional[str] = None,
        threshold: float = 0.82,
    ) -> Optional[str]:
        """
        Multi-tier intent classification:
        1. Keyword short-circuit (AGENT_HANDOFF only â€” free, instant)
        2. LLM classification (persona-aware, context-aware)
        3. Embedding fallback (when LLM unavailable)
        """
        from app.core.metrics import intent_classification_method, intent_classification_latency

        t0 = time.monotonic()
        msg_lower = message.lower().strip()

        # --- Tier 1: Fast keyword short-circuit for Agent Handoff / History Transform ---
        handoff_keywords = [
            "talk to human", "speak with an agent", "connect to a person",
            "human support", "representative", "agent se connect karo",
            "human se baat karao", "mujhe insan se baat karni hai",
            "customer care se baat karni hai"
        ]
        if any(kw in msg_lower for kw in handoff_keywords):
            latency = time.monotonic() - t0
            intent_classification_latency.observe(latency)
            intent_classification_method.labels(method="keyword_shortcircuit").inc()
            return "AGENT_HANDOFF"

        normalized_msg = msg_lower.strip(" .!?")
        if normalized_msg in cls.ROUTES.get("CONVERSATIONAL", []):
            latency = time.monotonic() - t0
            intent_classification_latency.observe(latency)
            intent_classification_method.labels(method="keyword_shortcircuit").inc()
            return "CONVERSATIONAL"

        if cls._matches_history_transform(message):
            latency = time.monotonic() - t0
            intent_classification_latency.observe(latency)
            intent_classification_method.labels(method="keyword_shortcircuit").inc()
            return "HISTORY_TRANSFORM"

        # --- Tier 2: Embedding Fast-Path (First LLM Avoidance) ---
        # Prioritize embedding search for high-confidence intents to save LLM costs.
        emb_intent, emb_score = cls._classify_with_embeddings(message, 0.0) # get best regardless of threshold
        if emb_score >= 0.85 and emb_intent:
            latency = time.monotonic() - t0
            intent_classification_latency.observe(latency)
            intent_classification_method.labels(method="embedding_fastpath").inc()
            return emb_intent

        # --- Tier 3: LLM-based classification (persona + context aware) ---
        if persona and api_key:
            llm_result = cls._classify_with_llm(
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
                return llm_result

        # --- Tier 4: Embedding fallback (existing behavior) ---
        if emb_score >= threshold and emb_intent:
            latency = time.monotonic() - t0
            intent_classification_latency.observe(latency)
            intent_classification_method.labels(method="embedding_fallback").inc()
            return emb_intent

        return None

    @classmethod
    def _classify_with_llm(
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

            result = llm.invoke([
                SystemMessage(content=sys_prompt),
                HumanMessage(content="User message: " + message + "\n\nIntent:")
            ]).content.strip().upper()

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

    @classmethod
    def _build_classifier_context(cls, history: List[Any], memory: Optional[dict]) -> str:
        """
        Build conversation context for the intent classifier.
        Short conversations (â‰¤6 msgs): use raw history directly (zero LLM cost).
        Long conversations (>6 msgs): use structured summary + last 4 raw messages.
        """
        from app.models.conversation import MessageRole

        if not history:
            return "New conversation"

        if len(history) <= MEMORY_THRESHOLD:
            # Short conversation â€” raw history is small enough
            lines = []
            for m in history[-6:]:
                role_label = "USER" if m.role == MessageRole.USER else "BOT"
                lines.append(f"{role_label}: {m.content}")
            return "Recent messages:\n" + "\n".join(lines)

        # Long conversation â€” use summary + recent raw messages
        if memory and memory.get("summary"):
            summary = memory.get("summary", "")
            mood = memory.get("user_mood", "unknown")
            phase = memory.get("phase", "unknown")

            lines = []
            for m in history[-4:]:
                role_label = "USER" if m.role == MessageRole.USER else "BOT"
                lines.append(f"{role_label}: {m.content}")

            return (
                f"Summary: {summary}\n"
                f"User mood: {mood}, Phase: {phase}\n"
                f"Recent:\n" + "\n".join(lines)
            )

        # Long conversation but no summary yet â€” use last 6 raw
        lines = []
        for m in history[-6:]:
            role_label = "USER" if m.role == MessageRole.USER else "BOT"
            lines.append(f"{role_label}: {m.content}")
        return "Recent messages:\n" + "\n".join(lines)

    @classmethod
    def _classify_with_embeddings(cls, message: str, threshold: float = 0.82) -> Tuple[Optional[str], float]:
        """Original embedding-based classification â€” used as fallback when LLM is unavailable."""
        if not cls._initialized:
            cls._initialize()

        if not cls._initialized or not cls._encoded_routes:
            return None, 0.0

        try:
            # Encode user message
            query_vector = embedding_service.encode([message])[0]
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
