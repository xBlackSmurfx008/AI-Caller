"""ICS calendar support (works with any calendar that exposes an ICS feed)."""

from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime

import httpx
from ics import Calendar

from src.utils.logging import get_logger

logger = get_logger(__name__)


def _to_iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    # Ensure timezone-aware ISO output when available
    if dt.tzinfo:
        return dt.isoformat()
    return dt.replace(tzinfo=None).isoformat()


def fetch_ics_events(ics_url: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch and parse an ICS feed into a normalized list of events.

    Args:
        ics_url: Public ICS/ICAL URL (Google, Outlook, Apple, etc.).
        limit: Max number of events to return.

    Returns:
        List of events with id/summary/start/end/location/htmlLink.
    """
    if not ics_url or not ics_url.lower().startswith(("http://", "https://")):
        raise ValueError("ICS URL must start with http:// or https://")

    resp = httpx.get(ics_url, timeout=10.0)
    resp.raise_for_status()

    cal = Calendar(resp.text)
    events: List[Dict[str, Any]] = []

    for event in cal.events:
        start = _to_iso(event.begin.datetime if event.begin else None)
        end = _to_iso(event.end.datetime if event.end else None)
        events.append(
            {
                "id": getattr(event, "uid", None) or getattr(event, "id", None) or event.name,
                "summary": event.name or "Untitled event",
                "description": event.description or "",
                "location": event.location or "",
                "start": {"dateTime": start} if start else {},
                "end": {"dateTime": end} if end else {},
                "htmlLink": event.url or ics_url,
            }
        )

    # Sort by start (nulls last) and limit
    events.sort(key=lambda e: e.get("start", {}).get("dateTime") or "9999")
    return events[:limit]

