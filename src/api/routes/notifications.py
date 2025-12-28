"""Notification management routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import uuid
from src.database.models import Notification as NotificationModel
from src.database.database import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel

router = APIRouter()


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    read: bool
    created_at: str
    metadata: Optional[dict] = None
    action_url: Optional[str] = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: Optional[bool] = Query(None, alias="unread_only"),
    type: Optional[str] = Query(None),
    limit: Optional[int] = Query(20, ge=1, le=100),
    offset: Optional[int] = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List notifications"""
    query = db.query(NotificationModel)
    
    if unread_only:
        query = query.filter(NotificationModel.read == False)
    
    if type:
        query = query.filter(NotificationModel.type == type)
    
    total_unread = db.query(NotificationModel).filter(
        NotificationModel.user_id == current_user.id,
        NotificationModel.read == False
    ).count()
    
    notifications = query.order_by(NotificationModel.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "notifications": [
            {
                "id": str(n.id),
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "read": n.read,
                "created_at": n.created_at.isoformat(),
                "metadata": n.meta_data,
                "action_url": n.action_url,
            }
            for n in notifications
        ],
        "unread_count": total_unread,
    }


@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
):
    """Get unread notification count"""
    count = db.query(NotificationModel).filter(
        NotificationModel.user_id == current_user.id,
        NotificationModel.read == False
    ).count()
    return {"unread_count": count}


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
):
    """Mark a notification as read"""
    notification = db.query(NotificationModel).filter(
        NotificationModel.id == notification_id,
        NotificationModel.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.read = True
    db.commit()
    db.refresh(notification)
    
    return {"message": "Notification marked as read"}


@router.patch("/read-all")
async def mark_all_as_read(
    db: Session = Depends(get_db),
):
    """Mark all notifications as read for the current user"""
    db.query(NotificationModel).filter(
        NotificationModel.user_id == current_user.id,
        NotificationModel.read == False
    ).update({"read": True})
    db.commit()
    
    return {"message": "All notifications marked as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
):
    """Delete a notification"""
    notification = db.query(NotificationModel).filter(
        NotificationModel.id == notification_id,
        NotificationModel.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    return {"message": "Notification deleted"}

