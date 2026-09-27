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
        # bypass duplicate DB query & embedding call, preserving the vector.
        cached_vec = state.get("original_query_vector") or state.get("query_vector")
        return {
            "cache_hit": False,
            "original_query_vector": cached_vec,
            "rewritten_query_vector": cached_vec,
            "query_vector": cached_vec,
        }

    retriever: BaseRetriever = state.get("retriever") or get_default_retriever()
    vec_holder = {}
    cached_vec = state.get("original_query_vector") if rewritten.lower().strip() == original.lower().strip() else None
    response_text, sources, similarity = await retriever.acheck_cache(
        org_id=state.get("org_id"),
        chatbot_id=state.get("chatbot_id"),
        query=rewritten,
        knowledge_base_version=state.get("knowledge_base_version", 1),
        persona_version=state.get("persona_version", 1),
        threshold=settings.CACHE_SIMILARITY_THRESHOLD,
        query_vector=cached_vec,
        out_query_vector=vec_holder,
    )
    new_vec = vec_holder.get("vector") or cached_vec

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
            "query_vector": new_vec,
        }

    semantic_cache_requests_total.labels(result="miss").inc()
    return {
        "cache_hit": False,
        "original_query_vector": state.get("original_query_vector"),
        "rewritten_query_vector": new_vec,
        "query_vector": new_vec or state.get("original_query_vector"),
    }

