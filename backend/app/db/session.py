from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# Sync engine — used by background workers, alembic, health checks
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_recycle=1800)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine — used by FastAPI request handlers
ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=15,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={"statement_cache_size": 0},
)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            if session.in_transaction():
                await session.rollback()
        except Exception:
            try:
                if session.in_transaction():
                    await session.rollback()
            except Exception:
                pass
            raise

