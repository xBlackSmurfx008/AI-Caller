"""Gmail API routes (OAuth + email operations)."""

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import Any, Dict, List, Optional

from src.email.gmail import (
    start_gmail_oauth,
    finish_gmail_oauth,
    is_gmail_connected,
    send_gmail_message,
    list_gmail_messages,
    get_gmail_message
)
from src.utils.logging import get_logger
from src.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


class SendEmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    body_html: Optional[str] = None
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None


@router.get("/status")
async def gmail_status():
    """Check Gmail connection status"""
    return {"connected": is_gmail_connected()}


@router.get("/oauth/start")
async def gmail_oauth_start(request: Request):
    """Start Gmail OAuth flow"""
    try:
        base = str(request.base_url).rstrip("/")
        redirect_uri = f"{base}/api/gmail/oauth/callback"
        
        # Determine frontend URL for redirect
        # 1. Configured FRONTEND_URL
        # 2. Referer header
        # 3. Fallback to localhost:5173
        frontend_base = settings.FRONTEND_URL
        
        if not frontend_base:
            referer = request.headers.get("referer")
            if referer:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(referer)
                    frontend_base = f"{parsed.scheme}://{parsed.netloc}"
                except Exception:
                    pass
        
        if not frontend_base:
            frontend_base = "http://localhost:5173"
                
        return start_gmail_oauth(redirect_uri=redirect_uri, state=frontend_base)
    except Exception as e:
        logger.error("gmail_oauth_start_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/oauth/callback")
async def gmail_oauth_callback(request: Request, code: str, state: Optional[str] = None):
    """Complete Gmail OAuth flow"""
    try:
        base = str(request.base_url).rstrip("/")
        redirect_uri = f"{base}/api/gmail/oauth/callback"
        finish_gmail_oauth(redirect_uri=redirect_uri, code=code, state=state)
        
        # Redirect back to frontend
        frontend_base = state
        if not frontend_base:
            if settings.FRONTEND_URL:
                frontend_base = settings.FRONTEND_URL
            else:
                frontend_base = "http://localhost:5173"
                
        return RedirectResponse(f"{frontend_base}/oauth/callback?code=success")
    except Exception as e:
        logger.error("gmail_oauth_failed", error=str(e))
        
        # Redirect with error
        frontend_base = state
        if not frontend_base:
            if settings.FRONTEND_URL:
                frontend_base = settings.FRONTEND_URL
            else:
                frontend_base = "http://localhost:5173"
                
        return RedirectResponse(f"{frontend_base}/oauth/callback?error={str(e)}")


@router.post("/send")
async def gmail_send_email(req: SendEmailRequest):
    """Send an email via Gmail"""
    try:
        result = send_gmail_message(
            to=req.to,
            subject=req.subject,
            body=req.body,
            body_html=req.body_html,
            cc=req.cc,
            bcc=req.bcc
        )
        return {"success": True, "message": result}
    except Exception as e:
        logger.error("gmail_send_failed", error=str(e), to=req.to)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/messages")
async def gmail_list_messages(
    query: Optional[str] = None,
    max_results: int = 10,
    page_token: Optional[str] = None
):
    """List Gmail messages"""
    try:
        result = list_gmail_messages(
            query=query,
            max_results=max_results,
            page_token=page_token
        )
        return result
    except Exception as e:
        logger.error("gmail_list_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/messages/{message_id}")
async def gmail_get_message(message_id: str, format: str = "full"):
    """Get a specific Gmail message"""
    try:
        message = get_gmail_message(message_id, format=format)
        return {"message": message}
    except Exception as e:
        logger.error("gmail_get_message_failed", error=str(e), message_id=message_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

