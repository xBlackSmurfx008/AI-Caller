"""Preferences/Trusted List API routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.database.database import get_db
from src.database.models import PreferenceEntry, PreferenceCategory
from src.utils.logging import get_logger
from src.utils.auth import require_user_id, filter_by_user

logger = get_logger(__name__)
router = APIRouter()


# Pydantic models
class PreferenceEntryCreate(BaseModel):
    type: str  # VENDOR | PROVIDER | WEBSITE | LOCATION | TOOL | AVOID
    category: str
    name: str
    priority: str = "PRIMARY"  # PRIMARY | SECONDARY | AVOID
    tags: Optional[List[str]] = None
    url: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    constraints: Optional[dict] = None
    related_contact_id: Optional[str] = None


class PreferenceEntryUpdate(BaseModel):
    type: Optional[str] = None
    category: Optional[str] = None
    name: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    url: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    constraints: Optional[dict] = None
    related_contact_id: Optional[str] = None


class PreferenceEntryResponse(BaseModel):
    id: str
    owner_user_id: Optional[str] = None
    type: str
    category: str
    name: str
    priority: str
    tags: Optional[List[str]] = None
    url: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    constraints: Optional[dict] = None
    last_used_at: Optional[str] = None
    related_contact_id: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PreferenceCategoryResponse(BaseModel):
    id: str
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    default_entry_id: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PreferenceResolveRequest(BaseModel):
    task_request: str
    context: Optional[dict] = None


class PreferenceResolveResponse(BaseModel):
    chosen_default: Optional[dict] = None
    alternatives: List[dict] = []
    avoid_list: List[dict] = []
    required_confirmations: List[dict] = []
    constraints_applied: dict = {}
    intent: str


# Helper function to convert model to response
def _entry_to_response(entry: PreferenceEntry) -> PreferenceEntryResponse:
    return PreferenceEntryResponse(
        id=entry.id,
        owner_user_id=entry.owner_user_id,
        type=entry.type,
        category=entry.category,
        name=entry.name,
        priority=entry.priority,
        tags=entry.tags,
        url=entry.url,
        phone=entry.phone,
        address=entry.address,
        notes=entry.notes,
        constraints=entry.constraints,
        last_used_at=entry.last_used_at.isoformat() if entry.last_used_at else None,
        related_contact_id=entry.related_contact_id,
        created_at=entry.created_at.isoformat(),
        updated_at=entry.updated_at.isoformat()
    )


@router.get("/", response_model=List[PreferenceEntryResponse])
async def list_preferences(
    category: Optional[str] = None,
    type: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """List all preferences with optional filters"""
    query = db.query(PreferenceEntry)
    query = filter_by_user(query, user_id, PreferenceEntry, db)
    
    if category:
        query = query.filter(PreferenceEntry.category == category)
    if type:
        query = query.filter(PreferenceEntry.type == type)
    if priority:
        query = query.filter(PreferenceEntry.priority == priority)
    if search:
        query = query.filter(
            or_(
                PreferenceEntry.name.ilike(f"%{search}%"),
                PreferenceEntry.notes.ilike(f"%{search}%")
            )
        )
    
    # Order by priority (PRIMARY > SECONDARY > AVOID), then by last_used_at (most recent first), then by created_at
    from sqlalchemy import case
    priority_order = case(
        (PreferenceEntry.priority == "PRIMARY", 1),
        (PreferenceEntry.priority == "SECONDARY", 2),
        (PreferenceEntry.priority == "AVOID", 3),
        else_=4
    )
    entries = query.order_by(
        priority_order.asc(),
        PreferenceEntry.last_used_at.desc(),
        PreferenceEntry.created_at.desc()
    ).all()
    
    return [_entry_to_response(entry) for entry in entries]


@router.get("/categories", response_model=List[PreferenceCategoryResponse])
async def list_categories(
    db: Session = Depends(get_db)
):
    """List all preference categories"""
    categories = db.query(PreferenceCategory).order_by(PreferenceCategory.name).all()
    return [
        PreferenceCategoryResponse(
            id=cat.id,
            name=cat.name,
            display_name=cat.display_name,
            description=cat.description,
            default_entry_id=cat.default_entry_id,
            created_at=cat.created_at.isoformat(),
            updated_at=cat.updated_at.isoformat()
        )
        for cat in categories
    ]


@router.get("/{entry_id}", response_model=PreferenceEntryResponse)
async def get_preference(
    entry_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """Get a specific preference entry"""
    entry = db.query(PreferenceEntry).filter(PreferenceEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found")
    
    # Check user access
    if entry.owner_user_id and entry.owner_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return _entry_to_response(entry)


@router.post("/", response_model=PreferenceEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_preference(
    data: PreferenceEntryCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """Create a new preference entry"""
    # Validate type and priority
    valid_types = ["VENDOR", "PROVIDER", "WEBSITE", "LOCATION", "TOOL", "AVOID"]
    valid_priorities = ["PRIMARY", "SECONDARY", "AVOID"]
    
    if data.type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid type. Must be one of: {', '.join(valid_types)}"
        )
    
    if data.priority not in valid_priorities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
        )
    
    # Create entry
    entry = PreferenceEntry(
        owner_user_id=user_id,
        type=data.type,
        category=data.category,
        name=data.name,
        priority=data.priority,
        tags=data.tags,
        url=data.url,
        phone=data.phone,
        address=data.address,
        notes=data.notes,
        constraints=data.constraints,
        related_contact_id=data.related_contact_id
    )
    
    db.add(entry)
    db.commit()
    db.refresh(entry)
    
    logger.info("preference_created", entry_id=entry.id, category=data.category, name=data.name)
    return _entry_to_response(entry)


@router.put("/{entry_id}", response_model=PreferenceEntryResponse)
async def update_preference(
    entry_id: str,
    data: PreferenceEntryUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """Update a preference entry"""
    entry = db.query(PreferenceEntry).filter(PreferenceEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found")
    
    # Check user access
    if entry.owner_user_id and entry.owner_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Update fields
    if data.type is not None:
        valid_types = ["VENDOR", "PROVIDER", "WEBSITE", "LOCATION", "TOOL", "AVOID"]
        if data.type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid type. Must be one of: {', '.join(valid_types)}"
            )
        entry.type = data.type
    
    if data.category is not None:
        entry.category = data.category
    if data.name is not None:
        entry.name = data.name
    if data.priority is not None:
        valid_priorities = ["PRIMARY", "SECONDARY", "AVOID"]
        if data.priority not in valid_priorities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
            )
        entry.priority = data.priority
    if data.tags is not None:
        entry.tags = data.tags
    if data.url is not None:
        entry.url = data.url
    if data.phone is not None:
        entry.phone = data.phone
    if data.address is not None:
        entry.address = data.address
    if data.notes is not None:
        entry.notes = data.notes
    if data.constraints is not None:
        entry.constraints = data.constraints
    if data.related_contact_id is not None:
        entry.related_contact_id = data.related_contact_id
    
    entry.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(entry)
    
    logger.info("preference_updated", entry_id=entry_id)
    return _entry_to_response(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preference(
    entry_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """Delete a preference entry"""
    entry = db.query(PreferenceEntry).filter(PreferenceEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found")
    
    # Check user access
    if entry.owner_user_id and entry.owner_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    db.delete(entry)
    db.commit()
    
    logger.info("preference_deleted", entry_id=entry_id)


@router.post("/resolve", response_model=PreferenceResolveResponse)
async def resolve_preferences(
    request: PreferenceResolveRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id)
):
    """Resolve preferences for a task request"""
    from src.orchestrator.preference_resolver import PreferenceResolver
    
    resolver = PreferenceResolver()
    
    # Add user_id to context
    context = request.context or {}
    context["user_id"] = user_id
    
    result = resolver.resolve_preferences(db, request.task_request, context)
    
    return PreferenceResolveResponse(**result)

