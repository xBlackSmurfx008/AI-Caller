"""AI Assistant (planner/executor) using OpenAI function calling."""

from typing import Dict, Any, Optional, List, Tuple
import json

from openai import OpenAI, RateLimitError, APIConnectionError, APIError, APITimeoutError
from src.utils.config import get_settings
from src.utils.logging import get_logger
from src.utils.errors import OpenAIError
from src.utils.openai_client import (
    create_openai_client,
    ensure_chat_model,
    retry_openai_call,
    validate_tools,
    get_openai_error_message
)
from src.agent.tools import TOOLS, TOOL_HANDLERS
from src.security.policy import PlannedToolCall
from src.orchestrator.orchestrator_service import OrchestratorService

logger = get_logger(__name__)
settings = get_settings()


class VoiceAssistant:
    """Voice-to-voice AI assistant (plans tool calls, then executes when approved)."""
    
    def __init__(self, client: Optional[OpenAI] = None, model: Optional[str] = None):
        """Initialize the assistant"""
        # Use best practices client with timeout and retry configuration
        self.client = client or create_openai_client(timeout=60.0, max_retries=3)
        self.model = ensure_chat_model(model or settings.OPENAI_MODEL)
        self.orchestrator = OrchestratorService()
        
        # Validate tools on initialization
        is_valid, error_msg = validate_tools(TOOLS)
        if not is_valid:
            logger.error("invalid_tool_schemas", error=error_msg)
            raise ValueError(f"Invalid tool schemas: {error_msg}")
        self.instructions = """You are a helpful AI assistant that can help users by:
1. Making phone calls to contacts
2. Sending text messages (SMS)
3. Sending emails (via Gmail, Outlook, or SMTP)
4. Reading and searching emails (from Gmail or Outlook)
5. Managing calendar events

When a user gives you a task, break it down into steps and use the available tools to complete it.
Be proactive and helpful. If you need clarification, ask the user.
Execute actions directly when instructed - do not ask for confirmation, just do it.

TOOL-CALLING REQUIREMENTS (CRITICAL):
- If you call a tool, you MUST provide VALID JSON for tool arguments (an object/dict).
- Do NOT include trailing commas or comments in JSON.
- Only call tools when necessary; otherwise respond with guidance/questions.

EMAIL CAPABILITIES:
- You can send emails using send_email tool - it automatically tries Gmail first, then Outlook, then SMTP
- You can read emails using read_email tool - specify 'gmail' or 'outlook' as the provider
- You can list/search emails using list_emails tool - supports Gmail search syntax or Outlook OData filters
- When reading emails, you can get a specific message by ID or search/list multiple messages
- Always check which email provider is connected before attempting to read emails

IMPORTANT: If context includes contact_memory, use it to:
- Align your messaging with the contact's preferences and relationship status
- Reference relevant past interactions and commitments
- Consider active Godfather goals for that contact
- Match the sentiment and tone of the relationship
- Follow up on outstanding actions when appropriate

If context includes orchestrator_suggestions or project_context, use them to:
- Identify win-win opportunities
- Suggest value-first actions (give before asking)
- Connect contacts to relevant projects when beneficial to both
- Maintain reciprocity balance in relationships"""
    
    def _parse_tool_arguments(self, tool_name: str, raw_arguments: str) -> Dict[str, Any]:
        """Parse OpenAI tool arguments safely and enforce dict/object shape."""
        try:
            parsed = json.loads(raw_arguments or "{}")
        except json.JSONDecodeError as e:
            raise OpenAIError(
                f"Model returned invalid JSON arguments for tool '{tool_name}'."
            ) from e
        if not isinstance(parsed, dict):
            raise OpenAIError(
                f"Model returned non-object arguments for tool '{tool_name}' (expected JSON object)."
            )
        return parsed
    
    def _extract_from_responses(self, resp: Any) -> tuple[str, List[PlannedToolCall]]:
        """
        Extract assistant text + tool calls from OpenAI Responses API output (best-effort).
        Supports common shapes:
        - response.output: list of items (message + tool/function calls)
        - tool calls as items with type in {"function_call","tool_call"} containing name + arguments/parameters
        """
        assistant_text = ""
        planned: List[PlannedToolCall] = []

        output = getattr(resp, "output", None)
        if not isinstance(output, list):
            # Fallback: if SDK returns dict-like
            if isinstance(resp, dict):
                output = resp.get("output")
        if not isinstance(output, list):
            return assistant_text, planned

        for item in output:
            if isinstance(item, dict):
                item_type = item.get("type")
                if item_type == "message" and item.get("role") == "assistant":
                    content = item.get("content") or []
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("type") in {"output_text", "text"}:
                                assistant_text = c.get("text") or assistant_text
                                break
                if item_type in {"function_call", "tool_call"}:
                    name = item.get("name")
                    args = item.get("arguments")
                    if args is None:
                        args = item.get("parameters")
                    if isinstance(args, str):
                        parsed_args = self._parse_tool_arguments(name or "unknown", args)
                    elif isinstance(args, dict):
                        parsed_args = args
                    else:
                        parsed_args = {}
                    if name:
                        planned.append(PlannedToolCall(name=name, arguments=parsed_args))
                continue

            # Typed SDK objects (best-effort)
            item_type = getattr(item, "type", None)
            if item_type == "message" and getattr(item, "role", None) == "assistant":
                content = getattr(item, "content", None)
                if isinstance(content, list):
                    for c in content:
                        ct = getattr(c, "type", None)
                        if ct in {"output_text", "text"}:
                            assistant_text = getattr(c, "text", "") or assistant_text
                            break
            if item_type in {"function_call", "tool_call"}:
                name = getattr(item, "name", None)
                args = getattr(item, "arguments", None) or getattr(item, "parameters", None)
                if isinstance(args, str):
                    parsed_args = self._parse_tool_arguments(name or "unknown", args)
                elif isinstance(args, dict):
                    parsed_args = args
                else:
                    parsed_args = {}
                if name:
                    planned.append(PlannedToolCall(name=name, arguments=parsed_args))

        return assistant_text, planned
        
    def plan_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Plan a task: produce a natural language response plus zero or more tool calls.
        
        Args:
            task: The task description from the user
            context: Optional context or conversation history
        
        Returns:
            Dictionary with plan details (no side effects)
        """
        try:
            logger.info("planning_task", task=task)
            
            # Prepare messages
            messages = [
                {"role": "system", "content": self.instructions}
            ]
            
            # Add memory context if available
            if context and "contact_memory" in context:
                memory_info = []
                for mem in context["contact_memory"]:
                    contact_name = mem.get("contact", "Contact")
                    memory = mem.get("memory", {})
                    mem_text = f"Memory for {contact_name}:\n"
                    if memory.get("latest_summary"):
                        mem_text += f"- Latest: {memory['latest_summary']}\n"
                    if memory.get("sentiment_trend"):
                        mem_text += f"- Sentiment: {memory['sentiment_trend']}\n"
                    if memory.get("active_goals"):
                        mem_text += f"- Active goals: {', '.join(memory['active_goals'])}\n"
                    if memory.get("outstanding_actions"):
                        mem_text += f"- Outstanding actions: {', '.join(memory['outstanding_actions'][:3])}\n"
                    if memory.get("key_preferences"):
                        mem_text += f"- Preferences: {', '.join(memory['key_preferences'])}\n"
                    if memory.get("relationship_status"):
                        mem_text += f"- Relationship: {memory['relationship_status']}\n"
                    memory_info.append(mem_text)
                
                if memory_info:
                    messages.append({
                        "role": "system",
                        "content": "CONTACT MEMORY CONTEXT:\n\n" + "\n\n".join(memory_info)
                    })
            
            if context and "history" in context:
                messages.extend(context["history"])
            
            messages.append({"role": "user", "content": task})
            
            use_responses = bool(getattr(settings, "OPENAI_USE_RESPONSES", False)) and hasattr(self.client, "responses")

            @retry_openai_call(max_retries=3, initial_delay=1.0)
            def _create_completion():
                if use_responses:
                    return self.client.responses.create(
                        model=self.model,
                        input=messages,
                        tools=TOOLS,
                        tool_choice="auto",
                        temperature=0.2,
                    )
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    # Lower temperature improves tool-call determinism and reduces malformed JSON.
                    temperature=0.2,
                    timeout=60.0,  # Explicit timeout
                )
            
            try:
                response = _create_completion()
            except (RateLimitError, APIConnectionError, APITimeoutError, APIError) as e:
                error_msg = get_openai_error_message(e)
                logger.error("openai_api_call_failed", error=str(e), error_type=type(e).__name__)
                raise OpenAIError(f"OpenAI API call failed: {error_msg}") from e
            
            # Store response for cost logging (will be logged in routes if db available)
            # The response object contains usage information that can be logged
            
            planned: List[PlannedToolCall] = []
            assistant_message = "Task completed."

            if use_responses:
                assistant_message, planned = self._extract_from_responses(response)
                assistant_message = assistant_message or "Task completed."
            else:
                message = response.choices[0].message

                # Handle function calls
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = self._parse_tool_arguments(function_name, tool_call.function.arguments)

                        logger.info(
                            "planned_tool",
                            tool_name=function_name,
                            arguments=function_args
                        )

                        planned.append(PlannedToolCall(name=function_name, arguments=function_args))

                # Get assistant's response
                assistant_message = message.content or "Task completed."
            
            return {
                "success": True,
                "response": assistant_message,
                "planned_tool_calls": [{"name": c.name, "arguments": c.arguments} for c in planned],
                "task": task,
                "_openai_response": response  # Include response for cost logging
            }
            
        except Exception as e:
            logger.error("task_planning_error", error=str(e), task=task)
            raise OpenAIError(f"Failed to plan task: {str(e)}") from e

    async def execute_planned_tools(self, planned_tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a list of planned tool calls in parallel (side effects)."""
        import asyncio
        
        async def execute_single_tool(c: Dict[str, Any]) -> Dict[str, Any]:
            name = c.get("name")
            args = c.get("arguments") or {}
            if name not in TOOL_HANDLERS:
                return {"tool": name, "error": f"Unknown tool: {name}"}
            logger.info("executing_tool", tool_name=name, arguments=args)
            try:
                tool_result = await TOOL_HANDLERS[name](**args)
                return {
                    "tool": name,
                    "result": tool_result,
                    "original_arguments": args
                }
            except Exception as e:
                return {"tool": name, "error": str(e), "original_arguments": args}
        
        # Execute all tools in parallel for faster completion
        results = await asyncio.gather(
            *[execute_single_tool(c) for c in planned_tool_calls],
            return_exceptions=False
        )
        return list(results)
    
    async def handle_voice_conversation(
        self,
        audio_input: bytes,
        session_id: str
    ) -> bytes:
        """
        Handle voice-to-voice conversation.
        
        Args:
            audio_input: PCM16 audio data from user
            session_id: Session identifier
        
        Returns:
            PCM16 audio data for response
        """
        # TODO: Implement using OpenAI Realtime API
        # This will bridge Twilio Media Streams with OpenAI Realtime API
        raise NotImplementedError("Voice conversation not yet implemented")

