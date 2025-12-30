"""
Project Execution Confirmation (PEC) Generator

Generates structured confirmation artifacts that validate project scope, plan,
tool feasibility, constraints, and risks before execution.
"""

from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
import pytz

from src.database.models import (
    Project, ProjectTask, Contact, ProjectStakeholder,
    PreferenceEntry, WorkPreferences, Budget, PricingRule
)
from src.orchestrator.preference_resolver import PreferenceResolver
from src.cost.cost_estimator import CostEstimator
from src.agent.tools import TOOLS, TOOL_HANDLERS
from src.utils.config import get_settings
from src.utils.openai_client import ensure_chat_model, create_openai_client, retry_openai_call
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ExecutionGate(str, Enum):
    """Execution gate states"""
    READY = "READY"  # All tasks feasible, risks acceptable, no unanswered questions
    READY_WITH_QUESTIONS = "READY_WITH_QUESTIONS"  # Tasks feasible but needs user answers/approvals
    BLOCKED = "BLOCKED"  # At least one critical task is blocked


class TaskFeasibility(str, Enum):
    """Task feasibility classification"""
    FULLY_AUTONOMOUS = "FULLY_AUTONOMOUS"  # ✅ Can complete without human intervention
    PARTIAL = "PARTIAL"  # 🟡 Needs user approval or human actions
    BLOCKED = "BLOCKED"  # 🔴 Cannot proceed - requires external access or human provider


class PECGenerator:
    """
    Generates Project Execution Confirmation (PEC) artifacts.
    
    A PEC validates:
    - Project scope and deliverables
    - Task-tool mapping and feasibility
    - Preferences and constraints
    - Risks and gaps
    - Execution readiness
    """
    
    def __init__(self):
        """Initialize PEC generator"""
        self.client = create_openai_client(timeout=60.0, max_retries=3)
        self.model = ensure_chat_model(settings.OPENAI_MODEL)
        self.preference_resolver = PreferenceResolver()
        self.cost_estimator = CostEstimator()
        
        # Available tools/skills registry
        self.available_tools = {
            "make_call": {
                "name": "make_call",
                "category": "telephony",
                "description": "Make outbound phone calls",
                "requires_approval": True,
                "external_dependency": "twilio"
            },
            "send_sms": {
                "name": "send_sms",
                "category": "messaging",
                "description": "Send SMS text messages",
                "requires_approval": True,
                "external_dependency": "twilio"
            },
            "send_email": {
                "name": "send_email",
                "category": "email",
                "description": "Send email messages (Gmail/Outlook/SMTP)",
                "requires_approval": True,
                "external_dependency": "email_provider"
            },
            "read_email": {
                "name": "read_email",
                "category": "email",
                "description": "Read emails from Gmail or Outlook",
                "requires_approval": False,
                "external_dependency": "email_provider"
            },
            "web_research": {
                "name": "web_research",
                "category": "research",
                "description": "Fetch and summarize web content",
                "requires_approval": False,
                "external_dependency": None
            },
            "calendar_create_event": {
                "name": "calendar_create_event",
                "category": "scheduling",
                "description": "Create Google Calendar events",
                "requires_approval": True,
                "external_dependency": "google_calendar"
            },
            "calendar_list_upcoming": {
                "name": "calendar_list_upcoming",
                "category": "scheduling",
                "description": "List upcoming calendar events",
                "requires_approval": False,
                "external_dependency": "google_calendar"
            },
            # AI-only capabilities (no external API)
            "research_summarization": {
                "name": "research_summarization",
                "category": "research",
                "description": "Research topics and summarize findings",
                "requires_approval": False,
                "external_dependency": None
            },
            "drafting_comms": {
                "name": "drafting_comms",
                "category": "drafting",
                "description": "Draft emails, SMS, or other communications",
                "requires_approval": False,
                "external_dependency": None
            },
            "document_generation": {
                "name": "document_generation",
                "category": "drafting",
                "description": "Generate documents, reports, or summaries",
                "requires_approval": False,
                "external_dependency": None
            },
            "crm_memory_recall": {
                "name": "crm_memory_recall",
                "category": "memory",
                "description": "Recall contact history, relationships, and context",
                "requires_approval": False,
                "external_dependency": None
            },
            "strategy_suggestions": {
                "name": "strategy_suggestions",
                "category": "analysis",
                "description": "Suggest strategies based on data",
                "requires_approval": False,
                "external_dependency": None
            },
            "cost_tracking": {
                "name": "cost_tracking",
                "category": "cost",
                "description": "Track and estimate costs",
                "requires_approval": False,
                "external_dependency": None
            },
            "task_management": {
                "name": "task_management",
                "category": "scheduling",
                "description": "Manage tasks and scheduling",
                "requires_approval": False,
                "external_dependency": None
            }
        }
    
    def generate_pec(
        self,
        db: Session,
        project_id: str,
        include_cost_estimate: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a Project Execution Confirmation for a project
        
        Args:
            db: Database session
            project_id: Project ID to generate PEC for
            include_cost_estimate: Whether to include cost estimates
        
        Returns:
            Complete PEC artifact dictionary
        """
        # Fetch project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Fetch tasks
        tasks = db.query(ProjectTask).filter(
            ProjectTask.project_id == project_id
        ).order_by(ProjectTask.created_at).all()
        
        # Fetch stakeholders
        stakeholders = db.query(ProjectStakeholder).filter(
            ProjectStakeholder.project_id == project_id
        ).all()
        
        # Generate each section
        summary = self._generate_summary(project, tasks)
        deliverables = self._extract_deliverables(project, tasks)
        milestones = self._extract_milestones(project, tasks)
        task_plan = self._generate_task_plan(tasks)
        task_tool_map = self._map_tasks_to_tools(db, tasks)
        dependencies_risks = self._analyze_dependencies_and_risks(db, project, tasks, task_tool_map)
        preferences_constraints = self._resolve_preferences_constraints(db, project)
        assumptions = self._generate_assumptions(project, tasks, preferences_constraints)
        gaps = self._detect_gaps(db, project, tasks, task_tool_map)
        
        # Cost estimate (optional)
        cost_estimate = None
        if include_cost_estimate:
            cost_estimate = self._estimate_project_cost(db, tasks, task_tool_map)
        
        # Determine execution gate
        execution_gate, approval_checklist = self._compute_execution_gate(
            task_tool_map, dependencies_risks, gaps, preferences_constraints
        )
        
        # Build PEC
        pec = {
            "pec_id": str(uuid.uuid4()),
            "project_id": project_id,
            "version": 1,
            "created_at": datetime.now(pytz.UTC).isoformat(),
            "summary": summary,
            "deliverables": deliverables,
            "milestones": milestones,
            "task_plan": task_plan,
            "task_tool_map": task_tool_map,
            "dependencies": dependencies_risks.get("dependencies", []),
            "risks": dependencies_risks.get("risks", []),
            "preferences_applied": preferences_constraints.get("preferences", []),
            "constraints_applied": preferences_constraints.get("constraints", []),
            "assumptions": assumptions,
            "gaps": gaps,
            "cost_estimate": cost_estimate,
            "execution_gate": execution_gate.value,
            "approval_checklist": approval_checklist,
            "stakeholders": [
                {
                    "contact_id": sh.contact_id,
                    "role": sh.role,
                    "how_they_help": sh.how_they_help
                }
                for sh in stakeholders
            ]
        }
        
        logger.info("pec_generated", project_id=project_id, gate=execution_gate.value)
        return pec
    
    def _generate_summary(
        self,
        project: Project,
        tasks: List[ProjectTask]
    ) -> Dict[str, Any]:
        """Generate project summary section"""
        total_estimated_time = sum(t.estimated_minutes or 0 for t in tasks)
        
        # Determine definition of success
        success_criteria = []
        if project.milestones:
            for m in project.milestones:
                if isinstance(m, dict) and m.get("title"):
                    success_criteria.append(m.get("title"))
        
        if not success_criteria:
            success_criteria = [f"Complete all {len(tasks)} tasks"]
        
        return {
            "project_id": project.id,
            "title": project.title,
            "description": project.description or "",
            "goal": project.description or project.title,
            "definition_of_success": success_criteria,
            "status": project.status,
            "priority": project.priority,
            "target_due_date": project.target_due_date.isoformat() if project.target_due_date else None,
            "total_tasks": len(tasks),
            "total_estimated_minutes": total_estimated_time,
            "ai_executable_tasks": sum(1 for t in tasks if t.execution_mode in ["AI", "HYBRID"]),
            "human_tasks": sum(1 for t in tasks if t.execution_mode == "HUMAN")
        }
    
    def _extract_deliverables(
        self,
        project: Project,
        tasks: List[ProjectTask]
    ) -> List[Dict[str, Any]]:
        """Extract deliverables from project and tasks"""
        deliverables = []
        
        # Extract from milestones
        if project.milestones:
            for idx, milestone in enumerate(project.milestones):
                if isinstance(milestone, dict):
                    deliverables.append({
                        "id": f"deliverable-{idx}",
                        "title": milestone.get("title", f"Milestone {idx + 1}"),
                        "description": milestone.get("description", ""),
                        "source": "milestone",
                        "due_date": milestone.get("due_date")
                    })
        
        # Extract from task outputs
        for task in tasks:
            if task.execution_mode in ["AI", "HYBRID"]:
                deliverables.append({
                    "id": f"task-output-{task.id}",
                    "title": f"Output: {task.title}",
                    "description": task.description or "",
                    "source": "task",
                    "task_id": task.id
                })
        
        return deliverables
    
    def _extract_milestones(
        self,
        project: Project,
        tasks: List[ProjectTask]
    ) -> List[Dict[str, Any]]:
        """Extract milestones with timeline info"""
        milestones = []
        
        if project.milestones:
            for idx, m in enumerate(project.milestones):
                if isinstance(m, dict):
                    milestones.append({
                        "id": f"milestone-{idx}",
                        "title": m.get("title", f"Milestone {idx + 1}"),
                        "description": m.get("description"),
                        "due_date": m.get("due_date"),
                        "deadline_type": m.get("deadline_type", "FLEX"),
                        "status": m.get("status", "pending")
                    })
        
        # Add synthetic milestone for project completion
        milestones.append({
            "id": "milestone-completion",
            "title": "Project Completion",
            "description": f"All {len(tasks)} tasks completed",
            "due_date": project.target_due_date.isoformat() if project.target_due_date else None,
            "deadline_type": "HARD" if project.constraints and project.constraints.get("hard_deadline") else "FLEX",
            "status": "pending"
        })
        
        return milestones
    
    def _generate_task_plan(
        self,
        tasks: List[ProjectTask]
    ) -> List[Dict[str, Any]]:
        """Generate task plan with estimates"""
        task_plan = []
        
        for task in tasks:
            task_plan.append({
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "estimated_minutes": task.estimated_minutes,
                "execution_mode": task.execution_mode,
                "deadline_type": task.deadline_type or "FLEX",
                "due_at": task.due_at.isoformat() if task.due_at else None,
                "dependencies": task.dependencies or [],
                "tags": task.tags or [],
                "energy_level": task.energy_level
            })
        
        return task_plan
    
    def _map_tasks_to_tools(
        self,
        db: Session,
        tasks: List[ProjectTask]
    ) -> List[Dict[str, Any]]:
        """
        Map each task to tools/skills and determine feasibility
        
        For each task:
        1. Classify task type
        2. Select required tools/skills
        3. Compute feasibility (FULLY_AUTONOMOUS, PARTIAL, BLOCKED)
        4. List required approvals and inputs
        """
        task_tool_map = []
        
        for task in tasks:
            # Use AI to classify task and identify tools
            tool_mapping = self._classify_task_and_tools(task)
            
            # Determine feasibility based on tools
            feasibility, required_approvals, required_inputs, fallback_plan = \
                self._compute_task_feasibility(db, tool_mapping["tools"])
            
            task_tool_map.append({
                "task_id": task.id,
                "task_title": task.title,
                "task_type": tool_mapping["task_type"],
                "tools_required": tool_mapping["tools"],
                "skills_required": tool_mapping["skills"],
                "feasibility": feasibility.value,
                "feasibility_icon": "✅" if feasibility == TaskFeasibility.FULLY_AUTONOMOUS else ("🟡" if feasibility == TaskFeasibility.PARTIAL else "🔴"),
                "required_approvals": required_approvals,
                "required_inputs": required_inputs,
                "fallback_plan": fallback_plan,
                "execution_mode": task.execution_mode
            })
        
        return task_tool_map
    
    def _classify_task_and_tools(
        self,
        task: ProjectTask
    ) -> Dict[str, Any]:
        """Use AI to classify task type and identify required tools"""
        try:
            prompt = f"""Analyze this task and identify required tools/skills:

Task: {task.title}
Description: {task.description or 'No description'}
Execution Mode: {task.execution_mode}

Available tools:
- make_call: Make phone calls (Twilio)
- send_sms: Send SMS messages (Twilio)
- send_email: Send emails (Gmail/Outlook)
- read_email: Read emails
- web_research: Research web content
- calendar_create_event: Create calendar events
- calendar_list_upcoming: List calendar events
- research_summarization: AI research and summarization (no external API)
- drafting_comms: Draft communications (no external API)
- document_generation: Generate documents (no external API)
- crm_memory_recall: Recall contact/relationship data (internal)
- strategy_suggestions: Generate strategy suggestions (internal)
- cost_tracking: Track costs (internal)
- task_management: Manage tasks (internal)

Classify the task and list required tools/skills.

Respond with JSON:
{{
    "task_type": "<research|drafting|scheduling|booking|coordination|communication|other>",
    "tools": ["<tool_name>"],
    "skills": ["<skill description>"],
    "reasoning": "<brief explanation>"
}}"""
            
            @retry_openai_call(max_retries=2, initial_delay=0.5, max_delay=10.0)
            def _call():
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert at analyzing tasks and identifying required tools. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"},
                    timeout=15
                )
            
            response = _call()
            result = json.loads(response.choices[0].message.content)
            
            return {
                "task_type": result.get("task_type", "other"),
                "tools": result.get("tools", []),
                "skills": result.get("skills", []),
                "reasoning": result.get("reasoning", "")
            }
        except Exception as e:
            logger.warning("task_classification_failed", error=str(e), task_id=task.id)
            # Fallback: basic classification based on title keywords
            return self._fallback_classify_task(task)
    
    def _fallback_classify_task(self, task: ProjectTask) -> Dict[str, Any]:
        """Fallback task classification without AI"""
        title_lower = (task.title or "").lower()
        desc_lower = (task.description or "").lower()
        combined = f"{title_lower} {desc_lower}"
        
        tools = []
        skills = []
        task_type = "other"
        
        if any(w in combined for w in ["call", "phone", "dial"]):
            tools.append("make_call")
            task_type = "communication"
        if any(w in combined for w in ["text", "sms", "message"]):
            tools.append("send_sms")
            task_type = "communication"
        if any(w in combined for w in ["email", "mail", "send"]):
            tools.append("send_email")
            task_type = "communication"
        if any(w in combined for w in ["research", "find", "look up", "search"]):
            tools.append("web_research")
            tools.append("research_summarization")
            task_type = "research"
        if any(w in combined for w in ["schedule", "calendar", "meeting", "book"]):
            tools.append("calendar_create_event")
            task_type = "scheduling"
        if any(w in combined for w in ["draft", "write", "compose"]):
            tools.append("drafting_comms")
            task_type = "drafting"
        
        if not tools:
            tools.append("task_management")
            skills.append("General task execution")
        
        return {
            "task_type": task_type,
            "tools": tools,
            "skills": skills,
            "reasoning": "Fallback classification based on keywords"
        }
    
    def _compute_task_feasibility(
        self,
        db: Session,
        tools: List[str]
    ) -> Tuple[TaskFeasibility, List[str], List[str], Optional[str]]:
        """
        Compute feasibility based on required tools
        
        Returns:
            (feasibility, required_approvals, required_inputs, fallback_plan)
        """
        required_approvals = []
        required_inputs = []
        blocked_reasons = []
        
        for tool_name in tools:
            tool_info = self.available_tools.get(tool_name)
            if not tool_info:
                # Unknown tool - blocked
                blocked_reasons.append(f"Unknown tool: {tool_name}")
                continue
            
            # Check if tool requires approval
            if tool_info.get("requires_approval"):
                required_approvals.append(f"Approval required for {tool_info['description']}")
            
            # Check external dependencies
            ext_dep = tool_info.get("external_dependency")
            if ext_dep:
                if ext_dep == "twilio":
                    if not settings.TWILIO_ACCOUNT_SID:
                        blocked_reasons.append("Twilio not configured")
                    else:
                        required_inputs.append("Twilio credentials configured")
                elif ext_dep == "google_calendar":
                    # Check if calendar is connected (would need to check OAuth)
                    required_inputs.append("Google Calendar connection")
                elif ext_dep == "email_provider":
                    required_inputs.append("Email provider (Gmail/Outlook) connection")
        
        # Determine feasibility
        if blocked_reasons:
            return (
                TaskFeasibility.BLOCKED,
                required_approvals,
                required_inputs,
                "Manual execution required: " + "; ".join(blocked_reasons)
            )
        elif required_approvals:
            return (
                TaskFeasibility.PARTIAL,
                required_approvals,
                required_inputs,
                None
            )
        else:
            return (
                TaskFeasibility.FULLY_AUTONOMOUS,
                [],
                required_inputs,
                None
            )
    
    def _analyze_dependencies_and_risks(
        self,
        db: Session,
        project: Project,
        tasks: List[ProjectTask],
        task_tool_map: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze dependencies and identify risks"""
        dependencies = []
        risks = []
        
        # Build task dependency graph
        task_ids = {t.id for t in tasks}
        for task in tasks:
            if task.dependencies:
                for dep_id in task.dependencies:
                    if dep_id in task_ids:
                        dependencies.append({
                            "task_id": task.id,
                            "depends_on": dep_id,
                            "type": "must_complete_first"
                        })
        
        # Identify critical path (tasks with most dependents)
        dependent_count = {}
        for dep in dependencies:
            dep_id = dep["depends_on"]
            dependent_count[dep_id] = dependent_count.get(dep_id, 0) + 1
        
        # Risk analysis
        blocked_tasks = [t for t in task_tool_map if t["feasibility"] == "BLOCKED"]
        if blocked_tasks:
            risks.append({
                "risk_id": "blocked-tasks",
                "severity": "critical",
                "category": "feasibility",
                "description": f"{len(blocked_tasks)} tasks cannot be executed automatically",
                "affected_tasks": [t["task_id"] for t in blocked_tasks],
                "mitigation": "Review blocked tasks and provide missing access/configuration"
            })
        
        # Timeline risk
        if project.target_due_date:
            total_time = sum(t.estimated_minutes or 60 for t in tasks)
            days_available = (project.target_due_date - datetime.now(pytz.UTC)).days
            hours_needed = total_time / 60
            
            if hours_needed > days_available * 6:  # Assuming 6 productive hours/day
                risks.append({
                    "risk_id": "timeline-tight",
                    "severity": "warning",
                    "category": "timeline",
                    "description": f"Estimated {hours_needed:.1f} hours of work, only {days_available} days until deadline",
                    "affected_tasks": [t.id for t in tasks],
                    "mitigation": "Consider prioritizing critical tasks or extending deadline"
                })
        
        # External dependency risks
        external_deps = set()
        for ttm in task_tool_map:
            for tool in ttm["tools_required"]:
                tool_info = self.available_tools.get(tool)
                if tool_info and tool_info.get("external_dependency"):
                    external_deps.add(tool_info["external_dependency"])
        
        if external_deps:
            risks.append({
                "risk_id": "external-dependencies",
                "severity": "info",
                "category": "dependency",
                "description": f"Project requires external services: {', '.join(external_deps)}",
                "affected_tasks": [],
                "mitigation": "Ensure all external services are configured and accessible"
            })
        
        return {
            "dependencies": dependencies,
            "critical_path_tasks": sorted(dependent_count.items(), key=lambda x: -x[1])[:5],
            "risks": risks
        }
    
    def _resolve_preferences_constraints(
        self,
        db: Session,
        project: Project
    ) -> Dict[str, Any]:
        """Resolve preferences and constraints for the project"""
        preferences = []
        constraints = []
        
        # Get work preferences
        work_prefs = db.query(WorkPreferences).first()
        if work_prefs:
            constraints.append({
                "type": "work_hours",
                "description": f"Working hours: {work_prefs.working_hours_start} - {work_prefs.working_hours_end}",
                "source": "work_preferences"
            })
            constraints.append({
                "type": "timezone",
                "description": f"Timezone: {work_prefs.timezone}",
                "source": "work_preferences"
            })
        
        # Get budget constraints
        budget = db.query(Budget).filter(
            Budget.is_active == True,
            Budget.scope == "overall"
        ).first()
        if budget:
            constraints.append({
                "type": "budget",
                "description": f"Budget cap: ${budget.limit:.2f} ({budget.period})",
                "enforcement_mode": budget.enforcement_mode,
                "source": "budget"
            })
        
        # Get project constraints
        if project.constraints:
            for key, value in project.constraints.items():
                constraints.append({
                    "type": key,
                    "description": f"{key}: {value}",
                    "source": "project"
                })
        
        # Get trusted list preferences
        trusted_entries = db.query(PreferenceEntry).filter(
            PreferenceEntry.priority == "PRIMARY"
        ).limit(10).all()
        
        for entry in trusted_entries:
            preferences.append({
                "entry_id": entry.id,
                "type": entry.type,
                "category": entry.category,
                "name": entry.name,
                "priority": entry.priority,
                "source": "trusted_list"
            })
        
        return {
            "preferences": preferences,
            "constraints": constraints
        }
    
    def _generate_assumptions(
        self,
        project: Project,
        tasks: List[ProjectTask],
        preferences_constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate explicit assumptions"""
        assumptions = []
        
        # Time-related assumptions
        avg_task_time = sum(t.estimated_minutes or 60 for t in tasks) / max(len(tasks), 1)
        assumptions.append({
            "assumption_id": "task-duration",
            "category": "scheduling",
            "description": f"Tasks will be scheduled in ~{int(avg_task_time)}-minute blocks unless specified otherwise.",
            "editable": True,
            "impact": "scheduling"
        })
        
        # Approval assumptions
        outbound_tasks = sum(1 for t in tasks if t.execution_mode in ["AI", "HYBRID"])
        if outbound_tasks > 0:
            assumptions.append({
                "assumption_id": "message-approval",
                "category": "approval",
                "description": "Confirmation will be required before sending any outbound messages.",
                "editable": True,
                "impact": "execution_flow"
            })
        
        # Deadline assumptions
        hard_deadline_tasks = sum(1 for t in tasks if t.deadline_type == "HARD")
        if hard_deadline_tasks > 0:
            assumptions.append({
                "assumption_id": "deadline-priority",
                "category": "scheduling",
                "description": f"Hard deadlines ({hard_deadline_tasks} tasks) will be prioritized over flexible ones.",
                "editable": True,
                "impact": "scheduling"
            })
        
        # Budget assumptions
        has_budget = any(c["type"] == "budget" for c in preferences_constraints.get("constraints", []))
        if has_budget:
            assumptions.append({
                "assumption_id": "budget-enforcement",
                "category": "cost",
                "description": "Tasks will be paused if budget limits are approached.",
                "editable": True,
                "impact": "execution_flow"
            })
        
        return assumptions
    
    def _detect_gaps(
        self,
        db: Session,
        project: Project,
        tasks: List[ProjectTask],
        task_tool_map: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect gaps and missing information"""
        gaps = []
        
        # Check for tasks without descriptions
        no_description = [t for t in tasks if not t.description]
        if no_description:
            gaps.append({
                "gap_id": "missing-descriptions",
                "severity": "info",
                "category": "task_clarity",
                "description": f"{len(no_description)} tasks have no description",
                "affected_items": [t.id for t in no_description],
                "recommendation": "Add descriptions for better AI understanding"
            })
        
        # Check for missing time estimates
        no_estimate = [t for t in tasks if not t.estimated_minutes]
        if no_estimate:
            gaps.append({
                "gap_id": "missing-estimates",
                "severity": "warning",
                "category": "scheduling",
                "description": f"{len(no_estimate)} tasks have no time estimate",
                "affected_items": [t.id for t in no_estimate],
                "recommendation": "Add time estimates for accurate scheduling"
            })
        
        # Check for missing pricing rules
        tools_used = set()
        for ttm in task_tool_map:
            tools_used.update(ttm.get("tools_required", []))
        
        if "send_sms" in tools_used or "make_call" in tools_used:
            rule = db.query(PricingRule).filter(
                PricingRule.provider == "twilio"
            ).first()
            if not rule:
                gaps.append({
                    "gap_id": "missing-twilio-pricing",
                    "severity": "warning",
                    "category": "cost",
                    "description": "Twilio pricing rules not configured",
                    "affected_items": [],
                    "recommendation": "Add Twilio pricing rules for accurate cost forecasting"
                })
        
        # Check for contacts with missing info (if coordination tasks exist)
        coordination_tasks = [t for t in task_tool_map if t["task_type"] in ["communication", "coordination"]]
        if coordination_tasks:
            gaps.append({
                "gap_id": "contact-verification",
                "severity": "info",
                "category": "data",
                "description": "Communication tasks detected - verify contact information is up to date",
                "affected_items": [t["task_id"] for t in coordination_tasks],
                "recommendation": "Review contacts involved in communication tasks"
            })
        
        return gaps
    
    def _estimate_project_cost(
        self,
        db: Session,
        tasks: List[ProjectTask],
        task_tool_map: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Estimate total project cost"""
        try:
            total_estimate = 0.0
            breakdown = []
            
            for task, ttm in zip(tasks, task_tool_map):
                if task.execution_mode in ["AI", "HYBRID"]:
                    task_plan = {
                        "task": task.title,
                        "description": task.description
                    }
                    tool_plan = [{"name": t} for t in ttm.get("tools_required", [])]
                    
                    estimate = self.cost_estimator.estimate_task_cost(
                        db, task_plan, tool_plan
                    )
                    
                    if estimate:
                        total_estimate += estimate.get("estimated_total_cost", 0)
                        breakdown.append({
                            "task_id": task.id,
                            "task_title": task.title,
                            "estimated_cost": estimate.get("estimated_total_cost", 0),
                            "confidence": estimate.get("confidence_score", 0.5)
                        })
            
            return {
                "total_estimated_cost": total_estimate,
                "currency": "USD",
                "breakdown": breakdown,
                "confidence": sum(b["confidence"] for b in breakdown) / max(len(breakdown), 1)
            }
        except Exception as e:
            logger.warning("cost_estimation_failed", error=str(e))
            return None
    
    def _compute_execution_gate(
        self,
        task_tool_map: List[Dict[str, Any]],
        dependencies_risks: Dict[str, Any],
        gaps: List[Dict[str, Any]],
        preferences_constraints: Dict[str, Any]
    ) -> Tuple[ExecutionGate, List[Dict[str, Any]]]:
        """
        Compute execution gate status and approval checklist
        
        Returns:
            (gate_status, approval_checklist)
        """
        approval_checklist = []
        has_blocked = False
        has_questions = False
        
        # Check task feasibility
        blocked_count = sum(1 for t in task_tool_map if t["feasibility"] == "BLOCKED")
        partial_count = sum(1 for t in task_tool_map if t["feasibility"] == "PARTIAL")
        
        if blocked_count > 0:
            has_blocked = True
            approval_checklist.append({
                "item": "resolve_blocked_tasks",
                "description": f"Resolve {blocked_count} blocked tasks",
                "status": "required",
                "blocking": True
            })
        
        if partial_count > 0:
            has_questions = True
            approval_checklist.append({
                "item": "approval_policy",
                "description": f"Configure approval policy for {partial_count} tasks requiring approval",
                "status": "pending",
                "blocking": False
            })
        
        # Check for critical risks
        critical_risks = [r for r in dependencies_risks.get("risks", []) if r["severity"] == "critical"]
        if critical_risks:
            has_blocked = True
            approval_checklist.append({
                "item": "address_critical_risks",
                "description": f"Address {len(critical_risks)} critical risks",
                "status": "required",
                "blocking": True
            })
        
        # Standard checklist items
        approval_checklist.extend([
            {
                "item": "confirm_scope",
                "description": "Confirm scope and deliverables",
                "status": "pending",
                "blocking": False
            },
            {
                "item": "confirm_timeline",
                "description": "Confirm timeline and deadlines",
                "status": "pending",
                "blocking": False
            },
            {
                "item": "confirm_budget",
                "description": "Confirm budget/cost guardrails",
                "status": "pending",
                "blocking": False
            },
            {
                "item": "confirm_tools",
                "description": "Confirm tools and access",
                "status": "pending",
                "blocking": False
            },
            {
                "item": "confirm_messaging",
                "description": "Confirm outbound messaging approval policy",
                "status": "pending",
                "blocking": False
            }
        ])
        
        # Determine gate status
        if has_blocked:
            return (ExecutionGate.BLOCKED, approval_checklist)
        elif has_questions:
            return (ExecutionGate.READY_WITH_QUESTIONS, approval_checklist)
        else:
            return (ExecutionGate.READY, approval_checklist)
    
    def regenerate_pec(
        self,
        db: Session,
        project_id: str,
        previous_pec_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Regenerate PEC after changes (increments version)
        
        Args:
            db: Database session
            project_id: Project ID
            previous_pec_id: Previous PEC ID for version tracking
        
        Returns:
            New PEC with incremented version
        """
        pec = self.generate_pec(db, project_id)
        
        # If we have a previous PEC, increment version
        if previous_pec_id:
            pec["previous_pec_id"] = previous_pec_id
            # Version would come from stored PEC - for now just use 1
        
        pec["regenerated_at"] = datetime.now(pytz.UTC).isoformat()
        
        return pec

