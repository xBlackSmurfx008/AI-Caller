"""
Relationship Operations Service - The "Godfather Brain"

Runs 4 times daily to move relationships forward:
- 5:30 AM: Morning Command Plan
- 12:00 PM: Midday Momentum Push  
- 4:30 PM: Afternoon Coordination & Follow-Up
- 8:00 PM: Relationship Review + Next-Day Prep
"""

from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta, date
import json
import pytz
import uuid

from src.database.models import (
    Contact, ContactMemoryState, Interaction, MemorySummary,
    Project, ProjectStakeholder, Commitment, Suggestion,
    IntroductionRecommendation, Message, RelationshipAction, DailyRunResult,
    GodfatherIntention
)
from src.utils.config import get_settings
from src.utils.openai_client import ensure_chat_model, create_openai_client, retry_openai_call
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RelationshipOpsService:
    """
    Master Networker CRM Orchestrator - Executive Assistant for Relationship Management
    
    Runs scheduled jobs to:
    1. Ingest recent interactions
    2. Update contact memory state
    3. Detect opportunities/risks
    4. Generate action plan + drafts + tasks
    5. Update dashboards + approvals queue
    """
    
    RUN_TYPES = {
        "morning": {
            "title": "Morning Command Plan",
            "focus": "Today's social capital moves + project acceleration",
            "hour": 5,
            "minute": 30
        },
        "midday": {
            "title": "Midday Momentum Push",
            "focus": "Fast follow-through + keep momentum",
            "hour": 12,
            "minute": 0
        },
        "afternoon": {
            "title": "Afternoon Coordination & Follow-Up",
            "focus": "Close loops + schedule next steps",
            "hour": 16,
            "minute": 30
        },
        "evening": {
            "title": "Relationship Review + Next-Day Prep",
            "focus": "Strategic relationship posture",
            "hour": 20,
            "minute": 0
        }
    }
    
    def __init__(self):
        """Initialize relationship ops service"""
        self.client = create_openai_client(timeout=60.0, max_retries=3)
        self.model = ensure_chat_model(settings.OPENAI_MODEL)
        self.timezone = pytz.timezone("America/New_York")
    
    def _chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        timeout: float = 45.0,
        response_format: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
    ):
        """Internal helper to call OpenAI with consistent retry/timeout behavior."""
        @retry_openai_call(max_retries=3, initial_delay=0.5, max_delay=30.0)
        def _call():
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "timeout": timeout,
            }
            if response_format is not None:
                kwargs["response_format"] = response_format
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            return self.client.chat.completions.create(**kwargs)
        
        return _call()
    
    def execute_run(
        self,
        db: Session,
        run_type: str,
        force: bool = False
    ) -> DailyRunResult:
        """
        Execute a relationship ops run
        
        Args:
            db: Database session
            run_type: One of "morning", "midday", "afternoon", "evening"
            force: Force run even if already ran today
            
        Returns:
            DailyRunResult with all outputs
        """
        if run_type not in self.RUN_TYPES:
            raise ValueError(f"Invalid run_type: {run_type}. Must be one of {list(self.RUN_TYPES.keys())}")
        
        run_config = self.RUN_TYPES[run_type]
        now = datetime.now(self.timezone)
        
        # Check if already ran today (unless forced)
        if not force:
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            existing_run = db.query(DailyRunResult).filter(
                DailyRunResult.run_type == run_type,
                DailyRunResult.run_date >= today_start,
                DailyRunResult.status == "completed"
            ).first()
            if existing_run:
                logger.info("run_already_completed", run_type=run_type, run_id=existing_run.id)
                return existing_run
        
        # Create run record
        run = DailyRunResult(
            run_type=run_type,
            run_date=now,
            status="running",
            summary_title=run_config["title"]
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        
        logger.info("relationship_ops_run_started", run_type=run_type, run_id=run.id)
        
        try:
            # Step A: Gather context
            context = self._gather_context(db, run)
            
            # Step B: Update memory
            memory_updates = self._update_contact_memory(db, context)
            run.contacts_updated = len(memory_updates)
            
            # Step C: Opportunity detection
            opportunities = self._detect_opportunities(db, context, run_type)
            
            # Step D: Rank actions
            ranked_actions = self._rank_actions(opportunities)
            
            # Step E: Produce outputs based on run type
            outputs = self._produce_outputs(db, run, ranked_actions, run_type)
            
            # Update run with outputs
            run.top_actions = outputs.get("top_actions", [])
            run.messages_to_reply = outputs.get("messages_to_reply", [])
            run.intros_to_consider = outputs.get("intros_to_consider", [])
            run.trust_risks = outputs.get("trust_risks", [])
            run.value_first_moves = outputs.get("value_first_moves", [])
            run.scheduled_blocks_proposed = outputs.get("scheduled_blocks_proposed", [])
            run.approvals_needed = outputs.get("approvals_needed", [])
            
            # Evening-specific outputs
            if run_type == "evening":
                run.relationship_wins = outputs.get("relationship_wins", [])
                run.relationship_slips = outputs.get("relationship_slips", [])
                run.reconnect_tomorrow = outputs.get("reconnect_tomorrow", [])
                run.health_score_trend = outputs.get("health_score_trend")
            
            # Generate summary
            run.summary_text = self._generate_run_summary(run_type, outputs)
            
            run.status = "completed"
            run.completed_at = datetime.now(self.timezone)
            db.commit()
            
            logger.info("relationship_ops_run_completed", 
                       run_type=run_type, 
                       run_id=run.id,
                       actions_generated=len(run.top_actions or []))
            
            return run
            
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.now(self.timezone)
            db.commit()
            logger.error("relationship_ops_run_failed", run_type=run_type, run_id=run.id, error=str(e))
            raise
    
    def _gather_context(self, db: Session, run: DailyRunResult) -> Dict[str, Any]:
        """
        Step A: Gather all relevant context for the run
        """
        now = datetime.now(self.timezone)
        
        # Get last run time to fetch new interactions
        last_run = db.query(DailyRunResult).filter(
            DailyRunResult.id != run.id,
            DailyRunResult.status == "completed"
        ).order_by(desc(DailyRunResult.completed_at)).first()
        
        last_run_time = last_run.completed_at if last_run else now - timedelta(days=1)
        
        # Fetch new interactions since last run
        new_interactions = db.query(Interaction).filter(
            Interaction.created_at > last_run_time
        ).order_by(desc(Interaction.created_at)).all()
        
        run.interactions_ingested = len(new_interactions)
        
        # Fetch pending messages (inbound, unread)
        pending_messages = db.query(Message).filter(
            Message.direction == "inbound",
            Message.is_read == False
        ).order_by(desc(Message.timestamp)).all()
        
        # Fetch tasks/projects due soon
        from src.database.models import ProjectTask
        due_soon = db.query(ProjectTask).filter(
            ProjectTask.status.notin_(["done", "cancelled"]),
            ProjectTask.due_at.isnot(None),
            ProjectTask.due_at <= now + timedelta(days=7)
        ).order_by(ProjectTask.due_at).all()
        
        # Fetch outstanding commitments
        commitments = db.query(Commitment).filter(
            Commitment.status.in_(["pending", "overdue"])
        ).order_by(Commitment.deadline).all()
        
        # Fetch high-priority contacts not touched recently
        stale_contacts = db.query(Contact).join(ContactMemoryState).filter(
            Contact.is_sensitive == False,
            ContactMemoryState.do_not_contact == False,
            or_(
                ContactMemoryState.last_interaction_at.is_(None),
                ContactMemoryState.last_interaction_at < now - timedelta(days=14)
            )
        ).order_by(Contact.relationship_score.desc()).limit(20).all()
        
        # Fetch pending approvals
        pending_actions = db.query(RelationshipAction).filter(
            RelationshipAction.status == "pending",
            RelationshipAction.requires_approval == True
        ).all()
        
        # Get active projects
        active_projects = db.query(Project).filter(
            Project.status == "active"
        ).all()
        
        return {
            "new_interactions": new_interactions,
            "pending_messages": pending_messages,
            "due_soon_tasks": due_soon,
            "commitments": commitments,
            "stale_contacts": stale_contacts,
            "pending_actions": pending_actions,
            "active_projects": active_projects,
            "last_run_time": last_run_time
        }
    
    def _update_contact_memory(
        self,
        db: Session,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Step B: Update contact memory state for contacts with new interactions
        """
        updated_contacts = []
        
        # Group interactions by contact
        contact_interactions: Dict[str, List[Interaction]] = {}
        for interaction in context["new_interactions"]:
            if interaction.contact_id:
                if interaction.contact_id not in contact_interactions:
                    contact_interactions[interaction.contact_id] = []
                contact_interactions[interaction.contact_id].append(interaction)
        
        # Update each contact's memory state
        for contact_id, interactions in contact_interactions.items():
            try:
                self._update_single_contact_memory(db, contact_id, interactions)
                updated_contacts.append(contact_id)
            except Exception as e:
                logger.error("contact_memory_update_failed", contact_id=contact_id, error=str(e))
        
        db.commit()
        return updated_contacts
    
    def _update_single_contact_memory(
        self,
        db: Session,
        contact_id: str,
        interactions: List[Interaction]
    ):
        """Update memory state for a single contact"""
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return
        
        memory_state = db.query(ContactMemoryState).filter(
            ContactMemoryState.contact_id == contact_id
        ).first()
        
        if not memory_state:
            memory_state = ContactMemoryState(contact_id=contact_id)
            db.add(memory_state)
        
        # Build context for AI analysis
        interaction_summaries = []
        for interaction in interactions:
            summary = db.query(MemorySummary).filter(
                MemorySummary.interaction_id == interaction.id
            ).first()
            interaction_summaries.append({
                "channel": interaction.channel,
                "content": interaction.raw_content[:500],
                "summary": summary.summary if summary else None,
                "sentiment": summary.sentiment_score if summary else None,
                "timestamp": interaction.created_at.isoformat()
            })
        
        # Use AI to update memory state
        prompt = f"""Update the relationship memory state based on new interactions.

Contact: {contact.name}
Organization: {contact.organization or 'N/A'}
Current relationship score: {contact.relationship_score or 0.0}
Current sentiment trend: {memory_state.sentiment_trend or 'neutral'}

New Interactions:
{json.dumps(interaction_summaries, indent=2)}

Previous open loops: {json.dumps(memory_state.open_loops or [])}
Previous outstanding actions: {json.dumps(memory_state.outstanding_actions or [])}

Analyze the interactions and provide updated memory state:

Respond with JSON:
{{
    "latest_summary": "<updated summary of relationship>",
    "sentiment_trend": "<positive|neutral|negative|improving|declining>",
    "open_loops": ["<any unresolved conversation threads>"],
    "outstanding_actions": ["<next actions needed>"],
    "relationship_status": "<brief status description>",
    "commitments_detected": ["<any commitments made in these interactions>"],
    "reciprocity_change": <float -1.0 to 1.0, positive if they gave value, negative if we did>
}}"""

        try:
            response = self._chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert relationship analyst. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
                timeout=30,
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Update memory state
            memory_state.latest_summary = result.get("latest_summary")
            memory_state.sentiment_trend = result.get("sentiment_trend", "neutral")
            memory_state.open_loops = result.get("open_loops", [])
            memory_state.outstanding_actions = result.get("outstanding_actions", [])
            memory_state.relationship_status = result.get("relationship_status")
            memory_state.last_interaction_at = max(i.created_at for i in interactions)
            
            # Update reciprocity
            reciprocity_change = float(result.get("reciprocity_change", 0.0))
            memory_state.reciprocity_balance = (memory_state.reciprocity_balance or 0.0) + reciprocity_change
            
            # Store new commitments if detected
            new_commitments = result.get("commitments_detected", [])
            for commitment_text in new_commitments:
                commitment = Commitment(
                    contact_id=contact_id,
                    description=commitment_text,
                    committed_by="contact",  # Detected from their message
                    status="pending"
                )
                db.add(commitment)
            
        except Exception as e:
            logger.error("memory_state_ai_update_failed", contact_id=contact_id, error=str(e))
    
    def _detect_opportunities(
        self,
        db: Session,
        context: Dict[str, Any],
        run_type: str
    ) -> List[Dict[str, Any]]:
        """
        Step C: Detect relationship opportunities and risks
        """
        opportunities = []
        
        # 1. Unresolved commitments
        for commitment in context["commitments"]:
            if commitment.status == "overdue" or (
                commitment.deadline and commitment.deadline <= datetime.now(self.timezone) + timedelta(days=2)
            ):
                opportunities.append({
                    "type": "follow_up",
                    "subtype": "commitment",
                    "contact_id": commitment.contact_id,
                    "project_id": commitment.project_id,
                    "description": f"Follow up on commitment: {commitment.description[:100]}",
                    "urgency": 0.9 if commitment.status == "overdue" else 0.7,
                    "trust_risk": commitment.status == "overdue",
                    "commitment_id": commitment.id
                })
        
        # 2. Pending messages needing reply
        for message in context["pending_messages"]:
            contact = db.query(Contact).filter(Contact.id == message.contact_id).first()
            opportunities.append({
                "type": "reply",
                "contact_id": message.contact_id,
                "contact_name": contact.name if contact else "Unknown",
                "channel": message.channel,
                "message_id": message.id,
                "description": f"Reply to {contact.name if contact else 'Unknown'} via {message.channel}",
                "preview": (message.text_content or "")[:100],
                "urgency": 0.8,
                "trust_risk": False
            })
        
        # 3. Stale relationships (no touch in X days)
        for contact in context["stale_contacts"]:
            memory = db.query(ContactMemoryState).filter(
                ContactMemoryState.contact_id == contact.id
            ).first()
            
            days_since = 999
            if memory and memory.last_interaction_at:
                days_since = (datetime.now(self.timezone).replace(tzinfo=None) - memory.last_interaction_at.replace(tzinfo=None)).days
            
            opportunities.append({
                "type": "check_in",
                "contact_id": contact.id,
                "contact_name": contact.name,
                "description": f"Check in with {contact.name} (last contact: {days_since} days ago)",
                "days_since": days_since,
                "urgency": min(0.3 + (days_since / 90.0) * 0.5, 0.8),
                "trust_risk": False
            })
        
        # 4. Value-first opportunities
        contacts_with_memory = db.query(Contact).join(ContactMemoryState).filter(
            Contact.is_sensitive == False,
            ContactMemoryState.do_not_contact == False,
            ContactMemoryState.reciprocity_balance < 0  # We owe them value
        ).order_by(ContactMemoryState.reciprocity_balance).limit(10).all()
        
        for contact in contacts_with_memory:
            memory = contact.memory_state
            if memory and memory.wants:
                opportunities.append({
                    "type": "value_first",
                    "contact_id": contact.id,
                    "contact_name": contact.name,
                    "description": f"Offer value to {contact.name}",
                    "wants": memory.wants,
                    "reciprocity_balance": memory.reciprocity_balance,
                    "urgency": 0.5,
                    "trust_risk": False
                })
        
        # 5. Project leverage opportunities
        for project in context["active_projects"]:
            # Find contacts that could help
            network_opps = self._find_project_helpers(db, project)
            for opp in network_opps:
                opportunities.append({
                    "type": "project_leverage",
                    "contact_id": opp["contact_id"],
                    "contact_name": opp["contact_name"],
                    "project_id": project.id,
                    "project_title": project.title,
                    "description": f"Connect {opp['contact_name']} with project: {project.title}",
                    "how_they_help": opp.get("how_they_help"),
                    "urgency": 0.6,
                    "trust_risk": False
                })
        
        # 6. Introduction opportunities
        intro_recommendations = self._find_intro_opportunities(db)
        for intro in intro_recommendations:
            opportunities.append({
                "type": "intro",
                "contact_a_id": intro["contact_a_id"],
                "contact_b_id": intro["contact_b_id"],
                "contact_a_name": intro["contact_a_name"],
                "contact_b_name": intro["contact_b_name"],
                "description": f"Introduce {intro['contact_a_name']} to {intro['contact_b_name']}",
                "mutual_benefit": intro["mutual_benefit"],
                "urgency": 0.4,
                "trust_risk": False
            })
        
        return opportunities
    
    def _find_project_helpers(
        self,
        db: Session,
        project: Project,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find contacts who could help with a project"""
        # Get existing stakeholders
        existing_ids = [
            sh.contact_id for sh in db.query(ProjectStakeholder).filter(
                ProjectStakeholder.project_id == project.id
            ).all()
        ]
        
        # Find contacts with relevant skills/offers
        results = []
        contacts = db.query(Contact).join(ContactMemoryState).filter(
            ~Contact.id.in_(existing_ids) if existing_ids else True,
            Contact.is_sensitive == False,
            ContactMemoryState.do_not_contact == False
        ).limit(50).all()
        
        for contact in contacts:
            if contact.value_map and contact.value_map.get("offers"):
                # Simple keyword matching (could be enhanced with AI)
                offers = " ".join(contact.value_map["offers"]).lower()
                project_text = f"{project.title} {project.description or ''}".lower()
                
                # Check for keyword overlap
                overlap = len(set(offers.split()) & set(project_text.split()))
                if overlap > 1:
                    results.append({
                        "contact_id": contact.id,
                        "contact_name": contact.name,
                        "how_they_help": ", ".join(contact.value_map["offers"][:3])
                    })
        
        return results[:limit]
    
    def _find_intro_opportunities(self, db: Session, limit: int = 5) -> List[Dict[str, Any]]:
        """Find high-value introduction opportunities"""
        # Get recent intro recommendations that haven't been executed
        recommendations = db.query(IntroductionRecommendation).filter(
            IntroductionRecommendation.status == "pending"
        ).order_by(desc(IntroductionRecommendation.score)).limit(limit).all()
        
        results = []
        for rec in recommendations:
            contact_a = db.query(Contact).filter(Contact.id == rec.contact_a_id).first()
            contact_b = db.query(Contact).filter(Contact.id == rec.contact_b_id).first()
            if contact_a and contact_b:
                results.append({
                    "contact_a_id": rec.contact_a_id,
                    "contact_b_id": rec.contact_b_id,
                    "contact_a_name": contact_a.name,
                    "contact_b_name": contact_b.name,
                    "mutual_benefit": rec.mutual_benefit,
                    "score": rec.score
                })
        
        return results
    
    def _rank_actions(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Step D: Rank opportunities by priority score
        
        Priority = weighted combination of:
        - Trust risk (highest weight)
        - Urgency
        - Relationship strength opportunity
        - Reciprocity balance
        - Project impact
        """
        for opp in opportunities:
            # Base score from urgency
            score = opp.get("urgency", 0.5)
            
            # Boost for trust risks
            if opp.get("trust_risk"):
                score += 0.3
            
            # Boost for replies (always high priority)
            if opp["type"] == "reply":
                score += 0.2
            
            # Slight boost for value-first (builds trust)
            if opp["type"] == "value_first":
                score += 0.1
            
            # Cap at 1.0
            opp["priority_score"] = min(score, 1.0)
        
        # Sort by priority score descending
        return sorted(opportunities, key=lambda x: x.get("priority_score", 0), reverse=True)
    
    def _produce_outputs(
        self,
        db: Session,
        run: DailyRunResult,
        ranked_actions: List[Dict[str, Any]],
        run_type: str
    ) -> Dict[str, Any]:
        """
        Step E: Produce outputs based on run type
        """
        outputs: Dict[str, Any] = {
            "top_actions": [],
            "messages_to_reply": [],
            "intros_to_consider": [],
            "trust_risks": [],
            "value_first_moves": [],
            "scheduled_blocks_proposed": [],
            "approvals_needed": []
        }
        
        # Process top actions
        for i, action in enumerate(ranked_actions[:10]):
            # Create RelationshipAction record
            rel_action = self._create_relationship_action(db, run, action)
            if rel_action:
                action_dict = {
                    "action_id": rel_action.id,
                    "type": action["type"],
                    "contact_id": action.get("contact_id"),
                    "contact_name": action.get("contact_name"),
                    "description": action.get("description"),
                    "priority_score": action.get("priority_score", 0.5),
                    "trust_risk": action.get("trust_risk", False),
                    "draft_available": bool(rel_action.draft_message)
                }
                
                if i < 5:
                    outputs["top_actions"].append(action_dict)
                
                # Categorize by type
                if action["type"] == "reply":
                    outputs["messages_to_reply"].append(action_dict)
                elif action["type"] == "intro":
                    outputs["intros_to_consider"].append(action_dict)
                elif action["type"] == "value_first":
                    outputs["value_first_moves"].append(action_dict)
                
                if action.get("trust_risk"):
                    outputs["trust_risks"].append(action_dict)
                
                if rel_action.requires_approval:
                    outputs["approvals_needed"].append(action_dict)
        
        # Evening-specific: relationship wins/slips
        if run_type == "evening":
            outputs.update(self._generate_evening_review(db))
        
        db.commit()
        return outputs
    
    def _create_relationship_action(
        self,
        db: Session,
        run: DailyRunResult,
        opportunity: Dict[str, Any]
    ) -> Optional[RelationshipAction]:
        """Create a RelationshipAction record with draft message"""
        try:
            # Generate draft message if applicable
            draft = None
            draft_channel = opportunity.get("channel")
            
            if opportunity["type"] in ["reply", "follow_up", "check_in", "value_first"]:
                draft = self._generate_draft_message(db, opportunity)
            
            action = RelationshipAction(
                run_id=run.id,
                contact_id=opportunity.get("contact_id"),
                project_id=opportunity.get("project_id"),
                action_type=opportunity["type"],
                priority_score=opportunity.get("priority_score", 0.5),
                why_now=opportunity.get("description"),
                expected_win_win_outcome=opportunity.get("mutual_benefit") or opportunity.get("how_they_help"),
                risk_flags=["trust_risk"] if opportunity.get("trust_risk") else None,
                draft_message=draft,
                draft_channel=draft_channel or "sms",
                requires_approval=True,
                status="pending",
                expires_at=datetime.now(self.timezone) + timedelta(days=3)
            )
            
            db.add(action)
            return action
            
        except Exception as e:
            logger.error("create_relationship_action_failed", error=str(e))
            return None
    
    def _generate_draft_message(
        self,
        db: Session,
        opportunity: Dict[str, Any]
    ) -> Optional[str]:
        """Generate a draft message for an opportunity"""
        contact_id = opportunity.get("contact_id")
        if not contact_id:
            return None
        
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return None
        
        memory = db.query(ContactMemoryState).filter(
            ContactMemoryState.contact_id == contact_id
        ).first()
        
        prompt = f"""Generate a brief, warm message for this relationship action.

Contact: {contact.name}
Action type: {opportunity['type']}
Context: {opportunity.get('description', '')}
Relationship summary: {memory.latest_summary if memory else 'No prior context'}
Sentiment trend: {memory.sentiment_trend if memory else 'neutral'}

Guidelines:
- Be genuine and warm, not transactional
- Keep it brief (2-3 sentences max for SMS/text)
- Match the relationship tone
- If following up on something specific, reference it naturally
- Don't over-apologize or be overly formal

Respond with just the message text, no JSON."""

        try:
            response = self._chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert at crafting warm, genuine relationship messages. Be concise and natural."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200,
                timeout=20,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("draft_message_generation_failed", error=str(e))
            return None
    
    def _generate_evening_review(self, db: Session) -> Dict[str, Any]:
        """Generate evening review outputs"""
        now = datetime.now(self.timezone)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Find today's wins (executed actions, positive interactions)
        executed_today = db.query(RelationshipAction).filter(
            RelationshipAction.status == "executed",
            RelationshipAction.executed_at >= today_start
        ).all()
        
        wins = []
        for action in executed_today:
            contact = db.query(Contact).filter(Contact.id == action.contact_id).first()
            wins.append({
                "contact_name": contact.name if contact else "Unknown",
                "action_type": action.action_type,
                "description": action.why_now
            })
        
        # Find slips (missed commitments, expired actions)
        slips = db.query(Commitment).filter(
            Commitment.status == "overdue",
            Commitment.updated_at >= today_start
        ).all()
        
        slip_data = []
        for slip in slips:
            contact = db.query(Contact).filter(Contact.id == slip.contact_id).first()
            slip_data.append({
                "contact_name": contact.name if contact else "Unknown",
                "description": slip.description,
                "days_overdue": (now.replace(tzinfo=None) - slip.deadline.replace(tzinfo=None)).days if slip.deadline else 0
            })
        
        # Find top 3 to reconnect tomorrow
        stale = db.query(Contact).join(ContactMemoryState).filter(
            Contact.is_sensitive == False,
            ContactMemoryState.do_not_contact == False
        ).order_by(
            ContactMemoryState.last_interaction_at.asc().nullsfirst()
        ).limit(3).all()
        
        reconnect = []
        for contact in stale:
            memory = contact.memory_state
            reconnect.append({
                "contact_id": contact.id,
                "contact_name": contact.name,
                "last_interaction": memory.last_interaction_at.isoformat() if memory and memory.last_interaction_at else None,
                "reason": "Long time since last contact"
            })
        
        # Calculate health score trend (simple average of recent relationship scores)
        recent_contacts = db.query(Contact).filter(
            Contact.relationship_score.isnot(None)
        ).all()
        avg_score = sum(c.relationship_score or 0 for c in recent_contacts) / max(len(recent_contacts), 1)
        
        return {
            "relationship_wins": wins,
            "relationship_slips": slip_data,
            "reconnect_tomorrow": reconnect,
            "health_score_trend": avg_score
        }
    
    def _generate_run_summary(self, run_type: str, outputs: Dict[str, Any]) -> str:
        """Generate executive summary for the run"""
        config = self.RUN_TYPES[run_type]
        
        action_count = len(outputs.get("top_actions", []))
        reply_count = len(outputs.get("messages_to_reply", []))
        risk_count = len(outputs.get("trust_risks", []))
        
        summary_parts = [f"Focus: {config['focus']}"]
        
        if action_count > 0:
            summary_parts.append(f"{action_count} relationship actions recommended")
        
        if reply_count > 0:
            summary_parts.append(f"{reply_count} messages awaiting reply")
        
        if risk_count > 0:
            summary_parts.append(f"⚠️ {risk_count} trust risks detected")
        
        if run_type == "evening":
            wins = len(outputs.get("relationship_wins", []))
            slips = len(outputs.get("relationship_slips", []))
            if wins > 0:
                summary_parts.append(f"✓ {wins} relationship wins today")
            if slips > 0:
                summary_parts.append(f"⚠ {slips} commitments slipped")
        
        return " | ".join(summary_parts)
    
    def get_today_command_center(self, db: Session) -> Dict[str, Any]:
        """
        Get all data needed for Today Command Center view
        """
        now = datetime.now(self.timezone)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get today's runs
        today_runs = db.query(DailyRunResult).filter(
            DailyRunResult.run_date >= today_start,
            DailyRunResult.status == "completed"
        ).order_by(desc(DailyRunResult.completed_at)).all()
        
        # Get pending actions
        pending_actions = db.query(RelationshipAction).filter(
            RelationshipAction.status == "pending"
        ).order_by(desc(RelationshipAction.priority_score)).limit(10).all()
        
        # Get at-risk commitments
        at_risk = db.query(Commitment).filter(
            Commitment.status.in_(["pending", "overdue"]),
            or_(
                Commitment.deadline.is_(None),
                Commitment.deadline <= now + timedelta(days=3)
            )
        ).order_by(Commitment.deadline).limit(5).all()
        
        # Get unread messages
        unread_messages = db.query(Message).filter(
            Message.direction == "inbound",
            Message.is_read == False
        ).order_by(desc(Message.timestamp)).limit(10).all()
        
        # Get pending approvals count
        approval_count = db.query(RelationshipAction).filter(
            RelationshipAction.status == "pending",
            RelationshipAction.requires_approval == True
        ).count()
        
        # Get AI-executable tasks (relationship actions without approval needed)
        ai_ready = db.query(RelationshipAction).filter(
            RelationshipAction.status == "pending",
            RelationshipAction.requires_approval == False
        ).limit(5).all()
        
        # Format outputs
        actions_data = []
        for action in pending_actions:
            contact = db.query(Contact).filter(Contact.id == action.contact_id).first()
            actions_data.append({
                "id": action.id,
                "type": action.action_type,
                "contact_id": action.contact_id,
                "contact_name": contact.name if contact else "Unknown",
                "description": action.why_now,
                "priority_score": action.priority_score,
                "draft_message": action.draft_message,
                "draft_channel": action.draft_channel,
                "requires_approval": action.requires_approval,
                "risk_flags": action.risk_flags
            })
        
        commitments_data = []
        for c in at_risk:
            contact = db.query(Contact).filter(Contact.id == c.contact_id).first()
            commitments_data.append({
                "id": c.id,
                "description": c.description,
                "contact_name": contact.name if contact else "Unknown",
                "deadline": c.deadline.isoformat() if c.deadline else None,
                "status": c.status,
                "is_trust_risk": c.is_trust_risk,
                "committed_by": c.committed_by
            })
        
        messages_data = []
        for msg in unread_messages:
            contact = db.query(Contact).filter(Contact.id == msg.contact_id).first()
            messages_data.append({
                "id": msg.id,
                "contact_id": msg.contact_id,
                "contact_name": contact.name if contact else "Unknown",
                "channel": msg.channel,
                "preview": (msg.text_content or "")[:100],
                "timestamp": msg.timestamp.isoformat()
            })
        
        return {
            "generated_at": now.isoformat(),
            "today_runs": [
                {
                    "id": r.id,
                    "run_type": r.run_type,
                    "title": r.summary_title,
                    "summary": r.summary_text,
                    "completed_at": r.completed_at.isoformat() if r.completed_at else None
                }
                for r in today_runs
            ],
            "top_actions": actions_data,
            "at_risk_commitments": commitments_data,
            "must_reply_messages": messages_data,
            "pending_approvals_count": approval_count,
            "ai_ready_actions": [
                {
                    "id": a.id,
                    "type": a.action_type,
                    "description": a.why_now
                }
                for a in ai_ready
            ]
        }
    
    def approve_action(
        self,
        db: Session,
        action_id: str,
        approved_by: str = "godfather"
    ) -> RelationshipAction:
        """Approve a relationship action"""
        action = db.query(RelationshipAction).filter(
            RelationshipAction.id == action_id
        ).first()
        
        if not action:
            raise ValueError(f"Action {action_id} not found")
        
        action.status = "approved"
        action.approved_by = approved_by
        action.approved_at = datetime.now(self.timezone)
        db.commit()
        
        return action
    
    def dismiss_action(
        self,
        db: Session,
        action_id: str,
        reason: Optional[str] = None
    ) -> RelationshipAction:
        """Dismiss/decline a relationship action"""
        action = db.query(RelationshipAction).filter(
            RelationshipAction.id == action_id
        ).first()
        
        if not action:
            raise ValueError(f"Action {action_id} not found")
        
        action.status = "dismissed"
        db.commit()
        
        return action
    
    def execute_action(
        self,
        db: Session,
        action_id: str
    ) -> Dict[str, Any]:
        """Execute an approved relationship action (send message, etc.)"""
        action = db.query(RelationshipAction).filter(
            RelationshipAction.id == action_id
        ).first()
        
        if not action:
            raise ValueError(f"Action {action_id} not found")
        
        if action.status != "approved":
            raise ValueError(f"Action must be approved before execution. Current status: {action.status}")
        
        result = {"action_id": action_id, "executed": False, "message": ""}
        
        # Execute based on action type
        if action.action_type in ["reply", "follow_up", "check_in", "value_first"]:
            if action.draft_message and action.draft_channel:
                # Send via messaging service
                try:
                    from src.messaging.twilio_service import TwilioMessagingService
                    messaging = TwilioMessagingService()
                    
                    contact = db.query(Contact).filter(Contact.id == action.contact_id).first()
                    if contact and contact.phone_number:
                        # Create message record
                        message = Message(
                            contact_id=action.contact_id,
                            channel=action.draft_channel,
                            direction="outbound",
                            timestamp=datetime.now(self.timezone),
                            text_content=action.draft_message,
                            status="queued"
                        )
                        db.add(message)
                        db.commit()
                        
                        # Send via Twilio
                        sent = messaging.send_sms(contact.phone_number, action.draft_message)
                        
                        action.status = "executed"
                        action.executed_at = datetime.now(self.timezone)
                        result["executed"] = True
                        result["message"] = "Message sent successfully"
                    else:
                        result["message"] = "Contact has no phone number"
                        
                except Exception as e:
                    result["message"] = f"Failed to send: {str(e)}"
                    logger.error("action_execution_failed", action_id=action_id, error=str(e))
        
        db.commit()
        return result

