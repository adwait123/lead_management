"""
Lead model definition
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from .database import Base

class Lead(Base):
    __tablename__ = "leads"

    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True, index=True)  # Make nullable for first_name/last_name split
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True, index=True)
    address = Column(Text, nullable=True)  # Full address for service businesses
    external_id = Column(String(255), nullable=True, index=True)  # For Yelp lead ID, Zapier IDs, etc.

    # Lead details
    service_requested = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="new", index=True)
    # Status options: new, contacted, qualified, won, lost

    source = Column(String(100), nullable=False, index=True)
    # Source options: Facebook Ads, Google Ads, Website, Referral

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # JSON fields for complex data
    notes = Column(JSON, nullable=True, default=list)
    # Array of note objects: [{"id": 1, "content": "...", "timestamp": "...", "author": "..."}]

    interaction_history = Column(JSON, nullable=True, default=list)
    # Array of interaction objects: [{"id": 1, "type": "email", "content": "...", "timestamp": "...", "agent_id": 1}]

    def __repr__(self):
        return f"<Lead(id={self.id}, name='{self.name}', email='{self.email}', status='{self.status}')>"

    def to_dict(self):
        """Convert Lead instance to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "address": self.address,
            "external_id": self.external_id,
            "service_requested": self.service_requested,
            "status": self.status,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes or [],
            "interaction_history": self.interaction_history or []
        }