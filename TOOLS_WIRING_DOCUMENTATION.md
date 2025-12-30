# Tools & Skills Wiring Documentation

**Last Updated**: 2025-01-29  
**Status**: ✅ All tools properly wired and connected

## Overview

This document verifies that all AI assistant tools are properly defined, wired, and connected to their handlers. It ensures the complete flow from OpenAI function calling to tool execution.

## Tool Inventory

### Total Tools: 8

1. **make_call** - Make phone calls
2. **send_sms** - Send text messages
3. **send_email** - Send emails (Gmail/Outlook/SMTP)
4. **read_email** - Read emails from Gmail/Outlook
5. **list_emails** - List/search emails
6. **web_research** - Research allowlisted URLs
7. **calendar_create_event** - Create Google Calendar events
8. **calendar_list_upcoming** - List upcoming calendar events

## Wiring Verification

### ✅ Tool Definitions → Handlers Mapping

| Tool Name | Handler Function | Status |
|-----------|-----------------|--------|
| `make_call` | `make_call()` | ✅ Wired |
| `send_sms` | `send_sms()` | ✅ Wired |
| `send_email` | `send_email()` | ✅ Wired |
| `read_email` | `read_email()` | ✅ Wired |
| `list_emails` | `list_emails()` | ✅ Wired |
| `web_research` | `web_research_tool()` | ✅ Wired |
| `calendar_create_event` | `calendar_create_event()` | ✅ Wired |
| `calendar_list_upcoming` | `calendar_list_upcoming()` | ✅ Wired |

**Verification**: All 8 tools in `TOOLS` array have corresponding handlers in `TOOL_HANDLERS` dictionary.

### ✅ Handler Functions → Tool Definitions

All handlers in `TOOL_HANDLERS` have corresponding tool definitions in `TOOLS` array.

**No orphaned handlers found.**

## Tool Execution Flow

### 1. Planning Phase (`plan_task`)

**File**: `src/agent/assistant.py`

```python
# OpenAI receives tools and user request
response = client.chat.completions.create(
    model=self.model,
    messages=messages,
    tools=TOOLS,  # ← All tools available
    tool_choice="auto",
)

# Extract planned tool calls
if message.tool_calls:
    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        planned.append(PlannedToolCall(name=function_name, arguments=function_args))
```

**Flow**:
1. ✅ `TOOLS` array passed to OpenAI
2. ✅ OpenAI selects appropriate tools
3. ✅ Tool calls extracted and stored
4. ✅ Returned in `planned_tool_calls`

### 2. Policy Check (`decide_confirmation`)

**File**: `src/security/policy.py`

```python
# Check if tools require confirmation
policy = decide_confirmation(actor, planned_calls)

# High-risk tools require confirmation:
# - make_call
# - send_sms
# - send_email
# - calendar_create_event
```

**Flow**:
1. ✅ Tools classified by risk level
2. ✅ High-risk tools flagged for confirmation
3. ✅ Low-risk tools (web_research) can execute immediately

### 3. Execution Phase (`execute_planned_tools`)

**File**: `src/agent/assistant.py`

```python
async def execute_planned_tools(self, planned_tool_calls: List[Dict[str, Any]]):
    for c in planned_tool_calls:
        name = c.get("name")
        args = c.get("arguments") or {}
        
        if name not in TOOL_HANDLERS:
            # Error: tool not found
            continue
        
        # Execute tool
        tool_result = await TOOL_HANDLERS[name](**args)
        results.append({"tool": name, "result": tool_result})
```

**Flow**:
1. ✅ Iterate through planned tool calls
2. ✅ Look up handler in `TOOL_HANDLERS`
3. ✅ Execute handler with arguments
4. ✅ Collect results

### 4. API Integration (`/tasks` endpoint)

**File**: `src/api/routes/tasks.py`

```python
# Create task
plan = assistant.plan_task(task, context)
planned_tool_calls = plan.get("planned_tool_calls") or []

# Check policy
policy = decide_confirmation(actor, planned_calls)

# Execute if no confirmation needed
if not policy.requires_confirmation:
    tool_results = await assistant.execute_planned_tools(planned_tool_calls)
```

**Flow**:
1. ✅ Task created with plan
2. ✅ Policy check determines if confirmation needed
3. ✅ Tools executed if approved
4. ✅ Results stored in task record

## Tool Schema Verification

### ✅ All Tools Have Valid Schemas

Each tool follows OpenAI function calling format:

```json
{
  "type": "function",
  "function": {
    "name": "tool_name",
    "description": "Clear description of what the tool does",
    "parameters": {
      "type": "object",
      "properties": {
        "param_name": {
          "type": "string",
          "description": "Parameter description"
        }
      },
      "required": ["param_name"]
    }
  }
}
```

### Schema Validation

All tools validated using `validate_tool_schema()`:
- ✅ Proper structure
- ✅ Required fields present
- ✅ Parameter types defined
- ✅ Descriptions provided

## Tool Capabilities

### Communication Tools

#### 1. `make_call`
- **Purpose**: Initiate phone calls
- **Risk**: HIGH (requires confirmation)
- **Parameters**: `to_number` (required), `message` (optional), `from_number` (optional)
- **Handler**: `make_call()` in `src/agent/tools.py`
- **Integration**: Twilio telephony service

#### 2. `send_sms`
- **Purpose**: Send text messages
- **Risk**: HIGH (requires confirmation)
- **Parameters**: `to_number` (required), `message` (required), `from_number` (optional)
- **Handler**: `send_sms()` in `src/agent/tools.py`
- **Integration**: Twilio SMS service

#### 3. `send_email`
- **Purpose**: Send emails via multiple providers
- **Risk**: HIGH (requires confirmation)
- **Parameters**: `to_email` (required), `subject` (required), `body` (required), `from_email` (optional), `provider` (optional), `cc` (optional), `bcc` (optional)
- **Handler**: `send_email()` in `src/agent/tools.py`
- **Integration**: Gmail → Outlook → SMTP fallback

#### 4. `read_email`
- **Purpose**: Read specific email or search emails
- **Risk**: LOW (read-only)
- **Parameters**: `provider` (required), `message_id` (optional), `query` (optional), `limit` (optional)
- **Handler**: `read_email()` in `src/agent/tools.py`
- **Integration**: Gmail API or Outlook/Microsoft Graph API

#### 5. `list_emails`
- **Purpose**: List/search emails (convenience wrapper)
- **Risk**: LOW (read-only)
- **Parameters**: `provider` (required), `query` (optional), `limit` (optional)
- **Handler**: `list_emails()` in `src/agent/tools.py`
- **Integration**: Calls `read_email()` internally

### Research Tools

#### 6. `web_research`
- **Purpose**: Fetch and extract text from allowlisted URLs
- **Risk**: LOW (read-only, allowlisted)
- **Parameters**: `url` (required), `allow_hosts_csv` (optional)
- **Handler**: `web_research_tool()` in `src/agent/tools.py`
- **Integration**: Custom web scraping with allowlist

### Calendar Tools

#### 7. `calendar_create_event`
- **Purpose**: Create Google Calendar events
- **Risk**: HIGH (requires confirmation)
- **Parameters**: `summary` (required), `start_iso` (required), `end_iso` (required), `description` (optional), `location` (optional), `attendees_emails` (optional), `timezone` (optional), `add_google_meet` (optional)
- **Handler**: `calendar_create_event()` in `src/agent/tools.py`
- **Integration**: Google Calendar API

#### 8. `calendar_list_upcoming`
- **Purpose**: List upcoming calendar events
- **Risk**: LOW (read-only)
- **Parameters**: `limit` (optional, default: 10)
- **Handler**: `calendar_list_upcoming()` in `src/agent/tools.py`
- **Integration**: Google Calendar API

## Integration Points

### ✅ OpenAI Function Calling
- **Location**: `src/agent/assistant.py` → `plan_task()`
- **Status**: All tools passed to OpenAI
- **Verification**: Tools validated on initialization

### ✅ Tool Execution
- **Location**: `src/agent/assistant.py` → `execute_planned_tools()`
- **Status**: All handlers mapped correctly
- **Verification**: Handler lookup verified

### ✅ Policy Enforcement
- **Location**: `src/security/policy.py` → `decide_confirmation()`
- **Status**: All tools classified by risk
- **Verification**: High-risk tools require confirmation

### ✅ API Endpoints
- **Location**: `src/api/routes/tasks.py`
- **Status**: Tools integrated into task workflow
- **Verification**: Execution flow complete

### ✅ Memory System
- **Location**: `src/api/routes/tasks.py` → `_capture_interactions_from_tools()`
- **Status**: Tool results captured for memory
- **Verification**: Interactions logged

## Error Handling

### ✅ Tool Not Found
```python
if name not in TOOL_HANDLERS:
    results.append({"tool": name, "error": f"Unknown tool: {name}"})
```

### ✅ Tool Execution Errors
```python
try:
    tool_result = await TOOL_HANDLERS[name](**args)
except Exception as e:
    results.append({"tool": name, "error": str(e)})
```

### ✅ Parameter Validation
- Each tool handler validates its own parameters
- Invalid parameters raise `TaskError`
- Errors logged and returned in results

## Testing

### Verification Script

Run the tool wiring verification:

```bash
python scripts/verify_tool_wiring.py
```

**Checks**:
- ✅ All tools have handlers
- ✅ All handlers have tools
- ✅ Tool schemas match function signatures
- ✅ Required parameters match
- ✅ Tool descriptions present
- ✅ Schema validation passes

## Best Practices

### ✅ Tool Design
1. Clear, descriptive tool names
2. Detailed parameter descriptions
3. Proper required/optional field specification
4. Type validation in handlers

### ✅ Handler Implementation
1. Async functions for I/O operations
2. Parameter validation
3. Error handling with `TaskError`
4. Structured return values
5. Logging of operations

### ✅ Integration
1. Tools registered in `TOOLS` array
2. Handlers mapped in `TOOL_HANDLERS`
3. Policy classification in `tool_risk()`
4. Execution flow in `execute_planned_tools()`

## Future Enhancements

### Potential New Tools
- `update_calendar_event` - Update existing events
- `cancel_calendar_event` - Cancel events
- `search_contacts` - Search contact database
- `create_note` - Create notes/memos
- `set_reminder` - Set reminders

### Improvements
- Parallel tool execution for independent tools
- Tool result caching
- Tool usage analytics
- Tool performance monitoring

## Summary

✅ **All 8 tools properly wired and connected**

- **Tool Definitions**: 8 tools in `TOOLS` array
- **Tool Handlers**: 8 handlers in `TOOL_HANDLERS` dictionary
- **Wiring**: 100% match between tools and handlers
- **Schemas**: All validated and correct
- **Execution Flow**: Complete from planning to execution
- **Integration**: Properly integrated with API, policy, and memory systems

**Status**: Production ready ✅

---

**Verification Date**: 2025-01-29  
**Verified By**: Automated tool wiring verification script

