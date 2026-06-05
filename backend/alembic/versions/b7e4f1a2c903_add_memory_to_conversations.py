"""add memory jsonb to conversations

Revision ID: b7e4f1a2c903
Revises: ad20ca5a8485
Create Date: 2026-06-04 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'b7e4f1a2c903'
down_revision = 'ad20ca5a8485'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('conversations', sa.Column('memory', JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column('conversations', 'memory')
