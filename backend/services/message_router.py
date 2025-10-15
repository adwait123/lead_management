"""
Message Router Service for handling conversation routing to active agent sessions
"""
import logging
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from datetime import datetime

from models.agent_session import AgentSession
from models.agent import Agent
from models.lead import Lead
from models.message import Message

logger = logging.getLogger(__name__)


class MessageRouter:
    """Service for routing messages to appropriate agent sessions"""

    def __init__(self, db: Session):
        self.db = db

    def route_message(self, lead_id: int, message: str, message_type: str = "text",
                     metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Route an incoming message to the appropriate agent session and persist it

        Args:
            lead_id: ID of the lead sending the message
            message: The message content
            message_type: Type of message (text, voice, etc.)
            metadata: Additional metadata about the message

        Returns:
            Dictionary with routing information and next steps
        """
        try:
            # Find active session for this lead
            active_session = self._get_active_session(lead_id)

            if active_session:
                # Route to existing session and persist message
                result = self._route_to_existing_session(active_session, message, message_type, metadata)
                if result["success"]:
                    # Persist the incoming message
                    self._persist_incoming_message(active_session, lead_id, message, message_type, metadata)
            else:
                # No active session - determine if we should create one
                result = self._handle_new_conversation(lead_id, message, message_type, metadata)
                if result["success"] and result.get("session_id"):
                    # Persist the incoming message to the new session
                    new_session = self.db.query(AgentSession).filter(AgentSession.id == result["session_id"]).first()
                    if new_session:
                        self._persist_incoming_message(new_session, lead_id, message, message_type, metadata)

            return result

        except Exception as e:
            logger.error(f"Error routing message for lead {lead_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "routing_decision": "error",
                "should_respond": False
            }

    def _get_active_session(self, lead_id: int) -> Optional[AgentSession]:
        """Get the active agent session for a lead (includes taken_over sessions)"""
        return self.db.query(AgentSession).filter(
            AgentSession.lead_id == lead_id,
            AgentSession.session_status.in_(["active", "taken_over"])
        ).first()

    def _route_to_existing_session(self, session: AgentSession, message: str,
                                 message_type: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Route message to an existing active session"""

        # Update session message statistics
        session.update_message_stats(from_agent=False)

        # Check if session should be escalated due to message count
        if session.should_escalate():
            return self._escalate_session(session, "max_message_count_reached")

        # Check if session has timed out
        if session.is_timeout_eligible():
            return self._timeout_session(session)

        try:
            self.db.commit()

            # Handle follow-up sequence cancellation when lead responds
            self._handle_lead_response_follow_up(session)

            # Get agent information
            agent = self.db.query(Agent).filter(Agent.id == session.agent_id).first()
            lead = self.db.query(Lead).filter(Lead.id == session.lead_id).first()

            # Check if session is taken over by business owner
            is_taken_over = session.session_status == "taken_over"
            should_respond = not is_taken_over  # Agent should not respond if taken over

            return {
                "success": True,
                "routing_decision": "existing_session_taken_over" if is_taken_over else "existing_session",
                "session_id": session.id,
                "agent_id": session.agent_id,
                "agent_name": agent.name if agent else "Unknown",
                "lead_name": lead.name if lead else "Unknown",
                "message_count": session.message_count,
                "session_goal": session.session_goal,
                "should_respond": should_respond,
                "taken_over": is_taken_over,
                "agent_context": {
                    "session_goal": session.session_goal,
                    "message_count": session.message_count,
                    "session_created": session.created_at.isoformat() if session.created_at else None,
                    "initial_context": session.initial_context,
                    "trigger_type": session.trigger_type,
                    "taken_over": is_taken_over
                }
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating session {session.id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "routing_decision": "error",
                "should_respond": False
            }

    def _handle_new_conversation(self, lead_id: int, message: str,
                               message_type: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle a new conversation when no active session exists"""

        # Check if this should trigger a new agent session
        # For now, we'll look for agents with "new_lead" or general triggers
        potential_agents = self._find_agents_for_new_conversation(lead_id)

        if not potential_agents:
            return {
                "success": True,
                "routing_decision": "no_agent_available",
                "should_respond": False,
                "message": "No agents configured to handle new conversations"
            }

        # Use the first available agent (could be enhanced with priority logic)
        agent = potential_agents[0]

        # Create new session
        try:
            session = AgentSession(
                agent_id=agent.id,
                lead_id=lead_id,
                trigger_type="message_received",  # Different from workflow triggers
                session_goal=self._determine_session_goal_from_message(message, agent),
                initial_context={
                    "first_message": message,
                    "message_type": message_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": metadata or {}
                }
            )

            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            # Update with first message
            session.update_message_stats(from_agent=False)
            self.db.commit()

            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()

            logger.info(f"Created new session {session.id} for lead {lead_id} with agent {agent.id}")

            return {
                "success": True,
                "routing_decision": "new_session_created",
                "session_id": session.id,
                "agent_id": agent.id,
                "agent_name": agent.name,
                "lead_name": lead.name if lead else "Unknown",
                "message_count": session.message_count,
                "session_goal": session.session_goal,
                "should_respond": True,
                "agent_context": {
                    "session_goal": session.session_goal,
                    "message_count": session.message_count,
                    "session_created": session.created_at.isoformat() if session.created_at else None,
                    "initial_context": session.initial_context,
                    "trigger_type": session.trigger_type,
                    "is_new_session": True
                }
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating new session: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "routing_decision": "error",
                "should_respond": False
            }

    def _find_agents_for_new_conversation(self, lead_id: int) -> list[Agent]:
        """Find agents that can handle new conversations for this specific lead"""

        # Get lead information to check source
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return []

        # Get all active agents
        agents = self.db.query(Agent).filter(Agent.is_active == True).all()

        suitable_agents = []

        for agent in agents:
            # Check if agent has triggers that would handle new conversations
            if self._agent_can_handle_new_conversation(agent, lead.source):
                suitable_agents.append(agent)

        if not suitable_agents:
            logger.warning(f"No suitable agents found for lead {lead_id} with source '{lead.source}'")

        # Sort by priority (could be enhanced with agent ranking logic)
        # For now, prioritize by use case
        priority_order = ["general_sales", "lead_qualification", "customer_support"]

        def get_priority(agent):
            try:
                return priority_order.index(agent.use_case)
            except ValueError:
                return len(priority_order)  # Put unknown use cases at the end

        suitable_agents.sort(key=get_priority)

        return suitable_agents

    def _agent_can_handle_new_conversation(self, agent: Agent, lead_source: str = None) -> bool:
        """Check if an agent can handle new conversations based on its triggers and lead source"""

        if not agent.triggers:
            # If no specific triggers, assume it can handle general conversations
            return True

        # Check for conversation-related triggers
        conversation_triggers = {"new_lead", "form_submission", "website_visit", "general", "message_received"}

        for trigger in agent.triggers:
            if isinstance(trigger, dict):
                trigger_event = trigger.get('event') or trigger.get('type') or trigger.get('event_type')

                # Check if this trigger matches conversation events
                if trigger_event in conversation_triggers:
                    # Check lead source filtering if specified
                    allowed_sources = trigger.get('lead_sources') or trigger.get('sources')

                    if allowed_sources:
                        # If agent specifies allowed sources, lead source must match
                        if isinstance(allowed_sources, list):
                            return lead_source in allowed_sources
                        elif isinstance(allowed_sources, str):
                            return lead_source == allowed_sources
                    else:
                        # No source filtering, agent accepts all sources
                        return True
            else:
                # Simple string trigger - check if it's a conversation trigger
                trigger_event = trigger
                if trigger_event in conversation_triggers:
                    # String triggers don't have source filtering, accept all
                    return True

        return False

    def _determine_session_goal_from_message(self, message: str, agent: Agent) -> str:
        """Determine session goal based on the first message and agent type"""

        message_lower = message.lower()

        # Simple keyword-based goal detection (could be enhanced with NLP)
        if any(word in message_lower for word in ["price", "cost", "quote", "estimate"]):
            return "provide_pricing"
        elif any(word in message_lower for word in ["schedule", "appointment", "meeting", "call"]):
            return "book_appointment"
        elif any(word in message_lower for word in ["support", "help", "problem", "issue"]):
            return "provide_support"
        elif any(word in message_lower for word in ["info", "information", "learn", "tell me"]):
            return "provide_information"
        else:
            # Default based on agent use case
            use_case_goals = {
                "lead_qualification": "qualify_lead",
                "customer_support": "provide_support",
                "general_sales": "close_lead",
                "appointment_booking": "book_appointment"
            }
            return use_case_goals.get(agent.use_case, "engage_lead")

    def _escalate_session(self, session: AgentSession, reason: str) -> Dict[str, Any]:
        """Escalate a session that has reached limits"""

        session.session_status = "escalated"
        session.completion_reason = reason
        session.ended_at = datetime.utcnow()

        try:
            self.db.commit()
            logger.info(f"Escalated session {session.id} due to: {reason}")

            return {
                "success": True,
                "routing_decision": "session_escalated",
                "session_id": session.id,
                "escalation_reason": reason,
                "should_respond": True,
                "escalation_message": "This conversation has been escalated to a human agent who will assist you shortly."
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error escalating session {session.id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "routing_decision": "error",
                "should_respond": False
            }

    def _timeout_session(self, session: AgentSession) -> Dict[str, Any]:
        """Handle a session that has timed out"""

        session.session_status = "timeout"
        session.completion_reason = "inactivity_timeout"
        session.ended_at = datetime.utcnow()

        try:
            self.db.commit()
            logger.info(f"Timed out session {session.id} due to inactivity")

            # Start a new session for this message
            return self._handle_new_conversation(
                session.lead_id,
                "Session resumed after timeout",
                "text"
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error timing out session {session.id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "routing_decision": "error",
                "should_respond": False
            }

    def get_session_context(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get context information for an active session"""

        session = self.db.query(AgentSession).filter(AgentSession.id == session_id).first()
        if not session:
            return None

        agent = self.db.query(Agent).filter(Agent.id == session.agent_id).first()
        lead = self.db.query(Lead).filter(Lead.id == session.lead_id).first()

        return {
            "session_id": session.id,
            "agent": {
                "id": agent.id if agent else None,
                "name": agent.name if agent else "Unknown",
                "use_case": agent.use_case if agent else None,
                "prompt_template": agent.prompt_template if agent else None
            },
            "lead": {
                "id": lead.id if lead else None,
                "name": lead.name if lead else "Unknown",
                "email": lead.email if lead else None,
                "company": lead.company if lead else None
            },
            "session": {
                "goal": session.session_goal,
                "message_count": session.message_count,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "initial_context": session.initial_context,
                "trigger_type": session.trigger_type
            }
        }

    def update_agent_response(self, session_id: int, response: str, response_metadata: Dict[str, Any] = None) -> bool:
        """Update session after agent sends a response"""

        session = self.db.query(AgentSession).filter(AgentSession.id == session_id).first()
        if not session:
            return False

        try:
            # Update message stats for agent response
            session.update_message_stats(from_agent=True)

            # Could store response metadata if needed
            if response_metadata:
                current_metadata = session.session_metadata or {}
                current_metadata.update(response_metadata)
                session.session_metadata = current_metadata

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating agent response for session {session_id}: {str(e)}")
            return False

    def _persist_incoming_message(
        self,
        session: AgentSession,
        lead_id: int,
        message: str,
        message_type: str,
        metadata: Dict[str, Any] = None
    ) -> Optional[Message]:
        """Persist an incoming message from a lead or business owner"""
        try:
            # Check if this is a business owner message based on metadata
            if metadata and metadata.get("sender") == "business_owner":
                # Create business owner message
                incoming_message = Message.create_business_owner_message(
                    agent_session_id=session.id,
                    lead_id=lead_id,
                    content=message,
                    business_owner_name=metadata.get("business_owner_name"),
                    metadata=metadata or {},
                    external_conversation_id=metadata.get("yelp_conversation_id"),
                    external_platform=metadata.get("platform", "web_ui"),
                    message_type=message_type
                )
            else:
                # Create lead message (default)
                incoming_message = Message.create_lead_message(
                    agent_session_id=session.id,
                    lead_id=lead_id,
                    content=message,
                    metadata=metadata or {},
                    external_conversation_id=metadata.get("yelp_conversation_id") if metadata else None,
                    external_platform=metadata.get("platform") if metadata else None,
                    message_type=message_type
                )

            # Save to database
            self.db.add(incoming_message)
            self.db.commit()
            self.db.refresh(incoming_message)

            logger.info(f"Persisted incoming message {incoming_message.id} for session {session.id}")
            return incoming_message

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error persisting incoming message for session {session.id}: {str(e)}")
            return None

    def get_conversation_history(
        self,
        session_id: int = None,
        lead_id: int = None,
        limit: int = 50,
        include_system_messages: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session or lead

        Args:
            session_id: Filter by agent session ID
            lead_id: Filter by lead ID (if no session_id provided)
            limit: Maximum number of messages to return
            include_system_messages: Whether to include system messages

        Returns:
            List of message dictionaries ordered by creation time
        """
        try:
            query = self.db.query(Message)

            if session_id:
                query = query.filter(Message.agent_session_id == session_id)
            elif lead_id:
                query = query.filter(Message.lead_id == lead_id)
            else:
                logger.error("Either session_id or lead_id must be provided")
                return []

            if not include_system_messages:
                query = query.filter(Message.sender_type != "system")

            messages = query.order_by(Message.created_at.asc()).limit(limit).all()

            return [msg.to_dict() for msg in messages]

        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []

    def get_message_statistics(self, session_id: int) -> Dict[str, Any]:
        """Get message statistics for a session"""
        try:
            # Count messages by sender type
            agent_messages = self.db.query(Message).filter(
                Message.agent_session_id == session_id,
                Message.sender_type == "agent"
            ).count()

            lead_messages = self.db.query(Message).filter(
                Message.agent_session_id == session_id,
                Message.sender_type == "lead"
            ).count()

            system_messages = self.db.query(Message).filter(
                Message.agent_session_id == session_id,
                Message.sender_type == "system"
            ).count()

            # Get first and last message times
            first_message = self.db.query(Message).filter(
                Message.agent_session_id == session_id
            ).order_by(Message.created_at.asc()).first()

            last_message = self.db.query(Message).filter(
                Message.agent_session_id == session_id
            ).order_by(Message.created_at.desc()).first()

            return {
                "session_id": session_id,
                "total_messages": agent_messages + lead_messages + system_messages,
                "agent_messages": agent_messages,
                "lead_messages": lead_messages,
                "system_messages": system_messages,
                "first_message_at": first_message.created_at.isoformat() if first_message else None,
                "last_message_at": last_message.created_at.isoformat() if last_message else None,
                "conversation_duration": None  # Could calculate if needed
            }

        except Exception as e:
            logger.error(f"Error getting message statistics for session {session_id}: {str(e)}")
            return {
                "session_id": session_id,
                "error": str(e)
            }

    def _handle_lead_response_follow_up(self, session: AgentSession):
        """Handle follow-up sequence cancellation when lead responds"""
        try:
            # Import follow-up scheduler here to avoid circular imports
            from services.follow_up_scheduler import FollowUpScheduler

            scheduler = FollowUpScheduler(self.db)
            scheduler.handle_lead_response(session.id)

            logger.debug(f"Processed lead response follow-up for session {session.id}")

        except Exception as e:
            logger.error(f"Error handling lead response follow-up for session {session.id}: {str(e)}")