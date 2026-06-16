"""add_model_override_to_routing_rules

Revision ID: 20260614_model_override
Revises: 20260613_hnsw_cache
Create Date: 2026-06-14

Changes:
  1. Add model_override column to routing_rules (nullable)
"""
from alembic import op
import sqlalchemy as sa

revision = "20260614_model_override"
down_revision = "20260613_hnsw_cache"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("routing_rules", sa.Column("model_override", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("routing_rules", "model_override")
