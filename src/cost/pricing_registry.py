"""Pricing Registry - Manages API pricing rules"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.database.models import PricingRule
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PricingRegistry:
    """Manages API pricing rules and resolves costs"""
    
    def __init__(self):
        """Initialize pricing registry"""
        pass
    
    def add_pricing_rule(
        self,
        db: Session,
        provider: str,
        service: str,
        service_type: str,
        pricing_model: str,
        unit_costs: Dict[str, float],
        effective_date: datetime,
        currency: str = "USD",
        expires_at: Optional[datetime] = None,
        documentation_url: Optional[str] = None,
        notes: Optional[str] = None,
        rate_limits: Optional[Dict[str, Any]] = None,
        free_tier: Optional[Dict[str, Any]] = None
    ) -> PricingRule:
        """
        Add a new pricing rule
        
        Args:
            db: Database session
            provider: API provider name (e.g., "openai", "twilio")
            service: Service name (e.g., "chat", "sms", "whatsapp")
            service_type: Type of service (e.g., "LLM", "messaging")
            pricing_model: Pricing model ("PER_TOKEN", "PER_REQUEST", "PER_MESSAGE", "PER_MINUTE", "PER_IMAGE")
            unit_costs: Dictionary of unit costs (e.g., {"input_token": 0.00001, "output_token": 0.00003})
            effective_date: When this pricing takes effect
            currency: Currency code (default: USD)
            expires_at: When this pricing expires (None = current)
            documentation_url: Link to pricing documentation
            notes: Additional notes
            rate_limits: Rate limit information
            free_tier: Free tier information
        
        Returns:
            Created PricingRule
        """
        # Expire any existing rules for this provider/service that overlap
        if expires_at is None:
            # If new rule has no expiration, expire all current rules
            existing = db.query(PricingRule).filter(
                PricingRule.provider == provider,
                PricingRule.service == service,
                PricingRule.expires_at.is_(None)
            ).all()
            for rule in existing:
                rule.expires_at = effective_date
        
        rule = PricingRule(
            provider=provider,
            service=service,
            service_type=service_type,
            pricing_model=pricing_model,
            unit_costs=unit_costs,
            currency=currency,
            effective_date=effective_date,
            expires_at=expires_at,
            documentation_url=documentation_url,
            notes=notes,
            rate_limits=rate_limits,
            free_tier=free_tier
        )
        
        db.add(rule)
        db.commit()
        db.refresh(rule)
        
        logger.info(
            "pricing_rule_added",
            provider=provider,
            service=service,
            effective_date=effective_date.isoformat()
        )
        
        return rule
    
    def get_pricing_rule(
        self,
        db: Session,
        provider: str,
        service: str,
        effective_date: Optional[datetime] = None
    ) -> Optional[PricingRule]:
        """
        Get the active pricing rule for a provider/service at a given date
        
        Args:
            db: Database session
            provider: API provider name
            service: Service name
            effective_date: Date to check (defaults to now)
        
        Returns:
            Active PricingRule or None
        """
        if effective_date is None:
            effective_date = datetime.utcnow()
        
        rule = db.query(PricingRule).filter(
            PricingRule.provider == provider,
            PricingRule.service == service,
            PricingRule.effective_date <= effective_date,
            or_(
                PricingRule.expires_at.is_(None),
                PricingRule.expires_at > effective_date
            )
        ).order_by(PricingRule.effective_date.desc()).first()
        
        return rule
    
    def update_pricing_rule(
        self,
        db: Session,
        rule_id: str,
        **updates
    ) -> Optional[PricingRule]:
        """
        Update a pricing rule
        
        Args:
            db: Database session
            rule_id: Rule ID to update
            **updates: Fields to update
        
        Returns:
            Updated PricingRule or None if not found
        """
        rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()
        if not rule:
            return None
        
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        db.commit()
        db.refresh(rule)
        
        logger.info("pricing_rule_updated", rule_id=rule_id)
        
        return rule
    
    def list_pricing_rules(
        self,
        db: Session,
        provider: Optional[str] = None,
        service: Optional[str] = None,
        service_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[PricingRule]:
        """
        List pricing rules with optional filters
        
        Args:
            db: Database session
            provider: Filter by provider
            service: Filter by service
            service_type: Filter by service type
            active_only: Only return currently active rules
        
        Returns:
            List of PricingRule objects
        """
        query = db.query(PricingRule)
        
        if provider:
            query = query.filter(PricingRule.provider == provider)
        if service:
            query = query.filter(PricingRule.service == service)
        if service_type:
            query = query.filter(PricingRule.service_type == service_type)
        
        if active_only:
            now = datetime.utcnow()
            query = query.filter(
                PricingRule.effective_date <= now,
                or_(
                    PricingRule.expires_at.is_(None),
                    PricingRule.expires_at > now
                )
            )
        
        return query.order_by(PricingRule.provider, PricingRule.service, PricingRule.effective_date.desc()).all()
    
    def calculate_cost(
        self,
        db: Session,
        provider: str,
        service: str,
        metric_type: str,
        units: float,
        effective_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate cost for a given usage
        
        Args:
            db: Database session
            provider: API provider
            service: Service name
            metric_type: Type of metric ("tokens", "requests", "messages", "minutes", "images")
            units: Number of units consumed
            effective_date: Date to use for pricing (defaults to now)
            metadata: Additional metadata (e.g., model name, input/output split)
        
        Returns:
            Dictionary with unit_cost, total_cost, and pricing_rule_id
        """
        rule = self.get_pricing_rule(db, provider, service, effective_date)
        
        if not rule:
            logger.warning(
                "pricing_rule_not_found",
                provider=provider,
                service=service,
                metric_type=metric_type
            )
            return {
                "unit_cost": None,
                "total_cost": 0.0,
                "pricing_rule_id": None,
                "is_priced": False
            }
        
        unit_costs = rule.unit_costs
        unit_cost = None
        total_cost = 0.0
        
        # Resolve unit cost based on pricing model
        if rule.pricing_model == "PER_TOKEN":
            # For tokens, we need input/output split from metadata
            if metadata and "input_tokens" in metadata and "output_tokens" in metadata:
                input_cost = unit_costs.get("input_token", 0.0) * metadata["input_tokens"]
                output_cost = unit_costs.get("output_token", 0.0) * metadata["output_tokens"]
                total_cost = input_cost + output_cost
                # Average unit cost
                unit_cost = total_cost / units if units > 0 else 0.0
            else:
                # Fallback: use average token cost
                avg_token_cost = (unit_costs.get("input_token", 0.0) + unit_costs.get("output_token", 0.0)) / 2
                unit_cost = avg_token_cost
                total_cost = unit_cost * units
        elif rule.pricing_model == "PER_MESSAGE":
            # For messages, may have segment-based pricing
            segments = metadata.get("segments", 1) if metadata else 1
            per_segment = unit_costs.get("per_segment", unit_costs.get("per_message", 0.0))
            unit_cost = per_segment
            total_cost = per_segment * segments
        elif rule.pricing_model in ["PER_REQUEST", "PER_MINUTE", "PER_IMAGE"]:
            # Simple per-unit pricing
            unit_cost = unit_costs.get(f"per_{metric_type.rstrip('s')}", unit_costs.get("per_unit", 0.0))
            total_cost = unit_cost * units
        else:
            # Unknown pricing model
            logger.warning(
                "unknown_pricing_model",
                provider=provider,
                service=service,
                pricing_model=rule.pricing_model
            )
            return {
                "unit_cost": None,
                "total_cost": 0.0,
                "pricing_rule_id": rule.id,
                "is_priced": False
            }
        
        return {
            "unit_cost": unit_cost,
            "total_cost": total_cost,
            "pricing_rule_id": rule.id,
            "is_priced": True
        }

