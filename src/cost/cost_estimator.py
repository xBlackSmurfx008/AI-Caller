"""Cost Estimator - Pre-flight cost estimation for tasks"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from src.cost.pricing_registry import PricingRegistry
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CostEstimator:
    """Estimates costs before task execution"""
    
    def __init__(self):
        """Initialize cost estimator"""
        self.pricing_registry = PricingRegistry()
    
    def estimate_task_cost(
        self,
        db: Session,
        task_plan: Dict[str, Any],
        tool_plan: Optional[List[Dict[str, Any]]] = None,
        context_size: Optional[int] = None,
        model_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Estimate cost for a task before execution
        
        Args:
            db: Database session
            task_plan: Task plan/description
            tool_plan: Planned tool calls
            context_size: Expected context size (tokens)
            model_config: Model configuration (model name, etc.)
        
        Returns:
            Dictionary with estimate breakdown, total, confidence, and optimizations
        """
        breakdown = []
        total_estimate = 0.0
        confidence_scores = []
        optimizations = []
        
        # Estimate LLM costs
        llm_estimate = self._estimate_llm_cost(
            db, task_plan, tool_plan, context_size, model_config
        )
        if llm_estimate:
            breakdown.append(llm_estimate)
            total_estimate += llm_estimate["estimated_cost"]
            confidence_scores.append(llm_estimate.get("confidence", 0.5))
        
        # Estimate messaging costs (Twilio)
        if tool_plan:
            messaging_estimate = self._estimate_messaging_cost(db, tool_plan)
            if messaging_estimate:
                breakdown.append(messaging_estimate)
                total_estimate += messaging_estimate["estimated_cost"]
                confidence_scores.append(messaging_estimate.get("confidence", 0.7))
        
        # Estimate other tool costs
        if tool_plan:
            other_estimates = self._estimate_other_tool_costs(db, tool_plan)
            breakdown.extend(other_estimates)
            for est in other_estimates:
                total_estimate += est["estimated_cost"]
                confidence_scores.append(est.get("confidence", 0.5))
        
        # Calculate overall confidence (average of individual confidences)
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        # Generate optimization suggestions
        optimizations = self._generate_optimizations(db, breakdown, model_config)
        
        return {
            "estimated_total_cost": total_estimate,
            "confidence_score": overall_confidence,
            "breakdown": breakdown,
            "cost_optimizations": optimizations
        }
    
    def _estimate_llm_cost(
        self,
        db: Session,
        task_plan: Dict[str, Any],
        tool_plan: Optional[List[Dict[str, Any]]],
        context_size: Optional[int],
        model_config: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Estimate LLM token costs"""
        model = model_config.get("model", "gpt-4o") if model_config else "gpt-4o"
        
        # Get pricing rule
        rule = self.pricing_registry.get_pricing_rule(db, "openai", "chat")
        if not rule:
            logger.warning("no_pricing_rule_for_llm", model=model)
            return None
        
        # Estimate tokens
        # Heuristic: task description length * 1.5 for input, response length estimate for output
        task_text = str(task_plan.get("task", task_plan.get("description", "")))
        estimated_input_tokens = len(task_text.split()) * 1.3  # ~1.3 tokens per word
        
        # Add context if provided
        if context_size:
            estimated_input_tokens += context_size
        else:
            # Default context estimate
            estimated_input_tokens += 1000
        
        # Estimate output tokens (heuristic: 20% of input for simple tasks, more for complex)
        tool_count = len(tool_plan) if tool_plan else 0
        if tool_count > 0:
            # Tool calls generate more output
            estimated_output_tokens = estimated_input_tokens * 0.3 + (tool_count * 200)
        else:
            estimated_output_tokens = estimated_input_tokens * 0.2
        
        # Calculate cost
        unit_costs = rule.unit_costs
        input_cost = unit_costs.get("input_token", 0.0) * estimated_input_tokens
        output_cost = unit_costs.get("output_token", 0.0) * estimated_output_tokens
        total_cost = input_cost + output_cost
        
        # Confidence: higher if we have context_size, lower if estimating
        confidence = 0.7 if context_size else 0.5
        
        return {
            "provider": "openai",
            "service": "chat",
            "metric_type": "tokens",
            "estimated_units": estimated_input_tokens + estimated_output_tokens,
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_cost": total_cost,
            "confidence": confidence,
            "model": model,
            "metadata": {
                "model": model,
                "tool_calls_planned": tool_count
            }
        }
    
    def _estimate_messaging_cost(
        self,
        db: Session,
        tool_plan: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Estimate Twilio messaging costs"""
        messaging_tools = [t for t in tool_plan if t.get("name") in ["send_sms", "send_message"]]
        if not messaging_tools:
            return None
        
        # Get pricing rule
        rule = self.pricing_registry.get_pricing_rule(db, "twilio", "sms")
        if not rule:
            logger.warning("no_pricing_rule_for_twilio_sms")
            return None
        
        # Estimate: 1 message per tool call, ~1 segment per message (160 chars)
        message_count = len(messaging_tools)
        segments = message_count  # Simplified: assume 1 segment per message
        
        unit_costs = rule.unit_costs
        per_segment = unit_costs.get("per_segment", unit_costs.get("per_message", 0.0))
        total_cost = per_segment * segments
        
        return {
            "provider": "twilio",
            "service": "sms",
            "metric_type": "messages",
            "estimated_units": message_count,
            "estimated_segments": segments,
            "estimated_cost": total_cost,
            "confidence": 0.8,  # High confidence for message count
            "metadata": {
                "message_count": message_count
            }
        }
    
    def _estimate_other_tool_costs(
        self,
        db: Session,
        tool_plan: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Estimate costs for other tools (web search, etc.)"""
        estimates = []
        
        # Check for web search tools
        web_search_tools = [t for t in tool_plan if t.get("name") == "web_search"]
        if web_search_tools:
            # If there's a paid search API, estimate here
            # For now, assume free or minimal cost
            pass
        
        return estimates
    
    def _generate_optimizations(
        self,
        db: Session,
        breakdown: List[Dict[str, Any]],
        model_config: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate cost optimization suggestions"""
        optimizations = []
        
        # Check for expensive LLM usage
        llm_breakdown = next((b for b in breakdown if b.get("provider") == "openai"), None)
        if llm_breakdown:
            estimated_cost = llm_breakdown.get("estimated_cost", 0.0)
            if estimated_cost > 0.50:  # If estimated cost > $0.50
                # Suggest cheaper model
                optimizations.append({
                    "suggestion": "Consider using gpt-4o-mini for lower cost (estimated savings: $0.10-0.30)",
                    "potential_savings": estimated_cost * 0.3,
                    "type": "model_selection"
                })
        
        # Check for multiple messaging calls
        messaging_breakdown = next((b for b in breakdown if b.get("provider") == "twilio"), None)
        if messaging_breakdown:
            message_count = messaging_breakdown.get("estimated_units", 0)
            if message_count > 5:
                optimizations.append({
                    "suggestion": f"Batching {message_count} messages may reduce costs",
                    "potential_savings": 0.0,  # Minimal for SMS
                    "type": "batching"
                })
        
        return optimizations

