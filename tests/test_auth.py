"""Tests for authentication endpoints"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from jose import jwt

from src.main import app
from src.database.models import User
from src.database.database import get_db
from src.api.routes.auth import get_password_hash

client = TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create a test user"""
    user = User(
        id="test-user-id",
        email="test@example.com",
        name="Test User",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_register_user(db: Session):
    """Test user registration"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "name": "New User",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["name"] == "New User"
    assert "id" in data


def test_login_success(test_user, db: Session):
    """Test successful login"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data


def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401


def test_get_current_user(test_user, db: Session):
    """Test getting current user info"""
    # First login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Use token to get user info
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def test_protected_endpoint_without_token():
    """Test accessing protected endpoint without token"""
    response = client.get("/api/v1/calls")
    assert response.status_code == 403  # Forbidden - no token


def test_protected_endpoint_with_invalid_token():
    """Test accessing protected endpoint with invalid token"""
    response = client.get(
        "/api/v1/calls",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401  # Unauthorized

