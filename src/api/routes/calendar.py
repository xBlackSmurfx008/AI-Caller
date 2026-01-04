"""Calendar API routes (Google Calendar OAuth + basic event ops)."""

from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from src.calendar.google_calendar import start_oauth, finish_oauth, is_connected, list_upcoming, create_event
from src.calendar.ics_calendar import fetch_ics_events
from src.utils.logging import get_logger
from src.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


class CreateEventRequest(BaseModel):
    summary: str
    start_iso: str
    end_iso: str
    description: str = ""
    location: str = ""
    attendees_emails: Optional[List[str]] = None
    timezone: str = "UTC"
    add_google_meet: bool = True


class IcsPreviewRequest(BaseModel):
    ics_url: str
    limit: int = 10


@router.get("/status")
async def calendar_status():
    return {"connected": is_connected()}


@router.get("/oauth/start")
async def calendar_oauth_start(request: Request):
    base = str(request.base_url).rstrip("/")
    redirect_uri = f"{base}/api/calendar/oauth/callback"
    
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
            
    try:
        return start_oauth(redirect_uri=redirect_uri, state=frontend_base)
    except RuntimeError as e:
        logger.error("calendar_oauth_start_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


@router.get("/oauth/callback")
async def calendar_oauth_callback(request: Request, code: str, state: Optional[str] = None):
    base = str(request.base_url).rstrip("/")
    redirect_uri = f"{base}/api/calendar/oauth/callback"
    
    # Determine fallback frontend URL
    frontend_base = state
    if not frontend_base:
         if settings.FRONTEND_URL:
             frontend_base = settings.FRONTEND_URL
         else:
             frontend_base = "http://localhost:5173"

    try:
        finish_oauth(redirect_uri=redirect_uri, code=code, state=state)
        logger.info("calendar_oauth_token_saved_successfully")
        return RedirectResponse(f"{frontend_base}/oauth/callback?code=success&service=calendar")
    except Exception as e:
        import traceback
        logger.error("calendar_oauth_failed", error=str(e), traceback=traceback.format_exc())
        from urllib.parse import quote
        return RedirectResponse(f"{frontend_base}/oauth/callback?error={quote(str(e))}&service=calendar")


@router.get("/events/upcoming")
async def calendar_upcoming(limit: int = 10):
    try:
        return {"events": list_upcoming(max_results=limit)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/events")
async def calendar_create_event(req: CreateEventRequest):
    try:
        ev = create_event(
            summary=req.summary,
            start_iso=req.start_iso,
            end_iso=req.end_iso,
            description=req.description,
            location=req.location,
            attendees_emails=req.attendees_emails,
            timezone_str=req.timezone,
            add_google_meet=req.add_google_meet,
        )
        return {"event": ev, "link": ev.get("htmlLink"), "meet": ev.get("hangoutLink")}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/ics/preview")
async def calendar_ics_preview(req: IcsPreviewRequest):
    """
    Preview events from any calendar that exposes an ICS/ICAL feed.
    Works with Google, Outlook, Apple, Fastmail, etc.
    """
    try:
        events = fetch_ics_events(req.ics_url, limit=req.limit)
        return {"events": events}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("ics_preview_failed", error=str(e), ics_url=req.ics_url)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch ICS feed")


