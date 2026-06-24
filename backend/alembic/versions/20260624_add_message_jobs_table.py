"""add message_jobs table for outbound message queue

Revision ID: 20260624_message_jobs
Revises: 20260614_model_override
Create Date: 2026-06-24

Changes:
  1. Create enum_message_job_status enum type
  2. Create message_jobs table with FK to conversations
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260624_message_jobs"
down_revision: Union[str, None] = "20260614_model_override"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        with op.get_bind().begin_nested():
            msg_job_status = postgresql.ENUM(
                "QUEUED", "PROCESSING", "COMPLETED", "FAILED",
                name="enum_message_job_status", create_type=False,
            )
            msg_job_status.create(op.get_bind(), checkfirst=True)
    except Exception:
        pass

    try:
        with op.get_bind().begin_nested():
            op.create_table(
                "message_jobs",
                sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("channel", sa.String(), nullable=False),
                sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
                sa.Column(
                    "status",
                    postgresql.ENUM("QUEUED", "PROCESSING", "COMPLETED", "FAILED", name="enum_message_job_status", create_type=False),
                    nullable=False,
                    server_default="QUEUED",
                ),
                sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
                sa.Column("error_message", sa.Text(), nullable=True),
                sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
                sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
                sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("retry_after", sa.DateTime(timezone=True), nullable=True),
                sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
                sa.PrimaryKeyConstraint("id"),
            )
    except Exception:
        pass

    # Create indexes
    try:
        with op.get_bind().begin_nested():
            op.create_index("ix_message_jobs_channel", "message_jobs", ["channel"])
    except Exception:
        pass
    try:
        with op.get_bind().begin_nested():
            op.create_index("ix_message_jobs_status", "message_jobs", ["status"])
    except Exception:
        pass
    try:
        with op.get_bind().begin_nested():
            op.create_index("ix_message_jobs_retry_after", "message_jobs", ["retry_after"])
    except Exception:
        pass
    try:
        with op.get_bind().begin_nested():
            op.create_index("ix_message_jobs_conversation_id", "message_jobs", ["conversation_id"])
    except Exception:
        pass


def downgrade() -> None:
    try:
        with op.get_bind().begin_nested():
            op.drop_table("message_jobs")
    except Exception:
        pass
    try:
        with op.get_bind().begin_nested():
            postgresql.ENUM(name="enum_message_job_status").drop(op.get_bind(), checkfirst=True)
    except Exception:
        pass
