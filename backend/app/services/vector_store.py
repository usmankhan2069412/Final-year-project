import os
import faiss
import numpy as np
import pickle
from typing import List, Dict, Any
from app.core.config import settings

class VectorStoreService:
    @staticmethod
    def _get_index_paths(chatbot_id: str):
        chatbot_dir = os.path.join(settings.FAISS_DIR, str(chatbot_id))
        os.makedirs(chatbot_dir, exist_ok=True)
        index_file = os.path.join(chatbot_dir, "index.faiss")
        meta_file = os.path.join(chatbot_dir, "metadata.pkl")
        return index_file, meta_file

    @classmethod
    def load_index(cls, chatbot_id: str):
        index_file, meta_file = cls._get_index_paths(chatbot_id)
        if os.path.exists(index_file) and os.path.exists(meta_file):
            index = faiss.read_index(index_file)
            with open(meta_file, "rb") as f:
                metadata = pickle.load(f)
            # Ensure compatibility with older structure
            if "chunk_texts" not in metadata:
                metadata["chunk_texts"] = {}
            return index, metadata
        
        index = faiss.IndexFlatIP(settings.EMBEDDING_DIM)
        return index, {"ids": [], "source_map": {}, "chunk_texts": {}}

    @classmethod
    def save_index(cls, chatbot_id: str, index, metadata):
        index_file, meta_file = cls._get_index_paths(chatbot_id)
        faiss.write_index(index, index_file)
        with open(meta_file, "wb") as f:
            pickle.dump(metadata, f)

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
