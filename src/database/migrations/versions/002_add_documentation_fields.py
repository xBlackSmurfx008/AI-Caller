"""Add documentation-specific fields to knowledge_entries

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001_initial_schema'
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
        tags_default = '[]'
    else:
        # SQLite uses Text for JSON
        json_type = sa.Text()
        tags_default = "'[]'"  # String default for SQLite
    
    # Add documentation-specific columns to knowledge_entries
    op.add_column('knowledge_entries', sa.Column('vendor', sa.String(), nullable=True))
    op.add_column('knowledge_entries', sa.Column('doc_type', sa.String(), nullable=True))
    op.add_column('knowledge_entries', sa.Column('api_version', sa.String(), nullable=True))
    op.add_column('knowledge_entries', sa.Column('endpoint', sa.String(), nullable=True))
    
    # Add tags column with database-appropriate type
    if is_postgresql:
        op.add_column('knowledge_entries', sa.Column('tags', json_type, nullable=True, server_default=tags_default))
    else:
        op.add_column('knowledge_entries', sa.Column('tags', json_type, nullable=True, server_default=tags_default))
    
    op.add_column('knowledge_entries', sa.Column('last_synced', sa.DateTime(), nullable=True))
    
    # Create indexes for better query performance
    op.create_index('idx_knowledge_vendor', 'knowledge_entries', ['vendor'])
    op.create_index('idx_knowledge_doc_type', 'knowledge_entries', ['doc_type'])
    op.create_index('idx_knowledge_vendor_type', 'knowledge_entries', ['vendor', 'doc_type'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_knowledge_vendor_type', table_name='knowledge_entries')
    op.drop_index('idx_knowledge_doc_type', table_name='knowledge_entries')
    op.drop_index('idx_knowledge_vendor', table_name='knowledge_entries')
    
    # Drop columns
    op.drop_column('knowledge_entries', 'last_synced')
    op.drop_column('knowledge_entries', 'tags')
    op.drop_column('knowledge_entries', 'endpoint')
    op.drop_column('knowledge_entries', 'api_version')
    op.drop_column('knowledge_entries', 'doc_type')
    op.drop_column('knowledge_entries', 'vendor')

