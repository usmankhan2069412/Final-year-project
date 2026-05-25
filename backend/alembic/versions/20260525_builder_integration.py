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
    op.add_column("chatbots", sa.Column("name", sa.String(length=160), nullable=False, server_default="Aina Bot"))
    op.add_column("chatbots", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("chatbots", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.add_column("chatbots", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.add_column("knowledge_sources", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.add_column("deployments", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))

    job_status = postgresql.ENUM("QUEUED", "PROCESSING", "COMPLETED", "FAILED", name="enum_knowledge_job_status", create_type=False)
    job_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "knowledge_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chatbot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", job_status, nullable=False, server_default="QUEUED"),
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


def downgrade() -> None:
    op.drop_table("knowledge_jobs")
    postgresql.ENUM(name="enum_knowledge_job_status").drop(op.get_bind(), checkfirst=True)
    op.drop_column("deployments", "created_at")
    op.drop_column("knowledge_sources", "updated_at")
    op.drop_column("chatbots", "updated_at")
    op.drop_column("chatbots", "created_at")
    op.drop_column("chatbots", "description")
    op.drop_column("chatbots", "name")
