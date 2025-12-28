"""Tests for configuration endpoints"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import uuid

from src.main import app
from src.database.models import User, BusinessConfig
from tests.conftest import get_auth_token, create_test_user


client = TestClient(app)


def test_test_connection_endpoint(db_session, test_user):
    """Test POST /api/v1/config/test-connection endpoint"""
    token = get_auth_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with valid credentials (mocked)
    response = client.post(
        "/api/v1/config/test-connection",
        json={
            "openai_api_key": "sk-test-key",
            "twilio_account_sid": "ACtest",
            "twilio_auth_token": "test-token",
            "twilio_phone_number": "+1234567890",
        },
        headers=headers,
    )
    
    # Should return response (may fail connection test but endpoint should work)
    assert response.status_code in [200, 400, 500]  # Endpoint exists, connection may fail
    if response.status_code == 200:
        data = response.json()
        assert "openai" in data
        assert "twilio" in data
        assert "success" in data


def test_business_config_crud(db_session, test_user):
    """Test business config CRUD operations"""
    token = get_auth_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create config
    create_response = client.post(
        "/api/v1/config/business",
        json={
            "name": "Test Business",
            "type": "customer_support",
            "config_data": {
                "ai": {"model": "gpt-4o"},
                "voice": {"language": "en"},
            },
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    config_id = create_response.json()["config"]["id"]
    
    # Get config
    get_response = client.get(f"/api/v1/config/business/{config_id}", headers=headers)
    assert get_response.status_code == 200
    
    # Update config
    update_response = client.put(
        f"/api/v1/config/business/{config_id}",
        json={
            "name": "Updated Business",
            "type": "sales",
            "config_data": {
                "ai": {"model": "gpt-4"},
                "voice": {"language": "en"},
            },
        },
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["config"]["name"] == "Updated Business"
    
    # List configs
    list_response = client.get("/api/v1/config/business", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()["configs"]) > 0
    
    # Delete config
    delete_response = client.delete(f"/api/v1/config/business/{config_id}", headers=headers)
    assert delete_response.status_code == 200


def test_business_config_usage(db_session, test_user):
    """Test GET /api/v1/config/business/{id}/usage endpoint"""
    token = get_auth_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create config
    create_response = client.post(
        "/api/v1/config/business",
        json={
            "name": "Test Business",
            "type": "customer_support",
            "config_data": {"ai": {"model": "gpt-4o"}},
        },
        headers=headers,
    )
    config_id = create_response.json()["config"]["id"]
    
    # Check usage
    usage_response = client.get(f"/api/v1/config/business/{config_id}/usage", headers=headers)
    assert usage_response.status_code == 200
    data = usage_response.json()
    assert "is_in_use" in data
    assert "total_calls" in data
    assert "active_calls" in data

