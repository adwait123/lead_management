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
        "prompt_template": """You are Mike, a friendly and professional customer service representative for AILead Services.

When greeting callers, introduce yourself as Mike. Your role is to:
- Greet callers warmly saying "Hi, this is Mike from AILead Services" and identify their needs
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
                                                   f"Hi, this is {agent_name} from AILead Services. How can I help you today?")

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
    async def generate_appointment_slots(self, context: agents.RunContext, address: str, project_type: str, reasoning_for_tool_call: str) -> str:
        """
        Generate available appointment time slots for design consultation.

        Args:
            address (str): The customer's address for the consultation.
            project_type (str): Type of flooring project.
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: Available appointment slots.
        """
        from datetime import datetime, timedelta

        # Generate dummy appointment slots - next 3 business days
        today = datetime.now()
        slots = []

        # Find next 3 business days
        current_date = today + timedelta(days=1)
        while len(slots) < 3:
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                day_name = current_date.strftime("%A")
                date_str = current_date.strftime("%B %d")

                # Morning and afternoon slots
                morning_time = "10:00 AM"
                afternoon_time = "2:00 PM"

                slots.append({
                    "day": day_name,
                    "date": date_str,
                    "time": morning_time,
                    "slot_id": f"slot_{len(slots)+1}"
                })

                if len(slots) < 3:
                    slots.append({
                        "day": day_name,
                        "date": date_str,
                        "time": afternoon_time,
                        "slot_id": f"slot_{len(slots)+1}"
                    })

            current_date += timedelta(days=1)

        # Return only the first 3 slots
        available_slots = slots[:3]

        result_message = json.dumps({
            "status": "success",
            "available_slots": available_slots,
            "message": f"Found {len(available_slots)} available consultation slots"
        })

        return result_message

    @agents.function_tool()
    async def book_appointment(self, context: agents.RunContext, slot_id: str, day: str, date: str, time: str, address: str, reasoning_for_tool_call: str) -> str:
        """
        Book the selected appointment slot for design consultation.

        Args:
            slot_id (str): Unique identifier for the selected appointment slot.
            day (str): Day of the week for the appointment.
            date (str): Date of the appointment.
            time (str): Time of the appointment.
            address (str): Customer's address for the consultation.
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: Appointment booking confirmation.
        """
        import random

        # Generate dummy appointment confirmation
        appointment_id = f"FCI-{random.randint(10000, 99999)}"
        consultant_name = random.choice(["Sarah Johnson", "Mike Thompson", "Lisa Chen", "David Rodriguez"])

        booking_details = {
            "appointment_id": appointment_id,
            "day": day,
            "date": date,
            "time": time,
            "address": address,
            "consultant_name": consultant_name,
            "service_type": "Free In-Home Design Consultation",
            "duration": "60-90 minutes",
            "confirmation_sms": "Will be sent within 15-20 minutes"
        }

        result_message = json.dumps({
            "status": "success",
            "booking_details": booking_details,
            "message": f"Appointment successfully booked for {day}, {date} at {time}"
        })

        return result_message

    @agents.function_tool()
    async def raise_callback_request(self, context: agents.RunContext, customer_phone: str, preferred_time: str, reason: str, reasoning_for_tool_call: str) -> str:
        """
        Request a callback from the scheduling manager when no suitable appointment slots are available.

        Args:
            customer_phone (str): Customer's phone number for callback.
            preferred_time (str): Customer's preferred callback time.
            reason (str): Reason for callback (e.g., no available slots).
            reasoning_for_tool_call (str): The agent's reasoning for the tool call.

        Returns:
            str: Callback request confirmation.
        """
        import random
        from datetime import datetime, timedelta

        # Generate dummy callback request details
        callback_id = f"CB-{random.randint(10000, 99999)}"
        callback_time = datetime.now() + timedelta(minutes=random.randint(30, 60))
        manager_name = random.choice(["Jennifer Adams", "Robert Martinez", "Susan Williams", "Michael Brown"])

        callback_details = {
            "callback_id": callback_id,
            "customer_phone": customer_phone,
            "scheduled_callback_time": callback_time.strftime("%I:%M %p"),
            "manager_name": manager_name,
            "reason": reason,
            "status": "scheduled",
            "priority": "high"
        }

        result_message = json.dumps({
            "status": "success",
            "callback_details": callback_details,
            "message": f"Callback scheduled with {manager_name} within the next hour at {callback_time.strftime('%I:%M %p')}"
        })

        return result_message


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

    await session_obj.start(
        room=ctx.room,
        agent=Assistant(room=ctx.room, agent_config=agent_config, is_sip_session=is_sip_session),
        room_input_options=room_input_options,
        room_output_options=room_output_options
    )


if __name__ == "__main__":
    logger.info(f"Starting agent... {os.getenv('AGENT_NAME','XXX de nada XXX')}")
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint, agent_name=os.getenv("AGENT_NAME"))
    )
    