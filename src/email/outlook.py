"""Outlook email integration (Microsoft Graph API + OAuth)."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

try:
    import msal  # type: ignore
    _OUTLOOK_OK = True
except Exception:  # pragma: no cover
    msal = None  # type: ignore
    _OUTLOOK_OK = False

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


# Microsoft Graph API scopes for email
OUTLOOK_SCOPES = [
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/Mail.Read"
]

# Microsoft Graph API endpoints
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"


def _require_outlook() -> None:
    if not _OUTLOOK_OK:
        raise RuntimeError(
            "Outlook dependencies are not installed. "
            "Run: pip install msal"
        )


def _load_app_config() -> Dict[str, Any]:
    """Load Microsoft app registration configuration"""
    _require_outlook()
    if settings.OUTLOOK_OAUTH_CLIENT_SECRETS_JSON:
        return json.loads(settings.OUTLOOK_OAUTH_CLIENT_SECRETS_JSON)
    if settings.OUTLOOK_OAUTH_CLIENT_SECRETS_FILE:
        with open(settings.OUTLOOK_OAUTH_CLIENT_SECRETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    raise RuntimeError("Missing Outlook OAuth client secrets (set OUTLOOK_OAUTH_CLIENT_SECRETS_JSON or _FILE).")


def _token_path() -> str:
    return settings.OUTLOOK_OAUTH_TOKEN_FILE


def _save_token(token_cache: msal.SerializableTokenCache) -> None:
    """Save token cache to file"""
    _require_outlook()
    path = _token_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(token_cache.serialize())


def _load_token_cache() -> msal.SerializableTokenCache:
    """Load token cache from file"""
    _require_outlook()
    token_cache = msal.SerializableTokenCache()
    path = _token_path()
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                token_cache.deserialize(f.read())
        except Exception as e:
            logger.error("outlook_token_load_failed", error=str(e))
    return token_cache


def _get_app() -> msal.ConfidentialClientApplication:
    """Get MSAL app instance"""
    _require_outlook()
    config = _load_app_config()
    
    # Support both file-based and inline JSON config
    client_id = config.get("client_id") or config.get("appId")
    client_secret = config.get("client_secret") or config.get("password")
    authority = config.get("authority") or f"https://login.microsoftonline.com/{config.get('tenant', 'common')}"
    
    if not client_id:
        raise RuntimeError("Missing client_id/appId in Outlook OAuth config")
    if not client_secret:
        raise RuntimeError("Missing client_secret/password in Outlook OAuth config")
    
    token_cache = _load_token_cache()
    
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=authority,
        token_cache=token_cache
    )
    
    return app


def is_outlook_connected() -> bool:
    """Check if Outlook is connected (has valid token)"""
    if not _OUTLOOK_OK:
        return False
    
    try:
        app = _get_app()
        accounts = app.get_accounts()
        if not accounts:
            return False
        
        # Try to get a token silently
        result = app.acquire_token_silent(OUTLOOK_SCOPES, account=accounts[0])
        if result and "access_token" in result:
            _save_token(app.token_cache)
            return True
        return False
    except Exception as e:
        logger.error("outlook_connection_check_failed", error=str(e))
        return False


def start_outlook_oauth(redirect_uri: str, state: Optional[str] = None) -> Dict[str, str]:
    """Start Outlook OAuth flow"""
    _require_outlook()
    app = _get_app()
    
    # Generate authorization URL
    auth_url = app.get_authorization_request_url(
        scopes=OUTLOOK_SCOPES,
        redirect_uri=redirect_uri,
        state=state
    )
    
    # Store state for verification (in a real app, you'd use session storage)
    # For simplicity, we'll return the auth URL
    return {
        "auth_url": auth_url,
        "state": state or ""
    }


def finish_outlook_oauth(redirect_uri: str, code: str, state: Optional[str] = None) -> None:
    """Complete Outlook OAuth flow"""
    _require_outlook()
    app = _get_app()
    
    # Exchange authorization code for token
    result = app.acquire_token_by_authorization_code(
        code=code,
        scopes=OUTLOOK_SCOPES,
        redirect_uri=redirect_uri
    )
    
    if "error" in result:
        raise RuntimeError(f"Outlook OAuth failed: {result.get('error_description', result.get('error'))}")
    
    # Save token cache
    _save_token(app.token_cache)
    logger.info("outlook_oauth_completed")


def _get_access_token() -> str:
    """Get valid access token"""
    _require_outlook()
    app = _get_app()
    accounts = app.get_accounts()
    
    if not accounts:
        raise RuntimeError("Outlook is not connected. Please complete OAuth flow.")
    
    # Try to get token silently
    result = app.acquire_token_silent(OUTLOOK_SCOPES, account=accounts[0])
    
    if not result or "access_token" not in result:
        raise RuntimeError("Outlook token is invalid. Please reconnect.")
    
    # Save updated token cache
    _save_token(app.token_cache)
    
    return result["access_token"]


def _make_graph_request(method: str, endpoint: str, access_token: str, json_data: Optional[Dict] = None) -> Dict[str, Any]:
    """Make a request to Microsoft Graph API"""
    import httpx
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    url = f"{GRAPH_API_ENDPOINT}{endpoint}"
    
    if method == "GET":
        response = httpx.get(url, headers=headers)
    elif method == "POST":
        response = httpx.post(url, headers=headers, json=json_data)
    elif method == "PATCH":
        response = httpx.patch(url, headers=headers, json=json_data)
    elif method == "DELETE":
        response = httpx.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    
    response.raise_for_status()
    return response.json() if response.content else {}


def send_outlook_message(
    to: str,
    subject: str,
    body: str,
    body_html: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send an email via Microsoft Graph API
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Plain text email body
        body_html: Optional HTML email body
        cc: Optional CC recipients
        bcc: Optional BCC recipients
    
    Returns:
        Dictionary with message ID
    """
    access_token = _get_access_token()
    
    # Build message payload
    message = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML" if body_html else "Text",
                "content": body_html or body
            },
            "toRecipients": [{"emailAddress": {"address": to}}]
        }
    }
    
    if cc:
        message["message"]["ccRecipients"] = [{"emailAddress": {"address": addr}} for addr in cc]
    if bcc:
        message["message"]["bccRecipients"] = [{"emailAddress": {"address": addr}} for addr in bcc]
    
    # Send message
    result = _make_graph_request("POST", "/me/sendMail", access_token, json_data=message)
    
    logger.info("outlook_message_sent", to=to, subject=subject)
    return {
        "success": True,
        "to": to,
        "subject": subject
    }


def list_outlook_messages(
    filter_query: Optional[str] = None,
    top: int = 10,
    skip: int = 0
) -> Dict[str, Any]:
    """
    List Outlook messages
    
    Args:
        filter_query: OData filter query (e.g., "from/emailAddress/address eq 'example@outlook.com'")
        top: Maximum number of messages to return
        skip: Number of messages to skip (for pagination)
    
    Returns:
        Dictionary with messages list
    """
    access_token = _get_access_token()
    
    # Build endpoint with query parameters
    endpoint = f"/me/messages?$top={top}&$skip={skip}&$orderby=receivedDateTime desc"
    
    if filter_query:
        endpoint += f"&$filter={filter_query}"
    
    result = _make_graph_request("GET", endpoint, access_token)
    
    return {
        "messages": result.get("value", []),
        "count": len(result.get("value", []))
    }


def get_outlook_message(message_id: str) -> Dict[str, Any]:
    """
    Get a specific Outlook message
    
    Args:
        message_id: Outlook message ID
    
    Returns:
        Message dictionary with headers, body, etc.
    """
    access_token = _get_access_token()
    
    message = _make_graph_request("GET", f"/me/messages/{message_id}", access_token)
    
    return message

