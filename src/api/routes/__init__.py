"""API routes"""

from fastapi import APIRouter

from src.api.routes import (
    auth,
    calls,
    config,
    knowledge,
    qa,
    escalation,
    notifications,
    analytics,
    agents,
    setup,
    documentation,
    phone_numbers,
)

api_router = APIRouter()

# Include auth routes (no authentication required)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Include all protected route modules
api_router.include_router(calls.router, prefix="/calls", tags=["calls"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(qa.router, prefix="/qa", tags=["qa"])
api_router.include_router(escalation.router, prefix="/escalation", tags=["escalation"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(phone_numbers.router, prefix="/phone-numbers", tags=["phone-numbers"])
api_router.include_router(setup.router, prefix="/setup", tags=["setup"])
api_router.include_router(documentation.router, prefix="/documentation", tags=["documentation"])

