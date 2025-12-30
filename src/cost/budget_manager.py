"""Budget Manager - Budget tracking and alerts"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from src.database.models import Budget, CostAlert, CostEvent
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BudgetManager:
    """Manages budgets and generates alerts"""
    
    def create_budget(
        self,
        db: Session,
        scope: str,
        period: str,
        limit: float,
        scope_id: Optional[str] = None,
        currency: str = "USD",
        enforcement_mode: str = "warn"
    ) -> Budget:
        """
        Create a budget
        
        Args:
            db: Database session
            scope: "overall", "provider", "project", "agent"
            period: "daily", "weekly", "monthly"
            limit: Budget limit in USD
            scope_id: Provider name, project_id, agent_id, or None for overall
            currency: Currency code
            enforcement_mode: "warn", "require_confirmation", "hard_stop"
        
        Returns:
            Created Budget
        """
        budget = Budget(
            scope=scope,
            scope_id=scope_id,
            period=period,
            limit=limit,
            currency=currency,
            enforcement_mode=enforcement_mode
        )
        
        db.add(budget)
        db.commit()
        db.refresh(budget)
        
        logger.info(
            "budget_created",
            budget_id=budget.id,
            scope=scope,
            period=period,
            limit=limit
        )
        
        return budget
    
    def get_current_spend(
        self,
        db: Session,
        scope: str,
        scope_id: Optional[str] = None,
        period: str = "monthly"
    ) -> Dict[str, Any]:
        """
        Get current spend for a scope/period
        
        Args:
            db: Database session
            scope: "overall", "provider", "project", "agent"
            period: "daily", "weekly", "monthly"
            scope_id: Provider name, project_id, agent_id, or None
        
        Returns:
            Dictionary with current spend, period info, and forecast
        """
        # Calculate date range based on period
        now = datetime.utcnow()
        if period == "daily":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        elif period == "weekly":
            # Start of week (Monday)
            days_since_monday = now.weekday()
            start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=7)
        else:  # monthly
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end_date = now.replace(year=now.year + 1, month=1, day=1)
            else:
                end_date = now.replace(month=now.month + 1, day=1)
        
        # Build query
        query = db.query(func.sum(CostEvent.total_cost)).filter(
            CostEvent.timestamp >= start_date,
            CostEvent.timestamp < end_date,
            CostEvent.is_priced == True
        )
        
        # Apply scope filter
        if scope == "provider":
            query = query.filter(CostEvent.provider == scope_id)
        elif scope == "project":
            query = query.filter(CostEvent.project_id == scope_id)
        elif scope == "agent":
            query = query.filter(CostEvent.agent_id == scope_id)
        # "overall" doesn't need additional filter
        
        current_spend = query.scalar() or 0.0
        
        # Calculate forecast (simple: extrapolate based on time elapsed)
        elapsed = (now - start_date).total_seconds()
        total_period = (end_date - start_date).total_seconds()
        progress = elapsed / total_period if total_period > 0 else 0.0
        
        if progress > 0:
            forecasted_spend = current_spend / progress if progress > 0 else current_spend
        else:
            forecasted_spend = current_spend
        
        return {
            "scope": scope,
            "scope_id": scope_id,
            "period": period,
            "current_spend": current_spend,
            "forecasted_spend": forecasted_spend,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "progress_percentage": progress * 100
        }
    
    def check_budgets(
        self,
        db: Session
    ) -> List[CostAlert]:
        """
        Check all active budgets and generate alerts if needed
        
        Args:
            db: Database session
        
        Returns:
            List of created CostAlert objects
        """
        active_budgets = db.query(Budget).filter(Budget.is_active == True).all()
        alerts = []
        
        for budget in active_budgets:
            spend_info = self.get_current_spend(
                db,
                scope=budget.scope,
                scope_id=budget.scope_id,
                period=budget.period
            )
            
            current_spend = spend_info["current_spend"]
            forecasted_spend = spend_info["forecasted_spend"]
            percentage_used = (current_spend / budget.limit * 100) if budget.limit > 0 else 0.0
            
            # Check for alerts
            if current_spend >= budget.limit:
                # Budget exceeded
                alert = self._create_alert(
                    db,
                    budget_id=budget.id,
                    alert_type="budget_exceeded",
                    severity="critical",
                    scope=budget.scope,
                    scope_id=budget.scope_id,
                    period=budget.period,
                    current_spend=current_spend,
                    limit=budget.limit,
                    percentage_used=percentage_used,
                    forecasted_spend=forecasted_spend,
                    message=f"Budget exceeded: ${current_spend:.2f} / ${budget.limit:.2f} ({percentage_used:.1f}%)"
                )
                if alert:
                    alerts.append(alert)
            elif forecasted_spend > budget.limit:
                # Forecasted to exceed
                alert = self._create_alert(
                    db,
                    budget_id=budget.id,
                    alert_type="forecast_exceeded",
                    severity="warning",
                    scope=budget.scope,
                    scope_id=budget.scope_id,
                    period=budget.period,
                    current_spend=current_spend,
                    limit=budget.limit,
                    percentage_used=percentage_used,
                    forecasted_spend=forecasted_spend,
                    message=f"Forecasted to exceed budget: ${forecasted_spend:.2f} projected vs ${budget.limit:.2f} limit"
                )
                if alert:
                    alerts.append(alert)
            elif percentage_used >= 80:
                # Approaching limit
                alert = self._create_alert(
                    db,
                    budget_id=budget.id,
                    alert_type="budget_warning",
                    severity="warning",
                    scope=budget.scope,
                    scope_id=budget.scope_id,
                    period=budget.period,
                    current_spend=current_spend,
                    limit=budget.limit,
                    percentage_used=percentage_used,
                    forecasted_spend=forecasted_spend,
                    message=f"Approaching budget limit: {percentage_used:.1f}% used (${current_spend:.2f} / ${budget.limit:.2f})"
                )
                if alert:
                    alerts.append(alert)
        
        return alerts
    
    def _create_alert(
        self,
        db: Session,
        budget_id: Optional[str],
        alert_type: str,
        severity: str,
        scope: str,
        scope_id: Optional[str],
        period: str,
        current_spend: float,
        limit: float,
        percentage_used: float,
        forecasted_spend: Optional[float],
        message: str
    ) -> Optional[CostAlert]:
        """Create a cost alert"""
        # Check if similar alert already exists (not resolved)
        existing = db.query(CostAlert).filter(
            CostAlert.budget_id == budget_id,
            CostAlert.alert_type == alert_type,
            CostAlert.is_resolved == False
        ).first()
        
        if existing:
            # Update existing alert
            existing.current_spend = current_spend
            existing.percentage_used = percentage_used
            existing.forecasted_spend = forecasted_spend
            existing.message = message
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new alert
        alert = CostAlert(
            budget_id=budget_id,
            alert_type=alert_type,
            severity=severity,
            scope=scope,
            scope_id=scope_id,
            period=period,
            current_spend=current_spend,
            limit=limit,
            percentage_used=percentage_used,
            forecasted_spend=forecasted_spend,
            message=message
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        logger.warning(
            "cost_alert_created",
            alert_id=alert.id,
            alert_type=alert_type,
            severity=severity,
            message=message
        )
        
        return alert
    
    def check_task_estimate(
        self,
        db: Session,
        task_id: str,
        estimated_cost: float
    ) -> Optional[CostAlert]:
        """
        Check if task estimate exceeds any budget thresholds
        
        Args:
            db: Database session
            task_id: Task ID
            estimated_cost: Estimated cost
        
        Returns:
            CostAlert if threshold exceeded, None otherwise
        """
        # Check for overall budget with hard stop
        overall_budget = db.query(Budget).filter(
            Budget.scope == "overall",
            Budget.is_active == True,
            Budget.enforcement_mode == "hard_stop"
        ).first()
        
        if overall_budget:
            spend_info = self.get_current_spend(db, scope="overall", period=overall_budget.period)
            if spend_info["current_spend"] + estimated_cost > overall_budget.limit:
                return self._create_alert(
                    db,
                    budget_id=overall_budget.id,
                    alert_type="task_estimate_high",
                    severity="critical",
                    scope="overall",
                    scope_id=None,
                    period=overall_budget.period,
                    current_spend=spend_info["current_spend"],
                    limit=overall_budget.limit,
                    percentage_used=(spend_info["current_spend"] / overall_budget.limit * 100),
                    forecasted_spend=None,
                    message=f"Task estimate (${estimated_cost:.2f}) would exceed budget"
                )
        
        return None

