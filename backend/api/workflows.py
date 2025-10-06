"""
Workflows API endpoints for trigger management and execution
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

from models.database import get_db
from models.agent import Agent
from models.lead import Lead
from models.agent_session import AgentSession
from services.workflow_service import WorkflowService

# Pydantic schemas for workflow APIs
class TriggerEventSchema(BaseModel):
    event_type: str
    lead_id: int
    event_data: Optional[Dict[str, Any]] = {}

class TriggerExecutionResponseSchema(BaseModel):
    success: bool
    event_type: str
    lead_id: int
    sessions_created: List[int]
    message: str

class WorkflowTestSchema(BaseModel):
    agent_id: int
    event_type: str
    test_data: Optional[Dict[str, Any]] = {}

class WorkflowTestResponseSchema(BaseModel):
    would_trigger: bool
    agent_id: int
    agent_name: str
    event_type: str
    reason: str

class AgentTriggerSummarySchema(BaseModel):
    agent_id: int
    agent_name: str
    is_active: bool
    triggers: List[Dict[str, Any]]
    trigger_count: int

class LeadCreatedEventSchema(BaseModel):
    lead_id: int
    source: Optional[str] = None
    form_data: Optional[Dict[str, Any]] = {}

class FormSubmissionEventSchema(BaseModel):
    lead_id: int
    form_type: str
    form_data: Dict[str, Any]

class EmailOpenedEventSchema(BaseModel):
    lead_id: int
    email_id: Optional[str] = None

class WebsiteVisitEventSchema(BaseModel):
    lead_id: int
    page_url: Optional[str] = None
    duration: Optional[int] = None

class MeetingScheduledEventSchema(BaseModel):
    lead_id: int
    meeting_time: str
    meeting_type: Optional[str] = None

class SupportTicketEventSchema(BaseModel):
    lead_id: int
    ticket_id: str
    issue_type: Optional[str] = None

# Router setup
router = APIRouter(prefix="/api/workflows", tags=["workflows"])

@router.post("/trigger", response_model=TriggerExecutionResponseSchema)
async def execute_trigger(trigger_data: TriggerEventSchema, db: Session = Depends(get_db)):
    """Execute a workflow trigger manually"""

    # Validate lead exists
    lead = db.query(Lead).filter(Lead.id == trigger_data.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        workflow_service = WorkflowService(db)
        session_ids = workflow_service.detect_and_execute_triggers(
            trigger_data.event_type,
            {**trigger_data.event_data, "lead_id": trigger_data.lead_id}
        )

        return TriggerExecutionResponseSchema(
            success=True,
            event_type=trigger_data.event_type,
            lead_id=trigger_data.lead_id,
            sessions_created=session_ids,
            message=f"Created {len(session_ids)} agent sessions"
        )

    except Exception as e:
        logger.error(f"Error executing trigger: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to execute trigger")

@router.post("/events/lead-created", response_model=TriggerExecutionResponseSchema)
async def handle_lead_created(event_data: LeadCreatedEventSchema, db: Session = Depends(get_db)):
    """Handle new lead creation event"""

    try:
        workflow_service = WorkflowService(db)
        session_ids = workflow_service.handle_lead_created(
            event_data.lead_id,
            event_data.source,
            event_data.form_data
        )

        return TriggerExecutionResponseSchema(
            success=True,
            event_type="new_lead",
            lead_id=event_data.lead_id,
            sessions_created=session_ids,
            message=f"Processed new lead event, created {len(session_ids)} sessions"
        )

    except Exception as e:
        logger.error(f"Error handling lead created event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process lead created event")

@router.post("/events/form-submission", response_model=TriggerExecutionResponseSchema)
async def handle_form_submission(event_data: FormSubmissionEventSchema, db: Session = Depends(get_db)):
    """Handle form submission event"""

    try:
        workflow_service = WorkflowService(db)
        session_ids = workflow_service.handle_form_submission(
            event_data.lead_id,
            event_data.form_type,
            event_data.form_data
        )

        return TriggerExecutionResponseSchema(
            success=True,
            event_type="form_submission",
            lead_id=event_data.lead_id,
            sessions_created=session_ids,
            message=f"Processed form submission event, created {len(session_ids)} sessions"
        )

    except Exception as e:
        logger.error(f"Error handling form submission event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process form submission event")

@router.post("/events/email-opened", response_model=TriggerExecutionResponseSchema)
async def handle_email_opened(event_data: EmailOpenedEventSchema, db: Session = Depends(get_db)):
    """Handle email opened event"""

    try:
        workflow_service = WorkflowService(db)
        session_ids = workflow_service.handle_email_opened(
            event_data.lead_id,
            event_data.email_id
        )

        return TriggerExecutionResponseSchema(
            success=True,
            event_type="email_opened",
            lead_id=event_data.lead_id,
            sessions_created=session_ids,
            message=f"Processed email opened event, created {len(session_ids)} sessions"
        )

    except Exception as e:
        logger.error(f"Error handling email opened event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process email opened event")

@router.post("/events/website-visit", response_model=TriggerExecutionResponseSchema)
async def handle_website_visit(event_data: WebsiteVisitEventSchema, db: Session = Depends(get_db)):
    """Handle website visit event"""

    try:
        workflow_service = WorkflowService(db)
        session_ids = workflow_service.handle_website_visit(
            event_data.lead_id,
            event_data.page_url,
            event_data.duration
        )

        return TriggerExecutionResponseSchema(
            success=True,
            event_type="website_visit",
            lead_id=event_data.lead_id,
            sessions_created=session_ids,
            message=f"Processed website visit event, created {len(session_ids)} sessions"
        )

    except Exception as e:
        logger.error(f"Error handling website visit event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process website visit event")

@router.post("/events/meeting-scheduled", response_model=TriggerExecutionResponseSchema)
async def handle_meeting_scheduled(event_data: MeetingScheduledEventSchema, db: Session = Depends(get_db)):
    """Handle meeting scheduled event"""

    try:
        workflow_service = WorkflowService(db)
        session_ids = workflow_service.handle_meeting_scheduled(
            event_data.lead_id,
            event_data.meeting_time,
            event_data.meeting_type
        )

        return TriggerExecutionResponseSchema(
            success=True,
            event_type="meeting_scheduled",
            lead_id=event_data.lead_id,
            sessions_created=session_ids,
            message=f"Processed meeting scheduled event, created {len(session_ids)} sessions"
        )

    except Exception as e:
        logger.error(f"Error handling meeting scheduled event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process meeting scheduled event")

@router.post("/events/support-ticket", response_model=TriggerExecutionResponseSchema)
async def handle_support_ticket(event_data: SupportTicketEventSchema, db: Session = Depends(get_db)):
    """Handle support ticket creation event"""

    try:
        workflow_service = WorkflowService(db)
        session_ids = workflow_service.handle_support_ticket(
            event_data.lead_id,
            event_data.ticket_id,
            event_data.issue_type
        )

        return TriggerExecutionResponseSchema(
            success=True,
            event_type="support_ticket",
            lead_id=event_data.lead_id,
            sessions_created=session_ids,
            message=f"Processed support ticket event, created {len(session_ids)} sessions"
        )

    except Exception as e:
        logger.error(f"Error handling support ticket event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process support ticket event")

@router.post("/test", response_model=WorkflowTestResponseSchema)
async def test_workflow_trigger(test_data: WorkflowTestSchema, db: Session = Depends(get_db)):
    """Test if a workflow trigger would be executed for an agent and event type"""

    # Validate agent exists
    agent = db.query(Agent).filter(Agent.id == test_data.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        workflow_service = WorkflowService(db)

        # Check if agent has matching trigger
        would_trigger = workflow_service._agent_has_matching_trigger(agent, test_data.event_type)

        reason = ""
        if would_trigger:
            reason = f"Agent has trigger configured for {test_data.event_type}"
        else:
            if not agent.is_active:
                reason = "Agent is not active"
            elif not agent.triggers:
                reason = "Agent has no triggers configured"
            else:
                reason = f"Agent has no trigger for {test_data.event_type}"

        return WorkflowTestResponseSchema(
            would_trigger=would_trigger,
            agent_id=test_data.agent_id,
            agent_name=agent.name,
            event_type=test_data.event_type,
            reason=reason
        )

    except Exception as e:
        logger.error(f"Error testing workflow trigger: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to test workflow trigger")

@router.get("/agents/{agent_id}/triggers", response_model=AgentTriggerSummarySchema)
async def get_agent_triggers(agent_id: int, db: Session = Depends(get_db)):
    """Get trigger configuration summary for an agent"""

    try:
        workflow_service = WorkflowService(db)
        summary = workflow_service.get_agent_trigger_summary(agent_id)

        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])

        return AgentTriggerSummarySchema(**summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent triggers: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get agent triggers")

@router.get("/agents/triggers/summary")
async def get_all_agent_triggers_summary(db: Session = Depends(get_db)):
    """Get trigger configuration summary for all agents"""

    try:
        workflow_service = WorkflowService(db)

        # Get all agents
        agents = db.query(Agent).all()

        summaries = []
        for agent in agents:
            try:
                summary = workflow_service.get_agent_trigger_summary(agent.id)
                if "error" not in summary:
                    summaries.append(summary)
            except Exception as e:
                logger.warning(f"Failed to get triggers for agent {agent.id}: {str(e)}")
                continue

        return {
            "total_agents": len(agents),
            "agents_with_triggers": len(summaries),
            "agent_summaries": summaries
        }

    except Exception as e:
        logger.error(f"Error getting all agent triggers: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get agent triggers summary")

@router.get("/sessions/recent")
async def get_recent_workflow_sessions(
    limit: int = Query(10, ge=1, le=100, description="Number of recent sessions to return"),
    db: Session = Depends(get_db)
):
    """Get recent workflow-created sessions"""

    try:
        # Get recent agent sessions ordered by creation time
        sessions = db.query(AgentSession)\
            .order_by(AgentSession.created_at.desc())\
            .limit(limit)\
            .all()

        session_data = []
        for session in sessions:
            # Get agent and lead names
            agent = db.query(Agent).filter(Agent.id == session.agent_id).first()
            lead = db.query(Lead).filter(Lead.id == session.lead_id).first()

            session_info = {
                "session_id": session.id,
                "agent_id": session.agent_id,
                "agent_name": agent.name if agent else "Unknown",
                "lead_id": session.lead_id,
                "lead_name": lead.name if lead else "Unknown",
                "trigger_type": session.trigger_type,
                "session_status": session.session_status,
                "session_goal": session.session_goal,
                "message_count": session.message_count,
                "created_at": session.created_at.isoformat() if session.created_at else None
            }
            session_data.append(session_info)

        return {
            "recent_sessions": session_data,
            "total_returned": len(session_data)
        }

    except Exception as e:
        logger.error(f"Error getting recent workflow sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recent workflow sessions")

@router.get("/stats")
async def get_workflow_stats(db: Session = Depends(get_db)):
    """Get workflow execution statistics"""

    try:
        # Count agents with triggers
        agents_with_triggers = db.query(Agent).filter(
            Agent.triggers.isnot(None),
            Agent.is_active == True
        ).count()

        total_active_agents = db.query(Agent).filter(Agent.is_active == True).count()

        # Count sessions by trigger type
        session_stats = db.query(
            AgentSession.trigger_type,
            db.func.count(AgentSession.id).label('count')
        ).group_by(AgentSession.trigger_type).all()

        trigger_type_counts = {stat.trigger_type: stat.count for stat in session_stats}

        # Count active sessions
        active_sessions = db.query(AgentSession).filter(
            AgentSession.session_status == "active"
        ).count()

        total_sessions = db.query(AgentSession).count()

        return {
            "agents": {
                "total_active": total_active_agents,
                "with_triggers": agents_with_triggers,
                "percentage_with_triggers": round((agents_with_triggers / total_active_agents * 100) if total_active_agents > 0 else 0, 2)
            },
            "sessions": {
                "total": total_sessions,
                "active": active_sessions,
                "by_trigger_type": trigger_type_counts
            }
        }

    except Exception as e:
        logger.error(f"Error getting workflow stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get workflow statistics")