"""
Inbound call model for tracking incoming calls
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class InboundCall(Base):
    __tablename__ = "inbound_calls"

    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)  # Created after call processing
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, index=True)  # Assigned during call

    # Call details
    caller_phone_number = Column(String(50), nullable=False, index=True)  # Who's calling
    inbound_phone_number = Column(String(50), nullable=False, default="+17622437375")  # Our number they called
    call_status = Column(String(50), nullable=False, default="received", index=True)
    # Status options: received, ringing, answered, in_progress, completed, failed, no_answer, rejected

    # External tracking
    twilio_call_sid = Column(String(255), nullable=True, index=True)  # Twilio's call identifier
    livekit_call_id = Column(String(255), nullable=True)  # LiveKit's call identifier
    room_name = Column(String(255), nullable=True)  # LiveKit room name

    # Call content
    call_duration = Column(Integer, nullable=True)  # Duration in seconds
    transcript = Column(Text, nullable=True)
    call_summary = Column(Text, nullable=True)

    # Call metadata
    call_metadata = Column(JSON, nullable=True, default=dict)
    # Can store: caller_info, call_outcome, lead_qualification_result, appointment_scheduled, etc.

    # Error tracking
    error_message = Column(Text, nullable=True)
    rejection_reason = Column(String(255), nullable=True)  # Why call was rejected (no agents, etc.)

    # Timestamps
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # When we got webhook
    answered_at = Column(DateTime(timezone=True), nullable=True)  # When agent joined
    ended_at = Column(DateTime(timezone=True), nullable=True)  # When call ended
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    lead = relationship("Lead", back_populates="inbound_calls")
    agent = relationship("Agent", back_populates="inbound_calls")

    def __repr__(self):
        return f"<InboundCall(id={self.id}, caller='{self.caller_phone_number}', status='{self.call_status}', lead_id={self.lead_id})>"

    def to_dict(self):
        """Convert InboundCall instance to dictionary"""
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "agent_id": self.agent_id,
            "caller_phone_number": self.caller_phone_number,
            "inbound_phone_number": self.inbound_phone_number,
            "call_status": self.call_status,
            "twilio_call_sid": self.twilio_call_sid,
            "livekit_call_id": self.livekit_call_id,
            "room_name": self.room_name,
            "call_duration": self.call_duration,
            "transcript": self.transcript,
            "call_summary": self.call_summary,
            "call_metadata": self.call_metadata or {},
            "error_message": self.error_message,
            "rejection_reason": self.rejection_reason,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }