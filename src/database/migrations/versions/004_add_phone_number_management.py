"""Add phone number management tables

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Detect database type
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == 'postgresql'
    
    # Get appropriate JSON type
    if is_postgresql:
        from sqlalchemy.dialects import postgresql
        json_type = postgresql.JSON(astext_type=sa.Text())
        json_default = '{}'
    else:
        # SQLite uses Text for JSON
        json_type = sa.Text()
        json_default = "'{}'"
    
    # Create phone_numbers table
    op.create_table(
        'phone_numbers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('phone_number', sa.String(), nullable=False),
        sa.Column('twilio_phone_sid', sa.String(), nullable=True),
        sa.Column('friendly_name', sa.String(), nullable=True),
        sa.Column('country_code', sa.String(), nullable=False),
        sa.Column('region', sa.String(), nullable=True),
        sa.Column('capabilities', json_type, nullable=True, server_default=json_default),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('webhook_url', sa.String(), nullable=True),
        sa.Column('webhook_method', sa.String(), nullable=False, server_default='POST'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('metadata', json_type, nullable=True, server_default=json_default),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for phone_numbers
    op.create_index('idx_phone_numbers_phone_number', 'phone_numbers', ['phone_number'], unique=True)
    op.create_index('idx_phone_numbers_twilio_sid', 'phone_numbers', ['twilio_phone_sid'], unique=True)
    op.create_index('idx_phone_numbers_status', 'phone_numbers', ['status'])
    op.create_index('idx_phone_numbers_active', 'phone_numbers', ['is_active'])
    op.create_index('idx_phone_numbers_country', 'phone_numbers', ['country_code'])
    
    # Create agent_phone_numbers table
    op.create_table(
        'agent_phone_numbers',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('phone_number_id', sa.String(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['human_agents.id'], ),
        sa.ForeignKeyConstraint(['phone_number_id'], ['phone_numbers.id'], ),
        sa.UniqueConstraint('agent_id', 'phone_number_id', name='uq_agent_phone_number')
    )
    
    # Create indexes for agent_phone_numbers
    op.create_index('idx_agent_phone_agent', 'agent_phone_numbers', ['agent_id'])
    op.create_index('idx_agent_phone_number', 'agent_phone_numbers', ['phone_number_id'])
    op.create_index('idx_agent_phone_primary', 'agent_phone_numbers', ['agent_id', 'is_primary'])
    
    # Create business_phone_numbers table
    op.create_table(
        'business_phone_numbers',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('business_id', sa.String(), nullable=False),
        sa.Column('phone_number_id', sa.String(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['business_id'], ['business_configs.id'], ),
        sa.ForeignKeyConstraint(['phone_number_id'], ['phone_numbers.id'], ),
        sa.UniqueConstraint('business_id', 'phone_number_id', name='uq_business_phone_number')
    )
    
    # Create indexes for business_phone_numbers
    op.create_index('idx_business_phone_business', 'business_phone_numbers', ['business_id'])
    op.create_index('idx_business_phone_number', 'business_phone_numbers', ['phone_number_id'])
    op.create_index('idx_business_phone_primary', 'business_phone_numbers', ['business_id', 'is_primary'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_business_phone_primary', table_name='business_phone_numbers')
    op.drop_index('idx_business_phone_number', table_name='business_phone_numbers')
    op.drop_index('idx_business_phone_business', table_name='business_phone_numbers')
    op.drop_index('idx_agent_phone_primary', table_name='agent_phone_numbers')
    op.drop_index('idx_agent_phone_number', table_name='agent_phone_numbers')
    op.drop_index('idx_agent_phone_agent', table_name='agent_phone_numbers')
    op.drop_index('idx_phone_numbers_country', table_name='phone_numbers')
    op.drop_index('idx_phone_numbers_active', table_name='phone_numbers')
    op.drop_index('idx_phone_numbers_status', table_name='phone_numbers')
    op.drop_index('idx_phone_numbers_twilio_sid', table_name='phone_numbers')
    op.drop_index('idx_phone_numbers_phone_number', table_name='phone_numbers')
    
    # Drop tables
    op.drop_table('business_phone_numbers')
    op.drop_table('agent_phone_numbers')
    op.drop_table('phone_numbers')

