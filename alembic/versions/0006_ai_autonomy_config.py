"""Add AI autonomy config table

Revision ID: 0006_ai_autonomy_config
Revises: 0005_chat_session_scopes
Create Date: 2026-01-03

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006_ai_autonomy_config"
down_revision = "0005_chat_session_scopes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_autonomy_config",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("level", sa.String(), nullable=True, default="balanced"),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("auto_execute_high_risk", sa.Boolean(), nullable=True, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_autonomy_config_id", "ai_autonomy_config", ["id"])
    op.create_index("ix_ai_autonomy_config_auto_execute_high_risk", "ai_autonomy_config", ["auto_execute_high_risk"])


def downgrade() -> None:
    op.drop_table("ai_autonomy_config")


