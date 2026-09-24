import asyncio
import structlog
from typing import Optional, Dict, Any
from langgraph.graph import StateGraph, END

from app.models.conversation import ConversationStatus
from app.core.config import settings
from app.core.metrics import semantic_cache_requests_total, semantic_cache_similarity_score
from app.services.semantic_router import SemanticRouter
from app.services.rag.helpers import context_from_sources
from app.services.rag.prompts import LocalizationCatalog
from app.services.rag.retriever import BaseRetriever, get_default_retriever
from app.services.rag.state import AgentState
from app.services.rag.nodes import (
    route_intent_node,
    agent_handoff_node,
    conversational_node,
    history_transform_node,
    rewrite_node,
    semantic_cache_node,
    retrieve_node,
    validate_node,
    rag_answer_node,
)

logger = structlog.get_logger(__name__)

# Singleton compiled graph cache
_compiled_rag_graph = None


def build_rag_graph():
    """
    Constructs and compiles the full LangGraph workflow for RAG and multi-intent orchestration.
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("route", route_intent_node)
    workflow.add_node("agent_handoff", agent_handoff_node)
    workflow.add_node("conversational", conversational_node)
    workflow.add_node("history_transform", history_transform_node)
    workflow.add_node("rewrite", rewrite_node)
    workflow.add_node("semantic_cache", semantic_cache_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("rag_answer", rag_answer_node)

    workflow.set_entry_point("route")

    def route_condition(state: AgentState):
        intent = state.get("intent", "RAG_LOOKUP")
        return intent if intent in (
            "AGENT_HANDOFF",
            "FRUSTRATION",
            "CONVERSATIONAL",
            "HISTORY_TRANSFORM",
            "RAG_LOOKUP",
        ) else "RAG_LOOKUP"

    workflow.add_conditional_edges(
        "route",
        route_condition,
        {
            "AGENT_HANDOFF": "agent_handoff",
            "FRUSTRATION": "agent_handoff",
            "CONVERSATIONAL": "conversational",
            "HISTORY_TRANSFORM": "history_transform",
            "RAG_LOOKUP": "rewrite",
        },
    )

    workflow.add_edge("agent_handoff", END)
    workflow.add_edge("conversational", END)
    workflow.add_edge("history_transform", END)
    workflow.add_edge("rewrite", "semantic_cache")

    def cache_condition(state: AgentState):
        return "hit" if state.get("cache_hit") else "miss"

    workflow.add_conditional_edges(
        "semantic_cache",
        cache_condition,
        {
            "hit": END,
            "miss": "retrieve",
        },
    )

    workflow.add_edge("retrieve", "validate")
    workflow.add_edge("validate", "rag_answer")
    workflow.add_edge("rag_answer", END)

    return workflow.compile()


def get_rag_graph():
    """Returns the compiled LangGraph workflow singleton."""
    global _compiled_rag_graph
    if _compiled_rag_graph is None:
        _compiled_rag_graph = build_rag_graph()
    return _compiled_rag_graph


async def precheck_semantic_cache(state: AgentState) -> Optional[Dict[str, Any]]:
    """
    Pre-check semantic cache with the ORIGINAL (un-rewritten) user query before graph execution.
    On hit, returns a final state that skips the entire 5-node RAG pipeline.
    Avoids embedding generation on obvious greetings, conversational chat, or handoff phrases.
    """
    msg = state.get("user_message", "").lower().strip()
    if not msg:
        return None

    normalized_msg = msg.strip(" .!?,")

    # 1. Exact greetings & common conversational patterns (English, Urdu, Roman Urdu)
    if (
        normalized_msg in SemanticRouter.EXACT_GREETINGS
        or any(msg.startswith(p) for p in SemanticRouter.GREETING_PREFIXES)
        or any(
            g in normalized_msg
            for g in [
                "kya haal",
                "kya hal",
                "kaise ho",
                "kaise hain",
                "kaisay ho",
                "kaisay hain",
                "theek ho",
                "ap kaise",
                "aap kaise",
                "kia haal",
                "kia hal",
                "kya chal raha",
                "kia chal raha",
                "who are you",
                "tum kon ho",
                "aap kon ho",
            ]
        )
    ):
        return None

    # 2. Agent handoff phrases (explicit human escalation)
    if any(kw in msg for kw in SemanticRouter.ROUTES.get("AGENT_HANDOFF", [])):
        return None

    # 3. History transformation requests (summarize, translate, shorten, bullets)
    if SemanticRouter._matches_history_transform(msg):
        return None

    retriever: BaseRetriever = state.get("retriever") or get_default_retriever()
    state["precheck_cache_checked"] = True
    vec_holder: Dict[str, Any] = {}
    response_text, sources, similarity = await retriever.acheck_cache(
        org_id=state["org_id"],
        chatbot_id=state["chatbot_id"],
        query=state["user_message"],
        knowledge_base_version=state.get("knowledge_base_version", 1),
        persona_version=state.get("persona_version", 1),
        threshold=settings.CACHE_SIMILARITY_THRESHOLD,
        out_query_vector=vec_holder,
    )
    if "vector" in vec_holder:
        state["original_query_vector"] = vec_holder["vector"]

    if response_text:
        semantic_cache_requests_total.labels(result="hit").inc()
        if similarity is not None:
            semantic_cache_similarity_score.observe(similarity)
        logger.info(
            "precheck_cache_hit",
            chatbot_id=state.get("chatbot_id"),
            similarity=similarity,
            skipped_pipeline=True,
        )
        return {
            "cache_hit": True,
            "response": response_text,
            "response_source": "semantic_cache",
            "cache_similarity": similarity,
            "sources": sources or [],
            "intent": "RAG_LOOKUP",
            "is_relevant": True,
            "validated_chunks_count": len(sources) if sources else 0,
            "context_text": context_from_sources(sources) if sources else "",
        }

    semantic_cache_requests_total.labels(result="miss").inc()
    return None


def _build_fallback_state(initial_state: AgentState) -> AgentState:
    persona = initial_state.get("persona")
    lang = getattr(persona, "language", "en") if persona else "en"
    fb = getattr(persona, "fallback", None) or LocalizationCatalog.get_fallback_message(lang)
    fallback_state = dict(initial_state)
    fallback_state.update({
        "response": fb,
        "response_source": "fallback",
        "status": fallback_state.get("status", ConversationStatus.ONGOING),
        "sources": [],
        "is_relevant": False,
        "validated_chunks_count": 0,
    })
    return fallback_state


async def execute_rag_pipeline(initial_state: AgentState) -> AgentState:
    """
    Main entry point for executing the RAG agent pipeline.
    Checks semantic cache first, then invokes the compiled LangGraph workflow with timeout protection.
    """
    cached = await precheck_semantic_cache(initial_state)
    if cached is not None:
        return cached

    graph = get_rag_graph()
    timeout = getattr(settings, "RAG_GRAPH_TIMEOUT", 30.0)
    try:
        return await asyncio.wait_for(graph.ainvoke(initial_state), timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(
            "rag_graph_execution_timed_out",
            timeout=timeout,
            chatbot_id=initial_state.get("chatbot_id"),
        )
        return _build_fallback_state(initial_state)
    except Exception as e:
        logger.error(
            "rag_graph_execution_failed",
            error=str(e),
            chatbot_id=initial_state.get("chatbot_id"),
            exc_info=True,
        )
        return _build_fallback_state(initial_state)
