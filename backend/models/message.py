"""
Message model for storing conversation messages between agents and leads
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class Message(Base):
    """Model for storing individual messages in agent-lead conversations"""
    __tablename__ = "messages"

    # Primary fields
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key relationships
    agent_session_id = Column(Integer, ForeignKey("agent_sessions.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, index=True)  # Null for lead messages

    # Message content
    content = Column(Text, nullable=False)
    message_type = Column(String(50), nullable=False, default="text", index=True)
    # Types: text, voice, image, file, system_notification, etc.

    # Message direction and sender info
    sender_type = Column(String(20), nullable=False, index=True)
    # Values: "agent", "lead", "system"

    sender_name = Column(String(255), nullable=True)
    # Display name for the sender

    # Message status and delivery
    message_status = Column(String(50), nullable=False, default="sent", index=True)
    # Values: draft, sent, delivered, read, failed

    delivery_status = Column(String(50), nullable=True, index=True)
    # Values: pending, sent_to_external, delivered, failed

    error_message = Column(Text, nullable=True)
    # Store any delivery errors

    # External platform integration
    external_message_id = Column(String(255), nullable=True, index=True)
    # ID from external platform (Yelp, Zapier, etc.)

    external_conversation_id = Column(String(255), nullable=True, index=True)
    # Conversation ID from external platform

    external_platform = Column(String(100), nullable=True, index=True)
    # Platform: yelp, zapier, sms, email, etc.

    # Message metadata
    message_metadata = Column(JSON, nullable=True, default=dict)
    # Additional data: attachments, formatting, platform-specific info

    # AI/Agent specific fields
    prompt_used = Column(Text, nullable=True)
    # The prompt template used to generate agent responses

    model_used = Column(String(100), nullable=True)
    # AI model used for generation (gpt-3.5-turbo, etc.)

    response_time_ms = Column(Integer, nullable=True)
    # Time taken to generate response in milliseconds

    token_usage = Column(JSON, nullable=True)
    # Token usage statistics for AI responses

    # Threading and conversation flow
    parent_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True, index=True)
    # For threading/reply chains

    thread_id = Column(String(255), nullable=True, index=True)
    # Thread identifier for grouping related messages

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Content moderation and quality
    is_flagged = Column(Boolean, default=False, nullable=False)
    flagged_reason = Column(String(255), nullable=True)
    quality_score = Column(String(10), nullable=True)  # 0.0 - 1.0 stored as string

    # Relationships
    agent_session = relationship("AgentSession", backref="messages")
    lead = relationship("Lead", backref="messages")
    agent = relationship("Agent", backref="messages")

    # Self-referential relationship for threading
    parent_message = relationship("Message", remote_side=[id], backref="replies")

    def __repr__(self):
        return f"<Message(id={self.id}, sender='{self.sender_type}', session={self.agent_session_id}, type='{self.message_type}')>"

    def to_dict(self):
        """Convert Message instance to dictionary"""
        return {
            "id": self.id,
            "agent_session_id": self.agent_session_id,
            "lead_id": self.lead_id,
            "agent_id": self.agent_id,
            "content": self.content,
            "message_type": self.message_type,
            "sender_type": self.sender_type,
            "sender_name": self.sender_name,
            "message_status": self.message_status,
            "delivery_status": self.delivery_status,
            "error_message": self.error_message,
            "external_message_id": self.external_message_id,
            "external_conversation_id": self.external_conversation_id,
            "external_platform": self.external_platform,
            "message_metadata": self.message_metadata or {},
            "prompt_used": self.prompt_used,
            "model_used": self.model_used,
            "response_time_ms": self.response_time_ms,
            "token_usage": self.token_usage or {},
            "parent_message_id": self.parent_message_id,
            "thread_id": self.thread_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "is_flagged": self.is_flagged,
            "flagged_reason": self.flagged_reason,
            "quality_score": self.quality_score
        }

    def mark_delivered(self, external_id: str = None):
        """Mark message as delivered"""
        from datetime import datetime
        self.delivery_status = "delivered"
        self.delivered_at = datetime.utcnow()
        if external_id:
            self.external_message_id = external_id

    def mark_read(self):
        """Mark message as read"""
        from datetime import datetime
        self.message_status = "read"
        self.read_at = datetime.utcnow()

    def mark_failed(self, error: str):
        """Mark message as failed with error"""
        self.delivery_status = "failed"
        self.message_status = "failed"
        self.error_message = error

    def get_conversation_context(self, db_session, limit: int = 10):
        """Get recent messages in the same conversation for context"""
        return db_session.query(Message)\
            .filter(Message.agent_session_id == self.agent_session_id)\
            .filter(Message.id < self.id)\
            .order_by(Message.created_at.desc())\
            .limit(limit)\
            .all()

    def is_from_agent(self) -> bool:
        """Check if this message is from an agent"""
        return self.sender_type == "agent"

    def is_from_lead(self) -> bool:
        """Check if this message is from a lead"""
        return self.sender_type == "lead"

    def is_system_message(self) -> bool:
        """Check if this is a system message"""
        return self.sender_type == "system"

    def is_from_business_owner(self) -> bool:
        """Check if this message is from a business owner"""
        return self.sender_type == "business_owner"

    def get_display_content(self, max_length: int = 100) -> str:
        """Get truncated content for display purposes"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length-3] + "..."

    @classmethod
    def create_agent_message(cls, agent_session_id: int, lead_id: int, agent_id: int,
                           content: str, metadata: dict = None, **kwargs):
        """Factory method to create agent messages"""
        # Extract message_type from kwargs to avoid duplicate parameter
        message_type = kwargs.pop('message_type', 'text')
        return cls(
            agent_session_id=agent_session_id,
            lead_id=lead_id,
            agent_id=agent_id,
            content=content,
            sender_type="agent",
            message_type=message_type,
            message_metadata=metadata or {},
            **kwargs
        )

    @classmethod
    def create_lead_message(cls, agent_session_id: int, lead_id: int, content: str,
                          external_conversation_id: str = None, metadata: dict = None, **kwargs):
        """Factory method to create lead messages"""
        # Extract message_type from kwargs to avoid duplicate parameter
        message_type = kwargs.pop('message_type', 'text')
        return cls(
            agent_session_id=agent_session_id,
            lead_id=lead_id,
            agent_id=None,
            content=content,
            sender_type="lead",
            external_conversation_id=external_conversation_id,
            message_type=message_type,
            message_metadata=metadata or {},
            **kwargs
        )

    @classmethod
    def create_business_owner_message(cls, agent_session_id: int, lead_id: int, content: str,
                                    business_owner_name: str = None, metadata: dict = None, **kwargs):
        """Factory method to create business owner messages"""
        # Extract message_type from kwargs to avoid duplicate parameter
        message_type = kwargs.pop('message_type', 'text')
        return cls(
            agent_session_id=agent_session_id,
            lead_id=lead_id,
            agent_id=None,
            content=content,
            sender_type="business_owner",
            sender_name=business_owner_name or "Business Owner",
            message_type=message_type,
            message_metadata=metadata or {},
            **kwargs
        )

    @classmethod
    def create_system_message(cls, agent_session_id: int, lead_id: int, content: str,
                            metadata: dict = None, **kwargs):
        """Factory method to create system messages"""
        # Extract message_type from kwargs to avoid duplicate parameter
        message_type = kwargs.pop('message_type', 'system_notification')
        return cls(
            agent_session_id=agent_session_id,
            lead_id=lead_id,
            agent_id=None,
            content=content,
            sender_type="system",
            message_type=message_type,
            message_metadata=metadata or {},
            **kwargs
        )