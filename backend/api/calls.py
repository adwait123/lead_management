"""
Calls API endpoints for outbound calling functionality
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import Optional, List, Dict, Any
import math
import logging
from datetime import datetime
from pydantic import ValidationError

from models.database import get_db
from models.call import Call
from models.lead import Lead
from models.agent import Agent
from models.schemas import (
    CallCreateSchema,
    CallUpdateSchema,
    CallResponseSchema,
    CallListResponseSchema,
    CallTriggerSchema
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calls", tags=["calls"])


@router.get("/", response_model=CallListResponseSchema)
async def get_calls(
    call_status: Optional[str] = Query(None),
    lead_id: Optional[int] = Query(None),
    agent_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all calls with filtering and pagination"""

    # Build query
    query = db.query(Call)

    # Apply filters
    if call_status:
        query = query.filter(Call.call_status == call_status)
    if lead_id:
        query = query.filter(Call.lead_id == lead_id)
    if agent_id:
        query = query.filter(Call.agent_id == agent_id)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    calls = query.order_by(Call.initiated_at.desc()).offset(offset).limit(per_page).all()

    # Calculate total pages
    total_pages = math.ceil(total / per_page)

    # Convert calls to response schema
    valid_calls = []
    for call in calls:
        try:
            valid_calls.append(CallResponseSchema.from_orm(call))
        except ValidationError as e:
            logger.warning(f"Skipping call {call.id} due to validation error: {e}")
            continue

    return CallListResponseSchema(
        calls=valid_calls,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/{call_id}", response_model=CallResponseSchema)
async def get_call(call_id: int, db: Session = Depends(get_db)):
    """Get a specific call by ID"""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    try:
        return CallResponseSchema.from_orm(call)
    except ValidationError as e:
        logger.error(f"Call {call_id} has invalid data: {e}")
        raise HTTPException(status_code=422, detail=f"Call data validation failed: {str(e)}")


@router.get("/lead/{lead_id}", response_model=CallListResponseSchema)
async def get_calls_for_lead(
    lead_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get all calls for a specific lead"""

    # Verify lead exists
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Build query for calls
    query = db.query(Call).filter(Call.lead_id == lead_id)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    calls = query.order_by(Call.initiated_at.desc()).offset(offset).limit(per_page).all()

    # Calculate total pages
    total_pages = math.ceil(total / per_page)

    # Convert calls to response schema
    valid_calls = []
    for call in calls:
        try:
            valid_calls.append(CallResponseSchema.from_orm(call))
        except ValidationError as e:
            logger.warning(f"Skipping call {call.id} due to validation error: {e}")
            continue

    return CallListResponseSchema(
        calls=valid_calls,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.post("/trigger/{lead_id}")
async def trigger_outbound_call(
    lead_id: int,
    trigger_data: CallTriggerSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger an outbound call to a lead"""

    # Verify lead exists and has phone number
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not lead.phone:
        raise HTTPException(status_code=400, detail="Lead has no phone number")

    # Demo restriction: Only allow calls for Torkin leads
    if not trigger_data.force_call and lead.source != "torkin":
        raise HTTPException(
            status_code=400,
            detail="Demo mode: Outbound calling only available for 'torkin' leads"
        )

    # Find appropriate outbound calling agent
    agent_query = db.query(Agent).filter(
        Agent.is_active == True,
        Agent.type == "outbound"
    )

    # Filter by communication mode if agent supports it
    agent_query = agent_query.filter(
        or_(
            Agent.conversation_settings.op('->>')('communicationMode') == 'voice',
            Agent.conversation_settings.op('->>')('communicationMode') == 'both'
        )
    )

    if trigger_data.agent_id:
        agent = agent_query.filter(Agent.id == trigger_data.agent_id).first()
    else:
        agent = agent_query.first()

    if not agent:
        raise HTTPException(status_code=400, detail="No suitable outbound calling agent found")

    # Check if there's already a pending or in-progress call for this lead
    existing_call = db.query(Call).filter(
        Call.lead_id == lead_id,
        Call.call_status.in_(["pending", "calling", "in_progress"])
    ).first()

    if existing_call and not trigger_data.force_call:
        raise HTTPException(
            status_code=400,
            detail=f"Call already in progress (Call ID: {existing_call.id})"
        )

    # Create call record
    call = Call(
        lead_id=lead_id,
        agent_id=agent.id,
        phone_number=lead.phone,
        call_status="pending",
        call_metadata={
            "lead_source": lead.source,
            "triggered_by": "api",
            "agent_name": agent.name,
            "demo_mode": True
        }
    )

    db.add(call)
    db.commit()
    db.refresh(call)

    # Schedule the actual call dispatch as background task
    background_tasks.add_task(dispatch_outbound_call, call.id)

    return {
        "success": True,
        "call_id": call.id,
        "message": f"Outbound call scheduled for {lead.first_name or lead.name or 'lead'} ({lead.phone})",
        "agent": agent.name,
        "demo_notice": "Demo mode: Using hardcoded prompt for Torkin integration"
    }


@router.put("/{call_id}", response_model=CallResponseSchema)
async def update_call(call_id: int, call_data: CallUpdateSchema, db: Session = Depends(get_db)):
    """Update call status, transcript, or metadata"""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    # Update only provided fields
    update_data = call_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(call, field, value)

    # Update timestamps based on status changes
    if call_data.call_status:
        if call_data.call_status == "in_progress" and not call.answered_at:
            call.answered_at = datetime.utcnow()
        elif call_data.call_status in ["completed", "failed", "no_answer"] and not call.ended_at:
            call.ended_at = datetime.utcnow()

    db.commit()
    db.refresh(call)

    try:
        return CallResponseSchema.from_orm(call)
    except ValidationError as e:
        logger.error(f"Updated call {call_id} has invalid data: {e}")
        raise HTTPException(status_code=422, detail=f"Call data validation failed: {str(e)}")


@router.get("/{call_id}/transcript")
async def get_call_transcript(call_id: int, db: Session = Depends(get_db)):
    """Get the transcript for a specific call"""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    return {
        "call_id": call_id,
        "transcript": call.transcript,
        "call_summary": call.call_summary,
        "call_duration": call.call_duration,
        "call_status": call.call_status
    }


@router.get("/stats/overview")
async def get_call_stats(db: Session = Depends(get_db)):
    """Get call statistics overview"""
    total_calls = db.query(Call).count()
    completed_calls = db.query(Call).filter(Call.call_status == "completed").count()
    failed_calls = db.query(Call).filter(Call.call_status == "failed").count()
    in_progress_calls = db.query(Call).filter(Call.call_status.in_(["pending", "calling", "in_progress"])).count()

    success_rate = (completed_calls / total_calls * 100) if total_calls > 0 else 0

    return {
        "total_calls": total_calls,
        "completed_calls": completed_calls,
        "failed_calls": failed_calls,
        "in_progress_calls": in_progress_calls,
        "success_rate": round(success_rate, 1)
    }


async def dispatch_outbound_call(call_id: int):
    """Background task to dispatch the actual outbound call"""
    # Create a new database session for this background task
    from models.database import SessionLocal
    db = SessionLocal()

    try:
        # Import here to avoid circular imports
        from services.outbound_call_service import OutboundCallService

        call_service = OutboundCallService(db)
        success = await call_service.dispatch_call(call_id)

        if success:
            logger.info(f"Successfully dispatched outbound call {call_id}")
        else:
            logger.error(f"Failed to dispatch outbound call {call_id}")

    except Exception as e:
        logger.error(f"Error dispatching outbound call {call_id}: {str(e)}")

        # Update call status to failed
        call = db.query(Call).filter(Call.id == call_id).first()
        if call:
            call.call_status = "failed"
            call.error_message = str(e)
            call.ended_at = datetime.utcnow()
            db.commit()
    finally:
        # Always close the database session
        db.close()