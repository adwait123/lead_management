"""
Messages API endpoints for handling conversation routing and message processing
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from pydantic import BaseModel, validator

# Configure logging
logger = logging.getLogger(__name__)

from models.database import get_db
from models.lead import Lead
from models.agent_session import AgentSession
from services.message_router import MessageRouter

# Pydantic schemas for message APIs
class IncomingMessageSchema(BaseModel):
    lead_id: Optional[int] = None
    lead_external_id: Optional[str] = None
    message: str
    message_type: Optional[str] = "text"
    metadata: Optional[Dict[str, Any]] = {}

    @validator('lead_external_id', always=True)
    def validate_lead_identification(cls, v, values):
        """Ensure exactly one of lead_id or lead_external_id is provided"""
        lead_id = values.get('lead_id')
        if not lead_id and not v:
            raise ValueError('Either lead_id or lead_external_id must be provided')
        if lead_id and v:
            raise ValueError('Cannot provide both lead_id and lead_external_id')
        return v

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
    # New fields for automatic agent response
    agent_response_generated: Optional[bool] = None
    agent_response_id: Optional[int] = None
    agent_response_error: Optional[str] = None
    agent_response_skip_reason: Optional[str] = None

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
    """Route an incoming message to the appropriate agent session and generate agent response"""

    # Lookup lead by either internal ID or external ID
    if message_data.lead_external_id:
        lead = db.query(Lead).filter(Lead.external_id == message_data.lead_external_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead not found with external_id: {message_data.lead_external_id}")
    else:
        lead = db.query(Lead).filter(Lead.id == message_data.lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

    try:
        router_service = MessageRouter(db)
        result = router_service.route_message(
            lead_id=lead.id,  # Use the lead ID from the found lead object
            message=message_data.message,
            message_type=message_data.message_type,
            metadata=message_data.metadata
        )

        # If routing was successful and agent should respond, generate agent response automatically
        if result.get("success") and result.get("should_respond") and result.get("session_id"):
            try:
                from services.agent_service import AgentService

                # Get session to check if it's taken over
                session = db.query(AgentSession).filter(AgentSession.id == result["session_id"]).first()

                if session and session.session_status != "taken_over":
                    logger.info(f"Generating automatic agent response for session {result['session_id']}")

                    agent_service = AgentService(db)
                    response_message = await agent_service.generate_response_message(
                        agent_session_id=result["session_id"],
                        incoming_message=message_data.message
                    )

                    if response_message:
                        logger.info(f"Generated automatic response message {response_message.id} for session {result['session_id']}")
                        # Add response info to result
                        result["agent_response_generated"] = True
                        result["agent_response_id"] = response_message.id
                    else:
                        logger.error(f"Failed to generate automatic agent response for session {result['session_id']}")
                        result["agent_response_generated"] = False
                        result["agent_response_error"] = "Failed to generate response"
                else:
                    logger.info(f"Skipping agent response - session {result['session_id']} is taken over or not found")
                    result["agent_response_generated"] = False
                    result["agent_response_skip_reason"] = "Session taken over or not found"

            except Exception as e:
                logger.error(f"Error generating automatic agent response: {str(e)}")
                result["agent_response_generated"] = False
                result["agent_response_error"] = str(e)

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
    """Get the active session information for a lead by internal ID"""

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

@router.get("/external/{external_id}/active-session")
async def get_lead_active_session_by_external_id(external_id: str, db: Session = Depends(get_db)):
    """Get the active session information for a lead by external ID"""

    # Validate lead exists
    lead = db.query(Lead).filter(Lead.external_id == external_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead not found with external_id: {external_id}")

    try:
        router_service = MessageRouter(db)
        active_session = router_service._get_active_session(lead.id)

        if not active_session:
            return {"has_active_session": False, "external_id": external_id, "lead_id": lead.id}

        context = router_service.get_session_context(active_session.id)

        return {
            "has_active_session": True,
            "external_id": external_id,
            "lead_id": lead.id,
            "session": context
        }

    except Exception as e:
        logger.error(f"Error getting lead active session by external_id: {str(e)}")
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

# Session Control Schemas
class SessionTakeoverSchema(BaseModel):
    business_owner_id: Optional[str] = "default"  # Could be user ID in future
    reason: Optional[str] = "Manual takeover"

class SessionControlResponseSchema(BaseModel):
    success: bool
    session_id: int
    previous_status: str
    new_status: str
    message: str
    timestamp: str

@router.post("/session/{session_id}/takeover", response_model=SessionControlResponseSchema)
async def takeover_session(
    session_id: int,
    takeover_data: SessionTakeoverSchema,
    db: Session = Depends(get_db)
):
    """Take over a session from the agent (business owner control)"""

    try:
        # Get the session
        session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Store previous status
        previous_status = session.session_status

        # Update session status to indicate takeover
        session.session_status = "taken_over"
        session.business_owner_active = True
        session.business_owner_takeover_at = datetime.utcnow()
        session.takeover_reason = takeover_data.reason

        # Add takeover note to session
        if hasattr(session, 'notes') and session.notes:
            session.notes.append({
                "timestamp": datetime.utcnow().isoformat(),
                "type": "takeover",
                "message": f"Business owner took over session. Reason: {takeover_data.reason}",
                "business_owner_id": takeover_data.business_owner_id
            })
        else:
            session.notes = [{
                "timestamp": datetime.utcnow().isoformat(),
                "type": "takeover",
                "message": f"Business owner took over session. Reason: {takeover_data.reason}",
                "business_owner_id": takeover_data.business_owner_id
            }]

        db.commit()
        db.refresh(session)

        logger.info(f"Session {session_id} taken over by business owner. Previous status: {previous_status}")

        return SessionControlResponseSchema(
            success=True,
            session_id=session_id,
            previous_status=previous_status,
            new_status="taken_over",
            message="Session successfully taken over by business owner",
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error taking over session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to take over session")

@router.post("/session/{session_id}/release", response_model=SessionControlResponseSchema)
async def release_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Release session back to agent control"""

    try:
        # Get the session
        session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Store previous status
        previous_status = session.session_status

        # Only allow release if currently taken over
        if previous_status != "taken_over":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot release session with status '{previous_status}'. Only 'taken_over' sessions can be released."
            )

        # Update session status back to active
        session.session_status = "active"
        session.business_owner_active = False
        session.business_owner_release_at = datetime.utcnow()

        # Add release note to session
        if hasattr(session, 'notes') and session.notes:
            session.notes.append({
                "timestamp": datetime.utcnow().isoformat(),
                "type": "release",
                "message": "Business owner released control back to agent",
            })
        else:
            session.notes = [{
                "timestamp": datetime.utcnow().isoformat(),
                "type": "release",
                "message": "Business owner released control back to agent",
            }]

        db.commit()
        db.refresh(session)

        logger.info(f"Session {session_id} released back to agent control")

        return SessionControlResponseSchema(
            success=True,
            session_id=session_id,
            previous_status=previous_status,
            new_status="active",
            message="Session successfully released back to agent",
            timestamp=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error releasing session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to release session")

@router.get("/session/{session_id}/status")
async def get_session_status(session_id: int, db: Session = Depends(get_db)):
    """Get current session status and control information"""

    try:
        session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session_id,
            "session_status": session.session_status,
            "business_owner_active": getattr(session, 'business_owner_active', False),
            "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
            "last_message_from": session.last_message_from,
            "message_count": session.message_count,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "takeover_reason": getattr(session, 'takeover_reason', None),
            "business_owner_takeover_at": getattr(session, 'business_owner_takeover_at', None),
            "business_owner_release_at": getattr(session, 'business_owner_release_at', None)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session status")

@router.get("/conversation/{lead_external_id}")
async def get_conversation_messages(
    lead_external_id: str,
    limit: int = 50,
    since_timestamp: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get complete conversation history (both agent and lead messages) for a lead

    Args:
        lead_external_id: External ID of the lead (e.g., Yelp lead ID)
        limit: Maximum number of messages to return (default: 50)
        since_timestamp: ISO timestamp to get messages after this time
    """
    try:
        # Find lead by external_id
        lead = db.query(Lead).filter(Lead.external_id == lead_external_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead not found: {lead_external_id}")

        from models.message import Message
        from datetime import datetime

        # Build query for all messages (agent and lead)
        query = db.query(Message).filter(
            Message.lead_id == lead.id
        )

        # Filter by timestamp if provided
        if since_timestamp:
            try:
                since_dt = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
                query = query.filter(Message.created_at > since_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid timestamp format")

        # Get messages ordered by creation time
        messages = query.order_by(Message.created_at.asc()).limit(limit).all()

        # Format response
        formatted_messages = []
        for message in messages:
            formatted_messages.append({
                "id": message.id,
                "content": message.content,
                "sender_type": message.sender_type,
                "sender_name": message.sender_name,
                "created_at": message.created_at.isoformat() if message.created_at else None,
                "message_type": message.message_type,
                "external_conversation_id": message.external_conversation_id,
                "delivery_status": message.delivery_status,
                "message_status": message.message_status,
                "error_message": message.error_message,
                "message_metadata": message.message_metadata or {},
                "model_used": message.model_used,
                "response_time_ms": message.response_time_ms,
                "quality_score": message.quality_score,
                "external_platform": message.external_platform
            })

        return {
            "success": True,
            "lead_external_id": lead_external_id,
            "lead_id": lead.id,
            "messages": formatted_messages,
            "total_messages": len(formatted_messages),
            "retrieved_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation for lead {lead_external_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")