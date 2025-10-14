"""
Agent model for AI Lead Management system
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class Agent(Base):
    """AI Agent model with configuration and workflow capabilities"""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    type = Column(String(50), nullable=False, default="conversational")  # conversational, lead_qualifier, follow_up, etc.

    # Agent configuration
    use_case = Column(String(100), nullable=True, default="general_sales")  # Lead Qualification, Customer Support, etc.

    # Prompt configuration
    prompt_template = Column(Text, nullable=False)  # Main prompt/instructions for the agent
    prompt_template_name = Column(String(100), nullable=True)  # Which template was used
    prompt_variables = Column(JSON, nullable=True, default=dict)  # Variable values like {company_name: "Acme Corp"}

    # Personality configuration (expanded to object)
    personality_traits = Column(JSON, nullable=True, default=list)  # ['Professional', 'Friendly', ...]
    personality_style = Column(String(100), nullable=True, default="professional")  # Communication style
    response_length = Column(String(50), nullable=True, default="moderate")  # Brief, Moderate, Detailed
    custom_personality_instructions = Column(Text, nullable=True)  # Additional personality notes

    # AI Model configuration
    model = Column(String(100), nullable=False, default="gpt-3.5-turbo")
    temperature = Column(String(10), nullable=False, default="0.7")  # Store as string for precision
    max_tokens = Column(Integer, nullable=False, default=500)

    # Knowledge Base
    knowledge = Column(JSON, nullable=True, default=list)  # Knowledge base items

    # Tools and Actions
    enabled_tools = Column(JSON, nullable=True, default=list)  # List of enabled tool names
    tool_configs = Column(JSON, nullable=True, default=dict)  # Tool-specific configurations

    # Conversation Settings
    conversation_settings = Column(JSON, nullable=True, default=dict)  # Voice/text specific settings

    # Workflow configuration
    triggers = Column(JSON, nullable=True, default=list)  # Event triggers that activate this agent
    actions = Column(JSON, nullable=True, default=list)  # Actions the agent can perform
    workflow_steps = Column(JSON, nullable=True, default=list)  # Step-by-step workflow

    # Integration settings
    integrations = Column(JSON, nullable=True, default=list)  # Connected services/APIs

    # Status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)  # Can be shared/used by others
    created_by = Column(String(255), nullable=True, default="system")

    # Performance metrics
    total_interactions = Column(Integer, default=0, nullable=False)
    success_rate = Column(String(10), nullable=True, default="0.0")  # Store as string for precision
    avg_response_time = Column(String(10), nullable=True, default="0.0")  # In seconds

    # Sample conversations for testing
    sample_conversations = Column(JSON, nullable=True, default=list)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    appointments = relationship("Appointment", back_populates="agent")
    calls = relationship("Call", back_populates="agent")

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', type='{self.type}')>"