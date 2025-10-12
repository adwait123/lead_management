"""
FollowUpTask model for tracking scheduled follow-up messages in agent workflows
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class FollowUpTask(Base):
    """Model for tracking individual scheduled follow-up tasks"""
    __tablename__ = "follow_up_tasks"

    # Primary fields
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key relationships
    agent_session_id = Column(Integer, ForeignKey("agent_sessions.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)

    # Task identification
    workflow_step_id = Column(String(255), nullable=False, index=True)
    # Links to the workflow step definition in agent.workflow_steps

    task_type = Column(String(100), nullable=False, index=True)
    # Types: no_response_sequence, appointment_reminder, reengagement, etc.

    # Sequence tracking
    sequence_name = Column(String(100), nullable=True, index=True)
    # For grouping related sequence steps (e.g., "no_response_sequence")

    sequence_position = Column(Integer, nullable=True, index=True)
    # Position in sequence (1, 2, 3, etc.)

    total_sequence_steps = Column(Integer, nullable=True)
    # Total steps in the sequence for progress tracking

    # Timing configuration
    trigger_event = Column(String(100), nullable=False, index=True)
    # What event triggers this follow-up (no_response, appointment_scheduled, etc.)

    delay_minutes = Column(Integer, nullable=False, index=True)
    # Delay in minutes from the trigger event

    original_delay = Column(Integer, nullable=False)
    # Original delay value as configured by user

    original_unit = Column(String(20), nullable=False)
    # Original time unit (minutes, hours, days)

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    # When this task should be executed

    executed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    # When this task was actually executed

    # Task status
    status = Column(String(50), nullable=False, default="pending", index=True)
    # Values: pending, executed, cancelled, failed, skipped

    failure_reason = Column(Text, nullable=True)
    # Why the task failed if status is 'failed'

    # Message configuration
    message_template = Column(Text, nullable=True)
    # Template for the follow-up message

    template_type = Column(String(100), nullable=True)
    # Type of template (no_response_sequence, appointment_reminder, etc.)

    generated_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True, index=True)
    # Link to the generated message if task was executed

    # Context and metadata
    trigger_context = Column(JSON, nullable=True, default=dict)
    # Context data from when the trigger occurred

    execution_metadata = Column(JSON, nullable=True, default=dict)
    # Additional data about task execution

    # Dependencies and conditions
    depends_on_task_id = Column(Integer, ForeignKey("follow_up_tasks.id"), nullable=True, index=True)
    # If this task depends on another task being completed

    conditions = Column(JSON, nullable=True, default=dict)
    # Additional conditions that must be met for execution

    # Retry configuration
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    agent_session = relationship("AgentSession", backref="follow_up_tasks")
    lead = relationship("Lead", backref="follow_up_tasks")
    agent = relationship("Agent", backref="follow_up_tasks")
    generated_message = relationship("Message", backref="follow_up_task")

    # Self-referential relationship for task dependencies
    dependency = relationship("FollowUpTask", remote_side=[id], backref="dependent_tasks")

    def __repr__(self):
        return f"<FollowUpTask(id={self.id}, type='{self.task_type}', status='{self.status}', session={self.agent_session_id})>"

    def to_dict(self):
        """Convert FollowUpTask instance to dictionary"""
        return {
            "id": self.id,
            "agent_session_id": self.agent_session_id,
            "lead_id": self.lead_id,
            "agent_id": self.agent_id,
            "workflow_step_id": self.workflow_step_id,
            "task_type": self.task_type,
            "sequence_name": self.sequence_name,
            "sequence_position": self.sequence_position,
            "total_sequence_steps": self.total_sequence_steps,
            "trigger_event": self.trigger_event,
            "delay_minutes": self.delay_minutes,
            "original_delay": self.original_delay,
            "original_unit": self.original_unit,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "status": self.status,
            "failure_reason": self.failure_reason,
            "message_template": self.message_template,
            "template_type": self.template_type,
            "generated_message_id": self.generated_message_id,
            "trigger_context": self.trigger_context or {},
            "execution_metadata": self.execution_metadata or {},
            "depends_on_task_id": self.depends_on_task_id,
            "conditions": self.conditions or {},
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def is_ready_for_execution(self):
        """Check if this task is ready to be executed"""
        if self.status != "pending":
            return False

        from datetime import datetime
        current_time = datetime.utcnow()

        # Check if scheduled time has arrived
        if self.scheduled_at > current_time:
            return False

        # Check if dependency is satisfied
        if self.depends_on_task_id:
            # This would need to be checked against the database
            # Implementation depends on how dependencies are handled
            pass

        # Check additional conditions
        if self.conditions:
            # Implementation depends on condition types
            pass

        return True

    def mark_executed(self, message_id: int = None):
        """Mark task as successfully executed"""
        from datetime import datetime
        self.status = "executed"
        self.executed_at = datetime.utcnow()
        if message_id:
            self.generated_message_id = message_id

    def mark_failed(self, reason: str):
        """Mark task as failed with reason"""
        self.status = "failed"
        self.failure_reason = reason

    def mark_cancelled(self, reason: str = None):
        """Mark task as cancelled"""
        self.status = "cancelled"
        if reason:
            self.failure_reason = reason

    def schedule_retry(self, delay_minutes: int = 30):
        """Schedule a retry of this task"""
        from datetime import datetime, timedelta

        if self.retry_count >= self.max_retries:
            self.mark_failed(f"Max retries ({self.max_retries}) exceeded")
            return False

        self.retry_count += 1
        self.next_retry_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
        self.status = "pending"
        self.failure_reason = None

        return True

    def get_sequence_progress(self):
        """Get progress information for this sequence"""
        if not self.sequence_position or not self.total_sequence_steps:
            return None

        return {
            "current_step": self.sequence_position,
            "total_steps": self.total_sequence_steps,
            "is_first": self.sequence_position == 1,
            "is_last": self.sequence_position == self.total_sequence_steps,
            "progress_percentage": (self.sequence_position / self.total_sequence_steps) * 100
        }

    @classmethod
    def create_sequence_tasks(cls, agent_session_id: int, lead_id: int, agent_id: int,
                            workflow_steps: list, trigger_context: dict = None):
        """Factory method to create a sequence of follow-up tasks"""
        tasks = []

        for step in workflow_steps:
            if step.get('type') == 'time_based_trigger':
                task = cls(
                    agent_session_id=agent_session_id,
                    lead_id=lead_id,
                    agent_id=agent_id,
                    workflow_step_id=step.get('id'),
                    task_type=step.get('action', {}).get('template_type', 'unknown'),
                    sequence_name=step.get('sequence_name'),
                    sequence_position=step.get('sequence_position'),
                    total_sequence_steps=len([s for s in workflow_steps if s.get('sequence_name') == step.get('sequence_name')]),
                    trigger_event=step.get('trigger', {}).get('event'),
                    delay_minutes=step.get('trigger', {}).get('delay_minutes', 0),
                    original_delay=step.get('trigger', {}).get('original_delay', 0),
                    original_unit=step.get('trigger', {}).get('original_unit', 'minutes'),
                    message_template=step.get('action', {}).get('template'),
                    template_type=step.get('action', {}).get('template_type'),
                    trigger_context=trigger_context or {}
                )
                tasks.append(task)

        return tasks

    def calculate_execution_time(self, reference_time=None):
        """Calculate when this task should be executed based on reference time"""
        from datetime import datetime, timedelta

        if reference_time is None:
            reference_time = datetime.utcnow()

        # For negative delays (like appointment reminders), subtract from reference time
        if self.delay_minutes < 0:
            execution_time = reference_time - timedelta(minutes=abs(self.delay_minutes))
        else:
            execution_time = reference_time + timedelta(minutes=self.delay_minutes)

        return execution_time