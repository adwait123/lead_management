"""
Appointment model for AI Lead Management system
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class Appointment(Base):
    """Appointment model for managing customer appointments"""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    # Customer information
    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(50), nullable=False)
    customer_email = Column(String(255), nullable=True)
    customer_address = Column(Text, nullable=False)

    # Service details
    service_type = Column(String(100), nullable=False)  # plumbing, hvac, electrical, etc.
    appointment_type = Column(String(50), nullable=False)  # estimate, repair, installation, maintenance, emergency
    service_description = Column(Text, nullable=True)
    estimated_duration = Column(Integer, nullable=False, default=60)  # Duration in minutes

    # Scheduling
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Status tracking
    status = Column(String(50), nullable=False, default="pending")  # pending, confirmed, in_progress, completed, cancelled, rescheduled
    priority = Column(String(20), nullable=False, default="normal")  # low, normal, high, urgent

    # Assignment
    assigned_technician = Column(String(255), nullable=True)
    assigned_team = Column(String(100), nullable=True)  # sales_team, technical_team, etc.

    # Notes and communication
    customer_notes = Column(Text, nullable=True)  # Customer's specific requests or notes
    internal_notes = Column(Text, nullable=True)  # Internal team notes
    agent_notes = Column(Text, nullable=True)  # Notes from AI agent interaction

    # Lead source and tracking
    lead_source = Column(String(100), nullable=True)  # website, phone, referral, etc.
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)  # Which agent handled this

    # Confirmation and reminders
    confirmation_sent = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    follow_up_required = Column(Boolean, default=False)

    # Outcome tracking
    show_status = Column(String(50), nullable=True)  # showed, no_show, rescheduled
    outcome = Column(String(100), nullable=True)  # job_scheduled, estimate_provided, no_service_needed, etc.
    outcome_notes = Column(Text, nullable=True)

    # Pricing (if applicable)
    estimated_cost = Column(String(20), nullable=True)  # Store as string to avoid float precision issues
    final_cost = Column(String(20), nullable=True)

    # Timestamps
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    agent = relationship("Agent", back_populates="appointments")

    def __repr__(self):
        return f"<Appointment(id={self.id}, customer='{self.customer_name}', service='{self.service_type}', status='{self.status}')>"


class AppointmentType(Base):
    """Appointment type configuration for businesses"""
    __tablename__ = "appointment_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    default_duration = Column(Integer, nullable=False, default=60)  # Duration in minutes
    category = Column(String(50), nullable=False)  # estimate, repair, installation, maintenance, emergency
    is_active = Column(Boolean, default=True)
    requires_preparation = Column(Boolean, default=False)
    preparation_instructions = Column(Text, nullable=True)

    # Scheduling constraints
    advance_booking_required = Column(Integer, default=24)  # Hours of advance notice required
    max_advance_booking = Column(Integer, default=720)  # Maximum hours in advance (30 days default)
    business_hours_only = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<AppointmentType(id={self.id}, name='{self.name}', duration={self.default_duration})>"