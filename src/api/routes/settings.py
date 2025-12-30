"""Settings routes for Godfather identity (dev-friendly persistence)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

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


