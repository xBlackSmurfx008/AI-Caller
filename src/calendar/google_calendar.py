"""Google Calendar integration (OAuth + basic event ops)."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from google.oauth2.credentials import Credentials  # type: ignore
    from google_auth_oauthlib.flow import Flow  # type: ignore
    from googleapiclient.discovery import build  # type: ignore
    _GOOGLE_OK = True
except Exception:  # pragma: no cover
    # Allow app to start without Google deps; raise only when calendar is used.
    Credentials = None  # type: ignore
    Flow = None  # type: ignore
    build = None  # type: ignore
    _GOOGLE_OK = False

from src.utils.config import get_settings
from src.utils.logging import get_logger
from src.utils.runtime import is_serverless

logger = get_logger(__name__)
settings = get_settings()


# NOTE: See src/email/gmail.py for context. Google can return tokens with a superset
# of scopes previously granted for the same OAuth client. To avoid "Scope has changed"
# errors during token exchange, request a consistent union of scopes used by this app.
REQUIRED_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]

REQUESTED_GOOGLE_SCOPES = [
    # Gmail (used elsewhere in the app; requesting union avoids scope mismatch errors)
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    # Calendar
    "https://www.googleapis.com/auth/calendar",
]

def _require_google() -> None:
    if not _GOOGLE_OK:
        raise RuntimeError(
            "Google Calendar dependencies are not installed. "
            "Run: pip install google-api-python-client google-auth google-auth-oauthlib"
        )


def _load_client_config() -> Dict[str, Any]:
    _require_google()
    if settings.GOOGLE_OAUTH_CLIENT_SECRETS_JSON:
        return json.loads(settings.GOOGLE_OAUTH_CLIENT_SECRETS_JSON)
    if settings.GOOGLE_OAUTH_CLIENT_SECRETS_FILE:
        with open(settings.GOOGLE_OAUTH_CLIENT_SECRETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    raise RuntimeError("Missing Google OAuth client secrets (set GOOGLE_OAUTH_CLIENT_SECRETS_FILE or _JSON).")


def _token_path() -> str:
    return settings.GOOGLE_OAUTH_TOKEN_FILE


def _use_db_storage() -> bool:
    """Check if we should use database storage (for serverless environments)."""
    if not settings.DATABASE_URL:
        return False
    return True


def _save_token(creds: Credentials) -> None:
    """Save token to database (preferred) or file."""
    _require_google()
    token_json = creds.to_json()
    
    if _use_db_storage():
        try:
            from src.database.database import SessionLocal
            from src.database.models import OAuthToken
            from src.database.database import engine, Base
            
            db = SessionLocal()
            try:
                # Ensure table exists (serverless deploys may skip init_db on cold start)
                Base.metadata.create_all(bind=engine, tables=[OAuthToken.__table__])
                existing = db.query(OAuthToken).filter(OAuthToken.provider == "google_calendar").first()
                if existing:
                    existing.token_data = json.loads(token_json)
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    new_token = OAuthToken(
                        provider="google_calendar",
                        token_data=json.loads(token_json),
                        scopes=list(getattr(creds, "scopes", None) or REQUESTED_GOOGLE_SCOPES),
                    )
                    db.add(new_token)
                db.commit()
                logger.info("google_calendar_token_saved_to_db")
                return
            finally:
                db.close()
        except Exception as e:
            logger.error("google_calendar_token_db_save_failed", error=str(e))
            # In serverless (Vercel), filesystem is read-only — do NOT fall back to file.
            if is_serverless():
                raise RuntimeError(f"Failed to persist Google Calendar OAuth token in DB: {e}") from e
    
    # File storage fallback
    path = _token_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(token_json)
    logger.info("google_calendar_token_saved_to_file", path=path)


def _load_token() -> Optional[Credentials]:
    """Load token from database (preferred) or file."""
    if not _GOOGLE_OK:
        return None
    
    # Try database first
    if _use_db_storage():
        try:
            from src.database.database import SessionLocal
            from src.database.models import OAuthToken
            
            db = SessionLocal()
            try:
                token_record = db.query(OAuthToken).filter(OAuthToken.provider == "google_calendar").first()
                if token_record and token_record.token_data:
                    logger.info("google_calendar_token_loaded_from_db")
                    creds = Credentials.from_authorized_user_info(token_record.token_data)
                    if creds and getattr(creds, "has_scopes", None) and not creds.has_scopes(REQUIRED_CALENDAR_SCOPES):
                        logger.warning("google_calendar_token_missing_required_scopes")
                        return None
                    return creds
            finally:
                db.close()
        except Exception as e:
            logger.error("google_calendar_token_db_load_failed", error=str(e))
    
    # Fall back to file storage
    path = _token_path()
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
        logger.info("google_calendar_token_loaded_from_file", path=path)
        creds = Credentials.from_authorized_user_info(json.loads(data))
        if creds and getattr(creds, "has_scopes", None) and not creds.has_scopes(REQUIRED_CALENDAR_SCOPES):
            logger.warning("google_calendar_token_missing_required_scopes")
            return None
        return creds
    except Exception as e:
        logger.error("google_token_load_failed", error=str(e))
        return None


def is_connected() -> bool:
    creds = _load_token()
    if not creds:
        return False
    if getattr(creds, "has_scopes", None) and not creds.has_scopes(REQUIRED_CALENDAR_SCOPES):
        return False
    return bool(creds.valid)


def build_flow(redirect_uri: str, state: Optional[str] = None) -> Flow:
    _require_google()
    client_config = _load_client_config()
    flow = Flow.from_client_config(client_config, scopes=REQUESTED_GOOGLE_SCOPES, state=state)
    flow.redirect_uri = redirect_uri
    return flow


def start_oauth(redirect_uri: str, state: Optional[str] = None) -> Dict[str, str]:
    flow = build_flow(redirect_uri=redirect_uri, state=state)
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return {"auth_url": auth_url, "state": state}


def finish_oauth(redirect_uri: str, code: str, state: Optional[str] = None) -> None:
    _require_google()
    flow = build_flow(redirect_uri=redirect_uri, state=state)
    flow.fetch_token(code=code)
    creds = flow.credentials
    _save_token(creds)


def _service():
    _require_google()
    creds = _load_token()
    if not creds or not creds.valid:
        raise RuntimeError("Google Calendar is not connected.")
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def list_upcoming(max_results: int = 10) -> List[Dict[str, Any]]:
    svc = _service()
    now = datetime.now(timezone.utc).isoformat()
    events = (
        svc.events()
        .list(
            calendarId=settings.GOOGLE_CALENDAR_ID,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events.get("items", [])


def create_event(
    summary: str,
    start_iso: str,
    end_iso: str,
    description: str = "",
    location: str = "",
    attendees_emails: Optional[List[str]] = None,
    timezone_str: str = "UTC",
    add_google_meet: bool = True,
) -> Dict[str, Any]:
    svc = _service()
    event: Dict[str, Any] = {
        "summary": summary,
        "description": description,
        "location": location,
        "start": {"dateTime": start_iso, "timeZone": timezone_str},
        "end": {"dateTime": end_iso, "timeZone": timezone_str},
    }
    if attendees_emails:
        event["attendees"] = [{"email": e} for e in attendees_emails]

    conference_data_version = 0
    if add_google_meet:
        conference_data_version = 1
        event["conferenceData"] = {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        }

    created = (
        svc.events()
        .insert(
            calendarId=settings.GOOGLE_CALENDAR_ID,
            body=event,
            conferenceDataVersion=conference_data_version,
            sendUpdates="all" if attendees_emails else "none",
        )
        .execute()
    )
    return created


def get_freebusy(
    time_min: str,
    time_max: str,
    calendar_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get free/busy information for calendar
    
    Args:
        time_min: ISO8601 datetime string for start of range
        time_max: ISO8601 datetime string for end of range
        calendar_id: Calendar ID (defaults to GOOGLE_CALENDAR_ID)
    
    Returns:
        Dictionary with freebusy information
    """
    svc = _service()
    cal_id = calendar_id or settings.GOOGLE_CALENDAR_ID
    
    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "items": [{"id": cal_id}]
    }
    
    result = svc.freebusy().query(body=body).execute()
    return result.get("calendars", {}).get(cal_id, {})


def update_event(
    event_id: str,
    summary: Optional[str] = None,
    start_iso: Optional[str] = None,
    end_iso: Optional[str] = None,
    description: Optional[str] = None,
    timezone_str: str = "UTC",
) -> Dict[str, Any]:
    """
    Update an existing calendar event
    
    Args:
        event_id: Google Calendar event ID
        summary: New event title
        start_iso: New start time (ISO8601)
        end_iso: New end time (ISO8601)
        description: New description
        timezone_str: Timezone string
    
    Returns:
        Updated event dictionary
    """
    svc = _service()
    
    # Get existing event
    event = svc.events().get(
        calendarId=settings.GOOGLE_CALENDAR_ID,
        eventId=event_id
    ).execute()
    
    # Update fields
    if summary is not None:
        event["summary"] = summary
    if start_iso is not None:
        event["start"] = {"dateTime": start_iso, "timeZone": timezone_str}
    if end_iso is not None:
        event["end"] = {"dateTime": end_iso, "timeZone": timezone_str}
    if description is not None:
        event["description"] = description
    
    # Update event
    updated = svc.events().update(
        calendarId=settings.GOOGLE_CALENDAR_ID,
        eventId=event_id,
        body=event
    ).execute()
    
    return updated


def delete_event(event_id: str) -> None:
    """
    Delete a calendar event
    
    Args:
        event_id: Google Calendar event ID
    """
    svc = _service()
    svc.events().delete(
        calendarId=settings.GOOGLE_CALENDAR_ID,
        eventId=event_id
    ).execute()


