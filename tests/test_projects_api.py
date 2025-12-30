"""Tests for Projects API"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Project
from src.main import app
from src.database.database import Base, get_db

# Dedicated DB for this module (keeps tests isolated and deterministic)
engine = create_engine("sqlite:///./test_projects_api.db", connect_args={"check_same_thread": False})
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
    yield db_session
    db_session.query(Project).delete()
    db_session.commit()

def test_create_project(client, mock_db_session):
    response = client.post(
        "/api/projects/",
        json={
            "title": "New Website Launch",
            "description": "Redesign the corporate website",
            "priority": 8
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Website Launch"
    assert data["status"] == "active"

def test_list_projects(client, mock_db_session):
    client.post(
        "/api/projects/",
        json={"title": "Project A", "priority": 5}
    )
    client.post(
        "/api/projects/",
        json={"title": "Project B", "priority": 3}
    )

    response = client.get("/api/projects/")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_project(client, mock_db_session):
    create_res = client.post(
        "/api/projects/",
        json={"title": "Target Project", "priority": 5}
    )
    project_id = create_res.json()["id"]

    response = client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Target Project"

