"""Initial schema migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types (PostgreSQL only - SQLite uses String)
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("CREATE TYPE callstatus AS ENUM ('initiated', 'ringing', 'in_progress', 'completed', 'failed', 'escalated')")
        op.execute("CREATE TYPE calldirection AS ENUM ('inbound', 'outbound')")
        op.execute("CREATE TYPE escalationstatus AS ENUM ('pending', 'in_progress', 'completed', 'cancelled')")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_active', 'users', ['is_active'])
    
    # Create business_configs table
    op.create_table(
        'business_configs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('created_by_user_id', sa.String(), nullable=True),
        sa.Column('config_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_business_configs_created_by_user_id'), 'business_configs', ['created_by_user_id'], unique=False)
    
    # Create calls table
    op.create_table(
        'calls',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('twilio_call_sid', sa.String(), nullable=True),
        sa.Column('direction', postgresql.ENUM('inbound', 'outbound', name='calldirection', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('initiated', 'ringing', 'in_progress', 'completed', 'failed', 'escalated', name='callstatus', create_type=False), nullable=False, server_default='initiated'),
        sa.Column('from_number', sa.String(), nullable=False),
        sa.Column('to_number', sa.String(), nullable=False),
        sa.Column('business_id', sa.String(), nullable=True),
        sa.Column('template_id', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.ForeignKeyConstraint(['business_id'], ['business_configs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_calls_status', 'calls', ['status'])
    op.create_index('idx_calls_business', 'calls', ['business_id'])
    op.create_index('idx_calls_started_at', 'calls', ['started_at'])
    op.create_index('idx_calls_business_status', 'calls', ['business_id', 'status'])
    op.create_index('idx_calls_started_at_status', 'calls', ['started_at', 'status'])
    op.create_index(op.f('ix_calls_twilio_call_sid'), 'calls', ['twilio_call_sid'], unique=True)
    
    # Create call_interactions table
    op.create_table(
        'call_interactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('call_id', sa.String(), nullable=False),
        sa.Column('speaker', sa.String(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('audio_url', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.ForeignKeyConstraint(['call_id'], ['calls.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_call_interactions_call_id'), 'call_interactions', ['call_id'], unique=False)
    op.create_index('idx_interactions_call_timestamp', 'call_interactions', ['call_id', 'timestamp'])
    
    # Create call_notes table
    op.create_table(
        'call_notes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('call_id', sa.String(), nullable=False),
        sa.Column('created_by_user_id', sa.String(), nullable=True),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['call_id'], ['calls.id'], ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_call_notes_call', 'call_notes', ['call_id'])
    op.create_index('idx_call_notes_user', 'call_notes', ['created_by_user_id'])
    
    # Create qa_scores table
    op.create_table(
        'qa_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('call_id', sa.String(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('compliance_score', sa.Float(), nullable=True),
        sa.Column('accuracy_score', sa.Float(), nullable=True),
        sa.Column('professionalism_score', sa.Float(), nullable=True),
        sa.Column('sentiment_label', sa.String(), nullable=True),
        sa.Column('compliance_issues', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('flagged_issues', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('reviewed_by', sa.String(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['call_id'], ['calls.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_qa_call', 'qa_scores', ['call_id'])
    op.create_index('idx_qa_score', 'qa_scores', ['overall_score'])
    
    # Create escalations table
    op.create_table(
        'escalations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('call_id', sa.String(), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'in_progress', 'completed', 'cancelled', name='escalationstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('trigger_type', sa.String(), nullable=False),
        sa.Column('trigger_details', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('assigned_agent_id', sa.String(), nullable=True),
        sa.Column('agent_name', sa.String(), nullable=True),
        sa.Column('conversation_summary', sa.Text(), nullable=True),
        sa.Column('context_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('requested_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['call_id'], ['calls.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_escalation_call', 'escalations', ['call_id'])
    op.create_index('idx_escalation_status', 'escalations', ['status'])
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('action_url', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_notifications_user', 'notifications', ['user_id'])
    op.create_index('idx_notifications_read', 'notifications', ['read'])
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('idx_notifications_user_read', 'notifications', ['user_id', 'read'])
    
    # Create knowledge_entries table
    op.create_table(
        'knowledge_entries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('business_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('source_type', sa.String(), nullable=True),
        sa.Column('vector_id', sa.String(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['business_id'], ['business_configs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_knowledge_business', 'knowledge_entries', ['business_id'])
    op.create_index('idx_knowledge_vector', 'knowledge_entries', ['vector_id'])
    
    # Create human_agents table
    op.create_table(
        'human_agents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('phone_number', sa.String(), nullable=True),
        sa.Column('extension', sa.String(), nullable=True),
        sa.Column('skills', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('departments', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('total_calls_handled', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_active_at', sa.DateTime(), nullable=True),
        sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_human_agents_email'), 'human_agents', ['email'], unique=True)
    op.create_index('idx_agents_available', 'human_agents', ['is_available', 'is_active'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('human_agents')
    op.drop_table('knowledge_entries')
    op.drop_table('notifications')
    op.drop_table('escalations')
    op.drop_table('qa_scores')
    op.drop_table('call_notes')
    op.drop_table('call_interactions')
    op.drop_table('calls')
    op.drop_table('business_configs')
    op.drop_table('users')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS escalationstatus')
    op.execute('DROP TYPE IF EXISTS calldirection')
    op.execute('DROP TYPE IF EXISTS callstatus')

