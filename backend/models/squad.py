"""
Squad model for multi-agent orchestration
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean
from sqlalchemy.sql import func
from .database import Base


class Squad(Base):
    """Multi-agent squad configuration for inbound call orchestration"""
    __tablename__ = "squads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Ordered list of agent configs within this squad
    # Each entry: {key, name, prompt, tools, allowed_handoffs, deterministic_routes,
    #              context_input, context_output, max_turns}
    agents = Column(JSON, nullable=False, default=list)

    # Routing rules — deterministic routes that bypass LLM (e.g. billing -> hard transfer)
    routing_config = Column(JSON, nullable=True, default=dict)

    # Shared context schema — what gets passed between agents
    # e.g. {customer_name: "string", intent: "string", phone: "string"}
    shared_context_schema = Column(JSON, nullable=True, default=dict)

    # Default entry agent key
    entry_agent_key = Column(String(100), nullable=False, default="router")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Squad(id={self.id}, name='{self.name}')>"
