"""add crawl metadata to knowledge_sources

Revision ID: 20260610_crawl_meta
Revises: ad20ca5a8485
Create Date: 2026-06-10 10:52:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260610_crawl_meta'
down_revision = '51f81e665f90'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("ALTER TABLE knowledge_sources ADD COLUMN IF NOT EXISTS pages_crawled INTEGER;")
    op.execute("ALTER TABLE knowledge_sources ADD COLUMN IF NOT EXISTS total_content_chars INTEGER;")
    op.execute("ALTER TABLE knowledge_sources ADD COLUMN IF NOT EXISTS crawl_duration_secs INTEGER;")

def downgrade() -> None:
    op.drop_column('knowledge_sources', 'crawl_duration_secs')
    op.drop_column('knowledge_sources', 'total_content_chars')
    op.drop_column('knowledge_sources', 'pages_crawled')
