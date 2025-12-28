# AgentKit Voice Integration Guide

Complete guide to integrating OpenAI AgentKit's voice abilities/tools into the AI Caller system.

## Overview

This document explains how OpenAI AgentKit's abilities/tools work with voice products and how to integrate them into the AI Caller system. It consolidates both the comprehensive guide and integration summary.

## What Has Been Implemented

### 1. **Comprehensive Documentation**
   - Explained AgentKit's two voice architectures (Speech-to-Speech and Chained)
   - Documented how abilities/tools work with voice products
   - Provided examples of voice agent abilities
   - Included best practices and integration steps

### 2. **Tool Handlers Implementation** (`src/ai/tool_handlers.py`)
   - Created `ToolHandlers` class to execute agent abilities
   - Implemented 7 example tools:
     - `lookup_customer` - Find customer information
     - `schedule_appointment` - Book appointments
     - `escalate_to_human` - Escalate calls
     - `search_knowledge_base` - RAG search
     - `check_order_status` - Order tracking
     - `create_support_ticket` - Ticket creation
     - `get_business_hours` - Business hours info
   - Created tool definition functions for different business types:
     - `get_customer_support_tools()`
     - `get_sales_tools()`
     - `get_appointment_tools()`

### 3. **Enhanced OpenAI Client** (`src/ai/openai_client.py`)
   - Added tool handler integration
   - Implemented function call event handling:
     - `response.function_call_arguments.delta` - Accumulates arguments
     - `response.function_call.done` - Executes tool and returns result
   - Automatic tool result submission back to OpenAI

## AgentKit Voice Architecture

### Two Main Architectures:

1. **Speech-to-Speech (Realtime) Architecture**
   - Uses `gpt-4o-realtime-preview` model
   - Processes audio inputs/outputs directly
   - Low-latency, natural conversational interactions
   - Best for: Language tutoring, interactive customer service

2. **Chained Architecture**
   - Audio → Text → LLM Processing → Text → Audio
   - High control and transparency
   - Best for: Structured workflows, customer support, sales

## AgentKit Abilities/Tools for Voice

### What are Abilities?

Abilities (also called "tools" or "functions") allow voice agents to:
- **Perform actions** during conversations (e.g., look up customer data, schedule appointments)
- **Access external systems** (databases, APIs, services)
- **Make decisions** based on real-time data
- **Execute workflows** (escalate calls, create tickets, send notifications)

### Key Features:

1. **Structured Multi-Modal Input Processing**
   - Handle transcribed speech as input
   - Process various input types (text, audio, structured data)
   - Seamless integration of speech-to-text into reasoning workflow

2. **Real-Time Decision Streaming**
   - Stream token output from language models
   - Incremental speech synthesis
   - Begin responding before fully formulating thoughts
   - Reduced latency

3. **Robust Context Handling**
   - Maintain conversational context across sessions
   - Consistent responses in recurring interactions
   - Memory of previous conversations

4. **Built-in Guardrails and Monitoring**
   - Prevent unsafe or irrelevant speech outputs
   - Evaluation tools for response accuracy, tone, compliance
   - Reliable and safe agent behavior

## Current Implementation

The system already supports tools in `src/ai/openai_client.py`:

```python
async def create_session(
    self,
    session_id: str,
    tools: Optional[List[Dict[str, Any]]] = None,  # Tools/abilities support
    ...
):
```

## Example Voice Agent Abilities

### 1. Customer Lookup Ability
```python
customer_lookup_tool = {
    "type": "function",
    "function": {
        "name": "lookup_customer",
        "description": "Look up customer information by phone number or email",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Customer phone number"
                },
                "email": {
                    "type": "string",
                    "description": "Customer email address"
                }
            }
        }
    }
}
```

### 2. Appointment Scheduling Ability
```python
schedule_appointment_tool = {
    "type": "function",
    "function": {
        "name": "schedule_appointment",
        "description": "Schedule an appointment for the customer",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Appointment date in YYYY-MM-DD format"
                },
                "time": {
                    "type": "string",
                    "description": "Appointment time in HH:MM format"
                },
                "service_type": {
                    "type": "string",
                    "description": "Type of service requested"
                }
            },
            "required": ["date", "time", "service_type"]
        }
    }
}
```

### 3. Escalation Ability
```python
escalate_call_tool = {
    "type": "function",
    "function": {
        "name": "escalate_to_human",
        "description": "Escalate the call to a human agent",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Reason for escalation",
                    "enum": ["complex_issue", "customer_request", "technical_problem"]
                },
                "priority": {
                    "type": "string",
                    "description": "Escalation priority",
                    "enum": ["low", "medium", "high", "urgent"]
                }
            },
            "required": ["reason"]
        }
    }
}
```

### 4. Knowledge Base Search Ability
```python
search_knowledge_tool = {
    "type": "function",
    "function": {
        "name": "search_knowledge_base",
        "description": "Search the knowledge base for information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "category": {
                    "type": "string",
                    "description": "Category to search in"
                }
            },
            "required": ["query"]
        }
    }
}
```

### 5. Order Status Check Ability
```python
check_order_status_tool = {
    "type": "function",
    "function": {
        "name": "check_order_status",
        "description": "Check the status of a customer order",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID or tracking number"
                }
            },
            "required": ["order_id"]
        }
    }
}
```

## Integration Steps

### Step 1: Define Tool Handlers

The tool handler module (`src/ai/tool_handlers.py`) has been created:

```python
"""Tool handlers for voice agent abilities"""

from typing import Dict, Any, Optional
from src.database.database import get_db
from src.knowledge.rag_pipeline import RAGPipeline
from src.escalation.escalation_manager import EscalationManager

class ToolHandlers:
    """Handlers for agent tools/abilities"""
    
    def __init__(self):
        self.rag = RAGPipeline()
        self.escalation_manager = EscalationManager()
    
    async def handle_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        call_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle tool calls from voice agent"""
        
        if tool_name == "lookup_customer":
            return await self.lookup_customer(arguments)
        elif tool_name == "schedule_appointment":
            return await self.schedule_appointment(arguments, call_id)
        elif tool_name == "escalate_to_human":
            return await self.escalate_call(arguments, call_id)
        elif tool_name == "search_knowledge_base":
            return await self.search_knowledge(arguments)
        elif tool_name == "check_order_status":
            return await self.check_order_status(arguments)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    async def lookup_customer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Look up customer information"""
        # Implementation here
        pass
    
    async def schedule_appointment(self, args: Dict[str, Any], call_id: str) -> Dict[str, Any]:
        """Schedule an appointment"""
        # Implementation here
        pass
    
    async def escalate_call(self, args: Dict[str, Any], call_id: str) -> Dict[str, Any]:
        """Escalate call to human"""
        # Implementation here
        pass
    
    async def search_knowledge(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search knowledge base"""
        query = args.get("query")
        results = await self.rag.search(query)
        return {"results": results}
    
    async def check_order_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check order status"""
        # Implementation here
        pass
```

### Step 2: Update OpenAI Client

The OpenAI client has been enhanced to handle tool calls:

```python
async def _handle_event(self, session_id: str, event: Dict[str, Any]) -> None:
    """Handle incoming event from OpenAI"""
    # ... existing code ...
    
    # Handle tool calls
    if event_type == "response.function_call_arguments.delta":
        # Accumulate function call arguments
        pass
    
    elif event_type == "response.function_call.done":
        # Execute tool and return result
        tool_call = event.get("function_call")
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})
        
        # Call tool handler
        result = await self.tool_handlers.handle_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            call_id=session_id,
        )
        
        # Send tool result back to OpenAI
        await self._send_event(session["websocket"], {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "function_call_id": tool_call.get("id"),
                "output": json.dumps(result),
            },
        })
```

### Step 3: Configure Tools for Business Types

Tool configurations per business type:

```python
# Customer Support Tools
CUSTOMER_SUPPORT_TOOLS = [
    customer_lookup_tool,
    search_knowledge_tool,
    escalate_call_tool,
    check_order_status_tool,
]

# Sales Tools
SALES_TOOLS = [
    customer_lookup_tool,
    schedule_appointment_tool,
    search_knowledge_tool,
]

# Appointment Booking Tools
APPOINTMENT_TOOLS = [
    customer_lookup_tool,
    schedule_appointment_tool,
    search_knowledge_tool,
]
```

## Key Features of AgentKit Voice Abilities

### 1. **Real-Time Action Execution**
Voice agents can now:
- Look up customer data during conversations
- Schedule appointments in real-time
- Search knowledge base while talking
- Escalate calls when needed
- Create support tickets
- Check order status

### 2. **Natural Voice Integration**
- Tools are called automatically based on conversation context
- Results are seamlessly integrated into agent responses
- No interruption to the natural flow of conversation

### 3. **Business-Type Specific**
Different tool sets for different use cases:
- **Customer Support**: Lookup, search, escalate, tickets
- **Sales**: Lookup, schedule, search products
- **Appointments**: Lookup, schedule, check availability

## How to Use

### Example: Setting up a voice call with abilities

```python
from src.ai.openai_client import OpenAIRealtimeClient
from src.ai.tool_handlers import get_customer_support_tools

# Initialize client
client = OpenAIRealtimeClient(business_id="your-business-id")

# Create session with tools
await client.create_session(
    session_id=call_id,
    system_prompt="You are a helpful customer service agent...",
    tools=get_customer_support_tools(),  # Add abilities!
    voice="nova",
)

# During conversation:
# Customer: "Can you check my order status?"
# → Agent automatically calls check_order_status tool
# → Gets order info
# → Speaks: "Your order #12345 is currently being shipped..."
```

### Example: Custom Tool

```python
# Define your tool
custom_tool = {
    "type": "function",
    "function": {
        "name": "your_custom_tool",
        "description": "What your tool does",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "..."}
            }
        }
    }
}

# Add handler
async def handle_your_custom_tool(self, args, call_id):
    # Your implementation
    return {"result": "..."}

# Use in session
await client.create_session(
    session_id=call_id,
    tools=[custom_tool, ...],
)
```

## Benefits of Using Abilities

1. **Actionable Conversations**: Agents can actually perform actions, not just talk
2. **Reduced Latency**: Tools execute in parallel with speech generation
3. **Better Context**: Tools access real-time data from your systems
4. **Scalability**: Easy to add new capabilities
5. **Monitoring**: Track tool usage and performance

## Architecture

```
Voice Call Flow with Abilities:
┌─────────────┐
│   Customer  │
└──────┬──────┘
       │ Speaks
       ▼
┌─────────────────┐
│  Twilio Media   │
└──────┬──────────┘
       │ Audio Stream
       ▼
┌──────────────────────┐
│ OpenAI Realtime API  │
│  (with Tools)        │
└──────┬───────────────┘
       │ Detects need for tool
       ▼
┌──────────────────────┐
│  Tool Handlers       │
│  - lookup_customer   │
│  - search_knowledge  │
│  - escalate_call     │
└──────┬───────────────┘
       │ Executes & Returns
       ▼
┌──────────────────────┐
│ OpenAI Processes     │
│ Result & Speaks      │
└──────┬───────────────┘
       │ Response Audio
       ▼
┌─────────────────┐
│  Twilio Media   │
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│   Customer  │
└─────────────┘
```

## Best Practices

### 1. Tool Design
- **Clear descriptions**: Tools should have clear, concise descriptions
- **Specific parameters**: Define parameters with types and descriptions
- **Error handling**: Always handle errors gracefully
- **Idempotency**: Make tools idempotent when possible

### 2. Voice-Specific Considerations
- **Natural language**: Tools should work with natural language inputs
- **Context awareness**: Tools should use conversation context
- **Fast responses**: Tool execution should be fast (< 2 seconds)
- **Clear feedback**: Provide clear feedback to users

### 3. Security
- **Input validation**: Validate all tool inputs
- **Authorization**: Check permissions before executing tools
- **Rate limiting**: Implement rate limiting for tools
- **Audit logging**: Log all tool executions

## Example: Complete Voice Call Flow with Abilities

```python
# 1. Initialize session with tools
await openai_client.create_session(
    session_id=call_id,
    system_prompt="You are a helpful customer service agent...",
    tools=CUSTOMER_SUPPORT_TOOLS,
    voice="nova",
)

# 2. Customer speaks: "I need to check my order status"
# → Agent recognizes intent
# → Calls check_order_status tool
# → Returns order information
# → Agent speaks: "Your order #12345 is currently being shipped..."

# 3. Customer speaks: "Can you escalate this?"
# → Agent calls escalate_to_human tool
# → Escalation manager assigns agent
# → Agent speaks: "I'm transferring you to a specialist..."
```

## Files Created/Modified

- ✅ `AGENTKIT_VOICE_ABILITIES.md` - Comprehensive guide (merged into this file)
- ✅ `src/ai/tool_handlers.py` - Tool execution handlers
- ✅ `src/ai/openai_client.py` - Enhanced with tool call handling
- ✅ `AGENTKIT_VOICE_INTEGRATION_SUMMARY.md` - Integration summary (merged into this file)

## Next Steps

1. **Customize Tools**: Modify tool handlers to connect to your actual systems
2. **Add More Tools**: Create additional abilities specific to your business
3. **Test Integration**: Test tool calls with real voice conversations
4. **Monitor Usage**: Track which tools are used most frequently
5. **Optimize**: Improve tool descriptions for better agent understanding

## Resources

- OpenAI AgentKit Docs: https://platform.openai.com/docs/guides/agents/agent-builder
- Voice Agents Guide: https://platform.openai.com/docs/guides/voice-agents
- Realtime API: https://platform.openai.com/docs/guides/realtime

