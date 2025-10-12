"""
Agent Service for generating AI responses and managing agent conversations
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import json

from models.agent import Agent
from models.lead import Lead
from models.agent_session import AgentSession
from models.message import Message
from services.openai_service import get_openai_service

logger = logging.getLogger(__name__)


class AgentService:
    """Service for generating agent responses and managing conversations"""

    def __init__(self, db: Session):
        self.db = db
        self.openai_service = get_openai_service()

    async def generate_initial_message(
        self,
        agent_session_id: int,
        lead_data: Dict[str, Any] = None,
        project_details: Dict[str, Any] = None
    ) -> Optional[Message]:
        """
        Generate the initial greeting message when an agent session is created

        Args:
            agent_session_id: ID of the agent session
            lead_data: Lead information for personalization
            project_details: Project/form data from lead creation

        Returns:
            Message object if successful, None if failed
        """
        try:
            # Get session, agent, and lead information
            session = self.db.query(AgentSession).filter(AgentSession.id == agent_session_id).first()
            if not session:
                logger.error(f"Agent session {agent_session_id} not found")
                return None

            agent = self.db.query(Agent).filter(Agent.id == session.agent_id).first()
            if not agent:
                logger.error(f"Agent {session.agent_id} not found")
                return None

            lead = self.db.query(Lead).filter(Lead.id == session.lead_id).first()
            if not lead:
                logger.error(f"Lead {session.lead_id} not found")
                return None

            # Build context for initial message generation
            context = self._build_initial_message_context(session, agent, lead, project_details)

            # Generate the greeting message
            message_content = await self._generate_greeting_content(agent, context)

            if not message_content:
                logger.error(f"Failed to generate greeting content for session {agent_session_id}")
                return None

            # Create the message record
            message = Message.create_agent_message(
                agent_session_id=agent_session_id,
                lead_id=session.lead_id,
                agent_id=agent.id,
                content=message_content['content'],
                metadata={
                    "is_initial_message": True,
                    "generation_context": context,
                    "message_type": "greeting"
                },
                prompt_used=message_content.get('prompt_used'),
                model_used=message_content.get('model_used'),
                response_time_ms=message_content.get('response_time_ms'),
                token_usage=message_content.get('token_usage'),
                sender_name=agent.name,
                external_platform=lead.source if lead.source else None
            )

            # Save to database
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)

            # Update session statistics
            session.update_message_stats(from_agent=True)
            self.db.commit()

            logger.info(f"Initial message generated for session {agent_session_id}")
            return message

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error generating initial message for session {agent_session_id}: {str(e)}")
            return None

    async def generate_response_message(
        self,
        agent_session_id: int,
        incoming_message: str,
        conversation_history: List[Message] = None,
        context_override: Dict[str, Any] = None
    ) -> Optional[Message]:
        """
        Generate an agent response to an incoming message

        Args:
            agent_session_id: ID of the agent session
            incoming_message: The message to respond to
            conversation_history: Previous messages in conversation
            context_override: Additional context to override defaults

        Returns:
            Message object if successful, None if failed
        """
        try:
            # Get session, agent, and lead information
            session = self.db.query(AgentSession).filter(AgentSession.id == agent_session_id).first()
            if not session:
                logger.error(f"Agent session {agent_session_id} not found")
                return None

            agent = self.db.query(Agent).filter(Agent.id == session.agent_id).first()
            if not agent:
                logger.error(f"Agent {session.agent_id} not found")
                return None

            lead = self.db.query(Lead).filter(Lead.id == session.lead_id).first()
            if not lead:
                logger.error(f"Lead {session.lead_id} not found")
                return None

            # Get conversation history if not provided
            if conversation_history is None:
                conversation_history = self._get_conversation_history(agent_session_id)

            # Build context for response generation
            context = self._build_response_context(
                session, agent, lead, incoming_message, conversation_history, context_override
            )

            # Generate the response
            response_content = await self._generate_response_content(agent, context)

            if not response_content:
                logger.error(f"Failed to generate response content for session {agent_session_id}")
                return None

            # Create the message record
            message = Message.create_agent_message(
                agent_session_id=agent_session_id,
                lead_id=session.lead_id,
                agent_id=agent.id,
                content=response_content['content'],
                metadata={
                    "is_response_to": incoming_message[:100],  # Store snippet of original message
                    "generation_context": context,
                    "message_type": "response"
                },
                prompt_used=response_content.get('prompt_used'),
                model_used=response_content.get('model_used'),
                response_time_ms=response_content.get('response_time_ms'),
                token_usage=response_content.get('token_usage'),
                sender_name=agent.name,
                external_platform=lead.source if lead.source else None
            )

            # Save to database
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)

            # Update session statistics
            session.update_message_stats(from_agent=True)
            self.db.commit()

            logger.info(f"Response message generated for session {agent_session_id}")
            return message

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error generating response message for session {agent_session_id}: {str(e)}")
            return None

    async def generate_follow_up_message(
        self,
        agent_session_id: int,
        template: str,
        template_type: str,
        context: Dict[str, Any] = None
    ) -> Optional[Message]:
        """
        Generate a follow-up message based on sequence configuration

        Args:
            agent_session_id: ID of the agent session
            template: Message template or content
            template_type: Type of follow-up (no_response_sequence, appointment_reminder, etc.)
            context: Additional context for message generation

        Returns:
            Message object if successful, None if failed
        """
        try:
            # Get session, agent, and lead information
            session = self.db.query(AgentSession).filter(AgentSession.id == agent_session_id).first()
            if not session:
                logger.error(f"Agent session {agent_session_id} not found")
                return None

            agent = self.db.query(Agent).filter(Agent.id == session.agent_id).first()
            if not agent:
                logger.error(f"Agent {session.agent_id} not found")
                return None

            lead = self.db.query(Lead).filter(Lead.id == session.lead_id).first()
            if not lead:
                logger.error(f"Lead {session.lead_id} not found")
                return None

            # Get conversation history for context
            conversation_history = self._get_conversation_history(agent_session_id, 5)

            # Build context for follow-up message generation
            follow_up_context = self._build_follow_up_context(
                session, agent, lead, template, template_type, conversation_history, context
            )

            # Generate the follow-up message content
            message_content = await self._generate_follow_up_content(agent, follow_up_context)

            if not message_content:
                logger.error(f"Failed to generate follow-up content for session {agent_session_id}")
                return None

            # Create the message record
            message = Message.create_agent_message(
                agent_session_id=agent_session_id,
                lead_id=session.lead_id,
                agent_id=agent.id,
                content=message_content['content'],
                metadata={
                    "is_follow_up": True,
                    "template_type": template_type,
                    "follow_up_context": context,
                    "message_type": "follow_up",
                    "sequence_info": context.get('sequence_progress', {}) if context else {}
                },
                prompt_used=message_content.get('prompt_used'),
                model_used=message_content.get('model_used'),
                response_time_ms=message_content.get('response_time_ms'),
                token_usage=message_content.get('token_usage'),
                sender_name=agent.name,
                external_platform=lead.source if lead.source else None
            )

            # Save to database
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)

            # Update session statistics
            session.update_message_stats(from_agent=True)
            self.db.commit()

            logger.info(f"Follow-up message generated for session {agent_session_id} (type: {template_type})")
            return message

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error generating follow-up message for session {agent_session_id}: {str(e)}")
            return None

    def _build_initial_message_context(
        self,
        session: AgentSession,
        agent: Agent,
        lead: Lead,
        project_details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Build context for initial message generation"""

        context = {
            "lead": {
                "first_name": getattr(lead, 'first_name', None) or (lead.name.split()[0] if lead.name else "there"),
                "last_name": getattr(lead, 'last_name', None) or "",
                "full_name": lead.name or "Customer",
                "email": lead.email,
                "phone": lead.phone,
                "company": lead.company,
                "service_requested": lead.service_requested,
                "source": lead.source
            },
            "session": {
                "trigger_type": session.trigger_type,
                "session_goal": session.session_goal,
                "initial_context": session.initial_context or {}
            },
            "agent": {
                "name": agent.name,
                "use_case": agent.use_case,
                "business_context": agent.tool_configs.get("business_context", {}) if agent.tool_configs else {}
            },
            "project_details": project_details or {},
            "is_initial_message": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Extract Yelp-specific data if available
        if project_details and "yelp_data" in project_details:
            yelp_data = project_details["yelp_data"]
            project_info = project_details.get("project", {})

            context["yelp"] = {
                "conversation_id": yelp_data.get("conversation_id"),
                "business_id": yelp_data.get("business_id"),
                "project": {
                    "job_names": project_info.get("job_names", []),
                    "location": project_info.get("location", {}),
                    "additional_info": project_info.get("additional_info"),
                    "availability": project_info.get("availability", {}),
                    "survey_answers": project_info.get("survey_answers", [])
                }
            }

        return context

    def _build_response_context(
        self,
        session: AgentSession,
        agent: Agent,
        lead: Lead,
        incoming_message: str,
        conversation_history: List[Message],
        context_override: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Build context for response generation"""

        # Convert conversation history to chat format (chronological order)
        chat_history = []
        for msg in conversation_history:  # Already limited and ordered chronologically
            role = "assistant" if msg.is_from_agent() else "user"
            chat_history.append({
                "role": role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat() if msg.created_at else None
            })

        context = {
            "lead": {
                "first_name": getattr(lead, 'first_name', None) or (lead.name.split()[0] if lead.name else "there"),
                "last_name": getattr(lead, 'last_name', None) or "",
                "full_name": lead.name or "Customer",
                "service_requested": lead.service_requested,
                "source": lead.source
            },
            "session": {
                "goal": session.session_goal,
                "message_count": session.message_count,
                "trigger_type": session.trigger_type
            },
            "agent": {
                "name": agent.name,
                "use_case": agent.use_case
            },
            "conversation": {
                "incoming_message": incoming_message,
                "history": chat_history,
                "message_count": len(conversation_history)
            },
            "is_initial_message": False,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Apply context overrides
        if context_override:
            context.update(context_override)

        return context

    async def _generate_greeting_content(self, agent: Agent, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate greeting message content using agent's prompt template"""

        if not self.openai_service.is_available():
            # Fallback greeting if OpenAI is not available
            first_name = context["lead"]["first_name"]
            service = context["lead"]["service_requested"] or "your inquiry"

            fallback_content = f"Hi {first_name}! Thanks for reaching out about {service}. I'm {agent.name} and I'm here to help. What questions can I answer for you?"

            return {
                "content": fallback_content,
                "model_used": "fallback",
                "response_time_ms": 0,
                "token_usage": {},
                "prompt_used": "fallback_greeting"
            }

        try:
            start_time = datetime.now()

            # Build prompt for initial message
            system_prompt = self._build_initial_message_prompt(agent, context)

            # Create user message with context
            user_message = self._format_initial_context_message(context)

            # Generate response
            response = await self.openai_service.chat_completion(
                messages=[{"role": "user", "content": user_message}],
                model=agent.model or "gpt-3.5-turbo",
                temperature=float(agent.temperature) if agent.temperature else 0.7,
                max_tokens=agent.max_tokens or 500,
                system_prompt=system_prompt
            )

            end_time = datetime.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)

            if response["success"]:
                return {
                    "content": response["response"],
                    "model_used": response["model"],
                    "response_time_ms": response_time_ms,
                    "token_usage": response["usage"],
                    "prompt_used": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt
                }
            else:
                logger.error(f"OpenAI response failed: {response['error']}")
                return None

        except Exception as e:
            logger.error(f"Error generating greeting content: {str(e)}")
            return None

    async def _generate_response_content(self, agent: Agent, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate response message content using agent's prompt template"""

        if not self.openai_service.is_available():
            # Fallback response if OpenAI is not available
            fallback_content = "Thank you for your message. I'm currently experiencing technical difficulties but will get back to you shortly."

            return {
                "content": fallback_content,
                "model_used": "fallback",
                "response_time_ms": 0,
                "token_usage": {},
                "prompt_used": "fallback_response"
            }

        try:
            start_time = datetime.now()

            # Build prompt for response with lead and conversation context
            system_prompt = self._build_response_prompt(agent, context)

            # Build conversation messages
            messages = []

            # Add conversation history
            for msg in context["conversation"]["history"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # Add current incoming message
            messages.append({
                "role": "user",
                "content": context["conversation"]["incoming_message"]
            })

            # Generate response
            response = await self.openai_service.chat_completion(
                messages=messages,
                model=agent.model or "gpt-3.5-turbo",
                temperature=float(agent.temperature) if agent.temperature else 0.7,
                max_tokens=agent.max_tokens or 500,
                system_prompt=system_prompt
            )

            end_time = datetime.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)

            if response["success"]:
                return {
                    "content": response["response"],
                    "model_used": response["model"],
                    "response_time_ms": response_time_ms,
                    "token_usage": response["usage"],
                    "prompt_used": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt
                }
            else:
                logger.error(f"OpenAI response failed: {response['error']}")
                return None

        except Exception as e:
            logger.error(f"Error generating response content: {str(e)}")
            return None

    def _build_initial_message_prompt(self, agent: Agent, context: Dict[str, Any]) -> str:
        """Build the system prompt for initial message generation using agent's prompt template"""

        # Use the agent's existing prompt template as the base
        base_prompt = agent.prompt_template or "You are a helpful customer service agent."

        # Replace template variables with actual lead data
        prompt_with_context = self._replace_prompt_variables(base_prompt, context)

        # Add specific instruction that this is the initial message
        initial_message_instruction = f"""

INITIAL MESSAGE CONTEXT:
This is your very first message to this lead. Generate an appropriate greeting based on your role and the lead information provided above.

Lead Details:
- First Name: {context['lead']['first_name']}
- Full Name: {context['lead']['full_name']}
- Service Requested: {context['lead']['service_requested']}
- Source Platform: {context['lead']['source']}

"""

        # Add Yelp-specific project context if available
        if "yelp" in context and context["yelp"]["project"]:
            project = context["yelp"]["project"]
            yelp_context = f"""
Yelp Project Information:
- Services Needed: {', '.join(project.get('job_names', []))}
- Project Details: {project.get('additional_info', 'None provided')}
- Location: {project.get('location', {}).get('postal_code', 'Not specified')}
- Survey Responses: {self._format_survey_answers(project.get('survey_answers', []))}
"""
            initial_message_instruction += yelp_context

        return prompt_with_context + initial_message_instruction

    def _build_response_prompt(self, agent: Agent, context: Dict[str, Any]) -> str:
        """Build system prompt for response generation including conversation context"""

        # Use the agent's prompt template as base
        base_prompt = agent.prompt_template or "You are a helpful customer service agent."

        # Replace template variables with actual lead and context data
        prompt_with_context = self._replace_prompt_variables(base_prompt, context)

        # Add conversation context instructions
        conversation_context = f"""

CONVERSATION CONTEXT:
You are responding to an ongoing conversation with {context['lead']['first_name']} about {context['lead']['service_requested']}.

Current conversation has {context['conversation']['message_count']} messages so far.

Lead Information:
- Name: {context['lead']['full_name']}
- Service: {context['lead']['service_requested']}
- Source: {context['lead']['source']}

IMPORTANT: Review the conversation history provided in the messages above to understand the context and provide a relevant, helpful response. Do not repeat information already discussed. Build on the conversation naturally.
"""

        return prompt_with_context + conversation_context

    def _format_initial_context_message(self, context: Dict[str, Any]) -> str:
        """Format the context into a user message for initial greeting generation"""

        # Since we're now using the agent's prompt template with variables replaced,
        # the user message can be simpler and just request the initial greeting
        message = "Generate your initial greeting message for this new lead based on the context provided above."

        # Add any additional context that might be helpful
        if "yelp" in context and context["yelp"]["project"]:
            message += " This lead came from Yelp and has provided specific project details."

        return message

    def _get_conversation_history(self, agent_session_id: int, limit: int = 10) -> List[Message]:
        """Get recent conversation history for the session in chronological order"""
        return self.db.query(Message)\
            .filter(Message.agent_session_id == agent_session_id)\
            .order_by(Message.created_at.asc())\
            .limit(limit)\
            .all()

    def get_session_context(self, agent_session_id: int) -> Optional[Dict[str, Any]]:
        """Get full context for an agent session"""
        try:
            session = self.db.query(AgentSession).filter(AgentSession.id == agent_session_id).first()
            if not session:
                return None

            agent = self.db.query(Agent).filter(Agent.id == session.agent_id).first()
            lead = self.db.query(Lead).filter(Lead.id == session.lead_id).first()
            messages = self._get_conversation_history(agent_session_id, 50)

            return {
                "session": session.to_dict() if session else None,
                "agent": agent.to_dict() if agent else None,
                "lead": lead.to_dict() if lead else None,
                "messages": [msg.to_dict() for msg in messages],
                "message_count": len(messages)
            }

        except Exception as e:
            logger.error(f"Error getting session context for {agent_session_id}: {str(e)}")
            return None

    def _replace_prompt_variables(self, prompt_template: str, context: Dict[str, Any]) -> str:
        """Replace template variables in the prompt with actual lead data"""

        # Create a mapping of template variables to actual values
        variables = {
            # Lead information
            "first_name": context.get('lead', {}).get('first_name', ''),
            "last_name": context.get('lead', {}).get('last_name', ''),
            "full_name": context.get('lead', {}).get('full_name', ''),
            "lead_name": context.get('lead', {}).get('full_name', ''),
            "email": context.get('lead', {}).get('email', ''),
            "phone": context.get('lead', {}).get('phone', ''),
            "company": context.get('lead', {}).get('company', ''),
            "service_requested": context.get('lead', {}).get('service_requested', ''),
            "source": context.get('lead', {}).get('source', ''),

            # Agent information
            "agent_name": context.get('agent', {}).get('name', ''),

            # Business context if available
            "business_name": context.get('agent', {}).get('business_context', {}).get('name', ''),

            # Session information
            "session_goal": context.get('session', {}).get('session_goal', ''),
            "trigger_type": context.get('session', {}).get('trigger_type', ''),
        }

        # Add Yelp-specific variables if available
        if "yelp" in context:
            project = context["yelp"]["project"]
            variables.update({
                "job_types": ', '.join(project.get('job_names', [])),
                "project_details": project.get('additional_info', ''),
                "location": project.get('location', {}).get('postal_code', ''),
                "postal_code": project.get('location', {}).get('postal_code', ''),
            })

        # Replace variables in the template
        # Support both {{variable}} and <variable/> formats commonly used in prompts
        prompt_with_values = prompt_template

        for var_name, var_value in variables.items():
            if var_value:  # Only replace if we have a value
                # Replace {{variable}} format
                prompt_with_values = prompt_with_values.replace(f"{{{{{var_name}}}}}", str(var_value))
                # Replace <variable/> format
                prompt_with_values = prompt_with_values.replace(f"<{var_name}/>", str(var_value))
                # Replace <variable> format
                prompt_with_values = prompt_with_values.replace(f"<{var_name}>", str(var_value))

        return prompt_with_values

    def _format_survey_answers(self, survey_answers: List[Dict[str, Any]]) -> str:
        """Format Yelp survey answers for inclusion in prompts"""
        if not survey_answers:
            return "None provided"

        formatted_answers = []
        for answer in survey_answers:
            question = answer.get('question_text', 'Unknown question')
            responses = answer.get('answer_text', [])
            if responses:
                response_text = ', '.join(responses) if isinstance(responses, list) else str(responses)
                formatted_answers.append(f"Q: {question}\nA: {response_text}")

        return '\n\n'.join(formatted_answers) if formatted_answers else "None provided"

    def _build_follow_up_context(
        self,
        session: AgentSession,
        agent: Agent,
        lead: Lead,
        template: str,
        template_type: str,
        conversation_history: List[Message],
        additional_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Build context for follow-up message generation"""

        # Convert conversation history to chat format
        chat_history = []
        for msg in conversation_history:
            role = "assistant" if msg.is_from_agent() else "user"
            chat_history.append({
                "role": role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat() if msg.created_at else None
            })

        # Get sequence progress if available
        sequence_progress = additional_context.get('sequence_progress', {}) if additional_context else {}

        context = {
            "lead": {
                "first_name": getattr(lead, 'first_name', None) or (lead.name.split()[0] if lead.name else "there"),
                "last_name": getattr(lead, 'last_name', None) or "",
                "full_name": lead.name or "Customer",
                "service_requested": lead.service_requested,
                "source": lead.source
            },
            "session": {
                "goal": session.session_goal,
                "message_count": session.message_count,
                "trigger_type": session.trigger_type,
                "time_since_last_message": session.get_time_since_last_message()
            },
            "agent": {
                "name": agent.name,
                "use_case": agent.use_case
            },
            "follow_up": {
                "template": template,
                "template_type": template_type,
                "sequence_progress": sequence_progress,
                "is_sequence": sequence_progress.get('current_step', 0) > 0,
                "is_first_in_sequence": sequence_progress.get('is_first', False),
                "is_last_in_sequence": sequence_progress.get('is_last', False)
            },
            "conversation": {
                "history": chat_history,
                "message_count": len(conversation_history),
                "last_message_was_from_agent": chat_history[-1]["role"] == "assistant" if chat_history else False
            },
            "is_follow_up_message": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Apply additional context
        if additional_context:
            context.update(additional_context)

        return context

    async def _generate_follow_up_content(self, agent: Agent, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate follow-up message content using sequence-aware templates"""

        follow_up_info = context["follow_up"]
        template_type = follow_up_info["template_type"]

        if not self.openai_service.is_available():
            # Fallback follow-up messages based on type
            fallback_messages = {
                "no_response_sequence": self._get_no_response_fallback(context),
                "appointment_reminder": f"Hi {context['lead']['first_name']}! This is a reminder about your upcoming appointment.",
                "reengagement": f"Hi {context['lead']['first_name']}! I wanted to follow up about {context['lead']['service_requested']}."
            }

            fallback_content = fallback_messages.get(template_type, "Following up on our previous conversation.")

            return {
                "content": fallback_content,
                "model_used": "fallback",
                "response_time_ms": 0,
                "token_usage": {},
                "prompt_used": f"fallback_{template_type}"
            }

        try:
            start_time = datetime.now()

            # Build system prompt for follow-up message
            system_prompt = self._build_follow_up_prompt(agent, context)

            # Create user message for follow-up generation
            user_message = self._format_follow_up_request(context)

            # Generate response
            response = await self.openai_service.chat_completion(
                messages=[{"role": "user", "content": user_message}],
                model=agent.model or "gpt-3.5-turbo",
                temperature=float(agent.temperature) if agent.temperature else 0.7,
                max_tokens=agent.max_tokens or 300,  # Shorter for follow-ups
                system_prompt=system_prompt
            )

            end_time = datetime.now()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)

            if response["success"]:
                return {
                    "content": response["response"],
                    "model_used": response["model"],
                    "response_time_ms": response_time_ms,
                    "token_usage": response["usage"],
                    "prompt_used": system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt
                }
            else:
                logger.error(f"OpenAI response failed for follow-up: {response['error']}")
                return None

        except Exception as e:
            logger.error(f"Error generating follow-up content: {str(e)}")
            return None

    def _build_follow_up_prompt(self, agent: Agent, context: Dict[str, Any]) -> str:
        """Build system prompt for follow-up message generation"""

        base_prompt = agent.prompt_template or "You are a helpful customer service agent."
        prompt_with_context = self._replace_prompt_variables(base_prompt, context)

        follow_up_info = context["follow_up"]
        sequence_progress = follow_up_info["sequence_progress"]

        # Add follow-up specific instructions
        follow_up_instruction = f"""

FOLLOW-UP MESSAGE CONTEXT:
You are generating a follow-up message for {context['lead']['first_name']} who has not responded recently.

Follow-up Details:
- Type: {follow_up_info['template_type']}
- Time since last message: {context['session']['time_since_last_message']} minutes
- Previous conversation messages: {context['conversation']['message_count']}

"""

        # Add sequence-specific context
        if follow_up_info["is_sequence"] and sequence_progress:
            sequence_instruction = f"""
SEQUENCE CONTEXT:
This is step {sequence_progress.get('current_step', 1)} of {sequence_progress.get('total_steps', 1)} in a follow-up sequence.
- Is first message in sequence: {follow_up_info['is_first_in_sequence']}
- Is last message in sequence: {follow_up_info['is_last_in_sequence']}
- Progress: {sequence_progress.get('progress_percentage', 0):.0f}% complete

"""
            follow_up_instruction += sequence_instruction

            if follow_up_info['is_first_in_sequence']:
                follow_up_instruction += "This is your first follow-up attempt. Be friendly and check if they need any information.\n"
            elif follow_up_info['is_last_in_sequence']:
                follow_up_instruction += "This is your final follow-up attempt. Offer alternative ways to connect or politely close the conversation.\n"
            else:
                follow_up_instruction += "This is a middle step in your follow-up sequence. Be persistent but respectful.\n"

        # Add template-specific instructions
        template_instructions = {
            "no_response_sequence": "Generate a polite follow-up message asking if they need any additional information or have questions.",
            "appointment_reminder": "Generate a friendly reminder about an upcoming appointment.",
            "reengagement": "Generate a re-engagement message to reconnect with an inactive lead."
        }

        template_instruction = template_instructions.get(follow_up_info['template_type'], "Generate an appropriate follow-up message.")
        follow_up_instruction += f"\nMessage Type Instruction: {template_instruction}\n"

        # Add template content if provided
        if follow_up_info['template'] and follow_up_info['template'] != 'default':
            follow_up_instruction += f"\nTemplate Content: Use this as inspiration but personalize it: '{follow_up_info['template']}'\n"

        return prompt_with_context + follow_up_instruction

    def _format_follow_up_request(self, context: Dict[str, Any]) -> str:
        """Format the user message for follow-up generation"""

        follow_up_info = context["follow_up"]

        message = f"Generate a follow-up message for {context['lead']['first_name']} based on the context above."

        # Add conversation context if available
        if context['conversation']['history']:
            message += f" They last engaged {context['session']['time_since_last_message']} minutes ago."

        # Add sequence context
        if follow_up_info['is_sequence']:
            step = follow_up_info['sequence_progress'].get('current_step', 1)
            total = follow_up_info['sequence_progress'].get('total_steps', 1)
            message += f" This is follow-up step {step} of {total}."

        return message

    def _get_no_response_fallback(self, context: Dict[str, Any]) -> str:
        """Get fallback message for no response follow-up"""

        first_name = context['lead']['first_name']
        sequence_progress = context['follow_up']['sequence_progress']

        if sequence_progress.get('is_first', True):
            return f"Hi {first_name}! I wanted to follow up on our conversation. Do you have any questions I can help answer?"
        elif sequence_progress.get('is_last', False):
            return f"Hi {first_name}! This is my final follow-up. If you'd like to continue our conversation, please feel free to reach out anytime!"
        else:
            return f"Hi {first_name}! Just checking in to see if you need any additional information from me."