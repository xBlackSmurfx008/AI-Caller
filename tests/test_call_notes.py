"""Tests for call notes endpoints"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from src.main import app
from src.database.models import Call, CallStatus, CallDirection, BusinessConfig
from tests.conftest import get_auth_token, create_test_user


client = TestClient(app)


def test_call_notes_crud(db_session, test_user):
    """Test call notes CRUD operations"""
    token = get_auth_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create business config
    config_response = client.post(
        "/api/v1/config/business",
        json={
            "name": "Test Business",
            "type": "customer_support",
            "config_data": {"ai": {"model": "gpt-4o"}},
        },
        headers=headers,
    )
    config_id = config_response.json()["config"]["id"]
    
    # Create a call
    call = Call(
        id="test-call-notes",
        twilio_call_sid="CA_TEST",
        direction=CallDirection.INBOUND,
        status=CallStatus.COMPLETED,
        from_number="+1234567890",
        to_number="+0987654321",
        business_id=config_id,
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
    )
    db_session.add(call)
    db_session.commit()
    
    # Add note
    add_response = client.post(
        "/api/v1/calls/test-call-notes/notes",
        json={
            "note": "Test note",
            "category": "Follow-up",
            "tags": ["important"],
        },
        headers=headers,
    )
    assert add_response.status_code == 201
    note_id = add_response.json()["note"]["id"]
    
    # List notes
    list_response = client.get("/api/v1/calls/test-call-notes/notes", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()["notes"]) > 0
    
    # Update note
    update_response = client.put(
        f"/api/v1/calls/test-call-notes/notes/{note_id}",
        json={
            "note": "Updated note",
        },
        headers=headers,
    )
    assert update_response.status_code == 200
    
    # Delete note
    delete_response = client.delete(
        f"/api/v1/calls/test-call-notes/notes/{note_id}",
        headers=headers,
    )
    assert delete_response.status_code == 200

