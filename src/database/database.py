"""Database connection and session management.

Notes on Postgres (Neon):
- On Python 3.14, `psycopg2-binary` wheels may not be available.
- To keep the app runnable, we *gracefully fall back to SQLite* if Postgres driver isn't installed.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from src.utils.config import get_settings
from src.utils.runtime import is_serverless

settings = get_settings()

# Create engine - use DATABASE_URL if provided, otherwise use SQLite for local dev
def _sqlite_engine():
    return create_engine(
        "sqlite:///./ai_caller.db",
        connect_args={"check_same_thread": False},
    )


engine = None
if settings.DATABASE_URL:
    try:
        # Postgres/Supabase compatibility:
        # - Supabase commonly requires SSL (`sslmode=require` for psycopg2).
        # - Serverless runtimes should prefer NullPool (no long-lived pooled conns).
        from sqlalchemy.engine.url import make_url
        from sqlalchemy.pool import NullPool

        url = settings.DATABASE_URL
        connect_args = {}
        try:
            parsed = make_url(url)
            is_postgres = parsed.drivername.startswith("postgres")
            if is_postgres and "sslmode" not in (parsed.query or {}):
                connect_args["sslmode"] = "require"
        except Exception:
            # If URL parsing fails, fall back to a simple heuristic.
            if "sslmode=" not in url and (url.startswith("postgres") or url.startswith("postgresql")):
                connect_args["sslmode"] = "require"

        engine_kwargs = {
            "pool_pre_ping": True,  # Verify connections before using
        }
        if connect_args:
            engine_kwargs["connect_args"] = connect_args

        if is_serverless():
            engine_kwargs["poolclass"] = NullPool
        else:
            engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE") or "5")
            engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW") or "10")

        engine = create_engine(url, **engine_kwargs)
    except Exception as e:
        # If Postgres driver isn't installed / URL invalid...
        import logging
        logger = logging.getLogger(__name__)

        # CRITICAL: In production, we must not silently fall back to SQLite as it would cause data loss in serverless envs.
        if settings.APP_ENV.lower() == "production":
            logger.error(f"DATABASE_URL configured but DB connection failed in PRODUCTION. Error: {e}")
            raise e

        logger.warning(f"DATABASE_URL configured but DB driver not available/connection failed; using SQLite. Error: {e}")
        engine = _sqlite_engine()
else:
    engine = _sqlite_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        # Log but don't fail - tables may already exist
        import logging
        logging.getLogger(__name__).warning(f"Database initialization warning: {e}")

