"""
Business Profile model for AI Lead Management system
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean
from sqlalchemy.sql import func
from .database import Base


class BusinessProfile(Base):
    """Business profile model for storing company information and settings"""
    __tablename__ = "business_profiles"

    id = Column(Integer, primary_key=True, index=True)

    # Basic business information
    company_name = Column(String(255), nullable=False)
    service_area = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    website = Column(String(255), nullable=True)

    # Business details
    business_hours = Column(String(255), nullable=False)
    emergency_hours = Column(String(255), nullable=True)
    services_offered = Column(Text, nullable=False)
    service_area_details = Column(Text, nullable=True)

    # Policies
    pricing_policy = Column(Text, nullable=True)
    warranty_policy = Column(Text, nullable=True)
    cancellation_policy = Column(Text, nullable=True)

    # Business settings
    industry = Column(String(100), nullable=False, default="home_services")
    business_type = Column(String(100), nullable=True)  # plumbing, hvac, electrical, general_contractor, etc.

    # Contact preferences
    preferred_contact_method = Column(String(50), nullable=True, default="phone")  # phone, email, text
    response_time_expectation = Column(String(100), nullable=True)  # "within 1 hour", "same day", etc.

    # Service area details (can be expanded to geographic data)
    service_radius = Column(Integer, nullable=True)  # Miles from business location
    travel_fee_threshold = Column(Integer, nullable=True)  # Miles before travel fee applies
    travel_fee_amount = Column(String(20), nullable=True)  # Dollar amount for travel fee

    # Business hours in structured format
    operating_schedule = Column(JSON, nullable=True)  # {"monday": {"start": "8:00", "end": "17:00", "closed": false}, ...}

    # Emergency service settings
    emergency_services_available = Column(Boolean, default=False)
    emergency_contact_number = Column(String(50), nullable=True)
    emergency_hours = Column(JSON, nullable=True)  # Structured emergency hours

    # Licensing and certifications
    license_number = Column(String(100), nullable=True)
    certifications = Column(JSON, nullable=True, default=list)  # List of certifications
    insurance_info = Column(JSON, nullable=True)  # Insurance details

    # Marketing and branding
    tagline = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    specialties = Column(JSON, nullable=True, default=list)  # Areas of expertise

    # Settings and preferences
    booking_settings = Column(JSON, nullable=True, default=dict)  # Online booking preferences
    communication_preferences = Column(JSON, nullable=True, default=dict)  # How to communicate with customers
    notification_settings = Column(JSON, nullable=True, default=dict)  # Internal notifications

    # Status
    is_active = Column(Boolean, default=True)
    setup_completed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<BusinessProfile(id={self.id}, company='{self.company_name}', industry='{self.industry}')>"


class FAQ(Base):
    """Frequently Asked Questions for business profiles"""
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    business_profile_id = Column(Integer, nullable=True)  # Can be global or business-specific

    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)  # pricing, services, scheduling, policies, etc.

    # Usage tracking
    usage_count = Column(Integer, default=0)
    is_popular = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    is_global = Column(Boolean, default=False)  # Can be used by all businesses in same industry

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<FAQ(id={self.id}, question='{self.question[:50]}...')>"