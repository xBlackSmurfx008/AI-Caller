"""Database connection and session management.

Notes on Postgres (Neon):
- On Python 3.14, `psycopg2-binary` wheels may not be available.
- To keep the app runnable, we *gracefully fall back to SQLite* if Postgres driver isn't installed.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from src.utils.config import get_settings

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
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,
            max_overflow=10,
        )
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

