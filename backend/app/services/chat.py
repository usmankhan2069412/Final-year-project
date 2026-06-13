import uuid
import logging
import re
import os
import json
import httpx
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, TypedDict
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from itertools import zip_longest

from app.core.config import settings, resolve_openrouter_key
from app.core.language import detect_message_language
from app.core.metrics import chat_requests_total, chat_latency_seconds, fallback_total, validated_chunks_count
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
    query_vector: List[float]
    sources: List[Dict[str, Any]]
    context_text: str
    is_relevant: bool
    routing_rules: Dict[str, str]
    default_model: str

    # Semantic Cache tracking
    org_id: str
    knowledge_base_version: int
    persona_version: int
    cache_hit: bool
    cache_similarity: float
    response_source: str # "semantic_cache" | "rag_generation" | "history_transform" | "fallback"
    validated_chunks_count: int

    # Conversation memory (lazy summarization)
    conversation_memory: Optional[dict]

    # Final Output
    response: str
    status: ConversationStatus
    callbacks: Optional[List[Any]]


from app.services.semantic_router import SemanticRouter

# --- Agent Graph Executor ---
class AgentGraphExecutor:
    """
    Pure graph executor operating on state dictionary variables.
    Decoupled entirely from database models/transactions.
    """
    _graph = None  # Compiled graph singleton â€” safe to share (stateless)

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

        effective_key, base_url = resolve_openrouter_key(api_key)
        if not effective_key:
            return None

        model_to_use = model if base_url else (model.split("/")[-1] if "/" in model else model)

        llm_kwargs = {
            "api_key": effective_key,
            "model": model_to_use,
            "temperature": temperature,
            "streaming": bool(callbacks),
            "callbacks": callbacks,
        }
        if base_url:
            llm_kwargs["base_url"] = base_url

        return ChatOpenAI(**llm_kwargs)

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
        if not query_terms or not context.strip():
            return False

        context_terms = cls._content_terms(context)
        overlap = query_terms & context_terms
        if not overlap:
            return False

        overlap_ratio = len(overlap) / max(len(query_terms), 1)
        if len(query_terms) <= 2:
            return len(overlap) == len(query_terms)
        return len(overlap) >= 3 or overlap_ratio >= 0.6

    @classmethod
    def _filter_lexically_relevant_sources(cls, query: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            source
            for source in sources
            if cls._has_lexical_relevance(query, source.get("text", ""))
        ]

    @staticmethod
    def _context_from_sources(sources: List[Dict[str, Any]]) -> str:
        return "\n\n".join(
            f"[Source {i + 1}]\n{text}"
            for i, text in enumerate(chunk.get("text") for chunk in sources if chunk.get("text"))
        )

    @staticmethod
    def _message_role_value(message: Any) -> str:
        role = message.get("role") if isinstance(message, dict) else getattr(message, "role", None)
        return getattr(role, "value", role) or ""

    @staticmethod
    def _message_content(message: Any) -> str:
        return (message.get("content") if isinstance(message, dict) else getattr(message, "content", "")) or ""

    @classmethod
    def _last_bot_answer(cls, history: List[Any]) -> str:
        for message in reversed(history or []):
            if cls._message_role_value(message) == MessageRole.BOT.value:
                content = cls._message_content(message).strip()
                if content:
                    return content
        return ""

    @staticmethod
    def _should_transform_recent_conversation(user_message: str) -> bool:
        msg = user_message.lower()
        conversation_markers = [
            "our chat", "our conversation", "this chat", "full conversation",
            "chat history", "conversation history", "hamari baat", "hamari chat",
            "poori chat", "puri chat", "sari chat",
        ]
        summary_markers = ["summarize", "summarise", "summary", "khulasa", "mukhtasar"]
        return any(marker in msg for marker in conversation_markers) and any(marker in msg for marker in summary_markers)

    @classmethod
    def _recent_conversation_text(cls, history: List[Any], limit: int = 8) -> str:
        lines = []
        for message in (history or [])[-limit:]:
            role = cls._message_role_value(message)
            content = cls._message_content(message).strip()
            if not content:
                continue
            role_label = "User" if role == MessageRole.USER.value else "Assistant"
            lines.append(f"{role_label}: {content}")
        return "\n".join(lines)

    @staticmethod
    def _history_transform_clarifying_message(lang: str) -> str:
        messages = {
            "urdu": "Ø¨Ø±Ø§Û Ú©Ø±Ù… ÙˆÛ Ù…ØªÙ† Ø¨Ú¾ÛŒØ¬ Ø¯ÛŒÚº Ø¬Ø³Û’ Ø¢Ù¾ translate, summarize, ya rewrite karwana chahte hain.",
            "roman_urdu": "Please woh text bhej dein jise aap translate, summarize, ya rewrite karwana chahte hain.",
        }
        return messages.get(lang, "Please send the text you want me to translate, summarize, or rewrite.")

    @staticmethod
    def _history_transform_unavailable_message(lang: str) -> str:
        messages = {
            "urdu": "Ù…Ø¹Ø§Ù Ú©ÛŒØ¬ÛŒÛ’ØŒ Ù…ÛŒÚº Ø§Ø³ ÙˆÙ‚Øª Ù¾Ú†Ú¾Ù„Û’ Ø¬ÙˆØ§Ø¨ Ú©Ùˆ transform Ù†ÛÛŒÚº Ú©Ø± Ù¾Ø§ Ø±ÛØ§Û” Ø¨Ø±Ø§Û Ú©Ø±Ù… Ø¯ÙˆØ¨Ø§Ø±Û Ú©ÙˆØ´Ø´ Ú©Ø±ÛŒÚºÛ”",
            "roman_urdu": "Sorry, main is waqt pichla jawab transform nahi kar pa raha. Please dobara try karein.",
        }
        return messages.get(lang, "Sorry, I cannot transform the previous answer right now. Please try again.")

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
                return {"response": result, "response_source": "conversational"}
            except Exception as e:
                logger.warning(f"LLM conversational generation failed: {e}")

        return {"response": greeting, "response_source": "conversational"}

    @staticmethod
    def history_transform_node(state: AgentState) -> AgentState:
        history = state.get("history") or []
        user_message = state["user_message"]
        lang = detect_message_language(user_message, history)

        if AgentGraphExecutor._should_transform_recent_conversation(user_message):
            target_type = "recent_conversation"
            target_text = AgentGraphExecutor._recent_conversation_text(history)
        else:
            target_type = "last_bot_answer"
            target_text = AgentGraphExecutor._last_bot_answer(history)

        if not target_text:
            logger.info(
                "history_transform_result",
                target_type="missing",
                transformed_chars=0,
            )
            return {
                "response": AgentGraphExecutor._history_transform_clarifying_message(lang),
                "response_source": "history_transform",
                "sources": [],
                "context_text": "",
                "is_relevant": False,
                "validated_chunks_count": 0,
            }

        llm = AgentGraphExecutor._get_llm(state, temperature=0.2)
        if not llm:
            logger.info(
                "history_transform_result",
                target_type=target_type,
                transformed_chars=0,
                no_llm=True,
            )
            return {
                "response": AgentGraphExecutor._history_transform_unavailable_message(lang),
                "response_source": "history_transform",
                "sources": [],
                "context_text": "",
                "is_relevant": False,
                "validated_chunks_count": 0,
            }

        try:
            persona_name = getattr(state["persona"], "name", None) or "Aina Bot"
            traits = ", ".join(state.get("traits") or [])
            sys_msg = SystemMessage(content=(
                f"You are {persona_name}. Traits: {traits}.\n"
                "The user is asking you to transform previous chat content.\n"
                "Use ONLY the target text below. Preserve every factual detail, list item, "
                "number, name, and ordering unless the user's instruction explicitly asks "
                "for compression or a different format. Do not add new facts. Do not perform "
                "a fresh knowledge lookup. Output only the transformed text.\n"
                "Use the language or format requested by the user. If none is requested, "
                "use the user's latest message language."
            ))
            human_msg = HumanMessage(content=(
                f"User instruction:\n{user_message}\n\n"
                f"Target type: {target_type}\n"
                f"Target text:\n{target_text}"
            ))
            response = llm.invoke([sys_msg, human_msg]).content.strip()
            if not response:
                response = AgentGraphExecutor._history_transform_unavailable_message(lang)

            logger.info(
                "history_transform_result",
                target_type=target_type,
                transformed_chars=len(response),
            )
            return {
                "response": response,
                "response_source": "history_transform",
                "sources": [],
                "context_text": "",
                "is_relevant": False,
                "validated_chunks_count": 0,
            }
        except Exception as e:
            logger.warning("history_transform_failed", error=str(e), target_type=target_type)
            return {
                "response": AgentGraphExecutor._history_transform_unavailable_message(lang),
                "response_source": "history_transform",
                "sources": [],
                "context_text": "",
                "is_relevant": False,
                "validated_chunks_count": 0,
            }

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
    def semantic_cache_node(state: AgentState) -> AgentState:
        rewritten = state.get("rewritten_query")
        if not rewritten:
            return {"cache_hit": False}

        from app.services.semantic_cache import SemanticCacheService
        from app.core.metrics import semantic_cache_requests_total, semantic_cache_similarity_score

        response_text, chunk_ids, similarity = SemanticCacheService.check_cache(
            org_id=state["org_id"],
            chatbot_id=state["chatbot_id"],
            rewritten_query=rewritten,
            knowledge_base_version=state.get("knowledge_base_version", 1),
            persona_version=state.get("persona_version", 1),
            threshold=settings.CACHE_SIMILARITY_THRESHOLD
        )

        if response_text:
            semantic_cache_requests_total.labels(result="hit").inc()
            if similarity is not None:
                semantic_cache_similarity_score.observe(similarity)
            sources = VectorStoreService.fetch_sources_by_chunk_ids(
                state["chatbot_id"],
                chunk_ids or []
            )
            return {
                "cache_hit": True,
                "response": response_text,
                "response_source": "semantic_cache",
                "cache_similarity": similarity,
                "sources": sources
            }

        semantic_cache_requests_total.labels(result="miss").inc()
        return {"cache_hit": False}

    @staticmethod
    def retrieve_node(state: AgentState) -> AgentState:
        rewritten = state.get("rewritten_query")
        original = state["user_message"]
        chatbot_id = state["chatbot_id"]

        from app.services.embedding import embedding_service

        # If no rewrite or exactly the same, do a single search
        if not rewritten or rewritten.lower().strip() == original.lower().strip():
            query_vector = embedding_service.encode([original])[0]
            query_list = query_vector.tolist() if hasattr(query_vector, "tolist") else list(query_vector)
            sources_list = VectorStoreService.search_hybrid(chatbot_id, original, top_k=settings.RETRIEVAL_TOP_K_SINGLE, query_vector=query_list)
            # Save vector for caching
            state["query_vector"] = query_list
        else:
            # Multi-Query Retrieval: search both and merge
            # Batch encode both queries to halve API calls
            vectors = embedding_service.encode([rewritten, original])
            rewritten_vec = vectors[0].tolist() if hasattr(vectors[0], "tolist") else list(vectors[0])
            original_vec = vectors[1].tolist() if hasattr(vectors[1], "tolist") else list(vectors[1])

            # Save rewritten vector to state for caching
            state["query_vector"] = rewritten_vec

            sources_rewritten = VectorStoreService.search_hybrid(chatbot_id, rewritten, top_k=settings.RETRIEVAL_TOP_K_MULTI, query_vector=rewritten_vec)
            sources_original = VectorStoreService.search_hybrid(chatbot_id, original, top_k=settings.RETRIEVAL_TOP_K_MULTI, query_vector=original_vec)

            seen_chunks = set()
            sources_list = []

            # Interleave to balance results, deduplicating by chunk_id
            for r, o in zip_longest(sources_rewritten, sources_original):
                if r and r["chunk_id"] not in seen_chunks:
                    sources_list.append(r)
                    seen_chunks.add(r["chunk_id"])
                if o and o["chunk_id"] not in seen_chunks:
                    sources_list.append(o)
                    seen_chunks.add(o["chunk_id"])

            # Keep top 4 combined
            sources_list = sources_list[:4]

        sources = [dict(chunk) for chunk in sources_list]
        context_text = AgentGraphExecutor._context_from_sources(sources)

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
        if not sources:
            logger.info("validation_result", is_relevant=False, chunks_before=0, chunks_after=0)
            return {"is_relevant": False, "context_text": ""}

        query = state.get("rewritten_query") or state["user_message"]

        # Only use the system-level OpenRouter key for reranking
        rerank_api_key = getattr(settings, "OPENROUTER_API_KEY", None) or os.getenv("OPENROUTER_API_KEY")

        if not rerank_api_key:
            filtered_sources = AgentGraphExecutor._filter_lexically_relevant_sources(query, sources)
            is_rel = bool(filtered_sources)
            context_text = AgentGraphExecutor._context_from_sources(filtered_sources)
            logger.info("validation_result", is_relevant=is_rel, chunks_before=len(sources), chunks_after=len(filtered_sources), no_api_key=True)
            return {
                "is_relevant": is_rel,
                "sources": filtered_sources,
                "context_text": context_text if is_rel else "",
                "validated_chunks_count": len(filtered_sources)
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
                "Authorization": f"Bearer {rerank_api_key}",
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
                        source = dict(sources[idx])
                        source["rerank_score"] = float(score)
                        filtered_sources.append(source)

            if not filtered_sources:
                logger.info("validation_result", is_relevant=False, chunks_before=len(sources), chunks_after=0)
                return {"is_relevant": False, "sources": [], "context_text": ""}

            new_context_text = AgentGraphExecutor._context_from_sources(filtered_sources)

            logger.info("validation_result", is_relevant=True, chunks_before=len(sources), chunks_after=len(filtered_sources))
            return {
                "is_relevant": True,
                "sources": filtered_sources,
                "context_text": new_context_text,
                "validated_chunks_count": len(filtered_sources)
            }
        except Exception as e:
            logger.warning("validate_node_rerank_api_failed", error=str(e))
            # Fall back to lexical relevance check with the original sources
            filtered_sources = AgentGraphExecutor._filter_lexically_relevant_sources(query, sources)
            is_rel = bool(filtered_sources)
            context_text = AgentGraphExecutor._context_from_sources(filtered_sources)
            logger.info("validation_result", is_relevant=is_rel, chunks_before=len(sources), chunks_after=len(filtered_sources), fallback_lexical=True)
            return {
                "is_relevant": is_rel,
                "sources": filtered_sources,
                "context_text": context_text if is_rel else "",
                "validated_chunks_count": len(filtered_sources) if is_rel else 0
            }

    @staticmethod
    def _generate_mock_response(query: str, traits: List[str]) -> str:
        lang = detect_message_language(query)
        if lang == "urdu":
            ans = "Ù…ÛŒÚº Ù†Û’ Ú©Ú†Ú¾ Ù…Ø¹Ù„ÙˆÙ…Ø§Øª ÚˆÚ¾ÙˆÙ†ÚˆÛŒ ÛÛŒÚº Ù„ÛŒÚ©Ù† ØªÚ©Ù†ÛŒÚ©ÛŒ Ù…Ø³Ø¦Ù„Û’ Ú©ÛŒ ÙˆØ¬Û Ø³Û’ Ù…Ú©Ù…Ù„ Ø¬ÙˆØ§Ø¨ Ù†ÛÛŒÚº Ø¯Û’ Ù¾Ø§ Ø±ÛØ§Û” Ø¨Ø±Ø§Û Ú©Ø±Ù… Ø¯ÙˆØ¨Ø§Ø±Û Ú©ÙˆØ´Ø´ Ú©Ø±ÛŒÚºÛ”"
        elif lang == "roman_urdu":
            ans = "Mujhe kuch details mili hain lekin technical error ki wajah se main mukammal jawab nahi de pa raha. Please try again."
        else:
            ans = "I found some relevant information but I am having trouble generating a complete response right now. Please try again."

        if "Friendly" in traits:
            ans += " I am here to help!"
        elif "Professional" in traits:
            ans = f"Dear User, {ans}"

        return ans

    @staticmethod
    def _fallback_message(lang: str) -> str:
        _MSGS = {
            "urdu": "Ù…Ø¹Ø§Ù Ú©ÛŒØ¬Ø¦Û’ Ú¯Ø§ØŒ Ù…ÛŒØ±Û’ Ù¾Ø§Ø³ ÙÛŒ Ø§Ù„Ø­Ø§Ù„ Ø§Ø³ Ú©ÛŒ ØªÙØµÛŒÙ„Ø§Øª Ù…ÙˆØ¬ÙˆØ¯ Ù†ÛÛŒÚº ÛÛŒÚºÛ” Ú©ÛŒØ§ Ù…ÛŒÚº Ø¢Ù¾ Ú©Ø§ Ø±Ø§Ø¨Ø·Û ÛÙ…Ø§Ø±ÛŒ Ù¹ÛŒÙ… Ø³Û’ Ú©Ø±ÙˆØ§ Ø¯ÙˆÚºØŸ",
            "roman_urdu": "I'm sorry, mere paas is waqt iski exact details nahi hain. Kya main aapka rabta apni support team se karwa doon?",
        }
        return _MSGS.get(lang, "I'm sorry, I don't have the exact details for that right now. Would you like me to connect you to someone from our team who can help?")

    @staticmethod
    def rag_answer_node(state: AgentState) -> AgentState:
        if not state.get("is_relevant") or not state.get("context_text"):
            fallback_msg = getattr(state["persona"], "fallback", None)
            if fallback_msg:
                return {"response": fallback_msg, "response_source": "fallback"}

            lang = state["persona"].language
            if lang == "multilingual":
                lang = detect_message_language(state["user_message"], state.get("history"))

            return {"response": AgentGraphExecutor._fallback_message(lang), "response_source": "fallback"}

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
                    "2. Use ONLY the following verified source text to answer the user's current query. If the source text does not answer it, politely say you don't know without breaking character.\n"
                    "3. Ignore any facts from earlier conversation turns unless they also appear in the verified source text.\n"
                    "4. Generate the response in the user's input language (English, Urdu script, or Roman Urdu).\n\n"
                    "Context:\n" + state.get("context_text", "")
                ))
                user_msg = state["user_message"]
                search_query = state.get("rewritten_query") or user_msg
                messages = [
                    sys_msg,
                    HumanMessage(content="Current user query: " + user_msg + "\nStandalone search query: " + search_query)
                ]

                ans = llm.invoke(messages).content.strip()
                return {"response": ans, "response_source": "rag_generation"}
            except Exception as e:
                logger.warning(f"RAG generation failed: {e}")

        # Mock fallback
        ans = AgentGraphExecutor._generate_mock_response(
            state.get("rewritten_query") or state["user_message"],
            state["traits"]
        )
        return {"response": ans, "response_source": "fallback"}



    @classmethod
    def build_graph(cls):
        workflow = StateGraph(AgentState)

        workflow.add_node("route", cls.route_intent)
        workflow.add_node("agent_handoff", cls.agent_handoff_node)
        workflow.add_node("conversational", cls.conversational_node)
        workflow.add_node("history_transform", cls.history_transform_node)
        workflow.add_node("rewrite", cls.rewrite_node)
        workflow.add_node("semantic_cache", cls.semantic_cache_node)
        workflow.add_node("retrieve", cls.retrieve_node)
        workflow.add_node("validate", cls.validate_node)
        workflow.add_node("rag_answer", cls.rag_answer_node)

        workflow.set_entry_point("route")

        def route_condition(state: AgentState):
            return state["intent"]

        workflow.add_conditional_edges("route", route_condition, {
            "AGENT_HANDOFF": "agent_handoff",
            "FRUSTRATION": "agent_handoff",
            "CONVERSATIONAL": "conversational",
            "HISTORY_TRANSFORM": "history_transform",
            "RAG_LOOKUP": "rewrite"
        })

        workflow.add_edge("agent_handoff", END)
        workflow.add_edge("conversational", END)
        workflow.add_edge("history_transform", END)
        workflow.add_edge("rewrite", "semantic_cache")

        def cache_condition(state: AgentState):
            return "hit" if state.get("cache_hit") else "miss"

        workflow.add_conditional_edges("semantic_cache", cache_condition, {
            "hit": END,
            "miss": "retrieve"
        })

        workflow.add_edge("retrieve", "validate")
        workflow.add_edge("validate", "rag_answer")
        workflow.add_edge("rag_answer", END)

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
    def background_summarize_memory(conversation_id: uuid.UUID, org_id: uuid.UUID, user_message: str, bot_response: str, api_key: str, history_len: int, memory: dict):
        """Conditionally summarize conversation memory in a background thread."""
        from app.services.semantic_router import MEMORY_THRESHOLD, MEMORY_REFRESH_INTERVAL
        from app.core.metrics import memory_summarization_total
        from app.db.session import SessionLocal
        from sqlalchemy import text
        from datetime import datetime, timezone

        # Fast check without DB
        if history_len <= MEMORY_THRESHOLD:
            return

        if memory and memory.get("summary"):
            covered = memory.get("summary_covers_until_turn", 0)
            unsummarized = history_len - covered
            if unsummarized < MEMORY_REFRESH_INTERVAL:
                return

        if not api_key:
            return

        db = SessionLocal()
        try:
            # Bind tenant context for Row-Level Security
            db.execute(
                text("SELECT set_config('app.current_org_id', :org_id, true)"),
                {"org_id": str(org_id)},
            )

            conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if not conv:
                return

            effective_key, base_url = resolve_openrouter_key(api_key)
            if not effective_key:
                return

            llm_kwargs = {
                "api_key": effective_key,
                "model": "openai/gpt-4o-mini" if base_url else "gpt-4o-mini",
                "temperature": 0.0,
                "max_tokens": 150,
            }
            if base_url:
                llm_kwargs["base_url"] = base_url

            llm = ChatOpenAI(**llm_kwargs)

            all_history = ChatService.message_repo.fetch_history(db, conversation_id, conv.started_at, datetime.now(timezone.utc))

            # Since the user message and bot response have already been committed, they are in all_history.
            # We don't need to append them manually.
            covered = memory.get("summary_covers_until_turn", 0) if memory else 0

            # Take only the unsummarized portion
            unsummarized_msgs = all_history[covered:] if covered < len(all_history) else all_history[-4:]

            if not unsummarized_msgs:
                return

            msg_lines = []
            for m in unsummarized_msgs:
                role_label = "USER" if m.role == MessageRole.USER else "BOT"
                msg_lines.append(f"{role_label}: {m.content}")

            existing_summary = memory.get("summary", "") if memory else ""
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

            if result.startswith("```"):
                result = result.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            parsed = json.loads(result)
            new_memory = {
                "summary": parsed.get("summary", ""),
                "turn_count": len(all_history),
                "summary_covers_until_turn": len(all_history),
                "topics": parsed.get("topics", []),
                "user_mood": parsed.get("user_mood", "neutral"),
                "phase": parsed.get("phase", "active"),
            }

            conv.memory = new_memory
            db.add(conv)
            db.commit()

            memory_summarization_total.inc()
            logger.info("conversation_memory_updated", turn_count=len(all_history), phase=new_memory["phase"])
        except Exception as e:
            logger.warning(f"Background memory summarization failed: {e}")
        finally:
            db.close()

    @staticmethod
    def route_intent(state: AgentState) -> AgentState:
        return AgentGraphExecutor.route_intent(state)

    @classmethod
    def get_rag_response(
        cls, db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID, user_message: str, conversation_id: Optional[uuid.UUID] = None, deployment_id: Optional[uuid.UUID] = None, callbacks: Optional[List[Any]] = None, background_tasks: Optional[BackgroundTasks] = None
    ) -> Dict[str, Any]:

        # 1. Fetch resources
        chatbot = db.query(Chatbot).filter(
            Chatbot.id == chatbot_id,
            Chatbot.org_id == org_id,
            Chatbot.deleted_at == None
        ).first()
        if not chatbot:
            raise ValueError("Chatbot not found or inaccessible")

        from sqlalchemy.orm import joinedload
        persona = db.query(Persona).options(joinedload(Persona.traits)).filter(
            Persona.id == chatbot.persona_id,
            Persona.deleted_at == None
        ).first()
        if not persona:
            raise ValueError("Chatbot Persona not found")

        traits = [t.trait_name for t in persona.traits]

        # 2. Resolve credentials safely
        api_key = None
        routing_rules_dict = {}

        active_config = db.query(AIModelConfig).filter(
            AIModelConfig.org_id == org_id,
            AIModelConfig.is_active == True,
            AIModelConfig.is_default == True,
        ).first()
        if not active_config:
            active_config = db.query(AIModelConfig).filter(
                AIModelConfig.org_id == org_id,
                AIModelConfig.is_active == True,
            ).first()
        if active_config:
            try:
                api_key = model_config_service.decrypt_key(active_config.encrypted_api_key)
            except Exception:
                pass
            for rule in active_config.routing_rules:
                if rule.is_active:
                    routing_rules_dict[rule.intent] = active_config.model_name

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
                active_config_id=active_config.id if active_config else None,
                background_tasks=background_tasks
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
        db.query(Chatbot).filter(Chatbot.id == chatbot.id).update(
            {Chatbot.total_messages: Chatbot.total_messages + 1}
        )
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
            "org_id": str(org_id),
            "knowledge_base_version": getattr(chatbot, "knowledge_base_version", 1),
            "persona_version": getattr(persona, "persona_version", 1)
        }

        t0 = time.monotonic()
        final_state = AgentGraphExecutor.execute(initial_state)
        latency = time.monotonic() - t0
        chat_latency_seconds.observe(latency)

        # 5. Extract values and update database context
        val_chunks = final_state.get("validated_chunks_count", 0)
        validated_chunks_count.observe(val_chunks)
        response_text = final_state.get("response", "An error occurred during generation.")
        new_status = final_state.get("status", conversation.status)
        sources = final_state.get("sources", [])
        intent = final_state.get("intent", "unknown")
        # Track metrics
        response_source = final_state.get("response_source")
        is_cache_hit = response_source == "semantic_cache"
        is_relevant = final_state.get("is_relevant", False)
        is_direct_answer = response_source in {"history_transform", "conversational"}
        outcome = "answered" if (is_relevant or is_cache_hit or is_direct_answer or new_status == ConversationStatus.ESCALATED) else "fallback"
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
                write_user_message=False,
                background_tasks=background_tasks
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
        db.query(Chatbot).filter(Chatbot.id == chatbot.id).update(
            {Chatbot.total_messages: Chatbot.total_messages + 1}
        )
        if is_new_conv:
            db.query(Chatbot).filter(Chatbot.id == chatbot.id).update(
                {Chatbot.total_conversations: Chatbot.total_conversations + 1}
            )

        db.commit()

        # Update cache on successful new RAG answers
        if intent == "RAG_LOOKUP" and final_state.get("is_relevant") and final_state.get("response_source") == "rag_generation" and final_state.get("validated_chunks_count", 0) > 0 and response_text:
            rewritten_query = final_state.get("rewritten_query")
            source_chunk_ids = [src["chunk_id"] for src in sources] if sources else []
            if rewritten_query:
                from app.services.semantic_cache import SemanticCacheService
                if background_tasks:
                    background_tasks.add_task(
                        SemanticCacheService.add_to_cache,
                        org_id=str(org_id),
                        chatbot_id=str(chatbot_id),
                        rewritten_query=rewritten_query,
                        response_text=response_text,
                        knowledge_base_version=getattr(chatbot, "knowledge_base_version", 1),
                        persona_version=getattr(persona, "persona_version", 1),
                        source_chunk_ids=source_chunk_ids,
                        query_vector=final_state.get("query_vector")
                    )
                else:
                    import threading
                    threading.Thread(
                        target=SemanticCacheService.add_to_cache,
                        kwargs=dict(
                            org_id=str(org_id),
                            chatbot_id=str(chatbot_id),
                            rewritten_query=rewritten_query,
                            response_text=response_text,
                            knowledge_base_version=getattr(chatbot, "knowledge_base_version", 1),
                            persona_version=getattr(persona, "persona_version", 1),
                            source_chunk_ids=source_chunk_ids,
                            query_vector=final_state.get("query_vector")
                        )
                    ).start()

        # Queue background summarization
        if background_tasks:
            background_tasks.add_task(
                ChatService.background_summarize_memory,
                conversation_id=conversation.id,
                org_id=org_id,
                user_message=user_message,
                bot_response=response_text,
                api_key=api_key,
                history_len=len(history) + 1,
                memory=conversation.memory
            )
        else:
            import threading
            threading.Thread(
                target=ChatService.background_summarize_memory,
                args=(conversation.id, org_id, user_message, response_text, api_key, len(history) + 1, conversation.memory)
            ).start()

        return {
            "response": response_text,
            "conversation_id": conversation.id,
            "status": new_status,
            "sources": sources
        }

    @classmethod
    def get_rag_stream(
        cls, db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID, user_message: str, conversation_id: Optional[uuid.UUID] = None, deployment_id: Optional[uuid.UUID] = None, background_tasks: Optional[BackgroundTasks] = None
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
                    thread_db, org_id, chatbot_id, user_message, conversation_id, deployment_id, callbacks=[handler], background_tasks=background_tasks
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
