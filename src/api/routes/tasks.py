"""Task management API routes (plan -> confirm -> execute)."""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

from src.agent.assistant import VoiceAssistant
from src.utils.logging import get_logger
from src.utils.errors import TaskError
from src.security.policy import Actor, decide_confirmation, PlannedToolCall
from src.database.database import get_db, init_db
from src.database.models import Task as TaskModel
from src.memory.memory_service import MemoryService
from src.orchestrator.orchestrator_service import OrchestratorService
from src.memory.interaction_capture import capture_sms_interaction, capture_email_interaction
from src.cost.cost_estimator import CostEstimator
from src.cost.runtime_cost_tracker import RuntimeCostTracker
from src.cost.cost_event_logger import CostEventLogger
from src.cost.instrumentation import OpenAIInstrumentation
from src.cost.budget_manager import BudgetManager

router = APIRouter()
logger = get_logger(__name__)
assistant = VoiceAssistant()
memory_service = MemoryService()
orchestrator_service = OrchestratorService()
cost_estimator = CostEstimator()
runtime_cost_tracker = RuntimeCostTracker()
cost_logger = CostEventLogger()
budget_manager = BudgetManager()

# Initialize database on module load
try:
    init_db()
except Exception as e:
    logger.warning("database_init_failed", error=str(e))


class TaskRequest(BaseModel):
    """Task request model"""
    task: str
    context: Optional[Dict[str, Any]] = None
    # Optional actor info (used for policy decisions)
    actor_phone: Optional[str] = None
    actor_email: Optional[str] = None
    # Optional project association
    project_id: Optional[str] = None


class TaskResponse(BaseModel):
    """Task response model"""
    task_id: str
    status: str
    task: str
    requires_confirmation: bool = False
    planned_tool_calls: Optional[List[Dict[str, Any]]] = None
    policy_reasons: Optional[List[str]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str


class TaskConfirmRequest(BaseModel):
    approve: bool


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(request: TaskRequest, db: Session = Depends(get_db)):
    """
    Create a task.
    
    Flow:
    - Plan tool calls (no side effects)
    - If policy requires confirmation: return awaiting_confirmation
    - Else: execute immediately
    """
    try:
        task_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Build context with project_id if provided
        task_context = request.context or {}
        if request.project_id:
            task_context["project_id"] = request.project_id
        
        # Create task record
        task_record = TaskModel(
            task_id=task_id,
            status="planning",
            task=request.task,
            context=task_context,
            created_at=now,
            updated_at=now,
        )
        db.add(task_record)
        db.commit()
        db.refresh(task_record)
        
        logger.info("task_created", task_id=task_id, task=request.task)
        
        # Plan (no side effects)
        try:
            # Enhance context with memory if contact is involved
            enhanced_context = request.context or {}
            if request.task:
                # Try to extract contact info from task and retrieve memory
                # This is a simple heuristic - could be improved with NLP
                enhanced_context = await _enhance_context_with_memory(db, request.task, enhanced_context)
            
            # Resolve preferences for this task
            try:
                from src.orchestrator.preference_resolver import PreferenceResolver
                resolver = PreferenceResolver()
                preference_context = resolver.resolve_preferences(db, request.task, enhanced_context)
                
                # Add preference context to enhanced_context
                enhanced_context["preferences"] = preference_context
                
                # If a default preference was chosen, add it to the plan response
                if preference_context.get("chosen_default"):
                    default_name = preference_context["chosen_default"].get("name")
                    if default_name:
                        enhanced_context["preferred_vendor"] = default_name
                        enhanced_context["preference_reason"] = f"Using your preferred {preference_context.get('intent', 'option')}: {default_name}"
            except Exception as pref_error:
                logger.warning("preference_resolution_failed", error=str(pref_error))
                # Continue without preferences if resolution fails
            
            plan = assistant.plan_task(request.task, enhanced_context)
            planned_tool_calls = plan.get("planned_tool_calls") or []
            
            # Log LLM cost from planning
            openai_response = plan.get("_openai_response")
            if openai_response:
                try:
                    from src.cost.instrumentation import OpenAIInstrumentation
                    instrumentation = OpenAIInstrumentation(db)
                    instrumentation.log_chat_completion(
                        response=openai_response,
                        task_id=task_record.task_id,
                        metadata={"phase": "planning"}
                    )
                except Exception as cost_error:
                    logger.warning("cost_logging_failed", error=str(cost_error))

            # Estimate cost after planning
            cost_estimate = cost_estimator.estimate_task_cost(
                db=db,
                task_plan={"task": request.task, "description": request.task},
                tool_plan=planned_tool_calls,
                context_size=None,
                model_config={"model": assistant.model}
            )
            
            # Check budget constraints
            budget_alert = budget_manager.check_task_estimate(
                db=db,
                task_id=task_record.task_id,
                estimated_cost=cost_estimate["estimated_total_cost"]
            )
            
            # Start cost tracking
            runtime_cost_tracker.start_task_tracking(
                db=db,
                task_id=task_record.task_id,
                estimate=cost_estimate
            )

            actor = Actor(
                kind="godfather" if request.actor_phone or request.actor_email else "external",
                phone_number=request.actor_phone,
                email=request.actor_email,
            )
            policy = decide_confirmation(
                actor=actor,
                planned_calls=[PlannedToolCall(name=c["name"], arguments=c.get("arguments") or {}) for c in planned_tool_calls],
            )

            task_record.status = "awaiting_confirmation" if policy.requires_confirmation else "processing"
            task_record.requires_confirmation = policy.requires_confirmation
            task_record.policy_reasons = policy.reasons
            task_record.planned_tool_calls = planned_tool_calls
            task_record.plan_response = plan.get("response")
            task_record.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(task_record)

            if not policy.requires_confirmation:
                tool_results = await assistant.execute_planned_tools(planned_tool_calls)
                
                # Capture interactions for memory system
                await _capture_interactions_from_tools(db, tool_results)
                
                # Finalize cost tracking
                try:
                    cost_report = runtime_cost_tracker.finalize_task_costs(db, task_record.task_id)
                    logger.info("task_cost_finalized", task_id=task_record.task_id, actual_cost=cost_report.get("actual_total_cost"))
                except Exception as cost_error:
                    logger.error("cost_finalization_failed", error=str(cost_error))
                
                task_record.status = "completed"
                task_record.result = {
                    "success": True,
                    "response": plan.get("response"),
                    "tool_results": tool_results,
                    "task": request.task,
                }
                task_record.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(task_record)
        except Exception as e:
            logger.error("task_execution_failed", task_id=task_id, error=str(e))
            task_record.status = "failed"
            task_record.error = str(e)
            task_record.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(task_record)
        
        return _task_to_response(task_record)
        
    except Exception as e:
        db.rollback()
        logger.error("create_task_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get task status and results"""
    task_record = db.query(TaskModel).filter(TaskModel.task_id == task_id).first()
    if not task_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return _task_to_response(task_record)


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """List all tasks"""
    tasks = db.query(TaskModel).order_by(TaskModel.created_at.desc()).offset(offset).limit(limit).all()
    return [_task_to_response(task) for task in tasks]


@router.post("/{task_id}/confirm", response_model=TaskResponse)
async def confirm_task(task_id: str, request: TaskConfirmRequest, db: Session = Depends(get_db)):
    """Approve or reject a pending task."""
    task_record = db.query(TaskModel).filter(TaskModel.task_id == task_id).first()
    if not task_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if task_record.status != "awaiting_confirmation":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task is not awaiting confirmation")

    task_record.updated_at = datetime.utcnow()

    if not request.approve:
        task_record.status = "rejected"
        task_record.result = {"success": False, "response": "Rejected by Godfather", "tool_results": []}
        db.commit()
        db.refresh(task_record)
        return _task_to_response(task_record)

    # Execute side effects
    task_record.status = "processing"
    planned_tool_calls = task_record.planned_tool_calls or []
    plan_response = task_record.plan_response
    try:
        tool_results = await assistant.execute_planned_tools(planned_tool_calls)
        
        # Capture interactions for memory system
        await _capture_interactions_from_tools(db, tool_results)
        
        task_record.status = "completed"
        task_record.result = {
            "success": True,
            "response": plan_response or "Approved and executed.",
            "tool_results": tool_results,
            "task": task_record.task,
        }
        task_record.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task_record)
    except Exception as e:
        task_record.status = "failed"
        task_record.error = str(e)
        task_record.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task_record)

    return _task_to_response(task_record)


async def _enhance_context_with_memory(
    db: Session,
    task: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enhance context with contact memory if a contact is mentioned in the task
    
    Args:
        db: Database session
        task: Task description
        context: Existing context
    
    Returns:
        Enhanced context with memory information
    """
    try:
        # Simple heuristic: look for phone numbers or emails in task
        import re
        from difflib import SequenceMatcher
        
        phone_pattern = r'\+?[1-9]\d{1,14}'
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        phones = re.findall(phone_pattern, task)
        emails = re.findall(email_pattern, task)
        
        memory_contexts = []
        found_contact_ids = set()
        
        # Find contacts by phone/email
        for phone in phones:
            contact = memory_service.find_contact_by_identifier(db, phone_number=phone)
            if contact and contact.id not in found_contact_ids:
                memory_context = memory_service.get_contact_context(db, contact.id)
                if memory_context.get("has_memory"):
                    memory_contexts.append({
                        "contact": contact.name,
                        "memory": memory_context
                    })
                    found_contact_ids.add(contact.id)
        
        for email in emails:
            contact = memory_service.find_contact_by_identifier(db, email=email)
            if contact and contact.id not in found_contact_ids:
                memory_context = memory_service.get_contact_context(db, contact.id)
                if memory_context.get("has_memory"):
                    memory_contexts.append({
                        "contact": contact.name,
                        "memory": memory_context
                    })
                    found_contact_ids.add(contact.id)
        
        # Try to find contacts by name using fuzzy matching
        # Extract potential names (capitalized words, 2+ characters, not common words)
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'call', 'send', 'email', 'sms', 'text', 'message', 'to', 'about', 'meeting', 'call', 'schedule'}
        
        # Extract capitalized words that might be names
        words = re.findall(r'\b[A-Z][a-z]+\b', task)
        potential_names = [w for w in words if w.lower() not in common_words and len(w) > 2]
        
        # Get all contacts for fuzzy matching
        from src.database.models import Contact
        all_contacts = db.query(Contact).all()
        
        for potential_name in potential_names:
            if potential_name.lower() in [c.name.lower() for c in all_contacts]:
                # Exact match (case-insensitive)
                contact = db.query(Contact).filter(
                    Contact.name.ilike(f"%{potential_name}%")
                ).first()
            else:
                # Fuzzy match - find best match
                best_match = None
                best_score = 0.0
                
                for contact in all_contacts:
                    if contact.id in found_contact_ids:
                        continue
                    
                    # Try full name match
                    similarity = SequenceMatcher(None, potential_name.lower(), contact.name.lower()).ratio()
                    
                    # Also try matching against first or last name
                    name_parts = contact.name.split()
                    for part in name_parts:
                        part_similarity = SequenceMatcher(None, potential_name.lower(), part.lower()).ratio()
                        similarity = max(similarity, part_similarity)
                    
                    if similarity > best_score:
                        best_score = similarity
                        best_match = contact
                
                # Use 80% similarity threshold
                if best_score >= 0.8:
                    contact = best_match
                else:
                    contact = None
            
            if contact and contact.id not in found_contact_ids:
                memory_context = memory_service.get_contact_context(db, contact.id)
                if memory_context.get("has_memory"):
                    memory_contexts.append({
                        "contact": contact.name,
                        "memory": memory_context
                    })
                    found_contact_ids.add(contact.id)
        
        if memory_contexts:
            context = context.copy()
            context["contact_memory"] = memory_contexts
            
            # Add orchestrator suggestions for relevant contacts
            try:
                suggestions = []
                for mem_ctx in memory_contexts:
                    contact_name = mem_ctx.get("contact", "")
                    # Get top suggestions for this contact
                    from src.database.models import Suggestion, Contact
                    contact = db.query(Contact).filter(Contact.name == contact_name).first()
                    if contact:
                        contact_suggestions = db.query(Suggestion).filter(
                            Suggestion.contact_id == contact.id,
                            Suggestion.status == "pending"
                        ).order_by(Suggestion.score.desc()).limit(3).all()
                        
                        for sug in contact_suggestions:
                            suggestions.append({
                                "type": sug.suggestion_type,
                                "intent": sug.intent,
                                "rationale": sug.rationale,
                                "message_draft": sug.message_draft,
                                "best_timing": sug.best_timing
                            })
                
                if suggestions:
                    context["orchestrator_suggestions"] = suggestions
                    logger.info("context_enhanced_with_suggestions", suggestions_count=len(suggestions))
            except Exception as e:
                logger.warning("failed_to_add_suggestions", error=str(e))
            
            logger.info("context_enhanced_with_memory", contexts_count=len(memory_contexts))
        
    except Exception as e:
        logger.error("memory_context_enhancement_failed", error=str(e))
    
    return context


async def _capture_interactions_from_tools(
    db: Session,
    tool_results: List[Dict[str, Any]]
) -> None:
    """
    Capture interactions from tool execution results
    
    Args:
        db: Database session
        tool_results: List of tool execution results
    """
    for result in tool_results:
        tool_name = result.get("tool")
        tool_result = result.get("result", {})
        original_args = result.get("original_arguments", {})
        
        try:
            if tool_name == "send_sms" and tool_result.get("success"):
                await capture_sms_interaction(
                    db=db,
                    to_number=original_args.get("to_number") or tool_result.get("to", ""),
                    message=original_args.get("message", ""),
                    message_sid=tool_result.get("message_sid")
                )
            elif tool_name == "send_email" and tool_result.get("success"):
                await capture_email_interaction(
                    db=db,
                    to_email=original_args.get("to_email") or tool_result.get("to", ""),
                    subject=original_args.get("subject", ""),
                    body=original_args.get("body", "")
                )
            # Note: Call transcripts are handled separately when calls complete
        except Exception as e:
            logger.error("interaction_capture_failed", tool=tool_name, error=str(e))


def _task_to_response(task_record: TaskModel) -> TaskResponse:
    """Convert TaskModel to TaskResponse"""
    return TaskResponse(
        task_id=task_record.task_id,
        status=task_record.status,
        task=task_record.task,
        requires_confirmation=task_record.requires_confirmation,
        planned_tool_calls=task_record.planned_tool_calls,
        policy_reasons=task_record.policy_reasons,
        result=task_record.result,
        error=task_record.error,
        created_at=task_record.created_at.isoformat() if task_record.created_at else datetime.utcnow().isoformat(),
        updated_at=task_record.updated_at.isoformat() if task_record.updated_at else datetime.utcnow().isoformat(),
    )

