"""Runtime Cost Tracker - Live cost tracking during task execution"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from src.database.models import TaskCostEstimate, CostEvent
from src.cost.cost_event_logger import CostEventLogger
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RuntimeCostTracker:
    """Tracks costs in real-time during task execution"""
    
    def __init__(self):
        """Initialize runtime cost tracker"""
        self.cost_logger = CostEventLogger()
    
    def get_task_cost_status(
        self,
        db: Session,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Get current cost status for a running task
        
        Args:
            db: Database session
            task_id: Task ID
        
        Returns:
            Dictionary with estimated, actual, breakdown, and projected costs
        """
        # Get estimate
        estimate = db.query(TaskCostEstimate).filter(
            TaskCostEstimate.task_id == task_id
        ).first()
        
        # Get actual cost events so far
        cost_events = db.query(CostEvent).filter(
            CostEvent.task_id == task_id
        ).all()
        
        # Aggregate actual costs
        actual_total = sum(event.total_cost for event in cost_events if event.is_priced)
        actual_breakdown = self._aggregate_breakdown(cost_events)
        
        # Projected total (simple: actual + remaining estimate)
        estimated_total = estimate.estimated_total_cost if estimate else 0.0
        remaining_estimate = max(0.0, estimated_total - actual_total)
        projected_total = actual_total + remaining_estimate
        
        return {
            "task_id": task_id,
            "estimated_total_cost": estimated_total,
            "actual_cost_so_far": actual_total,
            "projected_total_cost": projected_total,
            "remaining_estimated": remaining_estimate,
            "breakdown": {
                "estimated": estimate.breakdown if estimate else [],
                "actual": actual_breakdown
            },
            "cost_events_count": len(cost_events),
            "last_updated": max([e.timestamp for e in cost_events]).isoformat() if cost_events else None
        }
    
    def _aggregate_breakdown(
        self,
        cost_events: list[CostEvent]
    ) -> list[Dict[str, Any]]:
        """Aggregate cost events by provider/service"""
        breakdown_map = {}
        
        for event in cost_events:
            if not event.is_priced:
                continue
            
            key = f"{event.provider}:{event.service}"
            if key not in breakdown_map:
                breakdown_map[key] = {
                    "provider": event.provider,
                    "service": event.service,
                    "actual_cost": 0.0,
                    "events_count": 0,
                    "total_units": 0.0
                }
            
            breakdown_map[key]["actual_cost"] += event.total_cost
            breakdown_map[key]["events_count"] += 1
            breakdown_map[key]["total_units"] += event.units
        
        return list(breakdown_map.values())
    
    def start_task_tracking(
        self,
        db: Session,
        task_id: str,
        estimate: Dict[str, Any]
    ) -> TaskCostEstimate:
        """
        Start tracking costs for a task (store estimate)
        
        Args:
            db: Database session
            task_id: Task ID
            estimate: Cost estimate dictionary from CostEstimator
        
        Returns:
            Created TaskCostEstimate
        """
        # Check if estimate already exists
        existing = db.query(TaskCostEstimate).filter(
            TaskCostEstimate.task_id == task_id
        ).first()
        
        if existing:
            # Update existing estimate
            existing.estimated_total_cost = estimate["estimated_total_cost"]
            existing.confidence_score = estimate.get("confidence_score")
            existing.breakdown = estimate["breakdown"]
            existing.cost_optimizations = estimate.get("cost_optimizations", [])
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new estimate
        task_estimate = TaskCostEstimate(
            task_id=task_id,
            estimated_total_cost=estimate["estimated_total_cost"],
            confidence_score=estimate.get("confidence_score"),
            breakdown=estimate["breakdown"],
            cost_optimizations=estimate.get("cost_optimizations", [])
        )
        
        db.add(task_estimate)
        db.commit()
        db.refresh(task_estimate)
        
        logger.info(
            "task_cost_tracking_started",
            task_id=task_id,
            estimated_cost=estimate["estimated_total_cost"]
        )
        
        return task_estimate
    
    def finalize_task_costs(
        self,
        db: Session,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Finalize and aggregate costs after task completion
        
        Args:
            db: Database session
            task_id: Task ID
        
        Returns:
            Dictionary with final cost report
        """
        from src.database.models import TaskCostActual
        
        # Get all cost events
        cost_events = self.cost_logger.get_task_cost_events(db, task_id)
        
        # Aggregate actual costs
        actual_total = sum(event.total_cost for event in cost_events if event.is_priced)
        actual_breakdown = self._aggregate_breakdown(cost_events)
        
        # Get estimate for variance analysis
        estimate = db.query(TaskCostEstimate).filter(
            TaskCostEstimate.task_id == task_id
        ).first()
        
        estimated_cost = estimate.estimated_total_cost if estimate else None
        variance = actual_total - estimated_cost if estimated_cost else None
        variance_percentage = (variance / estimated_cost * 100) if estimated_cost and estimated_cost > 0 else None
        
        # Analyze variance by provider
        variance_breakdown = []
        if estimate and estimate.breakdown:
            for est_item in estimate.breakdown:
                provider = est_item.get("provider")
                service = est_item.get("service")
                est_cost = est_item.get("estimated_cost", 0.0)
                
                # Find actual cost for this provider/service
                actual_item = next(
                    (a for a in actual_breakdown if a.get("provider") == provider and a.get("service") == service),
                    None
                )
                actual_cost = actual_item.get("actual_cost", 0.0) if actual_item else 0.0
                
                item_variance = actual_cost - est_cost
                if abs(item_variance) > 0.01:  # Only report significant variances
                    variance_breakdown.append({
                        "provider": provider,
                        "service": service,
                        "variance": item_variance,
                        "estimated": est_cost,
                        "actual": actual_cost,
                        "reason": "Usage exceeded estimate" if item_variance > 0 else "Usage below estimate"
                    })
        
        # Create or update TaskCostActual
        existing_actual = db.query(TaskCostActual).filter(
            TaskCostActual.task_id == task_id
        ).first()
        
        if existing_actual:
            existing_actual.actual_total_cost = actual_total
            existing_actual.breakdown = actual_breakdown
            existing_actual.estimated_cost = estimated_cost
            existing_actual.variance = variance
            existing_actual.variance_percentage = variance_percentage
            existing_actual.variance_breakdown = variance_breakdown
            db.commit()
            db.refresh(existing_actual)
            cost_actual = existing_actual
        else:
            cost_actual = TaskCostActual(
                task_id=task_id,
                actual_total_cost=actual_total,
                breakdown=actual_breakdown,
                estimated_cost=estimated_cost,
                variance=variance,
                variance_percentage=variance_percentage,
                variance_breakdown=variance_breakdown
            )
            db.add(cost_actual)
            db.commit()
            db.refresh(cost_actual)
        
        logger.info(
            "task_costs_finalized",
            task_id=task_id,
            actual_cost=actual_total,
            estimated_cost=estimated_cost,
            variance=variance
        )
        
        return {
            "task_id": task_id,
            "actual_total_cost": actual_total,
            "estimated_cost": estimated_cost,
            "variance": variance,
            "variance_percentage": variance_percentage,
            "breakdown": actual_breakdown,
            "variance_breakdown": variance_breakdown,
            "cost_events_count": len(cost_events)
        }

