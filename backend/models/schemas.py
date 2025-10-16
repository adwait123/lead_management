"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

# Note schema
class NoteSchema(BaseModel):
    id: int
    content: str
    timestamp: datetime
    author: str = "System"

class NoteCreateSchema(BaseModel):
    content: str
    author: str = "User"

# Interaction schema
class InteractionSchema(BaseModel):
    id: int
    type: str  # email, call, sms, chat, etc.
    content: str
    timestamp: datetime
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None

# Survey and Project Data schemas
class SurveyAnswerSchema(BaseModel):
    question_text: str
    question_identifier: Optional[str] = None
    answer_text: List[str]

class AttachmentSchema(BaseModel):
    id: Optional[str] = None
    url: str
    resource_name: str
    mime_type: str

class AvailabilitySchema(BaseModel):
    status: str  # "SPECIFIC_DATES", "FLEXIBLE", etc.
    dates: Optional[List[str]] = []
    time_preferences: Optional[Dict[str, Any]] = {}

class ProjectLocationSchema(BaseModel):
    postal_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    full_address: Optional[str] = None

class ProjectDataSchema(BaseModel):
    """Rich project data structure matching Yelp format"""
    job_names: Optional[List[str]] = []
    additional_info: Optional[str] = None
    location: Optional[ProjectLocationSchema] = None
    availability: Optional[AvailabilitySchema] = None
    survey_answers: Optional[List[SurveyAnswerSchema]] = []
    attachments: Optional[List[AttachmentSchema]] = []
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    special_requirements: Optional[str] = None

# Lead schemas
class LeadBaseSchema(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    external_id: Optional[str] = None
    service_requested: Optional[str] = None
    status: str = "new"
    source: str

class LeadCreateSchema(LeadBaseSchema):
    notes: Optional[List[Dict[str, Any]]] = []
    interaction_history: Optional[List[Dict[str, Any]]] = []

    # Rich project data support
    project_data: Optional[ProjectDataSchema] = None

    # Platform-specific metadata (for Yelp IDs, conversation IDs, etc.)
    platform_metadata: Optional[Dict[str, Any]] = {}

class LeadUpdateSchema(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    external_id: Optional[str] = None
    service_requested: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None

class LeadResponseSchema(LeadBaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    notes: List[Dict[str, Any]] = []
    interaction_history: List[Dict[str, Any]] = []

    class Config:
        orm_mode = True

class LeadListResponseSchema(BaseModel):
    leads: List[LeadResponseSchema]
    total: int
    page: int
    per_page: int
    total_pages: int

# Lead filters
class LeadFiltersSchema(BaseModel):
    status: Optional[str] = None
    source: Optional[str] = None
    company: Optional[str] = None
    search: Optional[str] = None  # Search in name, email, company
    page: int = 1
    per_page: int = 20

# Agent schemas
class AgentBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    type: str = "text"  # voice, text, or both
    use_case: str = "general_sales"

    # Prompt configuration
    prompt_template: str
    prompt_template_name: Optional[str] = None
    prompt_variables: Optional[Dict[str, Any]] = {}

    # Personality configuration (expanded)
    personality_traits: Optional[List[str]] = []
    personality_style: str = "professional"
    response_length: str = "moderate"
    custom_personality_instructions: Optional[str] = None

    # AI Model configuration
    model: str = "gpt-3.5-turbo"
    temperature: str = "0.7"
    max_tokens: int = 500

    # Status
    is_active: bool = True
    is_public: bool = False

class AgentCreateSchema(AgentBaseSchema):
    # Knowledge Base
    knowledge: Optional[List[Dict[str, Any]]] = []

    # Tools and Actions
    enabled_tools: Optional[List[str]] = []
    tool_configs: Optional[Dict[str, Any]] = {}

    # Conversation Settings
    conversation_settings: Optional[Dict[str, Any]] = {}

    # Workflow configuration
    triggers: Optional[List[Dict[str, Any]]] = []
    actions: Optional[List[Dict[str, Any]]] = []
    workflow_steps: Optional[List[Dict[str, Any]]] = []
    integrations: Optional[List[Dict[str, Any]]] = []
    sample_conversations: Optional[List[Dict[str, Any]]] = []
    created_by: str = "user"

class AgentUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    use_case: Optional[str] = None

    # Prompt configuration
    prompt_template: Optional[str] = None
    prompt_template_name: Optional[str] = None
    prompt_variables: Optional[Dict[str, Any]] = None

    # Personality configuration
    personality_traits: Optional[List[str]] = None
    personality_style: Optional[str] = None
    response_length: Optional[str] = None
    custom_personality_instructions: Optional[str] = None

    # AI Model configuration
    model: Optional[str] = None
    temperature: Optional[str] = None
    max_tokens: Optional[int] = None

    # Knowledge Base
    knowledge: Optional[List[Dict[str, Any]]] = None

    # Tools and Actions
    enabled_tools: Optional[List[str]] = None
    tool_configs: Optional[Dict[str, Any]] = None

    # Conversation Settings
    conversation_settings: Optional[Dict[str, Any]] = None

    # Workflow configuration
    triggers: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    workflow_steps: Optional[List[Dict[str, Any]]] = None
    integrations: Optional[List[Dict[str, Any]]] = None
    sample_conversations: Optional[List[Dict[str, Any]]] = None

    # Status
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None

class AgentResponseSchema(AgentBaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None

    # Knowledge Base
    knowledge: List[Dict[str, Any]] = []

    # Tools and Actions
    enabled_tools: List[str] = []
    tool_configs: Dict[str, Any] = {}

    # Conversation Settings
    conversation_settings: Dict[str, Any] = {}

    # Workflow configuration
    triggers: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []
    workflow_steps: List[Dict[str, Any]] = []
    integrations: List[Dict[str, Any]] = []
    sample_conversations: List[Dict[str, Any]] = []

    # Performance metrics
    total_interactions: int = 0
    success_rate: str = "0.0"
    avg_response_time: str = "0.0"
    created_by: str = "system"

    class Config:
        orm_mode = True

    @validator('knowledge', pre=True)
    def parse_knowledge(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except json.JSONDecodeError:
                return []
        return v if v is not None else []

    @validator('enabled_tools', pre=True)
    def parse_enabled_tools(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except json.JSONDecodeError:
                return []
        return v if v is not None else []

    @validator('tool_configs', pre=True)
    def parse_tool_configs(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v) if v else {}
            except json.JSONDecodeError:
                return {}
        return v if v is not None else {}

    @validator('conversation_settings', pre=True)
    def parse_conversation_settings(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v) if v else {}
            except json.JSONDecodeError:
                return {}
        return v if v is not None else {}

    @validator('triggers', pre=True)
    def parse_triggers(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except json.JSONDecodeError:
                return []
        return v if v is not None else []

    @validator('actions', pre=True)
    def parse_actions(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except json.JSONDecodeError:
                return []
        return v if v is not None else []

    @validator('workflow_steps', pre=True)
    def parse_workflow_steps(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except json.JSONDecodeError:
                return []
        return v if v is not None else []

    @validator('integrations', pre=True)
    def parse_integrations(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except json.JSONDecodeError:
                return []
        return v if v is not None else []

    @validator('sample_conversations', pre=True)
    def parse_sample_conversations(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except json.JSONDecodeError:
                return []
        return v if v is not None else []

    @validator('personality_traits', pre=True)
    def parse_personality_traits(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except json.JSONDecodeError:
                return []
        return v if v is not None else []

    @validator('prompt_variables', pre=True)
    def parse_prompt_variables(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v) if v else {}
            except json.JSONDecodeError:
                return {}
        return v if v is not None else {}

class AgentListResponseSchema(BaseModel):
    agents: List[AgentResponseSchema]
    total: int
    page: int
    per_page: int
    total_pages: int

class AgentTestSchema(BaseModel):
    message: str

class AgentTestResponseSchema(BaseModel):
    response: str
    processing_time: float
    success: bool
    error: Optional[str] = None

# Agent Session schemas
class AgentSessionCreateSchema(BaseModel):
    agent_id: int
    lead_id: int
    trigger_type: str
    session_goal: Optional[str] = None
    initial_context: Optional[Dict[str, Any]] = {}
    auto_timeout_hours: Optional[int] = 48
    max_message_count: Optional[int] = 100

class AgentSessionUpdateSchema(BaseModel):
    session_status: Optional[str] = None
    completion_reason: Optional[str] = None
    escalated_to: Optional[str] = None
    escalation_reason: Optional[str] = None
    satisfaction_score: Optional[str] = None

class AgentSessionResponseSchema(BaseModel):
    id: int
    agent_id: int
    lead_id: int
    trigger_type: str
    session_status: str
    initial_context: Dict[str, Any]
    session_metadata: Dict[str, Any]
    message_count: int
    last_message_at: Optional[datetime]
    last_message_from: Optional[str]
    session_goal: Optional[str]
    completion_reason: Optional[str]
    response_time_avg: Optional[str]
    satisfaction_score: Optional[str]
    escalated_to: Optional[str]
    escalation_reason: Optional[str]
    auto_timeout_hours: int
    max_message_count: int
    created_at: datetime
    updated_at: datetime
    ended_at: Optional[datetime]

    class Config:
        orm_mode = True

class AgentSessionListResponseSchema(BaseModel):
    sessions: List[AgentSessionResponseSchema]
    total: int
    page: int
    page_size: int
    total_pages: int

class MessageStatsUpdateSchema(BaseModel):
    from_agent: bool = True

# Call schemas
class CallBaseSchema(BaseModel):
    lead_id: int
    agent_id: int
    phone_number: str
    call_status: str = "pending"

class CallCreateSchema(CallBaseSchema):
    call_metadata: Optional[Dict[str, Any]] = {}

class CallUpdateSchema(BaseModel):
    call_status: Optional[str] = None
    transcript: Optional[str] = None
    call_summary: Optional[str] = None
    call_duration: Optional[int] = None
    call_metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class CallResponseSchema(CallBaseSchema):
    id: int
    room_name: Optional[str] = None
    call_duration: Optional[int] = None
    transcript: Optional[str] = None
    call_summary: Optional[str] = None
    call_metadata: Dict[str, Any] = {}
    error_message: Optional[str] = None
    retry_count: int = 0
    initiated_at: datetime
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CallListResponseSchema(BaseModel):
    calls: List[CallResponseSchema]
    total: int
    page: int
    per_page: int
    total_pages: int

class CallTriggerSchema(BaseModel):
    """Schema for triggering outbound calls"""
    agent_id: Optional[int] = None  # If not provided, will use first available outbound agent
    force_call: bool = False  # Override normal trigger conditions

# Inbound Call schemas
class InboundCallBaseSchema(BaseModel):
    caller_phone_number: str
    inbound_phone_number: str = "+17622437375"
    call_status: str = "received"

class InboundCallCreateSchema(InboundCallBaseSchema):
    lead_id: Optional[int] = None  # Can be null initially, assigned after lead creation
    agent_id: Optional[int] = None  # Assigned when agent joins call
    twilio_call_sid: Optional[str] = None
    livekit_call_id: Optional[str] = None
    call_metadata: Optional[Dict[str, Any]] = {}

class InboundCallUpdateSchema(BaseModel):
    lead_id: Optional[int] = None
    agent_id: Optional[int] = None
    call_status: Optional[str] = None
    twilio_call_sid: Optional[str] = None
    livekit_call_id: Optional[str] = None
    room_name: Optional[str] = None
    call_duration: Optional[int] = None
    transcript: Optional[str] = None
    call_summary: Optional[str] = None
    call_metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    rejection_reason: Optional[str] = None

class InboundCallResponseSchema(InboundCallBaseSchema):
    id: int
    lead_id: Optional[int] = None
    agent_id: Optional[int] = None
    twilio_call_sid: Optional[str] = None
    livekit_call_id: Optional[str] = None
    room_name: Optional[str] = None
    call_duration: Optional[int] = None
    transcript: Optional[str] = None
    call_summary: Optional[str] = None
    call_metadata: Dict[str, Any] = {}
    error_message: Optional[str] = None
    rejection_reason: Optional[str] = None
    received_at: datetime
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InboundCallListResponseSchema(BaseModel):
    inbound_calls: List[InboundCallResponseSchema]
    total: int
    page: int
    per_page: int
    total_pages: int

class InboundCallFiltersSchema(BaseModel):
    call_status: Optional[str] = None
    caller_phone_number: Optional[str] = None
    agent_id: Optional[int] = None
    lead_id: Optional[int] = None
    page: int = 1
    per_page: int = 20

# Webhook schemas for external services
class TwilioWebhookSchema(BaseModel):
    """Schema for Twilio webhook payloads"""
    CallSid: str
    From: str
    To: str
    CallStatus: str
    Direction: Optional[str] = None
    ApiVersion: Optional[str] = None
    CallerName: Optional[str] = None
    CallerCity: Optional[str] = None
    CallerState: Optional[str] = None
    CallerZip: Optional[str] = None
    CallerCountry: Optional[str] = None

class LiveKitWebhookSchema(BaseModel):
    """Schema for LiveKit webhook payloads"""
    event: str
    room: Optional[Dict[str, Any]] = None
    participant: Optional[Dict[str, Any]] = None
    track: Optional[Dict[str, Any]] = None
    egress_info: Optional[Dict[str, Any]] = None