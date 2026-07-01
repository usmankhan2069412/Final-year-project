"""Add index to persona_traits

Revision ID: c9fcdcbe251c
Revises: ee9cb0d56b35
Create Date: 2026-07-01 17:06:04.293412

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c9fcdcbe251c'
down_revision: Union[str, Sequence[str], None] = 'ee9cb0d56b35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(op.f('ix_persona_traits_persona_id'), 'persona_traits', ['persona_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_persona_traits_persona_id'), table_name='persona_traits')
