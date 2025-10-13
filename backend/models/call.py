"""
Call model for tracking outbound calls
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Call(Base):
    __tablename__ = "calls"

    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)

    # Call details
    phone_number = Column(String(50), nullable=False)
    call_status = Column(String(50), nullable=False, default="pending", index=True)
    # Status options: pending, calling, in_progress, completed, failed, no_answer

    room_name = Column(String(255), nullable=True)  # LiveKit room name
    call_duration = Column(Integer, nullable=True)  # Duration in seconds

    # Call content
    transcript = Column(Text, nullable=True)
    call_summary = Column(Text, nullable=True)

    # Call metadata
    call_metadata = Column(JSON, nullable=True, default=dict)
    # Can store: customer_info, call_outcome, appointment_scheduled, etc.

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    initiated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    answered_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    lead = relationship("Lead", back_populates="calls")
    agent = relationship("Agent", back_populates="calls")

    def __repr__(self):
        return f"<Call(id={self.id}, lead_id={self.lead_id}, status='{self.call_status}', phone='{self.phone_number}')>"

    def to_dict(self):
        """Convert Call instance to dictionary"""
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "agent_id": self.agent_id,
            "phone_number": self.phone_number,
            "call_status": self.call_status,
            "room_name": self.room_name,
            "call_duration": self.call_duration,
            "transcript": self.transcript,
            "call_summary": self.call_summary,
            "call_metadata": self.call_metadata or {},
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "initiated_at": self.initiated_at.isoformat() if self.initiated_at else None,
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }