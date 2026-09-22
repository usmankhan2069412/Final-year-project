"""migrate vector dimension to 2048 halfvec for qwen3-embedding-8b

Revision ID: 20260919_vector_4096
Revises: c9fcdcbe251c, 20260907_vector_1536
Create Date: 2026-09-19

Changes:
  1. Migrate knowledge_chunks.embedding from vector(1536) to halfvec(2048)
  2. Rebuild idx_knowledge_chunks_embedding HNSW index using direct halfvec_cosine_ops
  3. Reset knowledge_chunks index_status to QUEUED
  4. Truncate semantic_caches and migrate query_embedding to halfvec(2048)
  5. Rebuild idx_semantic_cache_embedding HNSW index using direct halfvec_cosine_ops
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260919_vector_4096"
down_revision: Union[str, Sequence[str], None] = ("c9fcdcbe251c", "20260907_vector_1536")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Migrate knowledge_chunks.embedding to halfvec(2048)
    op.execute("DROP INDEX IF EXISTS idx_knowledge_chunks_embedding;")
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN IF EXISTS embedding;")
    op.execute("ALTER TABLE knowledge_chunks ADD COLUMN embedding halfvec(2048);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding "
        "ON knowledge_chunks USING hnsw (embedding halfvec_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )
    op.execute("UPDATE knowledge_chunks SET index_status = 'QUEUED';")

    # 2. Migrate semantic_caches.query_embedding to halfvec(2048)
    op.execute("DROP INDEX IF EXISTS idx_semantic_cache_embedding;")
    op.execute("TRUNCATE TABLE semantic_caches;")
    op.execute("ALTER TABLE semantic_caches DROP COLUMN IF EXISTS query_embedding;")
    op.execute("ALTER TABLE semantic_caches ADD COLUMN query_embedding halfvec(2048);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding "
        "ON semantic_caches USING hnsw (query_embedding halfvec_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )


def downgrade() -> None:
    # 1. Revert knowledge_chunks.embedding to vector(1536)
    op.execute("DROP INDEX IF EXISTS idx_knowledge_chunks_embedding;")
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN IF EXISTS embedding;")
    op.execute("ALTER TABLE knowledge_chunks ADD COLUMN embedding vector(1536);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding "
        "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);"
    )
    op.execute("UPDATE knowledge_chunks SET index_status = 'QUEUED';")

    # 2. Revert semantic_caches.query_embedding to vector(1536)
    op.execute("DROP INDEX IF EXISTS idx_semantic_cache_embedding;")
    op.execute("TRUNCATE TABLE semantic_caches;")
    op.execute("ALTER TABLE semantic_caches DROP COLUMN IF EXISTS query_embedding;")
    op.execute("ALTER TABLE semantic_caches ADD COLUMN query_embedding vector(1536);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding "
        "ON semantic_caches USING hnsw ((query_embedding::halfvec(1536)) halfvec_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )
