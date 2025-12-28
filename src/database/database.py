"""Database connection and session management"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

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

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_timeout=pool_timeout,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.APP_DEBUG,
    future=True,
)

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

