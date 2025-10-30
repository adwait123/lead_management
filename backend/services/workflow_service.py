"""
Workflow Service for handling agent trigger detection and session management
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from models.agent import Agent
from models.lead import Lead
from models.agent_session import AgentSession

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for managing workflow triggers and agent session creation"""

    def __init__(self, db: Session):
        self.db = db

    def detect_and_execute_triggers(self, event_type: str, event_data: Dict[str, Any]) -> List[int]:
        """
        Detect matching triggers and execute them by creating agent sessions

        Args:
            event_type: Type of event (new_lead, form_submission, etc.)
            event_data: Data associated with the event (lead_id, form_data, etc.)

        Returns:
            List of created session IDs
        """
        logger.info(f"Processing event: {event_type} with data: {event_data}")

        # Extract lead source from event data
        lead_source = event_data.get('source')

        # Find agents with matching triggers
        matching_agents = self._find_matching_agents(event_type, lead_source)

        if not matching_agents:
            logger.info(f"No agents found with trigger for event type: {event_type} and lead source: {lead_source}")
            return []

        # Filter agents based on lead-agent compatibility
        compatible_agents = self._filter_compatible_agents(matching_agents, event_data)

        if not compatible_agents:
            logger.warning(f"No compatible agents found for event {event_type}. Original matches: {len(matching_agents)}")
            # Fall back to original matching agents if no compatible ones found
            compatible_agents = matching_agents

        matching_agents = compatible_agents

        created_sessions = []

        for agent in matching_agents:
            try:
                session_id = self._create_agent_session(agent, event_type, event_data)
                if session_id:
                    created_sessions.append(session_id)
                    logger.info(f"Created session {session_id} for agent {agent.id} on event {event_type}")
            except Exception as e:
                logger.error(f"Failed to create session for agent {agent.id}: {str(e)}")
                continue

        return created_sessions

    def _find_matching_agents(self, event_type: str, lead_source: str = None) -> List[Agent]:
        """Find agents that have triggers matching the event type and lead source"""

        # Get all active agents
        agents = self.db.query(Agent).filter(Agent.is_active == True).all()

        matching_agents = []

        for agent in agents:
            if self._agent_has_matching_trigger(agent, event_type, lead_source):
                matching_agents.append(agent)

        # Prioritize agents with workflow steps (follow-up sequences) over those without
        # This ensures that agents with follow-up capabilities are selected first
        matching_agents.sort(key=lambda agent: (
            len(agent.workflow_steps or []) > 0,  # True for agents with workflow steps (sorts first)
            -len(agent.workflow_steps or []),     # More workflow steps preferred
            agent.id                              # Consistent ordering for same capabilities
        ), reverse=True)

        logger.info(f"Found {len(matching_agents)} matching agents for event {event_type}")
        for agent in matching_agents:
            workflow_count = len(agent.workflow_steps or [])
            logger.info(f"  Agent {agent.id} ({agent.name}): {workflow_count} workflow steps")

        return matching_agents

    def _agent_has_matching_trigger(self, agent: Agent, event_type: str, lead_source: str = None) -> bool:
        """Check if an agent has a trigger that matches the event type and lead source"""

        if not agent.triggers:
            return False

        for trigger in agent.triggers:
            # Handle different trigger formats
            if isinstance(trigger, dict):
                trigger_event = trigger.get('event') or trigger.get('type') or trigger.get('event_type')
            else:
                trigger_event = trigger

            if trigger_event == event_type:
                # Check lead source filtering if specified
                if isinstance(trigger, dict):
                    allowed_sources = trigger.get('lead_sources') or trigger.get('sources')

                    if allowed_sources and lead_source:
                        # If agent specifies allowed sources, lead source must match
                        if isinstance(allowed_sources, list):
                            if lead_source not in allowed_sources:
                                continue  # This trigger doesn't match the lead source
                        elif isinstance(allowed_sources, str):
                            if lead_source != allowed_sources:
                                continue  # This trigger doesn't match the lead source

                # Check if trigger has additional conditions
                if isinstance(trigger, dict) and 'condition' in trigger:
                    # TODO: Implement condition evaluation logic
                    # For now, we'll assume conditions pass
                    logger.debug(f"Trigger condition found but not evaluated: {trigger.get('condition')}")

                return True

        return False

    def _filter_compatible_agents(self, agents: List[Agent], event_data: Dict[str, Any]) -> List[Agent]:
        """Filter agents based on lead-agent compatibility (phone availability vs agent capabilities)"""
        from models.lead import Lead

        # Get lead data to check phone availability
        lead_id = event_data.get('lead_id')
        if not lead_id:
            logger.debug("No lead_id in event_data, returning all agents")
            return agents

        try:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                logger.warning(f"Lead {lead_id} not found in database, returning all agents")
                return agents

            has_phone = bool(lead.phone and lead.phone.strip())
            logger.info(f"Lead {lead_id} phone availability: {has_phone}")

            if not has_phone:
                # Lead has no phone - only return text-enabled agents
                compatible_agents = []
                for agent in agents:
                    text_enabled = agent.conversation_settings.get("text_enabled", True) if agent.conversation_settings else True
                    if text_enabled:
                        compatible_agents.append(agent)
                        logger.info(f"Agent {agent.id} ({agent.name}) is text-enabled, compatible with phoneless lead")
                    else:
                        logger.info(f"Agent {agent.id} ({agent.name}) is voice-only, incompatible with phoneless lead")

                if compatible_agents:
                    logger.info(f"Filtered to {len(compatible_agents)} text-enabled agents for phoneless lead")
                    return compatible_agents
                else:
                    logger.warning("No text-enabled agents found for phoneless lead, returning all agents as fallback")
                    return agents
            else:
                # Lead has phone - all agents are compatible
                logger.info(f"Lead {lead_id} has phone number, all {len(agents)} agents are compatible")
                return agents

        except Exception as e:
            logger.error(f"Error checking lead-agent compatibility: {str(e)}")
            return agents  # Return all agents on error

    def _create_agent_session(self, agent: Agent, event_type: str, event_data: Dict[str, Any]) -> Optional[int]:
        """Create an agent session for the triggered agent"""

        # Extract lead_id from event data
        lead_id = event_data.get('lead_id')
        if not lead_id:
            logger.error(f"No lead_id found in event data for {event_type}")
            return None

        # Validate lead exists
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return None

        # Check if lead already has an active session
        existing_session = self.db.query(AgentSession).filter(
            AgentSession.lead_id == lead_id,
            AgentSession.session_status == "active"
        ).first()

        if existing_session:
            logger.warning(f"Lead {lead_id} already has active session {existing_session.id}")
            return None

        # Determine session goal based on agent type/use case
        session_goal = self._determine_session_goal(agent, event_type)

        # Create the session
        session = AgentSession(
            agent_id=agent.id,
            lead_id=lead_id,
            trigger_type=event_type,
            session_goal=session_goal,
            initial_context=event_data,
            auto_timeout_hours=getattr(agent, 'auto_timeout_hours', 48),
            max_message_count=getattr(agent, 'max_message_count', 100)
        )

        try:
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            # Set up follow-up sequences if agent has workflow steps
            self._setup_follow_up_sequences(session, agent)

            # Handle agent-specific initialization based on type
            if agent.type == "outbound":
                # Check agent's communication preference
                text_enabled = agent.conversation_settings.get("text_enabled", True) if agent.conversation_settings else True

                if text_enabled:
                    # Text-only outbound agent: skip calling, send message immediately
                    logger.info(f"Outbound agent {agent.id} is text-enabled, sending message directly")
                    self._trigger_initial_message_generation(session.id, lead, event_data)
                else:
                    # Voice-only outbound agent: only make calls, no text fallback
                    logger.info(f"Outbound agent {agent.id} is voice-only, attempting call")
                    self._trigger_outbound_call(session.id, lead, agent)
            elif agent.type == "inbound" or agent.type == "conversational":
                # Check if agent is configured for text messages
                text_enabled = agent.conversation_settings.get("text_enabled", True) if agent.conversation_settings else True
                if text_enabled:
                    # Text-enabled agents should generate initial messages
                    self._trigger_initial_message_generation(session.id, lead, event_data)
                else:
                    # Voice-only agents should not generate text messages
                    logger.info(f"Agent {agent.id} ({agent.name}) is voice-only (text_enabled=false), skipping text message generation")
            else:
                logger.warning(f"Unknown agent type '{agent.type}' for agent {agent.id}, defaulting to message generation")
                self._trigger_initial_message_generation(session.id, lead, event_data)

            return session.id
        except Exception as e:
            self.db.rollback()
            logger.error(f"Database error creating session: {str(e)}")
            return None

    def _determine_session_goal(self, agent: Agent, event_type: str) -> str:
        """Determine session goal based on agent and trigger type"""

        # Map agent use cases to session goals
        use_case_goals = {
            "lead_qualification": "qualify_lead",
            "customer_support": "provide_support",
            "general_sales": "close_lead",
            "appointment_booking": "book_appointment",
            "follow_up": "follow_up_lead"
        }

        # Map event types to session goals
        event_type_goals = {
            "new_lead": "qualify_lead",
            "form_submission": "qualify_lead",
            "email_opened": "follow_up_lead",
            "website_visit": "engage_visitor",
            "meeting_scheduled": "prepare_meeting",
            "support_ticket": "provide_support"
        }

        # Use agent use case first, then event type, then default
        goal = use_case_goals.get(agent.use_case)
        if not goal:
            goal = event_type_goals.get(event_type, "engage_lead")

        return goal

    def handle_lead_created(self, lead_id: int, source: str = None, form_data: Dict[str, Any] = None) -> List[int]:
        """Handle new lead creation event"""

        event_data = {
            "lead_id": lead_id,
            "source": source,
            "form_data": form_data or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        return self.detect_and_execute_triggers("new_lead", event_data)

    def handle_form_submission(self, lead_id: int, form_type: str, form_data: Dict[str, Any]) -> List[int]:
        """Handle form submission event"""

        event_data = {
            "lead_id": lead_id,
            "form_type": form_type,
            "form_data": form_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        return self.detect_and_execute_triggers("form_submission", event_data)

    def handle_email_opened(self, lead_id: int, email_id: str = None) -> List[int]:
        """Handle email opened event"""

        event_data = {
            "lead_id": lead_id,
            "email_id": email_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        return self.detect_and_execute_triggers("email_opened", event_data)

    def handle_website_visit(self, lead_id: int, page_url: str = None, duration: int = None) -> List[int]:
        """Handle website visit event"""

        event_data = {
            "lead_id": lead_id,
            "page_url": page_url,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat()
        }

        return self.detect_and_execute_triggers("website_visit", event_data)

    def handle_meeting_scheduled(self, lead_id: int, meeting_time: str, meeting_type: str = None) -> List[int]:
        """Handle meeting scheduled event"""

        event_data = {
            "lead_id": lead_id,
            "meeting_time": meeting_time,
            "meeting_type": meeting_type,
            "timestamp": datetime.utcnow().isoformat()
        }

        return self.detect_and_execute_triggers("meeting_scheduled", event_data)

    def handle_support_ticket(self, lead_id: int, ticket_id: str, issue_type: str = None) -> List[int]:
        """Handle support ticket creation event"""

        event_data = {
            "lead_id": lead_id,
            "ticket_id": ticket_id,
            "issue_type": issue_type,
            "timestamp": datetime.utcnow().isoformat()
        }

        return self.detect_and_execute_triggers("support_ticket", event_data)

    def get_agent_trigger_summary(self, agent_id: int) -> Dict[str, Any]:
        """Get summary of triggers configured for an agent"""

        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return {"error": "Agent not found"}

        trigger_summary = {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "is_active": agent.is_active,
            "triggers": [],
            "trigger_count": 0
        }

        if agent.triggers:
            for trigger in agent.triggers:
                if isinstance(trigger, dict):
                    trigger_info = {
                        "event": trigger.get('event') or trigger.get('type') or trigger.get('event_type'),
                        "condition": trigger.get('condition') or trigger.get('conditions'),
                        "active": trigger.get('active', True)
                    }
                else:
                    trigger_info = {
                        "event": trigger,
                        "condition": None,
                        "active": True
                    }

                trigger_summary["triggers"].append(trigger_info)

            trigger_summary["trigger_count"] = len(agent.triggers)

        return trigger_summary

    def _trigger_initial_message_generation(self, session_id: int, lead: Lead, event_data: Dict[str, Any]):
        """Trigger initial message generation for a new agent session"""
        try:
            # Import here to avoid circular imports
            from services.agent_service import AgentService
            from models.database import SessionLocal
            import asyncio

            # Create agent service with a new DB session to avoid conflicts
            new_db = SessionLocal()
            agent_service = AgentService(new_db)

            # Extract project details from event data for context
            project_details = event_data.get('form_data', {})

            # Build lead data dictionary
            lead_data = {
                "id": lead.id,
                "name": lead.name,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "email": lead.email,
                "phone": lead.phone,
                "company": lead.company,
                "service_requested": lead.service_requested,
                "source": lead.source
            }

            # Schedule async message generation
            # Note: We run this in a background task to avoid blocking the webhook response
            asyncio.create_task(
                self._generate_initial_message_async(
                    agent_service, new_db, session_id, lead_data, project_details
                )
            )

            logger.info(f"Scheduled initial message generation for session {session_id}")

        except Exception as e:
            logger.error(f"Error triggering initial message generation for session {session_id}: {str(e)}")

    async def _generate_initial_message_async(
        self,
        agent_service: 'AgentService',
        db_session: Session,
        session_id: int,
        lead_data: Dict[str, Any],
        project_details: Dict[str, Any]
    ):
        """Asynchronously generate the initial message"""
        try:
            logger.info(f"Starting initial message generation for session {session_id}")

            # Generate the initial message
            message = await agent_service.generate_initial_message(
                agent_session_id=session_id,
                lead_data=lead_data,
                project_details=project_details
            )

            if message:
                logger.info(f"Successfully generated initial message {message.id} for session {session_id}")
            else:
                logger.error(f"Failed to generate initial message for session {session_id}")

        except Exception as e:
            logger.error(f"Error in async initial message generation for session {session_id}: {str(e)}")
        finally:
            # Always close the database session to prevent leaks
            try:
                db_session.close()
                logger.debug(f"Closed database session for initial message generation {session_id}")
            except Exception as e:
                logger.error(f"Error closing database session: {str(e)}")

    def _trigger_outbound_call(self, session_id: int, lead: Lead, agent: Agent) -> bool:
        """Trigger outbound call for outbound-type agents. Returns True if successful, False if failed."""
        try:
            logger.info(f"Triggering outbound call for session {session_id}, lead {lead.id}, agent {agent.id}")

            # Check if lead has a valid phone number
            if not lead.phone:
                logger.error(f"Cannot trigger outbound call for lead {lead.id}: No phone number")
                return False

            # Import here to avoid circular imports
            from models.call import Call
            from services.outbound_web_service import OutboundWebService
            from models.database import SessionLocal
            import asyncio

            # Create a new database session for call operations
            new_db = SessionLocal()

            try:
                # Create call record
                call = Call(
                    lead_id=lead.id,
                    agent_id=agent.id,
                    phone_number=lead.phone,
                    call_status="pending",
                    call_metadata={
                        "agent_session_id": session_id,
                        "triggered_by": "workflow",
                        "agent_name": agent.name,
                        "auto_triggered": True,
                        "lead_source": lead.source,
                        "service_requested": lead.service_requested
                    }
                )

                new_db.add(call)
                new_db.commit()
                new_db.refresh(call)

                logger.info(f"Created call record {call.id} for session {session_id}")

                # Dispatch the call using OutboundWebService
                web_service = OutboundWebService(new_db)
                asyncio.create_task(web_service.dispatch_call(call.id))

                logger.info(f"Scheduled outbound call dispatch for call {call.id}, session {session_id}")
                return True  # Success

            except Exception as e:
                new_db.rollback()
                logger.error(f"Error creating call record for session {session_id}: {str(e)}")
                return False  # Failed to create call record
            finally:
                new_db.close()

        except Exception as e:
            logger.error(f"Error triggering outbound call for session {session_id}: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False  # Failed due to exception

    def _setup_follow_up_sequences(self, session: AgentSession, agent: Agent):
        """Set up follow-up sequences for the agent session based on agent workflow steps"""
        try:
            logger.info(f"Setting up follow-up sequences for session {session.id} with agent {agent.id}")

            # Check if agent has workflow steps with follow-up sequences
            if not agent.workflow_steps:
                logger.info(f"No workflow steps found for agent {agent.id}")
                return

            logger.info(f"Agent {agent.id} has {len(agent.workflow_steps)} workflow steps")

            # Import follow-up scheduler here to avoid circular imports
            from services.follow_up_scheduler import FollowUpScheduler

            # Filter workflow steps for follow-up sequences
            follow_up_steps = []
            for i, step in enumerate(agent.workflow_steps):
                logger.debug(f"Processing workflow step {i+1}: {step}")
                if isinstance(step, dict) and step.get("type") == "time_based_trigger":
                    trigger = step.get("trigger", {})
                    if trigger.get("event") == "no_response":
                        follow_up_steps.append(step)
                        logger.info(f"Found follow-up step: {step}")

            if not follow_up_steps:
                logger.warning(f"No follow-up sequences found in workflow steps for agent {agent.id}")
                logger.debug(f"Workflow steps were: {agent.workflow_steps}")
                return

            logger.info(f"Found {len(follow_up_steps)} follow-up steps for agent {agent.id}")

            # Sort by sequence position
            follow_up_steps.sort(key=lambda x: x.get("sequence_position", 0))

            # Create follow-up scheduler and schedule the sequence
            logger.info(f"Creating FollowUpScheduler and scheduling sequence for session {session.id}")
            scheduler = FollowUpScheduler(self.db)
            created_task_ids = scheduler.schedule_follow_up_sequence(
                agent_session_id=session.id,
                trigger_event="no_response"
            )

            if created_task_ids:
                logger.info(f"Successfully scheduled {len(created_task_ids)} follow-up tasks for session {session.id}")
            else:
                logger.error(f"Failed to schedule follow-up sequence for session {session.id}")

        except Exception as e:
            logger.error(f"Error setting up follow-up sequences for session {session.id}: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")