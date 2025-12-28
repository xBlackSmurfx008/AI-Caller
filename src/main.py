"""Main FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from src.api.routes import api_router
from src.api.routes.websocket import sio
from src.api.webhooks.twilio_webhook import router as twilio_webhook_router
from src.api.middleware_classes import LoggingMiddleware, RateLimitMiddleware, HTTPSRedirectMiddleware
from src.utils.config import get_settings
from src.utils.logging import setup_logging

# Setup logging
setup_logging()

# Get settings
settings = get_settings()

# Create FastAPI app
fastapi_app = FastAPI(
    title="Enterprise AI Caller System",
    description="AI-powered call center system with OpenAI Voice API and Twilio",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTPS redirect middleware (must be first)
fastapi_app.add_middleware(HTTPSRedirectMiddleware)

# Logging middleware
fastapi_app.add_middleware(LoggingMiddleware)

# Rate limiting middleware
fastapi_app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

# Include API routes
fastapi_app.include_router(api_router, prefix="/api/v1")

# Include webhook routes
fastapi_app.include_router(twilio_webhook_router, prefix="/webhooks/twilio", tags=["webhooks"])


def _check_health():
    """Health check logic - extracted to avoid duplication"""
    from datetime import datetime
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": {"status": "unknown", "error": None},
        "redis": {"status": "unknown", "error": None},
    }
    
    # Check database connectivity with proper context management
    try:
        from src.database.database import get_db
        db_gen = get_db()
        db = next(db_gen)
        try:
            db.execute(text("SELECT 1"))
            health_status["database"]["status"] = "connected"
        finally:
            db.close()
    except Exception as e:
        health_status["database"]["status"] = "disconnected"
        health_status["database"]["error"] = str(e)
        health_status["status"] = "degraded"
    
    # Check Redis connectivity
    try:
        import redis
        redis_client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        redis_client.ping()
        health_status["redis"]["status"] = "connected"
        redis_client.close()
    except Exception as e:
        health_status["redis"]["status"] = "disconnected"
        health_status["redis"]["error"] = str(e)
        # Redis is optional, so we don't mark as degraded if it fails
    
    # Determine overall status
    if health_status["database"]["status"] != "connected":
        health_status["status"] = "unhealthy"
    
    return health_status


@fastapi_app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Enterprise AI Caller System API",
        "version": "1.0.0",
        "status": "running"
    }


@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint with database and Redis connectivity checks"""
    return _check_health()


# Mount Socket.IO app on /ws/calls path
app = socketio.ASGIApp(sio, fastapi_app, socketio_path="/ws/calls")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

