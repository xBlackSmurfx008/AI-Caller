"""Main FastAPI application entry point"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes.tasks import router as tasks_router
from src.api.routes.calendar import router as calendar_router
from src.api.routes.settings import router as settings_router
from src.api.routes.contacts import router as contacts_router
from src.api.routes.memory import router as memory_router
from src.api.routes.projects import router as projects_router
from src.api.routes.goals import router as goals_router
from src.api.routes.orchestrator import router as orchestrator_router
from src.api.routes.commitments import router as commitments_router
from src.api.routes.messaging import router as messaging_router
from src.api.routes.dashboard import router as dashboard_router
from src.api.routes.health import router as health_router
from src.api.routes.project_tasks import router as project_tasks_router
from src.api.routes.scheduling import router as scheduling_router
from src.api.routes.cost import router as cost_router
from src.api.routes.preferences import router as preferences_router
from src.api.routes.gmail import router as gmail_router
from src.api.routes.outlook import router as outlook_router
from src.api.routes.audio import router as audio_router
from src.api.routes.pec import router as pec_router
from src.api.routes.relationship_ops import router as relationship_ops_router
from src.api.webhooks.twilio_webhook import router as twilio_webhook_router
from src.utils.config import get_settings
from src.integrations.manager import get_integration_manager
from src.utils.logging import setup_logging
from src.security.auth import require_godfather, is_auth_exempt
from src.utils.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from src.calendar.reminders import ReminderEngine
from src.database.database import init_db
from src.utils.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from src.orchestrator.commitment_manager import CommitmentManager
# Import all models to ensure they're registered with SQLAlchemy
from src.database import models  # noqa: F401

# Setup logging
setup_logging()

# Get settings
settings = get_settings()

# Initialize database tables
try:
    init_db()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Database initialization warning: {e}")

# Initialize all integrations
try:
    integration_manager = get_integration_manager()
    integration_manager.initialize_all()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Integration initialization warning: {e}")

# Initialize service registry
try:
    from src.services.registry import get_service_registry
    service_registry = get_service_registry()
    service_registry.initialize_services()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Service registry initialization warning: {e}")

# Start background worker for memory summaries
try:
    from src.memory.background_tasks import start_background_worker
    start_background_worker()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Background worker initialization warning: {e}")

# Create FastAPI app
app = FastAPI(
    title="AI Voice Assistant",
    description="Voice-to-voice AI assistant that executes tasks via calling, texting, and emailing",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Auth middleware (Godfather-only)
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Rate limit exceeded: {exc.detail}",
            "retry_after": exc.retry_after
        }
    )

# Include routes
app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])
app.include_router(calendar_router, prefix="/api/calendar", tags=["calendar"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
app.include_router(contacts_router, prefix="/api/contacts", tags=["contacts"])
app.include_router(memory_router, prefix="/api/memory", tags=["memory"])
app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
app.include_router(goals_router, prefix="/api/goals", tags=["goals"])
app.include_router(orchestrator_router, prefix="/api/orchestrator", tags=["orchestrator"])
app.include_router(commitments_router, prefix="/api/commitments", tags=["commitments"])
app.include_router(messaging_router, prefix="/api/messaging", tags=["messaging"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(project_tasks_router, prefix="/api/project-tasks", tags=["project-tasks"])
app.include_router(scheduling_router, prefix="/api/scheduling", tags=["scheduling"])
app.include_router(cost_router, prefix="/api/cost", tags=["cost"])
app.include_router(preferences_router, prefix="/api/preferences", tags=["preferences"])
app.include_router(gmail_router, prefix="/api/gmail", tags=["gmail"])
app.include_router(outlook_router, prefix="/api/outlook", tags=["outlook"])
app.include_router(audio_router, prefix="/api/audio", tags=["audio"])
app.include_router(pec_router, prefix="/api", tags=["pec"])
app.include_router(relationship_ops_router, prefix="/api/relationship-ops", tags=["relationship-ops"])
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(twilio_webhook_router, prefix="/webhooks/twilio", tags=["webhooks"])

_reminders = ReminderEngine()
_commitment_manager = CommitmentManager()
from src.messaging.background_tasks import _messaging_background_tasks


@app.on_event("startup")
async def _start_background_tasks():
    """Start background tasks for reminders and commitment updates"""
    import asyncio
    
    async def _reminder_loop():
        while True:
            try:
                await _reminders.run_once()
            except Exception:
                pass
            await asyncio.sleep(60)
    
    async def _commitment_update_loop():
        """Update overdue commitments daily"""
        from src.database.database import SessionLocal
        while True:
            try:
                # Wait until next day at 2 AM
                await asyncio.sleep(3600)  # Check every hour
                from datetime import datetime
                now = datetime.utcnow()
                if now.hour == 2:  # Run at 2 AM UTC
                    db = SessionLocal()
                    try:
                        count = _commitment_manager.update_overdue_commitments(db)
                        if count > 0:
                            import logging
                            logging.getLogger(__name__).info(f"Updated {count} overdue commitments")
                    finally:
                        db.close()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Commitment update loop error: {e}")
    
    async def _messaging_summary_loop():
        """Process conversation summaries in background"""
        await _messaging_background_tasks.run_periodic_tasks(interval_seconds=300)  # Every 5 minutes
    
    async def _suggestion_expiration_loop():
        """Expire old suggestions daily"""
        from src.database.database import SessionLocal
        from src.orchestrator.suggestion_manager import SuggestionManager
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                from datetime import datetime
                now = datetime.utcnow()
                if now.hour == 3:  # Run at 3 AM UTC (after commitment updates)
                    db = SessionLocal()
                    try:
                        count = SuggestionManager.expire_old_suggestions(db)
                        if count > 0:
                            import logging
                            logging.getLogger(__name__).info(f"Expired {count} old suggestions")
                    finally:
                        db.close()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Suggestion expiration loop error: {e}")
    
    async def _daily_suggestion_generation():
        """Generate suggestions daily at 9 AM"""
        from src.database.database import SessionLocal
        from src.orchestrator.orchestrator_service import OrchestratorService
        orchestrator = OrchestratorService()
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                from datetime import datetime
                now = datetime.utcnow()
                if now.hour == 9:  # Run at 9 AM UTC
                    db = SessionLocal()
                    try:
                        suggestions = orchestrator.generate_suggestions(db, limit=50)
                        import logging
                        logging.getLogger(__name__).info(f"Generated {len(suggestions)} daily suggestions")
                    finally:
                        db.close()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Daily suggestion generation error: {e}")
    
    async def _weekly_review_generation():
        """Generate weekly review on Mondays at 8 AM"""
        from src.database.database import SessionLocal
        from src.orchestrator.weekly_review import WeeklyReviewGenerator
        review_gen = WeeklyReviewGenerator()
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                from datetime import datetime
                now = datetime.utcnow()
                if now.weekday() == 0 and now.hour == 8:  # Monday at 8 AM UTC
                    db = SessionLocal()
                    try:
                        review = review_gen.generate_weekly_review(db)
                        import logging
                        logging.getLogger(__name__).info("Weekly review generated", week_start=review.get("week_start"))
                        # TODO: Send review via email/notification
                    finally:
                        db.close()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Weekly review generation error: {e}")
    
    async def _budget_check_loop():
        """Check budgets and generate alerts periodically"""
        from src.database.database import SessionLocal
        from src.cost.budget_manager import BudgetManager
        budget_manager = BudgetManager()
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                db = SessionLocal()
                try:
                    alerts = budget_manager.check_budgets(db)
                    if alerts:
                        import logging
                        logging.getLogger(__name__).info(f"Generated {len(alerts)} budget alerts")
                finally:
                    db.close()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Budget check loop error: {e}")
    
    async def _relationship_ops_scheduler():
        """
        Master Networker CRM - Scheduled Relationship Ops Runs
        
        Runs 4 times daily (America/New_York timezone):
        - 5:30 AM: Morning Command Plan
        - 12:00 PM: Midday Momentum Push
        - 4:30 PM: Afternoon Coordination & Follow-Up
        - 8:00 PM: Relationship Review + Next-Day Prep
        """
        import pytz
        from src.database.database import SessionLocal
        from src.orchestrator.relationship_ops import RelationshipOpsService
        
        tz = pytz.timezone("America/New_York")
        service = RelationshipOpsService()
        
        # Schedule configuration: (hour, minute, run_type)
        schedules = [
            (5, 30, "morning"),
            (12, 0, "midday"),
            (16, 30, "afternoon"),
            (20, 0, "evening")
        ]
        
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                from datetime import datetime
                now = datetime.now(tz)
                current_hour = now.hour
                current_minute = now.minute
                
                for hour, minute, run_type in schedules:
                    if current_hour == hour and current_minute == minute:
                        db = SessionLocal()
                        try:
                            import logging
                            logging.getLogger(__name__).info(f"Starting relationship ops {run_type} run")
                            result = service.execute_run(db, run_type)
                            logging.getLogger(__name__).info(
                                f"Relationship ops {run_type} run completed: {result.id}",
                                extra={"actions": len(result.top_actions or [])}
                            )
                        except Exception as e:
                            import logging
                            logging.getLogger(__name__).error(f"Relationship ops {run_type} run failed: {e}")
                        finally:
                            db.close()
                        
                        # Wait 61 seconds to avoid re-triggering in same minute
                        await asyncio.sleep(61)
                        break
                        
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Relationship ops scheduler error: {e}")
    
    asyncio.create_task(_reminder_loop())
    asyncio.create_task(_commitment_update_loop())
    asyncio.create_task(_messaging_summary_loop())
    asyncio.create_task(_suggestion_expiration_loop())
    asyncio.create_task(_daily_suggestion_generation())
    asyncio.create_task(_weekly_review_generation())
    asyncio.create_task(_budget_check_loop())
    asyncio.create_task(_relationship_ops_scheduler())


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Voice Assistant API",
        "version": "2.0.0",
        "status": "running"
    }




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.APP_HOST, port=settings.APP_PORT)
