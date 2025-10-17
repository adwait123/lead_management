"""
Inbound Calls API endpoints for inbound calling functionality
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Form, Response
from twilio.twiml.voice_response import VoiceResponse, Connect, Dial
import os
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import Optional, List, Dict, Any
import math
import logging
from datetime import datetime
from pydantic import ValidationError

from models.database import get_db
from models.inbound_call import InboundCall
from models.lead import Lead
from models.agent import Agent
from models.agent_session import AgentSession
from models.message import Message
from models.schemas import (
    InboundCallCreateSchema,
    InboundCallUpdateSchema,
    InboundCallResponseSchema,
    InboundCallListResponseSchema,
    InboundCallFiltersSchema,
    TwilioWebhookSchema,
    LiveKitWebhookSchema
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inbound-calls", tags=["inbound-calls"])


# Helper functions for lead management
def validate_phone_number(phone: str) -> Optional[str]:
    """
    Validate and format phone number for inbound calls.
    """
    import re

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


async def find_or_create_lead(phone_number: str, db: Session) -> Optional[Lead]:
    """
    Find existing lead by phone number or create a new one.
    """
    try:
        # Validate phone number
        validated_phone = validate_phone_number(phone_number)
        if not validated_phone:
            logger.warning(f"Invalid phone number: {phone_number}")
            validated_phone = phone_number  # Use as-is if validation fails

        # Try to find existing lead by phone
        existing_lead = db.query(Lead).filter(Lead.phone == validated_phone).first()
        if existing_lead:
            logger.info(f"Found existing lead {existing_lead.id} for phone {validated_phone}")
            # Update status to contacted if it was new
            if existing_lead.status == "new":
                existing_lead.status = "contacted"
                db.commit()
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

        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)

        logger.info(f"Created new lead {new_lead.id} for phone {validated_phone}")
        return new_lead

    except Exception as e:
        logger.error(f"Error finding/creating lead for {phone_number}: {str(e)}")
        return None


async def create_agent_session_for_call(call: InboundCall, lead: Lead, agent: Agent, db: Session) -> bool:
    """
    Create an agent session for conversation tracking.
    """
    try:
        # Check if session already exists
        existing_session = db.query(AgentSession).filter(
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
                "room_name": call.room_name,
                "routing_method": "livekit_sip_trunk"
            },
            session_metadata={
                "source": "inbound_call",
                "call_initiated_at": call.received_at.isoformat(),
                "agent_type": agent.type
            },
            auto_timeout_hours=2,  # Shorter timeout for phone calls
            max_message_count=50   # Reasonable limit for voice conversations
        )

        db.add(session)
        db.commit()
        db.refresh(session)

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

        db.add(system_message)
        db.commit()

        logger.info(f"Created agent session {session.id} for inbound call {call.id}")
        return True

    except Exception as e:
        logger.error(f"Failed to create agent session for call {call.id}: {str(e)}")
        return False


async def trigger_lead_workflow_for_call(lead: Lead, db: Session) -> bool:
    """
    Trigger the existing workflow system for new leads.
    """
    try:
        # Import here to avoid circular imports
        from services.workflow_service import WorkflowService

        workflow_service = WorkflowService(db)
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


async def process_inbound_call_background(call_id: int):
    """
    Background task to process inbound call - create lead and agent session
    after TwiML response is sent to avoid blocking the webhook response.
    """
    from models.database import SessionLocal
    db = SessionLocal()

    try:
        # Get the inbound call record
        call = db.query(InboundCall).filter(InboundCall.id == call_id).first()
        if not call:
            logger.error(f"Inbound call {call_id} not found for background processing")
            return

        logger.info(f"Background processing inbound call {call_id} from {call.caller_phone_number}")

        # Step 1: Find or create lead
        lead = await find_or_create_lead(call.caller_phone_number, db)
        if not lead:
            logger.error(f"Failed to create/find lead for {call.caller_phone_number}")
            call.call_status = "failed"
            call.error_message = "Failed to create lead"
            db.commit()
            return

        # Step 2: Find active inbound agent
        inbound_agent = db.query(Agent).filter(
            Agent.type == "inbound",
            Agent.is_active == True
        ).first()

        if not inbound_agent:
            logger.warning(f"No active inbound agents available for call {call_id}")
            # Don't fail the call, just continue without agent assignment
        else:
            # Step 3: Update call with lead and agent information
            call.agent_id = inbound_agent.id

            # Step 4: Create agent session for conversation tracking
            session_created = await create_agent_session_for_call(call, lead, inbound_agent, db)
            if not session_created:
                logger.warning(f"Failed to create agent session for call {call_id}")
                # Not critical - continue processing

        # Always update the call with lead ID regardless of agent availability
        call.lead_id = lead.id

        # Update call metadata to include lead info
        current_metadata = call.call_metadata or {}
        current_metadata.update({
            "lead_id": lead.id,
            "lead_name": lead.name,
            "lead_phone": lead.phone,
            "lead_status": lead.status,
            "lead_source": lead.source,
            "background_processed": True,
            "processed_at": datetime.utcnow().isoformat()
        })
        call.call_metadata = current_metadata

        db.commit()

        # Step 5: Trigger workflow for new lead (if applicable)
        if lead.status == "new":
            await trigger_lead_workflow_for_call(lead, db)

        logger.info(f"Successfully background processed inbound call {call_id} - Lead: {lead.id}, Agent: {call.agent_id}")

    except Exception as e:
        logger.error(f"Error in background processing of inbound call {call_id}: {str(e)}")
        if call:
            call.call_status = "failed"
            call.error_message = f"Background processing error: {str(e)}"
            db.commit()
    finally:
        db.close()


@router.get("/", response_model=InboundCallListResponseSchema)
async def get_inbound_calls(
    call_status: Optional[str] = Query(None),
    caller_phone_number: Optional[str] = Query(None),
    lead_id: Optional[int] = Query(None),
    agent_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all inbound calls with filtering and pagination"""

    # Build query
    query = db.query(InboundCall)

    # Apply filters
    if call_status:
        query = query.filter(InboundCall.call_status == call_status)
    if caller_phone_number:
        query = query.filter(InboundCall.caller_phone_number.ilike(f"%{caller_phone_number}%"))
    if lead_id:
        query = query.filter(InboundCall.lead_id == lead_id)
    if agent_id:
        query = query.filter(InboundCall.agent_id == agent_id)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    inbound_calls = query.order_by(InboundCall.received_at.desc()).offset(offset).limit(per_page).all()

    # Calculate total pages
    total_pages = math.ceil(total / per_page)

    # Convert inbound calls to response schema
    valid_calls = []
    for call in inbound_calls:
        try:
            valid_calls.append(InboundCallResponseSchema.model_validate(call))
        except ValidationError as e:
            logger.warning(f"Skipping inbound call {call.id} due to validation error: {e}")
            continue

    return InboundCallListResponseSchema(
        inbound_calls=valid_calls,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/{call_id}", response_model=InboundCallResponseSchema)
async def get_inbound_call(call_id: int, db: Session = Depends(get_db)):
    """Get a specific inbound call by ID"""
    call = db.query(InboundCall).filter(InboundCall.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Inbound call not found")

    try:
        return InboundCallResponseSchema.model_validate(call)
    except ValidationError as e:
        logger.error(f"Inbound call {call_id} has invalid data: {e}")
        raise HTTPException(status_code=422, detail=f"Inbound call data validation failed: {str(e)}")


@router.get("/lead/{lead_id}", response_model=InboundCallListResponseSchema)
async def get_inbound_calls_for_lead(
    lead_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get all inbound calls for a specific lead"""

    # Verify lead exists
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Build query for inbound calls
    query = db.query(InboundCall).filter(InboundCall.lead_id == lead_id)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    inbound_calls = query.order_by(InboundCall.received_at.desc()).offset(offset).limit(per_page).all()

    # Calculate total pages
    total_pages = math.ceil(total / per_page)

    # Convert inbound calls to response schema
    valid_calls = []
    for call in inbound_calls:
        try:
            valid_calls.append(InboundCallResponseSchema.model_validate(call))
        except ValidationError as e:
            logger.warning(f"Skipping inbound call {call.id} due to validation error: {e}")
            continue

    return InboundCallListResponseSchema(
        inbound_calls=valid_calls,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/phone/{phone_number}", response_model=InboundCallListResponseSchema)
async def get_inbound_calls_by_phone(
    phone_number: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get all inbound calls from a specific phone number"""

    # Build query for inbound calls
    query = db.query(InboundCall).filter(InboundCall.caller_phone_number == phone_number)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    inbound_calls = query.order_by(InboundCall.received_at.desc()).offset(offset).limit(per_page).all()

    # Calculate total pages
    total_pages = math.ceil(total / per_page)

    # Convert inbound calls to response schema
    valid_calls = []
    for call in inbound_calls:
        try:
            valid_calls.append(InboundCallResponseSchema.model_validate(call))
        except ValidationError as e:
            logger.warning(f"Skipping inbound call {call.id} due to validation error: {e}")
            continue

    return InboundCallListResponseSchema(
        inbound_calls=valid_calls,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.post("/", response_model=InboundCallResponseSchema)
async def create_inbound_call(
    call_data: InboundCallCreateSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new inbound call record"""

    # Create inbound call record
    inbound_call = InboundCall(
        caller_phone_number=call_data.caller_phone_number,
        inbound_phone_number=call_data.inbound_phone_number,
        call_status=call_data.call_status,
        lead_id=call_data.lead_id,
        agent_id=call_data.agent_id,
        twilio_call_sid=call_data.twilio_call_sid,
        livekit_call_id=call_data.livekit_call_id,
        call_metadata=call_data.call_metadata or {}
    )

    db.add(inbound_call)
    db.commit()
    db.refresh(inbound_call)

    # Process the inbound call in background
    background_tasks.add_task(process_inbound_call, inbound_call.id)

    try:
        return InboundCallResponseSchema.model_validate(inbound_call)
    except ValidationError as e:
        logger.error(f"Created inbound call {inbound_call.id} has invalid data: {e}")
        raise HTTPException(status_code=422, detail=f"Inbound call data validation failed: {str(e)}")


@router.put("/{call_id}", response_model=InboundCallResponseSchema)
async def update_inbound_call(call_id: int, call_data: InboundCallUpdateSchema, db: Session = Depends(get_db)):
    """Update inbound call status, transcript, or metadata"""
    call = db.query(InboundCall).filter(InboundCall.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Inbound call not found")

    # Update only provided fields
    update_data = call_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(call, field, value)

    # Update timestamps based on status changes
    if call_data.call_status:
        if call_data.call_status == "answered" and not call.answered_at:
            call.answered_at = datetime.utcnow()
        elif call_data.call_status in ["completed", "failed", "no_answer", "rejected"] and not call.ended_at:
            call.ended_at = datetime.utcnow()

    db.commit()
    db.refresh(call)

    try:
        return InboundCallResponseSchema.model_validate(call)
    except ValidationError as e:
        logger.error(f"Updated inbound call {call_id} has invalid data: {e}")
        raise HTTPException(status_code=422, detail=f"Inbound call data validation failed: {str(e)}")


@router.get("/{call_id}/transcript")
async def get_inbound_call_transcript(call_id: int, db: Session = Depends(get_db)):
    """Get the transcript for a specific inbound call"""
    call = db.query(InboundCall).filter(InboundCall.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Inbound call not found")

    return {
        "call_id": call_id,
        "transcript": call.transcript,
        "call_summary": call.call_summary,
        "call_duration": call.call_duration,
        "call_status": call.call_status,
        "caller_phone_number": call.caller_phone_number
    }


@router.get("/agent-config/{call_id}")
async def get_agent_config_for_call(call_id: int, db: Session = Depends(get_db)):
    """Get agent configuration for a specific inbound call - used by inbound_raq agent"""

    # Find the inbound call
    inbound_call = db.query(InboundCall).filter(InboundCall.id == call_id).first()
    if not inbound_call:
        raise HTTPException(status_code=404, detail="Inbound call not found")

    # Get the assigned agent
    agent = None
    if inbound_call.agent_id:
        agent = db.query(Agent).filter(Agent.id == inbound_call.agent_id).first()

    # If no specific agent assigned, get default inbound agent
    if not agent:
        agent = db.query(Agent).filter(
            Agent.type == "inbound",
            Agent.is_active == True
        ).first()

    if not agent:
        raise HTTPException(status_code=404, detail="No inbound agent available")

    # Get lead information
    lead = None
    if inbound_call.lead_id:
        lead = db.query(Lead).filter(Lead.id == inbound_call.lead_id).first()

    # Build agent configuration response
    config = {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "agent_type": agent.type,
        "call_id": call_id,
        "call_metadata": inbound_call.call_metadata or {},

        # Core agent configuration
        "prompt_template": agent.prompt_template,
        "prompt_variables": agent.prompt_variables or {},
        "personality_traits": agent.personality_traits or [],
        "personality_style": agent.personality_style or "professional",
        "response_length": agent.response_length or "moderate",
        "custom_personality_instructions": agent.custom_personality_instructions,

        # AI model settings
        "model": agent.model or "gpt-3.5-turbo",
        "temperature": float(agent.temperature) if agent.temperature else 0.7,
        "max_tokens": agent.max_tokens or 500,

        # Conversation settings
        "conversation_settings": agent.conversation_settings or {},

        # Lead context (if available)
        "lead_context": {
            "lead_id": lead.id if lead else None,
            "first_name": lead.first_name if lead else "Caller",
            "last_name": lead.last_name if lead else "",
            "phone": lead.phone if lead else inbound_call.caller_phone_number,
            "company": lead.company if lead else None,
            "service_requested": lead.service_requested if lead else "Phone inquiry",
            "source": lead.source if lead else "phone_call",
            "status": lead.status if lead else "new"
        },

        # Call context
        "call_context": {
            "caller_phone": inbound_call.caller_phone_number,
            "inbound_phone": inbound_call.inbound_phone_number,
            "call_status": inbound_call.call_status,
            "room_name": inbound_call.room_name,
            "received_at": inbound_call.received_at.isoformat() if inbound_call.received_at else None
        },

        # Business context
        "business_context": {
            "company_name": "AILead Services",
            "phone_number": "+17622437375",
            "services": ["Lead Management", "Customer Support", "Business Automation"]
        }
    }

    return config


@router.post("/agent-config/update-session")
async def update_agent_session_from_call(
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update agent session with conversation data from inbound_raq agent"""

    call_id = update_data.get("call_id")
    message_content = update_data.get("message_content")
    message_type = update_data.get("message_type", "text")
    sender_type = update_data.get("sender_type", "agent")

    if not call_id:
        raise HTTPException(status_code=400, detail="call_id is required")

    # Find the inbound call
    inbound_call = db.query(InboundCall).filter(InboundCall.id == call_id).first()
    if not inbound_call:
        raise HTTPException(status_code=404, detail="Inbound call not found")

    # Find the agent session
    session = None
    if inbound_call.lead_id and inbound_call.agent_id:
        session = db.query(AgentSession).filter(
            AgentSession.lead_id == inbound_call.lead_id,
            AgentSession.agent_id == inbound_call.agent_id,
            AgentSession.session_status == "active"
        ).first()

    if session and message_content:
        # Create message record
        if sender_type == "agent":
            message = Message.create_agent_message(
                session_id=session.id,
                lead_id=inbound_call.lead_id,
                agent_id=inbound_call.agent_id,
                content=message_content,
                metadata={
                    "call_id": call_id,
                    "message_type": message_type,
                    "room_name": inbound_call.room_name
                }
            )
        else:
            message = Message.create_lead_message(
                session_id=session.id,
                lead_id=inbound_call.lead_id,
                content=message_content,
                external_id=str(call_id),
                metadata={
                    "call_id": call_id,
                    "message_type": message_type,
                    "phone_number": inbound_call.caller_phone_number
                }
            )

        db.add(message)

        # Update session stats
        session.message_count += 1
        session.last_message_at = datetime.utcnow()
        session.last_message_from = sender_type

        db.commit()

    # Update call metadata if provided
    if "call_status" in update_data:
        inbound_call.call_status = update_data["call_status"]

    if "transcript_segment" in update_data:
        # Append to existing transcript
        current_transcript = inbound_call.transcript or ""
        new_segment = update_data["transcript_segment"]
        inbound_call.transcript = current_transcript + "\n" + new_segment if current_transcript else new_segment

    if "call_summary" in update_data:
        inbound_call.call_summary = update_data["call_summary"]

    db.commit()

    return {"status": "success", "session_id": session.id if session else None}


@router.get("/stats/overview")
async def get_inbound_call_stats(db: Session = Depends(get_db)):
    """Get inbound call statistics overview"""
    total_calls = db.query(InboundCall).count()
    answered_calls = db.query(InboundCall).filter(InboundCall.call_status == "completed").count()
    rejected_calls = db.query(InboundCall).filter(InboundCall.call_status == "rejected").count()
    failed_calls = db.query(InboundCall).filter(InboundCall.call_status == "failed").count()
    active_calls = db.query(InboundCall).filter(
        InboundCall.call_status.in_(["received", "ringing", "answered", "in_progress"])
    ).count()

    answer_rate = (answered_calls / total_calls * 100) if total_calls > 0 else 0

    return {
        "total_calls": total_calls,
        "answered_calls": answered_calls,
        "rejected_calls": rejected_calls,
        "failed_calls": failed_calls,
        "active_calls": active_calls,
        "answer_rate": round(answer_rate, 1)
    }


# Webhook endpoints
@router.post("/webhooks/twilio")
async def handle_twilio_webhook(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...),
    Direction: Optional[str] = Form(None),
    ApiVersion: Optional[str] = Form(None),
    CallerName: Optional[str] = Form(None),
    CallerCity: Optional[str] = Form(None),
    CallerState: Optional[str] = Form(None),
    CallerZip: Optional[str] = Form(None),
    CallerCountry: Optional[str] = Form(None),
):
    """Handle Twilio webhook for inbound calls"""

    webhook_data = TwilioWebhookSchema(
        CallSid=CallSid,
        From=From,
        To=To,
        CallStatus=CallStatus,
        Direction=Direction,
        ApiVersion=ApiVersion,
        CallerName=CallerName,
        CallerCity=CallerCity,
        CallerState=CallerState,
        CallerZip=CallerZip,
        CallerCountry=CallerCountry,
    )

    logger.info(f"Received Twilio webhook: {webhook_data.dict()}")

    # Create or update inbound call record for logging purposes
    existing_call = db.query(InboundCall).filter(
        InboundCall.twilio_call_sid == webhook_data.CallSid
    ).first()

    if existing_call:
        # Update existing call status
        existing_call.call_status = webhook_data.CallStatus.lower()
        db.commit()
        call_id = existing_call.id
    else:
        # Create new inbound call record for logging/tracking
        inbound_call = InboundCall(
            caller_phone_number=webhook_data.From,
            inbound_phone_number=webhook_data.To,
            call_status=webhook_data.CallStatus.lower(),
            twilio_call_sid=webhook_data.CallSid,
            call_metadata={
                "direction": webhook_data.Direction,
                "caller_name": webhook_data.CallerName,
                "caller_city": webhook_data.CallerCity,
                "caller_state": webhook_data.CallerState,
                "caller_country": webhook_data.CallerCountry,
                "api_version": webhook_data.ApiVersion,
                "routing_method": "livekit_sip_trunk"
            }
        )

        db.add(inbound_call)
        db.commit()
        db.refresh(inbound_call)
        call_id = inbound_call.id

        logger.info(f"Created inbound call record {call_id} - routing to LiveKit SIP trunk")

    # Create TwiML response for LiveKit SIP trunk integration
    response = VoiceResponse()

    # Get caller phone number from webhook data
    caller_phone = webhook_data.From

    # Get SIP trunk configuration
    sip_inbound_trunk_id = os.getenv('SIP_INBOUND_TRUNK_ID')
    if not sip_inbound_trunk_id:
        logger.error("SIP_INBOUND_TRUNK_ID environment variable not set")
        response.say("Service configuration error. Please contact support.")
        return Response(content=str(response), media_type="application/xml")

    # Route to LiveKit SIP trunk - LiveKit will handle room creation and agent dispatch
    # Using the configured SIP trunk endpoint
    sip_uri = f"sip:{caller_phone}@1w7n1n4d64r.sip.livekit.cloud;transport=tcp"

    # Use Dial + Sip to route to LiveKit SIP trunk
    dial = Dial(timeout=30)
    dial.sip(sip_uri)
    response.append(dial)

    logger.info(f"Generated TwiML routing to LiveKit SIP trunk: {sip_uri} for call {call_id}")

    # Add background task to process lead creation and agent session after TwiML response
    # This ensures we don't delay the webhook response to Twilio
    background_tasks.add_task(process_inbound_call_background, call_id)

    return Response(content=str(response), media_type="application/xml")


@router.post("/webhooks/livekit")
async def handle_livekit_webhook(
    webhook_data: LiveKitWebhookSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Handle LiveKit webhook for inbound call events"""

    logger.info(f"Received LiveKit webhook: {webhook_data.dict()}")

    # Process different LiveKit events
    if webhook_data.event == "room_started":
        # Handle room started event
        room_name = webhook_data.room.get("name") if webhook_data.room else None
        background_tasks.add_task(handle_livekit_room_started, room_name, webhook_data.dict())

    elif webhook_data.event == "participant_joined":
        # Handle participant joined event
        room_name = webhook_data.room.get("name") if webhook_data.room else None
        participant = webhook_data.participant
        background_tasks.add_task(handle_livekit_participant_joined, room_name, participant)

    elif webhook_data.event == "room_finished":
        # Handle room finished event
        room_name = webhook_data.room.get("name") if webhook_data.room else None
        background_tasks.add_task(handle_livekit_room_finished, room_name, webhook_data.dict())

    return {"status": "success", "event": webhook_data.event}



async def handle_livekit_room_started(room_name: str, event_data: Dict[str, Any]):
    """Handle LiveKit room started event"""
    from models.database import SessionLocal
    db = SessionLocal()

    try:
        # Find inbound call by room name or create new one
        call = db.query(InboundCall).filter(InboundCall.room_name == room_name).first()

        if call:
            call.call_status = "in_progress"
            db.commit()
            logger.info(f"Updated inbound call {call.id} status to in_progress for room {room_name}")
        else:
            logger.warning(f"No inbound call found for room {room_name}")

    except Exception as e:
        logger.error(f"Error handling LiveKit room started for {room_name}: {str(e)}")
    finally:
        db.close()


async def handle_livekit_participant_joined(room_name: str, participant_data: Dict[str, Any]):
    """Handle LiveKit participant joined event"""
    from models.database import SessionLocal
    db = SessionLocal()

    try:
        # Find inbound call and update with participant info
        call = db.query(InboundCall).filter(InboundCall.room_name == room_name).first()

        if call:
            if not call.answered_at:
                call.answered_at = datetime.utcnow()
                call.call_status = "answered"
                db.commit()
                logger.info(f"Marked inbound call {call.id} as answered for room {room_name}")

    except Exception as e:
        logger.error(f"Error handling LiveKit participant joined for {room_name}: {str(e)}")
    finally:
        db.close()


async def handle_livekit_room_finished(room_name: str, event_data: Dict[str, Any]):
    """Handle LiveKit room finished event"""
    from models.database import SessionLocal
    db = SessionLocal()

    try:
        # Find inbound call and mark as completed
        call = db.query(InboundCall).filter(InboundCall.room_name == room_name).first()

        if call:
            call.call_status = "completed"
            if not call.ended_at:
                call.ended_at = datetime.utcnow()

            # Calculate duration if we have start and end times
            if call.answered_at and call.ended_at:
                duration = (call.ended_at - call.answered_at).total_seconds()
                call.call_duration = int(duration)

            db.commit()
            logger.info(f"Marked inbound call {call.id} as completed for room {room_name}")

    except Exception as e:
        logger.error(f"Error handling LiveKit room finished for {room_name}: {str(e)}")
    finally:
        db.close()