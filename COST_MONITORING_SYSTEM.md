# Cost Monitoring & Forecasting System

## Overview

The Cost Monitoring & Forecasting System provides comprehensive API cost tracking, estimation, and budgeting for the AI orchestration platform. It enables the Godfather to:

- See **estimated cost before running a task**
- Monitor **live burn** while tasks execute
- Review **actual cost after completion**
- Track costs **per API**, **per project**, **per agent**, and **overall**
- Maintain a pricing library for all APIs used

## Architecture

### Core Components

1. **PricingRegistry** (`src/cost/pricing_registry.py`)
   - Manages API pricing rules
   - Resolves costs based on usage
   - Supports versioned pricing (effective dates)

2. **CostEventLogger** (`src/cost/cost_event_logger.py`)
   - Single source of truth for cost events
   - Logs atomic billable events
   - Prevents duplicates via event_id

3. **CostEstimator** (`src/cost/cost_estimator.py`)
   - Pre-flight cost estimation
   - Estimates LLM, messaging, and other tool costs
   - Provides confidence scores and optimization suggestions

4. **RuntimeCostTracker** (`src/cost/runtime_cost_tracker.py`)
   - Live cost tracking during task execution
   - Aggregates cost events in real-time
   - Finalizes costs after task completion

5. **BudgetManager** (`src/cost/budget_manager.py`)
   - Budget configuration and tracking
   - Alert generation for budget thresholds
   - Forecast-based warnings

### Database Models

- `pricing_rules` - API pricing configuration
- `cost_events` - Atomic billable events
- `task_cost_estimates` - Pre-flight estimates
- `task_cost_actuals` - Post-task actual costs
- `budgets` - Budget configuration
- `cost_alerts` - Budget alerts

## Usage

### 1. Seed Initial Pricing Rules

```bash
python -m src.cost.seed_pricing
```

This seeds default pricing for:
- OpenAI GPT-4o and GPT-4o-mini
- Twilio SMS, WhatsApp, MMS, and Voice

### 2. Add Custom Pricing Rules

```python
from src.cost.pricing_registry import PricingRegistry
from datetime import datetime

registry = PricingRegistry()
registry.add_pricing_rule(
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
    documentation_url="https://openai.com/api/pricing/"
)
```

### 3. Cost Estimation (Automatic)

Cost estimation is automatically integrated into the task execution flow:

```python
# In task creation route
cost_estimate = cost_estimator.estimate_task_cost(
    db=db,
    task_plan={"task": task_description},
    tool_plan=planned_tool_calls,
    model_config={"model": "gpt-4o"}
)

# Estimate includes:
# - estimated_total_cost
# - confidence_score
# - breakdown by provider/service
# - cost_optimizations (suggestions)
```

### 4. Cost Tracking (Automatic)

Cost events are automatically logged when:
- LLM calls are made (via instrumentation)
- Twilio messages are sent (via tool wrappers)
- Other API calls occur

### 5. Budget Management

```python
from src.cost.budget_manager import BudgetManager

budget_manager = BudgetManager()

# Create a budget
budget = budget_manager.create_budget(
    db=db,
    scope="overall",  # or "provider", "project", "agent"
    period="monthly",  # or "daily", "weekly"
    limit=100.0,  # $100/month
    enforcement_mode="warn"  # or "require_confirmation", "hard_stop"
)

# Check budgets (generates alerts)
alerts = budget_manager.check_budgets(db)
```

## API Endpoints

### Cost Summary

```http
GET /api/cost/summary?range=week
```

Returns:
- Total cost for the period
- Breakdown by provider
- Breakdown by service

### Costs by Provider

```http
GET /api/cost/by-provider?range=month
```

### Costs by Project

```http
GET /api/cost/by-project?range=month
```

### Task Cost Status

```http
GET /api/cost/tasks/{task_id}/cost
```

Returns:
- Estimated cost
- Actual cost so far
- Projected total cost
- Breakdown

### Project Cost Summary

```http
GET /api/cost/projects/{project_id}/cost?range=month
```

### Budgets

```http
GET /api/cost/budgets?active_only=true
POST /api/cost/budgets/check  # Manually trigger budget check
```

### Alerts

```http
GET /api/cost/alerts?unresolved_only=true
```

## Instrumentation

### LLM Calls

Cost events are logged automatically when OpenAI API calls are made. The system tracks:
- Input tokens
- Output tokens
- Model used
- Task/project context

### Twilio Calls

Cost events are logged when:
- SMS messages are sent
- WhatsApp messages are sent
- MMS messages are sent
- Voice calls are made

## Cost Optimization

The system provides optimization suggestions:

1. **Model Selection**: Suggests cheaper models for low-stakes tasks
2. **Batching**: Recommends batching multiple messages
3. **Context Management**: Suggests reducing context size for expensive operations

## Budget Alerts

Alerts are generated when:
- Budget is exceeded (critical)
- Forecasted spend exceeds budget (warning)
- Approaching budget limit (80% threshold, warning)

Alert types:
- `budget_exceeded` - Current spend >= limit
- `forecast_exceeded` - Projected spend > limit
- `budget_warning` - Approaching limit (80%+)
- `task_estimate_high` - Task estimate would exceed budget

## Future Enhancements

- [ ] Cost mode settings (Economy/Balanced/Premium)
- [ ] Automatic model selection based on task complexity
- [ ] Token budget caps per task
- [ ] Cost forecasting with ML models
- [ ] Cost allocation by contact/relationship
- [ ] Historical cost trend analysis
- [ ] Cost anomaly detection

## Notes

- Cost events are logged even if tasks fail
- Missing pricing rules result in `is_priced=False` events (can be backfilled later)
- All costs are stored in USD (currency conversion can be added)
- Pricing rules support versioning via effective_date/expires_at

