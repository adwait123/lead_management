"""
Follow-up Testing API endpoints for testing follow-up sequence functionality
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging
from datetime import datetime

from models.database import get_db
from models.follow_up_task import FollowUpTask
from models.agent_session import AgentSession
from services.follow_up_scheduler import FollowUpScheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/testing/follow-ups", tags=["follow-up-testing"])

@router.post("/execute-due-tasks")
async def execute_due_follow_up_tasks(db: Session = Depends(get_db)):
    """Execute all due follow-up tasks (for testing)"""
    try:
        scheduler = FollowUpScheduler(db)
        results = scheduler.execute_due_tasks()

        return {
            "success": True,
            "execution_results": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error executing due tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute tasks: {str(e)}")

@router.get("/session/{session_id}/tasks")
async def get_session_follow_up_tasks(session_id: int, db: Session = Depends(get_db)):
    """Get all follow-up tasks for a session"""
    try:
        tasks = db.query(FollowUpTask).filter(
            FollowUpTask.agent_session_id == session_id
        ).order_by(FollowUpTask.sequence_position).all()

        task_list = []
        for task in tasks:
            task_list.append({
                "id": task.id,
                "sequence_position": task.sequence_position,
                "status": task.status,
                "delay_minutes": task.delay_minutes,
                "original_delay": task.original_delay,
                "original_unit": task.original_unit,
                "scheduled_at": task.scheduled_at.isoformat() if task.scheduled_at else None,
                "executed_at": task.executed_at.isoformat() if task.executed_at else None,
                "message_template": task.message_template,
                "sequence_name": task.sequence_name,
                "total_sequence_steps": task.total_sequence_steps
            })

        return {
            "success": True,
            "session_id": session_id,
            "tasks": task_list,
            "total_tasks": len(task_list)
        }

    except Exception as e:
        logger.error(f"Error getting session tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")

@router.get("/stats")
async def get_follow_up_stats(days_back: int = 7, db: Session = Depends(get_db)):
    """Get follow-up task statistics"""
    try:
        scheduler = FollowUpScheduler(db)
        stats = scheduler.get_task_statistics(days_back=days_back)

        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.post("/session/{session_id}/cancel-tasks")
async def cancel_session_follow_ups(
    session_id: int,
    task_types: List[str] = None,
    reason: str = "Cancelled via testing API",
    db: Session = Depends(get_db)
):
    """Cancel follow-up tasks for a session"""
    try:
        scheduler = FollowUpScheduler(db)
        cancelled_count = scheduler.cancel_pending_tasks(
            agent_session_id=session_id,
            task_types=task_types,
            reason=reason
        )

        return {
            "success": True,
            "session_id": session_id,
            "cancelled_tasks": cancelled_count,
            "reason": reason
        }

    except Exception as e:
        logger.error(f"Error cancelling tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel tasks: {str(e)}")

@router.post("/session/{session_id}/simulate-lead-response")
async def simulate_lead_response(session_id: int, db: Session = Depends(get_db)):
    """Simulate a lead response to trigger follow-up cancellation"""
    try:
        scheduler = FollowUpScheduler(db)
        result = scheduler.handle_lead_response(session_id)

        return {
            "success": True,
            "response_handling": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error simulating lead response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to simulate response: {str(e)}")

@router.get("/all-tasks")
async def get_all_follow_up_tasks(status: str = None, limit: int = 50, db: Session = Depends(get_db)):
    """Get all follow-up tasks with optional filtering"""
    try:
        query = db.query(FollowUpTask)

        if status:
            query = query.filter(FollowUpTask.status == status)

        tasks = query.order_by(FollowUpTask.created_at.desc()).limit(limit).all()

        task_list = []
        for task in tasks:
            task_list.append({
                "id": task.id,
                "agent_session_id": task.agent_session_id,
                "lead_id": task.lead_id,
                "sequence_position": task.sequence_position,
                "status": task.status,
                "delay_minutes": task.delay_minutes,
                "scheduled_at": task.scheduled_at.isoformat() if task.scheduled_at else None,
                "executed_at": task.executed_at.isoformat() if task.executed_at else None,
                "message_template": task.message_template[:100] + "..." if task.message_template and len(task.message_template) > 100 else task.message_template,
                "created_at": task.created_at.isoformat() if task.created_at else None
            })

        return {
            "success": True,
            "tasks": task_list,
            "total_tasks": len(task_list),
            "filter_status": status
        }

    except Exception as e:
        logger.error(f"Error getting all tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")