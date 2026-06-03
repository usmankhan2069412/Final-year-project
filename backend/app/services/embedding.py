import logging
import time
from typing import List
import numpy as np
from app.core.config import settings
from app.core.circuit_breaker import gemini_breaker
from app.core.metrics import embedding_errors_total

try:
    from google import genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

# Gemini embed_content supports up to 100 texts per batch call.
# Batching dramatically reduces API call count and ingestion time.
EMBEDDING_BATCH_SIZE = 100


class EmbeddingService:
    def __init__(self):
        self._client = None
        self._openrouter_client = None

    def get_client(self):
        if settings.OPENROUTER_API_KEY:
            if OpenAI is None:
                raise ImportError("openai package is not installed.")
            if self._openrouter_client is None:
                logger.info("Initializing OpenAI/OpenRouter client for embeddings.")
                self._openrouter_client = OpenAI(
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url=settings.OPENROUTER_BASE_URL
                )
            return self._openrouter_client

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

        if gemini_breaker.is_open:
            logger.error("gemini_embedding_circuit_breaker_open — skipping call.")
            embedding_errors_total.inc()
            raise RuntimeError("Gemini embedding API circuit is open due to recent failures.")

        client = self.get_client()
        all_embeddings = []

        logger.info(
            "Generating embeddings for %d chunks using %s (batch_size=%d)...",
            len(texts), settings.EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE
        )

        for batch_start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[batch_start:batch_start + EMBEDDING_BATCH_SIZE]
            retries = 3
            while retries > 0:
                try:
                    if settings.OPENROUTER_API_KEY:
                        response = client.embeddings.create(
                            model=settings.EMBEDDING_MODEL,
                            input=batch,
                            encoding_format="float"
                        )
                        for emb in response.data:
                            all_embeddings.append(emb.embedding)
                    else:
                        result = client.models.embed_content(
                            model=settings.EMBEDDING_MODEL,
                            contents=batch
                        )
                        for emb in result.embeddings:
                            all_embeddings.append(emb.values)
                    gemini_breaker.record_success()
                    break
                except Exception as e:
                    gemini_breaker.record_failure()
                    embedding_errors_total.inc()
                    if "429" in str(e):
                        logger.warning(
                            "Rate limit hit at batch starting chunk %d, sleeping 5 s...",
                            batch_start
                        )
                        time.sleep(5)
                        retries -= 1
                        if retries == 0:
                            raise
                    else:
                        logger.error(
                            "Failed to generate embeddings for batch starting at chunk %d: %s",
                            batch_start, e
                        )
                        raise

            # Proactive inter-batch throttle — avoid hitting the rate limit
            if batch_start + EMBEDDING_BATCH_SIZE < len(texts):
                time.sleep(1)

        return np.array(all_embeddings, dtype=np.float32)


embedding_service = EmbeddingService()

