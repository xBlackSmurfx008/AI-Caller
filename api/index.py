"""
Vercel serverless function entry point for AI Voice Assistant.
"""

import os
import sys
import traceback

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize app
app = FastAPI(
    title="AI Voice Assistant (Vercel)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup logging and settings
try:
    from src.utils.logging import setup_logging
    setup_logging()
except Exception as e:
    print(f"Warning: Failed to setup logging: {e}")

# Start background worker for memory summaries
try:
    from src.memory.background_tasks import start_background_worker
    start_background_worker()
except Exception as e:
    print(f"Warning: Failed to start background worker: {e}")

try:
    from src.utils.config import get_settings
    settings = get_settings()
    cors_origins = settings.CORS_ORIGINS if hasattr(settings, 'CORS_ORIGINS') else ["*"]
except Exception as e:
    print(f"Warning: Failed to load settings: {e}")
    settings = None
    cors_origins = ["*"]

# Initialize database tables
try:
    from src.database.database import init_db
    from src.database import models  # noqa: F401 - Import to register models
    init_db()
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")
    # Continue anyway - tables will be created on first use

# Initialize all integrations
try:
    from src.integrations.manager import get_integration_manager
    integration_manager = get_integration_manager()
    integration_manager.initialize_all()
except Exception as e:
    print(f"Warning: Integration initialization failed: {e}")
    traceback.print_exc()

# Initialize service registry
try:
    from src.services.registry import get_service_registry
    service_registry = get_service_registry()
    service_registry.initialize_services()
except Exception as e:
    print(f"Warning: Service registry initialization failed: {e}")
    traceback.print_exc()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
try:
    from src.api.routes.tasks import router as tasks_router
    app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])
except Exception as e:
    print(f"Warning: Failed to load tasks router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.calendar import router as calendar_router
    app.include_router(calendar_router, prefix="/api/calendar", tags=["calendar"])
except Exception as e:
    print(f"Warning: Failed to load calendar router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.settings import router as settings_router
    app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
except Exception as e:
    print(f"Warning: Failed to load settings router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.contacts import router as contacts_router
    app.include_router(contacts_router, prefix="/api/contacts", tags=["contacts"])
except Exception as e:
    print(f"Warning: Failed to load contacts router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.memory import router as memory_router
    app.include_router(memory_router, prefix="/api/memory", tags=["memory"])
except Exception as e:
    print(f"Warning: Failed to load memory router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.projects import router as projects_router
    app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
except Exception as e:
    print(f"Warning: Failed to load projects router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.goals import router as goals_router
    app.include_router(goals_router, prefix="/api/goals", tags=["goals"])
except Exception as e:
    print(f"Warning: Failed to load goals router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.orchestrator import router as orchestrator_router
    app.include_router(orchestrator_router, prefix="/api/orchestrator", tags=["orchestrator"])
except Exception as e:
    print(f"Warning: Failed to load orchestrator router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.messaging import router as messaging_router
    app.include_router(messaging_router, prefix="/api/messaging", tags=["messaging"])
except Exception as e:
    print(f"Warning: Failed to load messaging router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.preferences import router as preferences_router
    app.include_router(preferences_router, prefix="/api/preferences", tags=["preferences"])
except Exception as e:
    print(f"Warning: Failed to load preferences router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.health import router as health_router
    app.include_router(health_router, prefix="/api", tags=["health"])
except Exception as e:
    print(f"Warning: Failed to load health router: {e}")
    traceback.print_exc()

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

# Serve built frontend (frontend/dist) if present) after API routes so /api/* takes precedence
try:
    from fastapi.staticfiles import StaticFiles
    import pathlib

    # Try multiple possible locations for static files
    project_root = pathlib.Path(__file__).resolve().parent.parent
    frontend_dir = project_root / "frontend" / "dist"
    
    # On Vercel, static build outputs might be at root level
    root_dist = project_root / "dist"
    
    if frontend_dir.exists() and (frontend_dir / "index.html").exists():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
        print(f"Frontend mounted from: {frontend_dir}")
    elif root_dist.exists() and (root_dist / "index.html").exists():
        app.mount("/", StaticFiles(directory=str(root_dist), html=True), name="frontend")
        print(f"Frontend mounted from: {root_dist}")
    else:
        print(f"Warning: Frontend dist not found at {frontend_dir} or {root_dist}")
except Exception as e:
    print(f"Warning: Failed to mount frontend static files: {e}")
    import traceback
    traceback.print_exc()


@app.get("/")
async def root():
    return {"message": "AI Voice Assistant API", "status": "running", "version": "2.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Voice Assistant",
        "settings_loaded": settings is not None,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    error_msg = str(exc)
    traceback_str = traceback.format_exc()
    
    print(f"Unhandled exception: {error_msg}")
    print(traceback_str)
    
    # If it's a webhook request, return TwiML error response
    if "/webhooks/twilio" in str(request.url):
        return Response(
            content='<Response><Say>An error occurred. Please try again later.</Say></Response>',
            media_type="application/xml",
            status_code=200
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": error_msg,
            "type": type(exc).__name__
        }
    )
