"""
Inbound Call Service - Handles incoming call processing and agent routing
"""
import os
import re
import json
import asyncio
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.inbound_call import InboundCall
from models.lead import Lead
from models.agent import Agent
from models.agent_session import AgentSession
from models.message import Message

logger = logging.getLogger(__name__)


class InboundCallService:
    """Service for handling inbound call processing and agent assignment"""

    def __init__(self, db: Session):
        self.db = db

    def can_handle_inbound_call(self) -> Tuple[bool, Optional[Agent], str]:
        """
        Check if we can handle an inbound call by validating agent availability.
        Returns: (can_handle, agent, reason)
        """
        # Find active inbound agents
        inbound_agent = self.db.query(Agent).filter(
            Agent.type == "inbound",
            Agent.is_active == True
        ).first()

        if not inbound_agent:
            return False, None, "No active inbound agents available"

        return True, inbound_agent, "Inbound agent available"

    def validate_phone_number(self, phone: str) -> Optional[str]:
        """
        Validate and format phone number for inbound calls.
        """
        # Remove all non-digit characters
        digits_only = re.sub(r'[^\d]', '', phone)

        # Handle US numbers
        if len(digits_only) == 10:
            # Add US country code
            formatted = f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            # Already has US country code
            formatted = f"+{digits_only}"
        else:
            return None

        # Validate US phone number format
        if re.match(r'^\+1[2-9]\d{2}[2-9]\d{6}$', formatted):
            return formatted
        else:
            return None

    async def process_call(self, call_id: int) -> bool:
        """
        Main entry point for processing an inbound call.
        This orchestrates the entire inbound call workflow.
        """
        try:
            # Get the inbound call record
            call = self.db.query(InboundCall).filter(InboundCall.id == call_id).first()
            if not call:
                logger.error(f"Inbound call {call_id} not found")
                return False

            logger.info(f"Processing inbound call {call_id} from {call.caller_phone_number}")

            # Step 1: Check if we can handle the call
            can_handle, agent, reason = self.can_handle_inbound_call()
            if not can_handle:
                logger.warning(f"Cannot handle inbound call {call_id}: {reason}")
                call.call_status = "rejected"
                call.rejection_reason = reason
                call.ended_at = datetime.utcnow()
                self.db.commit()
                return False

            # Step 2: Create or find existing lead
            lead = await self.find_or_create_lead(call.caller_phone_number)
            if not lead:
                logger.error(f"Failed to create/find lead for {call.caller_phone_number}")
                call.call_status = "failed"
                call.error_message = "Failed to create lead"
                call.ended_at = datetime.utcnow()
                self.db.commit()
                return False

            # Step 3: Update call with lead and agent information
            call.lead_id = lead.id
            call.agent_id = agent.id
            call.call_status = "ringing"  # Ready for agent to join
            self.db.commit()

            logger.info(f"Assigned inbound call {call_id} to lead {lead.id} and agent {agent.id}")

            # Step 4: Create LiveKit room for the call
            room_created = await self.create_livekit_room(call, lead, agent)
            if not room_created:
                logger.error(f"Failed to create LiveKit room for call {call_id}")
                call.call_status = "failed"
                call.error_message = "Failed to create LiveKit room"
                call.ended_at = datetime.utcnow()
                self.db.commit()
                return False

            # Step 5: Create agent session for conversation tracking
            session_created = await self.create_agent_session(call, lead, agent)
            if not session_created:
                logger.warning(f"Failed to create agent session for call {call_id}")
                # Not critical - continue processing

            # Step 6: Trigger workflow for new lead (if applicable)
            if lead.status == "new":
                await self.trigger_lead_workflow(lead)

            logger.info(f"Successfully processed inbound call {call_id}")
            return True

        except Exception as e:
            logger.error(f"Error processing inbound call {call_id}: {str(e)}")
            if call:
                call.call_status = "failed"
                call.error_message = str(e)
                call.ended_at = datetime.utcnow()
                self.db.commit()
            return False

    async def find_or_create_lead(self, phone_number: str) -> Optional[Lead]:
        """
        Find existing lead by phone number or create a new one.
        """
        try:
            # Validate phone number
            validated_phone = self.validate_phone_number(phone_number)
            if not validated_phone:
                logger.warning(f"Invalid phone number: {phone_number}")
                validated_phone = phone_number  # Use as-is if validation fails

            # Try to find existing lead by phone
            existing_lead = self.db.query(Lead).filter(Lead.phone == validated_phone).first()
            if existing_lead:
                logger.info(f"Found existing lead {existing_lead.id} for phone {validated_phone}")
                # Update status to contacted if it was new
                if existing_lead.status == "new":
                    existing_lead.status = "contacted"
                    self.db.commit()
                return existing_lead

            # Create new lead for unknown caller
            logger.info(f"Creating new lead for unknown caller {validated_phone}")

            # Extract area code for basic geographic info
            area_code = validated_phone[2:5] if len(validated_phone) >= 5 else "000"

            new_lead = Lead(
                name=f"Caller {area_code}",  # Placeholder name
                email=f"caller_{area_code}@inbound.placeholder",  # Required field - placeholder
                phone=validated_phone,
                status="new",
                source="phone_call",  # New source type for inbound calls
                service_requested="Phone inquiry",
                notes=[{
                    "id": 1,
                    "content": f"Lead created from inbound call to +17622437375",
                    "timestamp": datetime.utcnow().isoformat(),
                    "author": "System"
                }],
                interaction_history=[{
                    "id": 1,
                    "type": "inbound_call",
                    "content": f"Received inbound call from {validated_phone}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_id": None
                }]
            )

            self.db.add(new_lead)
            self.db.commit()
            self.db.refresh(new_lead)

            logger.info(f"Created new lead {new_lead.id} for phone {validated_phone}")
            return new_lead

        except Exception as e:
            logger.error(f"Error finding/creating lead for {phone_number}: {str(e)}")
            return None

    async def create_livekit_room(self, call: InboundCall, lead: Lead, agent: Agent) -> bool:
        """
        Create a LiveKit room for the inbound call and dispatch the inbound_raq agent.
        """
        try:
            from livekit.api import LiveKitAPI
            from livekit.protocol.room import CreateRoomRequest
            from livekit.protocol.agent_dispatch import CreateAgentDispatchRequest

            # Generate unique room name
            room_name = f"inbound_call_{call.caller_phone_number.replace('+', '').replace('-', '')}_{call.id}"

            # Create metadata with call information
            metadata = {
                "phone_number": call.caller_phone_number,
                "lead_id": str(lead.id),
                "call_id": str(call.id),
                "call_type": "inbound",
                "agent_name": agent.name,
                "agent_id": str(agent.id),
                "customer_info": {
                    "first_name": lead.first_name or lead.name or "Caller",
                    "last_name": lead.last_name or "",
                    "phone": lead.phone,
                    "address": lead.address or "Unknown",
                    "service_requested": lead.service_requested or "Phone inquiry"
                },
                "initiated_via": "inbound_webhook",
                "timestamp": datetime.utcnow().isoformat(),
                "inbound_number": call.inbound_phone_number,
                "source": lead.source
            }

            # Get LiveKit credentials
            livekit_url = os.getenv('LIVEKIT_URL')
            livekit_api_key = os.getenv('LIVEKIT_API_KEY')
            livekit_api_secret = os.getenv('LIVEKIT_API_SECRET')

            if not all([livekit_url, livekit_api_key, livekit_api_secret]):
                logger.error("Missing LiveKit configuration")
                return False

            # Use the configured inbound agent name
            inbound_agent_name = "inbound_raq"  # As specified by user

            logger.info(f"Creating LiveKit room for inbound call: {room_name}")

            # Initialize LiveKit API client
            api = LiveKitAPI(livekit_url, livekit_api_key, livekit_api_secret)

            # Create room first
            room_request = CreateRoomRequest(name=room_name)
            room = await api.room.create_room(room_request)
            logger.info(f"Created room: {room.name}")

            # Create agent dispatch request
            dispatch_request = CreateAgentDispatchRequest(
                room=room_name,
                agent_name=inbound_agent_name,
                metadata=json.dumps(metadata)
            )

            # Dispatch the agent
            dispatch_response = await api.agent_dispatch.create_dispatch(dispatch_request)
            logger.info(f"Inbound agent dispatch successful: {dispatch_response}")

            # Update call with room information
            call.room_name = room_name
            call.livekit_call_id = room.name
            call.call_status = "answered"  # Agent is joining
            call.answered_at = datetime.utcnow()
            call.call_metadata = metadata
            self.db.commit()

            logger.info(f"LiveKit room created successfully for inbound call {call.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create LiveKit room for call {call.id}: {str(e)}")
            return False

    async def create_agent_session(self, call: InboundCall, lead: Lead, agent: Agent) -> bool:
        """
        Create an agent session for conversation tracking.
        """
        try:
            # Check if session already exists
            existing_session = self.db.query(AgentSession).filter(
                AgentSession.lead_id == lead.id,
                AgentSession.agent_id == agent.id,
                AgentSession.session_status == "active"
            ).first()

            if existing_session:
                logger.info(f"Using existing agent session {existing_session.id}")
                return True

            # Create new agent session
            session = AgentSession(
                agent_id=agent.id,
                lead_id=lead.id,
                trigger_type="inbound_call",
                session_status="active",
                session_goal="Handle inbound call inquiry and qualify lead",
                initial_context={
                    "call_id": call.id,
                    "call_type": "inbound",
                    "caller_phone": call.caller_phone_number,
                    "inbound_number": call.inbound_phone_number,
                    "room_name": call.room_name
                },
                session_metadata={
                    "source": "inbound_call",
                    "call_initiated_at": call.received_at.isoformat(),
                    "agent_type": agent.type
                },
                auto_timeout_hours=2,  # Shorter timeout for phone calls
                max_message_count=50   # Reasonable limit for voice conversations
            )

            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            # Create initial system message
            system_message = Message.create_system_message(
                agent_session_id=session.id,
                lead_id=lead.id,
                content=f"Inbound call started from {call.caller_phone_number}",
                metadata={
                    "call_id": call.id,
                    "room_name": call.room_name,
                    "event_type": "call_started"
                }
            )

            self.db.add(system_message)
            self.db.commit()

            logger.info(f"Created agent session {session.id} for inbound call {call.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create agent session for call {call.id}: {str(e)}")
            return False

    async def trigger_lead_workflow(self, lead: Lead) -> bool:
        """
        Trigger the existing workflow system for new leads.
        """
        try:
            # Import here to avoid circular imports
            from services.workflow_service import WorkflowService

            workflow_service = WorkflowService(self.db)
            workflow_service.handle_lead_created(
                lead_id=lead.id,
                source=lead.source,
                form_data={
                    "phone": lead.phone,
                    "service_requested": lead.service_requested,
                    "trigger_type": "inbound_call"
                }
            )

            logger.info(f"Triggered workflow for new lead {lead.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to trigger workflow for lead {lead.id}: {str(e)}")
            return False

    async def update_call_status(self, call_id: int, status: str, metadata: Optional[Dict] = None) -> bool:
        """
        Update the status of an inbound call.
        """
        try:
            call = self.db.query(InboundCall).filter(InboundCall.id == call_id).first()
            if not call:
                return False

            call.call_status = status

            if metadata:
                current_metadata = call.call_metadata or {}
                current_metadata.update(metadata)
                call.call_metadata = current_metadata

            # Update timestamps based on status
            if status == "answered" and not call.answered_at:
                call.answered_at = datetime.utcnow()
            elif status in ["completed", "failed", "no_answer", "rejected"] and not call.ended_at:
                call.ended_at = datetime.utcnow()

            # Calculate duration if call is completed
            if status == "completed" and call.answered_at and not call.call_duration:
                if call.ended_at:
                    duration = (call.ended_at - call.answered_at).total_seconds()
                    call.call_duration = int(duration)

            self.db.commit()
            logger.info(f"Updated inbound call {call_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to update call {call_id} status: {str(e)}")
            return False

    async def get_call_stats(self) -> Dict[str, Any]:
        """
        Get statistics for inbound calls.
        """
        try:
            total_calls = self.db.query(InboundCall).count()
            answered_calls = self.db.query(InboundCall).filter(InboundCall.call_status == "completed").count()
            rejected_calls = self.db.query(InboundCall).filter(InboundCall.call_status == "rejected").count()
            failed_calls = self.db.query(InboundCall).filter(InboundCall.call_status == "failed").count()
            active_calls = self.db.query(InboundCall).filter(
                InboundCall.call_status.in_(["received", "ringing", "answered", "in_progress"])
            ).count()

            answer_rate = (answered_calls / total_calls * 100) if total_calls > 0 else 0

            # Get recent calls
            recent_calls = self.db.query(InboundCall).order_by(
                InboundCall.received_at.desc()
            ).limit(5).all()

            return {
                "total_calls": total_calls,
                "answered_calls": answered_calls,
                "rejected_calls": rejected_calls,
                "failed_calls": failed_calls,
                "active_calls": active_calls,
                "answer_rate": round(answer_rate, 1),
                "recent_calls": [
                    {
                        "id": call.id,
                        "caller": call.caller_phone_number,
                        "status": call.call_status,
                        "received_at": call.received_at.isoformat() if call.received_at else None
                    }
                    for call in recent_calls
                ]
            }

        except Exception as e:
            logger.error(f"Failed to get call stats: {str(e)}")
            return {
                "total_calls": 0,
                "answered_calls": 0,
                "rejected_calls": 0,
                "failed_calls": 0,
                "active_calls": 0,
                "answer_rate": 0,
                "recent_calls": []
            }

    def cleanup_old_calls(self, hours_old: int = 24) -> int:
        """
        Clean up old completed/failed calls to prevent database bloat.
        Returns number of calls cleaned up.
        """
        try:
            from datetime import timedelta

            cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)

            old_calls = self.db.query(InboundCall).filter(
                InboundCall.call_status.in_(["completed", "failed", "rejected"]),
                InboundCall.ended_at < cutoff_time
            ).all()

            count = len(old_calls)

            for call in old_calls:
                self.db.delete(call)

            self.db.commit()

            logger.info(f"Cleaned up {count} old inbound calls")
            return count

        except Exception as e:
            logger.error(f"Failed to cleanup old calls: {str(e)}")
            return 0