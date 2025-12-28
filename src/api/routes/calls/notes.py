"""Call notes endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.database.models import Call, CallNote, BusinessConfig, User
from src.api.schemas.calls import AddNoteRequest
from src.database.schemas import CallNoteResponse, CallNoteUpdate
from src.api.routes.websocket import emit_call_updated
from src.api.middleware.auth import get_current_user
from src.api.utils import handle_service_errors, handle_service_errors_sync
from src.utils.logging import get_logger
from .utils import call_to_response

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{call_id}/notes")
@handle_service_errors_sync
def list_call_notes(
    call_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all notes for a call"""
    # Verify call belongs to user's business configs
    user_business_ids = db.query(BusinessConfig.id).filter(
        BusinessConfig.created_by_user_id == current_user.id
    ).subquery()
    
    call = db.query(Call).filter(
        Call.id == call_id,
        Call.business_id.in_(db.query(user_business_ids))
    ).first()
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    notes = db.query(CallNote).filter(CallNote.call_id == call_id).order_by(CallNote.created_at.desc()).all()
    
    return {"notes": [CallNoteResponse.model_validate(note) for note in notes]}


@router.post("/{call_id}/notes", status_code=status.HTTP_201_CREATED)
@handle_service_errors
async def add_note_to_call(
    call_id: str,
    request: AddNoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a note to a call"""
    # Verify call belongs to user's business configs
    user_business_ids = db.query(BusinessConfig.id).filter(
        BusinessConfig.created_by_user_id == current_user.id
    ).subquery()
    
    call = db.query(Call).filter(
        Call.id == call_id,
        Call.business_id.in_(db.query(user_business_ids))
    ).first()
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Create note using CallNote model
    note = CallNote(
        call_id=call_id,
        created_by_user_id=current_user.id,
        note=request.note,
        tags=request.tags or [],
        category=request.category,
    )
    
    db.add(note)
    db.commit()
    db.refresh(note)
    
    # Emit WebSocket event
    await emit_call_updated(call_to_response(call, db))
    
    logger.info("note_added", call_id=call_id, note_id=note.id, user_id=current_user.id)
    return {
        "success": True,
        "note": CallNoteResponse.model_validate(note),
        "message": "Note added successfully"
    }


@router.put("/{call_id}/notes/{note_id}")
@handle_service_errors
async def update_call_note(
    call_id: str,
    note_id: int,
    request: CallNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a call note"""
    # Verify call belongs to user's business configs
    user_business_ids = db.query(BusinessConfig.id).filter(
        BusinessConfig.created_by_user_id == current_user.id
    ).subquery()
    call = db.query(Call).filter(
        Call.id == call_id,
        Call.business_id.in_(db.query(user_business_ids))
    ).first()
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Get note and verify it belongs to the call and user
    note = db.query(CallNote).filter(
        CallNote.id == note_id,
        CallNote.call_id == call_id,
        CallNote.created_by_user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with ID {note_id} not found"
        )
    
    # Update note fields
    if request.note is not None:
        note.note = request.note
    if request.tags is not None:
        note.tags = request.tags
    if request.category is not None:
        note.category = request.category
    
    db.commit()
    db.refresh(note)
    
    logger.info("note_updated", call_id=call_id, note_id=note_id, user_id=current_user.id)
    return {
        "success": True,
        "note": CallNoteResponse.model_validate(note),
        "message": "Note updated successfully"
    }


@router.delete("/{call_id}/notes/{note_id}")
@handle_service_errors
async def delete_call_note(
    call_id: str,
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a call note"""
    # Verify call belongs to user's business configs
    user_business_ids = db.query(BusinessConfig.id).filter(
        BusinessConfig.created_by_user_id == current_user.id
    ).subquery()
    call = db.query(Call).filter(
        Call.id == call_id,
        Call.business_id.in_(db.query(user_business_ids))
    ).first()
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with ID {call_id} not found"
        )
    
    # Get note and verify it belongs to the call and user
    note = db.query(CallNote).filter(
        CallNote.id == note_id,
        CallNote.call_id == call_id,
        CallNote.created_by_user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with ID {note_id} not found"
        )
    
    db.delete(note)
    db.commit()
    
    logger.info("note_deleted", call_id=call_id, note_id=note_id, user_id=current_user.id)
    return {"success": True, "message": "Note deleted successfully"}

