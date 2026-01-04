"""Settings routes for Godfather identity and user-level preferences."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import uuid

from src.database.database import get_db
from src.database.models import WorkPreferences, AIAutonomyConfig, GodfatherProfile
from src.utils.autonomy import config_to_dict

from src.security.godfather_store import GodfatherIdentity, load_identity, save_identity

router = APIRouter()


class GodfatherUpdateRequest(BaseModel):
    phone_numbers_csv: str = ""
    email: str = ""


@router.get("/godfather")
async def get_godfather():
    ident = load_identity()
    return {"phone_numbers_csv": ident.phone_numbers_csv, "email": ident.email}


@router.post("/godfather")
async def set_godfather(req: GodfatherUpdateRequest):
    ident = GodfatherIdentity(phone_numbers_csv=req.phone_numbers_csv, email=req.email)
    save_identity(ident)
    return {"success": True}


class WorkPreferencesRequest(BaseModel):
    working_hours_start: str = "09:00"
    working_hours_end: str = "17:00"
    working_days: Optional[List[int]] = None
    buffer_minutes: int = 15
    max_blocks_per_day: int = 8
    timezone: str = "UTC"


@router.get("/work-preferences")
async def get_work_preferences(db: Session = Depends(get_db)):
    prefs = db.query(WorkPreferences).order_by(WorkPreferences.updated_at.desc()).first()
    if not prefs:
        return WorkPreferencesRequest().model_dump()
    return {
        "working_hours_start": prefs.working_hours_start,
        "working_hours_end": prefs.working_hours_end,
        "working_days": prefs.working_days or [1, 2, 3, 4, 5],
        "buffer_minutes": prefs.buffer_minutes,
        "max_blocks_per_day": prefs.max_blocks_per_day,
        "timezone": prefs.timezone,
    }


@router.post("/work-preferences")
async def set_work_preferences(req: WorkPreferencesRequest, db: Session = Depends(get_db)):
    prefs = db.query(WorkPreferences).order_by(WorkPreferences.updated_at.desc()).first()
    if not prefs:
        prefs = WorkPreferences(id=str(uuid.uuid4()))
        db.add(prefs)

    prefs.working_hours_start = req.working_hours_start
    prefs.working_hours_end = req.working_hours_end
    prefs.working_days = req.working_days or [1, 2, 3, 4, 5]
    prefs.buffer_minutes = req.buffer_minutes
    prefs.max_blocks_per_day = req.max_blocks_per_day
    prefs.timezone = req.timezone

    db.commit()
    db.refresh(prefs)
    return {"success": True}


class AIAutonomyUpdateRequest(BaseModel):
    level: str = "balanced"
    auto_execute_high_risk: bool = False
    settings: Optional[Dict[str, Any]] = None


@router.get("/ai-autonomy")
async def get_ai_autonomy(db: Session = Depends(get_db)):
    cfg = db.query(AIAutonomyConfig).order_by(AIAutonomyConfig.updated_at.desc()).first()
    if not cfg:
        return {"level": "balanced", "auto_execute_high_risk": False, "settings": {}}
    return config_to_dict(cfg)


@router.post("/ai-autonomy")
async def set_ai_autonomy(req: AIAutonomyUpdateRequest, db: Session = Depends(get_db)):
    cfg = db.query(AIAutonomyConfig).order_by(AIAutonomyConfig.updated_at.desc()).first()
    if not cfg:
        cfg = AIAutonomyConfig(id=str(uuid.uuid4()))
        db.add(cfg)

    cfg.level = req.level
    cfg.auto_execute_high_risk = bool(req.auto_execute_high_risk)
    cfg.settings = req.settings or {}

    db.commit()
    db.refresh(cfg)
    return {"success": True, "config": config_to_dict(cfg)}


class GodfatherProfileRequest(BaseModel):
    full_name: Optional[str] = None
    preferred_name: Optional[str] = None
    pronouns: Optional[str] = None
    location: Optional[str] = None
    timezone: str = "UTC"
    company: Optional[str] = None
    title: Optional[str] = None
    bio: Optional[str] = None
    assistant_notes: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


@router.get("/profile")
async def get_profile(db: Session = Depends(get_db)):
    prof = db.query(GodfatherProfile).order_by(GodfatherProfile.updated_at.desc()).first()
    if not prof:
        return GodfatherProfileRequest().model_dump()
    return {
        "full_name": prof.full_name,
        "preferred_name": prof.preferred_name,
        "pronouns": prof.pronouns,
        "location": prof.location,
        "timezone": prof.timezone or "UTC",
        "company": prof.company,
        "title": prof.title,
        "bio": prof.bio,
        "assistant_notes": prof.assistant_notes,
        "preferences": prof.preferences or {},
    }


@router.post("/profile")
async def set_profile(req: GodfatherProfileRequest, db: Session = Depends(get_db)):
    prof = db.query(GodfatherProfile).order_by(GodfatherProfile.updated_at.desc()).first()
    if not prof:
        prof = GodfatherProfile(id=str(uuid.uuid4()))
        db.add(prof)

    prof.full_name = req.full_name
    prof.preferred_name = req.preferred_name
    prof.pronouns = req.pronouns
    prof.location = req.location
    prof.timezone = req.timezone or "UTC"
    prof.company = req.company
    prof.title = req.title
    prof.bio = req.bio
    prof.assistant_notes = req.assistant_notes
    prof.preferences = req.preferences or {}

    db.commit()
    db.refresh(prof)
    return {"success": True}

