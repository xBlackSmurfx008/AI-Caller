"""Memory service for processing and storing contact interactions"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.database.models import Contact, Interaction, MemorySummary, ContactMemoryState, Commitment
from src.utils.config import get_settings
from src.utils.openai_client import ensure_chat_model, create_openai_client
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class MemoryService:
    """Service for managing per-contact memory and interaction summaries"""
    
    def __init__(self):
        """Initialize memory service"""
        self.client = create_openai_client(timeout=60.0, max_retries=3)
        self.model = ensure_chat_model(settings.OPENAI_MODEL)
    
    def store_interaction(
        self,
        db: Session,
        contact_id: str,
        channel: str,
        raw_content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Interaction:
        """
        Store raw interaction content with deduplication check
        
        Args:
            db: Database session
            contact_id: Contact ID
            channel: "email", "sms", or "call"
            raw_content: Full transcript/message content
            metadata: Optional metadata (subject, call_sid, etc.)
        
        Returns:
            Created or existing Interaction instance
        """
        metadata = metadata or {}
        
        # Check for duplicate interaction
        # For SMS/Email: check by message_sid or similar unique identifier
        # For calls: check by call_sid
        # Also check by content hash and timestamp (within 5 minutes)
        duplicate = None
        
        if channel in ["sms", "email"]:
            message_sid = metadata.get("message_sid")
            if message_sid:
                duplicate = db.query(Interaction).filter(
                    Interaction.contact_id == contact_id,
                    Interaction.channel == channel,
                    Interaction.meta_data['message_sid'].astext == str(message_sid)
                ).first()
        elif channel == "call":
            call_sid = metadata.get("call_sid")
            if call_sid:
                duplicate = db.query(Interaction).filter(
                    Interaction.contact_id == contact_id,
                    Interaction.channel == channel,
                    Interaction.meta_data['call_sid'].astext == str(call_sid)
                ).first()
        
        # If no duplicate found by ID, check by content and recent timestamp
        if not duplicate:
            from datetime import timedelta
            recent_time = datetime.utcnow() - timedelta(minutes=5)
            
            # Check for same content within last 5 minutes
            duplicate = db.query(Interaction).filter(
                Interaction.contact_id == contact_id,
                Interaction.channel == channel,
                Interaction.raw_content == raw_content,
                Interaction.created_at >= recent_time
            ).first()
        
        if duplicate:
            logger.info(
                "interaction_already_exists",
                interaction_id=duplicate.id,
                contact_id=contact_id,
                channel=channel
            )
            return duplicate
        
        # Create new interaction
        interaction = Interaction(
            contact_id=contact_id,
            channel=channel,
            raw_content=raw_content,
            metadata=metadata
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        
        logger.info(
            "interaction_stored",
            interaction_id=interaction.id,
            contact_id=contact_id,
            channel=channel
        )
        
        return interaction
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),  # Retry on any exception
        reraise=True
    )
    def generate_summary(
        self,
        db: Session,
        interaction_id: str,
        contact_name: Optional[str] = None
    ) -> MemorySummary:
        """
        Generate structured summary for an interaction using AI
        
        Args:
            db: Database session
            interaction_id: Interaction ID to summarize
            contact_name: Optional contact name for context
        
        Returns:
            Created MemorySummary instance
        """
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            raise ValueError(f"Interaction {interaction_id} not found")
        
        contact = db.query(Contact).filter(Contact.id == interaction.contact_id).first()
        contact_name = contact_name or (contact.name if contact else "Contact")
        
        # Get existing memory state for context
        memory_state = db.query(ContactMemoryState).filter(
            ContactMemoryState.contact_id == interaction.contact_id
        ).first()
        
        # Build context prompt
        context_parts = []
        if memory_state:
            if memory_state.active_goals:
                context_parts.append(f"Active Godfather goals: {', '.join(memory_state.active_goals)}")
            if memory_state.key_preferences:
                context_parts.append(f"Known preferences: {', '.join(memory_state.key_preferences)}")
            if memory_state.relationship_status:
                context_parts.append(f"Relationship status: {memory_state.relationship_status}")
        
        context_str = "\n".join(context_parts) if context_parts else "No prior context available."
        
        # Generate summary using OpenAI
        prompt = f"""Analyze this interaction with {contact_name} and create a structured summary.

Previous context:
{context_str}

Interaction details:
Channel: {interaction.channel}
Content:
{interaction.raw_content}

Please provide a JSON response with the following structure:
{{
    "summary": "A brief 2-3 sentence TL;DR summary of this interaction",
    "key_facts": ["fact1", "fact2", ...],
    "sentiment_score": <float between -1.0 (very negative) and 1.0 (very positive)>,
    "sentiment_explanation": "Brief explanation of the sentiment",
    "godfather_goals": ["goal1", "goal2", ...] or [],
    "commitments": [{{"description": "...", "deadline": "..." or null}}, ...] or [],
    "next_actions": ["action1", "action2", ...] or [],
    "preferences": ["preference1", "preference2", ...] or [],
    "value_map": {{
        "offers": ["skill/resource/influence they can provide", ...],
        "wants": ["goal/pain point/interest they mentioned", ...],
        "mutual_benefits": ["win-win opportunity identified", ...]
    }} or {{"offers": [], "wants": [], "mutual_benefits": []}}
}}

Focus on:
- What was discussed or accomplished
- Any commitments or deadlines mentioned
- Sentiment and relationship dynamics
- Information that would help in future interactions
- Any Godfather goals that are relevant or implied
- What they can offer (skills, resources, influence, connections)
- What they want or need (goals, pain points, interests)
- Mutual benefit opportunities (win-win scenarios)
"""
        
        try:
            # Retry logic is handled by decorator, but we log attempts
            logger.info("generating_summary_attempt", interaction_id=interaction_id)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing conversations and extracting structured insights. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            summary_data = json.loads(response.choices[0].message.content)
            
            # Create memory summary
            memory_summary = MemorySummary(
                interaction_id=interaction_id,
                summary=summary_data.get("summary", ""),
                key_facts=summary_data.get("key_facts", []),
                sentiment_score=summary_data.get("sentiment_score"),
                sentiment_explanation=summary_data.get("sentiment_explanation"),
                godfather_goals=summary_data.get("godfather_goals", []),
                commitments=summary_data.get("commitments", []),
                next_actions=summary_data.get("next_actions", []),
                preferences=summary_data.get("preferences", [])
            )
            
            db.add(memory_summary)
            db.commit()
            db.refresh(memory_summary)
            
            # Extract and store commitments
            self._extract_and_store_commitments(
                db, memory_summary, interaction.contact_id, interaction.id
            )
            
            # Update contact memory state and value map
            memory_state = self._update_contact_memory_state(db, interaction.contact_id, summary_data.get("value_map"))
            
            # Invalidate cache for this contact
            self._invalidate_contact_cache(interaction.contact_id)
            
            # Check for commitment completion in this interaction
            if memory_state and memory_state.latest_summary:
                try:
                    from src.orchestrator.commitment_manager import CommitmentManager
                    CommitmentManager.detect_commitment_completion(
                        db, interaction.contact_id, memory_state.latest_summary
                    )
                except ImportError:
                    # Orchestrator not available, skip
                    pass
            
            # Trigger orchestrator to refresh suggestions (async, non-blocking)
            try:
                self._trigger_orchestrator_refresh(db, interaction.contact_id)
            except Exception as e:
                logger.warning("orchestrator_refresh_failed", error=str(e))
            
            logger.info(
                "summary_generated",
                interaction_id=interaction_id,
                contact_id=interaction.contact_id
            )
            
            return memory_summary
            
        except Exception as e:
            logger.error("summary_generation_failed", error=str(e), interaction_id=interaction_id)
            raise
    
    def _update_contact_memory_state(
        self,
        db: Session,
        contact_id: str,
        new_value_map: Optional[Dict[str, Any]] = None
    ) -> ContactMemoryState:
        """
        Update rolling contact memory state based on all interactions
        
        Args:
            db: Database session
            contact_id: Contact ID
        
        Returns:
            Updated ContactMemoryState instance
        """
        # Get all recent summaries for this contact
        recent_summaries = db.query(MemorySummary).join(Interaction).filter(
            Interaction.contact_id == contact_id
        ).order_by(MemorySummary.created_at.desc()).limit(10).all()
        
        if not recent_summaries:
            # Return existing memory state or create empty one
            memory_state = db.query(ContactMemoryState).filter(
                ContactMemoryState.contact_id == contact_id
            ).first()
            if not memory_state:
                memory_state = ContactMemoryState(contact_id=contact_id)
                db.add(memory_state)
                db.commit()
            return memory_state
        
        latest_summary = recent_summaries[0]
        latest_interaction = db.query(Interaction).filter(
            Interaction.id == latest_summary.interaction_id
        ).first()
        
        # Aggregate data from recent summaries
        all_goals = set()
        all_actions = []
        all_preferences = set()
        sentiment_scores = []
        
        for summary in recent_summaries:
            if summary.godfather_goals:
                all_goals.update(summary.godfather_goals)
            if summary.next_actions:
                all_actions.extend(summary.next_actions)
            if summary.preferences:
                all_preferences.update(summary.preferences)
            if summary.sentiment_score is not None:
                sentiment_scores.append(summary.sentiment_score)
        
        # Calculate sentiment trend
        sentiment_trend = None
        if len(sentiment_scores) >= 2:
            recent_avg = sum(sentiment_scores[:3]) / min(3, len(sentiment_scores))
            older_avg = sum(sentiment_scores[3:6]) / max(1, len(sentiment_scores) - 3) if len(sentiment_scores) > 3 else recent_avg
            if recent_avg > older_avg + 0.2:
                sentiment_trend = "improving"
            elif recent_avg < older_avg - 0.2:
                sentiment_trend = "declining"
            elif recent_avg > 0.3:
                sentiment_trend = "positive"
            elif recent_avg < -0.3:
                sentiment_trend = "negative"
            else:
                sentiment_trend = "neutral"
        elif len(sentiment_scores) == 1:
            score = sentiment_scores[0]
            if score > 0.3:
                sentiment_trend = "positive"
            elif score < -0.3:
                sentiment_trend = "negative"
            else:
                sentiment_trend = "neutral"
        
        # Get or create memory state
        memory_state = db.query(ContactMemoryState).filter(
            ContactMemoryState.contact_id == contact_id
        ).first()
        
        if not memory_state:
            memory_state = ContactMemoryState(contact_id=contact_id)
            db.add(memory_state)
        
        # Get contact to update value map and relationship score
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        
        # Update value map if new data provided
        if new_value_map and contact:
            existing_value_map = contact.value_map or {"offers": [], "wants": [], "mutual_benefits": []}
            
            # Merge new value map data
            existing_offers = set(existing_value_map.get("offers", []))
            existing_wants = set(existing_value_map.get("wants", []))
            existing_benefits = set(existing_value_map.get("mutual_benefits", []))
            
            new_offers = set(new_value_map.get("offers", []))
            new_wants = set(new_value_map.get("wants", []))
            new_benefits = set(new_value_map.get("mutual_benefits", []))
            
            contact.value_map = {
                "offers": list(existing_offers | new_offers),
                "wants": list(existing_wants | new_wants),
                "mutual_benefits": list(existing_benefits | new_benefits)
            }
        
        # Calculate relationship score
        if contact:
            relationship_score = self._calculate_relationship_score(
                db, contact_id, sentiment_scores, recent_summaries
            )
            contact.relationship_score = relationship_score
        
        # Update fields
        memory_state.latest_summary = latest_summary.summary
        memory_state.sentiment_trend = sentiment_trend
        memory_state.active_goals = list(all_goals)
        memory_state.outstanding_actions = all_actions[:10]  # Keep top 10
        memory_state.key_preferences = list(all_preferences)
        memory_state.last_interaction_at = latest_interaction.created_at if latest_interaction else datetime.utcnow()
        
        # Generate relationship status using AI if needed
        if not memory_state.relationship_status or len(recent_summaries) % 5 == 0:
            memory_state.relationship_status = self._generate_relationship_status(
                recent_summaries, latest_summary
            )
        
        db.commit()
        db.refresh(memory_state)
        
        return memory_state
    
    def _calculate_relationship_score(
        self,
        db: Session,
        contact_id: str,
        sentiment_scores: List[float],
        recent_summaries: List[MemorySummary]
    ) -> float:
        """
        Calculate relationship strength score (0.0 to 1.0)
        
        Factors:
        - Sentiment trend
        - Frequency of interactions
        - Fulfillment of commitments
        - Reciprocity balance
        """
        from src.database.models import Commitment
        
        base_score = 0.5  # Start at neutral
        
        # Sentiment component (0.0 to 0.3)
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            sentiment_component = (avg_sentiment + 1.0) / 2.0 * 0.3  # Normalize to 0-0.3
        else:
            sentiment_component = 0.15  # Neutral if no sentiment data
        
        # Frequency component (0.0 to 0.2)
        interaction_count = len(recent_summaries)
        frequency_component = min(interaction_count / 10.0, 1.0) * 0.2
        
        # Commitment fulfillment component (0.0 to 0.3)
        commitments = db.query(Commitment).filter(
            Commitment.contact_id == contact_id
        ).all()
        
        fulfillment_component = 0.15  # Default
        if commitments:
            completed = sum(1 for c in commitments if c.status == "completed")
            total = len(commitments)
            if total > 0:
                fulfillment_rate = completed / total
                fulfillment_component = fulfillment_rate * 0.3
        
        # Reciprocity component (0.0 to 0.2)
        # Check if we've been giving value (value-first actions)
        # For now, use a simple heuristic based on sentiment
        reciprocity_component = 0.1  # Default neutral
        
        total_score = base_score + sentiment_component + frequency_component + fulfillment_component + reciprocity_component
        
        # Clamp to 0.0-1.0
        return max(0.0, min(1.0, total_score))
    
    def _extract_and_store_commitments(
        self,
        db: Session,
        memory_summary: MemorySummary,
        contact_id: str,
        interaction_id: str
    ) -> None:
        """
        Extract commitments from summary and create Commitment records
        
        Args:
            db: Database session
            memory_summary: MemorySummary with commitments data
            contact_id: Contact ID
            interaction_id: Interaction ID for reference
        """
        if not memory_summary.commitments:
            return
        
        from src.database.models import Commitment
        
        try:
            for commitment_data in memory_summary.commitments:
                if not isinstance(commitment_data, dict):
                    continue
                
                description = commitment_data.get("description", "").strip()
                if not description:
                    continue
                
                # Parse deadline if provided
                deadline = None
                deadline_str = commitment_data.get("deadline")
                if deadline_str:
                    try:
                        # Try ISO format first
                        if isinstance(deadline_str, str):
                            deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                        elif isinstance(deadline_str, datetime):
                            deadline = deadline_str
                    except (ValueError, AttributeError):
                        # Try parsing as date string
                        try:
                            from dateutil import parser
                            deadline = parser.parse(deadline_str)
                        except:
                            logger.warning("failed_to_parse_deadline", deadline=deadline_str)
                
                # Determine who made the commitment
                # Heuristic: if description mentions "I will" or "we will", it's likely Godfather
                # Otherwise, assume it's the contact
                description_lower = description.lower()
                if any(phrase in description_lower for phrase in ["i will", "i'll", "we will", "we'll", "i promise"]):
                    committed_by = "godfather"
                else:
                    committed_by = "contact"
                
                # Check if similar commitment already exists (avoid duplicates)
                existing = db.query(Commitment).filter(
                    Commitment.contact_id == contact_id,
                    Commitment.description.ilike(f"%{description[:50]}%"),
                    Commitment.status == "pending"
                ).first()
                
                if existing:
                    # Update existing commitment if deadline is more specific
                    if deadline and (not existing.deadline or deadline < existing.deadline):
                        existing.deadline = deadline
                        db.commit()
                    continue
                
                # Create new commitment
                commitment = Commitment(
                    contact_id=contact_id,
                    description=description,
                    committed_by=committed_by,
                    deadline=deadline,
                    status="pending"
                )
                
                db.add(commitment)
            
            db.commit()
            logger.info(
                "commitments_extracted",
                contact_id=contact_id,
                interaction_id=interaction_id,
                count=len(memory_summary.commitments) if memory_summary.commitments else 0
            )
        except Exception as e:
            logger.error("commitment_extraction_failed", error=str(e), contact_id=contact_id)
            db.rollback()
    
    def _trigger_orchestrator_refresh(self, db: Session, contact_id: str) -> None:
        """
        Trigger orchestrator to refresh suggestions for a contact after interaction
        
        This is a lightweight trigger that marks the contact for suggestion refresh.
        Actual suggestion generation can happen in background.
        
        Args:
            db: Database session
            contact_id: Contact ID
        """
        try:
            # For now, we'll just log that suggestions should be refreshed
            # In production, this could trigger a background job or queue a task
            logger.info(
                "orchestrator_refresh_triggered",
                contact_id=contact_id,
                note="Suggestions should be regenerated for this contact"
            )
            
            # Optionally: Mark existing suggestions as stale or queue refresh
            # This is a placeholder for future async job implementation
        except Exception as e:
            logger.warning("orchestrator_refresh_trigger_failed", error=str(e), contact_id=contact_id)
    
    def _generate_relationship_status(self, summaries: List[MemorySummary], latest: MemorySummary) -> str:
        """Generate relationship status description using AI"""
        if not summaries:
            return "New contact"
        
        summaries_text = "\n\n".join([
            f"Summary {i+1}: {s.summary}\nSentiment: {s.sentiment_explanation or 'N/A'}"
            for i, s in enumerate(summaries[:5])
        ])
        
        prompt = f"""Based on these interaction summaries, provide a brief (1-2 sentence) relationship status description.

Recent summaries:
{summaries_text}

Provide a concise description of the current relationship status and dynamics."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing relationship dynamics. Provide concise, professional descriptions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("relationship_status_generation_failed", error=str(e))
            return "Active relationship"
    
    def get_contact_context(
        self,
        db: Session,
        contact_id: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve context for a contact to guide task execution (with caching)
        
        Args:
            db: Database session
            contact_id: Contact ID
            use_cache: Whether to use cache (default True)
        
        Returns:
            Dictionary with context information
        """
        # Try cache first
        if use_cache:
            try:
                from src.utils.cache_decorator import get_redis_client
                redis_client = get_redis_client()
                if redis_client:
                    cache_key = f"contact_context:{contact_id}"
                    cached = redis_client.get(cache_key)
                    if cached:
                        import json
                        logger.debug("contact_context_cache_hit", contact_id=contact_id)
                        return json.loads(cached)
            except Exception as e:
                logger.warning("cache_lookup_failed", error=str(e))
        
        memory_state = db.query(ContactMemoryState).filter(
            ContactMemoryState.contact_id == contact_id
        ).first()
        
        if not memory_state:
            result = {
                "has_memory": False,
                "message": "No prior interactions with this contact"
            }
        else:
            # Get recent summaries for additional context
            recent_summaries = db.query(MemorySummary).join(Interaction).filter(
                Interaction.contact_id == contact_id
            ).order_by(MemorySummary.created_at.desc()).limit(3).all()
            
            result = {
                "has_memory": True,
                "latest_summary": memory_state.latest_summary,
                "sentiment_trend": memory_state.sentiment_trend,
                "active_goals": memory_state.active_goals or [],
                "outstanding_actions": memory_state.outstanding_actions or [],
                "relationship_status": memory_state.relationship_status,
                "key_preferences": memory_state.key_preferences or [],
                "last_interaction_at": memory_state.last_interaction_at.isoformat() if memory_state.last_interaction_at else None,
                "recent_summaries": [
                    {
                        "summary": s.summary,
                        "sentiment": s.sentiment_explanation,
                        "channel": s.interaction.channel,
                        "created_at": s.created_at.isoformat()
                    }
                    for s in recent_summaries
                ]
            }
        
        # Cache result (5 minute TTL)
        if use_cache:
            try:
                from src.utils.cache_decorator import get_redis_client
                redis_client = get_redis_client()
                if redis_client:
                    cache_key = f"contact_context:{contact_id}"
                    import json
                    redis_client.setex(
                        cache_key,
                        300,  # 5 minutes
                        json.dumps(result, default=str)
                    )
                    logger.debug("contact_context_cached", contact_id=contact_id)
            except Exception as e:
                logger.warning("cache_store_failed", error=str(e))
        
        return result
    
    def find_contact_by_identifier(
        self,
        db: Session,
        phone_number: Optional[str] = None,
        email: Optional[str] = None
    ) -> Optional[Contact]:
        """
        Find contact by phone number or email
        
        Args:
            db: Database session
            phone_number: Phone number to search for
            email: Email to search for
        
        Returns:
            Contact instance or None
        """
        if phone_number:
            contact = db.query(Contact).filter(Contact.phone_number == phone_number).first()
            if contact:
                return contact
        
        if email:
            contact = db.query(Contact).filter(Contact.email == email).first()
            if contact:
                return contact
        
        return None
    
    def create_contact_if_missing(
        self,
        db: Session,
        phone_number: Optional[str] = None,
        email: Optional[str] = None
    ) -> Contact:
        """
        Find contact by identifier, or create if missing
        
        Args:
            db: Database session
            phone_number: Phone number to search/create
            email: Email to search/create
        
        Returns:
            Contact instance (existing or newly created)
        """
        # Try to find existing contact
        contact = self.find_contact_by_identifier(db, phone_number=phone_number, email=email)
        if contact:
            return contact
        
        # Create new contact
        # Use phone number or email as name if no name available
        name = phone_number or email or "Unknown Contact"
        
        contact = Contact(
            name=name,
            phone_number=phone_number,
            email=email
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
        
        logger.info(
            "contact_auto_created",
            contact_id=contact.id,
            phone_number=phone_number,
            email=email
        )
        
        return contact

