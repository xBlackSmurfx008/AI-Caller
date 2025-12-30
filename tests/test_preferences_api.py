"""Tests for Preferences API"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import PreferenceEntry, PreferenceCategory
from src.database.database import Base, get_db
from src.main import app

# Dedicated DB for this module (keeps tests isolated and deterministic)
engine = create_engine("sqlite:///./test_preferences_api.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def mock_db_session(db_session):
    """Fixture to clean up preferences after tests"""
    yield db_session
    db_session.query(PreferenceEntry).delete()
    db_session.query(PreferenceCategory).delete()
    db_session.commit()

def test_create_preference(client, mock_db_session):
    response = client.post(
        "/api/preferences/",
        json={
            "type": "VENDOR",
            "category": "groceries",
            "name": "Whole Foods",
            "priority": "PRIMARY",
            "tags": ["organic", "expensive"]
        },
        headers={"X-User-ID": "test_user"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Whole Foods"
    assert data["category"] == "groceries"
    assert "organic" in data["tags"]

def test_list_preferences(client, mock_db_session):
    # Create two preferences
    client.post(
        "/api/preferences/",
        json={
            "type": "VENDOR",
            "category": "groceries",
            "name": "Whole Foods",
            "priority": "PRIMARY"
        },
        headers={"X-User-ID": "test_user"}
    )
    client.post(
        "/api/preferences/",
        json={
            "type": "VENDOR",
            "category": "electronics",
            "name": "Best Buy",
            "priority": "SECONDARY"
        },
        headers={"X-User-ID": "test_user"}
    )

    # Test list all
    response = client.get("/api/preferences/", headers={"X-User-ID": "test_user"})
    assert response.status_code == 200
    assert len(response.json()) == 2

    # Test filter by category
    response = client.get("/api/preferences/?category=groceries", headers={"X-User-ID": "test_user"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Whole Foods"

def test_preference_resolution(client, mock_db_session):
    # Create a preference
    client.post(
        "/api/preferences/",
        json={
            "type": "VENDOR",
            "category": "groceries",
            "name": "Trader Joe's",
            "priority": "PRIMARY",
            "tags": ["default"]
        },
        headers={"X-User-ID": "test_user"}
    )

    # Test resolution
    response = client.post(
        "/api/preferences/resolve",
        json={
            "task_request": "Buy some organic apples",
            "context": {"location": "San Francisco"}
        },
        headers={"X-User-ID": "test_user"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Note: Classification depends on OpenAI mock, but structure should be correct
    assert "chosen_default" in data
    assert "alternatives" in data
    assert "intent" in data

