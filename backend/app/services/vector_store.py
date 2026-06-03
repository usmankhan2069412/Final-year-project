import numpy as np
import re
import logging
import uuid
from collections import OrderedDict
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

class VectorStoreService:
    # BM25 in-memory cache: evicts oldest entry when over _BM25_CACHE_MAXSIZE
    _bm25_cache: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    _BM25_CACHE_MAXSIZE = 100

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
            faiss_vectors = np.array(vectors, dtype=np.float32)
            if faiss_vectors.ndim != 2:
                raise ValueError("vectors must be a 2-dimensional array")

            # Update each chunk in the database with its embedding vector
            for i, chunk_id in enumerate(chunk_ids):
                chunk_uuid = uuid.UUID(chunk_id) if isinstance(chunk_id, str) else chunk_id
                chunk = db.query(KnowledgeChunk).filter(KnowledgeChunk.id == chunk_uuid).first()
                if chunk:
                    # Convert numpy array to list for pgvector compatibility
                    chunk.embedding = faiss_vectors[i].tolist()
                    db.add(chunk)

            if close_db:
                db.commit()
            else:
                db.flush()
                
            cls._bm25_cache.pop(str(chatbot_id), None)
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
        cls._bm25_cache.pop(str(chatbot_id), None)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    @classmethod
    def _get_bm25_index(cls, chatbot_id: str, chunk_ids: List[str], chunk_texts: Dict[str, str]):
        from rank_bm25 import BM25Okapi

        corpus = []
        for cid in chunk_ids:
            text = chunk_texts.get(cid)
            if not text:
                continue
            tokens = cls._tokenize(text)
            if tokens:
                corpus.append((cid, tokens))

        if not corpus:
            return [], None

        signature = tuple((cid, len(chunk_texts.get(cid, "")), hash(chunk_texts.get(cid, ""))) for cid, _ in corpus)
        cached = cls._bm25_cache.get(str(chatbot_id))
        if cached and cached.get("signature") == signature:
            return cached["corpus_ids"], cached["bm25"]

        corpus_ids = [cid for cid, _ in corpus]
        corpus_tokens = [tokens for _, tokens in corpus]
        bm25 = BM25Okapi(corpus_tokens)
        cls._bm25_cache[str(chatbot_id)] = {
            "signature": signature,
            "corpus_ids": corpus_ids,
            "bm25": bm25,
        }
        # LRU eviction: remove oldest entry if over size limit
        if len(cls._bm25_cache) > cls._BM25_CACHE_MAXSIZE:
            cls._bm25_cache.popitem(last=False)
        return corpus_ids, bm25

    @classmethod
    def search_hybrid(cls, chatbot_id: str, query: str, top_k: int = 5, db: Session = None) -> List[Dict[str, Any]]:
        """
        Runs hybrid search combining pgvector (Dense) and BM25 (Sparse) with Reciprocal Rank Fusion (RRF).
        """
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            from app.models.document import KnowledgeChunk

            chatbot_uuid = uuid.UUID(chatbot_id) if isinstance(chatbot_id, str) else chatbot_id

            # Fetch all chunks for this chatbot to build the BM25 index and map IDs to text/sources
            all_chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.chatbot_id == chatbot_uuid).all()
            if not all_chunks:
                return []

            chunk_ids = [str(c.id) for c in all_chunks]
            chunk_texts = {str(c.id): c.chunk_text for c in all_chunks}
            source_map = {str(c.id): str(c.source_id) for c in all_chunks}

            # --- DENSE RETRIEVAL (pgvector) ---
            from app.services.embedding import embedding_service
            query_vector = embedding_service.encode([query])[0]
            
            # Convert numpy array/list for query
            query_list = query_vector.tolist() if hasattr(query_vector, "tolist") else list(query_vector)

            # Retrieve top candidates using pgvector cosine_distance
            candidate_count = min(len(all_chunks), top_k * 4)
            dense_records = (
                db.query(KnowledgeChunk)
                .filter(KnowledgeChunk.chatbot_id == chatbot_uuid)
                .filter(KnowledgeChunk.embedding != None)
                .order_by(KnowledgeChunk.embedding.cosine_distance(query_list))
                .limit(candidate_count)
                .all()
            )
            dense_results = [str(r.id) for r in dense_records]

            # --- SPARSE RETRIEVAL BM25 ---
            sparse_results = []
            corpus_ids, bm25 = cls._get_bm25_index(chatbot_id, chunk_ids, chunk_texts)
            if bm25:
                query_tokens = cls._tokenize(query)
                scores = bm25.get_scores(query_tokens)
                
                # Pair IDs with scores, filter out zero/negative scores
                scored_ids = [(cid, score) for cid, score in zip(corpus_ids, scores) if score > 0]
                scored_ids.sort(key=lambda x: x[1], reverse=True)
                sparse_results = [x[0] for x in scored_ids[:candidate_count]]

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

            # Build final response structure
            results = []
            for cid, rrf_score in top_chunks:
                source_id = source_map.get(cid)
                text_val = chunk_texts.get(cid, "")
                results.append({
                    "chunk_id": cid,
                    "source_id": source_id,
                    "text": text_val,
                    "score": float(rrf_score)
                })
                
            return results

        except Exception as e:
            logger.error(f"pgvector_hybrid_search_failed for chatbot {chatbot_id}: {e}", exc_info=True)
            return []
        finally:
            if close_db:
                db.close()
