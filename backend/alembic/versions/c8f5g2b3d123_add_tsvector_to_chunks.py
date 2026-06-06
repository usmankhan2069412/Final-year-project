"""add tsvector to knowledge chunks

Revision ID: c8f5g2b3d123
Revises: b7e4f1a2c903
Create Date: 2026-06-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR

# revision identifiers, used by Alembic.
revision = 'c8f5g2b3d123'
down_revision = 'b7e4f1a2c903'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adding a generated column. It will automatically backfill for existing rows.
    op.execute(
        "ALTER TABLE knowledge_chunks ADD COLUMN text_search_vector tsvector "
        "GENERATED ALWAYS AS (to_tsvector('simple', coalesce(chunk_text, ''))) STORED;"
    )
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_text_search_vector ON knowledge_chunks USING GIN (text_search_vector);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_text_search_vector;")
    op.drop_column('knowledge_chunks', 'text_search_vector')
