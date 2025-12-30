"""Initial schema (create_all fallback)

Revision ID: 0001_initial
Revises: None
Create Date: 2025-12-28

This migration uses SQLAlchemy metadata to create all tables defined in `src/database/models.py`.
For long-term production use, prefer explicit `op.create_table(...)` migrations.
"""

from __future__ import annotations

from alembic import op

from src.database.database import Base
from src.database import models  # noqa: F401


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)


