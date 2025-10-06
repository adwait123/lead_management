"""
Agent Internal APIs for session management and autonomous agent operations
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

from models.database import get_db
from models.agent_session import AgentSession
from models.agent import Agent
from models.lead import Lead

# Pydantic schemas for agent internal APIs
class SessionUpdateSchema(BaseModel):
    session_goal: Optional[str] = None
    completion_reason: Optional[str] = None
    escalated_to: Optional[str] = None
    escalation_reason: Optional[str] = None
    satisfaction_score: Optional[str] = None
    session_metadata: Optional[Dict[str, Any]] = None

class SessionEndSchema(BaseModel):
    reason: str
    escalated_to: Optional[str] = None
    final_notes: Optional[str] = None

class InternalReminderSchema(BaseModel):
    reminder_type: str  # follow_up, check_in, escalation_check
    delay_hours: int
    reminder_data: Optional[Dict[str, Any]] = {}
    priority: Optional[str] = "medium"  # low, medium, high

class AgentDecisionSchema(BaseModel):
    decision_type: str  # continue, escalate, end_session, schedule_follow_up
    reasoning: str
    confidence_score: Optional[float] = None
    next_action: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class ConversationAnalysisSchema(BaseModel):
    session_id: int
    sentiment: Optional[str] = None  # positive, negative, neutral
    lead_satisfaction: Optional[str] = None  # satisfied, neutral, frustrated
    conversation_stage: Optional[str] = None  # introduction, qualification, negotiation, closing
    key_topics: Optional[List[str]] = []
    next_recommended_action: Optional[str] = None

# Router setup
router = APIRouter(prefix="/api/agent-internals", tags=["agent-internals"])

@router.get("/session/{session_id}")
async def get_session_for_agent(session_id: int, db: Session = Depends(get_db)):
    """Get session details from agent's perspective with full context"""

    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get related data
    agent = db.query(Agent).filter(Agent.id == session.agent_id).first()
    lead = db.query(Lead).filter(Lead.id == session.lead_id).first()

    # Build comprehensive session context
    context = {
        "session": {
            "id": session.id,
            "status": session.session_status,
            "goal": session.session_goal,
            "message_count": session.message_count,
            "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
            "last_message_from": session.last_message_from,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "trigger_type": session.trigger_type,
            "initial_context": session.initial_context,
            "session_metadata": session.session_metadata or {},
            "auto_timeout_hours": session.auto_timeout_hours,
            "max_message_count": session.max_message_count,
            "completion_reason": session.completion_reason,
            "escalated_to": session.escalated_to,
            "escalation_reason": session.escalation_reason
        },
        "agent": {
            "id": agent.id if agent else None,
            "name": agent.name if agent else "Unknown",
            "use_case": agent.use_case if agent else None,
            "prompt_template": agent.prompt_template if agent else None,
            "personality_style": agent.personality_style if agent else None,
            "response_length": agent.response_length if agent else None,
            "model": agent.model if agent else None,
            "temperature": agent.temperature if agent else None
        },
        "lead": {
            "id": lead.id if lead else None,
            "name": lead.name if lead else "Unknown",
            "email": lead.email if lead else None,
            "phone": lead.phone if lead else None,
            "company": lead.company if lead else None,
            "service_requested": lead.service_requested if lead else None,
            "status": lead.status if lead else None,
            "source": lead.source if lead else None,
            "notes": lead.notes if lead else [],
            "interaction_history": lead.interaction_history if lead else []
        },
        "conversation_analysis": {
            "time_since_last_message": _calculate_time_since_last_message(session),
            "is_approaching_timeout": session.is_timeout_eligible(),
            "is_approaching_escalation": session.should_escalate(),
            "conversation_velocity": _calculate_conversation_velocity(session),
            "session_duration_hours": _calculate_session_duration_hours(session)
        }
    }

    return context

@router.put("/session/{session_id}")
async def update_session_internal(
    session_id: int,
    update_data: SessionUpdateSchema,
    db: Session = Depends(get_db)
):
    """Update session from agent's internal perspective"""

    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.session_status not in ["active", "paused"]:
        raise HTTPException(status_code=400, detail="Cannot update inactive session")

    try:
        # Update provided fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if field == "session_metadata":
                # Merge metadata instead of replacing
                current_metadata = session.session_metadata or {}
                current_metadata.update(value or {})
                session.session_metadata = current_metadata
            else:
                setattr(session, field, value)

        db.commit()
        db.refresh(session)

        logger.info(f"Agent updated session {session_id} internally")
        return {"success": True, "message": "Session updated successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update session")

@router.post("/session/{session_id}/end")
async def end_session_internal(
    session_id: int,
    end_data: SessionEndSchema,
    db: Session = Depends(get_db)
):
    """End session from agent's internal perspective"""

    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.session_status not in ["active", "paused"]:
        raise HTTPException(status_code=400, detail="Session is already ended")

    try:
        # End the session
        session.end_session(reason=end_data.reason, escalated_to=end_data.escalated_to)

        # Add final notes to metadata if provided
        if end_data.final_notes:
            metadata = session.session_metadata or {}
            metadata["final_notes"] = end_data.final_notes
            metadata["ended_by"] = "agent"
            session.session_metadata = metadata

        db.commit()
        db.refresh(session)

        logger.info(f"Agent ended session {session_id} with reason: {end_data.reason}")
        return {
            "success": True,
            "message": "Session ended successfully",
            "final_status": session.session_status,
            "completion_reason": session.completion_reason
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error ending session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to end session")

@router.post("/session/{session_id}/decision")
async def record_agent_decision(
    session_id: int,
    decision_data: AgentDecisionSchema,
    db: Session = Depends(get_db)
):
    """Record an agent's decision-making process for analytics and learning"""

    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Store decision in session metadata
        metadata = session.session_metadata or {}
        decisions = metadata.get("agent_decisions", [])

        decision_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "decision_type": decision_data.decision_type,
            "reasoning": decision_data.reasoning,
            "confidence_score": decision_data.confidence_score,
            "next_action": decision_data.next_action,
            "metadata": decision_data.metadata or {},
            "message_count_at_decision": session.message_count
        }

        decisions.append(decision_record)
        metadata["agent_decisions"] = decisions
        session.session_metadata = metadata

        db.commit()

        logger.info(f"Recorded agent decision for session {session_id}: {decision_data.decision_type}")
        return {"success": True, "message": "Decision recorded successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error recording agent decision: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record decision")

@router.post("/session/{session_id}/analysis")
async def update_conversation_analysis(
    session_id: int,
    analysis_data: ConversationAnalysisSchema,
    db: Session = Depends(get_db)
):
    """Update conversation analysis from agent's perspective"""

    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Store analysis in session metadata
        metadata = session.session_metadata or {}
        analysis = metadata.get("conversation_analysis", {})

        # Update analysis fields
        analysis.update({
            "last_updated": datetime.utcnow().isoformat(),
            "sentiment": analysis_data.sentiment,
            "lead_satisfaction": analysis_data.lead_satisfaction,
            "conversation_stage": analysis_data.conversation_stage,
            "key_topics": analysis_data.key_topics or [],
            "next_recommended_action": analysis_data.next_recommended_action
        })

        metadata["conversation_analysis"] = analysis
        session.session_metadata = metadata

        db.commit()

        return {"success": True, "message": "Conversation analysis updated"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating conversation analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update analysis")

@router.post("/session/{session_id}/reminder")
async def schedule_internal_reminder(
    session_id: int,
    reminder_data: InternalReminderSchema,
    db: Session = Depends(get_db)
):
    """Schedule an internal reminder for the agent (for follow-ups, check-ins, etc.)"""

    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Calculate reminder time
        reminder_time = datetime.utcnow() + timedelta(hours=reminder_data.delay_hours)

        # Store reminder in session metadata
        metadata = session.session_metadata or {}
        reminders = metadata.get("internal_reminders", [])

        reminder_record = {
            "id": f"reminder_{len(reminders) + 1}",
            "type": reminder_data.reminder_type,
            "scheduled_for": reminder_time.isoformat(),
            "priority": reminder_data.priority,
            "reminder_data": reminder_data.reminder_data,
            "created_at": datetime.utcnow().isoformat(),
            "status": "scheduled"
        }

        reminders.append(reminder_record)
        metadata["internal_reminders"] = reminders
        session.session_metadata = metadata

        db.commit()

        logger.info(f"Scheduled internal reminder for session {session_id}: {reminder_data.reminder_type}")
        return {
            "success": True,
            "message": "Reminder scheduled successfully",
            "reminder_id": reminder_record["id"],
            "scheduled_for": reminder_time.isoformat()
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error scheduling reminder: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to schedule reminder")

@router.get("/session/{session_id}/reminders")
async def get_pending_reminders(session_id: int, db: Session = Depends(get_db)):
    """Get pending reminders for a session"""

    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    metadata = session.session_metadata or {}
    reminders = metadata.get("internal_reminders", [])

    # Filter for pending reminders
    now = datetime.utcnow()
    pending_reminders = []

    for reminder in reminders:
        if reminder.get("status") == "scheduled":
            reminder_time = datetime.fromisoformat(reminder["scheduled_for"])
            if reminder_time <= now:
                reminder["is_due"] = True
                pending_reminders.append(reminder)
            else:
                reminder["is_due"] = False
                reminder["time_until_due"] = str(reminder_time - now)

    return {
        "session_id": session_id,
        "pending_reminders": pending_reminders,
        "total_reminders": len(reminders)
    }

@router.post("/session/{session_id}/reminders/{reminder_id}/complete")
async def complete_reminder(
    session_id: int,
    reminder_id: str,
    action_taken: str,
    db: Session = Depends(get_db)
):
    """Mark a reminder as completed with the action taken"""

    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        metadata = session.session_metadata or {}
        reminders = metadata.get("internal_reminders", [])

        # Find and update the reminder
        for reminder in reminders:
            if reminder.get("id") == reminder_id:
                reminder["status"] = "completed"
                reminder["completed_at"] = datetime.utcnow().isoformat()
                reminder["action_taken"] = action_taken
                break
        else:
            raise HTTPException(status_code=404, detail="Reminder not found")

        metadata["internal_reminders"] = reminders
        session.session_metadata = metadata

        db.commit()

        return {"success": True, "message": "Reminder completed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing reminder: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete reminder")

@router.get("/agent/{agent_id}/active-sessions")
async def get_agent_active_sessions(agent_id: int, db: Session = Depends(get_db)):
    """Get all active sessions for a specific agent"""

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    sessions = db.query(AgentSession).filter(
        AgentSession.agent_id == agent_id,
        AgentSession.session_status == "active"
    ).all()

    session_summaries = []
    for session in sessions:
        lead = db.query(Lead).filter(Lead.id == session.lead_id).first()

        # Check for pending reminders
        metadata = session.session_metadata or {}
        reminders = metadata.get("internal_reminders", [])
        pending_reminders = [r for r in reminders if r.get("status") == "scheduled"]

        session_summary = {
            "session_id": session.id,
            "lead_name": lead.name if lead else "Unknown",
            "lead_id": session.lead_id,
            "session_goal": session.session_goal,
            "message_count": session.message_count,
            "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
            "last_message_from": session.last_message_from,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "time_since_last_message": _calculate_time_since_last_message(session),
            "is_approaching_timeout": session.is_timeout_eligible(),
            "pending_reminders_count": len(pending_reminders),
            "conversation_stage": metadata.get("conversation_analysis", {}).get("conversation_stage")
        }
        session_summaries.append(session_summary)

    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "active_sessions": session_summaries,
        "total_active_sessions": len(session_summaries)
    }

# Helper functions
def _calculate_time_since_last_message(session: AgentSession) -> Optional[str]:
    """Calculate time since last message in human-readable format"""
    if not session.last_message_at:
        return None

    delta = datetime.utcnow() - session.last_message_at
    hours = delta.total_seconds() / 3600

    if hours < 1:
        return f"{int(delta.total_seconds() / 60)} minutes ago"
    elif hours < 24:
        return f"{int(hours)} hours ago"
    else:
        return f"{int(hours / 24)} days ago"

def _calculate_conversation_velocity(session: AgentSession) -> Optional[float]:
    """Calculate messages per hour for the session"""
    if not session.created_at or session.message_count == 0:
        return None

    delta = datetime.utcnow() - session.created_at
    hours = delta.total_seconds() / 3600

    if hours > 0:
        return round(session.message_count / hours, 2)
    return None

def _calculate_session_duration_hours(session: AgentSession) -> float:
    """Calculate total session duration in hours"""
    if not session.created_at:
        return 0

    end_time = session.ended_at or datetime.utcnow()
    delta = end_time - session.created_at
    return round(delta.total_seconds() / 3600, 2)