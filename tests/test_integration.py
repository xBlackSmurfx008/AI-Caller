"""Integration tests for API workflows"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.database.models import User, BusinessConfig, Call, CallStatus, CallDirection
from src.database.database import get_db
from src.api.routes.auth import get_password_hash
from datetime import datetime

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
    """Get auth token"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    return response.json()["access_token"]


def test_create_config_and_list_calls_workflow(auth_token, test_user, db: Session):
    """Test workflow: create config -> create call -> list calls"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create business config
    config_response = client.post(
        "/api/v1/config/business",
        json={
            "name": "Test Business",
            "type": "customer_support",
            "config_data": {
                "ai": {"model": "gpt-4o"},
                "voice": {"language": "en"}
            }
        },
        headers=headers
    )
    assert config_response.status_code == 201
    config_id = config_response.json()["config"]["id"]
    
    # Verify config appears in list
    list_response = client.get("/api/v1/config/business", headers=headers)
    assert list_response.status_code == 200
    configs = list_response.json()["configs"]
    assert any(c["id"] == config_id for c in configs)
    
    # Create a call (would normally be done via Twilio webhook, but for testing we'll create directly)
    call = Call(
        id="test-call-workflow",
        twilio_call_sid="CA_WORKFLOW",
        direction=CallDirection.INBOUND,
        status=CallStatus.COMPLETED,
        from_number="+1234567890",
        to_number="+0987654321",
        business_id=config_id,
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    
    # List calls and verify it appears
    calls_response = client.get("/api/v1/calls", headers=headers)
    assert calls_response.status_code == 200
    calls = calls_response.json()["calls"]
    assert any(c["id"] == "test-call-workflow" for c in calls)


def test_notification_workflow(auth_token, test_user, db: Session):
    """Test notification creation and retrieval workflow"""
    from src.database.models import Notification
    import uuid
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Create a notification
    notification = Notification(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        type="test_notification",
        title="Test Notification",
        message="This is a test",
        read=False,
    )
    db.add(notification)
    db.commit()
    
    # Get notifications
    response = client.get("/api/v1/notifications", headers=headers)
    assert response.status_code == 200
    notifications = response.json()["notifications"]
    assert len(notifications) > 0
    assert any(n["id"] == notification.id for n in notifications)
    
    # Get unread count
    count_response = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count_response.status_code == 200
    assert count_response.json()["unread_count"] > 0
    
    # Mark as read
    read_response = client.patch(
        f"/api/v1/notifications/{notification.id}/read",
        headers=headers
    )
    assert read_response.status_code == 200
    
    # Verify unread count decreased
    count_response = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count_response.json()["unread_count"] == 0

