"""Notification service (SMS/email) for Godfather."""

from __future__ import annotations

from typing import Optional

from twilio.rest import Client as TwilioClient

from src.utils.config import get_settings
from src.utils.logging import get_logger
from src.security.policy import parse_phone_allowlist

logger = get_logger(__name__)
settings = get_settings()


class Notifier:
    def __init__(self):
        self._twilio = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def godfather_phone(self) -> Optional[str]:
        nums = parse_phone_allowlist(settings.GODFATHER_PHONE_NUMBERS)
        return nums[0] if nums else None

    def send_sms_to_godfather(self, message: str) -> bool:
        to = self.godfather_phone()
        if not to:
            logger.warning("no_godfather_phone_configured")
            return False
        try:
            msg = self._twilio.messages.create(to=to, from_=settings.TWILIO_PHONE_NUMBER, body=message)
            logger.info("godfather_sms_sent", sid=msg.sid)
            return True
        except Exception as e:
            logger.error("godfather_sms_failed", error=str(e))
            return False


