"""Tests for agent management endpoints"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from src.main import app
from src.database.models import User, HumanAgent
from tests.conftest import get_auth_token, create_test_user

client = TestClient(app)


def test_list_agents(db: Session):
    """Test GET /api/v1/agents endpoint"""
    user = create_test_user(db)
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test agents
    agent1 = HumanAgent(
        id=str(uuid.uuid4()),
        name="Agent One",
        email="agent1@test.com",
        is_available=True,
        is_active=True,
    )
    agent2 = HumanAgent(
        id=str(uuid.uuid4()),
        name="Agent Two",
        email="agent2@test.com",
        is_available=False,
        is_active=True,
    )
    db.add(agent1)
    db.add(agent2)
    db.commit()
    
    response = client.get("/api/v1/agents", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) >= 2


def test_list_agents_filtered(db: Session):
    """Test GET /api/v1/agents with filters"""
    user = create_test_user(db)
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test agents
    agent1 = HumanAgent(
        id=str(uuid.uuid4()),
        name="Available Agent",
        email="available@test.com",
        is_available=True,
        is_active=True,
    )
    agent2 = HumanAgent(
        id=str(uuid.uuid4()),
        name="Unavailable Agent",
        email="unavailable@test.com",
        is_available=False,
        is_active=True,
    )
    db.add(agent1)
    db.add(agent2)
    db.commit()
    
    # Filter by available
    response = client.get(
        "/api/v1/agents",
        headers=headers,
        params={"is_available": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert all(agent["is_available"] for agent in data["agents"])


def test_get_agent(db: Session):
    """Test GET /api/v1/agents/{id} endpoint"""
    user = create_test_user(db)
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    agent = HumanAgent(
        id=str(uuid.uuid4()),
        name="Test Agent",
        email="testagent@test.com",
        phone_number="+1234567890",
        is_available=True,
        is_active=True,
    )
    db.add(agent)
    db.commit()
    
    response = client.get(f"/api/v1/agents/{agent.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "agent" in data
    assert data["agent"]["id"] == agent.id
    assert data["agent"]["name"] == "Test Agent"


def test_create_agent(db: Session):
    """Test POST /api/v1/agents endpoint"""
    user = create_test_user(db)
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/api/v1/agents",
        headers=headers,
        json={
            "name": "New Agent",
            "email": "newagent@test.com",
            "phone_number": "+1234567890",
            "extension": "123",
            "skills": ["Customer Service", "Technical Support"],
            "departments": ["Support"],
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "agent" in data
    assert data["agent"]["name"] == "New Agent"
    assert data["agent"]["email"] == "newagent@test.com"


def test_create_agent_duplicate_email(db: Session):
    """Test POST /api/v1/agents with duplicate email"""
    user = create_test_user(db)
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create first agent
    agent = HumanAgent(
        id=str(uuid.uuid4()),
        name="Existing Agent",
        email="existing@test.com",
        is_available=True,
        is_active=True,
    )
    db.add(agent)
    db.commit()
    
    # Try to create another with same email
    response = client.post(
        "/api/v1/agents",
        headers=headers,
        json={
            "name": "Duplicate Agent",
            "email": "existing@test.com",
        }
    )
    
    assert response.status_code == 400


def test_update_agent(db: Session):
    """Test PUT /api/v1/agents/{id} endpoint"""
    user = create_test_user(db)
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    agent = HumanAgent(
        id=str(uuid.uuid4()),
        name="Original Name",
        email="original@test.com",
        is_available=True,
        is_active=True,
    )
    db.add(agent)
    db.commit()
    
    response = client.put(
        f"/api/v1/agents/{agent.id}",
        headers=headers,
        json={
            "name": "Updated Name",
            "email": "updated@test.com",
            "phone_number": "+9876543210",
            "skills": ["Sales"],
            "departments": ["Sales"],
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["agent"]["name"] == "Updated Name"
    assert data["agent"]["email"] == "updated@test.com"


def test_delete_agent(db: Session):
    """Test DELETE /api/v1/agents/{id} endpoint"""
    user = create_test_user(db)
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    agent = HumanAgent(
        id=str(uuid.uuid4()),
        name="To Delete",
        email="todelete@test.com",
        is_available=True,
        is_active=True,
    )
    db.add(agent)
    db.commit()
    
    response = client.delete(f"/api/v1/agents/{agent.id}", headers=headers)
    assert response.status_code == 200
    
    # Verify agent is deleted
    get_response = client.get(f"/api/v1/agents/{agent.id}", headers=headers)
    assert get_response.status_code == 404


def test_update_agent_availability(db: Session):
    """Test PATCH /api/v1/agents/{id}/availability endpoint"""
    user = create_test_user(db)
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    agent = HumanAgent(
        id=str(uuid.uuid4()),
        name="Test Agent",
        email="test@test.com",
        is_available=True,
        is_active=True,
    )
    db.add(agent)
    db.commit()
    
    response = client.patch(
        f"/api/v1/agents/{agent.id}/availability",
        headers=headers,
        json={"is_available": False}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["agent"]["is_available"] == False


def test_get_agent_usage(db: Session):
    """Test GET /api/v1/agents/{id}/usage endpoint"""
    user = create_test_user(db)
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    agent = HumanAgent(
        id=str(uuid.uuid4()),
        name="Test Agent",
        email="test@test.com",
        is_available=True,
        is_active=True,
    )
    db.add(agent)
    db.commit()
    
    response = client.get(f"/api/v1/agents/{agent.id}/usage", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "is_in_use" in data
    assert "active_escalations" in data
    assert "active_calls" in data
    assert "total_escalations" in data
    assert "total_calls" in data

