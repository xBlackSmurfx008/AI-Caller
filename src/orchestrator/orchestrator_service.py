"""CRM-style AI Orchestrator Service - Connects Goals/Projects with Network/Contacts"""

from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import json
import pytz

from src.database.models import (
    Contact, Project, Goal, ContactMemoryState, ProjectStakeholder,
    Suggestion, IntroductionRecommendation, Commitment, MemorySummary, Interaction
)
from src.utils.config import get_settings
from src.utils.openai_client import ensure_chat_model, create_openai_client, retry_openai_call
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class OrchestratorService:
    """Main orchestrator that connects Godfather OS (Goals/Projects) with Network OS (Contacts)"""
    
    def __init__(self):
        """Initialize orchestrator service"""
        self.client = create_openai_client(timeout=60.0, max_retries=3)
        self.model = ensure_chat_model(settings.OPENAI_MODEL)
    
    def _chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        timeout: float = 30.0,
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
    
    def get_project_context(
        self,
        db: Session,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Get full context for a project including stakeholders and network opportunities
        
        Args:
            db: Database session
            project_id: Project ID
        
        Returns:
            Dictionary with project context including network opportunities
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Get stakeholders
        stakeholders = db.query(ProjectStakeholder).filter(
            ProjectStakeholder.project_id == project_id
        ).all()
        
        stakeholder_data = []
        for sh in stakeholders:
            contact = db.query(Contact).filter(Contact.id == sh.contact_id).first()
            memory_state = db.query(ContactMemoryState).filter(
                ContactMemoryState.contact_id == sh.contact_id
            ).first()
            
            stakeholder_data.append({
                "contact_id": sh.contact_id,
                "contact_name": contact.name if contact else "Unknown",
                "role": sh.role,
                "how_they_help": sh.how_they_help,
                "how_we_help": sh.how_we_help,
                "relationship_score": contact.relationship_score if contact else 0.0,
                "memory_state": {
                    "latest_summary": memory_state.latest_summary if memory_state else None,
                    "sentiment_trend": memory_state.sentiment_trend if memory_state else None,
                    "outstanding_actions": memory_state.outstanding_actions if memory_state else []
                } if memory_state else None
            })
        
        # Get goal if linked
        goal = None
        if project.goal_id:
            goal = db.query(Goal).filter(Goal.id == project.goal_id).first()
        
        return {
            "project_id": project.id,
            "title": project.title,
            "description": project.description,
            "status": project.status,
            "milestones": project.milestones or [],
            "constraints": project.constraints or {},
            "goal": {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description
            } if goal else None,
            "stakeholders": stakeholder_data,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    
    def identify_network_opportunities(
        self,
        db: Session,
        project_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Identify contacts in the network who could help with this project
        
        Args:
            db: Database session
            project_id: Project ID
            limit: Maximum number of opportunities to return
        
        Returns:
            List of network opportunity dictionaries
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Validate project has description for AI analysis
        if not project.description and not project.title:
            logger.warning("project_missing_description", project_id=project_id)
            return []
        
        # Get existing stakeholders
        existing_stakeholder_ids = [
            sh.contact_id for sh in db.query(ProjectStakeholder).filter(
                ProjectStakeholder.project_id == project_id
            ).all()
        ]
        
        # Get all contacts with memory states (excluding existing stakeholders)
        contacts = db.query(Contact).filter(
            ~Contact.id.in_(existing_stakeholder_ids) if existing_stakeholder_ids else True,
            Contact.is_sensitive == False
        ).all()
        
        # Build context for AI analysis
        project_context = {
            "title": project.title,
            "description": project.description,
            "milestones": project.milestones or [],
            "constraints": project.constraints or {}
        }
        
        opportunities = []
        
        for contact in contacts:
            memory_state = db.query(ContactMemoryState).filter(
                ContactMemoryState.contact_id == contact.id
            ).first()
            
            if not memory_state:
                continue  # Skip contacts without memory
            
            # Use AI to assess fit
            fit_score, how_they_help, how_we_help = self._assess_contact_project_fit(
                contact, memory_state, project_context
            )
            
            if fit_score > 0.3:  # Only include if there's meaningful fit
                opportunities.append({
                    "contact_id": contact.id,
                    "contact_name": contact.name,
                    "fit_score": fit_score,
                    "how_they_help": how_they_help,
                    "how_we_help": how_we_help,
                    "relationship_score": contact.relationship_score,
                    "value_map": contact.value_map or {},
                    "memory_summary": memory_state.latest_summary
                })
        
        # Sort by fit score
        opportunities.sort(key=lambda x: x["fit_score"], reverse=True)
        
        return opportunities[:limit]
    
    def _assess_contact_project_fit(
        self,
        contact: Contact,
        memory_state: ContactMemoryState,
        project_context: Dict[str, Any]
    ) -> Tuple[float, str, str]:
        """
        Use AI to assess how well a contact fits a project
        
        Returns:
            (fit_score, how_they_help, how_we_help)
        """
        # Validate inputs
        if not contact or not memory_state:
            return (0.0, "", "")
        
        if not project_context.get("title"):
            logger.warning("project_context_missing_title", contact_id=contact.id)
            return (0.0, "", "")
        
        try:
            prompt = f"""Assess how well this contact could help with this project.

Contact:
- Name: {contact.name}
- Organization: {contact.organization or 'N/A'}
- Industries: {', '.join(contact.industries or [])}
- Relationship Summary: {memory_state.latest_summary or 'No summary available'}
- What they offer: {json.dumps(contact.value_map.get('offers', []) if contact.value_map else [])}
- What they want: {json.dumps(contact.value_map.get('wants', []) if contact.value_map else [])}

Project:
- Title: {project_context['title']}
- Description: {project_context.get('description', 'N/A')}
- Milestones: {json.dumps(project_context.get('milestones', []))}

Provide a JSON response:
{{
    "fit_score": <float 0.0 to 1.0>,
    "how_they_help": "<brief explanation of how they could help>",
    "how_we_help": "<brief explanation of how we could help them (win-win)>"
}}"""
            
            response = self._chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert at identifying win-win collaboration opportunities. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
                timeout=30,
            )
            
            result = json.loads(response.choices[0].message.content)
            fit_score = float(result.get("fit_score", 0.0))
            # Clamp score to valid range
            fit_score = max(0.0, min(1.0, fit_score))
            
            return (
                fit_score,
                result.get("how_they_help", ""),
                result.get("how_we_help", "")
            )
            
        except Exception as e:
            logger.error("contact_project_fit_assessment_failed", error=str(e), contact_id=contact.id)
            return (0.0, "", "")
    
    def generate_suggestions(
        self,
        db: Session,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Generate win-win relationship action suggestions
        
        Args:
            db: Database session
            limit: Maximum number of suggestions to generate
        
        Returns:
            List of suggestion dictionaries
        """
        # Get active projects
        active_projects = db.query(Project).filter(
            Project.status == "active"
        ).all()
        
        # Get contacts with memory states
        contacts_with_memory = db.query(Contact).join(ContactMemoryState).filter(
            Contact.is_sensitive == False
        ).all()
        
        suggestions = []
        
        # Generate suggestions for each contact
        for contact in contacts_with_memory:
            memory_state = db.query(ContactMemoryState).filter(
                ContactMemoryState.contact_id == contact.id
            ).first()
            
            if not memory_state:
                continue
            
            # Check for follow-up opportunities
            follow_up_suggestions = self._generate_follow_up_suggestions(
                db, contact, memory_state, active_projects
            )
            suggestions.extend(follow_up_suggestions)
            
            # Check for value-first opportunities
            value_first_suggestions = self._generate_value_first_suggestions(
                db, contact, memory_state, active_projects
            )
            suggestions.extend(value_first_suggestions)
            
            # Check for project leverage opportunities
            project_suggestions = self._generate_project_leverage_suggestions(
                db, contact, memory_state, active_projects
            )
            suggestions.extend(project_suggestions)
        
        # Sort by score and return top suggestions
        suggestions.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        # Store top suggestions in database
        stored_suggestions = []
        for sug in suggestions[:limit]:
            stored = self._store_suggestion(db, sug)
            if stored:
                stored_suggestions.append(stored)
        
        return stored_suggestions
    
    def _generate_follow_up_suggestions(
        self,
        db: Session,
        contact: Contact,
        memory_state: ContactMemoryState,
        active_projects: List[Project]
    ) -> List[Dict[str, Any]]:
        """Generate follow-up suggestions based on open loops and commitments"""
        suggestions = []
        
        # Check for outstanding actions
        if memory_state.outstanding_actions:
            days_since_last = (datetime.utcnow() - memory_state.last_interaction_at).days if memory_state.last_interaction_at else 999
            
            if days_since_last > 3:  # Only suggest if it's been a few days
                suggestions.append({
                    "suggestion_type": "follow_up",
                    "contact_id": contact.id,
                    "intent": f"Follow up on outstanding actions with {contact.name}",
                    "rationale": f"Last interaction was {days_since_last} days ago. Outstanding actions: {', '.join(memory_state.outstanding_actions[:3])}",
                    "expected_upside_godfather": "Maintain momentum and show follow-through",
                    "expected_upside_contact": "Receive timely updates and feel valued",
                    "best_timing": "now" if days_since_last > 7 else "later",
                    "score": 0.6 + (days_since_last / 30.0) * 0.2  # Higher score for older follow-ups
                })
        
        # Check for commitments
        commitments = db.query(Commitment).filter(
            Commitment.contact_id == contact.id,
            Commitment.status == "pending"
        ).all()
        
        for commitment in commitments:
            days_until_deadline = None
            if commitment.deadline:
                days_until_deadline = (commitment.deadline - datetime.utcnow()).days
            
            if days_until_deadline is not None and days_until_deadline < 3:
                suggestions.append({
                    "suggestion_type": "follow_up",
                    "contact_id": contact.id,
                    "project_id": commitment.project_id,
                    "intent": f"Check in on commitment: {commitment.description[:50]}",
                    "rationale": f"Deadline approaching in {days_until_deadline} days",
                    "expected_upside_godfather": "Ensure commitment is met on time",
                    "expected_upside_contact": "Receive reminder and support if needed",
                    "best_timing": "now" if days_until_deadline <= 1 else "later",
                    "score": 0.8 if days_until_deadline <= 1 else 0.6
                })
        
        return suggestions
    
    def _generate_value_first_suggestions(
        self,
        db: Session,
        contact: Contact,
        memory_state: ContactMemoryState,
        active_projects: List[Project]
    ) -> List[Dict[str, Any]]:
        """Generate value-first action suggestions (give before asking)"""
        suggestions = []
        
        value_map = contact.value_map or {}
        wants = value_map.get("wants", [])
        
        if wants:
            # Use AI to generate value-first suggestions
            prompt = f"""Generate a value-first action suggestion for this contact.

Contact: {contact.name}
What they want: {json.dumps(wants)}
Relationship summary: {memory_state.latest_summary or 'N/A'}
Sentiment: {memory_state.sentiment_trend or 'neutral'}

Suggest a specific action we could take to help them (introduction, resource, opportunity, feedback, etc.) without asking for anything in return.

Respond with JSON:
{{
    "action": "<specific action>",
    "rationale": "<why this would be valuable>",
    "message_draft": "<suggested message>"
}}"""
            
            try:
                response = self._chat_completion(
                    messages=[
                        {"role": "system", "content": "You are an expert at identifying ways to add value to relationships. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"},
                    timeout=30,
                )
                
                result = json.loads(response.choices[0].message.content)
                
                suggestions.append({
                    "suggestion_type": "value_first",
                    "contact_id": contact.id,
                    "intent": f"Add value to {contact.name} by: {result.get('action', '')}",
                    "rationale": result.get("rationale", ""),
                    "expected_upside_godfather": "Build trust and reciprocity",
                    "expected_upside_contact": result.get("rationale", ""),
                    "message_draft": result.get("message_draft", ""),
                    "best_timing": "now",
                    "score": 0.7
                })
            except Exception as e:
                logger.error("value_first_suggestion_failed", error=str(e), contact_id=contact.id)
        
        return suggestions
    
    def _generate_project_leverage_suggestions(
        self,
        db: Session,
        contact: Contact,
        memory_state: ContactMemoryState,
        active_projects: List[Project]
    ) -> List[Dict[str, Any]]:
        """Generate suggestions to involve contact in active projects"""
        suggestions = []
        
        # Check if contact is already a stakeholder
        existing_project_ids = [
            sh.project_id for sh in db.query(ProjectStakeholder).filter(
                ProjectStakeholder.contact_id == contact.id
            ).all()
        ]
        
        for project in active_projects:
            if project.id in existing_project_ids:
                continue  # Already involved
            
            # Assess fit
            fit_score, how_they_help, how_we_help = self._assess_contact_project_fit(
                contact,
                memory_state,
                {
                    "title": project.title,
                    "description": project.description or "",
                    "milestones": project.milestones or []
                }
            )
            
            if fit_score > 0.5:  # Only suggest if strong fit
                suggestions.append({
                    "suggestion_type": "contact",
                    "contact_id": contact.id,
                    "project_id": project.id,
                    "intent": f"Involve {contact.name} in project: {project.title}",
                    "rationale": f"Strong fit (score: {fit_score:.2f}). {how_they_help}",
                    "expected_upside_godfather": how_they_help,
                    "expected_upside_contact": how_we_help,
                    "best_timing": "now" if fit_score > 0.7 else "later",
                    "score": fit_score
                })
        
        return suggestions
    
    def _store_suggestion(
        self,
        db: Session,
        suggestion_data: Dict[str, Any]
    ) -> Optional[Suggestion]:
        """Store a suggestion in the database"""
        try:
            from datetime import datetime, timedelta
            
            # Set default expiration (7 days for most, 3 days for time-sensitive)
            expires_at = None
            best_timing = suggestion_data.get("best_timing", "later")
            if best_timing == "now":
                expires_at = datetime.utcnow() + timedelta(days=3)
            else:
                expires_at = datetime.utcnow() + timedelta(days=7)
            
            suggestion = Suggestion(
                suggestion_type=suggestion_data.get("suggestion_type"),
                contact_id=suggestion_data.get("contact_id"),
                project_id=suggestion_data.get("project_id"),
                intent=suggestion_data.get("intent", ""),
                rationale=suggestion_data.get("rationale"),
                expected_upside_godfather=suggestion_data.get("expected_upside_godfather"),
                expected_upside_contact=suggestion_data.get("expected_upside_contact"),
                risk_flags=suggestion_data.get("risk_flags"),
                message_draft=suggestion_data.get("message_draft"),
                best_timing=best_timing,
                score=suggestion_data.get("score"),
                expires_at=expires_at
            )
            
            db.add(suggestion)
            db.commit()
            db.refresh(suggestion)
            
            return suggestion
        except Exception as e:
            logger.error("store_suggestion_failed", error=str(e))
            db.rollback()
            return None
    
    def generate_introduction_recommendations(
        self,
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for introducing contacts to each other
        
        Args:
            db: Database session
            limit: Maximum number of recommendations
        
        Returns:
            List of introduction recommendation dictionaries
        """
        contacts = db.query(Contact).filter(
            Contact.is_sensitive == False
        ).all()
        
        recommendations = []
        
        # Compare pairs of contacts
        for i, contact_a in enumerate(contacts):
            memory_a = db.query(ContactMemoryState).filter(
                ContactMemoryState.contact_id == contact_a.id
            ).first()
            
            if not memory_a:
                continue
            
            for contact_b in contacts[i+1:]:
                memory_b = db.query(ContactMemoryState).filter(
                    ContactMemoryState.contact_id == contact_b.id
                ).first()
                
                if not memory_b:
                    continue
                
                # Use AI to assess mutual benefit
                mutual_benefit, score = self._assess_introduction_fit(
                    contact_a, memory_a, contact_b, memory_b
                )
                
                if score > 0.5:  # Only include if meaningful mutual benefit
                    recommendations.append({
                        "contact_a_id": contact_a.id,
                        "contact_b_id": contact_b.id,
                        "mutual_benefit": mutual_benefit,
                        "score": score
                    })
        
        # Sort by score
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        # Store top recommendations
        stored = []
        for rec in recommendations[:limit]:
            stored_rec = IntroductionRecommendation(
                contact_a_id=rec["contact_a_id"],
                contact_b_id=rec["contact_b_id"],
                mutual_benefit=rec["mutual_benefit"],
                score=rec["score"]
            )
            db.add(stored_rec)
            stored.append(stored_rec)
        
        db.commit()
        
        return [{
            "id": r.id,
            "contact_a_id": r.contact_a_id,
            "contact_b_id": r.contact_b_id,
            "mutual_benefit": r.mutual_benefit,
            "score": r.score
        } for r in stored]
    
    def _assess_introduction_fit(
        self,
        contact_a: Contact,
        memory_a: ContactMemoryState,
        contact_b: Contact,
        memory_b: ContactMemoryState
    ) -> Tuple[str, float]:
        """Use AI to assess if two contacts should be introduced"""
        # Validate inputs
        if not all([contact_a, memory_a, contact_b, memory_b]):
            return ("", 0.0)
        
        try:
            prompt = f"""Assess if these two contacts should be introduced to each other.

Contact A:
- Name: {contact_a.name}
- Organization: {contact_a.organization or 'N/A'}
- What they offer: {json.dumps(contact_a.value_map.get('offers', []) if contact_a.value_map else [])}
- What they want: {json.dumps(contact_a.value_map.get('wants', []) if contact_a.value_map else [])}
- Summary: {memory_a.latest_summary or 'N/A'}

Contact B:
- Name: {contact_b.name}
- Organization: {contact_b.organization or 'N/A'}
- What they offer: {json.dumps(contact_b.value_map.get('offers', []) if contact_b.value_map else [])}
- What they want: {json.dumps(contact_b.value_map.get('wants', []) if contact_b.value_map else [])}
- Summary: {memory_b.latest_summary or 'N/A'}

Respond with JSON:
{{
    "mutual_benefit": "<explanation of why they should meet>",
    "score": <float 0.0 to 1.0>
}}"""
            
            response = self._chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert at identifying win-win introduction opportunities. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
                timeout=30,
            )
            
            result = json.loads(response.choices[0].message.content)
            score = float(result.get("score", 0.0))
            score = max(0.0, min(1.0, score))  # Clamp to valid range
            
            return (
                result.get("mutual_benefit", ""),
                score
            )
                    
        except Exception as e:
            logger.error("introduction_assessment_failed", error=str(e))
            return ("", 0.0)
    
    def recommend_channel(
        self,
        db: Session,
        contact_id: str,
        memory_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Recommend best channel for messaging a contact
        
        Args:
            db: Database session
            contact_id: Contact ID
            memory_context: Optional memory context from memory service
            
        Returns:
            Dictionary with channel recommendation and rationale
        """
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")
        
        # Get channel identities
        from src.database.models import ChannelIdentity
        channel_identities = db.query(ChannelIdentity).filter(
            ChannelIdentity.contact_id == contact_id
        ).all()
        
        available_channels = [ci.channel for ci in channel_identities]
        
        # If no channel identities, default to SMS if phone number exists
        if not available_channels and contact.phone_number:
            available_channels = ["sms"]
        
        if not available_channels:
            return {
                "channel": "sms",
                "rationale": "No contact information available, defaulting to SMS"
            }
        
        # Use AI to recommend channel based on context
        memory_str = ""
        if memory_context:
            memory_str = f"""
Relationship: {memory_context.get('relationship_status', 'N/A')}
Sentiment: {memory_context.get('sentiment_trend', 'N/A')}
Last interaction: {memory_context.get('last_interaction_at', 'N/A')}
"""
        
        prompt = f"""Recommend the best messaging channel for this contact.

Contact: {contact.name}
Available channels: {', '.join(available_channels)}
{memory_str}

Consider:
- Urgency of message
- Relationship formality
- Contact preferences (if known)
- Channel reliability

Respond with JSON:
{{
    "channel": "<sms|whatsapp|mms>",
    "rationale": "<explanation>"
}}"""
        
        try:
            response = self._chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert at choosing communication channels. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
                timeout=20,
            )
            
            result = json.loads(response.choices[0].message.content)
            recommended = result.get("channel", available_channels[0])
            
            # Ensure recommended channel is available
            if recommended not in available_channels:
                recommended = available_channels[0]
            
            return {
                "channel": recommended,
                "rationale": result.get("rationale", f"Recommended {recommended} based on context")
            }
        except Exception as e:
            logger.error("channel_recommendation_failed", error=str(e), contact_id=contact_id)
            return {
                "channel": available_channels[0],
                "rationale": "Default channel selection"
            }
    
    def generate_message_draft(
        self,
        db: Session,
        contact_id: str,
        channel: str,
        memory_context: Optional[Dict[str, Any]] = None,
        intent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate message draft for a contact
        
        Args:
            db: Database session
            contact_id: Contact ID
            channel: Channel name
            memory_context: Optional memory context
            intent: Optional intent/purpose for the message
            
        Returns:
            Dictionary with draft, rationale, risk flags, and tone guidance
        """
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")
        
        # Build context
        context_parts = []
        
        if memory_context:
            if memory_context.get("latest_summary"):
                context_parts.append(f"Latest interaction: {memory_context['latest_summary']}")
            if memory_context.get("sentiment_trend"):
                context_parts.append(f"Sentiment: {memory_context['sentiment_trend']}")
            if memory_context.get("outstanding_actions"):
                context_parts.append(f"Outstanding actions: {', '.join(memory_context['outstanding_actions'][:3])}")
            if memory_context.get("key_preferences"):
                context_parts.append(f"Preferences: {', '.join(memory_context['key_preferences'][:3])}")
        
        # Get active projects
        from src.database.models import ProjectStakeholder
        project_stakeholders = db.query(ProjectStakeholder).filter(
            ProjectStakeholder.contact_id == contact_id
        ).all()
        
        if project_stakeholders:
            project_ids = [ps.project_id for ps in project_stakeholders]
            projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
            if projects:
                project_titles = [p.title for p in projects]
                context_parts.append(f"Active projects: {', '.join(project_titles)}")
        
        context_str = "\n".join(context_parts) if context_parts else "No prior context available."
        
        # Build prompt
        intent_str = f"\nIntent: {intent}" if intent else ""
        
        prompt = f"""Generate a message draft for {contact.name} via {channel}.

Context:
{context_str}
{intent_str}

Guidelines:
- Match the relationship tone and formality
- Be value-first (give before asking)
- Keep it concise and clear
- Respect any known preferences
- Avoid over-asking or sensitive topics
- Consider the channel (SMS should be shorter, WhatsApp can be more conversational)

Respond with JSON:
{{
    "draft": "<message text>",
    "rationale": "<why this message and tone>",
    "risk_flags": ["<any risks or concerns>"] or [],
    "tone_guidance": "<brief tone description>"
}}"""
        
        try:
            response = self._chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert at crafting relationship-building messages. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
                timeout=30,
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "draft": result.get("draft", ""),
                "rationale": result.get("rationale", ""),
                "risk_flags": result.get("risk_flags", []),
                "tone_guidance": result.get("tone_guidance", "")
            }
        except Exception as e:
            logger.error("message_draft_generation_failed", error=str(e), contact_id=contact_id)
            return None
    
    def generate_project_plan(
        self,
        db: Session,
        goal_description: str,
        project_title: Optional[str] = None,
        target_due_date: Optional[datetime] = None,
        priority: int = 5
    ) -> Dict[str, Any]:
        """
        Generate a project plan from a goal description (AI-powered)
        
        Args:
            db: Database session
            goal_description: Description of the goal/project
            project_title: Optional project title (AI will generate if not provided)
            target_due_date: Optional target completion date
            priority: Priority level (1-10)
        
        Returns:
            Dictionary with project and tasks
        """
        try:
            prompt = f"""Generate a detailed project plan for this goal:

Goal: {goal_description}
Target completion: {target_due_date.isoformat() if target_due_date else 'Not specified'}
Priority: {priority}/10

Create a structured project plan with:
1. Project title
2. Project description
3. List of tasks, each with:
   - Title
   - Description
   - Estimated time in minutes
   - Priority (1-10)
   - Dependencies (list of task indices that must complete first, empty if none)
   - Execution mode: "HUMAN", "AI", or "HYBRID"
   - Tags: ["deep_work"] or ["shallow_work"] or both
   - Energy level: "low", "medium", or "high"
   - Deadline type: "HARD" or "FLEX"

Tasks should be ordered logically with dependencies considered.

Respond with JSON:
{{
    "project_title": "<title>",
    "project_description": "<description>",
    "tasks": [
        {{
            "title": "<task title>",
            "description": "<task description>",
            "estimated_minutes": <number>,
            "priority": <1-10>,
            "dependencies": [<task indices>],
            "execution_mode": "<HUMAN|AI|HYBRID>",
            "tags": ["<tag>"],
            "energy_level": "<low|medium|high>",
            "deadline_type": "<HARD|FLEX>"
        }}
    ]
}}"""
            
            response = self._chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert project planner. Break down goals into actionable tasks with realistic time estimates. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
                timeout=45,
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Create project
            from src.database.models import Project
            project = Project(
                title=result.get("project_title") or project_title or "Untitled Project",
                description=result.get("project_description") or goal_description,
                priority=priority,
                target_due_date=target_due_date,
                status="active"
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            
            # Create tasks
            from src.database.models import ProjectTask
            created_tasks = []
            task_map = {}  # Map task index to task ID for dependencies
            
            for idx, task_data in enumerate(result.get("tasks", [])):
                # Resolve dependencies (convert indices to task IDs)
                dependency_ids = []
                if task_data.get("dependencies"):
                    for dep_idx in task_data["dependencies"]:
                        if dep_idx in task_map:
                            dependency_ids.append(task_map[dep_idx])
                
                task = ProjectTask(
                    project_id=project.id,
                    title=task_data.get("title", "Untitled Task"),
                    description=task_data.get("description"),
                    estimated_minutes=task_data.get("estimated_minutes", 60),
                    priority=task_data.get("priority", 5),
                    dependencies=dependency_ids if dependency_ids else None,
                    execution_mode=task_data.get("execution_mode", "HUMAN"),
                    tags=task_data.get("tags", []),
                    energy_level=task_data.get("energy_level", "medium"),
                    deadline_type=task_data.get("deadline_type", "FLEX"),
                    status="todo"
                )
                db.add(task)
                db.commit()
                db.refresh(task)
                
                task_map[idx] = task.id
                created_tasks.append(task)
            
            return {
                "project_id": project.id,
                "project_title": project.title,
                "tasks_created": len(created_tasks),
                "tasks": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "estimated_minutes": t.estimated_minutes,
                        "execution_mode": t.execution_mode
                    }
                    for t in created_tasks
                ]
            }
        except Exception as e:
            logger.error("project_plan_generation_failed", error=str(e))
            raise
    
    def generate_daily_plan(
        self,
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate daily plan with scheduled tasks and AI-executable actions
        
        Returns:
            Dictionary with today's plan
        """
        from datetime import date, timedelta
        from src.database.models import ProjectTask, CalendarBlock, AIExecution
        
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=pytz.UTC)
        today_end = today_start + timedelta(days=1)
        
        # Get tasks scheduled for today
        today_blocks = db.query(CalendarBlock).filter(
            CalendarBlock.start_at >= today_start,
            CalendarBlock.start_at < today_end
        ).all()
        
        scheduled_tasks = []
        for block in today_blocks:
            task = db.query(ProjectTask).filter(ProjectTask.id == block.task_id).first()
            if task:
                scheduled_tasks.append({
                    "task_id": task.id,
                    "title": task.title,
                    "start": block.start_at.isoformat(),
                    "end": block.end_at.isoformat(),
                    "estimated_minutes": task.estimated_minutes,
                    "execution_mode": task.execution_mode
                })
        
        # Get high-priority tasks not yet scheduled
        unscheduled_high_priority = db.query(ProjectTask).filter(
            ProjectTask.status.in_(["todo", "scheduled"]),
            ProjectTask.priority >= 7,
            ~ProjectTask.id.in_([b.task_id for b in today_blocks])
        ).order_by(ProjectTask.priority.desc(), ProjectTask.due_at.asc()).limit(5).all()
        
        # Get AI-executable tasks
        ai_tasks = db.query(ProjectTask).filter(
            ProjectTask.execution_mode.in_(["AI", "HYBRID"]),
            ProjectTask.status == "todo"
        ).order_by(ProjectTask.priority.desc()).limit(5).all()
        
        # Get tasks at risk (due soon, not scheduled)
        risk_tasks = db.query(ProjectTask).filter(
            ProjectTask.status != "done",
            ProjectTask.due_at.isnot(None),
            ProjectTask.due_at <= datetime.now(pytz.UTC) + timedelta(days=3),
            ~ProjectTask.id.in_([b.task_id for b in today_blocks])
        ).all()
        
        return {
            "date": date.today().isoformat(),
            "scheduled_tasks": scheduled_tasks,
            "unscheduled_high_priority": [
                {
                    "task_id": t.id,
                    "title": t.title,
                    "priority": t.priority,
                    "due_at": t.due_at.isoformat() if t.due_at else None
                }
                for t in unscheduled_high_priority
            ],
            "ai_executable_tasks": [
                {
                    "task_id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "execution_mode": t.execution_mode
                }
                for t in ai_tasks
            ],
            "at_risk_tasks": [
                {
                    "task_id": t.id,
                    "title": t.title,
                    "due_at": t.due_at.isoformat(),
                    "deadline_type": t.deadline_type
                }
                for t in risk_tasks
            ]
        }

