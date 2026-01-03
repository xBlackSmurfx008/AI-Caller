"""Add relationship ops models for Master Networker CRM

Revision ID: 0003_relationship_ops
Revises: 0002
Create Date: 2024-12-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0003_relationship_ops'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create daily_run_results table
    op.create_table(
        'daily_run_results',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('run_type', sa.String(), nullable=False),
        sa.Column('run_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(), nullable=True, default='running'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('interactions_ingested', sa.Integer(), nullable=True, default=0),
        sa.Column('contacts_updated', sa.Integer(), nullable=True, default=0),
        sa.Column('top_actions', sa.JSON(), nullable=True),
        sa.Column('messages_to_reply', sa.JSON(), nullable=True),
        sa.Column('intros_to_consider', sa.JSON(), nullable=True),
        sa.Column('trust_risks', sa.JSON(), nullable=True),
        sa.Column('value_first_moves', sa.JSON(), nullable=True),
        sa.Column('scheduled_blocks_proposed', sa.JSON(), nullable=True),
        sa.Column('tasks_created', sa.JSON(), nullable=True),
        sa.Column('approvals_needed', sa.JSON(), nullable=True),
        sa.Column('summary_title', sa.String(), nullable=True),
        sa.Column('summary_text', sa.Text(), nullable=True),
        sa.Column('relationship_wins', sa.JSON(), nullable=True),
        sa.Column('relationship_slips', sa.JSON(), nullable=True),
        sa.Column('reconnect_tomorrow', sa.JSON(), nullable=True),
        sa.Column('health_score_trend', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_daily_run_results_id', 'daily_run_results', ['id'])
    op.create_index('ix_daily_run_results_run_type', 'daily_run_results', ['run_type'])
    op.create_index('ix_daily_run_results_run_date', 'daily_run_results', ['run_date'])
    op.create_index('ix_daily_run_results_status', 'daily_run_results', ['status'])
    
    # Create relationship_actions table
    op.create_table(
        'relationship_actions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), sa.ForeignKey('daily_run_results.id', ondelete='CASCADE'), nullable=True),
        sa.Column('contact_id', sa.String(), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('priority_score', sa.Float(), nullable=True, default=0.5),
        sa.Column('why_now', sa.Text(), nullable=True),
        sa.Column('expected_win_win_outcome', sa.Text(), nullable=True),
        sa.Column('risk_flags', sa.JSON(), nullable=True),
        sa.Column('draft_message', sa.Text(), nullable=True),
        sa.Column('draft_channel', sa.String(), nullable=True),
        sa.Column('draft_subject', sa.String(), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=True, default=True),
        sa.Column('status', sa.String(), nullable=True, default='pending'),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('suggested_schedule_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('calendar_block_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_relationship_actions_id', 'relationship_actions', ['id'])
    op.create_index('ix_relationship_actions_run_id', 'relationship_actions', ['run_id'])
    op.create_index('ix_relationship_actions_contact_id', 'relationship_actions', ['contact_id'])
    op.create_index('ix_relationship_actions_project_id', 'relationship_actions', ['project_id'])
    op.create_index('ix_relationship_actions_action_type', 'relationship_actions', ['action_type'])
    op.create_index('ix_relationship_actions_status', 'relationship_actions', ['status'])
    
    # Create godfather_intentions table
    op.create_table(
        'godfather_intentions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('contact_id', sa.String(), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('intention', sa.Text(), nullable=False),
        sa.Column('intention_type', sa.String(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True, default=5),
        sa.Column('status', sa.String(), nullable=True, default='active'),
        sa.Column('target_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('milestones', sa.JSON(), nullable=True),
        sa.Column('current_progress', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_godfather_intentions_id', 'godfather_intentions', ['id'])
    op.create_index('ix_godfather_intentions_contact_id', 'godfather_intentions', ['contact_id'])
    
    # Add new columns to contact_memory_state table
    with op.batch_alter_table('contact_memory_state') as batch_op:
        batch_op.add_column(sa.Column('relationship_score_trend', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('open_loops', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('commitments_made', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('commitments_received', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('offers', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('wants', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('ways_to_help_them', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('preferred_channels', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('best_times', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('sensitivities', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('do_not_contact', sa.Boolean(), nullable=True, default=False))
        batch_op.add_column(sa.Column('reciprocity_balance', sa.Float(), nullable=True, default=0.0))
        batch_op.add_column(sa.Column('last_value_given_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('last_value_received_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove new columns from contact_memory_state
    with op.batch_alter_table('contact_memory_state') as batch_op:
        batch_op.drop_column('relationship_score_trend')
        batch_op.drop_column('open_loops')
        batch_op.drop_column('commitments_made')
        batch_op.drop_column('commitments_received')
        batch_op.drop_column('offers')
        batch_op.drop_column('wants')
        batch_op.drop_column('ways_to_help_them')
        batch_op.drop_column('preferred_channels')
        batch_op.drop_column('best_times')
        batch_op.drop_column('sensitivities')
        batch_op.drop_column('do_not_contact')
        batch_op.drop_column('reciprocity_balance')
        batch_op.drop_column('last_value_given_at')
        batch_op.drop_column('last_value_received_at')
    
    # Drop tables
    op.drop_table('godfather_intentions')
    op.drop_table('relationship_actions')
    op.drop_table('daily_run_results')

