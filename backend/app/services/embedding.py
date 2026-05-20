import logging
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self._model = None

    def get_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
            # Load model with trust_remote_code=True for Qwen architecture
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL, trust_remote_code=True)
            logger.info("Embedding model loaded successfully.")
        return self._model

    def encode(self, texts: List[str]) -> np.ndarray:
        model = self.get_model()
        return model.encode(texts, show_progress_bar=False)

embedding_service = EmbeddingService()
