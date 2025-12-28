"""Call handler for managing call lifecycle"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.database.database import get_db
from src.database.models import (
    Call, CallStatus, CallDirection,
    PhoneNumber, AgentPhoneNumber, BusinessPhoneNumber, HumanAgent
)
from src.telephony.twilio_client import TwilioService
from src.telephony.call_manager import get_call_manager
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CallHandler:
    """Handler for managing calls"""

    def __init__(self):
        """Initialize call handler"""
        self.twilio = TwilioService()

    def initiate_outbound_call(
        self,
        to_number: str,
        from_number: Optional[str] = None,
        business_id: Optional[str] = None,
        template_id: Optional[str] = None,
        agent_personality: Optional[str] = None,
        agent_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Call:
        """
        Initiate an outbound call and create call record
        
        Args:
            to_number: Phone number to call
            from_number: Phone number to call from
            business_id: Business configuration ID
            template_id: Template ID
            agent_personality: Agent personality for the call
            agent_id: Agent ID to use for routing
            db: Database session
            
        Returns:
            Call model instance
        """
        if db is None:
            db = next(get_db())

        try:
            # Determine from_number based on agent or business assignment
            if not from_number:
                if agent_id:
                    # Get agent's primary phone number
                    agent_assignment = db.query(AgentPhoneNumber).join(PhoneNumber).filter(
                        AgentPhoneNumber.agent_id == agent_id,
                        AgentPhoneNumber.is_primary == True,
                        PhoneNumber.is_active == True,
                    ).first()
                    
                    if agent_assignment:
                        phone_number = db.query(PhoneNumber).filter(
                            PhoneNumber.id == agent_assignment.phone_number_id
                        ).first()
                        if phone_number:
                            from_number = phone_number.phone_number
                
                if not from_number and business_id:
                    # Get business's primary phone number
                    business_assignment = db.query(BusinessPhoneNumber).join(PhoneNumber).filter(
                        BusinessPhoneNumber.business_id == business_id,
                        BusinessPhoneNumber.is_primary == True,
                        PhoneNumber.is_active == True,
                    ).first()
                    
                    if business_assignment:
                        phone_number = db.query(PhoneNumber).filter(
                            PhoneNumber.id == business_assignment.phone_number_id
                        ).first()
                        if phone_number:
                            from_number = phone_number.phone_number
            
            # Initiate call via Twilio
            call_info = self.twilio.initiate_call(
                to_number=to_number,
                from_number=from_number,
            )

            # Create call record
            metadata = {}
            if agent_personality:
                metadata["agent_personality"] = agent_personality
            if agent_id:
                metadata["agent_id"] = agent_id
                agent = db.query(HumanAgent).filter(HumanAgent.id == agent_id).first()
                if agent:
                    metadata["agent_name"] = agent.name
            
            call = Call(
                id=str(uuid.uuid4()),
                twilio_call_sid=call_info["call_sid"],
                direction=CallDirection.OUTBOUND,
                status=CallStatus.INITIATED,
                from_number=call_info["from"],
                to_number=call_info["to"],
                business_id=business_id,
                template_id=template_id,
                meta_data=metadata if metadata else None,
                started_at=datetime.utcnow(),
            )

            db.add(call)
            db.commit()
            db.refresh(call)

            # Emit WebSocket event
            try:
                from src.api.routes.websocket import emit_call_started
                import asyncio
                
                call_data = {
                    "id": call.id,
                    "twilio_call_sid": call.twilio_call_sid,
                    "direction": call.direction.value,
                    "status": call.status.value,
                    "from_number": call.from_number,
                    "to_number": call.to_number,
                    "business_id": call.business_id,
                    "template_id": call.template_id,
                    "started_at": call.started_at.isoformat(),
                    "created_at": call.created_at.isoformat(),
                    "updated_at": call.updated_at.isoformat(),
                    "metadata": call.meta_data or {},
                }
                
                # Emit event (run in event loop if available)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(emit_call_started(call_data))
                    else:
                        loop.run_until_complete(emit_call_started(call_data))
                except RuntimeError:
                    # No event loop, create new one
                    asyncio.run(emit_call_started(call_data))
            except Exception as e:
                logger.warning("websocket_emit_failed", error=str(e), call_id=call.id)

            logger.info(
                "outbound_call_initiated",
                call_id=call.id,
                call_sid=call.twilio_call_sid,
                to_number=to_number,
            )

            # Note: Bridge will be started when media stream connects via WebSocket
            # This happens automatically when Twilio connects the media stream

            return call
        except Exception as e:
            db.rollback()
            logger.error("call_initiation_failed", error=str(e), to_number=to_number)
            raise

    def handle_inbound_call(
        self,
        call_sid: str,
        from_number: str,
        to_number: str,
        business_id: Optional[str] = None,
        template_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Call:
        """
        Handle an inbound call and create call record
        
        Args:
            call_sid: Twilio call SID
            from_number: Phone number calling from
            to_number: Phone number called
            business_id: Business configuration ID
            template_id: Template ID
            db: Database session
            
        Returns:
            Call model instance
        """
        if db is None:
            db = next(get_db())

        try:
            # Look up phone number in database
            phone_number = db.query(PhoneNumber).filter(
                PhoneNumber.phone_number == to_number
            ).first()
            
            routing_metadata = {}
            assigned_agent_id = None
            
            # If phone number found, route to associated agent/business
            if phone_number:
                # Find associated business
                business_assignment = db.query(BusinessPhoneNumber).filter(
                    BusinessPhoneNumber.phone_number_id == phone_number.id,
                    BusinessPhoneNumber.is_primary == True,
                ).first()
                
                if business_assignment:
                    business_id = business_assignment.business_id
                    routing_metadata["routed_via"] = "business_phone_assignment"
                
                # Find associated agent (primary first, then any available)
                agent_assignment = db.query(AgentPhoneNumber).filter(
                    AgentPhoneNumber.phone_number_id == phone_number.id,
                    AgentPhoneNumber.is_primary == True,
                ).first()
                
                if not agent_assignment:
                    # Try any assignment with available agent
                    agent_assignment = db.query(AgentPhoneNumber).join(HumanAgent).filter(
                        AgentPhoneNumber.phone_number_id == phone_number.id,
                        HumanAgent.is_available == True,
                        HumanAgent.is_active == True,
                    ).first()
                
                if agent_assignment:
                    assigned_agent_id = agent_assignment.agent_id
                    agent = db.query(HumanAgent).filter(HumanAgent.id == assigned_agent_id).first()
                    if agent:
                        routing_metadata["routed_via"] = "agent_phone_assignment"
                        routing_metadata["assigned_agent_id"] = assigned_agent_id
                        routing_metadata["assigned_agent_name"] = agent.name
                        routing_metadata["phone_number_id"] = phone_number.id
            
            # Create call record
            call = Call(
                id=str(uuid.uuid4()),
                twilio_call_sid=call_sid,
                direction=CallDirection.INBOUND,
                status=CallStatus.IN_PROGRESS,
                from_number=from_number,
                to_number=to_number,
                business_id=business_id,
                template_id=template_id,
                started_at=datetime.utcnow(),
                meta_data=routing_metadata if routing_metadata else None,
            )

            db.add(call)
            db.commit()
            db.refresh(call)

            # Emit WebSocket event
            try:
                from src.api.routes.websocket import emit_call_started
                import asyncio
                
                call_data = {
                    "id": call.id,
                    "twilio_call_sid": call.twilio_call_sid,
                    "direction": call.direction.value,
                    "status": call.status.value,
                    "from_number": call.from_number,
                    "to_number": call.to_number,
                    "business_id": call.business_id,
                    "template_id": call.template_id,
                    "started_at": call.started_at.isoformat(),
                    "created_at": call.created_at.isoformat(),
                    "updated_at": call.updated_at.isoformat(),
                    "metadata": call.meta_data or {},
                }
                
                # Emit event (run in event loop if available)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(emit_call_started(call_data))
                    else:
                        loop.run_until_complete(emit_call_started(call_data))
                except RuntimeError:
                    # No event loop, create new one
                    asyncio.run(emit_call_started(call_data))
            except Exception as e:
                logger.warning("websocket_emit_failed", error=str(e), call_id=call.id)

            logger.info(
                "inbound_call_received",
                call_id=call.id,
                call_sid=call_sid,
                from_number=from_number,
            )

            return call
        except Exception as e:
            db.rollback()
            logger.error("inbound_call_handling_failed", error=str(e), call_sid=call_sid)
            raise

    def update_call_status(
        self,
        call_sid: str,
        status: CallStatus,
        db: Optional[Session] = None,
    ) -> Optional[Call]:
        """
        Update call status
        
        Args:
            call_sid: Twilio call SID
            status: New status
            db: Database session
            
        Returns:
            Updated call model instance
        """
        if db is None:
            db = next(get_db())

        try:
            call = db.query(Call).filter(Call.twilio_call_sid == call_sid).first()
            if not call:
                logger.warning("call_not_found", call_sid=call_sid)
                return None

            call.status = status
            if status == CallStatus.COMPLETED:
                call.ended_at = datetime.utcnow()

            db.commit()
            db.refresh(call)

            # Emit WebSocket events
            try:
                from src.api.routes.websocket import emit_call_updated, emit_call_ended
                import asyncio
                
                call_data = {
                    "id": call.id,
                    "twilio_call_sid": call.twilio_call_sid,
                    "direction": call.direction.value,
                    "status": call.status.value,
                    "from_number": call.from_number,
                    "to_number": call.to_number,
                    "business_id": call.business_id,
                    "template_id": call.template_id,
                    "started_at": call.started_at.isoformat(),
                    "ended_at": call.ended_at.isoformat() if call.ended_at else None,
                    "created_at": call.created_at.isoformat(),
                    "updated_at": call.updated_at.isoformat(),
                    "metadata": call.meta_data or {},
                }
                
                # Emit events (run in event loop if available)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(emit_call_updated(call_data))
                        if status == CallStatus.COMPLETED:
                            asyncio.create_task(emit_call_ended(call.id))
                    else:
                        loop.run_until_complete(emit_call_updated(call_data))
                        if status == CallStatus.COMPLETED:
                            loop.run_until_complete(emit_call_ended(call.id))
                except RuntimeError:
                    # No event loop, create new one
                    asyncio.run(emit_call_updated(call_data))
                    if status == CallStatus.COMPLETED:
                        asyncio.run(emit_call_ended(call.id))
            except Exception as e:
                logger.warning("websocket_emit_failed", error=str(e), call_id=call.id)

            logger.info(
                "call_status_updated",
                call_id=call.id,
                call_sid=call_sid,
                status=status.value,
            )

            return call
        except Exception as e:
            db.rollback()
            logger.error("call_status_update_failed", error=str(e), call_sid=call_sid)
            raise

    def get_call_by_sid(
        self,
        call_sid: str,
        db: Optional[Session] = None,
    ) -> Optional[Call]:
        """
        Get call by Twilio call SID
        
        Args:
            call_sid: Twilio call SID
            db: Database session
            
        Returns:
            Call model instance or None
        """
        if db is None:
            db = next(get_db())

        return db.query(Call).filter(Call.twilio_call_sid == call_sid).first()

    def get_call_by_id(
        self,
        call_id: str,
        db: Optional[Session] = None,
    ) -> Optional[Call]:
        """
        Get call by internal ID
        
        Args:
            call_id: Internal call ID
            db: Database session
            
        Returns:
            Call model instance or None
        """
        if db is None:
            db = next(get_db())

        return db.query(Call).filter(Call.id == call_id).first()

