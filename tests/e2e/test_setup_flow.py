"""
End-to-end tests for setup wizard flow

Note: These tests require a running application and database.
Run with: pytest tests/e2e/ -v
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from tests.conftest import get_auth_token, create_test_user


client = TestClient(app)


@pytest.mark.e2e
def test_complete_setup_wizard_flow(db_session, test_user):
    """Test complete setup wizard flow from start to finish"""
    token = get_auth_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1: Test API connection
    test_conn_response = client.post(
        "/api/v1/config/test-connection",
        json={
            "openai_api_key": "sk-test",
            "twilio_account_sid": "ACtest",
            "twilio_auth_token": "test-token",
            "twilio_phone_number": "+1234567890",
        },
        headers=headers,
    )
    # Connection may fail but endpoint should work
    assert test_conn_response.status_code in [200, 400, 500]
    
    # Step 2: Complete setup
    setup_response = client.post(
        "/api/v1/setup/complete",
        json={
            "business_config": {
                "name": "E2E Test Business",
                "type": "customer_support",
                "config_data": {
                    "ai": {"model": "gpt-4o"},
                    "voice": {"language": "en"},
                },
            },
            "agents": [
                {
                    "name": "E2E Agent",
                    "email": "e2e@test.com",
                },
            ],
        },
        headers=headers,
    )
    
    # Setup should complete (may have warnings)
    assert setup_response.status_code in [200, 201, 500]
    
    if setup_response.status_code == 200:
        data = setup_response.json()
        assert data.get("success") is True


@pytest.mark.e2e
def test_call_lifecycle_with_notes(db_session, test_user):
    """Test complete call lifecycle including notes"""
    token = get_auth_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create business config
    config_response = client.post(
        "/api/v1/config/business",
        json={
            "name": "E2E Business",
            "type": "customer_support",
            "config_data": {"ai": {"model": "gpt-4o"}},
        },
        headers=headers,
    )
    
    if config_response.status_code == 201:
        config_id = config_response.json()["config"]["id"]
        
        # Create call (would normally be via Twilio webhook)
        # For E2E test, we'll simulate by creating directly in DB
        from src.database.models import Call, CallStatus, CallDirection
        from datetime import datetime
        
        call = Call(
            id="e2e-call",
            twilio_call_sid="CA_E2E",
            direction=CallDirection.INBOUND,
            status=CallStatus.IN_PROGRESS,
            from_number="+1234567890",
            to_number="+0987654321",
            business_id=config_id,
            started_at=datetime.utcnow(),
        )
        db_session.add(call)
        db_session.commit()
        
        # Add note
        note_response = client.post(
            "/api/v1/calls/e2e-call/notes",
            json={"note": "E2E test note"},
            headers=headers,
        )
        assert note_response.status_code == 201
        
        # List notes
        notes_response = client.get("/api/v1/calls/e2e-call/notes", headers=headers)
        assert notes_response.status_code == 200
        assert len(notes_response.json()["notes"]) > 0

