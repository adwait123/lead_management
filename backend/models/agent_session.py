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