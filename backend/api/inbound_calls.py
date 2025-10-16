"""
Inbound Calls API endpoints for inbound calling functionality
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Form
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
    """Handle Twilio webhook for inbound calls"""

    logger.info(f"Received Twilio webhook: {webhook_data.dict()}")

    # Create or update inbound call record
    existing_call = db.query(InboundCall).filter(
        InboundCall.twilio_call_sid == webhook_data.CallSid
    ).first()

    if existing_call:
        # Update existing call
        existing_call.call_status = webhook_data.CallStatus.lower()
        db.commit()
        call_id = existing_call.id
    else:
        # Create new inbound call record
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
                "api_version": webhook_data.ApiVersion
            }
        )

        db.add(inbound_call)
        db.commit()
        db.refresh(inbound_call)
        call_id = inbound_call.id

        # Process new inbound call
        background_tasks.add_task(process_inbound_call, call_id)

    return {"status": "success", "call_id": call_id}


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


# Background tasks
async def process_inbound_call(call_id: int):
    """Background task to process inbound call (create lead, assign agent, etc.)"""
    from models.database import SessionLocal
    db = SessionLocal()

    try:
        # Import here to avoid circular imports
        from services.inbound_call_service import InboundCallService

        call_service = InboundCallService(db)
        success = await call_service.process_call(call_id)

        if success:
            logger.info(f"Successfully processed inbound call {call_id}")
        else:
            logger.error(f"Failed to process inbound call {call_id}")

    except Exception as e:
        logger.error(f"Error processing inbound call {call_id}: {str(e)}")

        # Update call status to failed
        call = db.query(InboundCall).filter(InboundCall.id == call_id).first()
        if call:
            call.call_status = "failed"
            call.error_message = str(e)
            call.ended_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


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