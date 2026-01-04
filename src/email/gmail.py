"""Gmail integration (OAuth + email operations)."""

from __future__ import annotations

import json
import os
import base64
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional

try:
    from google.oauth2.credentials import Credentials  # type: ignore
    from google_auth_oauthlib.flow import Flow  # type: ignore
    from googleapiclient.discovery import build  # type: ignore
    _GMAIL_OK = True
except Exception:  # pragma: no cover
    # Allow app to start without Google deps; raise only when Gmail is used.
    Credentials = None  # type: ignore
    Flow = None  # type: ignore
    build = None  # type: ignore
    _GMAIL_OK = False

from src.utils.config import get_settings
from src.utils.logging import get_logger
from src.utils.runtime import is_serverless

logger = get_logger(__name__)
settings = get_settings()


# NOTE: Google can return a token with a *superset* of scopes previously granted
# for the same OAuth client (incremental auth). google-auth-oauthlib will raise
# "Scope has changed ..." if the token response scopes don't match what we asked for.
# To keep the flow stable, we request a consistent union of scopes used by this app.
REQUIRED_GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]

REQUESTED_GOOGLE_SCOPES = [
    # Gmail
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    # Calendar (used elsewhere in the app; requesting union avoids scope mismatch errors)
    "https://www.googleapis.com/auth/calendar",
]


def _require_gmail() -> None:
    if not _GMAIL_OK:
        raise RuntimeError(
            "Gmail dependencies are not installed. "
            "Run: pip install google-api-python-client google-auth google-auth-oauthlib"
        )


def _load_client_config() -> Dict[str, Any]:
    _require_gmail()
    if settings.GMAIL_OAUTH_CLIENT_SECRETS_JSON:
        return json.loads(settings.GMAIL_OAUTH_CLIENT_SECRETS_JSON)
    if settings.GMAIL_OAUTH_CLIENT_SECRETS_FILE:
        with open(settings.GMAIL_OAUTH_CLIENT_SECRETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    raise RuntimeError("Missing Gmail OAuth client secrets (set GMAIL_OAUTH_CLIENT_SECRETS_FILE or _JSON).")


def _token_path() -> str:
    return settings.GMAIL_OAUTH_TOKEN_FILE


def _use_db_storage() -> bool:
    """Check if we should use database storage (for serverless environments)."""
    # Use DB if DATABASE_URL is set and we're on Vercel or file path doesn't exist
    if not settings.DATABASE_URL:
        return False
    # Always prefer DB storage when available
    return True


def _save_token(creds: Credentials) -> None:
    """Save token to database (preferred) or file."""
    _require_gmail()
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
                # Check if token exists
                existing = db.query(OAuthToken).filter(OAuthToken.provider == "gmail").first()
                if existing:
                    existing.token_data = json.loads(token_json)
                    existing.updated_at = datetime.utcnow()
                else:
                    new_token = OAuthToken(
                        provider="gmail",
                        token_data=json.loads(token_json),
                        scopes=list(getattr(creds, "scopes", None) or REQUESTED_GOOGLE_SCOPES),
                    )
                    db.add(new_token)
                db.commit()
                logger.info("gmail_token_saved_to_db")
                return
            finally:
                db.close()
        except Exception as e:
            logger.error("gmail_token_db_save_failed", error=str(e))
            # In serverless (Vercel), filesystem is read-only — do NOT fall back to file.
            if is_serverless():
                raise RuntimeError(f"Failed to persist Gmail OAuth token in DB: {e}") from e
            # Fall back to file storage in local/dev only
    
    # File storage fallback
    path = _token_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(token_json)
    logger.info("gmail_token_saved_to_file", path=path)


def _load_token() -> Optional[Credentials]:
    """Load token from database (preferred) or file."""
    if not _GMAIL_OK:
        return None
    
    # Try database first
    if _use_db_storage():
        try:
            from src.database.database import SessionLocal
            from src.database.models import OAuthToken
            
            db = SessionLocal()
            try:
                token_record = db.query(OAuthToken).filter(OAuthToken.provider == "gmail").first()
                if token_record and token_record.token_data:
                    logger.info("gmail_token_loaded_from_db")
                    creds = Credentials.from_authorized_user_info(token_record.token_data)
                    if creds and getattr(creds, "has_scopes", None) and not creds.has_scopes(REQUIRED_GMAIL_SCOPES):
                        logger.warning("gmail_token_missing_required_scopes")
                        return None
                    return creds
            finally:
                db.close()
        except Exception as e:
            logger.error("gmail_token_db_load_failed", error=str(e))
    
    # Fall back to file storage
    path = _token_path()
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
        logger.info("gmail_token_loaded_from_file", path=path)
        creds = Credentials.from_authorized_user_info(json.loads(data))
        if creds and getattr(creds, "has_scopes", None) and not creds.has_scopes(REQUIRED_GMAIL_SCOPES):
            logger.warning("gmail_token_missing_required_scopes")
            return None
        return creds
    except Exception as e:
        logger.error("gmail_token_load_failed", error=str(e))
        return None


def is_gmail_connected() -> bool:
    """Check if Gmail is connected (has valid token)"""
    from google.auth.transport.requests import Request
    creds = _load_token()
    if not creds:
        return False
    # Ensure required Gmail scopes exist (token may have superset scopes)
    if getattr(creds, "has_scopes", None) and not creds.has_scopes(REQUIRED_GMAIL_SCOPES):
        return False
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                _save_token(creds)
                return True
            except Exception as e:
                logger.error("gmail_token_refresh_failed", error=str(e))
                return False
        return False
    return True


def build_flow(redirect_uri: str, state: Optional[str] = None) -> Flow:
    _require_gmail()
    client_config = _load_client_config()
    flow = Flow.from_client_config(client_config, scopes=REQUESTED_GOOGLE_SCOPES, state=state)
    flow.redirect_uri = redirect_uri
    return flow


def start_gmail_oauth(redirect_uri: str, state: Optional[str] = None) -> Dict[str, str]:
    """Start Gmail OAuth flow"""
    flow = build_flow(redirect_uri=redirect_uri, state=state)
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return {"auth_url": auth_url, "state": state}


def finish_gmail_oauth(redirect_uri: str, code: str, state: Optional[str] = None) -> None:
    """Complete Gmail OAuth flow"""
    _require_gmail()
    from google.auth.transport.requests import Request
    flow = build_flow(redirect_uri=redirect_uri, state=state)
    flow.fetch_token(code=code)
    creds = flow.credentials
    _save_token(creds)


def _service():
    """Get Gmail API service"""
    _require_gmail()
    from google.auth.transport.requests import Request
    creds = _load_token()
    if not creds:
        raise RuntimeError("Gmail is not connected. Please complete OAuth flow.")
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_token(creds)
        else:
            raise RuntimeError("Gmail token is invalid. Please reconnect.")
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def send_gmail_message(
    to: str,
    subject: str,
    body: str,
    body_html: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send an email via Gmail API
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Plain text email body
        body_html: Optional HTML email body
        cc: Optional CC recipients
        bcc: Optional BCC recipients
    
    Returns:
        Dictionary with message ID and thread ID
    """
    svc = _service()
    
    # Get user's email address
    profile = svc.users().getProfile(userId="me").execute()
    from_email = profile.get("emailAddress")
    
    # Create message
    message = MIMEMultipart("alternative")
    message["To"] = to
    message["From"] = from_email
    message["Subject"] = subject
    
    if cc:
        message["Cc"] = ", ".join(cc)
    if bcc:
        message["Bcc"] = ", ".join(bcc)
    
    # Add plain text part
    message.attach(MIMEText(body, "plain"))
    
    # Add HTML part if provided
    if body_html:
        message.attach(MIMEText(body_html, "html"))
    
    # Encode message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    
    # Send message
    result = svc.users().messages().send(
        userId="me",
        body={"raw": raw_message}
    ).execute()
    
    logger.info("gmail_message_sent", message_id=result.get("id"), to=to)
    return {
        "id": result.get("id"),
        "threadId": result.get("threadId"),
        "labelIds": result.get("labelIds", [])
    }


def list_gmail_messages(
    query: Optional[str] = None,
    max_results: int = 10,
    page_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    List Gmail messages
    
    Args:
        query: Gmail search query (e.g., "from:example@gmail.com")
        max_results: Maximum number of messages to return
        page_token: Token for pagination
    
    Returns:
        Dictionary with messages list and next page token
    """
    svc = _service()
    
    request_params = {
        "userId": "me",
        "maxResults": max_results
    }
    
    if query:
        request_params["q"] = query
    if page_token:
        request_params["pageToken"] = page_token
    
    result = svc.users().messages().list(**request_params).execute()
    
    messages = result.get("messages", [])
    return {
        "messages": messages,
        "nextPageToken": result.get("nextPageToken"),
        "resultSizeEstimate": result.get("resultSizeEstimate", 0)
    }


def get_gmail_message(message_id: str, format: str = "full") -> Dict[str, Any]:
    """
    Get a specific Gmail message
    
    Args:
        message_id: Gmail message ID
        format: Message format ("full", "metadata", "minimal", "raw")
    
    Returns:
        Message dictionary with headers, body, etc.
    """
    svc = _service()
    
    message = svc.users().messages().get(
        userId="me",
        id=message_id,
        format=format
    ).execute()
    
    return message

