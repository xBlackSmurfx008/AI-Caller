"""Tests for notification endpoints"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from tests.conftest import get_auth_token, create_test_user


client = TestClient(app)


def test_notifications_list(db_session, test_user):
    """Test GET /api/v1/notifications endpoint"""
    token = get_auth_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/v1/notifications", headers=headers)
    assert response.status_code == 200
    assert "notifications" in response.json()


def test_notifications_unread_count(db_session, test_user):
    """Test GET /api/v1/notifications/unread-count endpoint"""
    token = get_auth_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert response.status_code == 200
    assert "count" in response.json()

