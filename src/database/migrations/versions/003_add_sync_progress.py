"""Add sync progress tracking table

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
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
        json_default_list = '[]'
        json_default_dict = '{}'
    else:
        # SQLite uses Text for JSON
        json_type = sa.Text()
        json_default_list = "'[]'"
        json_default_dict = "'{}'"
    
    # Create sync_progress table
    op.create_table(
        'sync_progress',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('vendor', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('pages_scraped', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pages_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_pages', sa.Integer(), nullable=True),
        sa.Column('current_url', sa.String(), nullable=True),
        sa.Column('visited_urls', json_type, nullable=True, server_default=json_default_list),
        sa.Column('errors', json_type, nullable=True, server_default=json_default_list),
        sa.Column('metadata', json_type, nullable=True, server_default=json_default_dict),  # Note: stored as 'metadata' in DB, accessed as meta_data in code
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_sync_vendor_status', 'sync_progress', ['vendor', 'status'])
    op.create_index('idx_sync_status', 'sync_progress', ['status'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_sync_status', table_name='sync_progress')
    op.drop_index('idx_sync_vendor_status', table_name='sync_progress')
    
    # Drop table
    op.drop_table('sync_progress')

