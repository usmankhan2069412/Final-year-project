import uuid
import logging
import re
import os
import json
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, TypedDict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.language import detect_message_language
from app.core.metrics import chat_requests_total, chat_latency_seconds, fallback_total
from app.db.base_repository import MessageRepository, ConversationRepository
from app.models.chatbot import Chatbot
from app.models.persona import Persona, PersonaTrait
from app.models.conversation import Conversation, Message as DBMessage, ConversationStatus, MessageRole
from app.models.ai_model import AIModelConfig
from app.services.bot import model_config_service
from app.services.vector_store import VectorStoreService

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

import structlog
logger = structlog.get_logger()

# --- LangGraph State Definition ---
class AgentState(TypedDict, total=False):
    user_message: str
    history: List[DBMessage]
    api_key: Optional[str]
    model_name: str
    persona: Persona
    traits: List[str]
    chatbot_id: str
    
    # Pipeline variables
    intent: Optional[str]
    rewritten_query: Optional[str]
    sources: List[Dict[str, Any]]
    context_text: str
    is_relevant: bool
    routing_rules: Dict[str, str]
    default_model: str
    
    # Conversation memory (lazy summarization)
    conversation_memory: Optional[dict]
    
    # Final Output
    response: str
    status: ConversationStatus
    callbacks: Optional[List[Any]]


from app.services.semantic_router import SemanticRouter

# --- Intent Heuristics Classifier (DEPRECATED) ---
# We keep this strictly for reference or completely remove it. It's been replaced by SemanticRouter.
# ------------------------------------------------

def _resolve_openrouter_key(api_key: str) -> tuple[Optional[str], Optional[str]]:
    """Resolve an API key that may be 'managed-by-openrouter' into (effective_key, base_url).
    Returns (None, None) if no key can be resolved."""
    if api_key != "managed-by-openrouter":
        return api_key, None
    effective = getattr(settings, "OPENROUTER_API_KEY", None) or os.getenv("OPENROUTER_API_KEY")
    if effective:
        return effective, "https://openrouter.ai/api/v1"
    effective = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
    return (effective, None) if effective else (None, None)

# --- Agent Graph Executor ---
class AgentGraphExecutor:
    """
    Pure graph executor operating on state dictionary variables.
    Decoupled entirely from database models/transactions.
    """
    _graph = None  # Compiled graph singleton — safe to share (stateless)

    @classmethod
    def _get_graph(cls):
        if cls._graph is None:
            cls._graph = cls.build_graph()
        return cls._graph
    @staticmethod
    def _get_llm(state: AgentState, temperature: float = 0.3) -> Optional[ChatOpenAI]:
        api_key = state.get("api_key")
        if not api_key:
            return None
            
        model = state.get("model_name", "openai/gpt-4o-mini")
        callbacks = state.get("callbacks")
        
        # If it's a managed OpenRouter key, use OpenRouter API
        if api_key == "managed-by-openrouter":
            real_key = getattr(settings, "OPENROUTER_API_KEY", None) or os.getenv("OPENROUTER_API_KEY")
            if not real_key:
                logger.warning("OPENROUTER_API_KEY not found in environment, falling back to OPENAI_API_KEY")
                api_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return None
            else:
                return ChatOpenAI(
                    api_key=real_key,
                    model=model,
                    temperature=temperature,
                    base_url="https://openrouter.ai/api/v1",
                    streaming=bool(callbacks),
                    callbacks=callbacks
                )
                
        # Standard fallback (e.g. native OpenAI)
        return ChatOpenAI(api_key=api_key, model=model, temperature=temperature, streaming=bool(callbacks), callbacks=callbacks)

    @staticmethod
    def _content_terms(text: str) -> set[str]:
        stop_words = {
            "the", "and", "for", "are", "you", "your", "with", "that", "this", "what", "when", "where",
            "how", "why", "can", "could", "would", "should", "about", "from", "into", "have", "has",
            "hai", "hain", "kya", "aur", "mein", "mujhe", "aap", "ap", "ke", "ki", "ka", "ko", "se",
        }
        return {
            word
            for word in re.findall(r"\w+", text.lower())
            if len(word) > 2 and word not in stop_words
        }

    @classmethod
    def _has_lexical_relevance(cls, query: str, context: str) -> bool:
        query_terms = cls._content_terms(query)
        if not query_terms:
            return bool(context.strip())

        context_terms = cls._content_terms(context)
        overlap = query_terms & context_terms
        if not overlap:
            return False

        overlap_ratio = len(overlap) / max(len(query_terms), 1)
        return len(overlap) >= 2 or overlap_ratio >= 0.35

    # --- Node Functions ---
    @staticmethod
    def route_intent(state: AgentState) -> AgentState:
        # Persona-aware, context-aware intent classification
        intent = SemanticRouter.classify(
            message=state["user_message"],
            persona=state.get("persona"),
            traits=state.get("traits"),
            history=state.get("history"),
            conversation_memory=state.get("conversation_memory"),
            api_key=state.get("api_key"),
        )
        chatbot_id = state.get("chatbot_id")
        
        final_intent = intent if intent else "RAG_LOOKUP"
        
        # Match intent to configured model, fallback to default OpenRouter model
        model_name = state.get("default_model", "openai/gpt-4o-mini")
        rules = state.get("routing_rules", {})
        
        if final_intent in rules:
            model_name = rules[final_intent]
        elif "General Inquiries" in rules:
            model_name = rules["General Inquiries"]

        logger.info("intent_routed", intent=final_intent, chatbot_id=chatbot_id, mapped_model=model_name)
        return {"intent": final_intent, "model_name": model_name}

    @staticmethod
    def agent_handoff_node(state: AgentState) -> AgentState:
        from app.core.messages import get_initial_handoff_message
        lang = state["persona"].language
        if lang == "multilingual":
            lang = detect_message_language(state["user_message"], state.get("history"))
            
        text = get_initial_handoff_message(lang)
            
        return {"response": text, "status": ConversationStatus.ESCALATED}

    @staticmethod
    def conversational_node(state: AgentState) -> AgentState:
        llm = AgentGraphExecutor._get_llm(state, temperature=0.7)
        greeting = getattr(state["persona"], "greeting", None) or "Hello! How can I help you today?"
        
        if llm:
            try:
                detected_lang = detect_message_language(state["user_message"], state.get("history"))
                lang_name = {
                    "urdu": "Urdu Script",
                    "roman_urdu": "Roman Urdu (Urdu written in English alphabets)",
                    "english": "English"
                }.get(detected_lang, "English")

                desc = getattr(state["persona"], "description", None) or ""
                desc_str = f"Description/Role: {desc}\n" if desc else ""
                
                # Build conversation context from memory for richer responses
                memory = state.get("conversation_memory")
                context_str = ""
                if memory and memory.get("summary"):
                    context_str = f"Conversation so far: {memory['summary']}\n"
                
                sys_msg = SystemMessage(content=(
                    f"You are {state['persona'].name or 'Aina Bot'}. "
                    f"Your traits are: {', '.join(state['traits'])}. "
                    f"{desc_str}"
                    f"{context_str}"
                    "IMPORTANT GUIDELINES:\n"
                    "1. Act strictly as a human representative. Never mention that you are an AI, a bot, or reading from a 'context' or 'database'.\n"
                    "2. Use natural, conversational language. Be polite and empathetic.\n"
                    f"3. Greet the user and chat politely. Your main greeting is: '{greeting}'.\n"
                    f"4. You MUST strictly speak and reply in: {lang_name}."
                ))
                messages = [sys_msg]
                for m in state["history"][-6:]:
                    role = HumanMessage if m.role == MessageRole.USER else AIMessage
                    messages.append(role(content=m.content))
                messages.append(HumanMessage(content=state["user_message"]))
                
                result = llm.invoke(messages).content.strip()
                return {"response": result}
            except Exception as e:
                logger.warning(f"LLM conversational generation failed: {e}")
                
        return {"response": greeting}

    @staticmethod
    def rewrite_node(state: AgentState) -> AgentState:
        llm = AgentGraphExecutor._get_llm(state)
        user_msg = state["user_message"]
        
        if not state["history"] or not llm:
            return {"rewritten_query": user_msg}
            
        try:
            history_str = ""
            for m in state["history"][-4:]:
                role_label = "USER" if m.role == MessageRole.USER else "BOT"
                history_str += f"{role_label}: {m.content}\n"
                
            sys_msg = SystemMessage(content=(
                "You are a search query rewriter. Given the chat history and the latest user message, rewrite the user message to be a standalone search query.\n"
                "CRITICAL RULES:\n"
                "1. If the user introduces a NEW topic, DO NOT mix it with the previous topic.\n"
                "2. If the user uses a pronoun ('it', 'this') and the history makes it 100% obvious, replace the pronoun. If it is ambiguous, leave it broad.\n"
                "3. If the latest message is already standalone, output it exactly as is.\n"
                "Do not answer the question; just output the rewritten query."
            ))
            h_msg = HumanMessage(content=f"History:\n{history_str}\nLatest user message: \"{user_msg}\"\nStandalone query:")
            
            rewritten = llm.invoke([sys_msg, h_msg]).content.strip()
            if rewritten.startswith('"') and rewritten.endswith('"'):
                rewritten = rewritten[1:-1]
            return {"rewritten_query": rewritten}
        except Exception as e:
            logger.warning(f"Query rewrite failed: {e}")
            return {"rewritten_query": user_msg}

    @staticmethod
    def retrieve_node(state: AgentState) -> AgentState:
        rewritten = state.get("rewritten_query")
        original = state["user_message"]
        chatbot_id = state["chatbot_id"]
        
        # If no rewrite or exactly the same, do a single search
        if not rewritten or rewritten.lower().strip() == original.lower().strip():
            sources_list = VectorStoreService.search_hybrid(chatbot_id, original, top_k=4)
        else:
            # Multi-Query Retrieval: search both and merge
            sources_rewritten = VectorStoreService.search_hybrid(chatbot_id, rewritten, top_k=3)
            sources_original = VectorStoreService.search_hybrid(chatbot_id, original, top_k=3)
            
            seen_chunks = set()
            sources_list = []
            
            # Interleave to balance results, deduplicating by chunk_id
            for r, o in zip(sources_rewritten + [None]*3, sources_original + [None]*3):
                if r and r["chunk_id"] not in seen_chunks:
                    sources_list.append(r)
                    seen_chunks.add(r["chunk_id"])
                if o and o["chunk_id"] not in seen_chunks:
                    sources_list.append(o)
                    seen_chunks.add(o["chunk_id"])
                    
            # Keep top 4 combined
            sources_list = sources_list[:4]
        
        context_text = "\n\n".join(
            f"[Source {idx + 1}]\n{chunk['text']}"
            for idx, chunk in enumerate(sources_list)
        )
        sources = [
            {
                "chunk_id": chunk["chunk_id"],
                "source_id": chunk["source_id"],
                "text": chunk["text"],
                "score": chunk["score"]
            }
            for chunk in sources_list
        ]
        
        logger.info(
            "retrieval_complete",
            chatbot_id=chatbot_id,
            chunks=len(sources),
            used_multi_query=bool(rewritten and rewritten.lower().strip() != original.lower().strip())
        )
        return {"sources": sources, "context_text": context_text}

    @staticmethod
    def validate_node(state: AgentState) -> AgentState:
        sources = state.get("sources", [])
        context_text = state.get("context_text", "")
        if not sources and not context_text.strip():
            logger.info("validation_result", is_relevant=False, chunks_before=0, chunks_after=0)
            return {"is_relevant": False, "context_text": ""}
            
        query = state.get("rewritten_query") or state["user_message"]
        
        # Resolve OpenRouter API Key
        api_key = state.get("api_key")
        if api_key == "managed-by-openrouter":
            api_key = getattr(settings, "OPENROUTER_API_KEY", None) or os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            is_rel = AgentGraphExecutor._has_lexical_relevance(query, state.get("context_text", ""))
            filtered_sources = state.get("sources", []) if is_rel else []
            logger.info("validation_result", is_relevant=is_rel, chunks_before=len(sources), chunks_after=len(filtered_sources), no_api_key=True)
            return {
                "is_relevant": is_rel,
                "sources": filtered_sources,
                "context_text": state.get("context_text", "") if is_rel else ""
            }
            
        try:
            documents = [src['text'] for src in sources]
            payload = {
                "model": "cohere/rerank-4-fast",
                "query": query,
                "documents": documents,
                "top_n": len(documents)
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            with httpx.Client() as client:
                response = client.post(
                    "https://openrouter.ai/api/v1/rerank",
                    json=payload,
                    headers=headers,
                    timeout=15.0
                )
                response.raise_for_status()
                result = response.json()
            
            filtered_sources = []
            
            if "results" in result:
                sorted_results = sorted(result["results"], key=lambda x: x.get("relevance_score", 0), reverse=True)
                for item in sorted_results:
                    score = item.get("relevance_score", 0)
                    idx = item.get("index")
                    
                    if score >= 0.3 and idx is not None and 0 <= idx < len(sources):
                        filtered_sources.append(sources[idx])
            
            if not filtered_sources:
                logger.info("validation_result", is_relevant=False, chunks_before=len(sources), chunks_after=0)
                return {"is_relevant": False, "sources": [], "context_text": ""}
                
            new_context_text = "\n\n".join(
                f"[Source {idx + 1}]\n{chunk['text']}"
                for idx, chunk in enumerate(filtered_sources)
            )
            
            logger.info("validation_result", is_relevant=True, chunks_before=len(sources), chunks_after=len(filtered_sources))
            return {
                "is_relevant": True, 
                "sources": filtered_sources, 
                "context_text": new_context_text
            }
        except Exception as e:
            logger.warning("validate_node_rerank_api_failed", error=str(e))
            # Fall back to lexical relevance check with the original sources
            is_rel = AgentGraphExecutor._has_lexical_relevance(query, state.get("context_text", ""))
            filtered_sources = state.get("sources", []) if is_rel else []
            logger.info("validation_result", is_relevant=is_rel, chunks_before=len(sources), chunks_after=len(filtered_sources), fallback_lexical=True)
            return {
                "is_relevant": is_rel,
                "sources": filtered_sources,
                "context_text": state.get("context_text", "") if is_rel else ""
            }

    @staticmethod
    def _generate_mock_response(query: str, context: str, persona: Persona, traits: List[str]) -> str:
        query_words = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 3]
        sentences = re.split(r'[.!?\n]+', context)
        
        matched_sentence = ""
        best_match_count = 0
        for s in sentences:
            s_lower = s.lower()
            cnt = sum(1 for w in query_words if w in s_lower)
            if cnt > best_match_count:
                best_match_count = cnt
                matched_sentence = s.strip()
                
        if not matched_sentence and sentences:
            for s in sentences:
                if s.strip():
                    matched_sentence = s.strip()
                    break

        lang = detect_message_language(query)
        if lang == "urdu":
            ans = f"معلومات کے مطابق: {matched_sentence}۔" if matched_sentence else "معاف کیجئے گا، میرے پاس اس کے متعلق معلومات نہیں ہیں۔"
        elif lang == "roman_urdu":
            ans = f"Maine details check ki hain: {matched_sentence}." if matched_sentence else "I'm sorry, mere paas is ki exact details nahi hain."
        else:
            ans = f"Here is what I found: {matched_sentence}." if matched_sentence else "I'm sorry, I couldn't find that specific information right now."

        if "Friendly" in traits:
            ans += " I am here to help."
        elif "Professional" in traits:
            ans = f"Dear User, {ans}"
            
        return ans

    @staticmethod
    def rag_answer_node(state: AgentState) -> AgentState:
        if not state.get("is_relevant") or not state.get("context_text"):
            # Check for custom fallback in persona first
            fallback_msg = getattr(state["persona"], "fallback", None)
            if fallback_msg:
                return {"response": fallback_msg}
                
            lang = state["persona"].language
            if lang == "multilingual":
                lang = detect_message_language(state["user_message"], state.get("history"))
                
            if lang == "urdu":
                ans = "معاف کیجئے گا، میرے پاس فی الحال اس کی تفصیلات موجود نہیں ہیں۔ کیا میں آپ کا رابطہ ہماری ٹیم سے کروا دوں؟"
            elif lang == "roman_urdu":
                ans = "I'm sorry, mere paas is waqt iski exact details nahi hain. Kya main aapka rabta apni support team se karwa doon?"
            elif lang == "english":
                ans = "I'm sorry, I don't have the exact details for that right now. Would you like me to connect you to someone from our team who can help?"
            else:
                detected = detect_message_language(state["user_message"], state.get("history"))
                if detected == "urdu":
                    ans = "معاف کیجئے گا، میرے پاس فی الحال اس کی تفصیلات موجود نہیں ہیں۔ کیا میں آپ کا رابطہ ہماری ٹیم سے کروا دوں؟"
                elif detected == "roman_urdu":
                    ans = "I'm sorry, mere paas is waqt iski exact details nahi hain. Kya main aapka rabta apni support team se karwa doon?"
                else:
                    ans = "I'm sorry, I don't have the exact details for that right now. Would you like me to connect you to someone from our team who can help?"
            return {"response": ans}

        llm = AgentGraphExecutor._get_llm(state)
        if llm:
            try:
                desc = getattr(state["persona"], "description", None) or ""
                desc_str = f"Description/Role: {desc}\n" if desc else ""
                sys_msg = SystemMessage(content=(
                    f"You are {state['persona'].name or 'Aina Bot'}. Traits: {', '.join(state['traits'])}. "
                    f"{desc_str}"
                    "IMPORTANT GUIDELINES:\n"
                    "1. Act strictly as a human representative. Never mention that you are an AI, a bot, or reading from a 'context' or 'database'.\n"
                    "2. Use ONLY the following context to answer the user's query. If you do not know the answer, politely say you don't know without breaking character. "
                    "3. Generate the response in the user's input language (English, Urdu script, or Roman Urdu).\n\n"
                    f"Context:\n{state['context_text']}"
                ))
                messages = [sys_msg]
                for m in state["history"][-6:]:
                    role = HumanMessage if m.role == MessageRole.USER else AIMessage
                    messages.append(role(content=m.content))
                messages.append(HumanMessage(content=state["user_message"]))
                
                ans = llm.invoke(messages).content.strip()
                return {"response": ans}
            except Exception as e:
                logger.warning(f"RAG generation failed: {e}")
                
        # Mock fallback
        ans = AgentGraphExecutor._generate_mock_response(
            state.get("rewritten_query") or state["user_message"], 
            state["context_text"], 
            state["persona"], 
            state["traits"]
        )
        return {"response": ans}

    @staticmethod
    def maybe_summarize_node(state: AgentState) -> AgentState:
        """Conditionally summarize conversation memory (lazy — only when needed)."""
        from app.services.semantic_router import MEMORY_THRESHOLD, MEMORY_REFRESH_INTERVAL
        from app.core.metrics import memory_summarization_total

        history = state.get("history", [])
        memory = state.get("conversation_memory") or {}
        # +1 for the current user message that was added to DB before graph execution
        history_len = len(history) + 1

        # Check if summarization is needed
        if history_len <= MEMORY_THRESHOLD:
            return {}  # Too short, skip

        if memory.get("summary"):
            covered = memory.get("summary_covers_until_turn", 0)
            unsummarized = history_len - covered
            if unsummarized < MEMORY_REFRESH_INTERVAL:
                return {}  # Summary is fresh enough, skip

        # Summarization needed
        api_key = state.get("api_key")
        if not api_key:
            return {}

        try:
            effective_key, base_url = _resolve_openrouter_key(api_key)
            if not effective_key:
                return {}

            llm_kwargs = {
                "api_key": effective_key,
                "model": "openai/gpt-4o-mini" if base_url else "gpt-4o-mini",
                "temperature": 0.0,
                "max_tokens": 150,
            }
            if base_url:
                llm_kwargs["base_url"] = base_url

            llm = ChatOpenAI(**llm_kwargs)

            # Build messages to summarize (only unsummarized ones)
            covered = memory.get("summary_covers_until_turn", 0)
            unsummarized_msgs = history[covered:] if covered < len(history) else history[-4:]
            msg_lines = []
            for m in unsummarized_msgs:
                role_label = "USER" if m.role == MessageRole.USER else "BOT"
                msg_lines.append(f"{role_label}: {m.content}")
            # Include the current exchange
            msg_lines.append(f"USER: {state['user_message']}")
            bot_response = state.get("response", "")
            if bot_response:
                msg_lines.append(f"BOT: {bot_response}")

            existing_summary = memory.get("summary", "")
            prev_context = f"Previous summary: {existing_summary}" if existing_summary else "Previous summary: None (new conversation)"

            sys_prompt = (
                "Analyze this conversation and output a JSON object.\n\n"
                f"{prev_context}\n\n"
                f"New messages since last summary:\n" + "\n".join(msg_lines) + "\n\n"
                "Output this exact JSON structure (no other text):\n"
                '{\n'
                '  "summary": "<1-2 sentence summary of entire conversation so far>",\n'
                '  "topics": ["<topic1>", "<topic2>"],\n'
                '  "user_mood": "<neutral|friendly|interested|confused|frustrated|closing>",\n'
                '  "phase": "<greeting|active|closing>"\n'
                '}'
            )

            result = llm.invoke([
                SystemMessage(content=sys_prompt),
                HumanMessage(content="Generate the JSON:")
            ]).content.strip()

            # Parse JSON response
            # Strip markdown code fences if present
            if result.startswith("```"):
                result = result.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            parsed = json.loads(result)
            new_memory = {
                "summary": parsed.get("summary", ""),
                "turn_count": history_len,
                "summary_covers_until_turn": history_len,
                "topics": parsed.get("topics", []),
                "user_mood": parsed.get("user_mood", "neutral"),
                "phase": parsed.get("phase", "active"),
            }

            memory_summarization_total.inc()
            logger.info("conversation_memory_updated", turn_count=history_len, phase=new_memory["phase"])
            return {"conversation_memory": new_memory}

        except Exception as e:
            logger.warning(f"Memory summarization failed (non-fatal): {e}")
            return {}

    @classmethod
    def build_graph(cls):
        workflow = StateGraph(AgentState)
        
        workflow.add_node("route", cls.route_intent)
        workflow.add_node("agent_handoff", cls.agent_handoff_node)
        workflow.add_node("conversational", cls.conversational_node)
        workflow.add_node("rewrite", cls.rewrite_node)
        workflow.add_node("retrieve", cls.retrieve_node)
        workflow.add_node("validate", cls.validate_node)
        workflow.add_node("rag_answer", cls.rag_answer_node)
        workflow.add_node("maybe_summarize", cls.maybe_summarize_node)
        
        workflow.set_entry_point("route")
        
        def route_condition(state: AgentState):
            return state["intent"]
            
        workflow.add_conditional_edges("route", route_condition, {
            "AGENT_HANDOFF": "agent_handoff",
            "FRUSTRATION": "agent_handoff",
            "CONVERSATIONAL": "conversational",
            "RAG_LOOKUP": "rewrite"
        })
        
        workflow.add_edge("agent_handoff", END)
        workflow.add_edge("conversational", "maybe_summarize")
        workflow.add_edge("rewrite", "retrieve")
        workflow.add_edge("retrieve", "validate")
        workflow.add_edge("validate", "rag_answer")
        workflow.add_edge("rag_answer", "maybe_summarize")
        workflow.add_edge("maybe_summarize", END)
        
        return workflow.compile()

    @classmethod
    def execute(cls, initial_state: AgentState) -> AgentState:
        return cls._get_graph().invoke(initial_state)


# --- Chat Service Orchestrator ---
class ChatService:
    """
    Orchestrator class managing DB transactions, security, lookup, and updates.
    Invokes the pure AgentGraphExecutor for LangGraph execution.
    """
    message_repo = MessageRepository()
    conversation_repo = ConversationRepository()

    @staticmethod
    def route_intent(state: AgentState) -> AgentState:
        return AgentGraphExecutor.route_intent(state)

    @classmethod
    def get_rag_response(
        cls, db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID, user_message: str, conversation_id: Optional[uuid.UUID] = None, deployment_id: Optional[uuid.UUID] = None, callbacks: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        
        # 1. Fetch resources
        chatbot = db.query(Chatbot).filter(
            Chatbot.id == chatbot_id, 
            Chatbot.org_id == org_id, 
            Chatbot.deleted_at == None
        ).first()
        if not chatbot:
            raise ValueError("Chatbot not found or inaccessible")

        persona = db.query(Persona).filter(
            Persona.id == chatbot.persona_id, 
            Persona.deleted_at == None
        ).first()
        if not persona:
            raise ValueError("Chatbot Persona not found")

        traits = [t.trait_name for t in db.query(PersonaTrait).filter(PersonaTrait.persona_id == persona.id).all()]

        # 2. Resolve credentials safely
        api_key = None
        routing_rules_dict = {}
        
        active_config = db.query(AIModelConfig).filter(AIModelConfig.org_id == org_id).first()
        if active_config:
            try:
                api_key = model_config_service.decrypt_key(active_config.encrypted_api_key)
            except Exception:
                pass
            for rule in active_config.routing_rules:
                routing_rules_dict[rule.intent] = rule.model_target

        if not api_key:
            # If no provider is explicitly configured, use OpenRouter by default
            api_key = "managed-by-openrouter"

        # 3. Resolve session
        is_new_conv = False
        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id, 
                Conversation.chatbot_id == chatbot_id, 
                Conversation.deleted_at == None
            ).first()
            if not conversation:
                raise ValueError("Conversation session not found")
            
            # If resolved, auto-resume bot
            if conversation.status == ConversationStatus.RESOLVED:
                conversation.status = ConversationStatus.ONGOING
                conversation.assigned_agent_id = None
                db.add(conversation)
                db.flush()
        else:
            conversation = Conversation(chatbot_id=chatbot_id, status=ConversationStatus.ONGOING, deployment_id=deployment_id)
            db.add(conversation)
            db.flush()
            is_new_conv = True

        # If already escalated, bypass RAG execution
        if conversation.status == ConversationStatus.ESCALATED:
            from app.services.escalation_router import EscalationRouter
            return EscalationRouter.handle_escalated_message(
                db=db,
                conversation=conversation,
                chatbot=chatbot,
                org_id=org_id,
                user_message=user_message,
                language=persona.language,
                active_config_id=active_config.id if active_config else None
            )

        start_date = conversation.started_at
        end_date = datetime.now(timezone.utc)
        history = cls.message_repo.fetch_history(db, conversation.id, start_date, end_date)

        # Record user message first to avoid ghost turns on execution failure
        user_msg = DBMessage(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=user_message,
            config_id=active_config.id if active_config else None
        )
        db.add(user_msg)
        db.flush()

        # 4. Invoke graph execution without DB dependencies
        initial_state = {
            "user_message": user_message,
            "history": history,
            "api_key": api_key,
            "model_name": "openai/gpt-4o-mini", # Will be overwritten by routing rules
            "persona": persona,
            "traits": traits,
            "chatbot_id": str(chatbot_id),
            "status": conversation.status,
            "sources": [],
            "routing_rules": routing_rules_dict,
            "default_model": "openai/gpt-4o-mini",
            "callbacks": callbacks,
            "conversation_memory": conversation.memory,  # Load memory from DB
        }
        
        import time
        
        t0 = time.monotonic()
        final_state = AgentGraphExecutor.execute(initial_state)
        latency = time.monotonic() - t0
        chat_latency_seconds.observe(latency)
        
        # 5. Extract values and update database context
        response_text = final_state.get("response", "An error occurred during generation.")
        new_status = final_state.get("status", conversation.status)
        sources = final_state.get("sources", [])
        intent = final_state.get("intent", "unknown")
        
        # Persist conversation memory if it was updated
        updated_memory = final_state.get("conversation_memory")
        if updated_memory and updated_memory != conversation.memory:
            conversation.memory = updated_memory
            db.add(conversation)
        
        # Track metrics
        is_relevant = final_state.get("is_relevant", False)
        outcome = "answered" if (is_relevant or new_status == ConversationStatus.ESCALATED) else "fallback"
        chat_requests_total.labels(intent=intent or "unknown", outcome=outcome).inc()
        if outcome == "fallback":
            fallback_total.inc()

        if new_status == ConversationStatus.ESCALATED:
            from app.services.escalation_router import EscalationRouter
            return EscalationRouter.escalate(
                db=db,
                conversation=conversation,
                chatbot=chatbot,
                org_id=org_id,
                user_message=user_message,
                response_text=response_text,
                language=persona.language,
                is_new_conv=is_new_conv,
                active_config_id=active_config.id if active_config else None,
                sources=sources,
                write_user_message=False
            )

        if new_status != conversation.status:
            conversation.status = new_status
            db.add(conversation)

        # Record bot reply
        db.add(DBMessage(
            conversation_id=conversation.id,
            role=MessageRole.BOT,
            content=response_text,
            config_id=active_config.id if active_config else None
        ))

        # Update chatbot statistics
        chatbot.total_messages += 2
        if is_new_conv:
            chatbot.total_conversations += 1
        db.add(chatbot)
        
        db.commit()

        return {
            "response": response_text,
            "conversation_id": conversation.id,
            "status": new_status,
            "sources": sources
        }

    @classmethod
    def get_rag_stream(
        cls, db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID, user_message: str, conversation_id: Optional[uuid.UUID] = None, deployment_id: Optional[uuid.UUID] = None
    ):
        import queue
        import threading
        import json
        from app.services.streaming import StreamingCallbackHandler
        
        q = queue.Queue()
        handler = StreamingCallbackHandler(q)
        
        result_container = []
        error_container = []
        
        def run_sync():
            from app.db.session import SessionLocal
            from sqlalchemy import text
            
            thread_db = SessionLocal()
            try:
                # Bind tenant organization context for RLS in this thread's session
                thread_db.execute(
                    text("SELECT set_config('app.current_org_id', :org_id, true)"),
                    {"org_id": str(org_id)},
                )
                res = cls.get_rag_response(
                    thread_db, org_id, chatbot_id, user_message, conversation_id, deployment_id, callbacks=[handler]
                )
                result_container.append(res)
            except Exception as e:
                error_container.append(str(e))
                logger.error("Error in RAG streaming thread", exc_info=True)
            finally:
                thread_db.close()
                q.put(None)  # Sentinel to stop generator
                
        thread = threading.Thread(target=run_sync)
        thread.start()
        
        def generate():
            while True:
                token = q.get()
                if token is None:
                    break
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                
            if error_container:
                yield f"data: {json.dumps({'type': 'error', 'error': error_container[0]})}\n\n"
            elif result_container:
                res = result_container[0]
                res["conversation_id"] = str(res["conversation_id"])
                # stringify chunk uuids if needed
                for src in res.get("sources", []):
                    if "chunk_id" in src: src["chunk_id"] = str(src["chunk_id"])
                    if "source_id" in src: src["source_id"] = str(src["source_id"])
                yield f"data: {json.dumps({'type': 'final', 'data': res})}\n\n"
                
            yield "data: [DONE]\n\n"
            
        return generate()
