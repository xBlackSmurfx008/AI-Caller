"""Database connection and session management"""

from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool

from src.database.models import Base
from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Create engine with connection pooling for production
# Use QueuePool for better performance and connection reuse
pool_size = getattr(settings, 'DB_POOL_SIZE', 5)
max_overflow = getattr(settings, 'DB_MAX_OVERFLOW', 10)
pool_timeout = getattr(settings, 'DB_POOL_TIMEOUT', 30)

db_url = settings.DATABASE_URL
is_sqlite = urlparse(db_url).scheme == "sqlite"

# SQLite needs different pooling/connection args (especially in serverless / multithreaded contexts)
engine_kwargs = {
    "echo": settings.APP_DEBUG,
    "future": True,
}

if is_sqlite:
    engine_kwargs.update(
        {
            "poolclass": NullPool,
            "connect_args": {"check_same_thread": False},
        }
    )
else:
    engine_kwargs.update(
        {
            "poolclass": QueuePool,
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_timeout": pool_timeout,
            "pool_pre_ping": True,  # Verify connections before using
        }
    )

engine = create_engine(db_url, **engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database (create tables)"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")


def drop_db() -> None:
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)
    logger.info("Database dropped")

