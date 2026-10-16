import os
from typing import List, Optional, Tuple
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aina AI Platform"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str

    # Authentication Security Settings
    # 🔴 SECRET_KEY must be set in .env — no insecure fallback
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    GOOGLE_CLIENT_ID: str = ""

    # SMTP Configuration Settings
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str = "smtp.resend.com"
    SMTP_USERNAME: str = "resend"
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "onboarding@resend.dev"
    SMTP_FROM_NAME: str = "Aina Security"
    SEND_REAL_EMAILS: bool = False

    # WhatsApp Cloud API Settings
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""
    WHATSAPP_API_VERSION: str = "v21.0"

    # Document Processing & Vector DB Settings
    UPLOAD_DIR: str = "data/uploads"
    EMBEDDING_MODEL: str = "qwen/qwen3-embedding-8b"
    EMBEDDING_DIM: int = 2048            # qwen/qwen3-embedding-8b MRL dimension (pgvector HNSW index limit is 4000)
    EMBEDDING_QUERY_INSTRUCTION: str = "Given a user question, retrieve relevant documents that answer the question"
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    CHUNK_SIZE: int = 500                # Tokens per chunk
    CHUNK_OVERLAP: int = 50              # Overlap between chunks
    MAX_UPLOAD_SIZE_MB: int = 50
    CACHE_SIMILARITY_THRESHOLD: float = 0.8
    RETRIEVAL_TOP_K_SINGLE: int = 4
    RETRIEVAL_TOP_K_MULTI: int = 3
    EMBEDDING_BATCH_DELAY: float = 0.0
    ENABLE_HYBRID_SEARCH: bool = False
    # Rerank & Relevance Settings
    RERANK_THRESHOLD: float = 0.3            # Min Cohere rerank score to keep a chunk
    RERANK_FALLBACK_SIMILARITY_THRESHOLD: float = 0.55  # Max cosine distance for semantic fallback

    # RAG Evaluation Settings
    EVAL_JUDGE_MODEL: str = "openai/gpt-4o-mini"
    EVAL_JUDGE_TEMPERATURE: float = 0.0

    # CORS Settings
    # Production: set to ["https://app.yourdomain.com"] in .env
    # Development: leave empty — main.py falls back to allowing all localhost ports
    CORS_ORIGINS: List[str] = []

    # Website scraping settings
    FIRECRAWL_API_KEY: str = ""
    FIRECRAWL_API_URL: str = "https://api.firecrawl.dev"
    SCRAPE_TIMEOUT_SECS: int = 45        # Per-page HTTP timeout in seconds
    SCRAPE_MAX_PAGES: int = 15           # Max pages to crawl per job
    SCRAPE_MAX_DEPTH: int = 2            # BFS crawl depth

    # PubSub / SSE scaling settings
    REDIS_URL: str = ""
    PUB_SUB_BACKEND: str = "in_memory"

    # TypeSafe Jev Model Settings
    TYPESAFE_API_KEY: str = ""
    TYPESAFE_TIMEOUT_SECS: float = 5.0
    TYPESAFE_CONFIDENCE_THRESHOLD: float = 0.70

    # RAG execution timeout
    RAG_GRAPH_TIMEOUT: float = 45.0
    RERANK_TIMEOUT_SECS: float = 8.0     # Max seconds before falling back to local hybrid validation
    COHERE_API_KEY: str = ""

    # HTTP & embedding connection pool settings
    EMBEDDING_MAX_CONNECTIONS: int = 150  # Max connections for HTTP/embedding client pool
    EMBEDDING_MAX_KEEPALIVE: int = 30     # Max idle keepalive connections

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()

if settings.TYPESAFE_API_KEY and not os.environ.get("TYPESAFE_API_KEY"):
    os.environ["TYPESAFE_API_KEY"] = settings.TYPESAFE_API_KEY


def resolve_openrouter_key(api_key: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Resolve an API key that may be 'managed-by-openrouter' or an OpenRouter key into (effective_key, base_url).
    Returns (None, None) if no key can be resolved."""
    if not api_key:
        return None, None
    if api_key == "managed-by-openrouter":
        effective = getattr(settings, "OPENROUTER_API_KEY", None) or os.getenv("OPENROUTER_API_KEY")
        if effective:
            return effective, "https://openrouter.ai/api/v1"
        effective = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
        return (effective, None) if effective else (None, None)
    if isinstance(api_key, str) and api_key.startswith("sk-or-"):
        return api_key, "https://openrouter.ai/api/v1"
    return api_key, None
