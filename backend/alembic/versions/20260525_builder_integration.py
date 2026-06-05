"""builder integration schema updates

Revision ID: 20260525_builder
Revises:
Create Date: 2026-05-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260525_builder"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safely add columns if they don't exist
    for table, col_name, col_type in [
        ("chatbots", "name", sa.Column("name", sa.String(length=160), nullable=False, server_default="Aina Bot")),
        ("chatbots", "description", sa.Column("description", sa.Text(), nullable=True)),
        ("chatbots", "created_at", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())),
        ("chatbots", "updated_at", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())),
        ("knowledge_sources", "updated_at", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())),
        ("deployments", "created_at", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    ]:
        try:
            with op.get_bind().begin_nested():
                op.add_column(table, col_type)
        except Exception as e:
            # Ignore DuplicateColumn error
            pass

    try:
        with op.get_bind().begin_nested():
            job_status = postgresql.ENUM("QUEUED", "PROCESSING", "COMPLETED", "FAILED", name="enum_knowledge_job_status", create_type=False)
            job_status.create(op.get_bind(), checkfirst=True)
    except Exception:
        pass

    try:
        with op.get_bind().begin_nested():
            op.create_table(
                "knowledge_jobs",
                sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("chatbot_id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("status", postgresql.ENUM("QUEUED", "PROCESSING", "COMPLETED", "FAILED", name="enum_knowledge_job_status", create_type=False), nullable=False, server_default="QUEUED"),
                sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
                sa.Column("error_message", sa.Text(), nullable=True),
                sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
                sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
                sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
                sa.ForeignKeyConstraint(["chatbot_id"], ["chatbots.id"], ondelete="CASCADE"),
                sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
                sa.ForeignKeyConstraint(["source_id"], ["knowledge_sources.id"], ondelete="CASCADE"),
                sa.PrimaryKeyConstraint("id"),
            )
    except Exception:
        pass


def downgrade() -> None:
    try:
        with op.get_bind().begin_nested():
            op.drop_table("knowledge_jobs")
    except Exception:
        pass
    try:
        with op.get_bind().begin_nested():
            postgresql.ENUM(name="enum_knowledge_job_status").drop(op.get_bind(), checkfirst=True)
    except Exception:
        pass
    for table, col in [
        ("deployments", "created_at"),
        ("knowledge_sources", "updated_at"),
        ("chatbots", "updated_at"),
        ("chatbots", "created_at"),
        ("chatbots", "description"),
        ("chatbots", "name")
    ]:
        try:
            with op.get_bind().begin_nested():
                op.drop_column(table, col)
        except Exception:
            pass
