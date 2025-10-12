"""
FollowUpScheduler service for managing time-based follow-up tasks and sequences
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.follow_up_task import FollowUpTask
from models.agent_session import AgentSession
from models.agent import Agent
from models.lead import Lead
from models.message import Message

logger = logging.getLogger(__name__)


class FollowUpScheduler:
    """Service for managing and executing follow-up task sequences"""

    def __init__(self, db: Session):
        self.db = db

    def schedule_follow_up_sequence(self, agent_session_id: int, trigger_event: str,
                                  reference_time: datetime = None) -> List[int]:
        """
        Schedule a complete follow-up sequence for an agent session

        Args:
            agent_session_id: ID of the agent session
            trigger_event: Event that triggered the sequence (no_response, appointment_scheduled, etc.)
            reference_time: Reference time for calculating delays (defaults to current time)

        Returns:
            List of created task IDs
        """
        logger.info(f"Scheduling follow-up sequence for session {agent_session_id}, trigger: {trigger_event}")

        if reference_time is None:
            reference_time = datetime.utcnow()

        # Get agent session and related data
        session = self.db.query(AgentSession).filter(AgentSession.id == agent_session_id).first()
        if not session:
            logger.error(f"Agent session {agent_session_id} not found")
            return []

        agent = self.db.query(Agent).filter(Agent.id == session.agent_id).first()
        if not agent or not agent.workflow_steps:
            logger.warning(f"No workflow steps found for agent {session.agent_id}")
            return []

        # Filter workflow steps for this trigger event
        matching_steps = [
            step for step in agent.workflow_steps
            if (step.get('trigger', {}).get('event') == trigger_event and
                step.get('type') == 'time_based_trigger')
        ]

        if not matching_steps:
            logger.info(f"No matching workflow steps for trigger {trigger_event}")
            return []

        created_task_ids = []

        try:
            # Create follow-up tasks for each matching step
            for step in matching_steps:
                task = self._create_follow_up_task(session, agent, step, reference_time)
                if task:
                    self.db.add(task)
                    self.db.flush()  # Get the ID
                    created_task_ids.append(task.id)
                    logger.info(f"Created follow-up task {task.id} for step {step.get('id')}")

            self.db.commit()
            logger.info(f"Successfully scheduled {len(created_task_ids)} follow-up tasks")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error scheduling follow-up sequence: {str(e)}")
            return []

        return created_task_ids

    def _create_follow_up_task(self, session: AgentSession, agent: Agent,
                             workflow_step: Dict[str, Any], reference_time: datetime) -> Optional[FollowUpTask]:
        """Create a single follow-up task from a workflow step"""

        trigger = workflow_step.get('trigger', {})
        action = workflow_step.get('action', {})

        # Calculate when this task should be executed
        delay_minutes = trigger.get('delay_minutes', 0)
        if delay_minutes < 0:
            # For negative delays (like appointment reminders), subtract from reference
            scheduled_at = reference_time - timedelta(minutes=abs(delay_minutes))
        else:
            scheduled_at = reference_time + timedelta(minutes=delay_minutes)

        # Determine sequence information
        sequence_name = None
        sequence_position = workflow_step.get('sequence_position')
        total_sequence_steps = None

        if sequence_position:
            # Count total steps in this sequence
            sequence_steps = [
                step for step in agent.workflow_steps
                if (step.get('trigger', {}).get('event') == trigger.get('event') and
                    step.get('sequence_position') is not None)
            ]
            total_sequence_steps = len(sequence_steps)
            sequence_name = f"{trigger.get('event')}_sequence"

        task = FollowUpTask(
            agent_session_id=session.id,
            lead_id=session.lead_id,
            agent_id=agent.id,
            workflow_step_id=workflow_step.get('id'),
            task_type=action.get('template_type', 'unknown'),
            sequence_name=sequence_name,
            sequence_position=sequence_position,
            total_sequence_steps=total_sequence_steps,
            trigger_event=trigger.get('event'),
            delay_minutes=delay_minutes,
            original_delay=trigger.get('original_delay', 0),
            original_unit=trigger.get('original_unit', 'minutes'),
            scheduled_at=scheduled_at,
            message_template=action.get('template'),
            template_type=action.get('template_type'),
            trigger_context={
                'reference_time': reference_time.isoformat(),
                'session_id': session.id,
                'trigger_type': session.trigger_type
            }
        )

        return task

    def execute_due_tasks(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Execute all follow-up tasks that are due for execution

        Args:
            batch_size: Maximum number of tasks to process in one batch

        Returns:
            Execution summary with counts and results
        """
        logger.info("Starting execution of due follow-up tasks")

        current_time = datetime.utcnow()

        # Find tasks that are due for execution
        due_tasks = self.db.query(FollowUpTask).filter(
            and_(
                FollowUpTask.status == "pending",
                FollowUpTask.scheduled_at <= current_time
            )
        ).order_by(FollowUpTask.scheduled_at).limit(batch_size).all()

        if not due_tasks:
            logger.debug("No due follow-up tasks found")
            return {"executed": 0, "failed": 0, "skipped": 0, "tasks": []}

        logger.info(f"Found {len(due_tasks)} due tasks to execute")

        results = {
            "executed": 0,
            "failed": 0,
            "skipped": 0,
            "tasks": []
        }

        for task in due_tasks:
            try:
                task_result = self._execute_single_task(task)
                results["tasks"].append(task_result)

                if task_result["status"] == "executed":
                    results["executed"] += 1
                elif task_result["status"] == "failed":
                    results["failed"] += 1
                else:
                    results["skipped"] += 1

            except Exception as e:
                logger.error(f"Error executing task {task.id}: {str(e)}")
                task.mark_failed(f"Execution error: {str(e)}")
                results["failed"] += 1
                results["tasks"].append({
                    "task_id": task.id,
                    "status": "failed",
                    "error": str(e)
                })

        try:
            self.db.commit()
            logger.info(f"Task execution complete: {results}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error committing task execution results: {str(e)}")

        return results

    def _execute_single_task(self, task: FollowUpTask) -> Dict[str, Any]:
        """Execute a single follow-up task"""

        logger.info(f"Executing follow-up task {task.id} (type: {task.task_type})")

        # Check if session is still active
        session = self.db.query(AgentSession).filter(AgentSession.id == task.agent_session_id).first()
        if not session or session.session_status != "active":
            logger.warning(f"Session {task.agent_session_id} is not active, skipping task {task.id}")
            task.mark_cancelled("Session not active")
            return {"task_id": task.id, "status": "skipped", "reason": "Session not active"}

        # Check for lead response since task was scheduled
        if task.task_type.startswith('no_response') and self._has_lead_responded_since(task):
            logger.info(f"Lead has responded since task {task.id} was scheduled, skipping")
            task.mark_cancelled("Lead has responded")
            return {"task_id": task.id, "status": "skipped", "reason": "Lead responded"}

        # Generate and send the follow-up message
        try:
            # For now, create a simple message without OpenAI generation to test the flow
            # In production, this would use the async message generation
            from models.message import Message

            # Create a simple follow-up message for testing
            message = Message.create_agent_message(
                agent_session_id=task.agent_session_id,
                lead_id=task.lead_id,
                agent_id=task.agent_id,
                content=task.message_template or f"Follow-up message #{task.sequence_position}",
                metadata={
                    "is_follow_up": True,
                    "template_type": task.template_type,
                    "sequence_position": task.sequence_position
                }
            )

            # Save message to database
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)

            task.mark_executed(message.id)
            logger.info(f"Successfully executed task {task.id}, message {message.id}")
            return {
                "task_id": task.id,
                "status": "executed",
                "message_id": message.id,
                "sequence_progress": task.get_sequence_progress()
            }

        except Exception as e:
            logger.error(f"Error generating message for task {task.id}: {str(e)}")
            task.mark_failed(f"Message generation error: {str(e)}")
            return {"task_id": task.id, "status": "failed", "error": str(e)}

    def _has_lead_responded_since(self, task: FollowUpTask) -> bool:
        """Check if the lead has responded since the task was scheduled"""

        # Look for messages from the lead after the task was created
        recent_lead_messages = self.db.query(Message).filter(
            and_(
                Message.agent_session_id == task.agent_session_id,
                Message.sender_type == "lead",
                Message.created_at > task.created_at
            )
        ).count()

        return recent_lead_messages > 0

    async def _generate_follow_up_message(self, task: FollowUpTask) -> Optional[Message]:
        """Generate the actual follow-up message"""

        try:
            # Import here to avoid circular imports
            from services.agent_service import AgentService

            agent_service = AgentService(self.db)

            # Build context for message generation
            context = {
                "follow_up_task": task.to_dict(),
                "sequence_progress": task.get_sequence_progress(),
                "original_trigger": task.trigger_context
            }

            # Generate message using agent service (async)
            message = await agent_service.generate_follow_up_message(
                agent_session_id=task.agent_session_id,
                template=task.message_template,
                template_type=task.template_type,
                context=context
            )

            return message

        except Exception as e:
            logger.error(f"Error in message generation for task {task.id}: {str(e)}")
            return None

    def cancel_pending_tasks(self, agent_session_id: int, task_types: List[str] = None,
                           reason: str = "Cancelled by system") -> int:
        """
        Cancel pending follow-up tasks for a session

        Args:
            agent_session_id: ID of the agent session
            task_types: Optional list of task types to cancel (cancels all if None)
            reason: Reason for cancellation

        Returns:
            Number of tasks cancelled
        """

        query = self.db.query(FollowUpTask).filter(
            and_(
                FollowUpTask.agent_session_id == agent_session_id,
                FollowUpTask.status == "pending"
            )
        )

        if task_types:
            query = query.filter(FollowUpTask.task_type.in_(task_types))

        tasks_to_cancel = query.all()

        cancelled_count = 0
        for task in tasks_to_cancel:
            task.mark_cancelled(reason)
            cancelled_count += 1

        try:
            self.db.commit()
            logger.info(f"Cancelled {cancelled_count} pending tasks for session {agent_session_id}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cancelling tasks: {str(e)}")
            return 0

        return cancelled_count

    def get_session_pending_tasks(self, agent_session_id: int) -> List[Dict[str, Any]]:
        """Get all pending follow-up tasks for a session"""

        tasks = self.db.query(FollowUpTask).filter(
            and_(
                FollowUpTask.agent_session_id == agent_session_id,
                FollowUpTask.status == "pending"
            )
        ).order_by(FollowUpTask.scheduled_at).all()

        return [task.to_dict() for task in tasks]

    def reschedule_task(self, task_id: int, new_scheduled_time: datetime,
                       reason: str = "Rescheduled") -> bool:
        """Reschedule a pending task to a new time"""

        task = self.db.query(FollowUpTask).filter(FollowUpTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return False

        if task.status != "pending":
            logger.warning(f"Task {task_id} is not pending, cannot reschedule")
            return False

        old_time = task.scheduled_at
        task.scheduled_at = new_scheduled_time
        task.execution_metadata = task.execution_metadata or {}
        task.execution_metadata['rescheduled'] = {
            'from': old_time.isoformat(),
            'to': new_scheduled_time.isoformat(),
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }

        try:
            self.db.commit()
            logger.info(f"Rescheduled task {task_id} from {old_time} to {new_scheduled_time}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error rescheduling task {task_id}: {str(e)}")
            return False

    def get_task_statistics(self, days_back: int = 7) -> Dict[str, Any]:
        """Get statistics about follow-up task execution"""

        since_date = datetime.utcnow() - timedelta(days=days_back)

        # Count tasks by status
        total_tasks = self.db.query(FollowUpTask).filter(
            FollowUpTask.created_at >= since_date
        ).count()

        executed_tasks = self.db.query(FollowUpTask).filter(
            and_(
                FollowUpTask.created_at >= since_date,
                FollowUpTask.status == "executed"
            )
        ).count()

        failed_tasks = self.db.query(FollowUpTask).filter(
            and_(
                FollowUpTask.created_at >= since_date,
                FollowUpTask.status == "failed"
            )
        ).count()

        pending_tasks = self.db.query(FollowUpTask).filter(
            and_(
                FollowUpTask.created_at >= since_date,
                FollowUpTask.status == "pending"
            )
        ).count()

        cancelled_tasks = self.db.query(FollowUpTask).filter(
            and_(
                FollowUpTask.created_at >= since_date,
                FollowUpTask.status == "cancelled"
            )
        ).count()

        return {
            "period_days": days_back,
            "total_tasks": total_tasks,
            "executed": executed_tasks,
            "failed": failed_tasks,
            "pending": pending_tasks,
            "cancelled": cancelled_tasks,
            "success_rate": (executed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }

    def handle_lead_response(self, agent_session_id: int) -> Dict[str, Any]:
        """
        Handle when a lead responds - potentially cancelling no-response follow-ups

        Args:
            agent_session_id: ID of the session where lead responded

        Returns:
            Summary of actions taken
        """

        logger.info(f"Handling lead response for session {agent_session_id}")

        # Cancel pending no-response follow-ups
        cancelled_count = self.cancel_pending_tasks(
            agent_session_id=agent_session_id,
            task_types=['no_response_sequence', 'no_response_single'],
            reason="Lead responded"
        )

        return {
            "session_id": agent_session_id,
            "cancelled_tasks": cancelled_count,
            "action": "cancelled_no_response_followups"
        }

    async def start_background_processor(self, check_interval_seconds: int = 60):
        """
        Start background processor for executing due tasks

        Args:
            check_interval_seconds: How often to check for due tasks
        """

        logger.info(f"Starting background follow-up processor (check interval: {check_interval_seconds}s)")

        while True:
            try:
                results = self.execute_due_tasks()
                if results["executed"] > 0 or results["failed"] > 0:
                    logger.info(f"Background processor results: {results}")

                await asyncio.sleep(check_interval_seconds)

            except Exception as e:
                logger.error(f"Error in background processor: {str(e)}")
                await asyncio.sleep(check_interval_seconds * 2)  # Back off on errors