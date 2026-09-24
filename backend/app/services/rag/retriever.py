import structlog
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class BaseRetriever(ABC):
    """
    Abstract retriever seam decoupling the LangGraph pipeline from any direct database dependencies.
    Allows running the graph with Postgres (pgvector/hybrid) or pure In-Memory data.
    """

    @abstractmethod
    async def asearch(
        self,
        chatbot_id: str,
        query: str,
        top_k: int = 5,
        query_vector: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """Searches knowledge base for relevant chunks."""
        pass

    @abstractmethod
    async def acheck_cache(
        self,
        org_id: str,
        chatbot_id: str,
        query: str,
        knowledge_base_version: int = 1,
        persona_version: int = 1,
        threshold: Optional[float] = None,
        query_vector: Optional[List[float]] = None,
        out_query_vector: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]], Optional[float]]:
        """
        Checks semantic cache.
        Returns: (response_text, source_chunks, similarity_score) or (None, None, None)
        """
        pass


class PostgresRetriever(BaseRetriever):
    """
    Production retriever adapter backed by PostgreSQL (pgvector + BM25 TSVECTOR).
    Reuses the caller's active AsyncSession to prevent Supabase connection pool starvation.
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def asearch(
        self,
        chatbot_id: str,
        query: str,
        top_k: int = 5,
        query_vector: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        from app.services.vector_store import VectorStoreService

        if self.db is not None:
            return await VectorStoreService.asearch_hybrid(
                chatbot_id=chatbot_id,
                query=query,
                top_k=top_k,
                query_vector=query_vector,
                db=self.db,
            )

        # Fallback to local session context if no session was injected
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            return await VectorStoreService.asearch_hybrid(
                chatbot_id=chatbot_id,
                query=query,
                top_k=top_k,
                query_vector=query_vector,
                db=session,
            )

    async def acheck_cache(
        self,
        org_id: str,
        chatbot_id: str,
        query: str,
        knowledge_base_version: int = 1,
        persona_version: int = 1,
        threshold: Optional[float] = None,
        query_vector: Optional[List[float]] = None,
        out_query_vector: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]], Optional[float]]:
        from app.core.config import settings
        from app.services.semantic_cache import SemanticCacheService
        from app.services.vector_store import VectorStoreService

        thresh = threshold if threshold is not None else settings.CACHE_SIMILARITY_THRESHOLD

        if self.db is not None:
            resp, chunk_ids, sim = await SemanticCacheService.acheck_cache(
                org_id=org_id,
                chatbot_id=chatbot_id,
                rewritten_query=query,
                knowledge_base_version=knowledge_base_version,
                persona_version=persona_version,
                threshold=thresh,
                db=self.db,
                query_vector=query_vector,
                out_query_vector=out_query_vector,
            )
            sources = []
            if resp and chunk_ids:
                sources = await VectorStoreService.afetch_sources_by_chunk_ids(
                    chatbot_id=chatbot_id,
                    chunk_ids=chunk_ids,
                    db=self.db,
                )
            return resp, sources, sim

        # Fallback to local session context if no session was injected
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            resp, chunk_ids, sim = await SemanticCacheService.acheck_cache(
                org_id=org_id,
                chatbot_id=chatbot_id,
                rewritten_query=query,
                knowledge_base_version=knowledge_base_version,
                persona_version=persona_version,
                threshold=thresh,
                db=session,
                query_vector=query_vector,
                out_query_vector=out_query_vector,
            )
            sources = []
            if resp and chunk_ids:
                sources = await VectorStoreService.afetch_sources_by_chunk_ids(
                    chatbot_id=chatbot_id,
                    chunk_ids=chunk_ids,
                    db=session,
                )
            return resp, sources, sim


class InMemoryRetriever(BaseRetriever):
    """
    Pure in-memory retriever for unit tests, offline evaluations, and mock runs.
    Operates with zero database connection dependencies.
    """

    def __init__(
        self,
        chunks: Optional[List[Dict[str, Any]]] = None,
        cache_entries: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.chunks = chunks or []
        self.cache_entries = cache_entries or {}

    def add_chunk(self, chunk_id: str, text: str, source_id: str = "doc_1", score: float = 1.0):
        self.chunks.append({
            "chunk_id": chunk_id,
            "source_id": source_id,
            "text": text,
            "score": score,
            "dense_distance": 0.1,
            "retrieval_channels": ["in_memory"],
        })

    def add_cache_entry(self, query: str, response: str, sources: Optional[List[Dict[str, Any]]] = None, similarity: float = 1.0):
        self.cache_entries[query.lower().strip()] = {
            "response": response,
            "sources": sources or [],
            "similarity": similarity,
        }

    async def asearch(
        self,
        chatbot_id: str,
        query: str,
        top_k: int = 5,
        query_vector: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        query_words = set(query_lower.split())

        def score_chunk(c: Dict[str, Any]) -> float:
            text_words = set(c.get("text", "").lower().split())
            overlap = len(query_words & text_words)
            return overlap / max(len(query_words), 1)

        sorted_chunks = sorted(self.chunks, key=score_chunk, reverse=True)
        return sorted_chunks[:top_k]

    async def acheck_cache(
        self,
        org_id: str,
        chatbot_id: str,
        query: str,
        knowledge_base_version: int = 1,
        persona_version: int = 1,
        threshold: Optional[float] = None,
        query_vector: Optional[List[float]] = None,
        out_query_vector: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]], Optional[float]]:
        entry = self.cache_entries.get(query.lower().strip())
        if entry:
            return entry["response"], entry["sources"], entry.get("similarity", 1.0)
        return None, None, None


_default_retriever = None


def get_default_retriever() -> BaseRetriever:
    """Returns default unattached PostgresRetriever for standalone/eval runs."""
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = PostgresRetriever()
    return _default_retriever
