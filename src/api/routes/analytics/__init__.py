"""Analytics routes"""

from fastapi import APIRouter

from . import overview, call_volume, qa_analytics, sentiment, escalations, export

router = APIRouter()

# Include all sub-routers
router.include_router(overview.router)
router.include_router(call_volume.router)
router.include_router(qa_analytics.router)
router.include_router(sentiment.router)
router.include_router(escalations.router)
router.include_router(export.router)

