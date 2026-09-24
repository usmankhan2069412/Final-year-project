from app.core.config import settings
from app.core.metrics import semantic_cache_requests_total, semantic_cache_similarity_score
from app.services.rag.retriever import BaseRetriever, get_default_retriever
from app.services.rag.state import AgentState


async def semantic_cache_node(state: AgentState) -> AgentState:
    """
    Semantic cache lookup node.
    Uses the injected or default retriever seam for 100% database-independent execution.
    """
    rewritten = state.get("rewritten_query")
    if not rewritten:
        return {"cache_hit": False}

    original = state.get("user_message", "")
    if state.get("precheck_cache_checked") and rewritten.lower().strip() == original.lower().strip():
        # Precheck already looked up the exact same query in semantic cache and missed;
        # bypass duplicate DB query & embedding call.
        return {"cache_hit": False}

    retriever: BaseRetriever = state.get("retriever") or get_default_retriever()
    vec_holder = {}
    response_text, sources, similarity = await retriever.acheck_cache(
        org_id=state.get("org_id"),
        chatbot_id=state.get("chatbot_id"),
        query=rewritten,
        knowledge_base_version=state.get("knowledge_base_version", 1),
        persona_version=state.get("persona_version", 1),
        threshold=settings.CACHE_SIMILARITY_THRESHOLD,
        out_query_vector=vec_holder,
    )
    if "vector" in vec_holder:
        state["rewritten_query_vector"] = vec_holder["vector"]

    if response_text:
        semantic_cache_requests_total.labels(result="hit").inc()
        if similarity is not None:
            semantic_cache_similarity_score.observe(similarity)
        return {
            "cache_hit": True,
            "response": response_text,
            "response_source": "semantic_cache",
            "cache_similarity": similarity,
            "sources": sources or [],
        }

    semantic_cache_requests_total.labels(result="miss").inc()
    return {"cache_hit": False}

