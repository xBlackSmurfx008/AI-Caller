"""Tool handlers for voice agent abilities (AgentKit-style)"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.database.database import get_db
from src.database.models import Call, Escalation, EscalationStatus
from src.knowledge.rag_pipeline import RAGPipeline
from src.escalation.escalation_manager import EscalationManager
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ToolHandlers:
    """Handlers for agent tools/abilities in voice calls"""

    def __init__(self, business_id: Optional[str] = None):
        """
        Initialize tool handlers
        
        Args:
            business_id: Business configuration ID
        """
        self.business_id = business_id
        self.rag_pipeline = RAGPipeline(business_id=business_id) if business_id else None
        self.escalation_manager = EscalationManager()

    async def handle_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        call_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle tool calls from voice agent
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            call_id: Call ID for context
            
        Returns:
            Tool execution result
        """
        try:
            logger.info(
                "tool_call_received",
                tool_name=tool_name,
                call_id=call_id,
                arguments=arguments,
            )

            if tool_name == "lookup_customer":
                return await self.lookup_customer(arguments, call_id)
            elif tool_name == "schedule_appointment":
                return await self.schedule_appointment(arguments, call_id)
            elif tool_name == "escalate_to_human":
                return await self.escalate_call(arguments, call_id)
            elif tool_name == "search_knowledge_base":
                return await self.search_knowledge(arguments)
            elif tool_name == "check_order_status":
                return await self.check_order_status(arguments, call_id)
            elif tool_name == "create_support_ticket":
                return await self.create_support_ticket(arguments, call_id)
            elif tool_name == "get_business_hours":
                return await self.get_business_hours()
            else:
                return {
                    "error": f"Unknown tool: {tool_name}",
                    "available_tools": [
                        "lookup_customer",
                        "schedule_appointment",
                        "escalate_to_human",
                        "search_knowledge_base",
                        "check_order_status",
                        "create_support_ticket",
                        "get_business_hours",
                    ],
                }
        except Exception as e:
            logger.error(
                "tool_execution_error",
                tool_name=tool_name,
                error=str(e),
                call_id=call_id,
            )
            return {"error": f"Tool execution failed: {str(e)}"}

    async def lookup_customer(
        self, args: Dict[str, Any], call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Look up customer information
        
        Args:
            args: Tool arguments (phone_number or email)
            call_id: Call ID for context
            
        Returns:
            Customer information
        """
        phone_number = args.get("phone_number")
        email = args.get("email")

        # In a real implementation, query your CRM/database
        # This is a placeholder
        if phone_number:
            # Query by phone number
            customer_info = {
                "found": True,
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": phone_number,
                "account_type": "Premium",
                "member_since": "2023-01-15",
                "previous_calls": 3,
            }
        elif email:
            # Query by email
            customer_info = {
                "found": True,
                "name": "John Doe",
                "email": email,
                "phone": "+1234567890",
                "account_type": "Premium",
                "member_since": "2023-01-15",
                "previous_calls": 3,
            }
        else:
            return {"error": "Either phone_number or email is required"}

        logger.info("customer_lookup_success", call_id=call_id, customer=customer_info.get("name"))
        return customer_info

    async def schedule_appointment(
        self, args: Dict[str, Any], call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Schedule an appointment
        
        Args:
            args: Tool arguments (date, time, service_type)
            call_id: Call ID for context
            
        Returns:
            Appointment confirmation
        """
        date = args.get("date")
        time = args.get("time")
        service_type = args.get("service_type")

        if not all([date, time, service_type]):
            return {"error": "date, time, and service_type are required"}

        # In a real implementation, create appointment in your system
        appointment_id = f"APT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        result = {
            "success": True,
            "appointment_id": appointment_id,
            "date": date,
            "time": time,
            "service_type": service_type,
            "confirmation_number": appointment_id,
            "message": f"Appointment scheduled for {date} at {time}",
        }

        logger.info("appointment_scheduled", call_id=call_id, appointment_id=appointment_id)
        return result

    async def escalate_call(
        self, args: Dict[str, Any], call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Escalate call to human agent
        
        Args:
            args: Tool arguments (reason, priority)
            call_id: Call ID for context
            
        Returns:
            Escalation result
        """
        reason = args.get("reason", "customer_request")
        priority = args.get("priority", "medium")

        if not call_id:
            return {"error": "call_id is required for escalation"}

        try:
            db = next(get_db())
            call = db.query(Call).filter(Call.id == call_id).first()

            if not call:
                return {"error": "Call not found"}

            # Create escalation record
            escalation = Escalation(
                call_id=call_id,
                status=EscalationStatus.PENDING,
                trigger_type=reason,
                trigger_details={"priority": priority},
                requested_at=datetime.utcnow(),
            )

            db.add(escalation)
            db.commit()

            # Trigger escalation via escalation manager
            await self.escalation_manager.escalate_call(
                call_id=call_id,
                trigger_type=reason,
                priority=priority,
            )

            result = {
                "success": True,
                "escalation_id": escalation.id,
                "status": "pending",
                "message": "Call escalation initiated. You will be connected to a specialist shortly.",
            }

            logger.info("call_escalated", call_id=call_id, escalation_id=escalation.id)
            return result

        except Exception as e:
            logger.error("escalation_failed", error=str(e), call_id=call_id)
            return {"error": f"Escalation failed: {str(e)}"}

    async def search_knowledge(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search knowledge base
        
        Args:
            args: Tool arguments (query, category)
            
        Returns:
            Search results
        """
        query = args.get("query")
        category = args.get("category")

        if not query:
            return {"error": "query is required"}

        if not self.rag_pipeline:
            return {"error": "Knowledge base not available"}

        try:
            # Perform RAG search
            results = await self.rag_pipeline.retrieve(
                query=query,
                top_k=3,
                filter={"category": category} if category else None,
            )

            # Format results for agent
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.get("content", ""),
                    "source": result.get("source", ""),
                    "relevance_score": result.get("score", 0),
                })

            return {
                "success": True,
                "query": query,
                "results": formatted_results,
                "count": len(formatted_results),
            }

        except Exception as e:
            logger.error("knowledge_search_error", error=str(e), query=query)
            return {"error": f"Knowledge search failed: {str(e)}"}

    async def check_order_status(
        self, args: Dict[str, Any], call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check order status
        
        Args:
            args: Tool arguments (order_id)
            call_id: Call ID for context
            
        Returns:
            Order status information
        """
        order_id = args.get("order_id")

        if not order_id:
            return {"error": "order_id is required"}

        # In a real implementation, query your order system
        # This is a placeholder
        order_status = {
            "order_id": order_id,
            "status": "shipped",
            "tracking_number": f"TRACK-{order_id}",
            "estimated_delivery": "2024-01-20",
            "items": [
                {"name": "Product A", "quantity": 1, "status": "shipped"},
            ],
            "shipping_address": "123 Main St, City, State 12345",
        }

        logger.info("order_status_checked", call_id=call_id, order_id=order_id)
        return order_status

    async def create_support_ticket(
        self, args: Dict[str, Any], call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a support ticket
        
        Args:
            args: Tool arguments (subject, description, priority)
            call_id: Call ID for context
            
        Returns:
            Ticket creation result
        """
        subject = args.get("subject")
        description = args.get("description")
        priority = args.get("priority", "medium")

        if not subject or not description:
            return {"error": "subject and description are required"}

        # In a real implementation, create ticket in your system
        ticket_id = f"TICKET-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        result = {
            "success": True,
            "ticket_id": ticket_id,
            "subject": subject,
            "priority": priority,
            "status": "open",
            "message": f"Support ticket {ticket_id} has been created",
        }

        logger.info("support_ticket_created", call_id=call_id, ticket_id=ticket_id)
        return result

    async def get_business_hours(self) -> Dict[str, Any]:
        """
        Get business hours
        
        Returns:
            Business hours information
        """
        # In a real implementation, fetch from configuration
        business_hours = {
            "monday": {"open": "09:00", "close": "17:00"},
            "tuesday": {"open": "09:00", "close": "17:00"},
            "wednesday": {"open": "09:00", "close": "17:00"},
            "thursday": {"open": "09:00", "close": "17:00"},
            "friday": {"open": "09:00", "close": "17:00"},
            "saturday": {"open": "10:00", "close": "14:00"},
            "sunday": {"closed": True},
            "timezone": "America/New_York",
        }

        return business_hours


# Tool definitions for OpenAI Realtime API
def get_customer_support_tools() -> List[Dict[str, Any]]:
    """Get tools for customer support agents"""
    return [
        {
            "type": "function",
            "function": {
                "name": "lookup_customer",
                "description": "Look up customer information by phone number or email address",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone_number": {
                            "type": "string",
                            "description": "Customer phone number",
                        },
                        "email": {
                            "type": "string",
                            "description": "Customer email address",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "Search the knowledge base for information to help answer customer questions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional category to filter results",
                        },
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_order_status",
                "description": "Check the status of a customer order",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "Order ID or tracking number",
                        },
                    },
                    "required": ["order_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_support_ticket",
                "description": "Create a support ticket for issues that cannot be resolved immediately",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "string",
                            "description": "Ticket subject",
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the issue",
                        },
                        "priority": {
                            "type": "string",
                            "description": "Ticket priority",
                            "enum": ["low", "medium", "high", "urgent"],
                        },
                    },
                    "required": ["subject", "description"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "escalate_to_human",
                "description": "Escalate the call to a human agent when the customer requests it or the issue is too complex",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Reason for escalation",
                            "enum": ["complex_issue", "customer_request", "technical_problem"],
                        },
                        "priority": {
                            "type": "string",
                            "description": "Escalation priority",
                            "enum": ["low", "medium", "high", "urgent"],
                        },
                    },
                    "required": ["reason"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_business_hours",
                "description": "Get current business hours and availability",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        },
    ]


def get_sales_tools() -> List[Dict[str, Any]]:
    """Get tools for sales agents"""
    return [
        {
            "type": "function",
            "function": {
                "name": "lookup_customer",
                "description": "Look up customer information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone_number": {"type": "string"},
                        "email": {"type": "string"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "schedule_appointment",
                "description": "Schedule a sales appointment or consultation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                        "time": {"type": "string", "description": "Time in HH:MM format"},
                        "service_type": {"type": "string", "description": "Type of service"},
                    },
                    "required": ["date", "time", "service_type"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "Search product information and pricing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "category": {"type": "string"},
                    },
                    "required": ["query"],
                },
            },
        },
    ]


def get_appointment_tools() -> List[Dict[str, Any]]:
    """Get tools for appointment booking agents"""
    return [
        {
            "type": "function",
            "function": {
                "name": "lookup_customer",
                "description": "Look up customer information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone_number": {"type": "string"},
                        "email": {"type": "string"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "schedule_appointment",
                "description": "Schedule an appointment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "time": {"type": "string"},
                        "service_type": {"type": "string"},
                    },
                    "required": ["date", "time", "service_type"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_business_hours",
                "description": "Get available appointment times",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    ]

