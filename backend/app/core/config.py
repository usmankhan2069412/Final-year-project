from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

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
    EMBEDDING_MODEL: str = "gemini-embedding-2"
    EMBEDDING_DIM: int = 3072            # gemini-embedding-2 output dimension
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    CHUNK_SIZE: int = 500                # Characters per chunk
    CHUNK_OVERLAP: int = 50              # Overlap between chunks
    MAX_UPLOAD_SIZE_MB: int = 50

    # CORS Settings
    # Production: set to ["https://app.yourdomain.com"] in .env
    # Development: leave empty — main.py falls back to allowing all localhost ports
    CORS_ORIGINS: List[str] = []

    # Website scraping settings
    SCRAPE_TIMEOUT_SECS: int = 45        # Per-page HTTP timeout in seconds
    SCRAPE_MAX_PAGES: int = 15           # Max pages to crawl per job
    SCRAPE_MAX_DEPTH: int = 2            # BFS crawl depth

    # PubSub / SSE scaling settings
    REDIS_URL: str = ""
    PUB_SUB_BACKEND: str = "in_memory"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()
