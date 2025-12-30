"""Pytest configuration and fixtures"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure required settings exist for imports that happen during test collection.
# This prevents local `.env` values from breaking CI / sandboxed test runs.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "AC" + ("0" * 32))
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test-twilio-token")
os.environ.setdefault("TWILIO_PHONE_NUMBER", "+15550001111")

# Use an absolute SQLite path so all threads/sessions hit the same file.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_ROOT}/test_suite.db")

# Disable Godfather token enforcement for existing route tests unless explicitly enabled.
os.environ.setdefault("GODFATHER_API_TOKEN", "")

from src.utils.config import get_settings

get_settings.cache_clear()

from src.database.database import Base
from src.database import models  # noqa: F401  (populate Base.metadata)

# Test database URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{_ROOT}/test_contacts.db"

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Back-compat fixture name used by some tests."""
    yield test_db

