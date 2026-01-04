"""Add godfather profile table

Revision ID: 0007_godfather_profile
Revises: 0006_ai_autonomy_config
Create Date: 2026-01-03

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_godfather_profile"
down_revision = "0006_ai_autonomy_config"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "godfather_profile",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("preferred_name", sa.String(), nullable=True),
        sa.Column("pronouns", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("timezone", sa.String(), nullable=True, server_default="UTC"),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("assistant_notes", sa.Text(), nullable=True),
        sa.Column("preferences", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_godfather_profile_id", "godfather_profile", ["id"])


def downgrade() -> None:
    op.drop_table("godfather_profile")


