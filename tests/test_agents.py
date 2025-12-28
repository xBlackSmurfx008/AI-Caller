"""Tests for agent endpoints"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from tests.conftest import get_auth_token, create_test_user


client = TestClient(app)


def test_agent_usage_endpoint(db_session, test_user):
    """Test GET /api/v1/agents/{id}/usage endpoint"""
    token = get_auth_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create agent
    create_response = client.post(
        "/api/v1/agents",
        json={
            "name": "Test Agent",
            "email": "testagent@test.com",
            "phone_number": "+1234567890",
        },
        headers=headers,
    )
    
    if create_response.status_code == 201:
        agent_id = create_response.json()["agent"]["id"]
        
        # Check usage
        usage_response = client.get(f"/api/v1/agents/{agent_id}/usage", headers=headers)
        assert usage_response.status_code == 200
        data = usage_response.json()
        assert "is_in_use" in data
        assert "active_escalations" in data
        assert "active_calls" in data
        assert "total_escalations" in data
        assert "total_calls" in data

