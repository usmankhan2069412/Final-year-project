import os
import faiss
import numpy as np
import json
import re
import structlog
from collections import OrderedDict
from contextlib import contextmanager
from typing import List, Dict, Any
from app.core.config import settings

logger = structlog.get_logger()

class VectorStoreService:
    # BM25 in-memory cache: evicts oldest entry when over _BM25_CACHE_MAXSIZE
    _bm25_cache: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    _BM25_CACHE_MAXSIZE = 100

    # FAISS in-process cache: keyed on (chatbot_id -> (mtime, index, metadata))
    # Reloads from disk only when the index file's mtime changes.
    _index_cache: Dict[str, tuple] = {}

    @staticmethod
    def _get_index_paths(chatbot_id: str):
        chatbot_dir = os.path.join(settings.FAISS_DIR, str(chatbot_id))
        os.makedirs(chatbot_dir, exist_ok=True)
        index_file = os.path.join(chatbot_dir, "index.faiss")
        meta_file_json = os.path.join(chatbot_dir, "metadata.json")
        lock_file = os.path.join(chatbot_dir, ".index.lock")
        return index_file, meta_file_json, lock_file

    @staticmethod
    @contextmanager
    def _index_lock(lock_file: str):
        os.makedirs(os.path.dirname(lock_file), exist_ok=True)
        handle = open(lock_file, "a+", encoding="utf-8")
        try:
            try:
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            except ImportError:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            try:
                try:
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                except ImportError:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()

    @classmethod
    def load_index(cls, chatbot_id: str):
        index_file, meta_file_json, _ = cls._get_index_paths(chatbot_id)
        if os.path.exists(index_file):
            try:
                mtime = os.stat(index_file).st_mtime
                cached = cls._index_cache.get(str(chatbot_id))
                if cached and cached[0] == mtime:
                    return cached[1], cached[2]
                index = faiss.read_index(index_file)
                metadata = None
                if os.path.exists(meta_file_json):
                    with open(meta_file_json, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                if metadata is not None:
                    # Ensure compatibility with older structure
                    if "chunk_texts" not in metadata:
                        metadata["chunk_texts"] = {}
                    cls._index_cache[str(chatbot_id)] = (mtime, index, metadata)
                    return index, metadata
            except Exception as e:
                logger.error("faiss_index_load_failed", chatbot_id=chatbot_id, error=str(e), exc_info=True)
                # Fall back to empty index to avoid crashing client chat

        index = faiss.IndexFlatIP(settings.EMBEDDING_DIM)
        return index, {"ids": [], "source_map": {}, "chunk_texts": {}}

    @classmethod
    def save_index(cls, chatbot_id: str, index, metadata):
        index_file, meta_file_json, lock_file = cls._get_index_paths(chatbot_id)
        with cls._index_lock(lock_file):
            cls._save_index_unlocked(index_file, meta_file_json, index, metadata)
            cls._bm25_cache.pop(str(chatbot_id), None)
            cls._index_cache.pop(str(chatbot_id), None)  # invalidate stale cached index

    @staticmethod
    def _save_index_unlocked(index_file: str, meta_file_json: str, index, metadata):
        tmp_index = index_file + ".tmp"
        tmp_meta = meta_file_json + ".tmp"
        faiss.write_index(index, tmp_index)
        with open(tmp_meta, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        os.replace(tmp_index, index_file)
        os.replace(tmp_meta, meta_file_json)

    @classmethod
    def add_vectors(cls, chatbot_id: str, vectors: np.ndarray, chunk_ids: List[str], source_id: str, chunk_texts: List[str]):
        if not chunk_ids:
            return
        if len(chunk_ids) != len(chunk_texts):
            raise ValueError("chunk_ids and chunk_texts must have the same length")

        _, _, lock_file = cls._get_index_paths(chatbot_id)
        with cls._index_lock(lock_file):
            index, metadata = cls.load_index(chatbot_id)
            faiss_vectors = np.array(vectors, dtype=np.float32)
            if faiss_vectors.ndim != 2:
                raise ValueError("vectors must be a 2-dimensional array")
            if faiss_vectors.shape[0] != len(chunk_ids):
                raise ValueError("vector count must match chunk count")
            if faiss_vectors.shape[1] != settings.EMBEDDING_DIM:
                raise ValueError(f"embedding dimension mismatch: expected {settings.EMBEDDING_DIM}, got {faiss_vectors.shape[1]}")
            faiss.normalize_L2(faiss_vectors)
            index.add(faiss_vectors)
            if "chunk_texts" not in metadata:
                metadata["chunk_texts"] = {}
            for i, chunk_id in enumerate(chunk_ids):
                metadata["ids"].append(chunk_id)
                metadata["source_map"][chunk_id] = str(source_id)
                metadata["chunk_texts"][chunk_id] = chunk_texts[i]
            index_file, meta_file_json, _ = cls._get_index_paths(chatbot_id)
            cls._save_index_unlocked(index_file, meta_file_json, index, metadata)
            cls._bm25_cache.pop(str(chatbot_id), None)
            cls._index_cache.pop(str(chatbot_id), None)  # invalidate stale cached index

    @classmethod
    def remove_by_source(cls, chatbot_id: str, source_id: str):
        _, _, lock_file = cls._get_index_paths(chatbot_id)
        with cls._index_lock(lock_file):
            index, metadata = cls.load_index(chatbot_id)
            cls._remove_by_source_locked(chatbot_id, source_id, index, metadata)
            cls._bm25_cache.pop(str(chatbot_id), None)
            cls._index_cache.pop(str(chatbot_id), None)  # invalidate stale cached index

    @classmethod
    def _remove_by_source_locked(cls, chatbot_id: str, source_id: str, index, metadata):
        if index.ntotal == 0:
            return
            
        keep_indices = []
        new_ids = []
        new_source_map = {}
        new_chunk_texts = {}
        
        old_chunk_texts = metadata.get("chunk_texts", {})
        
        for idx, chunk_id in enumerate(metadata["ids"]):
            if metadata["source_map"].get(chunk_id) != str(source_id):
                keep_indices.append(idx)
                new_ids.append(chunk_id)
                new_source_map[chunk_id] = metadata["source_map"][chunk_id]
                if chunk_id in old_chunk_texts:
                    new_chunk_texts[chunk_id] = old_chunk_texts[chunk_id]
        
        if len(keep_indices) == index.ntotal:
            return
            
        if not keep_indices:
            new_index = faiss.IndexFlatIP(settings.EMBEDDING_DIM)
            index_file, meta_file_json, _ = cls._get_index_paths(chatbot_id)
            cls._save_index_unlocked(index_file, meta_file_json, new_index, {"ids": [], "source_map": {}, "chunk_texts": {}})
            return
 
        vectors = []
        for idx in keep_indices:
            vectors.append(index.reconstruct(idx))
            
        new_index = faiss.IndexFlatIP(settings.EMBEDDING_DIM)
        new_vectors = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(new_vectors)
        new_index.add(new_vectors)
        
        index_file, meta_file_json, _ = cls._get_index_paths(chatbot_id)
        cls._save_index_unlocked(index_file, meta_file_json, new_index, {
            "ids": new_ids, 
            "source_map": new_source_map, 
            "chunk_texts": new_chunk_texts
        })

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
    def search_hybrid(cls, chatbot_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Runs hybrid search combining FAISS (Dense) and BM25 (Sparse) with Reciprocal Rank Fusion (RRF).
        """
        # Load a consistent snapshot while writers are excluded.
        _, _, lock_file = cls._get_index_paths(chatbot_id)
        with cls._index_lock(lock_file):
            index, metadata = cls.load_index(chatbot_id)
        if index.ntotal == 0 or not metadata.get("ids"):
            return []

        chunk_ids = metadata["ids"]
        chunk_texts = metadata.get("chunk_texts", {})
        
        # Ensure we have chunks
        if not chunk_texts:
            return []

        # --- DENSE RETRIEVAL FAISS ---
        from app.services.embedding import embedding_service
        query_vector = embedding_service.encode([query])[0]
        
        q_vec = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(q_vec)
        
        # Retrieve candidates
        candidate_count = min(index.ntotal, top_k * 4)
        distances, indices = index.search(q_vec, candidate_count)
        
        dense_results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1 or idx >= len(chunk_ids):
                continue
            cid = chunk_ids[idx]
            dense_results.append(cid)

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
            source_id = metadata["source_map"].get(cid)
            text_val = chunk_texts.get(cid, "")
            results.append({
                "chunk_id": cid,
                "source_id": source_id,
                "text": text_val,
                "score": float(rrf_score)
            })
            
        return results
