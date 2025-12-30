"""Add project_execution_confirmations table

Revision ID: 0002
Revises: 0001_initial
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create project_execution_confirmations table"""
    op.create_table(
        'project_execution_confirmations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('status', sa.String(), nullable=False, default='draft'),
        sa.Column('execution_gate', sa.String(), nullable=False),
        sa.Column('summary', sa.JSON(), nullable=True),
        sa.Column('deliverables', sa.JSON(), nullable=True),
        sa.Column('milestones', sa.JSON(), nullable=True),
        sa.Column('task_plan', sa.JSON(), nullable=True),
        sa.Column('task_tool_map', sa.JSON(), nullable=True),
        sa.Column('dependencies', sa.JSON(), nullable=True),
        sa.Column('risks', sa.JSON(), nullable=True),
        sa.Column('preferences_applied', sa.JSON(), nullable=True),
        sa.Column('constraints_applied', sa.JSON(), nullable=True),
        sa.Column('assumptions', sa.JSON(), nullable=True),
        sa.Column('gaps', sa.JSON(), nullable=True),
        sa.Column('cost_estimate', sa.JSON(), nullable=True),
        sa.Column('approval_checklist', sa.JSON(), nullable=True),
        sa.Column('stakeholders', sa.JSON(), nullable=True),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.Column('previous_pec_id', sa.String(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['previous_pec_id'], ['project_execution_confirmations.id'], ondelete='SET NULL')
    )
    
    # Create indexes
    op.create_index('ix_pec_id', 'project_execution_confirmations', ['id'])
    op.create_index('ix_pec_project_id', 'project_execution_confirmations', ['project_id'])
    op.create_index('ix_pec_status', 'project_execution_confirmations', ['status'])


def downgrade() -> None:
    """Drop project_execution_confirmations table"""
    op.drop_index('ix_pec_status', 'project_execution_confirmations')
    op.drop_index('ix_pec_project_id', 'project_execution_confirmations')
    op.drop_index('ix_pec_id', 'project_execution_confirmations')
    op.drop_table('project_execution_confirmations')

