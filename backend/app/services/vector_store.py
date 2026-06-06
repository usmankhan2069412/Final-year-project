import numpy as np
import logging
import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

class VectorStoreService:
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
            for i, chunk_id in enumerate(chunk_ids):
                chunk_uuid = uuid.UUID(chunk_id) if isinstance(chunk_id, str) else chunk_id
                chunk = db.query(KnowledgeChunk).filter(KnowledgeChunk.id == chunk_uuid).first()
                if chunk:
                    # Convert numpy array to list for pgvector compatibility
                    chunk.embedding = np_vectors[i].tolist()
                    db.add(chunk)

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
    def remove_by_source(cls, chatbot_id: str, source_id: str):
        # No-op: handled automatically by database foreign keys and cascades
        pass

    @classmethod
    def search_hybrid(cls, chatbot_id: str, query: str, top_k: int = 5, db: Session = None) -> List[Dict[str, Any]]:
        """
        Runs hybrid search combining pgvector (Dense) and PostgreSQL TSVECTOR (Sparse) with Reciprocal Rank Fusion (RRF).
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            from app.models.document import KnowledgeChunk

            chatbot_uuid = uuid.UUID(chatbot_id) if isinstance(chatbot_id, str) else chatbot_id

            candidate_count = top_k * 4

            # --- DENSE RETRIEVAL (pgvector) ---
            from app.services.embedding import embedding_service
            query_vector = embedding_service.encode([query])[0]
            
            # Convert numpy array/list for query
            query_list = query_vector.tolist() if hasattr(query_vector, "tolist") else list(query_vector)

            # Retrieve top candidates using pgvector cosine_distance
            dense_records = (
                db.query(KnowledgeChunk.id)
                .filter(KnowledgeChunk.chatbot_id == chatbot_uuid)
                .filter(KnowledgeChunk.embedding != None)
                .order_by(KnowledgeChunk.embedding.cosine_distance(query_list))
                .limit(candidate_count)
                .all()
            )
            dense_results = [str(r.id) for r in dense_records]

            # --- SPARSE RETRIEVAL (PostgreSQL TSVECTOR) ---
            ts_query = func.websearch_to_tsquery('simple', query)
            sparse_records = (
                db.query(KnowledgeChunk.id)
                .filter(KnowledgeChunk.chatbot_id == chatbot_uuid)
                .filter(KnowledgeChunk.text_search_vector.op('@@')(ts_query))
                .order_by(func.ts_rank_cd(KnowledgeChunk.text_search_vector, ts_query).desc())
                .limit(candidate_count)
                .all()
            )
            sparse_results = [str(r.id) for r in sparse_records]

            # --- RECIPROCAL RANK FUSION (RRF) ---
            rrf_scores = {}
            RRF_K = 60
            
            for rank, cid in enumerate(dense_results):
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (RRF_K + rank + 1))
                
            for rank, cid in enumerate(sparse_results):
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (RRF_K + rank + 1))

            # Sort by RRF score descending
            sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
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
                        "score": float(rrf_score)
                    })
                
            return results

        except Exception as e:
            logger.error(f"pgvector_hybrid_search_failed for chatbot {chatbot_id}: {e}", exc_info=True)
            return []
        finally:
            if close_db:
                db.close()
