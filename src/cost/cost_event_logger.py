"""Cost Event Logger - Single source of truth for cost events"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from src.database.models import CostEvent
from src.cost.pricing_registry import PricingRegistry
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CostEventLogger:
    """Logs atomic cost events (single source of truth)"""
    
    def __init__(self):
        """Initialize cost event logger"""
        self.pricing_registry = PricingRegistry()
    
    def log_cost_event(
        self,
        db: Session,
        provider: str,
        service: str,
        metric_type: str,
        units: float,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        event_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        effective_date: Optional[datetime] = None
    ) -> CostEvent:
        """
        Log a cost event
        
        Args:
            db: Database session
            provider: API provider (e.g., "openai", "twilio")
            service: Service name (e.g., "chat", "sms")
            metric_type: Type of metric ("tokens", "requests", "messages", "minutes", "images")
            units: Number of units consumed
            task_id: Associated task ID
            project_id: Associated project ID
            agent_id: Agent identifier
            execution_id: AIExecution ID
            event_id: Provider request ID (for idempotency)
            metadata: Additional metadata (model, endpoint, region, etc.)
            effective_date: Date for pricing resolution (defaults to now)
        
        Returns:
            Created CostEvent
        """
        # Check for duplicate if event_id provided
        if event_id:
            existing = db.query(CostEvent).filter(CostEvent.event_id == event_id).first()
            if existing:
                logger.info("cost_event_duplicate_skipped", event_id=event_id)
                return existing
        
        # Calculate cost using pricing registry
        cost_calc = self.pricing_registry.calculate_cost(
            db=db,
            provider=provider,
            service=service,
            metric_type=metric_type,
            units=units,
            effective_date=effective_date or datetime.utcnow(),
            metadata=metadata
        )
        
        # Create cost event
        cost_event = CostEvent(
            event_id=event_id,
            task_id=task_id,
            project_id=project_id,
            agent_id=agent_id,
            execution_id=execution_id,
            provider=provider,
            service=service,
            metric_type=metric_type,
            units=units,
            unit_cost=cost_calc["unit_cost"],
            total_cost=cost_calc["total_cost"],
            meta_data=metadata or {},  # Use meta_data (maps to "metadata" column)
            is_priced=cost_calc["is_priced"],
            timestamp=datetime.utcnow()
        )
        
        db.add(cost_event)
        db.commit()
        db.refresh(cost_event)
        
        logger.info(
            "cost_event_logged",
            provider=provider,
            service=service,
            units=units,
            total_cost=cost_calc["total_cost"],
            task_id=task_id,
            is_priced=cost_calc["is_priced"]
        )
        
        return cost_event
    
    def get_task_cost_events(
        self,
        db: Session,
        task_id: str
    ) -> list[CostEvent]:
        """
        Get all cost events for a task
        
        Args:
            db: Database session
            task_id: Task ID
        
        Returns:
            List of CostEvent objects
        """
        return db.query(CostEvent).filter(
            CostEvent.task_id == task_id
        ).order_by(CostEvent.timestamp.asc()).all()
    
    def get_project_cost_events(
        self,
        db: Session,
        project_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[CostEvent]:
        """
        Get all cost events for a project
        
        Args:
            db: Database session
            project_id: Project ID
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            List of CostEvent objects
        """
        query = db.query(CostEvent).filter(CostEvent.project_id == project_id)
        
        if start_date:
            query = query.filter(CostEvent.timestamp >= start_date)
        if end_date:
            query = query.filter(CostEvent.timestamp <= end_date)
        
        return query.order_by(CostEvent.timestamp.asc()).all()

