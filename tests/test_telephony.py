"""Tests for telephony components"""

import pytest
from unittest.mock import Mock, patch

from src.telephony.twilio_client import TwilioService


@pytest.fixture
def mock_twilio_client():
    """Mock Twilio client"""
    with patch("src.telephony.twilio_client.TwilioClient") as mock:
        yield mock


def test_twilio_service_init(mock_twilio_client):
    """Test Twilio service initialization"""
    service = TwilioService()
    assert service.client is not None


def test_initiate_call(mock_twilio_client):
    """Test call initiation"""
    service = TwilioService()
    # Mock call creation
    mock_call = Mock()
    mock_call.sid = "test_call_sid"
    mock_call.status = "initiated"
    mock_call.to = "+1234567890"
    mock_call.from_ = "+0987654321"
    mock_call.direction = "outbound"
    
    service.client.calls.create.return_value = mock_call
    
    result = service.initiate_call(to_number="+1234567890")
    assert result["call_sid"] == "test_call_sid"

