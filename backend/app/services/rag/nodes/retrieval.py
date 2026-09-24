import structlog
from itertools import zip_longest
from typing import Dict, Any, List

from app.core.config import settings
from app.services.embedding import embedding_service
from app.services.rag.helpers import context_from_sources
from app.services.rag.retriever import BaseRetriever, get_default_retriever
from app.services.rag.state import AgentState

logger = structlog.get_logger(__name__)


async def retrieve_node(state: AgentState) -> Dict[str, Any]:
    """
    Hybrid vector + BM25 retrieval node.
    Supports single-query search or multi-query (original + rewritten) search with deduplication.
    Uses injected or default retriever seam for 100% database-independent execution.
    """
    rewritten = state.get("rewritten_query")
    original = state.get("user_message", "")
    chatbot_id = state.get("chatbot_id")
    retriever: BaseRetriever = state.get("retriever") or get_default_retriever()

    # If no rewrite or exactly the same, do a single search
    if not rewritten or rewritten.lower().strip() == original.lower().strip():
        query_list = state.get("original_query_vector") or state.get("rewritten_query_vector")
        if not query_list:
            try:
                query_vectors = await embedding_service.aencode([original], is_query=True)
                query_vector = query_vectors[0]
                query_list = query_vector.tolist() if hasattr(query_vector, "tolist") else list(query_vector)
            except Exception as e:
                logger.warning("retrieve_node_embedding_failed", error=str(e), query=original)
                query_list = None
        sources_list = await retriever.asearch(
            chatbot_id, original, top_k=settings.RETRIEVAL_TOP_K_SINGLE, query_vector=query_list
        )
        # Save vector for caching
        state["query_vector"] = query_list
    else:
        # Multi-Query Retrieval: search both and merge
        rewritten_vec = state.get("rewritten_query_vector")
        original_vec = state.get("original_query_vector")

        missing_texts = []
        if not rewritten_vec:
            missing_texts.append(rewritten)
        if not original_vec:
            missing_texts.append(original)

        if missing_texts:
            try:
                vectors = await embedding_service.aencode(missing_texts, is_query=True)
                idx = 0
                if not rewritten_vec:
                    rewritten_vec = vectors[idx].tolist() if hasattr(vectors[idx], "tolist") else list(vectors[idx])
                    idx += 1
                if not original_vec:
                    original_vec = vectors[idx].tolist() if hasattr(vectors[idx], "tolist") else list(vectors[idx])
            except Exception as e:
                logger.warning("retrieve_node_embedding_failed", error=str(e), missing_texts=missing_texts)

        # Save rewritten vector to state for caching
        state["query_vector"] = rewritten_vec

        sources_rewritten = await retriever.asearch(
            chatbot_id, rewritten, top_k=settings.RETRIEVAL_TOP_K_MULTI, query_vector=rewritten_vec
        )
        sources_original = await retriever.asearch(
            chatbot_id, original, top_k=settings.RETRIEVAL_TOP_K_MULTI, query_vector=original_vec
        )

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
    ctx_text = context_from_sources(sources)

    logger.info(
        "retrieval_complete",
        chatbot_id=chatbot_id,
        chunks=len(sources),
        used_multi_query=bool(rewritten and rewritten.lower().strip() != original.lower().strip()),
    )
    return {"sources": sources, "context_text": ctx_text}
