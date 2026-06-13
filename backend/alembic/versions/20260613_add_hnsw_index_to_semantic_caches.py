"""add_hnsw_index_to_semantic_caches

Revision ID: 20260613_hnsw_cache
Revises: 20260610_crawl_meta
Create Date: 2026-06-13 10:48:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260613_hnsw_cache'
down_revision = '20260610_crawl_meta'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding "
        "ON semantic_caches USING hnsw ((query_embedding::halfvec(3072)) halfvec_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_semantic_cache_embedding;")
