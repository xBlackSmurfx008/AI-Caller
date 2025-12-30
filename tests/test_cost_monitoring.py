"""Integration tests for cost monitoring system"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.database.database import SessionLocal, init_db
from src.database.models import (
    PricingRule, CostEvent, TaskCostEstimate, TaskCostActual, Budget, CostAlert
)
from src.cost.pricing_registry import PricingRegistry
from src.cost.cost_event_logger import CostEventLogger
from src.cost.cost_estimator import CostEstimator
from src.cost.runtime_cost_tracker import RuntimeCostTracker
from src.cost.budget_manager import BudgetManager


@pytest.fixture
def db():
    """Create a test database session"""
    init_db()  # Ensure tables exist
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def pricing_registry():
    """Create pricing registry instance"""
    return PricingRegistry()


@pytest.fixture
def cost_logger():
    """Create cost event logger instance"""
    return CostEventLogger()


@pytest.fixture
def cost_estimator():
    """Create cost estimator instance"""
    return CostEstimator()


@pytest.fixture
def runtime_tracker():
    """Create runtime cost tracker instance"""
    return RuntimeCostTracker()


@pytest.fixture
def budget_manager():
    """Create budget manager instance"""
    return BudgetManager()


@pytest.fixture
def sample_pricing_rule(db, pricing_registry):
    """Create a sample pricing rule for testing"""
    rule = pricing_registry.add_pricing_rule(
        db=db,
        provider="openai",
        service="chat",
        service_type="LLM",
        pricing_model="PER_TOKEN",
        unit_costs={
            "input_token": 0.0000025,
            "output_token": 0.00001
        },
        effective_date=datetime.utcnow(),
        currency="USD"
    )
    return rule


class TestPricingRegistry:
    """Tests for PricingRegistry"""
    
    def test_add_pricing_rule(self, db, pricing_registry):
        """Test adding a pricing rule"""
        rule = pricing_registry.add_pricing_rule(
            db=db,
            provider="test_provider",
            service="test_service",
            service_type="LLM",
            pricing_model="PER_TOKEN",
            unit_costs={"input_token": 0.001, "output_token": 0.002},
            effective_date=datetime.utcnow()
        )
        
        assert rule.id is not None
        assert rule.provider == "test_provider"
        assert rule.service == "test_service"
        assert rule.unit_costs["input_token"] == 0.001
    
    def test_get_pricing_rule(self, db, pricing_registry, sample_pricing_rule):
        """Test retrieving a pricing rule"""
        rule = pricing_registry.get_pricing_rule(
            db=db,
            provider="openai",
            service="chat"
        )
        
        assert rule is not None
        assert rule.provider == "openai"
        assert rule.service == "chat"
    
    def test_calculate_cost(self, db, pricing_registry, sample_pricing_rule):
        """Test cost calculation"""
        result = pricing_registry.calculate_cost(
            db=db,
            provider="openai",
            service="chat",
            metric_type="tokens",
            units=1000,
            metadata={"input_tokens": 600, "output_tokens": 400}
        )
        
        assert result["is_priced"] is True
        assert result["total_cost"] > 0
        assert result["pricing_rule_id"] is not None


class TestCostEventLogger:
    """Tests for CostEventLogger"""
    
    def test_log_cost_event(self, db, cost_logger, sample_pricing_rule):
        """Test logging a cost event"""
        event = cost_logger.log_cost_event(
            db=db,
            provider="openai",
            service="chat",
            metric_type="tokens",
            units=1000,
            task_id="test_task_123",
            metadata={"model": "gpt-4o"}
        )
        
        assert event.id is not None
        assert event.provider == "openai"
        assert event.service == "chat"
        assert event.units == 1000
        assert event.total_cost > 0
        assert event.is_priced is True
    
    def test_duplicate_event_id(self, db, cost_logger, sample_pricing_rule):
        """Test that duplicate event IDs are handled"""
        event_id = "test_event_123"
        
        event1 = cost_logger.log_cost_event(
            db=db,
            provider="openai",
            service="chat",
            metric_type="tokens",
            units=1000,
            event_id=event_id
        )
        
        # Try to log same event again
        event2 = cost_logger.log_cost_event(
            db=db,
            provider="openai",
            service="chat",
            metric_type="tokens",
            units=1000,
            event_id=event_id
        )
        
        # Should return the same event
        assert event1.id == event2.id


class TestCostEstimator:
    """Tests for CostEstimator"""
    
    def test_estimate_task_cost(self, db, cost_estimator, sample_pricing_rule):
        """Test cost estimation"""
        estimate = cost_estimator.estimate_task_cost(
            db=db,
            task_plan={"task": "Test task", "description": "Test description"},
            tool_plan=[{"name": "send_sms", "arguments": {}}],
            model_config={"model": "gpt-4o"}
        )
        
        assert estimate["estimated_total_cost"] >= 0
        assert "breakdown" in estimate
        assert "confidence_score" in estimate
        assert len(estimate["breakdown"]) > 0


class TestRuntimeCostTracker:
    """Tests for RuntimeCostTracker"""
    
    def test_start_task_tracking(self, db, runtime_tracker, cost_estimator, sample_pricing_rule):
        """Test starting cost tracking for a task"""
        estimate = cost_estimator.estimate_task_cost(
            db=db,
            task_plan={"task": "Test task"},
            model_config={"model": "gpt-4o"}
        )
        
        task_estimate = runtime_tracker.start_task_tracking(
            db=db,
            task_id="test_task_123",
            estimate=estimate
        )
        
        assert task_estimate.task_id == "test_task_123"
        assert task_estimate.estimated_total_cost == estimate["estimated_total_cost"]
    
    def test_get_task_cost_status(self, db, runtime_tracker, cost_logger, sample_pricing_rule):
        """Test getting cost status for a task"""
        task_id = "test_task_123"
        
        # Log some cost events
        cost_logger.log_cost_event(
            db=db,
            provider="openai",
            service="chat",
            metric_type="tokens",
            units=1000,
            task_id=task_id
        )
        
        status = runtime_tracker.get_task_cost_status(db, task_id)
        
        assert status["task_id"] == task_id
        assert status["actual_cost_so_far"] > 0
        assert "breakdown" in status


class TestBudgetManager:
    """Tests for BudgetManager"""
    
    def test_create_budget(self, db, budget_manager):
        """Test creating a budget"""
        budget = budget_manager.create_budget(
            db=db,
            scope="overall",
            period="monthly",
            limit=100.0,
            enforcement_mode="warn"
        )
        
        assert budget.id is not None
        assert budget.scope == "overall"
        assert budget.period == "monthly"
        assert budget.limit == 100.0
    
    def test_get_current_spend(self, db, budget_manager, cost_logger, sample_pricing_rule):
        """Test getting current spend"""
        # Log some cost events
        cost_logger.log_cost_event(
            db=db,
            provider="openai",
            service="chat",
            metric_type="tokens",
            units=1000
        )
        
        spend_info = budget_manager.get_current_spend(
            db=db,
            scope="overall",
            period="monthly"
        )
        
        assert spend_info["current_spend"] > 0
        assert spend_info["forecasted_spend"] >= spend_info["current_spend"]
    
    def test_check_budgets(self, db, budget_manager, cost_logger, sample_pricing_rule):
        """Test budget checking"""
        # Create a budget
        budget = budget_manager.create_budget(
            db=db,
            scope="overall",
            period="monthly",
            limit=0.01  # Very low limit to trigger alert
        )
        
        # Log a cost event that exceeds budget
        cost_logger.log_cost_event(
            db=db,
            provider="openai",
            service="chat",
            metric_type="tokens",
            units=10000  # Should cost more than $0.01
        )
        
        # Check budgets
        alerts = budget_manager.check_budgets(db)
        
        # Should generate at least one alert
        assert len(alerts) > 0
        assert any(alert.alert_type == "budget_exceeded" for alert in alerts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

