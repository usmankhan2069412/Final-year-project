import numpy as np
import logging
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

class VectorStoreService:
    # pgvector cosine distance is 0 for identical vectors and approaches 2 for
    # opposite vectors. This keeps dense retrieval from returning the "least bad"
    # chunk when the query is outside the knowledge base.
    DENSE_MAX_DISTANCE = 0.55

    @classmethod
    def add_vectors(cls, chatbot_id: str, vectors: np.ndarray, chunk_ids: List[str], source_id: str, chunk_texts: List[str], db: Session = None):
        if not chunk_ids:
            return

        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            from app.models.document import KnowledgeChunk
            np_vectors = np.array(vectors, dtype=np.float32)
            if np_vectors.ndim != 2:
                raise ValueError("vectors must be a 2-dimensional array")

            # Update each chunk in the database with its embedding vector
            chunk_uuids = [uuid.UUID(cid) if isinstance(cid, str) else cid for cid in chunk_ids]
            chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.id.in_(chunk_uuids)).all()
            chunk_map = {str(c.id): c for c in chunks}
            for i, chunk_id in enumerate(chunk_ids):
                chunk = chunk_map.get(str(chunk_id))
                if chunk:
                    chunk.embedding = np_vectors[i].tolist()

            if close_db:
                db.commit()
            else:
                db.flush()
                
            logger.info(f"Successfully saved vectors to pgvector database for chatbot {chatbot_id} (count: {len(chunk_ids)})")
        except Exception as e:
            logger.error(f"pgvector_add_vectors_failed for chatbot {chatbot_id}: {e}", exc_info=True)
            if close_db:
                db.rollback()
            raise
        finally:
            if close_db:
                db.close()

    @classmethod
    def fetch_sources_by_chunk_ids(
        cls,
        chatbot_id: str,
        chunk_ids: List[str],
        db: Session = None,
    ) -> List[Dict[str, Any]]:
        if not chunk_ids:
            return []

        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            from app.models.document import KnowledgeChunk, KnowledgeSource, ChunkStatus, SourceStatus

            chatbot_uuid = uuid.UUID(chatbot_id) if isinstance(chatbot_id, str) else chatbot_id
            ordered_ids = []
            for cid in chunk_ids:
                try:
                    ordered_ids.append(uuid.UUID(str(cid)))
                except ValueError:
                    continue

            if not ordered_ids:
                return []

            records = (
                db.query(KnowledgeChunk)
                .filter(KnowledgeChunk.chatbot_id == chatbot_uuid)
                .filter(KnowledgeChunk.id.in_(ordered_ids))
                .filter(KnowledgeChunk.index_status == ChunkStatus.COMPLETED)
                .all()
            )
            record_map = {record.id: record for record in records}

            results = []
            for cid in ordered_ids:
                record = record_map.get(cid)
                if record:
                    results.append({
                        "chunk_id": str(record.id),
                        "source_id": str(record.source_id),
                        "text": record.chunk_text,
                        "score": 1.0,
                        "dense_distance": None,
                        "sparse_rank": None,
                        "retrieval_channels": ["semantic_cache"],
                    })
            return results
        except Exception as e:
            logger.warning("fetch_sources_by_chunk_ids_failed for chatbot %s: %s", chatbot_id, e, exc_info=True)
            return []
        finally:
            if close_db:
                db.close()

    @classmethod
    def search_hybrid(
        cls,
        chatbot_id: str,
        query: str,
        top_k: int = 5,
        db: Session = None,
        dense_max_distance: float = DENSE_MAX_DISTANCE,
        query_vector: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Runs hybrid search combining pgvector (Dense) and PostgreSQL TSVECTOR (Sparse) with Reciprocal Rank Fusion (RRF).
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            from app.models.document import KnowledgeChunk, KnowledgeSource, ChunkStatus, SourceStatus

            query = (query or "").strip()
            if not query or top_k <= 0:
                return []
            chatbot_uuid = uuid.UUID(chatbot_id) if isinstance(chatbot_id, str) else chatbot_id

            candidate_count = max(top_k * 4, top_k)
            base_filters = (
                KnowledgeChunk.chatbot_id == chatbot_uuid,
                KnowledgeChunk.index_status == ChunkStatus.COMPLETED,
                KnowledgeSource.status == SourceStatus.INDEXED,
            )

            # --- DENSE RETRIEVAL (pgvector) ---
            dense_results = []
            dense_distances = {}
            try:
                from app.services.embedding import embedding_service
                if query_vector is None:
                    query_vector = embedding_service.encode([query])[0]
                    query_vector = query_vector.tolist() if hasattr(query_vector, "tolist") else list(query_vector)
                
                distance_expr = KnowledgeChunk.embedding.cosine_distance(query_vector)

                dense_query = (
                    db.query(KnowledgeChunk.id, distance_expr.label("distance"))
                    .join(KnowledgeSource, KnowledgeSource.id == KnowledgeChunk.source_id)
                    .filter(*base_filters)
                    .filter(KnowledgeChunk.embedding.isnot(None))
                )
                if dense_max_distance is not None:
                    dense_query = dense_query.filter(distance_expr <= dense_max_distance)

                dense_records = (
                    dense_query
                    .order_by(distance_expr)
                    .limit(candidate_count)
                    .all()
                )
                dense_results = [str(r.id) for r in dense_records]
                dense_distances = {str(r.id): float(r.distance) for r in dense_records}
            except Exception as e:
                logger.warning("dense_retrieval_failed for chatbot %s: %s", chatbot_id, e, exc_info=True)

            # --- SPARSE RETRIEVAL (PostgreSQL TSVECTOR) ---
            ts_query = func.websearch_to_tsquery('simple', query)
            sparse_records = (
                db.query(KnowledgeChunk.id)
                .join(KnowledgeSource, KnowledgeSource.id == KnowledgeChunk.source_id)
                .filter(*base_filters)
                .filter(KnowledgeChunk.text_search_vector.op('@@')(ts_query))
                .order_by(func.ts_rank_cd(KnowledgeChunk.text_search_vector, ts_query).desc())
                .limit(candidate_count)
                .all()
            )
            sparse_results = [str(r.id) for r in sparse_records]
            sparse_ranks = {cid: rank for rank, cid in enumerate(sparse_results)}

            # --- RECIPROCAL RANK FUSION (RRF) ---
            rrf_scores = {}
            channels = {}
            RRF_K = 60
            
            for rank, cid in enumerate(dense_results):
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (RRF_K + rank + 1))
                channels.setdefault(cid, []).append("dense")
                
            for rank, cid in enumerate(sparse_results):
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (RRF_K + rank + 1))
                channels.setdefault(cid, []).append("sparse")

            # Sort by RRF score descending
            sorted_chunks = sorted(
                rrf_scores.items(),
                key=lambda x: (x[1], -(dense_distances.get(x[0], 2.0))),
                reverse=True
            )
            top_chunks = sorted_chunks[:top_k]
            
            # Retrieve the actual text and source IDs for the final top chunks
            if not top_chunks:
                return []
                
            final_cids = [uuid.UUID(cid) for cid, _ in top_chunks]
            final_records = db.query(KnowledgeChunk).filter(KnowledgeChunk.id.in_(final_cids)).all()
            
            # Map for quick lookup
            record_map = {str(r.id): r for r in final_records}
            
            # Build final response structure maintaining the sorted order
            results = []
            for cid, rrf_score in top_chunks:
                chunk_record = record_map.get(cid)
                if chunk_record:
                    results.append({
                        "chunk_id": cid,
                        "source_id": str(chunk_record.source_id),
                        "text": chunk_record.chunk_text,
                        "score": float(rrf_score),
                        "dense_distance": dense_distances.get(cid),
                        "sparse_rank": sparse_ranks.get(cid),
                        "retrieval_channels": channels.get(cid, []),
                    })
                
            return results

        except Exception as e:
            logger.error(f"pgvector_hybrid_search_failed for chatbot {chatbot_id}: {e}", exc_info=True)
            return []
        finally:
            if close_db:
                db.close()
