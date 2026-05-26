import logging
import time
from typing import List
import numpy as np
from app.core.config import settings

try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self._client = None
        self._delay_seconds = 4  # 15 requests per minute = 1 request every 4 seconds roughly

    def get_client(self):
        if genai is None:
            raise ImportError("google-genai package is not installed.")
        if self._client is None:
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not set in environment variables.")
            logger.info("Initializing Gemini API client for embeddings.")
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def encode(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.array([])
            
        client = self.get_client()
        all_embeddings = []
        
        logger.info(f"Generating embeddings for {len(texts)} chunks using {settings.EMBEDDING_MODEL}...")
        
        # Process chunks one by one to ensure 1 vector per chunk
        for i, text in enumerate(texts):
            retries = 3
            while retries > 0:
                try:
                    result = client.models.embed_content(
                        model=settings.EMBEDDING_MODEL,
                        contents=text
                    )
                    all_embeddings.append(result.embeddings[0].values)
                    break
                except Exception as e:
                    if "429" in str(e):
                        logger.warning(f"Rate limit hit at chunk {i}, sleeping for 5 seconds...")
                        time.sleep(5)
                        retries -= 1
                        if retries == 0:
                            raise
                    else:
                        logger.error(f"Failed to generate embeddings for chunk {i}: {e}")
                        raise
                        
        return np.array(all_embeddings, dtype=np.float32)

embedding_service = EmbeddingService()
