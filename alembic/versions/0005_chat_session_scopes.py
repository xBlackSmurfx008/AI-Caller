"""Add chat session scope fields (global vs per-project)

Revision ID: 0005_chat_session_scopes
Revises: 0004_chat_sessions
Create Date: 2026-01-03

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0005_chat_session_scopes"
down_revision = "0004_chat_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("chat_sessions") as batch_op:
        batch_op.add_column(sa.Column("scope_type", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("scope_id", sa.String(), nullable=True))

    # Backfill existing rows to global scope
    op.execute("UPDATE chat_sessions SET scope_type = 'global' WHERE scope_type IS NULL")

    with op.batch_alter_table("chat_sessions") as batch_op:
        batch_op.alter_column("scope_type", existing_type=sa.String(), nullable=False)

    op.create_index("ix_chat_sessions_scope_type", "chat_sessions", ["scope_type"])
    op.create_index("ix_chat_sessions_scope_id", "chat_sessions", ["scope_id"])


def downgrade() -> None:
    op.drop_index("ix_chat_sessions_scope_id", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_scope_type", table_name="chat_sessions")
    with op.batch_alter_table("chat_sessions") as batch_op:
        batch_op.drop_column("scope_id")
        batch_op.drop_column("scope_type")


