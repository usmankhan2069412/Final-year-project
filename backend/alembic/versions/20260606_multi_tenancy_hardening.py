"""Multi-tenancy hardening: composite foreign keys and uniqueness constraints

Revision ID: 20260606_mt_hardening
Revises: c8f5g2b3d123
Create Date: 2026-06-06

Changes:
  1. Add composite uniqueness to parent tables
  2. Drop simple FKs and add composite FKs for tenant safety
  3. Add trigger for messages.config_id tenant validation
  4. Add missing uniqueness constraints
  5. Add case-insensitive email index
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260606_mt_hardening"
down_revision: Union[str, None] = "c8f5g2b3d123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_CREATE_FN_MESSAGES = """
CREATE OR REPLACE FUNCTION trg_check_messages_config_org()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    expected_org_id UUID;
    actual_org_id   UUID;
BEGIN
    IF NEW.config_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- Get the org_id of the chatbot that owns the conversation
    SELECT c.org_id INTO expected_org_id
    FROM conversations conv
    JOIN chatbots c ON c.id = conv.chatbot_id
    WHERE conv.id = NEW.conversation_id;

    -- Get the org_id of the AI model config
    SELECT org_id INTO actual_org_id
    FROM ai_model_configs
    WHERE id = NEW.config_id;

    IF expected_org_id IS NULL THEN
        RAISE EXCEPTION 'messages: conversation_id % or its chatbot does not exist', NEW.conversation_id;
    END IF;
    
    IF actual_org_id IS NULL THEN
        RAISE EXCEPTION 'messages: config_id % does not exist', NEW.config_id;
    END IF;

    IF actual_org_id <> expected_org_id THEN
        RAISE EXCEPTION 'messages: config_id % belongs to org %, but conversation belongs to org %',
            NEW.config_id, actual_org_id, expected_org_id;
    END IF;

    RETURN NEW;
END;
$$;
"""

_CREATE_TRIGGER_MESSAGES = """
CREATE TRIGGER trg_messages_config_org_check
BEFORE INSERT OR UPDATE ON messages
FOR EACH ROW EXECUTE FUNCTION trg_check_messages_config_org();
"""

_DROP_TRIGGER_MESSAGES = "DROP TRIGGER IF EXISTS trg_messages_config_org_check ON messages;"
_DROP_FN_MESSAGES = "DROP FUNCTION IF EXISTS trg_check_messages_config_org();"


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # Pre-flight checks
    # ------------------------------------------------------------------
    bad_ks = conn.execute(sa.text("""
        SELECT ks.id FROM knowledge_sources ks
        JOIN chatbots c ON c.id = ks.chatbot_id
        WHERE ks.org_id <> c.org_id LIMIT 1;
    """)).scalar()
    if bad_ks: raise ValueError("Cross-tenant leak found in knowledge_sources. Please clean data before migrating.")

    bad_doc = conn.execute(sa.text("""
        SELECT d.id FROM documents d
        JOIN knowledge_sources ks ON ks.id = d.source_id
        WHERE d.chatbot_id <> ks.chatbot_id OR d.org_id <> ks.org_id LIMIT 1;
    """)).scalar()
    if bad_doc: raise ValueError("Cross-tenant leak found in documents. Please clean data before migrating.")

    bad_job = conn.execute(sa.text("""
        SELECT kj.id FROM knowledge_jobs kj
        JOIN knowledge_sources ks ON ks.id = kj.source_id
        WHERE kj.chatbot_id <> ks.chatbot_id OR kj.org_id <> ks.org_id LIMIT 1;
    """)).scalar()
    if bad_job: raise ValueError("Cross-tenant leak found in knowledge_jobs. Please clean data before migrating.")

    # ------------------------------------------------------------------
    # Step 1: Add composite uniqueness to parent tables
    # ------------------------------------------------------------------
    op.create_unique_constraint("uq_chatbots_id_org", "chatbots", ["id", "org_id"])
    op.create_unique_constraint("uq_knowledge_sources_id_chatbot_org", "knowledge_sources", ["id", "chatbot_id", "org_id"])
    op.create_unique_constraint("uq_ai_model_configs_id_org", "ai_model_configs", ["id", "org_id"])
    op.create_unique_constraint("uq_conversations_id_chatbot", "conversations", ["id", "chatbot_id"])

    # ------------------------------------------------------------------
    # Step 2: Drop old FKs, Add composite FKs for tenant safety
    # ------------------------------------------------------------------
    op.drop_constraint("knowledge_sources_chatbot_id_fkey", "knowledge_sources", type_="foreignkey")
    op.drop_constraint("knowledge_sources_org_id_fkey", "knowledge_sources", type_="foreignkey")
    op.create_foreign_key(
        "fk_knowledge_sources_chatbot_org",
        "knowledge_sources", "chatbots",
        ["chatbot_id", "org_id"], ["id", "org_id"],
        ondelete="CASCADE"
    )

    op.drop_constraint("documents_chatbot_id_fkey", "documents", type_="foreignkey")
    op.drop_constraint("documents_org_id_fkey", "documents", type_="foreignkey")
    op.drop_constraint("documents_source_id_fkey", "documents", type_="foreignkey")
    op.create_foreign_key(
        "fk_documents_source_chatbot_org",
        "documents", "knowledge_sources",
        ["source_id", "chatbot_id", "org_id"], ["id", "chatbot_id", "org_id"],
        ondelete="CASCADE"
    )

    op.drop_constraint("knowledge_jobs_chatbot_id_fkey", "knowledge_jobs", type_="foreignkey")
    op.drop_constraint("knowledge_jobs_org_id_fkey", "knowledge_jobs", type_="foreignkey")
    op.drop_constraint("knowledge_jobs_source_id_fkey", "knowledge_jobs", type_="foreignkey")
    op.create_foreign_key(
        "fk_knowledge_jobs_source_chatbot_org",
        "knowledge_jobs", "knowledge_sources",
        ["source_id", "chatbot_id", "org_id"], ["id", "chatbot_id", "org_id"],
        ondelete="CASCADE"
    )

    # ------------------------------------------------------------------
    # Step 3: Trigger for messages.config_id mismatch
    # ------------------------------------------------------------------
    conn.execute(sa.text(_CREATE_FN_MESSAGES))
    conn.execute(sa.text(_CREATE_TRIGGER_MESSAGES))

    # ------------------------------------------------------------------
    # Step 4: Missing constraints & Indexes
    # ------------------------------------------------------------------
    # Clean duplicates first
    conn.execute(sa.text("""
        DELETE FROM knowledge_chunks kc WHERE id NOT IN (
            SELECT DISTINCT ON (source_id, chunk_index) id FROM knowledge_chunks ORDER BY source_id, chunk_index, id
        );
    """))
    op.create_unique_constraint("uq_knowledge_chunks_source_chunk", "knowledge_chunks", ["source_id", "chunk_index"])

    conn.execute(sa.text("""
        DELETE FROM ai_model_configs amc WHERE id NOT IN (
            SELECT DISTINCT ON (org_id, provider_id) id FROM ai_model_configs ORDER BY org_id, provider_id, id DESC
        );
    """))
    op.create_unique_constraint("uq_ai_model_configs_org_provider", "ai_model_configs", ["org_id", "provider_id"])

    # Drop existing unique constraint/index on users.email safely
    conn.execute(sa.text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_key;"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_users_email;"))
    # Add lower index
    conn.execute(sa.text("""
        CREATE UNIQUE INDEX uq_users_email_lower ON users (lower(email));
    """))

    # Active subscriptions partial index
    conn.execute(sa.text("""
        DROP INDEX IF EXISTS uq_subscriptions_one_active_per_org;
        CREATE UNIQUE INDEX uq_subscriptions_active
        ON subscriptions (org_id)
        WHERE status IN ('active', 'trialing', 'past_due');
    """))


def downgrade() -> None:
    conn = op.get_bind()

    # Revert index
    conn.execute(sa.text("DROP INDEX IF EXISTS uq_subscriptions_active;"))
    
    # Revert email index
    conn.execute(sa.text("DROP INDEX IF EXISTS uq_users_email_lower;"))
    op.create_unique_constraint("users_email_key", "users", ["email"])

    op.drop_constraint("uq_ai_model_configs_org_provider", "ai_model_configs", type_="unique")
    op.drop_constraint("uq_knowledge_chunks_source_chunk", "knowledge_chunks", type_="unique")

    conn.execute(sa.text(_DROP_TRIGGER_MESSAGES))
    conn.execute(sa.text(_DROP_FN_MESSAGES))

    # Revert FKs
    op.drop_constraint("fk_knowledge_jobs_source_chatbot_org", "knowledge_jobs", type_="foreignkey")
    op.create_foreign_key("knowledge_jobs_source_id_fkey", "knowledge_jobs", "knowledge_sources", ["source_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("knowledge_jobs_org_id_fkey", "knowledge_jobs", "organizations", ["org_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("knowledge_jobs_chatbot_id_fkey", "knowledge_jobs", "chatbots", ["chatbot_id"], ["id"], ondelete="CASCADE")

    op.drop_constraint("fk_documents_source_chatbot_org", "documents", type_="foreignkey")
    op.create_foreign_key("documents_source_id_fkey", "documents", "knowledge_sources", ["source_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("documents_org_id_fkey", "documents", "organizations", ["org_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("documents_chatbot_id_fkey", "documents", "chatbots", ["chatbot_id"], ["id"], ondelete="CASCADE")

    op.drop_constraint("fk_knowledge_sources_chatbot_org", "knowledge_sources", type_="foreignkey")
    op.create_foreign_key("knowledge_sources_org_id_fkey", "knowledge_sources", "organizations", ["org_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("knowledge_sources_chatbot_id_fkey", "knowledge_sources", "chatbots", ["chatbot_id"], ["id"], ondelete="CASCADE")

    # Drop parent unique constraints
    op.drop_constraint("uq_conversations_id_chatbot", "conversations", type_="unique")
    op.drop_constraint("uq_ai_model_configs_id_org", "ai_model_configs", type_="unique")
    op.drop_constraint("uq_knowledge_sources_id_chatbot_org", "knowledge_sources", type_="unique")
    op.drop_constraint("uq_chatbots_id_org", "chatbots", type_="unique")
