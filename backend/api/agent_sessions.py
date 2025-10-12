"""
Agent Sessions API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

from models.database import get_db
from models.agent_session import AgentSession
from models.agent import Agent
from models.lead import Lead
from models.schemas import (
    AgentSessionCreateSchema,
    AgentSessionUpdateSchema,
    AgentSessionResponseSchema,
    AgentSessionListResponseSchema,
    MessageStatsUpdateSchema
)

# Router setup
router = APIRouter(prefix="/api/agent-sessions", tags=["agent-sessions"])

@router.post("/", response_model=AgentSessionResponseSchema)
async def create_agent_session(session_data: AgentSessionCreateSchema, db: Session = Depends(get_db)):
    """Create a new agent session"""

    # Validate agent exists
    agent = db.query(Agent).filter(Agent.id == session_data.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Validate lead exists
    lead = db.query(Lead).filter(Lead.id == session_data.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check if there's already an active session for this lead
    existing_session = db.query(AgentSession).filter(
        and_(
            AgentSession.lead_id == session_data.lead_id,
            AgentSession.session_status == "active"
        )
    ).first()

    if existing_session:
        raise HTTPException(
            status_code=400,
            detail=f"Lead already has an active session (ID: {existing_session.id})"
        )

    # Create new session
    session = AgentSession(
        agent_id=session_data.agent_id,
        lead_id=session_data.lead_id,
        trigger_type=session_data.trigger_type,
        session_goal=session_data.session_goal,
        initial_context=session_data.initial_context or {},
        auto_timeout_hours=session_data.auto_timeout_hours,
        max_message_count=session_data.max_message_count
    )

    try:
        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(f"Created agent session {session.id} for agent {session_data.agent_id} and lead {session_data.lead_id}")

        return AgentSessionResponseSchema.from_orm(session)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating agent session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create agent session")

@router.get("/", response_model=AgentSessionListResponseSchema)
async def list_agent_sessions(
    status: Optional[str] = Query(None, description="Filter by session status"),
    agent_id: Optional[int] = Query(None, description="Filter by agent ID"),
    lead_id: Optional[int] = Query(None, description="Filter by lead ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List agent sessions with optional filters"""

    # Build query
    query = db.query(AgentSession)

    # Apply filters
    if status:
        query = query.filter(AgentSession.session_status == status)
    if agent_id:
        query = query.filter(AgentSession.agent_id == agent_id)
    if lead_id:
        query = query.filter(AgentSession.lead_id == lead_id)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    sessions = query.order_by(AgentSession.created_at.desc()).offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return AgentSessionListResponseSchema(
        sessions=[AgentSessionResponseSchema.from_orm(session) for session in sessions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{session_id}", response_model=AgentSessionResponseSchema)
async def get_agent_session(session_id: int, db: Session = Depends(get_db)):
    """Get a specific agent session by ID"""

    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Agent session not found")

    return AgentSessionResponseSchema.from_orm(session)

@router.get("/lead/{lead_id}/active", response_model=Optional[AgentSessionResponseSchema])
async def get_active_session_for_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get the active agent session for a specific lead"""

    # Validate lead exists
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    session = db.query(AgentSession).filter(
        and_(
            AgentSession.lead_id == lead_id,
            AgentSession.session_status == "active"
        )
    ).first()

    if not session:
        return None

    return AgentSessionResponseSchema.from_orm(session)

@router.put("/{session_id}", response_model=AgentSessionResponseSchema)
async def update_agent_session(
    session_id: int,
    update_data: AgentSessionUpdateSchema,
    db: Session = Depends(get_db)
):
    """Update an agent session"""

    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Agent session not found")

    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(session, field, value)

    # If ending the session, set ended_at timestamp
    if update_data.session_status and update_data.session_status in ["completed", "escalated", "timeout"]:
        session.ended_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(session)

        logger.info(f"Updated agent session {session_id}")
        return AgentSessionResponseSchema.from_orm(session)
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating agent session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update agent session")

@router.post("/{session_id}/message", response_model=AgentSessionResponseSchema)
async def update_message_stats(
    session_id: int,
    message_data: MessageStatsUpdateSchema,
    db: Session = Depends(get_db)
):
    """Update session message statistics when a new message is sent"""

    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Agent session not found")

    if session.session_status != "active":
        raise HTTPException(status_code=400, detail="Cannot update inactive session")

    # Update message stats
    session.update_message_stats(from_agent=message_data.from_agent)

    # Check if session should be escalated
    if session.should_escalate():
        session.session_status = "escalated"
        session.completion_reason = "max_message_count_reached"
        session.ended_at = datetime.utcnow()
        logger.info(f"Session {session_id} auto-escalated due to message count")

    try:
        db.commit()
        db.refresh(session)
        return AgentSessionResponseSchema.from_orm(session)
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating message stats for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update message statistics")

@router.post("/{session_id}/end", response_model=AgentSessionResponseSchema)
async def end_agent_session(
    session_id: int,
    reason: str = Query(..., description="Reason for ending the session"),
    escalated_to: Optional[str] = Query(None, description="Who/what the session was escalated to"),
    db: Session = Depends(get_db)
):
    """End an agent session"""

    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Agent session not found")

    if session.session_status not in ["active", "paused"]:
        raise HTTPException(status_code=400, detail="Session is already ended")

    # End the session
    session.end_session(reason=reason, escalated_to=escalated_to)

    try:
        db.commit()
        db.refresh(session)

        logger.info(f"Ended agent session {session_id} with reason: {reason}")
        return AgentSessionResponseSchema.from_orm(session)
    except Exception as e:
        db.rollback()
        logger.error(f"Error ending agent session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to end agent session")

@router.get("/active/count")
async def get_active_sessions_count(db: Session = Depends(get_db)):
    """Get count of currently active sessions"""

    count = db.query(AgentSession).filter(AgentSession.session_status == "active").count()

    return {"active_sessions": count}

@router.post("/cleanup/timeout")
async def cleanup_timeout_sessions(db: Session = Depends(get_db)):
    """Cleanup sessions that have timed out due to inactivity"""

    # Find sessions eligible for timeout
    timeout_sessions = db.query(AgentSession).filter(
        and_(
            AgentSession.session_status == "active",
            AgentSession.last_message_at.isnot(None)
        )
    ).all()

    updated_count = 0
    for session in timeout_sessions:
        if session.is_timeout_eligible():
            session.session_status = "timeout"
            session.completion_reason = "inactivity_timeout"
            session.ended_at = datetime.utcnow()
            updated_count += 1

    try:
        if updated_count > 0:
            db.commit()
            logger.info(f"Cleaned up {updated_count} timed out sessions")

        return {"sessions_timed_out": updated_count}
    except Exception as e:
        db.rollback()
        logger.error(f"Error cleaning up timeout sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cleanup timeout sessions")