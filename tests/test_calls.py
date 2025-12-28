"""Tests for call management endpoints"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from src.main import app
from src.database.models import User, Call, BusinessConfig, CallStatus, CallDirection
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


@pytest.fixture
def auth_token(test_user, db: Session):
    """Get auth token for test user"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def test_business_config(test_user, db: Session):
    """Create a test business config"""
    config = BusinessConfig(
        id="test-config-id",
        name="Test Config",
        type="customer_support",
        config_data={},
        created_by_user_id=test_user.id,
        is_active=True,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@pytest.fixture
def test_call(test_business_config, db: Session):
    """Create a test call"""
    call = Call(
        id="test-call-id",
        twilio_call_sid="CA123",
        direction=CallDirection.INBOUND,
        status=CallStatus.COMPLETED,
        from_number="+1234567890",
        to_number="+0987654321",
        business_id=test_business_config.id,
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


def test_list_calls(auth_token, test_call):
    """Test listing calls"""
    response = client.get(
        "/api/v1/calls",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "calls" in data
    assert "pagination" in data
    assert len(data["calls"]) > 0


def test_get_call_details(auth_token, test_call):
    """Test getting call details"""
    response = client.get(
        f"/api/v1/calls/{test_call.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "call" in data
    assert data["call"]["id"] == test_call.id


def test_get_call_not_found(auth_token):
    """Test getting non-existent call"""
    response = client.get(
        "/api/v1/calls/nonexistent-id",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404

