import os
from typing import AsyncIterable, cast
import textwrap
import aiohttp
import re

from dotenv import load_dotenv
import logging
import json
from dataclasses import asdict
import asyncio

from livekit import agents, rtc
from livekit.plugins import deepgram, openai, cartesia

from utils import session, tracing, fetching, common

load_dotenv()

logger: logging.Logger = logging.getLogger(os.getenv("AGENT_NAME"))


async def fetch_agent_config(room_name: str) -> dict:
    """
    Fetch agent configuration from the database API based on room name.
    For SIP calls, room name format is usually: call-{phone_digits}
    """
    try:
        # Get API base URL from environment
        api_base_url = os.getenv("API_BASE_URL", "https://lead-management-staging-backend.onrender.com")

        # Extract call ID from room name if possible
        # For SIP calls: room format is call-{phone_digits}
        # For regular calls: might have call_id in metadata
        call_id = None

        # Try to extract phone number from room name for SIP calls
        # Handle both formats: call-12014860463 and call_+12014860463_randomstring
        phone_match = re.search(r'call[-_]\+?([0-9]+)', room_name)
        phone_number = None

        if phone_match:
            phone_digits = phone_match.group(1)
            # Add country code if not present
            if len(phone_digits) == 10:
                phone_number = f"+1{phone_digits}"
            elif len(phone_digits) == 11 and phone_digits.startswith('1'):
                phone_number = f"+{phone_digits}"
            else:
                phone_number = f"+{phone_digits}"

            logger.info(f"SIP call detected - phone: {phone_number}, room: {room_name}")

            # Find the most recent inbound call for this phone number
            async with aiohttp.ClientSession() as session:
                url = f"{api_base_url}/api/inbound-calls/?caller_phone_number={phone_number.replace('+', '%2B')}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        calls = data.get("inbound_calls", [])
                        if calls:
                            # Get the most recent call
                            recent_call = calls[0]
                            call_id = recent_call.get("id")
                            logger.info(f"Found call ID: {call_id} for phone: {phone_number}")

        if not call_id:
            logger.warning(f"Could not determine call_id from room: {room_name}")

            # If this is a SIP call, create lead directly since webhook was bypassed
            if phone_match and phone_number:
                logger.info(f"Creating lead directly for SIP call: {phone_number}")
                lead_created = await create_lead_for_sip_call(phone_number, room_name, api_base_url)
                if lead_created:
                    logger.info(f"Successfully created lead for {phone_number}")
                else:
                    logger.warning(f"Failed to create lead for {phone_number}")

            return get_default_agent_config()

        # Fetch agent configuration for this call
        async with aiohttp.ClientSession() as session:
            config_url = f"{api_base_url}/api/inbound-calls/agent-config/{call_id}"
            async with session.get(config_url) as response:
                if response.status == 200:
                    config = await response.json()
                    logger.info(f"Retrieved agent config for call {call_id}")
                    return config
                else:
                    logger.warning(f"Failed to fetch agent config: {response.status}")
                    return get_default_agent_config()

    except Exception as e:
        logger.error(f"Error fetching agent config: {str(e)}")
        return get_default_agent_config()


async def create_lead_for_sip_call(phone_number: str, room_name: str, api_base_url: str) -> bool:
    """
    Create a lead directly for SIP calls since webhook was bypassed
    """
    try:
        # Create lead via backend API
        lead_data = {
            "caller_phone_number": phone_number,
            "inbound_phone_number": "+17622437375",
            "call_status": "received",
            "call_metadata": {
                "room_name": room_name,
                "routing_method": "direct_sip",
                "agent_created": True
            }
        }

        async with aiohttp.ClientSession() as session:
            url = f"{api_base_url}/api/inbound-calls/"
            async with session.post(url, json=lead_data) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Created inbound call record: {data.get('id')}")
                    return True
                else:
                    logger.error(f"Failed to create lead: {response.status}")
                    return False

    except Exception as e:
        logger.error(f"Error creating lead for SIP call: {str(e)}")
        return False


def get_default_agent_config() -> dict:
    """
    Return default agent configuration if database lookup fails
    """
    return {
        "agent_name": "Mike",
        "prompt_template": """You are Mike, a friendly and professional customer service representative for Torkin Pest Control.

When greeting callers, introduce yourself as Mike. Your role is to:
- Greet callers warmly saying "Hello, thank you for calling Torkin Pest Control. How can I help you?" and identify their needs
- Listen to their needs and questions
- Provide helpful information about services
- Collect contact information when appropriate
- Ensure customer satisfaction

Be friendly, professional, and solution-focused. Keep responses conversational and concise.

Customer Information:
- Caller: {customer_name}
- Phone: {caller_phone}
- Service Requested: {service_requested}
""",
        "personality_style": "professional",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 500,
        "lead_context": {
            "first_name": "Caller",
            "phone": "Unknown",
            "service_requested": "General inquiry"
        },
        "call_context": {
            "caller_phone": "Unknown",
            "inbound_phone": "+17622437375"
        }
    }


class Assistant(agents.Agent):
    def __init__(self, room: rtc.Room, agent_config: dict, is_sip_session: bool = False) -> None:
        # Extract configuration from agent_config
        prompt_template = agent_config.get("prompt_template", get_default_agent_config()["prompt_template"])
        model_name = agent_config.get("model", "gpt-4o-mini")
        temperature = float(agent_config.get("temperature", 0.7))
        max_tokens = agent_config.get("max_tokens", 500)

        # Get lead and call context for prompt variables
        lead_context = agent_config.get("lead_context", {})
        call_context = agent_config.get("call_context", {})

        # Format the prompt template with actual values
        formatted_instructions = prompt_template.format(
            customer_name=lead_context.get("first_name", "Caller"),
            caller_phone=call_context.get("caller_phone", "Unknown"),
            customer_phone=call_context.get("caller_phone", "Unknown"),
            inbound_phone=call_context.get("inbound_phone", "+17622437375"),
            service_requested=lead_context.get("service_requested", "General inquiry"),
            lead_status=lead_context.get("status", "new"),
            company=lead_context.get("company", ""),
            interaction_history="Previous interactions will be loaded from conversation history"
        )

        logger.info(f"Using agent: {agent_config.get('agent_name', 'Unknown')}")
        logger.info(f"Model: {model_name}, Temperature: {temperature}")

        super().__init__(
            instructions=formatted_instructions,
            stt=deepgram.STT(
                model="nova-2-phonecall",
                language="en-US",
                smart_format=True,
                interim_results=True,
                punctuate=True
            ),
            llm=openai.LLM(
                model=model_name,
                temperature=temperature
            ),
            tts=cartesia.TTS(
                model="sonic-2-2025-03-07",
                voice="146485fd-8736-41c7-88a8-7cdd0da34d84"
            ),
        )
        self.room = room
        self.agent_config = agent_config

    async def on_enter(self):
        logger.info(f"on_enter: Agent started now for user: {self.session.userdata.user_id}")
        logger.info(f"on_enter: User info: {self.session.userdata.country}, {self.session.userdata.app_version}")

        business_rules = fetching.fetch_business_rules()

        # Add context instructions
        chat_ctx = self.chat_ctx.copy()

        chat_ctx.add_message(
            role="system",  # role=system works for OpenAI's LLM and Realtime API
            content=textwrap.dedent(f"""
                Follow these business rules:
                {business_rules}
            """)
        )
        await self.update_chat_ctx(chat_ctx)

        # Get greeting from agent configuration
        agent_name = self.agent_config.get("agent_name", "Customer Service Agent")
        conversation_settings = self.agent_config.get("conversation_settings", {})
        greeting_message = conversation_settings.get("greeting_message",
                                                   f"Hello, thank you for calling Torkin Pest Control. How can I help you?")

        # Inbound call greeting
        await self.session.generate_reply(
            instructions=textwrap.dedent(f"""
                Start the conversation immediately with: "{greeting_message}"
                Wait for their response before proceeding.
            """),
            allow_interruptions=True
        )

    async def on_exit(self) -> None:
        logger.info(f"on_exit: Agent exited")
        if self.session.userdata.consent_to_record:
            await session.notify_session_end(self.session.userdata)

    async def llm_node(
        self, chat_ctx: agents.ChatContext, tools: list[agents.FunctionTool], model_settings: agents.ModelSettings
    ):
        # not all LLMs support structured output, so we need to cast to the specific LLM type
        llm = cast(openai.LLM, self.llm)
        tool_choice = model_settings.tool_choice if model_settings else agents.NOT_GIVEN
        async with llm.chat(
            chat_ctx=chat_ctx,
            tools=tools,
            tool_choice=tool_choice,
            response_format=session.ResponseFormat,
        ) as stream:
            async for chunk in stream:
                yield chunk

    async def tts_node(self, text: AsyncIterable[str], model_settings: agents.ModelSettings):
        logger.info(f"tts_node: inside tts_node")
        return agents.Agent.default.tts_node(self, session.process_structured_output(text), model_settings)

    @agents.function_tool()
    async def save_consent_to_record(self, context: agents.RunContext, consent_to_record: bool, reasoning_for_tool_call: str) -> str:
        """
        Save the user consent to record the conversation.

        Args:
            consent_to_record (bool): The user's consent to record the conversation.
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: success or failure.
        """
        self.session.userdata.consent_to_record = consent_to_record
        return json.dumps({"status": "success"})

    @agents.function_tool()
    async def confirm_lead_details(self, context: agents.RunContext, reasoning_for_tool_call: str) -> str:
        """
        Verify address and project type from the web form submission.

        Args:
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: Lead details including address and project type.
        """
        # Dummy data for lead details
        lead_details = {
            "address": "123 Oak Street, Springfield, IL 62701",
            "project_type": "Living room carpet replacement",
            "submitted_date": "2024-01-15",
            "phone": "+1-555-123-4567",
            "email": "john.smith@email.com",
            "preferred_contact": "phone"
        }

        result_message = json.dumps({
            "status": "success",
            "lead_details": lead_details,
            "message": f"Lead details confirmed: {lead_details['address']} for {lead_details['project_type']}"
        })

        return result_message

    @agents.function_tool()
    async def generate_appointment_slots(self, context: agents.RunContext, address: str, service_type: str, reasoning_for_tool_call: str) -> str:
        """
        Generate available appointment time slots for pest control service.

        Args:
            address (str): The customer's address for the service.
            service_type (str): Type of pest control service (inspection, treatment, etc.).
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: Available appointment slots.
        """
        from datetime import datetime, timedelta
        import random

        # Generate realistic appointment slots - next 5 business days
        today = datetime.now()
        slots = []

        # Find next 5 business days with varying times
        current_date = today + timedelta(days=1)
        slot_count = 0

        while slot_count < 6:  # Generate 6 slots across multiple days
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                day_name = current_date.strftime("%A")
                date_str = current_date.strftime("%B %d")

                # Multiple time slots per day (8 AM - 5 PM)
                time_options = ["8:00 AM", "10:00 AM", "11:30 AM", "1:00 PM", "2:30 PM", "4:00 PM"]
                available_times = random.sample(time_options, random.randint(1, 3))

                for time_slot in available_times:
                    if slot_count < 6:
                        slots.append({
                            "day": day_name,
                            "date": date_str,
                            "time": time_slot,
                            "slot_id": f"TPC-{current_date.strftime('%m%d')}-{time_slot.replace(':', '').replace(' ', '')}",
                            "technician": random.choice(["Tom Wilson", "Carlos Rodriguez", "Mike Thompson", "Sarah Davis"]),
                            "service_window": "2-hour window"
                        })
                        slot_count += 1

            current_date += timedelta(days=1)

        # Return only the first 5 slots for selection
        available_slots = slots[:5]

        result_message = json.dumps({
            "status": "success",
            "service_type": service_type,
            "available_slots": available_slots,
            "message": f"Found {len(available_slots)} available time slots for {service_type} service",
            "notes": "All appointments include free inspection and quote"
        })

        return result_message

    @agents.function_tool()
    async def book_appointment(self, context: agents.RunContext, slot_id: str, day: str, date: str, time: str, address: str, reasoning_for_tool_call: str) -> str:
        """
        Book the selected appointment slot for pest control service.

        Args:
            slot_id (str): Unique identifier for the selected appointment slot.
            day (str): Day of the week for the appointment.
            date (str): Date of the appointment.
            time (str): Time of the appointment.
            address (str): Customer's address for the service.
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: Appointment booking confirmation.
        """
        import random

        # Generate realistic pest control appointment confirmation
        appointment_id = f"TPC-{random.randint(10000, 99999)}"
        technician_name = random.choice(["Tom Wilson", "Carlos Rodriguez", "Mike Thompson", "Sarah Davis", "Jennifer Martinez"])
        service_types = ["Inspection & Quote", "Termite Treatment", "Rodent Control", "General Pest Control", "Ant Treatment"]
        selected_service = random.choice(service_types)

        booking_details = {
            "appointment_id": appointment_id,
            "confirmation_number": f"CONF-{random.randint(1000, 9999)}",
            "day": day,
            "date": date,
            "time": time,
            "service_window": "2-hour window",
            "address": address,
            "technician_name": technician_name,
            "service_type": selected_service,
            "estimated_duration": "1-3 hours depending on service",
            "what_to_expect": "Free inspection, detailed quote, and treatment if approved",
            "confirmation_sms": "Text confirmation sent within 10 minutes",
            "phone_reminder": "Call reminder 24 hours before appointment",
            "preparation_notes": "Please ensure access to all areas requiring inspection"
        }

        result_message = json.dumps({
            "status": "success",
            "booking_details": booking_details,
            "message": f"Pest control appointment successfully booked for {day}, {date} at {time}",
            "next_steps": "You'll receive confirmation via text and email. Our technician will call 30 minutes before arrival."
        })

        return result_message

    @agents.function_tool()
    async def raise_callback_request(self, context: agents.RunContext, customer_phone: str, preferred_time: str, reason: str, reasoning_for_tool_call: str) -> str:
        """
        Request a callback from the scheduling manager when no suitable appointment slots are available.

        Args:
            customer_phone (str): Customer's phone number for callback.
            preferred_time (str): Customer's preferred callback time.
            reason (str): Reason for callback (e.g., no available slots, emergency).
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: Callback request confirmation.
        """
        import random
        from datetime import datetime, timedelta

        # Generate realistic callback request details
        callback_id = f"TCB-{random.randint(10000, 99999)}"

        # Determine callback timing based on reason
        if "emergency" in reason.lower() or "urgent" in reason.lower():
            callback_time = datetime.now() + timedelta(minutes=random.randint(15, 30))
            priority = "urgent"
        else:
            callback_time = datetime.now() + timedelta(minutes=random.randint(30, 120))
            priority = "standard"

        manager_name = random.choice([
            "Jennifer Adams - Scheduling Manager",
            "Robert Martinez - Senior Coordinator",
            "Susan Williams - Customer Success Manager",
            "Michael Brown - Regional Manager"
        ])

        callback_details = {
            "callback_id": callback_id,
            "customer_phone": customer_phone,
            "preferred_time": preferred_time,
            "scheduled_callback_time": callback_time.strftime("%I:%M %p today"),
            "manager_name": manager_name.split(" - ")[0],
            "manager_title": manager_name.split(" - ")[1],
            "reason": reason,
            "status": "scheduled",
            "priority": priority,
            "reference_number": f"REF-{random.randint(1000, 9999)}",
            "estimated_wait": "15-45 minutes" if priority == "urgent" else "30-90 minutes"
        }

        result_message = json.dumps({
            "status": "success",
            "callback_details": callback_details,
            "message": f"Priority callback scheduled with {callback_details['manager_name']} within {callback_details['estimated_wait']}",
            "instructions": "Please keep your phone available. Our manager will call from a Torkin Pest Control number."
        })

        return result_message

    @agents.function_tool()
    async def transfer_to_team(self, context: agents.RunContext, department: str, reason: str, customer_info: str, reasoning_for_tool_call: str) -> str:
        """
        Transfer the customer to a specialized team department for advanced assistance.

        Args:
            department (str): Target department (sales, technical, billing, management).
            reason (str): Reason for transfer.
            customer_info (str): Brief customer information for context.
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: Transfer confirmation details.
        """
        import random
        from datetime import datetime

        # Generate realistic transfer details
        transfer_id = f"TXF-{random.randint(10000, 99999)}"

        # Department-specific team assignments
        departments = {
            "sales": {
                "team_name": "Sales & Estimates Team",
                "specialists": [
                    "David Chen - Senior Sales Specialist",
                    "Maria Rodriguez - Commercial Estimates Manager",
                    "James Thompson - Residential Sales Expert",
                    "Sarah Johnson - Account Executive"
                ],
                "avg_wait": "2-5 minutes",
                "specialty": "pricing, service packages, and contract negotiations"
            },
            "technical": {
                "team_name": "Technical Support Team",
                "specialists": [
                    "Mark Wilson - Lead Technician Supervisor",
                    "Lisa Park - IPM Specialist",
                    "Tony Garcia - Rodent Control Expert",
                    "Amanda Foster - Termite Treatment Specialist"
                ],
                "avg_wait": "1-3 minutes",
                "specialty": "treatment methods, pest identification, and service issues"
            },
            "billing": {
                "team_name": "Billing & Accounts Team",
                "specialists": [
                    "Robert Kim - Billing Specialist",
                    "Jennifer Martinez - Accounts Manager",
                    "Kevin Brown - Payment Coordinator",
                    "Nancy Davis - Contract Administration"
                ],
                "avg_wait": "3-7 minutes",
                "specialty": "payment processing, billing questions, and account management"
            },
            "management": {
                "team_name": "Management Team",
                "specialists": [
                    "Patricia Anderson - Customer Success Manager",
                    "Michael Taylor - Regional Operations Manager",
                    "Susan White - Service Quality Manager",
                    "Daniel Lee - Branch Manager"
                ],
                "avg_wait": "5-10 minutes",
                "specialty": "service complaints, escalations, and management decisions"
            }
        }

        # Default to management if department not found
        dept_info = departments.get(department.lower(), departments["management"])
        assigned_specialist = random.choice(dept_info["specialists"])

        transfer_details = {
            "transfer_id": transfer_id,
            "department": dept_info["team_name"],
            "assigned_specialist": assigned_specialist.split(" - ")[0],
            "specialist_title": assigned_specialist.split(" - ")[1],
            "reason": reason,
            "customer_summary": customer_info,
            "estimated_wait": dept_info["avg_wait"],
            "specialty_area": dept_info["specialty"],
            "transfer_time": datetime.now().strftime("%I:%M %p"),
            "priority": "high" if "urgent" in reason.lower() or "emergency" in reason.lower() else "standard",
            "reference_number": f"REF-{random.randint(1000, 9999)}"
        }

        result_message = json.dumps({
            "status": "transferring",
            "transfer_details": transfer_details,
            "message": f"Transferring you to {transfer_details['assigned_specialist']} in our {transfer_details['department']}",
            "instructions": f"Please hold while I connect you. Estimated wait time: {transfer_details['estimated_wait']}. Your reference number is {transfer_details['reference_number']}."
        })

        return result_message


class SquadOrchestrator(agents.Agent):
    """
    Orchestrates multiple sub-agents within a single LiveKit session.
    Swaps instructions + tools when handoff is triggered.
    The caller hears one continuous conversation — same voice, same session.
    """

    def __init__(self, room: rtc.Room, squad_config: dict, is_sip_session: bool = False) -> None:
        self.squad_config = squad_config
        self.agents_map = squad_config["agents"]  # dict keyed by agent key
        self.current_agent_key = squad_config["entry_agent_key"]
        self.shared_context = {}
        self.turn_count = 0
        self.total_handoffs = 0
        self.max_total_handoffs = squad_config.get("routing_config", {}).get("max_total_handoffs", 5)

        # Lead and call context from backend
        lead_context = squad_config.get("lead_context", {})
        call_context = squad_config.get("call_context", {})
        self.lead_context = lead_context
        self.call_context = call_context

        # Model settings
        model_name = squad_config.get("model", "gpt-4o-mini")
        temperature = float(squad_config.get("temperature", 0.7))

        # Build initial instructions from entry agent
        entry_agent = self.agents_map[self.current_agent_key]
        formatted_instructions = self._format_prompt(entry_agent["prompt"])

        logger.info(f"SquadOrchestrator: starting with entry agent '{self.current_agent_key}'")

        super().__init__(
            instructions=formatted_instructions,
            stt=deepgram.STT(
                model="nova-2-phonecall",
                language="en-US",
                smart_format=True,
                interim_results=True,
                punctuate=True
            ),
            llm=openai.LLM(
                model=model_name,
                temperature=temperature
            ),
            tts=cartesia.TTS(
                model="sonic-2-2025-03-07",
                voice="146485fd-8736-41c7-88a8-7cdd0da34d84"
            ),
        )
        self.room = room
        self.is_sip_session = is_sip_session

    def _format_prompt(self, prompt: str) -> str:
        """Format prompt template with shared context and lead context"""
        try:
            return prompt.format(
                customer_name=self.shared_context.get("customer_name",
                    self.lead_context.get("first_name", "Caller")),
                caller_phone=self.call_context.get("caller_phone", "Unknown"),
                customer_phone=self.call_context.get("caller_phone", "Unknown"),
                inbound_phone=self.call_context.get("inbound_phone", "+17622437375"),
                service_requested=self.lead_context.get("service_requested", "General inquiry"),
                lead_status=self.lead_context.get("status", "new"),
                company=self.lead_context.get("company", ""),
                interaction_history=""
            )
        except KeyError:
            return prompt

    async def on_enter(self):
        logger.info(f"SquadOrchestrator on_enter: agent={self.current_agent_key}")

        business_rules = fetching.fetch_business_rules()
        chat_ctx = self.chat_ctx.copy()
        chat_ctx.add_message(
            role="system",
            content=textwrap.dedent(f"""
                Follow these business rules:
                {business_rules}
            """)
        )
        await self.update_chat_ctx(chat_ctx)

        # Entry agent greeting
        conversation_settings = self.squad_config.get("conversation_settings", {})
        greeting_message = conversation_settings.get("greeting_message",
            "Hello, thank you for calling Torkin Pest Control. This is Mike, how can I help you today?")

        await self.session.generate_reply(
            instructions=textwrap.dedent(f"""
                Start the conversation immediately with: "{greeting_message}"
                Wait for their response before proceeding.
            """),
            allow_interruptions=True
        )

    async def on_exit(self) -> None:
        logger.info(f"SquadOrchestrator on_exit")
        if self.session.userdata.consent_to_record:
            await session.notify_session_end(self.session.userdata)

    async def llm_node(
        self, chat_ctx: agents.ChatContext, tools: list[agents.FunctionTool], model_settings: agents.ModelSettings
    ):
        # Filter tools based on current agent's allowed tools
        current_agent = self.agents_map[self.current_agent_key]
        allowed_tool_names = set(current_agent.get("tools", []))
        # handoff_to_agent and save_consent_to_record are always available
        allowed_tool_names.add("handoff_to_agent")
        allowed_tool_names.add("save_consent_to_record")

        active_tools = [t for t in tools if t.name in allowed_tool_names]

        # Increment turn count
        self.turn_count += 1

        # Turn limit guard
        max_turns = current_agent.get("max_turns", 10)
        if self.turn_count > max_turns:
            logger.warning(f"Turn limit ({max_turns}) exceeded for agent '{self.current_agent_key}'. Forcing handoff to router.")
            # Force handoff back to router
            await self._execute_handoff(
                target_agent_key="router",
                context_summary=self.shared_context,
                reason=f"Turn limit exceeded for {self.current_agent_key}"
            )

        llm = cast(openai.LLM, self.llm)
        tool_choice = model_settings.tool_choice if model_settings else agents.NOT_GIVEN
        async with llm.chat(
            chat_ctx=chat_ctx,
            tools=active_tools,
            tool_choice=tool_choice,
            response_format=session.ResponseFormat,
        ) as stream:
            async for chunk in stream:
                yield chunk

    async def tts_node(self, text: AsyncIterable[str], model_settings: agents.ModelSettings):
        return agents.Agent.default.tts_node(self, session.process_structured_output(text), model_settings)

    async def _execute_handoff(self, target_agent_key: str, context_summary: dict, reason: str):
        """Execute the actual agent handoff — swap instructions and rebuild context"""
        if target_agent_key not in self.agents_map:
            logger.error(f"Handoff target '{target_agent_key}' not found in squad agents")
            return

        logger.info(f"HANDOFF: {self.current_agent_key} -> {target_agent_key} | reason: {reason}")
        logger.info(f"  Context passed: {context_summary}")

        # Update shared context
        if context_summary:
            self.shared_context.update(context_summary)

        # Switch agent
        self.current_agent_key = target_agent_key
        self.turn_count = 0
        self.total_handoffs += 1

        target_agent = self.agents_map[target_agent_key]

        # Build clean chat context with new agent's prompt (clean slate)
        new_prompt = self._format_prompt(target_agent["prompt"])
        chat_ctx = self.chat_ctx.copy()

        # Wipe prior conversation, inject new system prompt + structured context
        chat_ctx = agents.ChatContext()
        chat_ctx.add_message(role="system", content=new_prompt)

        if self.shared_context:
            context_str = json.dumps(self.shared_context, indent=2)
            chat_ctx.add_message(
                role="system",
                content=f"Context from previous agent: {context_str}"
            )

        await self.update_chat_ctx(chat_ctx)
        logger.info(f"AGENT ACTIVATED: {target_agent_key} | tools: {target_agent.get('tools', [])}")

    @agents.function_tool()
    async def handoff_to_agent(
        self,
        context: agents.RunContext,
        target_agent_key: str,
        context_summary: str,
        reason: str,
        reasoning_for_tool_call: str
    ) -> str:
        """
        Hand off the conversation to another specialized agent.

        Args:
            target_agent_key (str): Which agent to hand off to (booking, job_inquiry, complaint, router).
            context_summary (str): JSON string with structured variables to pass forward (customer_name, intent, phone, etc.).
            reason (str): Why the handoff is happening.
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: Confirmation of the handoff.
        """
        # Validate target is in current agent's allowed_handoffs
        current_agent = self.agents_map[self.current_agent_key]
        allowed = current_agent.get("allowed_handoffs", [])

        # Check for deterministic routes first
        det_routes = current_agent.get("deterministic_routes", {})
        if target_agent_key in det_routes:
            route = det_routes[target_agent_key]
            logger.info(f"DETERMINISTIC ROUTE: {target_agent_key} -> {route}")
            # Execute the deterministic action directly
            if route.get("action") == "transfer_to_team":
                return await self.transfer_to_team(
                    context=context,
                    department=route["department"],
                    reason=route.get("reason", reason),
                    customer_info=context_summary,
                    reasoning_for_tool_call=f"Deterministic route: {target_agent_key}"
                )

        if target_agent_key not in allowed:
            return json.dumps({
                "status": "error",
                "message": f"Agent '{self.current_agent_key}' cannot hand off to '{target_agent_key}'. Allowed: {allowed}"
            })

        if self.total_handoffs >= self.max_total_handoffs:
            return json.dumps({
                "status": "error",
                "message": f"Maximum handoffs ({self.max_total_handoffs}) reached. Cannot hand off further."
            })

        # Parse context_summary
        try:
            ctx_dict = json.loads(context_summary) if isinstance(context_summary, str) else context_summary
        except (json.JSONDecodeError, TypeError):
            ctx_dict = {"raw_context": context_summary}

        await self._execute_handoff(target_agent_key, ctx_dict, reason)

        target_name = self.agents_map[target_agent_key]["name"]
        return json.dumps({
            "status": "success",
            "message": f"Handed off to {target_name}. Continue the conversation naturally without re-introducing yourself.",
            "active_agent": target_agent_key
        })

    @agents.function_tool()
    async def save_consent_to_record(self, context: agents.RunContext, consent_to_record: bool, reasoning_for_tool_call: str) -> str:
        """
        Save the user consent to record the conversation.

        Args:
            consent_to_record (bool): The user's consent to record the conversation.
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: success or failure.
        """
        self.session.userdata.consent_to_record = consent_to_record
        return json.dumps({"status": "success"})

    @agents.function_tool()
    async def confirm_lead_details(self, context: agents.RunContext, reasoning_for_tool_call: str) -> str:
        """
        Look up existing job/lead details by customer name or address.

        Args:
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: Job details including status, service type, and next visit.
        """
        import random
        from datetime import datetime, timedelta

        job_id = f"JOB-{random.randint(10000, 99999)}"
        last_treatment = datetime.now() - timedelta(days=random.randint(14, 60))
        next_visit = datetime.now() + timedelta(days=random.randint(7, 30))

        lead_details = {
            "job_id": job_id,
            "address": self.shared_context.get("address", "123 Oak Street, Springfield, IL 62701"),
            "service_type": random.choice(["General Pest Control", "Termite Treatment", "Rodent Control", "Ant Treatment"]),
            "last_treatment_date": last_treatment.strftime("%B %d, %Y"),
            "next_scheduled_visit": next_visit.strftime("%B %d, %Y"),
            "technician": random.choice(["Tom Wilson", "Carlos Rodriguez", "Mike Thompson", "Sarah Davis"]),
            "status": random.choice(["Active - Ongoing Treatment", "Active - Monitoring", "Scheduled Follow-up"]),
            "notes": "All areas treated. Monitoring stations placed around perimeter."
        }

        return json.dumps({
            "status": "success",
            "lead_details": lead_details,
            "message": f"Job {job_id}: {lead_details['service_type']} at {lead_details['address']}"
        })

    @agents.function_tool()
    async def generate_appointment_slots(self, context: agents.RunContext, address: str, service_type: str, reasoning_for_tool_call: str) -> str:
        """
        Generate available appointment time slots for pest control service.

        Args:
            address (str): The customer's address for the service.
            service_type (str): Type of pest control service (inspection, treatment, etc.).
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: Available appointment slots.
        """
        from datetime import datetime, timedelta
        import random

        today = datetime.now()
        slots = []
        current_date = today + timedelta(days=1)
        slot_count = 0

        while slot_count < 6:
            if current_date.weekday() < 5:
                day_name = current_date.strftime("%A")
                date_str = current_date.strftime("%B %d")
                time_options = ["8:00 AM", "10:00 AM", "11:30 AM", "1:00 PM", "2:30 PM", "4:00 PM"]
                available_times = random.sample(time_options, random.randint(1, 3))

                for time_slot in available_times:
                    if slot_count < 6:
                        slots.append({
                            "day": day_name,
                            "date": date_str,
                            "time": time_slot,
                            "slot_id": f"TPC-{current_date.strftime('%m%d')}-{time_slot.replace(':', '').replace(' ', '')}",
                            "technician": random.choice(["Tom Wilson", "Carlos Rodriguez", "Mike Thompson", "Sarah Davis"]),
                            "service_window": "2-hour window"
                        })
                        slot_count += 1

            current_date += timedelta(days=1)

        available_slots = slots[:5]

        return json.dumps({
            "status": "success",
            "service_type": service_type,
            "available_slots": available_slots,
            "message": f"Found {len(available_slots)} available time slots for {service_type} service",
            "notes": "All appointments include free inspection and quote"
        })

    @agents.function_tool()
    async def book_appointment(self, context: agents.RunContext, slot_id: str, day: str, date: str, time: str, address: str, reasoning_for_tool_call: str) -> str:
        """
        Book the selected appointment slot for pest control service.

        Args:
            slot_id (str): Unique identifier for the selected appointment slot.
            day (str): Day of the week for the appointment.
            date (str): Date of the appointment.
            time (str): Time of the appointment.
            address (str): Customer's address for the service.
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: Appointment booking confirmation.
        """
        import random

        appointment_id = f"TPC-{random.randint(10000, 99999)}"
        technician_name = random.choice(["Tom Wilson", "Carlos Rodriguez", "Mike Thompson", "Sarah Davis", "Jennifer Martinez"])

        booking_details = {
            "appointment_id": appointment_id,
            "confirmation_number": f"CONF-{random.randint(1000, 9999)}",
            "day": day,
            "date": date,
            "time": time,
            "service_window": "2-hour window",
            "address": address,
            "technician_name": technician_name,
            "service_type": "Pest Control Service",
            "estimated_duration": "1-3 hours depending on service",
            "what_to_expect": "Free inspection, detailed quote, and treatment if approved",
            "confirmation_sms": "Text confirmation sent within 10 minutes",
            "phone_reminder": "Call reminder 24 hours before appointment",
            "preparation_notes": "Please ensure access to all areas requiring inspection"
        }

        return json.dumps({
            "status": "success",
            "booking_details": booking_details,
            "message": f"Pest control appointment successfully booked for {day}, {date} at {time}",
            "next_steps": "You'll receive confirmation via text and email. Our technician will call 30 minutes before arrival."
        })

    @agents.function_tool()
    async def raise_callback_request(self, context: agents.RunContext, customer_phone: str, preferred_time: str, reason: str, reasoning_for_tool_call: str) -> str:
        """
        Request a callback from the scheduling manager when no suitable appointment slots are available.

        Args:
            customer_phone (str): Customer's phone number for callback.
            preferred_time (str): Customer's preferred callback time.
            reason (str): Reason for callback (e.g., no available slots, emergency).
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: Callback request confirmation.
        """
        import random
        from datetime import datetime, timedelta

        callback_id = f"TCB-{random.randint(10000, 99999)}"

        if "emergency" in reason.lower() or "urgent" in reason.lower():
            callback_time = datetime.now() + timedelta(minutes=random.randint(15, 30))
            priority = "urgent"
        else:
            callback_time = datetime.now() + timedelta(minutes=random.randint(30, 120))
            priority = "standard"

        manager_name = random.choice([
            "Jennifer Adams - Scheduling Manager",
            "Robert Martinez - Senior Coordinator",
            "Susan Williams - Customer Success Manager",
            "Michael Brown - Regional Manager"
        ])

        callback_details = {
            "callback_id": callback_id,
            "customer_phone": customer_phone,
            "preferred_time": preferred_time,
            "scheduled_callback_time": callback_time.strftime("%I:%M %p today"),
            "manager_name": manager_name.split(" - ")[0],
            "manager_title": manager_name.split(" - ")[1],
            "reason": reason,
            "status": "scheduled",
            "priority": priority,
            "reference_number": f"REF-{random.randint(1000, 9999)}",
            "estimated_wait": "15-45 minutes" if priority == "urgent" else "30-90 minutes"
        }

        return json.dumps({
            "status": "success",
            "callback_details": callback_details,
            "message": f"Priority callback scheduled with {callback_details['manager_name']} within {callback_details['estimated_wait']}",
            "instructions": "Please keep your phone available. Our manager will call from a Torkin Pest Control number."
        })

    @agents.function_tool()
    async def transfer_to_team(self, context: agents.RunContext, department: str, reason: str, customer_info: str, reasoning_for_tool_call: str) -> str:
        """
        Transfer the customer to a specialized team department for advanced assistance.

        Args:
            department (str): Target department (sales, technical, billing, management).
            reason (str): Reason for transfer.
            customer_info (str): Brief customer information for context.
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: Transfer confirmation details.
        """
        import random
        from datetime import datetime

        transfer_id = f"TXF-{random.randint(10000, 99999)}"

        departments = {
            "sales": {
                "team_name": "Sales & Estimates Team",
                "specialists": ["David Chen - Senior Sales Specialist", "Maria Rodriguez - Commercial Estimates Manager"],
                "avg_wait": "2-5 minutes",
                "specialty": "pricing, service packages, and contract negotiations"
            },
            "technical": {
                "team_name": "Technical Support Team",
                "specialists": ["Mark Wilson - Lead Technician Supervisor", "Lisa Park - IPM Specialist"],
                "avg_wait": "1-3 minutes",
                "specialty": "treatment methods, pest identification, and service issues"
            },
            "billing": {
                "team_name": "Billing & Accounts Team",
                "specialists": ["Robert Kim - Billing Specialist", "Jennifer Martinez - Accounts Manager"],
                "avg_wait": "3-7 minutes",
                "specialty": "payment processing, billing questions, and account management"
            },
            "management": {
                "team_name": "Management Team",
                "specialists": ["Patricia Anderson - Customer Success Manager", "Michael Taylor - Regional Operations Manager"],
                "avg_wait": "5-10 minutes",
                "specialty": "service complaints, escalations, and management decisions"
            }
        }

        dept_info = departments.get(department.lower(), departments["management"])
        assigned_specialist = random.choice(dept_info["specialists"])

        transfer_details = {
            "transfer_id": transfer_id,
            "department": dept_info["team_name"],
            "assigned_specialist": assigned_specialist.split(" - ")[0],
            "specialist_title": assigned_specialist.split(" - ")[1],
            "reason": reason,
            "customer_summary": customer_info,
            "estimated_wait": dept_info["avg_wait"],
            "specialty_area": dept_info["specialty"],
            "transfer_time": datetime.now().strftime("%I:%M %p"),
            "priority": "high" if "urgent" in reason.lower() or "emergency" in reason.lower() else "standard",
            "reference_number": f"REF-{random.randint(1000, 9999)}"
        }

        return json.dumps({
            "status": "transferring",
            "transfer_details": transfer_details,
            "message": f"Transferring you to {transfer_details['assigned_specialist']} in our {transfer_details['department']}",
            "instructions": f"Please hold while I connect you. Estimated wait time: {transfer_details['estimated_wait']}. Your reference number is {transfer_details['reference_number']}."
        })


async def entrypoint(ctx: agents.JobContext):
    # Initialize trace system first
    await tracing.init_trace_system()

    # Add shutdown callback for cleanup
    ctx.add_shutdown_callback(session.on_shutdown)

    try:
        metadata = json.loads(ctx.job.metadata)
    except:
        metadata = {"identity": "sales-lead"}
    logger.info(f"metadata: {metadata}")

    # Original inbound/console logic
    # parse metadata from the Livekit token
    mock_log_guidance = json.loads(metadata["mock_log_guidance"]) if "mock_log_guidance" in metadata else None
    modalities = metadata["modalities"] if "modalities" in metadata else "text_and_audio"
    conversation_id = metadata.get("conversation_id")

    # Gather user information from metadata, if available
    user_id = None
    user_info = {}
    tenant_id = None
    if "identity" in metadata:
        user_id = metadata["identity"]
        user_info = fetching.fetch_user_info(user_id)

    # Extract tenant_id from metadata (provided by SDK)
    if "tenant_id" in metadata:
        tenant_id = metadata["tenant_id"]

    # Connect to establish room connection
    await ctx.connect()

    # Get participants and their info
    participant: rtc.Participant = await ctx.wait_for_participant()

    is_sip_session = False
    if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
        is_sip_session = True
        # for SIP, Livekit token doesn't exist; therefore, metadata also doesn't exist;
        user_phone_number = participant.attributes['sip.phoneNumber']  # e.g. "+15105550100"
        logger.info(f"Phone number: {user_phone_number}")
        user_id = fetching.fetch_user_id_from_phone_number(user_phone_number)
        user_info = fetching.fetch_user_info(user_id)

    # Build and start the session
    mock_log_guidance = metadata.get("mock_log_guidance", None)
    if mock_log_guidance and isinstance(mock_log_guidance, str):
        mock_log_guidance = json.loads(mock_log_guidance)

    my_session_info = session.MySessionInfo(
        conversation_id=conversation_id or common.generate_session_id(),  # Use metadata conversation_id if available
        # tenant info
        tenant_id=tenant_id,
        # for testing
        mock_log_guidance=mock_log_guidance,
        # user info
        user_id=user_id,
        all_devices=user_info["all_devices"],
        country=user_info["country"],
        app_version=user_info["app_version"],
    )
    logger.info(f"Created session info: {asdict(my_session_info)}")

    session_obj = agents.AgentSession[session.MySessionInfo](userdata=my_session_info)

    def conversation_item_handler(event: agents.ConversationItemAddedEvent):
        asyncio.create_task(session.on_conversation_item_added(event, session_obj))
    session_obj.on("conversation_item_added")(conversation_item_handler)

    logger.info(f"Joining room: {ctx.room.name}")

    # Fetch agent configuration from database
    logger.info("Fetching agent configuration from database...")
    agent_config = await fetch_agent_config(ctx.room.name)
    logger.info(f"Agent config retrieved: {agent_config.get('agent_name', 'Unknown')}")

    # For inbound calls, always use audio mode
    modalities = metadata.get("modalities", "text_and_audio")
    if is_sip_session or modalities != "text_only":
        room_input_options = agents.RoomInputOptions(text_enabled=True, audio_enabled=True)
        room_output_options = agents.RoomOutputOptions(transcription_enabled=True, audio_enabled=True)
    else:
        room_input_options = agents.RoomInputOptions(text_enabled=True, audio_enabled=False)
        room_output_options = agents.RoomOutputOptions(transcription_enabled=True, audio_enabled=False)

    # Choose agent based on config mode
    if agent_config.get("mode") == "squad":
        logger.info(f"Squad mode detected: {agent_config.get('squad_name', 'Unknown Squad')}")
        agent = SquadOrchestrator(room=ctx.room, squad_config=agent_config, is_sip_session=is_sip_session)
    else:
        agent = Assistant(room=ctx.room, agent_config=agent_config, is_sip_session=is_sip_session)

    await session_obj.start(
        room=ctx.room,
        agent=agent,
        room_input_options=room_input_options,
        room_output_options=room_output_options
    )


if __name__ == "__main__":
    logger.info(f"Starting agent... {os.getenv('AGENT_NAME','XXX de nada XXX')}")
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint, agent_name=os.getenv("AGENT_NAME"))
    )
    