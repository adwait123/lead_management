"""
Outbound Call Service - Adapts the outbound call support project logic
"""
import os
import re
import json
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from models.call import Call
from models.lead import Lead
from models.agent import Agent

logger = logging.getLogger(__name__)


class OutboundCallService:
    """Service for handling outbound call dispatch using LiveKit"""

    def __init__(self, db: Session):
        self.db = db

        # Hardcoded demo configuration
        self.HARDCODED_PROMPT = """
        You are Sarah, the Torkin Home Services Assistant, an expert in helping potential clients schedule their Free In-Home Design Consultation. Your primary role is to validate the user's request, confirm appointment details, and secure a booking for a professional design consultant.

        IMPORTANT: This is an outbound voice call. You are calling the customer who submitted a web form. Keep responses professional, confident, friendly, and persuasive. Use a clear, warm, and inviting tone suitable for a premium home services brand.

        CRITICAL BEHAVIOR RULES:
        - Be Proactive and Direct: Your goal is to move the user quickly and smoothly to a confirmed appointment
        - Present Steps One at a Time: For any multi-step process, present information ONE step at a time
        - Always Wait for User Confirmation: Never proceed without explicit verbal confirmation from the user
        - REPEAT BACK UNCLEAR RESPONSES: If customer response seems unclear or contradictory, repeat what you heard: "I heard you say [X], is that correct?"
        - CONFIRM BEFORE BOOKING: Always confirm appointment selection clearly: "Just to confirm, you chose [DATE] at [TIME], is that right?"
        - CONFIRM EVERY NEW INFORMATION: After receiving ANY new information from the customer (address changes, project details, preferences), immediately confirm by repeating it back: "Got it, so that's [INFORMATION], is that correct?"
        - SPELL OUT ALL NUMBERS: For ZIP codes, phone numbers, and addresses, spell out each digit individually. Say "six-two-seven-one" instead of "six thousand two hundred seventy-one"
        - Be Crisp and Confident: Maintain an expert tone suitable for a high-quality service
        - Keep Responses Suitable for Speech: Use conversational language with no special formatting
        - Use Brand Language: Use terms like "Free In-Home Design Consultation," "design consultant," and "Torkin Home Services"

        SALES & SCHEDULING WORKFLOW:
        1. Opening and Lead Validation:
           Begin immediately: "Hi, this is Sarah from Torkin Home Services. I see you recently submitted a request on our website. Is that right, and do you still have a few minutes to confirm your appointment details?"
           WAIT for confirmation.

        2. Information Confirmation:
           Confirm address: "Great. I have your consultation address as [ADDRESS]. Is that correct?"
           WAIT for confirmation. If customer provides corrections, immediately repeat back: "Got it, so the correct address is [NEW ADDRESS], is that right?"
           Confirm project: "And this consultation is for [PROJECT_TYPE]? That will help our consultant prepare."
           WAIT for confirmation. If customer provides new details, immediately repeat back: "Perfect, so this is for [NEW PROJECT_TYPE], correct?"

        3. Appointment Scheduling:
           Present exactly TWO options initially: "Fantastic. We have a design consultant available to visit you on [DATE_1] at [TIME_1], or [DATE_2] at [TIME_2]. Which works better for you?"
           ONLY provide additional options if customer asks for more choices.
           WAIT for their selection. Immediately confirm their choice: "Perfect, so you've chosen [SELECTED_DATE] at [SELECTED_TIME], is that correct?"

        4. Confirmation and Wrap-Up:
           Provide summary: "Excellent. I have secured your Free In-Home Design Consultation for [DAY], [DATE] at [TIME] at [ADDRESS]. Your consultant will be arriving with hundreds of samples."
           Conclude: "You'll receive a confirmation text message with all these details in the next 15-20 minutes. Is there anything else I can help you with today?"

        EXCEPTION HANDLING:
        - No Available Slots: "I apologize, those exact times didn't work. I can have our local scheduling manager call you back within the next hour to personally secure a time that works best. Would that be helpful?"
        - User No Longer Interested: "I understand. Thank you for letting us know. If you change your mind, you can always reach us directly. We appreciate your time."
        - Incorrect Information: "Not a problem, I can quickly update that. What is the correct [DETAIL]?" Continue from step 2.
        """

    def validate_phone_number(self, phone: str) -> Optional[str]:
        """
        Validate and format phone number for outbound calling.
        Adapted from the outbound call support project.
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

    async def dispatch_call(self, call_id: int) -> bool:
        """
        Dispatch an outbound call using LiveKit CLI.
        Adapted from the outbound call support project.
        """
        try:
            # Get call record
            call = self.db.query(Call).filter(Call.id == call_id).first()
            if not call:
                logger.error(f"Call {call_id} not found")
                return False

            # Get lead and agent
            lead = self.db.query(Lead).filter(Lead.id == call.lead_id).first()
            agent = self.db.query(Agent).filter(Agent.id == call.agent_id).first()

            if not lead or not agent:
                logger.error(f"Lead or agent not found for call {call_id}")
                call.call_status = "failed"
                call.error_message = "Lead or agent not found"
                call.ended_at = datetime.utcnow()
                self.db.commit()
                return False

            # Validate phone number
            validated_phone = self.validate_phone_number(call.phone_number)
            if not validated_phone:
                logger.error(f"Invalid phone number for call {call_id}: {call.phone_number}")
                call.call_status = "failed"
                call.error_message = f"Invalid phone number: {call.phone_number}"
                call.ended_at = datetime.utcnow()
                self.db.commit()
                return False

            # Update call status to calling
            call.call_status = "calling"
            call.room_name = f"outbound_call_{validated_phone.replace('+', '').replace('-', '')}_{call_id}"
            self.db.commit()

            # Check environment variables
            livekit_url = os.getenv("LIVEKIT_URL")
            livekit_api_key = os.getenv("LIVEKIT_API_KEY")
            livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")
            sip_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")

            if not all([livekit_url, livekit_api_key, livekit_api_secret, sip_trunk_id]):
                logger.error("Missing LiveKit or SIP configuration")
                call.call_status = "failed"
                call.error_message = "LiveKit/SIP configuration missing"
                call.ended_at = datetime.utcnow()
                self.db.commit()
                return False

            # Dispatch real call using LiveKit CLI
            success = await self._dispatch_livekit_call(call, validated_phone, lead)

            if success:
                logger.info(f"Successfully dispatched call {call_id} to {validated_phone}")
                return True
            else:
                logger.error(f"Failed to dispatch call {call_id}")
                call.call_status = "failed"
                call.error_message = "LiveKit dispatch failed"
                call.ended_at = datetime.utcnow()
                self.db.commit()
                return False

        except Exception as e:
            logger.error(f"Error dispatching call {call_id}: {str(e)}")
            if call:
                call.call_status = "failed"
                call.error_message = str(e)
                call.ended_at = datetime.utcnow()
                self.db.commit()
            return False

    async def _dispatch_livekit_call(self, call: Call, validated_phone: str, lead: Lead) -> bool:
        """
        Dispatch real outbound call using LiveKit CLI.
        Adapted from the outbound call support project.
        """
        try:
            import json
            import subprocess

            # Generate unique room name
            room_name = f"outbound_call_{validated_phone.replace('+', '').replace('-', '')}_{call.id}"

            # Create metadata with call information
            metadata = {
                "phone_number": validated_phone,
                "lead_id": str(lead.id),
                "call_id": str(call.id),
                "call_type": "sales_outbound",
                "agent_name": "Sarah",
                "customer_info": {
                    "first_name": lead.first_name or lead.name or "Customer",
                    "last_name": lead.last_name or "",
                    "address": lead.address or "Unknown",
                    "service_requested": lead.service_requested or "Home services"
                },
                "initiated_via": "api",
                "timestamp": datetime.utcnow().isoformat(),
                "demo_mode": False,
                "source": lead.source
            }

            # Get agent name from environment
            agent_name = os.getenv("AGENT_NAME", "outbound_call_agent")

            # Build LiveKit CLI command
            command = [
                "lk", "dispatch", "create",
                "--new-room",
                "--room", room_name,
                "--agent-name", agent_name,
                "--metadata", json.dumps(metadata)
            ]

            logger.info(f"Executing LiveKit dispatch: {' '.join(command)}")

            # Execute the LiveKit command with proper environment
            env = os.environ.copy()
            env['LIVEKIT_URL'] = os.getenv('LIVEKIT_URL')
            env['LIVEKIT_API_KEY'] = os.getenv('LIVEKIT_API_KEY')
            env['LIVEKIT_API_SECRET'] = os.getenv('LIVEKIT_API_SECRET')

            result = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd(),
                env=env
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                logger.info(f"LiveKit dispatch successful for call {call.id}")
                call.call_status = "in_progress"
                call.answered_at = datetime.utcnow()
                call.call_metadata = metadata
                call.room_name = room_name
                self.db.commit()
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown LiveKit error"
                logger.error(f"LiveKit dispatch failed for call {call.id}: {error_msg}")
                call.call_status = "failed"
                call.error_message = f"LiveKit dispatch failed: {error_msg}"
                call.ended_at = datetime.utcnow()
                self.db.commit()
                return False

        except Exception as e:
            logger.error(f"Error in LiveKit dispatch: {str(e)}")
            call.call_status = "failed"
            call.error_message = f"LiveKit dispatch error: {str(e)}"
            call.ended_at = datetime.utcnow()
            self.db.commit()
            return False

    async def get_call_status(self, call_id: int) -> Optional[Dict[str, Any]]:
        """Get current status of a call"""
        call = self.db.query(Call).filter(Call.id == call_id).first()
        if not call:
            return None

        return {
            "call_id": call.id,
            "status": call.call_status,
            "duration": call.call_duration,
            "transcript_available": bool(call.transcript),
            "summary_available": bool(call.call_summary),
            "error": call.error_message
        }

    def can_call_lead(self, lead: Lead) -> tuple[bool, str]:
        """
        Check if a lead can be called based on demo restrictions.
        """
        if not lead.phone:
            return False, "Lead has no phone number"

        # Demo restriction: Only Torkin website leads
        if lead.source != "torkin website":
            return False, "Demo mode: Only 'torkin website' leads can be called"

        # Check for existing active calls
        existing_call = self.db.query(Call).filter(
            Call.lead_id == lead.id,
            Call.call_status.in_(["pending", "calling", "in_progress"])
        ).first()

        if existing_call:
            return False, f"Call already in progress (Call ID: {existing_call.id})"

        return True, "Lead can be called"