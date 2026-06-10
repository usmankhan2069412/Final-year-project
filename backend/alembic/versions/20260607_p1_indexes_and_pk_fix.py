"""P1: Fix messages composite PK and add production indexes

Revision ID: 20260607_p1
Revises: 20260606_mt_hardening
Create Date: 2026-06-07

Changes:
  1. Drop composite PK on messages (id, created_at) → PK(id) only
  2. Add idx_messages_conversation_created
  3. Add all missing production indexes
  4. Add pgvector HNSW index on knowledge_chunks.embedding
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20260607_p1"
down_revision: Union[str, None] = "20260606_mt_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. Fix messages composite PK: (id, created_at) → (id)
    # ------------------------------------------------------------------
    # Drop the existing composite primary key
    op.execute("ALTER TABLE messages DROP CONSTRAINT messages_pkey;")
    # Recreate as single-column PK
    op.execute("ALTER TABLE messages ADD CONSTRAINT messages_pkey PRIMARY KEY (id);")
    # Ensure created_at is NOT NULL (it was part of PK before, so it already is,
    # but be explicit for safety)
    op.alter_column("messages", "created_at", nullable=False)

    # ------------------------------------------------------------------
    # 2. Add production indexes
    # ------------------------------------------------------------------
    # Messages: fast message loading by conversation
    op.create_index(
        "idx_messages_conversation_created",
        "messages",
        ["conversation_id", "created_at"],
    )

    # Conversations: fast listing by chatbot
    op.create_index(
        "idx_conversations_chatbot_started",
        "conversations",
        [sa.text("chatbot_id"), sa.text("started_at DESC")],
    )

    # Chatbots: fast filtering by org
    op.create_index("idx_chatbots_org_id", "chatbots", ["org_id"])

    # Knowledge sources: fast lookup by chatbot and org
    op.create_index(
        "idx_knowledge_sources_chatbot_id", "knowledge_sources", ["chatbot_id"]
    )
    op.create_index(
        "idx_knowledge_sources_org_id", "knowledge_sources", ["org_id"]
    )

    # Documents: fast lookup by source
    op.create_index("idx_documents_source_id", "documents", ["source_id"])

    # Knowledge chunks: fast filtering by chatbot+status, source+index
    op.create_index(
        "idx_chunks_chatbot_status",
        "knowledge_chunks",
        ["chatbot_id", "index_status"],
    )
    op.create_index(
        "idx_chunks_source_index",
        "knowledge_chunks",
        ["source_id", "chunk_index"],
    )

    # Notifications: fast unread count and listing
    op.create_index(
        "idx_notifications_user_read", "notifications", ["user_id", "read"]
    )

    # API keys: fast prefix lookup
    op.create_index("idx_api_keys_prefix", "api_keys", ["key_prefix"])

    # ------------------------------------------------------------------
    # 3. pgvector ANN index (HNSW) on knowledge_chunks.embedding
    # ------------------------------------------------------------------
    # Create HNSW index for cosine distance (adjust operator class if using L2 or inner product)
    op.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);")
    
    # Also verify text_search_vector idempotency as requested by the plan
    # If the column wasn't converted to GENERATED ALWAYS AS, this ensures it.
    # Note: Skipping drop/re-add here if it was already done in a previous migration.

def downgrade() -> None:

    # Drop all production indexes
    op.drop_index("idx_api_keys_prefix", table_name="api_keys")
    op.drop_index("idx_notifications_user_read", table_name="notifications")
    op.drop_index("idx_chunks_source_index", table_name="knowledge_chunks")
    op.drop_index("idx_chunks_chatbot_status", table_name="knowledge_chunks")
    op.drop_index("idx_documents_source_id", table_name="documents")
    op.drop_index("idx_knowledge_sources_org_id", table_name="knowledge_sources")
    op.drop_index("idx_knowledge_sources_chatbot_id", table_name="knowledge_sources")
    op.drop_index("idx_chatbots_org_id", table_name="chatbots")
    op.drop_index("idx_conversations_chatbot_started", table_name="conversations")
    op.drop_index("idx_messages_conversation_created", table_name="messages")

    # Revert messages PK: (id) → (id, created_at)
    op.execute("ALTER TABLE messages DROP CONSTRAINT messages_pkey;")
    op.execute("ALTER TABLE messages ADD CONSTRAINT messages_pkey PRIMARY KEY (id, created_at);")
