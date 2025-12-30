"""AI task execution service - executes tasks using available tools"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import json
import asyncio
import pytz

from src.database.models import ProjectTask, AIExecution
from src.agent.tools import TOOLS, TOOL_HANDLERS
from src.utils.config import get_settings
from src.utils.openai_client import ensure_chat_model, create_openai_client, retry_openai_call
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class AIExecutor:
    """Executes AI-executable tasks using available tools"""
    
    def __init__(self):
        """Initialize executor"""
        self.client = create_openai_client(timeout=60.0, max_retries=3)
        self.model = ensure_chat_model(settings.OPENAI_MODEL)
    
    async def execute_task(
        self,
        db: Session,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Execute an AI-executable task
        
        Args:
            db: Database session
            task_id: Task ID to execute
        
        Returns:
            Dictionary with execution results
        """
        task = db.query(ProjectTask).filter(ProjectTask.id == task_id).first()
        if not task:
            return {"success": False, "error": "Task not found"}
        
        if task.execution_mode not in ["AI", "HYBRID"]:
            return {"success": False, "error": "Task is not AI-executable"}
        
        if task.status == "done":
            return {"success": False, "error": "Task already completed"}
        
        # Create execution record
        execution = AIExecution(
            task_id=task.id,
            status="running"
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        try:
            # Generate execution plan
            plan = await self._generate_execution_plan(task)
            execution.execution_plan = plan
            db.commit()
            
            # Execute plan
            results = await self._execute_plan(task, plan)
            
            # Update execution record
            execution.status = "completed"
            execution.outputs = results.get("outputs", {})
            execution.tool_calls = results.get("tool_calls", [])
            execution.required_approvals = results.get("required_approvals", [])
            execution.summary = results.get("summary", "")
            execution.completed_at = datetime.now(pytz.UTC)
            
            # Update task status
            if execution.required_approvals:
                task.status = "scheduled"  # Waiting for approval
                execution.status = "approved"  # Needs approval
            else:
                task.status = "done"
            
            db.commit()
            
            return {
                "success": True,
                "execution_id": execution.id,
                "outputs": execution.outputs,
                "required_approvals": execution.required_approvals,
                "summary": execution.summary
            }
        except Exception as e:
            logger.error("ai_execution_failed", error=str(e), task_id=task_id)
            execution.status = "failed"
            execution.error = str(e)
            db.commit()
            return {"success": False, "error": str(e)}
    
    async def _generate_execution_plan(
        self,
        task: ProjectTask
    ) -> Dict[str, Any]:
        """Generate execution plan for task"""
        prompt = f"""Generate an execution plan for this task:

Task: {task.title}
Description: {task.description or 'No description'}

Break down the task into steps and identify which tools are needed.
Available tools:
- make_call: Make phone calls
- send_sms: Send SMS messages
- send_email: Send emails
- web_research: Research topics on the web
- calendar_create_event: Create calendar events
- calendar_list_upcoming: List upcoming events

For each step, specify:
- Step description
- Tool to use (if any)
- Tool parameters
- Expected output

If the task requires sending messages or making calls, mark those steps as requiring approval.

Respond with JSON:
{{
    "steps": [
        {{
            "description": "<step description>",
            "tool": "<tool name or null>",
            "tool_parameters": {{}},
            "requires_approval": <true|false>,
            "expected_output": "<what this step produces>"
        }}
    ]
}}"""
        
        @retry_openai_call(max_retries=3, initial_delay=0.5, max_delay=15.0)
        def _call():
            return self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert task executor. Break down tasks into actionable steps using available tools. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
                timeout=20,
            )
        
        response = _call()
        
        return json.loads(response.choices[0].message.content)
    
    async def _execute_plan(
        self,
        task: ProjectTask,
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the plan steps"""
        outputs = {}
        tool_calls = []
        required_approvals = []
        
        for step in plan.get("steps", []):
            step_desc = step.get("description", "")
            tool_name = step.get("tool")
            
            if tool_name and tool_name in TOOL_HANDLERS:
                # Execute tool
                tool_params = step.get("tool_parameters", {})
                try:
                    handler = TOOL_HANDLERS[tool_name]
                    result = await handler(**tool_params)
                    
                    tool_calls.append({
                        "step": step_desc,
                        "tool": tool_name,
                        "parameters": tool_params,
                        "result": result
                    })
                    
                    outputs[step_desc] = result
                    
                    # Check if approval needed
                    if step.get("requires_approval"):
                        required_approvals.append({
                            "step": step_desc,
                            "tool": tool_name,
                            "result": result
                        })
                except Exception as e:
                    logger.error("tool_execution_failed", error=str(e), tool=tool_name, step=step_desc)
                    outputs[step_desc] = {"error": str(e)}
            else:
                # No tool needed, just record step
                outputs[step_desc] = {"status": "completed"}
        
        # Generate summary
        summary = f"Completed {len(plan.get('steps', []))} steps for task '{task.title}'"
        if required_approvals:
            summary += f". {len(required_approvals)} actions require approval."
        
        return {
            "outputs": outputs,
            "tool_calls": tool_calls,
            "required_approvals": required_approvals,
            "summary": summary
        }

