"""Commitment management and status updates"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from src.database.models import Commitment, Contact
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CommitmentManager:
    """Manage commitment lifecycle and status updates"""
    
    @staticmethod
    def update_overdue_commitments(db: Session) -> int:
        """
        Mark commitments as overdue if deadline has passed
        
        Args:
            db: Database session
        
        Returns:
            Number of commitments marked as overdue
        """
        now = datetime.utcnow()
        
        overdue = db.query(Commitment).filter(
            and_(
                Commitment.status == "pending",
                Commitment.deadline.isnot(None),
                Commitment.deadline < now
            )
        ).all()
        
        count = 0
        for commitment in overdue:
            commitment.status = "overdue"
            # Mark as trust risk if overdue by more than 7 days
            days_overdue = (now - commitment.deadline).days
            if days_overdue > 7:
                commitment.is_trust_risk = True
            count += 1
        
        if count > 0:
            db.commit()
            logger.info("commitments_marked_overdue", count=count)
        
        return count
    
    @staticmethod
    def detect_commitment_completion(
        db: Session,
        contact_id: str,
        interaction_summary: str
    ) -> List[str]:
        """
        Detect if commitments were completed based on interaction summary
        
        Uses simple keyword matching - could be enhanced with AI
        
        Args:
            db: Database session
            contact_id: Contact ID
            interaction_summary: Summary text from interaction
        
        Returns:
            List of commitment IDs that were likely completed
        """
        # Get pending commitments for this contact
        pending_commitments = db.query(Commitment).filter(
            and_(
                Commitment.contact_id == contact_id,
                Commitment.status.in_(["pending", "overdue"])
            )
        ).all()
        
        completed_ids = []
        summary_lower = interaction_summary.lower()
        
        # Keywords that suggest completion
        completion_keywords = [
            "completed", "done", "finished", "accomplished", "delivered",
            "sent", "provided", "submitted", "fulfilled", "met"
        ]
        
        for commitment in pending_commitments:
            # Check if summary mentions the commitment
            commitment_keywords = commitment.description.lower().split()[:3]  # First 3 words
            if any(keyword in summary_lower for keyword in commitment_keywords):
                # Check if completion keywords are present
                if any(keyword in summary_lower for keyword in completion_keywords):
                    commitment.status = "completed"
                    commitment.is_trust_risk = False
                    completed_ids.append(commitment.id)
                    logger.info(
                        "commitment_completed_detected",
                        commitment_id=commitment.id,
                        description=commitment.description[:50]
                    )
        
        if completed_ids:
            db.commit()
        
        return completed_ids
    
    @staticmethod
    def get_commitments_for_contact(
        db: Session,
        contact_id: str,
        status: Optional[str] = None
    ) -> List[Commitment]:
        """
        Get commitments for a contact with optional status filter
        
        Args:
            db: Database session
            contact_id: Contact ID
            status: Optional status filter
        
        Returns:
            List of Commitment objects
        """
        query = db.query(Commitment).filter(Commitment.contact_id == contact_id)
        
        if status:
            query = query.filter(Commitment.status == status)
        
        return query.order_by(Commitment.deadline.asc()).all()
    
    @staticmethod
    def get_trust_risk_commitments(db: Session) -> List[Commitment]:
        """
        Get all commitments flagged as trust risks
        
        Args:
            db: Database session
        
        Returns:
            List of Commitment objects with is_trust_risk=True
        """
        return db.query(Commitment).filter(
            Commitment.is_trust_risk == True
        ).order_by(Commitment.deadline.asc()).all()

