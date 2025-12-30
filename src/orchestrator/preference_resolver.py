"""Preference Resolver - Matches user preferences to task requests"""

from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
import json

from src.database.models import PreferenceEntry, PreferenceCategory
from src.utils.logging import get_logger
from src.utils.config import get_settings
from src.utils.openai_client import ensure_chat_model, create_openai_client, retry_openai_call, get_openai_error_message
from src.utils.errors import OpenAIError

logger = get_logger(__name__)
settings = get_settings()


class PreferenceResolver:
    """Resolves preferences for task execution"""
    
    def __init__(self):
        """Initialize preference resolver"""
        self.client = create_openai_client(timeout=20.0, max_retries=3)
        self.model = ensure_chat_model(settings.OPENAI_MODEL)
    
    def resolve_preferences(
        self,
        db: Session,
        task_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resolve preferences for a task request
        
        Args:
            db: Database session
            task_request: The task description/request
            context: Optional context (location, time, etc.)
        
        Returns:
            Dictionary with preference context:
            {
                "chosen_default": {...} or None,
                "alternatives": [...],
                "avoid_list": [...],
                "required_confirmations": [...],
                "constraints_applied": {...},
                "intent": "..."
            }
        """
        # Step 1: Classify intent
        intent = self._classify_intent(task_request, context)
        
        # Step 2: Match preferences
        matching_prefs = self._match_preferences(db, intent, context)
        
        # Step 3: Rank preferences
        ranked = self._rank_preferences(matching_prefs, context)
        
        # Step 4: Build result
        chosen_default = ranked.get("primary")[0] if ranked.get("primary") else None
        alternatives = ranked.get("secondary", [])[:2]  # Top 2 alternatives
        avoid_list = ranked.get("avoid", [])
        
        # Check if confirmation needed
        required_confirmations = []
        if chosen_default:
            if intent in ["doctor_appointment", "medical", "high_cost_booking", "travel_booking"]:
                required_confirmations.append({
                    "reason": f"High-impact task ({intent})",
                    "preference": chosen_default["name"],
                    "action": "confirm_before_execution"
                })
        
        return {
            "chosen_default": self._format_preference(chosen_default) if chosen_default else None,
            "alternatives": [self._format_preference(a) for a in alternatives],
            "avoid_list": [self._format_preference(a) for a in avoid_list],
            "required_confirmations": required_confirmations,
            "constraints_applied": chosen_default.get("constraints", {}) if chosen_default else {},
            "intent": intent
        }
    
    def _classify_intent(
        self,
        task_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Classify task intent using AI
        
        Returns:
            Intent string: grocery_order, hotel_research, doctor_appointment, etc.
        """
        try:
            prompt = f"""Classify the intent of this task request:

Task: {task_request}
Context: {json.dumps(context or {})}

Classify into one of these intents:
- grocery_order: Ordering groceries or food delivery
- restaurant_reservation: Booking a restaurant
- hotel_research: Finding or booking hotels
- travel_booking: Booking flights, hotels, or travel
- doctor_appointment: Scheduling medical appointments
- provider_appointment: Scheduling with any service provider (dentist, trainer, etc.)
- product_purchase: Buying products online
- service_booking: Booking any service
- location_search: Finding locations or addresses
- tool_usage: Using a specific tool or app
- research: Researching information
- other: Anything else

Respond with JSON:
{{
    "intent": "<intent_name>",
    "confidence": <0.0-1.0>
}}"""
            
            @retry_openai_call(max_retries=3, initial_delay=0.5, max_delay=10.0)
            def _call():
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert at classifying task intents. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"},
                    timeout=10
                )
            
            response = _call()
            
            result = json.loads(response.choices[0].message.content)
            return result.get("intent", "other")
        except Exception as e:
            logger.error("intent_classification_failed", error=str(e))
            return "other"
    
    def _match_preferences(
        self,
        db: Session,
        intent: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[PreferenceEntry]:
        """
        Find matching preferences for an intent
        
        Args:
            db: Database session
            intent: Task intent
            context: Optional context
        
        Returns:
            List of matching PreferenceEntry objects
        """
        # Map intent to category
        intent_to_category = {
            "grocery_order": "groceries",
            "restaurant_reservation": "restaurants",
            "hotel_research": "travel",
            "travel_booking": "travel",
            "doctor_appointment": "healthcare",
            "provider_appointment": "healthcare",
            "product_purchase": "shopping",
            "service_booking": "services",
            "location_search": "locations",
            "tool_usage": "tools",
            "research": "research"
        }
        
        category = intent_to_category.get(intent, "other")
        
        # Query preferences
        query = db.query(PreferenceEntry).filter(
            PreferenceEntry.category == category
        )
        
        # Filter by user if context has user_id
        if context and context.get("user_id"):
            query = query.filter(
                or_(
                    PreferenceEntry.owner_user_id == context["user_id"],
                    PreferenceEntry.owner_user_id.is_(None)  # Global defaults
                )
            )
        
        # Exclude AVOID entries unless explicitly requested
        if not context or not context.get("include_avoid"):
            query = query.filter(PreferenceEntry.priority != "AVOID")
        
        preferences = query.all()
        
        # Filter by constraints if context provided
        if context:
            filtered = []
            for pref in preferences:
                if self._matches_constraints(pref, context):
                    filtered.append(pref)
            return filtered
        
        return preferences
    
    def _matches_constraints(
        self,
        preference: PreferenceEntry,
        context: Dict[str, Any]
    ) -> bool:
        """Check if preference matches context constraints"""
        if not preference.constraints:
            return True
        
        constraints = preference.constraints
        
        # Check location constraints
        if constraints.get("only_for") == "business_travel" and context.get("trip_type") != "business":
            return False
        
        # Check price constraints
        if context.get("max_price") and constraints.get("min_price"):
            if context["max_price"] < constraints["min_price"]:
                return False
        
        # Add more constraint checks as needed
        return True
    
    def _rank_preferences(
        self,
        preferences: List[PreferenceEntry],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Rank preferences by priority and usage
        
        Returns:
            Dictionary with "primary", "secondary", "avoid" lists
        """
        primary = []
        secondary = []
        avoid = []
        
        for pref in preferences:
            pref_dict = {
                "id": pref.id,
                "type": pref.type,
                "category": pref.category,
                "name": pref.name,
                "priority": pref.priority,
                "tags": pref.tags or [],
                "url": pref.url,
                "phone": pref.phone,
                "address": pref.address,
                "notes": pref.notes,
                "constraints": pref.constraints or {},
                "last_used_at": pref.last_used_at.isoformat() if pref.last_used_at else None,
                "related_contact_id": pref.related_contact_id
            }
            
            if pref.priority == "PRIMARY":
                primary.append(pref_dict)
            elif pref.priority == "SECONDARY":
                secondary.append(pref_dict)
            elif pref.priority == "AVOID":
                avoid.append(pref_dict)
        
        # Sort by last_used_at (most recent first) and "default" tag
        def sort_key(p):
            score = 0
            if "default" in p.get("tags", []):
                score += 1000
            if p.get("last_used_at"):
                # More recent = higher score
                try:
                    last_used = datetime.fromisoformat(p["last_used_at"].replace("Z", "+00:00"))
                    days_ago = (datetime.now(last_used.tzinfo) - last_used).days
                    score += max(0, 100 - days_ago)  # Decay over time
                except:
                    pass
            return score
        
        primary.sort(key=sort_key, reverse=True)
        secondary.sort(key=sort_key, reverse=True)
        
        return {
            "primary": primary,
            "secondary": secondary,
            "avoid": avoid
        }
    
    def _format_preference(self, pref_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Format preference for response"""
        return {
            "entry_id": pref_dict["id"],
            "type": pref_dict["type"],
            "category": pref_dict["category"],
            "name": pref_dict["name"],
            "priority": pref_dict["priority"],
            "tags": pref_dict.get("tags", []),
            "url": pref_dict.get("url"),
            "phone": pref_dict.get("phone"),
            "address": pref_dict.get("address"),
            "notes": pref_dict.get("notes"),
            "constraints": pref_dict.get("constraints", {}),
            "last_used_at": pref_dict.get("last_used_at"),
            "related_contact_id": pref_dict.get("related_contact_id")
        }
    
    def mark_preference_used(
        self,
        db: Session,
        entry_id: str
    ) -> None:
        """Mark a preference as used (update last_used_at)"""
        try:
            entry = db.query(PreferenceEntry).filter(PreferenceEntry.id == entry_id).first()
            if entry:
                entry.last_used_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error("mark_preference_used_failed", error=str(e), entry_id=entry_id)
            db.rollback()

