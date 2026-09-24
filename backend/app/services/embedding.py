import logging
import time
from typing import List, Optional
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

# OpenRouter / Qwen3-Embedding supports batch embedding calls.
# 64 items per batch balances throughput with HTTP payload stability.
EMBEDDING_BATCH_SIZE = 64


class EmbeddingService:
    def __init__(self):
        self._client = None
        self._openrouter_client = None
        self._async_http_client = None
        self._sync_http_client = None

    @staticmethod
    def _format_input(text: str, is_query: bool = False, instruction: Optional[str] = None) -> str:
        task_inst = instruction if instruction is not None else (getattr(settings, "EMBEDDING_QUERY_INSTRUCTION", None) if is_query else None)
        if task_inst:
            return f"Instruct: {task_inst}\nQuery: {text}"
        return text

    def get_sync_http_client(self):
        import httpx
        if self._sync_http_client is None or self._sync_http_client.is_closed:
            self._sync_http_client = httpx.Client(
                timeout=30.0,
                limits=httpx.Limits(
                    max_keepalive_connections=settings.EMBEDDING_MAX_KEEPALIVE,
                    max_connections=settings.EMBEDDING_MAX_CONNECTIONS,
                ),
            )
        return self._sync_http_client

    def get_async_http_client(self):
        import httpx
        if self._async_http_client is None or self._async_http_client.is_closed:
            self._async_http_client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(
                    max_keepalive_connections=settings.EMBEDDING_MAX_KEEPALIVE,
                    max_connections=settings.EMBEDDING_MAX_CONNECTIONS,
                ),
            )
        return self._async_http_client

    async def aclose(self):
        if self._async_http_client is not None and not self._async_http_client.is_closed:
            await self._async_http_client.aclose()
            self._async_http_client = None
        if self._sync_http_client is not None and not self._sync_http_client.is_closed:
            self._sync_http_client.close()
            self._sync_http_client = None

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

    def encode(self, texts: List[str], is_query: bool = False, instruction: Optional[str] = None) -> np.ndarray:
        if not texts:
            return np.array([])

        if gemini_breaker.is_open:
            logger.error("gemini_embedding_circuit_breaker_open — skipping call.")
            embedding_errors_total.inc()
            raise RuntimeError("Gemini embedding API circuit is open due to recent failures.")

        client = self.get_client()
        all_embeddings = []

        formatted_texts = [self._format_input(t, is_query=is_query, instruction=instruction) for t in texts]

        logger.info(
            "Generating embeddings for %d chunks using %s (is_query=%s, batch_size=%d)...",
            len(texts), settings.EMBEDDING_MODEL, is_query, EMBEDDING_BATCH_SIZE
        )

        http_client = self.get_sync_http_client() if settings.OPENROUTER_API_KEY else None
        for batch_start in range(0, len(formatted_texts), EMBEDDING_BATCH_SIZE):
            batch = formatted_texts[batch_start:batch_start + EMBEDDING_BATCH_SIZE]
            retries = 3
            while retries > 0:
                try:
                    if settings.OPENROUTER_API_KEY:
                        payload = {
                            "model": settings.EMBEDDING_MODEL,
                            "input": batch,
                            "dimensions": settings.EMBEDDING_DIM
                        }
                        headers = {
                            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                            "Content-Type": "application/json"
                        }
                        resp = http_client.post("https://openrouter.ai/api/v1/embeddings", json=payload, headers=headers, timeout=30.0)
                        
                        if resp.status_code != 200:
                            raise ValueError(f"OpenRouter HTTP {resp.status_code}: {resp.text}")
                            
                        result = resp.json()
                        
                        if "error" in result:
                            raise ValueError(f"OpenRouter API Error: {result['error']}")
                            
                        if "data" not in result or result["data"] is None:
                            raise ValueError(f"No data in OpenRouter response. Raw: {result}")
                            
                        for item in result["data"]:
                            all_embeddings.append(item["embedding"])
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
            if batch_start + EMBEDDING_BATCH_SIZE < len(formatted_texts) and settings.EMBEDDING_BATCH_DELAY > 0:
                time.sleep(settings.EMBEDDING_BATCH_DELAY)

        return np.array(all_embeddings, dtype=np.float32)

    async def aencode(self, texts: List[str], is_query: bool = False, instruction: Optional[str] = None) -> np.ndarray:
        if not texts:
            return np.array([])

        if gemini_breaker.is_open:
            logger.error("gemini_embedding_circuit_breaker_open — skipping call.")
            embedding_errors_total.inc()
            raise RuntimeError("Gemini embedding API circuit is open due to recent failures.")

        client = self.get_client()
        all_embeddings = []

        formatted_texts = [self._format_input(t, is_query=is_query, instruction=instruction) for t in texts]

        logger.info(
            "Generating embeddings for %d chunks using %s (is_query=%s, batch_size=%d) [ASYNC]...",
            len(texts), settings.EMBEDDING_MODEL, is_query, EMBEDDING_BATCH_SIZE
        )

        import asyncio

        http_client = self.get_async_http_client()
        for batch_start in range(0, len(formatted_texts), EMBEDDING_BATCH_SIZE):
            batch = formatted_texts[batch_start:batch_start + EMBEDDING_BATCH_SIZE]
            retries = 3
            while retries > 0:
                try:
                    if settings.OPENROUTER_API_KEY:
                        payload = {
                            "model": settings.EMBEDDING_MODEL,
                            "input": batch,
                            "dimensions": settings.EMBEDDING_DIM
                        }
                        headers = {
                            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                            "Content-Type": "application/json"
                        }
                        resp = await http_client.post("https://openrouter.ai/api/v1/embeddings", json=payload, headers=headers, timeout=30.0)
                        
                        if resp.status_code != 200:
                            raise ValueError(f"OpenRouter HTTP {resp.status_code}: {resp.text}")
                            
                        result = resp.json()
                        
                        if "error" in result:
                            raise ValueError(f"OpenRouter API Error: {result['error']}")
                            
                        if "data" not in result or result["data"] is None:
                            raise ValueError(f"No data in OpenRouter response. Raw: {result}")
                            
                        for item in result["data"]:
                            all_embeddings.append(item["embedding"])
                    else:
                        # Native non-blocking async Gemini SDK call; falls back to thread pool if client is synchronous mock
                        if hasattr(client, "aio") and hasattr(client.aio, "models"):
                            result = await client.aio.models.embed_content(
                                model=settings.EMBEDDING_MODEL,
                                contents=batch
                            )
                        else:
                            result = await asyncio.to_thread(
                                client.models.embed_content,
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
                        await asyncio.sleep(5)
                        retries -= 1
                        if retries == 0:
                            raise
                    else:
                        logger.error(
                            "Failed to generate embeddings for batch starting at chunk %d: %s",
                            batch_start, e
                        )
                        raise

            if batch_start + EMBEDDING_BATCH_SIZE < len(formatted_texts) and settings.EMBEDDING_BATCH_DELAY > 0:
                await asyncio.sleep(settings.EMBEDDING_BATCH_DELAY)

        return np.array(all_embeddings, dtype=np.float32)

    def encode_queries(self, queries: List[str]) -> np.ndarray:
        return self.encode(queries, is_query=True)

    def encode_documents(self, documents: List[str]) -> np.ndarray:
        return self.encode(documents, is_query=False)

    async def aencode_queries(self, queries: List[str]) -> np.ndarray:
        return await self.aencode(queries, is_query=True)

    async def aencode_documents(self, documents: List[str]) -> np.ndarray:
        return await self.aencode(documents, is_query=False)



embedding_service = EmbeddingService()

