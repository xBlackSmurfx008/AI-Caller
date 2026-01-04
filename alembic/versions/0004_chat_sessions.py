"""Add chat sessions/messages/summaries for deep history

Revision ID: 0004_chat_sessions
Revises: 0003_relationship_ops
Create Date: 2026-01-03

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_chat_sessions"
down_revision = "0003_relationship_ops"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("actor_phone", sa.String(), nullable=True),
        sa.Column("actor_email", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_sessions_id", "chat_sessions", ["id"])
    op.create_index("ix_chat_sessions_actor_phone", "chat_sessions", ["actor_phone"])
    op.create_index("ix_chat_sessions_actor_email", "chat_sessions", ["actor_email"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_messages_id", "chat_messages", ["id"])
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])
    op.create_index("ix_chat_messages_role", "chat_messages", ["role"])

    op.create_table(
        "chat_session_summaries",
        sa.Column("session_id", sa.String(), sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=True, default=1),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index("ix_chat_session_summaries_session_id", "chat_session_summaries", ["session_id"])


def downgrade() -> None:
    op.drop_table("chat_session_summaries")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")


