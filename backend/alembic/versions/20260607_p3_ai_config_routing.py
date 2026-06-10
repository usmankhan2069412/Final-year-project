"""P3: AI config and routing redesign

Revision ID: 20260607_p3
Revises: 20260607_p2
Create Date: 2026-06-07

Changes:
  1. ai_model_configs: Add model_name, display_name, is_default, is_active, created_at, updated_at
  2. ai_model_configs: Change unique constraint uq_ai_model_configs_org_provider -> uq_ai_model_configs_org_provider_model
  3. routing_rules: Add org_id, chatbot_id, priority, fallback_config_id, is_active
  4. routing_rules: Keep model_target nullable
  5. Backfill data for new columns
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260607_p3"
down_revision: Union[str, None] = "20260607_p2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. ai_model_configs
    # ------------------------------------------------------------------
    op.add_column('ai_model_configs', sa.Column('model_name', sa.String(length=80), server_default="default", nullable=False))
    op.add_column('ai_model_configs', sa.Column('display_name', sa.String(length=120), nullable=True))
    op.add_column('ai_model_configs', sa.Column('is_default', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('ai_model_configs', sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.add_column('ai_model_configs', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('ai_model_configs', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))

    # Update constraints
    op.drop_constraint('uq_ai_model_configs_org_provider', 'ai_model_configs', type_='unique')
    op.create_unique_constraint('uq_ai_model_configs_org_provider_model', 'ai_model_configs', ['org_id', 'provider_id', 'model_name'])

    # ------------------------------------------------------------------
    # 2. routing_rules
    # ------------------------------------------------------------------
    # Add columns but nullable first for backfill
    op.add_column('routing_rules', sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('routing_rules', sa.Column('chatbot_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('routing_rules', sa.Column('priority', sa.Integer(), server_default="0", nullable=False))
    op.add_column('routing_rules', sa.Column('fallback_config_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('routing_rules', sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    
    # Make model_target nullable
    op.alter_column('routing_rules', 'model_target', existing_type=sa.String(length=80), nullable=True)

    # ------------------------------------------------------------------
    # 3. Backfill Data
    # ------------------------------------------------------------------
    conn = op.get_bind()
    
    # Backfill routing_rules.org_id from ai_model_configs
    conn.execute(sa.text("""
        UPDATE routing_rules rr
        SET org_id = amc.org_id
        FROM ai_model_configs amc
        WHERE rr.config_id = amc.id
    """))
    
    # Set the first config per org as is_default = True
    conn.execute(sa.text("""
        WITH first_configs AS (
            SELECT id,
                   row_number() OVER (PARTITION BY org_id ORDER BY id) as rn
            FROM ai_model_configs
        )
        UPDATE ai_model_configs
        SET is_default = true
        WHERE id IN (SELECT id FROM first_configs WHERE rn = 1)
    """))
    
    # Optional: backfill ai_model_configs.model_name from routing_rules.model_target
    conn.execute(sa.text("""
        UPDATE ai_model_configs amc
        SET model_name = COALESCE((
            SELECT model_target 
            FROM routing_rules rr 
            WHERE rr.config_id = amc.id 
            LIMIT 1
        ), 'default')
        WHERE EXISTS (
            SELECT 1 FROM routing_rules rr WHERE rr.config_id = amc.id
        )
    """))
    
    # Now that backfill is done, make org_id NOT NULL
    op.alter_column('routing_rules', 'org_id', existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    
    # Add foreign keys for routing_rules
    op.create_foreign_key('fk_routing_rules_org_id', 'routing_rules', 'organizations', ['org_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_routing_rules_chatbot_id', 'routing_rules', 'chatbots', ['chatbot_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_routing_rules_fallback_config', 'routing_rules', 'ai_model_configs', ['fallback_config_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    # ------------------------------------------------------------------
    # Revert routing_rules
    # ------------------------------------------------------------------
    op.drop_constraint('fk_routing_rules_fallback_config', 'routing_rules', type_='foreignkey')
    op.drop_constraint('fk_routing_rules_chatbot_id', 'routing_rules', type_='foreignkey')
    op.drop_constraint('fk_routing_rules_org_id', 'routing_rules', type_='foreignkey')
    
    # Note: we can't easily revert nullable=True for model_target to False without
    # providing default values or ensuring no nulls exist.
    
    op.drop_column('routing_rules', 'is_active')
    op.drop_column('routing_rules', 'fallback_config_id')
    op.drop_column('routing_rules', 'priority')
    op.drop_column('routing_rules', 'chatbot_id')
    op.drop_column('routing_rules', 'org_id')

    # ------------------------------------------------------------------
    # Revert ai_model_configs
    # ------------------------------------------------------------------
    op.drop_constraint('uq_ai_model_configs_org_provider_model', 'ai_model_configs', type_='unique')
    op.create_unique_constraint('uq_ai_model_configs_org_provider', 'ai_model_configs', ['org_id', 'provider_id'])
    
    op.drop_column('ai_model_configs', 'updated_at')
    op.drop_column('ai_model_configs', 'created_at')
    op.drop_column('ai_model_configs', 'is_active')
    op.drop_column('ai_model_configs', 'is_default')
    op.drop_column('ai_model_configs', 'display_name')
    op.drop_column('ai_model_configs', 'model_name')
