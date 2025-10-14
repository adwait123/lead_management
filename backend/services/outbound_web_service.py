"""
Outbound Web Service - HTTP API integration for outbound calling
Replaces LiveKit implementation with simple HTTP API calls
"""
import os
import re
import json
import asyncio
import logging
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from models.call import Call
from models.lead import Lead
from models.agent import Agent

logger = logging.getLogger(__name__)


class OutboundWebService:
    """Service for handling outbound call dispatch using external web API"""

    def __init__(self, db: Session):
        self.db = db

        # Web service configuration
        self.web_service_url = os.getenv(
            "OUTBOUND_WEB_SERVICE_URL",
            "https://outbound-call-support-webhook.onrender.com/api/v1/dispatch-call"
        )
        self.api_key = os.getenv(
            "OUTBOUND_WEB_SERVICE_API_KEY",
            "secure-api-key-change-this-in-production"
        )

    def validate_phone_number(self, phone: str) -> Optional[str]:
        """
        Validate and format phone number for outbound calling.
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
        Dispatch an outbound call using the web service API.
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
            self.db.commit()

            # Dispatch call using web service API
            success = await self._dispatch_web_service_call(call, validated_phone, lead, agent)

            if success:
                logger.info(f"Successfully dispatched call {call_id} to {validated_phone}")
                return True
            else:
                logger.error(f"Failed to dispatch call {call_id}")
                call.call_status = "failed"
                call.error_message = "Web service dispatch failed"
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

    async def _dispatch_web_service_call(self, call: Call, validated_phone: str, lead: Lead, agent: Agent) -> bool:
        """
        Make HTTP request to the web service API to dispatch the call.
        """
        try:
            # Prepare the API payload
            payload = {
                "first_name": lead.first_name or lead.name or "Customer",
                "last_name": lead.last_name or "",
                "phone_number": validated_phone,
                "address": lead.address or "Address not provided",
                "project_info": lead.service_requested or "General inquiry",
                "custom_prompt": agent.prompt_template or self._get_default_prompt(lead)
            }

            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }

            logger.info(f"Dispatching call {call.id} to web service: {self.web_service_url}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

            # Make the HTTP request
            timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.web_service_url,
                    json=payload,
                    headers=headers
                ) as response:

                    response_text = await response.text()
                    logger.info(f"Web service response status: {response.status}")
                    logger.debug(f"Web service response: {response_text}")

                    if response.status == 200:
                        # Parse response if it's JSON
                        try:
                            response_data = await response.json()
                            logger.info(f"Call dispatch successful: {response_data}")
                        except json.JSONDecodeError:
                            logger.info(f"Call dispatch successful (non-JSON response): {response_text}")
                            response_data = {"message": response_text}

                        # Update call status to in_progress
                        call.call_status = "in_progress"
                        call.answered_at = datetime.utcnow()
                        call.call_metadata = {
                            "web_service_response": response_data,
                            "phone_number": validated_phone,
                            "lead_id": str(lead.id),
                            "call_id": str(call.id),
                            "call_type": "sales_outbound",
                            "customer_info": {
                                "first_name": lead.first_name or lead.name or "Customer",
                                "last_name": lead.last_name or "",
                                "address": lead.address or "Unknown",
                                "service_requested": lead.service_requested or "Home services"
                            },
                            "initiated_via": "web_service",
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": lead.source
                        }
                        self.db.commit()

                        logger.info(f"Web service dispatch successful for call {call.id}")
                        return True
                    else:
                        logger.error(f"Web service API error: {response.status} - {response_text}")
                        call.call_status = "failed"
                        call.error_message = f"Web service error: {response.status} - {response_text}"
                        call.ended_at = datetime.utcnow()
                        self.db.commit()
                        return False

        except asyncio.TimeoutError:
            logger.error(f"Web service request timeout for call {call.id}")
            call.call_status = "failed"
            call.error_message = "Web service request timeout"
            call.ended_at = datetime.utcnow()
            self.db.commit()
            return False
        except Exception as e:
            logger.error(f"Web service API dispatch failed: {str(e)}")
            call.call_status = "failed"
            call.error_message = f"Web service dispatch error: {str(e)}"
            call.ended_at = datetime.utcnow()
            self.db.commit()
            return False

    def _get_default_prompt(self, lead: Lead) -> str:
        """
        Get default prompt for outbound calling if agent doesn't have one.
        """
        return f"""
        You are Sarah, a professional sales consultant calling about {lead.service_requested or 'home services'}.
        You are calling {lead.first_name or lead.name or 'the customer'} who submitted a request on our website.

        Be professional, friendly, and focused on understanding their needs and scheduling a consultation.
        Always confirm details and repeat back what you hear.

        Introduction: "Hi, this is Sarah calling about your recent inquiry for {lead.service_requested or 'our services'}.
        Do you have a few minutes to discuss your project?"
        """

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
            "error": call.error_message,
            "dispatched_via": "web_service"
        }

    def can_call_lead(self, lead: Lead) -> tuple[bool, str]:
        """
        Check if a lead can be called based on source restrictions.
        """
        if not lead.phone:
            return False, "Lead has no phone number"

        # Only allow calls for 'torkin' source leads
        if lead.source != "torkin":
            return False, "Only 'torkin' source leads can be called via web service"

        # Check for existing active calls
        existing_call = self.db.query(Call).filter(
            Call.lead_id == lead.id,
            Call.call_status.in_(["pending", "calling", "in_progress"])
        ).first()

        if existing_call:
            return False, f"Call already in progress (Call ID: {existing_call.id})"

        return True, "Lead can be called via web service"