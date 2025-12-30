"""Suggestion management and expiration handling"""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from src.database.models import Suggestion
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SuggestionManager:
    """Manage suggestion lifecycle and expiration"""
    
    @staticmethod
    def expire_old_suggestions(db: Session, days_old: int = 7) -> int:
        """
        Mark old suggestions as dismissed if they're expired
        
        Args:
            db: Database session
            days_old: Number of days after which to expire suggestions
        
        Returns:
            Number of suggestions expired
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Find expired suggestions
        expired = db.query(Suggestion).filter(
            and_(
                Suggestion.status == "pending",
                Suggestion.expires_at.isnot(None),
                Suggestion.expires_at < datetime.utcnow()
            )
        ).all()
        
        # Also find old suggestions without expiration date
        old_without_expiry = db.query(Suggestion).filter(
            and_(
                Suggestion.status == "pending",
                Suggestion.expires_at.is_(None),
                Suggestion.created_at < cutoff_date
            )
        ).all()
        
        count = 0
        for suggestion in expired + old_without_expiry:
            suggestion.status = "dismissed"
            count += 1
        
        if count > 0:
            db.commit()
            logger.info("suggestions_expired", count=count)
        
        return count
    
    @staticmethod
    def set_suggestion_expiry(
        db: Session,
        suggestion_id: str,
        days: int = 7
    ) -> bool:
        """
        Set expiration date for a suggestion
        
        Args:
            db: Database session
            suggestion_id: Suggestion ID
            days: Number of days until expiration
        
        Returns:
            True if successful
        """
        suggestion = db.query(Suggestion).filter(Suggestion.id == suggestion_id).first()
        if not suggestion:
            return False
        
        suggestion.expires_at = datetime.utcnow() + timedelta(days=days)
        db.commit()
        return True
    
    @staticmethod
    def get_active_suggestions(
        db: Session,
        contact_id: str = None,
        limit: int = 20
    ) -> List[Suggestion]:
        """
        Get active (non-expired, pending) suggestions
        
        Args:
            db: Database session
            contact_id: Optional contact ID filter
            limit: Maximum number to return
        
        Returns:
            List of active suggestions
        """
        now = datetime.utcnow()
        
        query = db.query(Suggestion).filter(
            and_(
                Suggestion.status == "pending",
                (Suggestion.expires_at.is_(None)) | (Suggestion.expires_at > now)
            )
        )
        
        if contact_id:
            query = query.filter(Suggestion.contact_id == contact_id)
        
        return query.order_by(Suggestion.score.desc()).limit(limit).all()

