"""P2: Enrich API keys and Knowledge chunks

Revision ID: 20260607_p2
Revises: 20260607_p1
Create Date: 2026-06-07

Changes:
  1. API Keys: add expires_at, created_by_user_id, unique constraint on key_prefix
  2. Knowledge Chunks: add document_id, token_count, content_hash, embedding_model, metadata_extra, created_at, updated_at
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260607_p2"
down_revision: Union[str, None] = "20260607_p1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- API Keys ---
    op.add_column('api_keys', sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('api_keys', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))
    
    op.create_foreign_key('fk_api_keys_created_by_users', 'api_keys', 'users', ['created_by_user_id'], ['id'], ondelete='SET NULL')
    
    # key_prefix unique constraint
    op.create_unique_constraint('uq_api_keys_prefix', 'api_keys', ['key_prefix'])
    
    # --- Knowledge Chunks ---
    op.add_column('knowledge_chunks', sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('knowledge_chunks', sa.Column('token_count', sa.Integer(), nullable=True))
    op.add_column('knowledge_chunks', sa.Column('content_hash', sa.String(length=64), nullable=True))
    op.add_column('knowledge_chunks', sa.Column('embedding_model', sa.String(length=100), nullable=True))
    op.add_column('knowledge_chunks', sa.Column('metadata_extra', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'"), nullable=False))
    op.add_column('knowledge_chunks', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column('knowledge_chunks', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    op.create_foreign_key('fk_knowledge_chunks_document_id', 'knowledge_chunks', 'documents', ['document_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    # --- Knowledge Chunks ---
    op.drop_constraint('fk_knowledge_chunks_document_id', 'knowledge_chunks', type_='foreignkey')
    op.drop_column('knowledge_chunks', 'updated_at')
    op.drop_column('knowledge_chunks', 'created_at')
    op.drop_column('knowledge_chunks', 'metadata_extra')
    op.drop_column('knowledge_chunks', 'embedding_model')
    op.drop_column('knowledge_chunks', 'content_hash')
    op.drop_column('knowledge_chunks', 'token_count')
    op.drop_column('knowledge_chunks', 'document_id')

    # --- API Keys ---
    op.drop_constraint('uq_api_keys_prefix', 'api_keys', type_='unique')
    op.drop_constraint('fk_api_keys_created_by_users', 'api_keys', type_='foreignkey')
    op.drop_column('api_keys', 'expires_at')
    op.drop_column('api_keys', 'created_by_user_id')
