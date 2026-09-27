import os
import structlog
from typing import Dict, Any

from app.core.config import settings
from app.core.metrics import rerank_fallback_total
from app.services.rag.helpers import (
    get_async_http_client,
    filter_hybrid_relevant_sources,
    context_from_sources,
)
from app.services.rag.state import AgentState

logger = structlog.get_logger(__name__)


async def validate_node(state: AgentState) -> Dict[str, Any]:
    """
    Reranks and validates retrieved context chunks using Cohere rerank API via OpenRouter.
    Falls back to hybrid (semantic dense_distance + lexical overlap) filtering if API fails or key is missing.
    """
    sources = state.get("sources", [])
    if not sources:
        logger.info("validation_result", is_relevant=False, chunks_before=0, chunks_after=0)
        return {"is_relevant": False, "context_text": ""}

    query = state.get("rewritten_query") or state.get("user_message", "")

    # Use OpenRouter API key for Cohere reranking via OpenRouter
    rerank_api_key = (
        getattr(settings, "OPENROUTER_API_KEY", None)
        or os.getenv("OPENROUTER_API_KEY")
        or getattr(settings, "COHERE_API_KEY", None)
        or os.getenv("COHERE_API_KEY")
    )

    if not rerank_api_key:
        filtered_sources = filter_hybrid_relevant_sources(query, sources)
        is_rel = bool(filtered_sources)
        ctx_text = context_from_sources(filtered_sources)
        logger.info(
            "validation_result",
            is_relevant=is_rel,
            chunks_before=len(sources),
            chunks_after=len(filtered_sources),
            method="hybrid_local",
        )
        return {
            "is_relevant": is_rel,
            "sources": filtered_sources,
            "context_text": ctx_text if is_rel else "",
            "validated_chunks_count": len(filtered_sources),
        }

    try:
        documents = [src["text"] for src in sources]
        payload = {
            "model": "cohere/rerank-v3.5",
            "query": query,
            "documents": documents,
            "top_n": len(documents),
        }
        headers = {
            "Authorization": f"Bearer {rerank_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://aina.ai",
            "X-Title": "Aina AI",
        }

        client = get_async_http_client()
        rerank_timeout = getattr(settings, "RERANK_TIMEOUT_SECS", 6.0)
        response = await client.post(
            "https://openrouter.ai/api/v1/rerank",
            json=payload,
            headers=headers,
            timeout=rerank_timeout,
        )
        response.raise_for_status()
        result = response.json()

        filtered_sources = []

        if "results" in result:
            sorted_results = sorted(result["results"], key=lambda x: x.get("relevance_score", 0), reverse=True)
            for item in sorted_results:
                score = item.get("relevance_score", 0)
                idx = item.get("index")

                if score >= settings.RERANK_THRESHOLD and idx is not None and 0 <= idx < len(sources):
                    source = dict(sources[idx])
                    source["rerank_score"] = float(score)
                    filtered_sources.append(source)

        if not filtered_sources:
            logger.info("validation_result", is_relevant=False, chunks_before=len(sources), chunks_after=0)
            return {"is_relevant": False, "sources": [], "context_text": ""}

        new_context_text = context_from_sources(filtered_sources)

        logger.info(
            "validation_result",
            is_relevant=True,
            chunks_before=len(sources),
            chunks_after=len(filtered_sources),
        )
        return {
            "is_relevant": True,
            "sources": filtered_sources,
            "context_text": new_context_text,
            "validated_chunks_count": len(filtered_sources),
        }
    except Exception as e:
        import httpx
        is_timeout = isinstance(e, httpx.TimeoutException) or "timed out" in str(e).lower()
        reason = "timeout" if is_timeout else "api_error"
        rerank_fallback_total.labels(reason=reason).inc()
        logger.warning("validate_node_rerank_fallback", reason=reason, error=str(e))
        # Fall back to hybrid (semantic + lexical) relevance check
        filtered_sources = filter_hybrid_relevant_sources(query, sources)
        is_rel = bool(filtered_sources)
        ctx_text = context_from_sources(filtered_sources)
        logger.info(
            "validation_result",
            is_relevant=is_rel,
            chunks_before=len(sources),
            chunks_after=len(filtered_sources),
            fallback_hybrid=True,
        )
        return {
            "is_relevant": is_rel,
            "sources": filtered_sources,
            "context_text": ctx_text if is_rel else "",
            "validated_chunks_count": len(filtered_sources) if is_rel else 0,
        }
