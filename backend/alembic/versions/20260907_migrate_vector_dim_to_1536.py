"""migrate vector dimension to 1536 for knowledge_chunks and semantic_caches

Revision ID: 20260907_vector_1536
Revises: 20260624_message_jobs
Create Date: 2026-09-07

Changes:
  1. Migrate knowledge_chunks.embedding from vector(3072) to vector(1536)
  2. Rebuild idx_knowledge_chunks_embedding HNSW index
  3. Migrate semantic_caches.query_embedding from vector(3072) to vector(1536)
  4. Rebuild idx_semantic_cache_embedding HNSW index with halfvec(1536)
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260907_vector_1536"
down_revision: Union[str, None] = "20260624_message_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Migrate knowledge_chunks.embedding
    op.execute("DROP INDEX IF EXISTS idx_knowledge_chunks_embedding;")
    op.execute("UPDATE knowledge_chunks SET embedding = NULL;")
    op.execute("ALTER TABLE knowledge_chunks ALTER COLUMN embedding TYPE vector(1536);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);")
    op.execute("UPDATE knowledge_chunks SET index_status = 'QUEUED';")

    # 2. Migrate semantic_caches.query_embedding
    op.execute("DROP INDEX IF EXISTS idx_semantic_cache_embedding;")
    op.execute("TRUNCATE TABLE semantic_caches;")
    op.execute("ALTER TABLE semantic_caches ALTER COLUMN query_embedding TYPE vector(1536);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding "
        "ON semantic_caches USING hnsw ((query_embedding::halfvec(1536)) halfvec_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_knowledge_chunks_embedding;")
    op.execute("UPDATE knowledge_chunks SET embedding = NULL;")
    op.execute("ALTER TABLE knowledge_chunks ALTER COLUMN embedding TYPE vector(3072);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);")

    op.execute("DROP INDEX IF EXISTS idx_semantic_cache_embedding;")
    op.execute("TRUNCATE TABLE semantic_caches;")
    op.execute("ALTER TABLE semantic_caches ALTER COLUMN query_embedding TYPE vector(3072);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding "
        "ON semantic_caches USING hnsw ((query_embedding::halfvec(3072)) halfvec_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )
