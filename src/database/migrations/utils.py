"""Utility functions for database-agnostic migrations"""

from sqlalchemy import inspect
from alembic import op


def get_dialect_name():
    """Get the database dialect name"""
    bind = op.get_bind()
    return bind.dialect.name


def is_postgresql():
    """Check if database is PostgreSQL"""
    return get_dialect_name() == 'postgresql'


def is_sqlite():
    """Check if database is SQLite"""
    return get_dialect_name() == 'sqlite'


def get_json_type():
    """Get appropriate JSON type for current database"""
    if is_postgresql():
        from sqlalchemy.dialects import postgresql
        return postgresql.JSON(astext_type=None)
    else:
        # SQLite and others use Text with JSON serialization
        from sqlalchemy import Text
        return Text


def get_enum_type(enum_name, values, column_name):
    """Get appropriate ENUM type for current database"""
    if is_postgresql():
        from sqlalchemy.dialects import postgresql
        return postgresql.ENUM(*values, name=enum_name, create_type=False)
    else:
        # SQLite uses String
        from sqlalchemy import String
        return String

