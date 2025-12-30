"""Reminder engine for upcoming calendar events."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Set

from src.calendar.google_calendar import list_upcoming
from src.notifications.notifier import Notifier
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ReminderEngine:
    """
    Simple in-memory reminder engine.
    - checks upcoming events
    - sends 15-minute reminders
    - de-dupes per event id for a window
    """

    def __init__(self):
        self._sent: Set[str] = set()
        self._notifier = Notifier()

    def _event_start(self, ev: Dict[str, Any]) -> str:
        start = (ev.get("start") or {}).get("dateTime") or (ev.get("start") or {}).get("date")
        return start or ""

    def _event_id(self, ev: Dict[str, Any]) -> str:
        return ev.get("id") or ""

    async def run_once(self) -> None:
        try:
            events = list_upcoming(max_results=20)
        except Exception as e:
            logger.error("reminders_list_failed", error=str(e))
            return

        now = datetime.now(timezone.utc)
        window_start = now + timedelta(minutes=14)
        window_end = now + timedelta(minutes=16)

        for ev in events:
            ev_id = self._event_id(ev)
            if not ev_id or ev_id in self._sent:
                continue

            start_iso = self._event_start(ev)
            if not start_iso:
                continue
            try:
                # Parse ISO (best-effort)
                dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
            except Exception:
                continue

            if window_start <= dt <= window_end:
                summary = ev.get("summary") or "Event"
                link = ev.get("hangoutLink") or ev.get("htmlLink") or ""
                msg = f"Reminder (15m): {summary}. {link}".strip()
                ok = self._notifier.send_sms_to_godfather(msg)
                if ok:
                    self._sent.add(ev_id)
                    logger.info("reminder_sent", event_id=ev_id)


