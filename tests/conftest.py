"""Pytest configuration and fixtures"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from passlib.context import CryptContext
import uuid

from src.database.database import Base, get_db
from src.database.models import User
from src.main import app
from src.api.routes.auth import create_access_token

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture(scope="function")
def db():
    """Create a test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db):
    """Alias for db fixture for compatibility"""
    return db


@pytest.fixture(scope="function")
def client(db):
    """Create a test client"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session):
    """Create a test user"""
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        hashed_password=pwd_context.hash("testpassword"),
        name="Test User",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_test_user(db: Session, email: str = "test@example.com", password: str = "testpassword"):
    """Helper function to create a test user"""
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=pwd_context.hash(password),
        name="Test User",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_token(user: User) -> str:
    """Get auth token for a user"""
    return create_access_token(data={"sub": user.id})

