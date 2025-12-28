"""Tests for analytics endpoints"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from src.main import app
from src.database.models import User, Call, BusinessConfig, CallStatus, CallDirection, QAScore, Escalation, EscalationStatus
from tests.conftest import get_auth_token, create_test_user

client = TestClient(app)


@pytest.fixture
def test_user_with_config(db: Session):
    """Create a test user with business config"""
    user = create_test_user(db)
    config = BusinessConfig(
        id=str(uuid.uuid4()),
        name="Test Business",
        type="customer_support",
        config_data={"ai": {"model": "gpt-4o"}},
        created_by_user_id=user.id,
        is_active=True,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return user, config


@pytest.fixture
def test_calls_with_qa(test_user_with_config, db: Session):
    """Create test calls with QA scores"""
    user, config = test_user_with_config
    
    # Create calls
    calls = []
    for i in range(5):
        call = Call(
            id=str(uuid.uuid4()),
            twilio_call_sid=f"CA{i}",
            direction=CallDirection.INBOUND if i % 2 == 0 else CallDirection.OUTBOUND,
            status=CallStatus.COMPLETED,
            from_number=f"+123456789{i}",
            to_number=f"+098765432{i}",
            business_id=config.id,
            started_at=datetime.utcnow() - timedelta(days=i),
            ended_at=datetime.utcnow() - timedelta(days=i) + timedelta(minutes=5),
        )
        db.add(call)
        calls.append(call)
    
    db.commit()
    
    # Add QA scores
    for i, call in enumerate(calls):
        qa_score = QAScore(
            call_id=call.id,
            overall_score=0.7 + (i * 0.05),
            sentiment_score=0.6 + (i * 0.05),
            sentiment_label="positive" if i % 2 == 0 else "negative",
            compliance_score=0.8,
            accuracy_score=0.75,
            professionalism_score=0.7,
        )
        db.add(qa_score)
    
    db.commit()
    return user, config, calls


def test_analytics_overview(test_calls_with_qa, db: Session):
    """Test GET /api/v1/analytics/overview endpoint"""
    user, config, calls = test_calls_with_qa
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(
        "/api/v1/analytics/overview",
        headers=headers,
        params={"business_id": config.id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total_calls" in data
    assert "active_calls" in data
    assert "completed_calls" in data
    assert "average_qa_score" in data
    assert "sentiment_distribution" in data
    assert "qa_score_distribution" in data


def test_analytics_call_volume(test_calls_with_qa, db: Session):
    """Test GET /api/v1/analytics/call-volume endpoint"""
    user, config, calls = test_calls_with_qa
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    from_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
    to_date = datetime.utcnow().isoformat()
    
    response = client.get(
        "/api/v1/analytics/call-volume",
        headers=headers,
        params={
            "from_date": from_date,
            "to_date": to_date,
            "interval": "day",
            "business_id": config.id,
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "period" in data[0]
        assert "total_calls" in data[0]


def test_analytics_qa_statistics(test_calls_with_qa, db: Session):
    """Test GET /api/v1/analytics/qa endpoint"""
    user, config, calls = test_calls_with_qa
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(
        "/api/v1/analytics/qa",
        headers=headers,
        params={"business_id": config.id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "average_scores" in data
    assert "score_distribution" in data
    assert "trends" in data
    assert "top_issues" in data


def test_analytics_sentiment(test_calls_with_qa, db: Session):
    """Test GET /api/v1/analytics/sentiment endpoint"""
    user, config, calls = test_calls_with_qa
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(
        "/api/v1/analytics/sentiment",
        headers=headers,
        params={"business_id": config.id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "distribution" in data
    assert "average_sentiment_score" in data
    assert "trends" in data
    assert "correlation" in data


def test_analytics_escalations(test_user_with_config, db: Session):
    """Test GET /api/v1/analytics/escalations endpoint"""
    user, config = test_user_with_config
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a call with escalation
    call = Call(
        id=str(uuid.uuid4()),
        twilio_call_sid="CA123",
        direction=CallDirection.INBOUND,
        status=CallStatus.ESCALATED,
        from_number="+1234567890",
        to_number="+0987654321",
        business_id=config.id,
        started_at=datetime.utcnow() - timedelta(days=1),
    )
    db.add(call)
    db.commit()
    
    escalation = Escalation(
        call_id=call.id,
        status=EscalationStatus.COMPLETED,
        trigger_type="manual",
        assigned_agent_id="agent-1",
        requested_at=datetime.utcnow() - timedelta(days=1),
        completed_at=datetime.utcnow() - timedelta(days=1) + timedelta(minutes=10),
    )
    db.add(escalation)
    db.commit()
    
    response = client.get(
        "/api/v1/analytics/escalations",
        headers=headers,
        params={"business_id": config.id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total_escalations" in data
    assert "escalation_rate" in data
    assert "by_trigger_type" in data
    assert "by_status" in data
    assert "trends" in data


def test_analytics_export_csv(test_calls_with_qa, db: Session):
    """Test POST /api/v1/analytics/export endpoint (CSV)"""
    user, config, calls = test_calls_with_qa
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/api/v1/analytics/export",
        headers=headers,
        json={
            "format": "csv",
            "report_type": "overview",
            "business_id": config.id,
        }
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"


def test_analytics_export_pdf(test_calls_with_qa, db: Session):
    """Test POST /api/v1/analytics/export endpoint (PDF)"""
    user, config, calls = test_calls_with_qa
    token = get_auth_token(user)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post(
        "/api/v1/analytics/export",
        headers=headers,
        json={
            "format": "pdf",
            "report_type": "overview",
            "business_id": config.id,
            "include_charts": True,
        }
    )
    
    # May return 501 if reportlab not installed, or 200 if installed
    assert response.status_code in [200, 501]
    if response.status_code == 200:
        assert "application/pdf" in response.headers.get("content-type", "")

