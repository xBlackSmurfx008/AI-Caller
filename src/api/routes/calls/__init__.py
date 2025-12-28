"""Call management routes"""

from fastapi import APIRouter

from . import crud, actions, notes

router = APIRouter()

# Include all sub-routers
router.include_router(crud.router)
router.include_router(actions.router)
router.include_router(notes.router)

