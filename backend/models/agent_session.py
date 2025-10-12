"""
AgentSession model for managing persistent agent-to-lead conversations
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class AgentSession(Base):
    """Model for tracking active agent sessions with leads"""
    __tablename__ = "agent_sessions"

    # Primary fields
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key relationships
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)

    # Session configuration
    trigger_type = Column(String(100), nullable=False, index=True)
    # Options: new_lead, form_submission, email_opened, website_visit, etc.

    session_status = Column(String(50), nullable=False, default="active", index=True)
    # Options: active, completed, escalated, timeout, paused

    # Session context and metadata
    initial_context = Column(JSON, nullable=True, default=dict)
    # Context data from the trigger event (form data, lead source, etc.)

    session_metadata = Column(JSON, nullable=True, default=dict)
    # Additional session configuration and runtime data

    # Conversation tracking
    message_count = Column(Integer, default=0, nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    last_message_from = Column(String(50), nullable=True)  # 'agent' or 'lead'

    # Session lifecycle
    session_goal = Column(String(255), nullable=True)
    # What the agent is trying to achieve (close_lead, qualify_lead, provide_support, etc.)

    completion_reason = Column(String(100), nullable=True)
    # Why the session ended (goal_achieved, timeout, escalated, etc.)

    # Performance tracking
    response_time_avg = Column(String(10), nullable=True, default="0.0")  # Average response time in seconds
    satisfaction_score = Column(String(10), nullable=True)  # Lead satisfaction if available

    # Escalation and handoff
    escalated_to = Column(String(255), nullable=True)  # User or system that received escalation
    escalation_reason = Column(Text, nullable=True)

    # Session settings
    auto_timeout_hours = Column(Integer, default=48, nullable=False)  # Hours of inactivity before timeout
    max_message_count = Column(Integer, default=100, nullable=False)  # Max messages before escalation

    # Follow-up sequence tracking
    active_follow_up_sequences = Column(JSON, nullable=True, default=dict)
    # Tracks active follow-up sequences: {"no_response": {"active": true, "current_step": 1, "total_steps": 3}}

    last_follow_up_trigger = Column(DateTime(timezone=True), nullable=True)
    # When the last follow-up sequence was triggered

    follow_up_sequence_state = Column(JSON, nullable=True, default=dict)
    # Detailed state for follow-up sequences

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    agent = relationship("Agent", backref="sessions")
    # Note: Lead relationship will be added when we update the Lead model

    def __repr__(self):
        return f"<AgentSession(id={self.id}, agent_id={self.agent_id}, lead_id={self.lead_id}, status='{self.session_status}')>"

    def to_dict(self):
        """Convert AgentSession instance to dictionary"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "lead_id": self.lead_id,
            "trigger_type": self.trigger_type,
            "session_status": self.session_status,
            "initial_context": self.initial_context or {},
            "session_metadata": self.session_metadata or {},
            "message_count": self.message_count,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "last_message_from": self.last_message_from,
            "session_goal": self.session_goal,
            "completion_reason": self.completion_reason,
            "response_time_avg": self.response_time_avg,
            "satisfaction_score": self.satisfaction_score,
            "escalated_to": self.escalated_to,
            "escalation_reason": self.escalation_reason,
            "auto_timeout_hours": self.auto_timeout_hours,
            "max_message_count": self.max_message_count,
            "active_follow_up_sequences": self.active_follow_up_sequences or {},
            "last_follow_up_trigger": self.last_follow_up_trigger.isoformat() if self.last_follow_up_trigger else None,
            "follow_up_sequence_state": self.follow_up_sequence_state or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None
        }

    def is_timeout_eligible(self):
        """Check if session is eligible for timeout based on inactivity"""
        if self.session_status != "active" or not self.last_message_at:
            return False

        import datetime
        timeout_threshold = datetime.datetime.utcnow() - datetime.timedelta(hours=self.auto_timeout_hours)
        return self.last_message_at < timeout_threshold

    def should_escalate(self):
        """Check if session should be escalated based on message count or other criteria"""
        if self.session_status != "active":
            return False

        # Escalate if max message count reached
        if self.message_count >= self.max_message_count:
            return True

        # Additional escalation criteria can be added here
        return False

    def update_message_stats(self, from_agent=True):
        """Update session statistics when a new message is sent"""
        from datetime import datetime

        self.message_count += 1
        self.last_message_at = datetime.utcnow()
        self.last_message_from = "agent" if from_agent else "lead"

    def end_session(self, reason, escalated_to=None):
        """End the agent session with a reason"""
        from datetime import datetime

        self.session_status = "escalated" if escalated_to else "completed"
        self.completion_reason = reason
        self.ended_at = datetime.utcnow()

        if escalated_to:
            self.escalated_to = escalated_to

    def start_follow_up_sequence(self, sequence_type: str, total_steps: int):
        """Start tracking a new follow-up sequence"""
        from datetime import datetime

        if self.active_follow_up_sequences is None:
            self.active_follow_up_sequences = {}

        self.active_follow_up_sequences[sequence_type] = {
            "active": True,
            "current_step": 0,
            "total_steps": total_steps,
            "started_at": datetime.utcnow().isoformat()
        }

        self.last_follow_up_trigger = datetime.utcnow()

    def advance_follow_up_sequence(self, sequence_type: str) -> bool:
        """Advance a follow-up sequence to the next step"""
        if not self.active_follow_up_sequences or sequence_type not in self.active_follow_up_sequences:
            return False

        sequence = self.active_follow_up_sequences[sequence_type]
        if not sequence.get("active"):
            return False

        sequence["current_step"] += 1

        # Check if sequence is complete
        if sequence["current_step"] >= sequence["total_steps"]:
            sequence["active"] = False
            sequence["completed_at"] = datetime.utcnow().isoformat()

        return True

    def cancel_follow_up_sequence(self, sequence_type: str, reason: str = "Cancelled"):
        """Cancel an active follow-up sequence"""
        if not self.active_follow_up_sequences or sequence_type not in self.active_follow_up_sequences:
            return False

        sequence = self.active_follow_up_sequences[sequence_type]
        sequence["active"] = False
        sequence["cancelled_at"] = datetime.utcnow().isoformat()
        sequence["cancellation_reason"] = reason

        return True

    def get_follow_up_sequence_progress(self, sequence_type: str) -> dict:
        """Get progress information for a follow-up sequence"""
        if not self.active_follow_up_sequences or sequence_type not in self.active_follow_up_sequences:
            return {"exists": False}

        sequence = self.active_follow_up_sequences[sequence_type]
        return {
            "exists": True,
            "active": sequence.get("active", False),
            "current_step": sequence.get("current_step", 0),
            "total_steps": sequence.get("total_steps", 0),
            "progress_percentage": (sequence.get("current_step", 0) / sequence.get("total_steps", 1)) * 100,
            "started_at": sequence.get("started_at"),
            "completed_at": sequence.get("completed_at"),
            "cancelled_at": sequence.get("cancelled_at")
        }

    def has_active_follow_up_sequences(self) -> bool:
        """Check if this session has any active follow-up sequences"""
        if not self.active_follow_up_sequences:
            return False

        return any(
            seq.get("active", False)
            for seq in self.active_follow_up_sequences.values()
        )

    def get_time_since_last_message(self) -> int:
        """Get minutes since last message for follow-up timing"""
        if not self.last_message_at:
            return 0

        from datetime import datetime
        delta = datetime.utcnow() - self.last_message_at
        return int(delta.total_seconds() / 60)