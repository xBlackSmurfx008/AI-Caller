"""Outlook API routes (Microsoft Graph OAuth + email operations)."""

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import Any, Dict, List, Optional

from src.email.outlook import (
    start_outlook_oauth,
    finish_outlook_oauth,
    is_outlook_connected,
    send_outlook_message,
    list_outlook_messages,
    get_outlook_message
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
async def outlook_status():
    """Check Outlook connection status"""
    return {"connected": is_outlook_connected()}


@router.get("/oauth/start")
async def outlook_oauth_start(request: Request):
    """Start Outlook OAuth flow"""
    try:
        base = str(request.base_url).rstrip("/")
        redirect_uri = f"{base}/api/outlook/oauth/callback"
        
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
                
        return start_outlook_oauth(redirect_uri=redirect_uri, state=frontend_base)
    except Exception as e:
        logger.error("outlook_oauth_start_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/oauth/callback")
async def outlook_oauth_callback(request: Request, code: str, state: Optional[str] = None):
    """Complete Outlook OAuth flow"""
    try:
        base = str(request.base_url).rstrip("/")
        redirect_uri = f"{base}/api/outlook/oauth/callback"
        finish_outlook_oauth(redirect_uri=redirect_uri, code=code, state=state)
        
        # Redirect back to frontend
        frontend_base = state
        if not frontend_base:
             if settings.FRONTEND_URL:
                 frontend_base = settings.FRONTEND_URL
             else:
                 frontend_base = "http://localhost:5173"

        return RedirectResponse(f"{frontend_base}/oauth/callback?code=success")
    except Exception as e:
        logger.error("outlook_oauth_failed", error=str(e))
        
        # Redirect with error
        frontend_base = state
        if not frontend_base:
             if settings.FRONTEND_URL:
                 frontend_base = settings.FRONTEND_URL
             else:
                 frontend_base = "http://localhost:5173"

        return RedirectResponse(f"{frontend_base}/oauth/callback?error={str(e)}")


@router.post("/send")
async def outlook_send_email(req: SendEmailRequest):
    """Send an email via Outlook"""
    try:
        result = send_outlook_message(
            to=req.to,
            subject=req.subject,
            body=req.body,
            body_html=req.body_html,
            cc=req.cc,
            bcc=req.bcc
        )
        return {"success": True, "message": result}
    except Exception as e:
        logger.error("outlook_send_failed", error=str(e), to=req.to)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/messages")
async def outlook_list_messages(
    filter_query: Optional[str] = None,
    top: int = 10,
    skip: int = 0
):
    """List Outlook messages"""
    try:
        result = list_outlook_messages(
            filter_query=filter_query,
            top=top,
            skip=skip
        )
        return result
    except Exception as e:
        logger.error("outlook_list_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/messages/{message_id}")
async def outlook_get_message(message_id: str):
    """Get a specific Outlook message"""
    try:
        message = get_outlook_message(message_id)
        return {"message": message}
    except Exception as e:
        logger.error("outlook_get_message_failed", error=str(e), message_id=message_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

