"""Weekly Godfather Review Generator"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
import json

from src.database.models import (
    Contact, ContactMemoryState, Project, Goal, Commitment, Suggestion
)
from src.utils.config import get_settings
from src.utils.openai_client import ensure_chat_model, create_openai_client, retry_openai_call
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class WeeklyReviewGenerator:
    """Generate weekly Godfather Review reports"""
    
    def __init__(self):
        """Initialize review generator"""
        self.client = create_openai_client(timeout=60.0, max_retries=3)
        self.model = ensure_chat_model(settings.OPENAI_MODEL)
    
    def generate_weekly_review(
        self,
        db: Session,
        week_start: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive weekly review
        
        Args:
            db: Database session
            week_start: Start of week (defaults to Monday of current week)
        
        Returns:
            Dictionary with weekly review data
        """
        if not week_start:
            # Get Monday of current week
            today = datetime.utcnow()
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        week_end = week_start + timedelta(days=7)
        
        # Gather data
        relationship_health = self._analyze_relationship_health(db, week_start, week_end)
        missed_commitments = self._find_missed_commitments(db, week_start, week_end)
        gratitude_opportunities = self._find_gratitude_opportunities(db, week_start, week_end)
        project_status = self._analyze_project_status(db)
        best_next_moves = self._suggest_best_next_moves(db)
        improvement_areas = self._identify_improvement_areas(
            db, relationship_health, missed_commitments
        )
        
        # Generate AI summary
        ai_summary = self._generate_ai_summary(
            relationship_health,
            missed_commitments,
            gratitude_opportunities,
            project_status,
            improvement_areas
        )
        
        return {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "relationship_health": relationship_health,
            "missed_commitments": missed_commitments,
            "gratitude_opportunities": gratitude_opportunities,
            "project_status": project_status,
            "best_next_moves": best_next_moves,
            "improvement_areas": improvement_areas,
            "ai_summary": ai_summary
        }
    
    def _analyze_relationship_health(
        self,
        db: Session,
        week_start: datetime,
        week_end: datetime
    ) -> Dict[str, Any]:
        """Analyze overall relationship health"""
        contacts_with_memory = db.query(Contact).join(ContactMemoryState).all()
        
        total_contacts = len(contacts_with_memory)
        positive_relationships = 0
        declining_relationships = 0
        high_trust_contacts = 0
        
        relationship_details = []
        
        for contact in contacts_with_memory:
            memory_state = db.query(ContactMemoryState).filter(
                ContactMemoryState.contact_id == contact.id
            ).first()
            
            if not memory_state:
                continue
            
            sentiment = memory_state.sentiment_trend or "neutral"
            score = contact.relationship_score or 0.0
            
            if sentiment in ["positive", "improving"]:
                positive_relationships += 1
            elif sentiment in ["negative", "declining"]:
                declining_relationships += 1
            
            if score > 0.7:
                high_trust_contacts += 1
            
            relationship_details.append({
                "contact_id": contact.id,
                "contact_name": contact.name,
                "relationship_score": score,
                "sentiment_trend": sentiment,
                "last_interaction": memory_state.last_interaction_at.isoformat() if memory_state.last_interaction_at else None
            })
        
        return {
            "total_contacts": total_contacts,
            "positive_relationships": positive_relationships,
            "declining_relationships": declining_relationships,
            "high_trust_contacts": high_trust_contacts,
            "average_relationship_score": sum(c.relationship_score or 0.0 for c in contacts_with_memory) / max(total_contacts, 1),
            "details": relationship_details[:20]  # Top 20
        }
    
    def _find_missed_commitments(
        self,
        db: Session,
        week_start: datetime,
        week_end: datetime
    ) -> List[Dict[str, Any]]:
        """Find missed or overdue commitments"""
        overdue = db.query(Commitment).filter(
            and_(
                Commitment.status == "pending",
                Commitment.deadline < datetime.utcnow()
            )
        ).all()
        
        missed = []
        for commitment in overdue:
            contact = db.query(Contact).filter(Contact.id == commitment.contact_id).first()
            days_overdue = (datetime.utcnow() - commitment.deadline).days if commitment.deadline else 0
            
            missed.append({
                "commitment_id": commitment.id,
                "description": commitment.description,
                "contact_id": commitment.contact_id,
                "contact_name": contact.name if contact else "Unknown",
                "deadline": commitment.deadline.isoformat() if commitment.deadline else None,
                "days_overdue": days_overdue,
                "is_trust_risk": days_overdue > 7
            })
        
        # Sort by days overdue
        missed.sort(key=lambda x: x["days_overdue"], reverse=True)
        
        return missed
    
    def _find_gratitude_opportunities(
        self,
        db: Session,
        week_start: datetime,
        week_end: datetime
    ) -> List[Dict[str, Any]]:
        """Find opportunities to express gratitude"""
        # Find contacts who helped us this week
        # This is a simplified version - in production, you'd track "help received" events
        
        contacts_with_positive_sentiment = db.query(Contact).join(ContactMemoryState).filter(
            ContactMemoryState.sentiment_trend.in_(["positive", "improving"])
        ).all()
        
        opportunities = []
        for contact in contacts_with_positive_sentiment[:10]:  # Top 10
            memory_state = db.query(ContactMemoryState).filter(
                ContactMemoryState.contact_id == contact.id
            ).first()
            
            if memory_state and memory_state.last_interaction_at:
                days_since = (datetime.utcnow() - memory_state.last_interaction_at).days
                if days_since < 7:  # Recent positive interaction
                    opportunities.append({
                        "contact_id": contact.id,
                        "contact_name": contact.name,
                        "reason": f"Recent positive interaction ({days_since} days ago)",
                        "suggested_action": "Send a thank you message"
                    })
        
        return opportunities
    
    def _analyze_project_status(self, db: Session) -> Dict[str, Any]:
        """Analyze status of all projects"""
        active_projects = db.query(Project).filter(Project.status == "active").all()
        completed_projects = db.query(Project).filter(Project.status == "completed").all()
        
        project_details = []
        for project in active_projects:
            stakeholders = db.query(ProjectStakeholder).filter(
                ProjectStakeholder.project_id == project.id
            ).count()
            
            project_details.append({
                "project_id": project.id,
                "title": project.title,
                "status": project.status,
                "stakeholder_count": stakeholders,
                "milestones": project.milestones or []
            })
        
        return {
            "active_count": len(active_projects),
            "completed_count": len(completed_projects),
            "projects": project_details
        }
    
    def _suggest_best_next_moves(self, db: Session) -> List[Dict[str, Any]]:
        """Suggest best next moves based on current state"""
        # Get top pending suggestions
        top_suggestions = db.query(Suggestion).filter(
            Suggestion.status == "pending"
        ).order_by(Suggestion.score.desc()).limit(10).all()
        
        moves = []
        for suggestion in top_suggestions:
            contact = db.query(Contact).filter(Contact.id == suggestion.contact_id).first()
            
            moves.append({
                "suggestion_id": suggestion.id,
                "type": suggestion.suggestion_type,
                "intent": suggestion.intent,
                "contact_name": contact.name if contact else "Unknown",
                "best_timing": suggestion.best_timing,
                "score": suggestion.score
            })
        
        return moves
    
    def _identify_improvement_areas(
        self,
        db: Session,
        relationship_health: Dict[str, Any],
        missed_commitments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify areas for improvement"""
        improvements = []
        
        # Check for trust risks
        trust_risks = [c for c in missed_commitments if c.get("is_trust_risk")]
        if trust_risks:
            improvements.append({
                "area": "Commitment Follow-through",
                "issue": f"{len(trust_risks)} commitments are overdue by more than 7 days",
                "recommendation": "Prioritize following up on overdue commitments to maintain trust"
            })
        
        # Check for declining relationships
        declining = relationship_health.get("declining_relationships", 0)
        if declining > 0:
            improvements.append({
                "area": "Relationship Maintenance",
                "issue": f"{declining} relationships are declining",
                "recommendation": "Reach out to declining relationships with value-first actions"
            })
        
        # Check for low interaction frequency
        low_interaction_contacts = []
        contacts = db.query(Contact).join(ContactMemoryState).all()
        for contact in contacts:
            memory_state = db.query(ContactMemoryState).filter(
                ContactMemoryState.contact_id == contact.id
            ).first()
            
            if memory_state and memory_state.last_interaction_at:
                days_since = (datetime.utcnow() - memory_state.last_interaction_at).days
                if days_since > 30:
                    low_interaction_contacts.append(contact.name)
        
        if len(low_interaction_contacts) > 5:
            improvements.append({
                "area": "Network Engagement",
                "issue": f"{len(low_interaction_contacts)} contacts haven't been contacted in 30+ days",
                "recommendation": "Schedule regular check-ins with key contacts"
            })
        
        return improvements
    
    def _generate_ai_summary(
        self,
        relationship_health: Dict[str, Any],
        missed_commitments: List[Dict[str, Any]],
        gratitude_opportunities: List[Dict[str, Any]],
        project_status: Dict[str, Any],
        improvement_areas: List[Dict[str, Any]]
    ) -> str:
        """Generate AI-powered summary of the week"""
        prompt = f"""Generate a comprehensive weekly review summary for the Godfather.

Relationship Health:
- Total contacts: {relationship_health.get('total_contacts', 0)}
- Positive relationships: {relationship_health.get('positive_relationships', 0)}
- Declining relationships: {relationship_health.get('declining_relationships', 0)}
- High trust contacts: {relationship_health.get('high_trust_contacts', 0)}
- Average relationship score: {relationship_health.get('average_relationship_score', 0):.2f}

Missed Commitments: {len(missed_commitments)}
Gratitude Opportunities: {len(gratitude_opportunities)}
Active Projects: {project_status.get('active_count', 0)}

Improvement Areas:
{json.dumps(improvement_areas, indent=2)}

Provide a thoughtful, actionable summary that:
1. Highlights wins and positive trends
2. Identifies trust risks and areas needing attention
3. Suggests specific actions for the coming week
4. Maintains a balance between ambition and relationship health
5. Emphasizes win-win opportunities and reciprocity

Write in a supportive, coaching tone that helps the Godfather be a better human while achieving goals."""
        
        try:
            @retry_openai_call(max_retries=3, initial_delay=0.5, max_delay=30.0)
            def _call():
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert relationship coach and strategic advisor. Provide thoughtful, actionable insights."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5,
                    max_tokens=1000,
                    timeout=45,
                )
            
            response = _call()
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("ai_summary_generation_failed", error=str(e))
            return "Unable to generate AI summary at this time."

