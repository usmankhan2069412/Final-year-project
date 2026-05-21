import os
import faiss
import numpy as np
import json
from typing import List, Dict, Any
from app.core.config import settings

class VectorStoreService:
    @staticmethod
    def _get_index_paths(chatbot_id: str):
        chatbot_dir = os.path.join(settings.FAISS_DIR, str(chatbot_id))
        os.makedirs(chatbot_dir, exist_ok=True)
        index_file = os.path.join(chatbot_dir, "index.faiss")
        meta_file_json = os.path.join(chatbot_dir, "metadata.json")
        return index_file, meta_file_json

    @classmethod
    def load_index(cls, chatbot_id: str):
        index_file, meta_file_json = cls._get_index_paths(chatbot_id)
        if os.path.exists(index_file):
            index = faiss.read_index(index_file)
            metadata = None
            if os.path.exists(meta_file_json):
                with open(meta_file_json, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            if metadata is not None:
                # Ensure compatibility with older structure
                if "chunk_texts" not in metadata:
                    metadata["chunk_texts"] = {}
                return index, metadata
        
        index = faiss.IndexFlatIP(settings.EMBEDDING_DIM)
        return index, {"ids": [], "source_map": {}, "chunk_texts": {}}

    @classmethod
    def save_index(cls, chatbot_id: str, index, metadata):
        index_file, meta_file_json = cls._get_index_paths(chatbot_id)
        faiss.write_index(index, index_file)
        with open(meta_file_json, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    @classmethod
    def add_vectors(cls, chatbot_id: str, vectors: np.ndarray, chunk_ids: List[str], source_id: str, chunk_texts: List[str]):
        index, metadata = cls.load_index(chatbot_id)
        
        faiss_vectors = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(faiss_vectors)
        
        index.add(faiss_vectors)
        
        if "chunk_texts" not in metadata:
            metadata["chunk_texts"] = {}
            
        for i, chunk_id in enumerate(chunk_ids):
            metadata["ids"].append(chunk_id)
            metadata["source_map"][chunk_id] = str(source_id)
            metadata["chunk_texts"][chunk_id] = chunk_texts[i]
            
        cls.save_index(chatbot_id, index, metadata)

    @classmethod
    def remove_by_source(cls, chatbot_id: str, source_id: str):
        index, metadata = cls.load_index(chatbot_id)
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
            cls.save_index(chatbot_id, new_index, {"ids": [], "source_map": {}, "chunk_texts": {}})
            return
 
        vectors = []
        for idx in keep_indices:
            vectors.append(index.reconstruct(idx))
            
        new_index = faiss.IndexFlatIP(settings.EMBEDDING_DIM)
        new_vectors = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(new_vectors)
        new_index.add(new_vectors)
        
        cls.save_index(chatbot_id, new_index, {
            "ids": new_ids, 
            "source_map": new_source_map, 
            "chunk_texts": new_chunk_texts
        })

    @classmethod
    def search_hybrid(cls, chatbot_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Runs hybrid search combining FAISS (Dense) and BM25 (Sparse) with Reciprocal Rank Fusion (RRF).
        """
        # Load index and metadata
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
        from rank_bm25 import BM25Okapi
        import re
        
        def tokenize(text: str) -> List[str]:
            return re.findall(r'\w+', text.lower())

        # Build BM25 index on the fly from metadata
        corpus_ids = [cid for cid in chunk_ids if cid in chunk_texts]
        corpus_tokens = [tokenize(chunk_texts[cid]) for cid in corpus_ids]
        
        sparse_results = []
        if corpus_tokens:
            bm25 = BM25Okapi(corpus_tokens)
            query_tokens = tokenize(query)
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

