"""Seed initial pricing rules for common APIs"""

from datetime import datetime
from sqlalchemy.orm import Session
from src.database.database import SessionLocal
from src.cost.pricing_registry import PricingRegistry
from src.utils.logging import get_logger

logger = get_logger(__name__)


def seed_default_pricing_rules(db: Session):
    """Seed default pricing rules for OpenAI and Twilio"""
    registry = PricingRegistry()
    now = datetime.utcnow()
    
    # OpenAI GPT-4o pricing (as of 2024)
    registry.add_pricing_rule(
        db=db,
        provider="openai",
        service="chat",
        service_type="LLM",
        pricing_model="PER_TOKEN",
        unit_costs={
            "input_token": 0.0000025,  # $2.50 per 1M input tokens
            "output_token": 0.00001    # $10.00 per 1M output tokens
        },
        effective_date=now,
        documentation_url="https://openai.com/api/pricing/",
        notes="GPT-4o pricing as of 2024"
    )
    
    # OpenAI GPT-4o-mini pricing (cheaper alternative)
    registry.add_pricing_rule(
        db=db,
        provider="openai",
        service="chat-mini",
        service_type="LLM",
        pricing_model="PER_TOKEN",
        unit_costs={
            "input_token": 0.00000015,  # $0.15 per 1M input tokens
            "output_token": 0.0000006   # $0.60 per 1M output tokens
        },
        effective_date=now,
        documentation_url="https://openai.com/api/pricing/",
        notes="GPT-4o-mini pricing (cheaper alternative)"
    )
    
    # Twilio SMS pricing (US)
    registry.add_pricing_rule(
        db=db,
        provider="twilio",
        service="sms",
        service_type="messaging",
        pricing_model="PER_MESSAGE",
        unit_costs={
            "per_message": 0.0075,  # $0.0075 per SMS (US)
            "per_segment": 0.0075   # SMS segments (160 chars each)
        },
        effective_date=now,
        documentation_url="https://www.twilio.com/pricing",
        notes="Twilio SMS pricing for US numbers"
    )
    
    # Twilio WhatsApp pricing
    registry.add_pricing_rule(
        db=db,
        provider="twilio",
        service="whatsapp",
        service_type="messaging",
        pricing_model="PER_MESSAGE",
        unit_costs={
            "per_message": 0.005,  # $0.005 per WhatsApp message
            "per_segment": 0.005
        },
        effective_date=now,
        documentation_url="https://www.twilio.com/pricing",
        notes="Twilio WhatsApp pricing"
    )
    
    # Twilio MMS pricing
    registry.add_pricing_rule(
        db=db,
        provider="twilio",
        service="mms",
        service_type="messaging",
        pricing_model="PER_MESSAGE",
        unit_costs={
            "per_message": 0.02,  # $0.02 per MMS
        },
        effective_date=now,
        documentation_url="https://www.twilio.com/pricing",
        notes="Twilio MMS pricing"
    )
    
    # Twilio Voice calls (per minute)
    registry.add_pricing_rule(
        db=db,
        provider="twilio",
        service="voice",
        service_type="telephony",
        pricing_model="PER_MINUTE",
        unit_costs={
            "per_minute": 0.013,  # $0.013 per minute for US calls
        },
        effective_date=now,
        documentation_url="https://www.twilio.com/pricing",
        notes="Twilio Voice pricing for US calls"
    )
    
    print("✅ Default pricing rules seeded successfully")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_default_pricing_rules(db)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding pricing rules: {e}")
    finally:
        db.close()

