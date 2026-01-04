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

# Runtime helpers
try:
    from src.utils.runtime import allow_background_tasks
except Exception:
    def allow_background_tasks() -> bool:  # type: ignore
        return False

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

# Background workers (threads / infinite loops) are unsafe on Vercel.
if allow_background_tasks():
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

# Godfather-only auth middleware (align with src/main.py)
try:
    from fastapi import HTTPException
    from src.security.auth import require_godfather, is_auth_exempt

    @app.middleware("http")
    async def _godfather_auth_middleware(request: Request, call_next):
        # Never block Twilio webhooks
        if request.url.path.startswith("/webhooks/twilio"):
            return await call_next(request)
        # Only protect API routes
        if request.url.path.startswith("/api") and not is_auth_exempt(request.url.path):
            try:
                require_godfather(request)
            except HTTPException as e:
                return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        return await call_next(request)
except Exception as e:
    print(f"Warning: Failed to install auth middleware: {e}")

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
    from src.api.routes.commitments import router as commitments_router
    app.include_router(commitments_router, prefix="/api/commitments", tags=["commitments"])
except Exception as e:
    print(f"Warning: Failed to load commitments router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.messaging import router as messaging_router
    app.include_router(messaging_router, prefix="/api/messaging", tags=["messaging"])
except Exception as e:
    print(f"Warning: Failed to load messaging router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.dashboard import router as dashboard_router
    app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
except Exception as e:
    print(f"Warning: Failed to load dashboard router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.project_tasks import router as project_tasks_router
    app.include_router(project_tasks_router, prefix="/api/project-tasks", tags=["project-tasks"])
except Exception as e:
    print(f"Warning: Failed to load project-tasks router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.scheduling import router as scheduling_router
    app.include_router(scheduling_router, prefix="/api/scheduling", tags=["scheduling"])
except Exception as e:
    print(f"Warning: Failed to load scheduling router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.cost import router as cost_router
    app.include_router(cost_router, prefix="/api/cost", tags=["cost"])
except Exception as e:
    print(f"Warning: Failed to load cost router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.preferences import router as preferences_router
    app.include_router(preferences_router, prefix="/api/preferences", tags=["preferences"])
except Exception as e:
    print(f"Warning: Failed to load preferences router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.gmail import router as gmail_router
    app.include_router(gmail_router, prefix="/api/gmail", tags=["gmail"])
except Exception as e:
    print(f"Warning: Failed to load gmail router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.outlook import router as outlook_router
    app.include_router(outlook_router, prefix="/api/outlook", tags=["outlook"])
except Exception as e:
    print(f"Warning: Failed to load outlook router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.audio import router as audio_router
    app.include_router(audio_router, prefix="/api/audio", tags=["audio"])
except Exception as e:
    print(f"Warning: Failed to load audio router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.pec import router as pec_router
    app.include_router(pec_router, prefix="/api", tags=["pec"])
except Exception as e:
    print(f"Warning: Failed to load pec router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.relationship_ops import router as relationship_ops_router
    app.include_router(relationship_ops_router, prefix="/api/relationship-ops", tags=["relationship-ops"])
except Exception as e:
    print(f"Warning: Failed to load relationship-ops router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.imessage import router as imessage_router
    app.include_router(imessage_router, prefix="/api/imessage", tags=["imessage"])
except Exception as e:
    print(f"Warning: Failed to load imessage router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.email_ingest import router as email_ingest_router
    app.include_router(email_ingest_router, prefix="/api/email-ingest", tags=["email-ingest"])
except Exception as e:
    print(f"Warning: Failed to load email-ingest router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.cron import router as cron_router
    app.include_router(cron_router, prefix="/api", tags=["cron"])
except Exception as e:
    print(f"Warning: Failed to load cron router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.health import router as health_router
    app.include_router(health_router, prefix="/api", tags=["health"])
except Exception as e:
    print(f"Warning: Failed to load health router: {e}")
    traceback.print_exc()

try:
    from src.api.routes.ai import router as ai_router
    app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
except Exception as e:
    print(f"Warning: Failed to load ai router: {e}")
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
