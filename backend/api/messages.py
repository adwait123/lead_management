"""
Messages API endpoints for handling conversation routing and message processing
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

from models.database import get_db
from models.lead import Lead
from models.agent_session import AgentSession
from services.message_router import MessageRouter

# Pydantic schemas for message APIs
class IncomingMessageSchema(BaseModel):
    lead_id: int
    message: str
    message_type: Optional[str] = "text"
    metadata: Optional[Dict[str, Any]] = {}

class MessageRoutingResponseSchema(BaseModel):
    success: bool
    routing_decision: str
    session_id: Optional[int] = None
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    lead_name: Optional[str] = None
    message_count: Optional[int] = None
    session_goal: Optional[str] = None
    should_respond: bool
    agent_context: Optional[Dict[str, Any]] = None
    escalation_reason: Optional[str] = None
    escalation_message: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None

class AgentResponseSchema(BaseModel):
    session_id: int
    response: str
    response_metadata: Optional[Dict[str, Any]] = {}

class SessionContextResponseSchema(BaseModel):
    session_id: int
    agent: Dict[str, Any]
    lead: Dict[str, Any]
    session: Dict[str, Any]

class ConversationHistorySchema(BaseModel):
    session_id: int
    messages: list[Dict[str, Any]]
    agent_name: str
    lead_name: str
    session_status: str

# Router setup
router = APIRouter(prefix="/api/messages", tags=["messages"])

@router.post("/route", response_model=MessageRoutingResponseSchema)
async def route_message(message_data: IncomingMessageSchema, db: Session = Depends(get_db)):
    """Route an incoming message to the appropriate agent session"""

    # Validate lead exists
    lead = db.query(Lead).filter(Lead.id == message_data.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        router_service = MessageRouter(db)
        result = router_service.route_message(
            lead_id=message_data.lead_id,
            message=message_data.message,
            message_type=message_data.message_type,
            metadata=message_data.metadata
        )

        return MessageRoutingResponseSchema(**result)

    except Exception as e:
        logger.error(f"Error routing message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to route message")

@router.post("/agent-response")
async def record_agent_response(response_data: AgentResponseSchema, db: Session = Depends(get_db)):
    """Record an agent's response to update session statistics"""

    try:
        router_service = MessageRouter(db)
        success = router_service.update_agent_response(
            session_id=response_data.session_id,
            response=response_data.response,
            response_metadata=response_data.response_metadata
        )

        if success:
            return {"success": True, "message": "Agent response recorded"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording agent response: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record agent response")

@router.get("/session/{session_id}/context", response_model=SessionContextResponseSchema)
async def get_session_context(session_id: int, db: Session = Depends(get_db)):
    """Get context information for an active session"""

    try:
        router_service = MessageRouter(db)
        context = router_service.get_session_context(session_id)

        if not context:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionContextResponseSchema(**context)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session context: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session context")

@router.get("/lead/{lead_id}/active-session")
async def get_lead_active_session(lead_id: int, db: Session = Depends(get_db)):
    """Get the active session information for a lead"""

    # Validate lead exists
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        router_service = MessageRouter(db)
        active_session = router_service._get_active_session(lead_id)

        if not active_session:
            return {"has_active_session": False, "lead_id": lead_id}

        context = router_service.get_session_context(active_session.id)

        return {
            "has_active_session": True,
            "lead_id": lead_id,
            "session": context
        }

    except Exception as e:
        logger.error(f"Error getting lead active session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get lead active session")

@router.get("/conversations/recent")
async def get_recent_conversations(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get recent conversation sessions"""

    try:
        # Get recent sessions with their associated agents and leads
        sessions = db.query(AgentSession)\
            .order_by(AgentSession.last_message_at.desc().nullslast(), AgentSession.created_at.desc())\
            .limit(limit)\
            .all()

        conversations = []
        for session in sessions:
            # Get agent and lead info
            agent = db.query(AgentSession.agent).filter(AgentSession.id == session.id).first()
            lead = db.query(Lead).filter(Lead.id == session.lead_id).first()

            conversation = {
                "session_id": session.id,
                "lead_id": session.lead_id,
                "lead_name": lead.name if lead else "Unknown",
                "agent_id": session.agent_id,
                "agent_name": session.agent.name if session.agent else "Unknown",
                "session_status": session.session_status,
                "session_goal": session.session_goal,
                "message_count": session.message_count,
                "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
                "last_message_from": session.last_message_from,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "trigger_type": session.trigger_type
            }
            conversations.append(conversation)

        return {
            "conversations": conversations,
            "total_returned": len(conversations)
        }

    except Exception as e:
        logger.error(f"Error getting recent conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recent conversations")

@router.post("/simulate/lead-message")
async def simulate_lead_message(
    lead_id: int,
    message: str,
    db: Session = Depends(get_db)
):
    """
    Simulate a message from a lead for testing purposes
    This endpoint can be used to test the message routing system
    """

    message_data = IncomingMessageSchema(
        lead_id=lead_id,
        message=message,
        message_type="text",
        metadata={"simulated": True, "timestamp": datetime.utcnow().isoformat()}
    )

    # Route the message
    result = await route_message(message_data, db)

    # If routing was successful and should respond, provide simulation response
    if result.success and result.should_respond:
        # This would normally trigger the actual agent response
        # For simulation, we'll just acknowledge
        response_info = {
            "simulation_note": "In real implementation, this would trigger the agent to generate a response",
            "next_steps": [
                "Agent would receive the message and context",
                "Agent would generate appropriate response based on session goal",
                "Response would be sent back to lead",
                "Session statistics would be updated"
            ],
            "routing_result": result.dict()
        }

        return response_info
    else:
        return {
            "simulation_note": "Message routed but no agent response needed",
            "routing_result": result.dict()
        }

@router.get("/stats")
async def get_message_stats(db: Session = Depends(get_db)):
    """Get messaging and routing statistics"""

    try:
        # Count active sessions
        active_sessions = db.query(AgentSession).filter(
            AgentSession.session_status == "active"
        ).count()

        # Count total messages (sum of message_count across all sessions)
        total_messages = db.query(
            db.func.sum(AgentSession.message_count)
        ).scalar() or 0

        # Count sessions by status
        session_stats = db.query(
            AgentSession.session_status,
            db.func.count(AgentSession.id).label('count')
        ).group_by(AgentSession.session_status).all()

        status_counts = {stat.session_status: stat.count for stat in session_stats}

        # Count sessions by trigger type
        trigger_stats = db.query(
            AgentSession.trigger_type,
            db.func.count(AgentSession.id).label('count')
        ).group_by(AgentSession.trigger_type).all()

        trigger_counts = {stat.trigger_type: stat.count for stat in trigger_stats}

        return {
            "active_sessions": active_sessions,
            "total_messages_processed": total_messages,
            "sessions_by_status": status_counts,
            "sessions_by_trigger_type": trigger_counts,
            "routing_stats": {
                "total_sessions_created": sum(status_counts.values()),
                "completion_rate": round(
                    (status_counts.get("completed", 0) / sum(status_counts.values()) * 100)
                    if sum(status_counts.values()) > 0 else 0, 2
                ),
                "escalation_rate": round(
                    (status_counts.get("escalated", 0) / sum(status_counts.values()) * 100)
                    if sum(status_counts.values()) > 0 else 0, 2
                )
            }
        }

    except Exception as e:
        logger.error(f"Error getting message stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get message statistics")