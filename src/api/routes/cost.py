"""Cost monitoring and reporting API routes"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from src.database.database import get_db
from src.database.models import CostEvent, TaskCostEstimate, TaskCostActual, Budget, CostAlert
from src.cost.runtime_cost_tracker import RuntimeCostTracker
from src.cost.budget_manager import BudgetManager
from src.cost.pricing_registry import PricingRegistry
from src.utils.logging import get_logger
from src.utils.rate_limit import limiter
from fastapi import Request

router = APIRouter()
logger = get_logger(__name__)
runtime_cost_tracker = RuntimeCostTracker()
budget_manager = BudgetManager()
pricing_registry = PricingRegistry()


class CostSummaryResponse(BaseModel):
    """Cost summary response"""
    total_cost: float
    period: str
    start_date: str
    end_date: str
    breakdown_by_provider: List[Dict[str, Any]]
    breakdown_by_service: List[Dict[str, Any]]


class TaskCostResponse(BaseModel):
    """Task cost response"""
    task_id: str
    estimated_total_cost: float
    actual_cost_so_far: float
    projected_total_cost: float
    breakdown: Dict[str, Any]
    cost_events_count: int


class BudgetCreateRequest(BaseModel):
    scope: str  # "overall", "provider", "project", "agent"
    scope_id: Optional[str] = None
    period: str  # "daily", "weekly", "monthly"
    limit: float
    currency: str = "USD"
    enforcement_mode: str = "warn"  # "warn", "require_confirmation", "hard_stop"


@router.post("/budgets", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_budget(
    request: Request,
    payload: BudgetCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a budget policy."""
    # Basic validation
    if payload.scope not in {"overall", "provider", "project", "agent"}:
        raise HTTPException(status_code=400, detail="Invalid scope")
    if payload.period not in {"daily", "weekly", "monthly"}:
        raise HTTPException(status_code=400, detail="Invalid period")
    if payload.enforcement_mode not in {"warn", "require_confirmation", "hard_stop"}:
        raise HTTPException(status_code=400, detail="Invalid enforcement_mode")
    if payload.limit <= 0:
        raise HTTPException(status_code=400, detail="Budget limit must be > 0")
    if payload.scope != "overall" and not (payload.scope_id or "").strip():
        raise HTTPException(status_code=400, detail="scope_id required for non-overall budgets")

    budget = budget_manager.create_budget(
        db,
        scope=payload.scope,
        scope_id=(payload.scope_id or None),
        period=payload.period,
        limit=float(payload.limit),
        currency=payload.currency,
        enforcement_mode=payload.enforcement_mode,
    )
    return {"success": True, "budget_id": budget.id}


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_budget(
    request: Request,
    budget_id: str,
    db: Session = Depends(get_db),
):
    """Delete a budget policy."""
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(budget)
    db.commit()
    return


@router.get("/summary", response_model=CostSummaryResponse)
@limiter.limit("100/minute")
async def get_cost_summary(
    request: Request,
    range: str = Query("week", description="Time range: day, week, month"),
    limit: int = Query(100, description="Maximum number of breakdown items to return"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """Get cost summary for a time range"""
    now = datetime.utcnow()
    if range == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif range == "week":
        days_since_monday = now.weekday()
        start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
    else:  # month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end_date = now.replace(year=now.year + 1, month=1, day=1)
        else:
            end_date = now.replace(month=now.month + 1, day=1)
    
    # Get cost events in range
    cost_events = db.query(CostEvent).filter(
        CostEvent.timestamp >= start_date,
        CostEvent.timestamp < end_date,
        CostEvent.is_priced == True
    ).all()
    
    total_cost = sum(event.total_cost for event in cost_events)
    
    # Breakdown by provider
    provider_breakdown = {}
    for event in cost_events:
        if event.provider not in provider_breakdown:
            provider_breakdown[event.provider] = {"cost": 0.0, "events": 0}
        provider_breakdown[event.provider]["cost"] += event.total_cost
        provider_breakdown[event.provider]["events"] += 1
    
    breakdown_by_provider = [
        {"provider": provider, "cost": data["cost"], "events": data["events"]}
        for provider, data in provider_breakdown.items()
    ]
    # Sort by cost descending and apply pagination
    breakdown_by_provider.sort(key=lambda x: x["cost"], reverse=True)
    breakdown_by_provider = breakdown_by_provider[offset:offset + limit]
    
    # Breakdown by service
    service_breakdown = {}
    for event in cost_events:
        key = f"{event.provider}:{event.service}"
        if key not in service_breakdown:
            service_breakdown[key] = {"provider": event.provider, "service": event.service, "cost": 0.0, "events": 0}
        service_breakdown[key]["cost"] += event.total_cost
        service_breakdown[key]["events"] += 1
    
    breakdown_by_service = list(service_breakdown.values())
    # Sort by cost descending and apply pagination
    breakdown_by_service.sort(key=lambda x: x["cost"], reverse=True)
    breakdown_by_service = breakdown_by_service[offset:offset + limit]
    
    return CostSummaryResponse(
        total_cost=total_cost,
        period=range,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        breakdown_by_provider=breakdown_by_provider,
        breakdown_by_service=breakdown_by_service
    )


@router.get("/by-provider")
@limiter.limit("100/minute")
async def get_costs_by_provider(
    request: Request,
    range: str = Query("month", description="Time range: day, week, month"),
    db: Session = Depends(get_db)
):
    """Get costs grouped by provider"""
    now = datetime.utcnow()
    if range == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif range == "week":
        days_since_monday = now.weekday()
        start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
    else:  # month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end_date = now.replace(year=now.year + 1, month=1, day=1)
        else:
            end_date = now.replace(month=now.month + 1, day=1)
    
    results = db.query(
        CostEvent.provider,
        func.sum(CostEvent.total_cost).label("total_cost"),
        func.count(CostEvent.id).label("event_count")
    ).filter(
        CostEvent.timestamp >= start_date,
        CostEvent.timestamp < end_date,
        CostEvent.is_priced == True
    ).group_by(CostEvent.provider).all()
    
    return [
        {
            "provider": r.provider,
            "total_cost": float(r.total_cost),
            "event_count": r.event_count
        }
        for r in results
    ]


@router.get("/by-project")
@limiter.limit("100/minute")
async def get_costs_by_project(
    request: Request,
    range: str = Query("month", description="Time range: day, week, month"),
    db: Session = Depends(get_db)
):
    """Get costs grouped by project"""
    now = datetime.utcnow()
    if range == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif range == "week":
        days_since_monday = now.weekday()
        start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
    else:  # month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end_date = now.replace(year=now.year + 1, month=1, day=1)
        else:
            end_date = now.replace(month=now.month + 1, day=1)
    
    results = db.query(
        CostEvent.project_id,
        func.sum(CostEvent.total_cost).label("total_cost"),
        func.count(CostEvent.id).label("event_count")
    ).filter(
        CostEvent.timestamp >= start_date,
        CostEvent.timestamp < end_date,
        CostEvent.is_priced == True,
        CostEvent.project_id.isnot(None)
    ).group_by(CostEvent.project_id).all()
    
    return [
        {
            "project_id": r.project_id,
            "total_cost": float(r.total_cost),
            "event_count": r.event_count
        }
        for r in results
    ]


@router.get("/tasks/{task_id}/cost", response_model=TaskCostResponse)
@limiter.limit("100/minute")
async def get_task_cost(
    request: Request,
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get cost status for a task"""
    cost_status = runtime_cost_tracker.get_task_cost_status(db, task_id)
    
    if not cost_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or no cost data"
        )
    
    return TaskCostResponse(
        task_id=cost_status["task_id"],
        estimated_total_cost=cost_status["estimated_total_cost"],
        actual_cost_so_far=cost_status["actual_cost_so_far"],
        projected_total_cost=cost_status["projected_total_cost"],
        breakdown=cost_status["breakdown"],
        cost_events_count=cost_status["cost_events_count"]
    )


@router.get("/projects/{project_id}/cost")
@limiter.limit("100/minute")
async def get_project_cost(
    request: Request,
    project_id: str,
    range: Optional[str] = Query(None, description="Time range: day, week, month"),
    db: Session = Depends(get_db)
):
    """Get cost summary for a project"""
    cost_events = runtime_cost_tracker.cost_logger.get_project_cost_events(db, project_id)
    
    if range:
        now = datetime.utcnow()
        if range == "day":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif range == "week":
            days_since_monday = now.weekday()
            start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # month
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        cost_events = [e for e in cost_events if e.timestamp >= start_date]
    
    total_cost = sum(event.total_cost for event in cost_events if event.is_priced)
    
    # Breakdown by provider
    provider_breakdown = {}
    for event in cost_events:
        if event.is_priced:
            if event.provider not in provider_breakdown:
                provider_breakdown[event.provider] = 0.0
            provider_breakdown[event.provider] += event.total_cost
    
    return {
        "project_id": project_id,
        "total_cost": total_cost,
        "event_count": len(cost_events),
        "breakdown_by_provider": [
            {"provider": p, "cost": c} for p, c in provider_breakdown.items()
        ]
    }


@router.get("/budgets")
@limiter.limit("60/minute")
async def list_budgets(
    request: Request,
    active_only: bool = Query(True, description="Only return active budgets"),
    db: Session = Depends(get_db)
):
    """List all budgets"""
    query = db.query(Budget)
    if active_only:
        query = query.filter(Budget.is_active == True)
    
    budgets = query.all()
    
    # Get current spend for each budget
    result = []
    for budget in budgets:
        spend_info = budget_manager.get_current_spend(
            db,
            scope=budget.scope,
            scope_id=budget.scope_id,
            period=budget.period
        )
        
        result.append({
            "id": budget.id,
            "scope": budget.scope,
            "scope_id": budget.scope_id,
            "period": budget.period,
            "limit": budget.limit,
            "currency": budget.currency,
            "enforcement_mode": budget.enforcement_mode,
            "is_active": budget.is_active,
            "current_spend": spend_info["current_spend"],
            "forecasted_spend": spend_info["forecasted_spend"],
            "percentage_used": (spend_info["current_spend"] / budget.limit * 100) if budget.limit > 0 else 0.0
        })
    
    return result


@router.get("/alerts")
@limiter.limit("60/minute")
async def list_alerts(
    request: Request,
    unresolved_only: bool = Query(True, description="Only return unresolved alerts"),
    db: Session = Depends(get_db)
):
    """List cost alerts"""
    query = db.query(CostAlert)
    if unresolved_only:
        query = query.filter(CostAlert.is_resolved == False)
    
    alerts = query.order_by(CostAlert.created_at.desc()).limit(50).all()
    
    return [
        {
            "id": alert.id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "scope": alert.scope,
            "scope_id": alert.scope_id,
            "message": alert.message,
            "current_spend": alert.current_spend,
            "limit": alert.limit,
            "percentage_used": alert.percentage_used,
            "forecasted_spend": alert.forecasted_spend,
            "is_resolved": alert.is_resolved,
            "created_at": alert.created_at.isoformat()
        }
        for alert in alerts
    ]


@router.post("/budgets/check")
@limiter.limit("10/minute")
async def check_budgets(
    request: Request,
    db: Session = Depends(get_db)
):
    """Manually trigger budget check and alert generation"""
    alerts = budget_manager.check_budgets(db)
    
    return {
        "alerts_generated": len(alerts),
        "alerts": [
            {
                "id": alert.id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message
            }
            for alert in alerts
        ]
    }

