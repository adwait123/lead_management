"""
Webhook Service for sending notifications to external systems
"""
import logging
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from models.lead import Lead
from models.agent_session import AgentSession
from models.agent import Agent

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for sending webhook notifications to external systems"""

    def __init__(self, db: Session):
        self.db = db
        # Default webhook URL - can be configured via environment variables
        self.webhook_urls = [
            "https://www.postb.in/1760299453060-7508493557106"  # Active PostBin for webhook testing
        ]

    async def send_agent_message_webhook(
        self,
        session_id: int,
        message_content: str,
        message_type: str = "agent_response"
    ) -> List[bool]:
        """
        Send webhook notification when agent sends a message

        Args:
            session_id: Agent session ID
            message_content: Content of the agent message
            message_type: Type of message (agent_response, follow_up, etc.)

        Returns:
            List of success status for each webhook URL
        """
        try:
            # Refresh database session to ensure we have latest data
            self.db.commit()

            # Get session, lead, and agent data
            session = self.db.query(AgentSession).filter(AgentSession.id == session_id).first()
            if not session:
                logger.error(f"Session {session_id} not found")
                return [False]

            lead = self.db.query(Lead).filter(Lead.id == session.lead_id).first()
            if not lead:
                logger.error(f"Lead {session.lead_id} not found for session {session_id}")
                return [False]

            agent = self.db.query(Agent).filter(Agent.id == session.agent_id).first()
            if not agent:
                logger.error(f"Agent {session.agent_id} not found for session {session_id}")
                return [False]

            # Log webhook data for debugging
            logger.info(f"Webhook data - Session ID: {session_id}, Lead: {lead.name}, Agent: {agent.name}, Message: {message_content[:100]}")
            logger.info(f"Lead details - ID: {lead.id}, External ID: {lead.external_id}, Email: {lead.email}")

            # Build webhook payload with explicit JSON serialization
            payload = {
                "event_type": "agent_message_sent",
                "timestamp": datetime.utcnow().isoformat(),
                "message": {
                    "content": str(message_content) if message_content else "",
                    "type": str(message_type) if message_type else "",
                    "session_id": int(session_id) if session_id else 0
                },
                "lead": {
                    "id": int(lead.id) if lead.id else 0,
                    "name": str(lead.name) if lead.name else "",
                    "first_name": str(lead.first_name) if lead.first_name else "",
                    "last_name": str(lead.last_name) if lead.last_name else "",
                    "email": str(lead.email) if lead.email else "",
                    "phone": str(lead.phone) if lead.phone else "",
                    "company": str(lead.company) if lead.company else "",
                    "address": str(lead.address) if lead.address else "",
                    "external_id": str(lead.external_id) if lead.external_id else "",
                    "service_requested": str(lead.service_requested) if lead.service_requested else "",
                    "status": str(lead.status) if lead.status else "",
                    "source": str(lead.source) if lead.source else ""
                },
                "agent": {
                    "id": int(agent.id) if agent.id else 0,
                    "name": str(agent.name) if agent.name else "",
                    "type": str(agent.type) if agent.type else "",
                    "use_case": str(agent.use_case) if agent.use_case else ""
                },
                "session": {
                    "id": int(session.id) if session.id else 0,
                    "trigger_type": str(session.trigger_type) if session.trigger_type else "",
                    "session_status": str(session.session_status) if session.session_status else "",
                    "session_goal": str(session.session_goal) if session.session_goal else "",
                    "message_count": int(session.message_count) if session.message_count else 0
                }
            }

            # Log the full payload for debugging
            logger.info(f"Webhook payload: {json.dumps(payload, indent=2)}")

            # Send to all configured webhook URLs
            results = []
            for webhook_url in self.webhook_urls:
                success = await self._send_webhook(webhook_url, payload)
                results.append(success)

            return results

        except Exception as e:
            logger.error(f"Error sending agent message webhook for session {session_id}: {str(e)}")
            return [False] * len(self.webhook_urls)

    async def send_lead_created_webhook(self, lead_id: int) -> List[bool]:
        """
        Send webhook notification when a new lead is created

        Args:
            lead_id: ID of the created lead

        Returns:
            List of success status for each webhook URL
        """
        try:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                logger.error(f"Lead {lead_id} not found")
                return [False]

            payload = {
                "event_type": "lead_created",
                "timestamp": datetime.utcnow().isoformat(),
                "lead": {
                    "id": lead.id,
                    "name": lead.name,
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "email": lead.email,
                    "phone": lead.phone,
                    "company": lead.company,
                    "address": lead.address,
                    "external_id": lead.external_id,
                    "service_requested": lead.service_requested,
                    "status": lead.status,
                    "source": lead.source,
                    "created_at": lead.created_at.isoformat() if lead.created_at else None
                }
            }

            # Send to all configured webhook URLs
            results = []
            for webhook_url in self.webhook_urls:
                success = await self._send_webhook(webhook_url, payload)
                results.append(success)

            return results

        except Exception as e:
            logger.error(f"Error sending lead created webhook for lead {lead_id}: {str(e)}")
            return [False] * len(self.webhook_urls)

    async def _send_webhook(self, webhook_url: str, payload: Dict[str, Any]) -> bool:
        """
        Send HTTP POST request to webhook URL

        Args:
            webhook_url: URL to send webhook to
            payload: Data to send

        Returns:
            Success status
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "AILead-Webhook-Service/1.0"
            }

            timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status >= 200 and response.status < 300:
                        logger.info(f"Successfully sent webhook to {webhook_url} (status: {response.status})")
                        return True
                    else:
                        logger.warning(f"Webhook to {webhook_url} failed with status {response.status}")
                        return False

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error sending webhook to {webhook_url}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending webhook to {webhook_url}: {str(e)}")
            return False

    def add_webhook_url(self, webhook_url: str):
        """Add a new webhook URL to the configuration"""
        if webhook_url not in self.webhook_urls:
            self.webhook_urls.append(webhook_url)
            logger.info(f"Added webhook URL: {webhook_url}")

    def remove_webhook_url(self, webhook_url: str):
        """Remove a webhook URL from the configuration"""
        if webhook_url in self.webhook_urls:
            self.webhook_urls.remove(webhook_url)
            logger.info(f"Removed webhook URL: {webhook_url}")

    def get_webhook_urls(self) -> List[str]:
        """Get list of configured webhook URLs"""
        return self.webhook_urls.copy()

    async def test_webhook(self, webhook_url: str) -> bool:
        """
        Test a webhook URL with a sample payload

        Args:
            webhook_url: URL to test

        Returns:
            Success status
        """
        test_payload = {
            "event_type": "webhook_test",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "This is a test webhook from AILead system"
        }

        return await self._send_webhook(webhook_url, test_payload)