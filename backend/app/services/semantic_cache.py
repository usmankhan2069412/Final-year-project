import hashlib
import logging
from typing import Optional, Tuple, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.semantic_cache import SemanticCache
from app.services.embedding import embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class SemanticCacheService:
    
    @classmethod
    def generate_query_hash(cls, query: str) -> str:
        """Generates a stable SHA256 hash of a normalized query."""
        normalized = query.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()

    @classmethod
    def check_cache(
        cls, 
        org_id: str, 
        chatbot_id: str, 
        rewritten_query: str, 
        knowledge_base_version: int, 
        persona_version: int,
        threshold: Optional[float] = None,
        db: Optional[Session] = None
    ) -> Tuple[Optional[str], Optional[List[str]], Optional[float]]:
        """
        Checks the semantic cache for a similar rewritten query.
        Returns (response_text, source_chunk_ids, similarity_score) or (None, None, None).
        """
        if threshold is None:
            threshold = settings.CACHE_SIMILARITY_THRESHOLD
        close_db = False
        if db is None:
            from app.db.session import SessionLocal
            db = SessionLocal()
            close_db = True

        try:
            query_vector = embedding_service.encode([rewritten_query])[0]
            query_list = query_vector.tolist() if hasattr(query_vector, "tolist") else list(query_vector)
            
            # Using pgvector cosine_distance (0 is identical, 2 is completely opposite)
            max_distance = 1.0 - threshold
            
            now = datetime.now(timezone.utc)

            # Compute cosine_distance inline so we get both the match
            # and the score in a single DB round-trip.
            distance_col = SemanticCache.query_embedding.cosine_distance(query_list).label("distance")
            row = (
                db.query(SemanticCache, distance_col)
                .filter(SemanticCache.org_id == org_id)
                .filter(SemanticCache.chatbot_id == chatbot_id)
                .filter(SemanticCache.is_active == True)
                .filter(SemanticCache.expires_at > now)
                .filter(SemanticCache.embedding_model == settings.EMBEDDING_MODEL)
                .filter(SemanticCache.knowledge_base_version == knowledge_base_version)
                .filter(SemanticCache.persona_version == persona_version)
                .filter(distance_col <= max_distance)
                .order_by(distance_col)
                .first()
            )
            
            if row:
                match, distance = row
                similarity_score = 1.0 - float(distance)
                
                match.hit_count += 1
                match.last_accessed_at = now
                db.commit()
                
                logger.info(f"Semantic Cache Hit for chatbot {chatbot_id} (score: {similarity_score:.4f})")
                return match.response_text, match.source_chunk_ids, similarity_score
                
            return None, None, None
            
        except Exception as e:
            logger.error(f"Failed to check semantic cache: {e}", exc_info=True)
            return None, None, None
        finally:
            if close_db:
                db.close()

    @classmethod
    def add_to_cache(
        cls, 
        org_id: str, 
        chatbot_id: str, 
        rewritten_query: str, 
        response_text: str, 
        knowledge_base_version: int, 
        persona_version: int,
        source_chunk_ids: Optional[List[str]] = None,
        source_document_ids: Optional[List[str]] = None,
        ttl_days: int = 7,
        db: Optional[Session] = None,
        query_vector: Optional[List[float]] = None
    ):
        """Adds a new successful RAG generation to the semantic cache."""
        close_db = False
        if db is None:
            from app.db.session import SessionLocal
            db = SessionLocal()
            close_db = True
            
        try:
            query_hash = cls.generate_query_hash(rewritten_query)
            
            # Embed the query if not already provided
            if query_vector is None:
                query_vector_res = embedding_service.encode([rewritten_query])[0]
                query_list = query_vector_res.tolist() if hasattr(query_vector_res, "tolist") else list(query_vector_res)
            else:
                query_list = query_vector
            
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(days=ttl_days)
            
            cache_entry = SemanticCache(
                org_id=org_id,
                chatbot_id=chatbot_id,
                query_text=rewritten_query,
                query_hash=query_hash,
                query_embedding=query_list,
                embedding_model=settings.EMBEDDING_MODEL,
                response_text=response_text,
                source_chunk_ids=source_chunk_ids,
                source_document_ids=source_document_ids,
                knowledge_base_version=knowledge_base_version,
                persona_version=persona_version,
                created_at=now,
                expires_at=expires_at
            )
            
            db.add(cache_entry)
            db.commit()
            logger.info(f"Added new entry to semantic cache for chatbot {chatbot_id}")
            
        except IntegrityError:
            # A duplicate entry was created by a concurrent request, which is totally fine.
            db.rollback()
            logger.debug(f"Semantic cache entry already exists (duplicate query hash) for chatbot {chatbot_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to add to semantic cache: {e}", exc_info=True)
        finally:
            if close_db:
                db.close()
