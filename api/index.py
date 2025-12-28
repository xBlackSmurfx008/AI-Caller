"""
Vercel serverless function entry point.

IMPORTANT:
- Vercel serverless has strict bundle size limits.
- The full AI Caller backend pulls in heavy optional deps (RAG, Playwright, etc.).
  For Twilio webhook testing, we only need a small subset of routes and deps.
"""

import os
import sys
import traceback

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize app first
app = FastAPI(
    title="AI Caller Webhooks (Vercel)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Try to setup logging and settings, but don't fail if they're not available
try:
    from src.utils.logging import setup_logging
    setup_logging()
except Exception as e:
    print(f"Warning: Failed to setup logging: {e}")

try:
    from src.utils.config import get_settings
    settings = get_settings()
    cors_origins = settings.CORS_ORIGINS if hasattr(settings, 'CORS_ORIGINS') else ["*"]
except Exception as e:
    print(f"Warning: Failed to load settings: {e}")
    settings = None
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to include webhook router, but handle gracefully if it fails
try:
    from src.api.webhooks.twilio_webhook import router as twilio_webhook_router
    app.include_router(twilio_webhook_router, prefix="/webhooks/twilio", tags=["webhooks"])
except Exception as e:
    print(f"Warning: Failed to load webhook router: {e}")
    traceback.print_exc()
    
    # Create a minimal fallback router
    from fastapi import APIRouter
    fallback_router = APIRouter()
    
    @fallback_router.post("/voice")
    async def fallback_voice():
        return Response(
            content='<Response><Say>Service temporarily unavailable. Please try again later.</Say></Response>',
            media_type="application/xml"
        )
    
    @fallback_router.post("/status")
    async def fallback_status():
        return {"status": "received", "note": "service_degraded"}
    
    app.include_router(fallback_router, prefix="/webhooks/twilio", tags=["webhooks"])


@app.get("/")
async def root():
    return {"message": "AI Caller Webhook API", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "settings_loaded": settings is not None,
    }
    
    # Check database if available
    if settings and hasattr(settings, 'DATABASE_URL'):
        try:
            from src.database.database import get_db
            from sqlalchemy import text
            db_gen = get_db()
            db = next(db_gen)
            try:
                db.execute(text("SELECT 1"))
                health_status["database"] = "connected"
            finally:
                db.close()
        except Exception as e:
            health_status["database"] = "disconnected"
            health_status["database_error"] = str(e)
            health_status["status"] = "degraded"
    
    return health_status


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to prevent crashes"""
    error_msg = str(exc)
    traceback_str = traceback.format_exc()
    
    print(f"Unhandled exception: {error_msg}")
    print(traceback_str)
    
    # If it's a webhook request, return TwiML error response
    if "/webhooks/twilio" in str(request.url):
        return Response(
            content='<Response><Say>An error occurred. Please try again later.</Say></Response>',
            media_type="application/xml",
            status_code=200  # Return 200 so Twilio doesn't retry
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": error_msg,
            "type": type(exc).__name__
        }
    )

