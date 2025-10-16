"""
Agents API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List, Dict, Any
import math
import time
import random
import logging
from datetime import datetime
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

from models.database import get_db
from models.agent import Agent
from models.schemas import (
    AgentCreateSchema,
    AgentUpdateSchema,
    AgentResponseSchema,
    AgentListResponseSchema,
    AgentTestSchema,
    AgentTestResponseSchema
)
from services.openai_service import get_openai_service

# Additional Pydantic models for OpenAI endpoints
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    model: Optional[str] = "gpt-3.5-turbo"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    usage: Optional[Dict[str, int]] = None
    success: bool
    error: Optional[str] = None

class PromptGenerationRequest(BaseModel):
    summary: str
    agent_type: Optional[str] = "customer_service"
    industry: Optional[str] = "general"
    model: Optional[str] = "gpt-3.5-turbo"

class ScenarioPromptRequest(BaseModel):
    scenario_description: str
    business_context: Optional[Dict[str, Any]] = None
    model: Optional[str] = "gpt-3.5-turbo"

class PromptGenerationResponse(BaseModel):
    generated_prompt: Optional[str] = None
    success: bool
    error: Optional[str] = None
    usage: Optional[Dict[str, int]] = None

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.get("/", response_model=AgentListResponseSchema)
async def get_agents(
    type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all agents with filtering and pagination"""

    # Build query
    query = db.query(Agent)

    # Apply filters
    if type:
        query = query.filter(Agent.type == type)
    if is_active is not None:
        query = query.filter(Agent.is_active == is_active)
    if search:
        query = query.filter(
            or_(
                Agent.name.ilike(f"%{search}%"),
                Agent.description.ilike(f"%{search}%"),
                Agent.type.ilike(f"%{search}%")
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    agents = query.order_by(Agent.created_at.desc()).offset(offset).limit(per_page).all()

    # Calculate total pages
    total_pages = math.ceil(total / per_page)

    return AgentListResponseSchema(
        agents=[AgentResponseSchema.model_validate(agent) for agent in agents],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/{agent_id}", response_model=AgentResponseSchema)
async def get_agent(agent_id: int, db: Session = Depends(get_db)):
    """Get a specific agent by ID"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponseSchema.model_validate(agent)

@router.post("/", response_model=AgentResponseSchema)
async def create_agent(agent_data: AgentCreateSchema, db: Session = Depends(get_db)):
    """Create a new agent"""

    # Check if agent name already exists
    existing_agent = db.query(Agent).filter(Agent.name == agent_data.name).first()
    if existing_agent:
        raise HTTPException(status_code=400, detail="Agent with this name already exists")

    # Create new agent
    agent = Agent(
        name=agent_data.name,
        description=agent_data.description,
        type=agent_data.type,
        use_case=agent_data.use_case,

        # Prompt configuration
        prompt_template=agent_data.prompt_template,
        prompt_template_name=agent_data.prompt_template_name,
        prompt_variables=agent_data.prompt_variables or {},

        # Personality configuration
        personality_traits=agent_data.personality_traits or [],
        personality_style=agent_data.personality_style,
        response_length=agent_data.response_length,
        custom_personality_instructions=agent_data.custom_personality_instructions,

        # AI Model configuration
        model=agent_data.model,
        temperature=agent_data.temperature,
        max_tokens=agent_data.max_tokens,

        # Knowledge Base
        knowledge=agent_data.knowledge or [],

        # Tools and Actions
        enabled_tools=agent_data.enabled_tools or [],
        tool_configs=agent_data.tool_configs or {},

        # Conversation Settings
        conversation_settings=agent_data.conversation_settings or {},

        # Workflow configuration
        triggers=agent_data.triggers or [],
        actions=agent_data.actions or [],
        workflow_steps=agent_data.workflow_steps or [],
        integrations=agent_data.integrations or [],
        sample_conversations=agent_data.sample_conversations or [],

        # Status and metadata
        is_active=agent_data.is_active,
        is_public=agent_data.is_public,
        created_by=agent_data.created_by
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return AgentResponseSchema.model_validate(agent)

@router.put("/{agent_id}", response_model=AgentResponseSchema)
async def update_agent(agent_id: int, agent_data: AgentUpdateSchema, db: Session = Depends(get_db)):
    """Update an existing agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Update only provided fields
    update_data = agent_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    db.commit()
    db.refresh(agent)

    return AgentResponseSchema.model_validate(agent)

@router.delete("/{agent_id}")
async def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    """Delete an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db.delete(agent)
    db.commit()

    return {"message": "Agent deleted successfully"}

@router.post("/{agent_id}/test", response_model=AgentTestResponseSchema)
async def test_agent(agent_id: int, test_data: AgentTestSchema, db: Session = Depends(get_db)):
    """Test an agent with a message"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Simulate AI processing time
    start_time = time.time()
    processing_time = random.uniform(0.5, 2.0)  # Simulate processing
    time.sleep(min(processing_time, 1.0))  # Limit actual wait time

    # Generate mock response based on agent configuration
    response_templates = {
        "conversational": [
            f"Thank you for reaching out! Based on your inquiry about '{test_data.message}', I'd be happy to help you explore our services.",
            f"I understand you're interested in '{test_data.message}'. Let me connect you with the right information.",
            f"Great question about '{test_data.message}'! I can help you with that."
        ],
        "lead_qualifier": [
            f"Thank you for your interest! To better understand your needs regarding '{test_data.message}', could you tell me more about your current situation?",
            f"I'd love to help you with '{test_data.message}'. What's your timeline for this project?",
            f"Based on '{test_data.message}', I can see this could be a great fit. What's your budget range?"
        ],
        "follow_up": [
            f"Following up on our previous conversation about '{test_data.message}' - do you have any additional questions?",
            f"I wanted to check in regarding '{test_data.message}'. Are you ready to move forward?",
            f"Hope you've had time to consider our discussion about '{test_data.message}'. What are your thoughts?"
        ]
    }

    # Adjust response based on personality
    personality_modifiers = {
        "professional": "",
        "friendly": " 😊",
        "casual": " Hope this helps!",
        "enthusiastic": " I'm excited to work with you!"
    }

    base_responses = response_templates.get(agent.type, response_templates["conversational"])
    response = random.choice(base_responses)

    personality_modifier = personality_modifiers.get(agent.personality_style, "")
    response += personality_modifier

    processing_time_actual = time.time() - start_time

    # Update agent statistics
    agent.total_interactions += 1
    agent.last_used_at = datetime.utcnow()

    # Update average response time (simple moving average)
    if agent.avg_response_time and agent.avg_response_time != "0.0":
        current_avg = float(agent.avg_response_time)
        new_avg = (current_avg + processing_time_actual) / 2
        agent.avg_response_time = f"{new_avg:.2f}"
    else:
        agent.avg_response_time = f"{processing_time_actual:.2f}"

    db.commit()

    return AgentTestResponseSchema(
        response=response,
        processing_time=processing_time_actual,
        success=True,
        error=None
    )

@router.get("/{agent_id}/stats")
async def get_agent_stats(agent_id: int, db: Session = Depends(get_db)):
    """Get agent performance statistics"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "agent_id": agent.id,
        "name": agent.name,
        "total_interactions": agent.total_interactions,
        "success_rate": agent.success_rate,
        "avg_response_time": agent.avg_response_time,
        "last_used_at": agent.last_used_at,
        "created_at": agent.created_at,
        "is_active": agent.is_active
    }

# Agent type statistics
@router.get("/stats/by-type")
async def get_agents_by_type(db: Session = Depends(get_db)):
    """Get agent count by type"""
    from sqlalchemy import func

    results = db.query(
        Agent.type,
        func.count(Agent.id).label("count")
    ).filter(Agent.is_active == True).group_by(Agent.type).all()

    return [{"type": result.type, "count": result.count} for result in results]

@router.get("/stats/overview")
async def get_agent_overview(db: Session = Depends(get_db)):
    """Get agent statistics overview"""
    from sqlalchemy import func

    total_agents = db.query(Agent).count()
    active_agents = db.query(Agent).filter(Agent.is_active == True).count()
    public_agents = db.query(Agent).filter(Agent.is_public == True).count()

    # Total interactions across all agents
    total_interactions = db.query(func.sum(Agent.total_interactions)).scalar() or 0

    return {
        "total_agents": total_agents,
        "active_agents": active_agents,
        "public_agents": public_agents,
        "total_interactions": total_interactions
    }

# OpenAI-powered endpoints

@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(
    agent_id: int,
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Chat with an agent using OpenAI with the agent's specific prompt"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check if OpenAI is available
    if not get_openai_service().is_available():
        # Fallback to the existing mock response system
        return await _fallback_chat_response(agent, chat_request.message)

    try:
        # Use the agent's prompt as system prompt
        system_prompt = agent.prompt_template or "You are a helpful AI assistant."

        # Convert chat history to OpenAI format
        messages = []
        for msg in chat_request.conversation_history:
            messages.append({"role": msg.role, "content": msg.content})

        # Add the current message
        messages.append({"role": "user", "content": chat_request.message})

        # Get response from OpenAI
        result = await get_openai_service().chat_completion(
            messages=messages,
            model=chat_request.model,
            temperature=chat_request.temperature,
            max_tokens=chat_request.max_tokens,
            system_prompt=system_prompt
        )

        # Update agent statistics
        agent.total_interactions += 1
        agent.last_used_at = datetime.utcnow()
        db.commit()

        return ChatResponse(
            response=result["response"],
            usage=result.get("usage"),
            success=result["success"],
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        # Fallback to mock response on error
        return await _fallback_chat_response(agent, chat_request.message)

async def _fallback_chat_response(agent, message: str) -> ChatResponse:
    """Fallback chat response when OpenAI is unavailable"""
    # Use the existing mock logic from the original test_agent endpoint
    response_templates = {
        "conversational": [
            f"Thank you for reaching out! Based on your message about '{message}', I'd be happy to help you explore our services.",
            f"I understand you're asking about '{message}'. Let me connect you with the right information.",
            f"Great question about '{message}'! I can help you with that."
        ],
        "lead_qualifier": [
            f"Thank you for your interest! To better understand your needs regarding '{message}', could you tell me more about your current situation?",
            f"I'd love to help you with '{message}'. What's your timeline for this project?",
            f"Based on '{message}', I can see this could be a great fit. What's your budget range?"
        ],
        "follow_up": [
            f"Following up on our previous conversation about '{message}' - do you have any additional questions?",
            f"I wanted to check in regarding '{message}'. Are you ready to move forward?",
            f"Hope you've had time to consider our discussion about '{message}'. What are your thoughts?"
        ]
    }

    base_responses = response_templates.get(agent.type, response_templates["conversational"])
    response = random.choice(base_responses)

    return ChatResponse(
        response=response,
        usage=None,
        success=True,
        error=None
    )

@router.post("/generate-prompt", response_model=PromptGenerationResponse)
async def generate_prompt_from_summary(request: PromptGenerationRequest):
    """Generate a detailed agent prompt from a brief summary"""
    if not get_openai_service().is_available():
        return PromptGenerationResponse(
            generated_prompt=None,
            success=False,
            error="OpenAI service is not available. Please configure your API key."
        )

    try:
        result = await get_openai_service().generate_prompt_from_summary(
            summary=request.summary,
            agent_type=request.agent_type,
            industry=request.industry,
            model=request.model
        )

        return PromptGenerationResponse(
            generated_prompt=result.get("generated_prompt"),
            success=result["success"],
            error=result.get("error"),
            usage=result.get("usage")
        )

    except Exception as e:
        return PromptGenerationResponse(
            generated_prompt=None,
            success=False,
            error=str(e)
        )

@router.post("/generate-scenario-prompt")
async def generate_scenario_prompt(request: ScenarioPromptRequest):
    """Generate a complete agent setup from a basic scenario description"""
    if not get_openai_service().is_available():
        return {
            "success": False,
            "error": "OpenAI service is not available. Please configure your API key.",
            "generated_data": None
        }

    try:
        result = await get_openai_service().generate_scenario_prompt(
            scenario_description=request.scenario_description,
            business_context=request.business_context,
            model=request.model
        )

        return {
            "success": result["success"],
            "error": result.get("error"),
            "generated_data": result.get("generated_data"),
            "scenario_description": request.scenario_description,
            "usage": result.get("usage")
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "generated_data": None
        }

@router.post("/{agent_id}/analyze-tools")
async def analyze_agent_tools(agent_id: int, db: Session = Depends(get_db)):
    """Analyze an agent's prompt and suggest which tools should be configured"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if not get_openai_service().is_available():
        return {
            "suggested_tools": ["/appointment", "/transfer", "/bailout", "/knowledge"],
            "tool_priorities": {"high": [], "medium": [], "low": []},
            "success": False,
            "error": "OpenAI service not available"
        }

    try:
        prompt = agent.prompt_template or "Generic customer service agent"
        result = await get_openai_service().analyze_tools_needed(prompt)
        return result

    except Exception as e:
        return {
            "suggested_tools": ["/appointment", "/transfer", "/bailout", "/knowledge"],
            "tool_priorities": {"high": [], "medium": [], "low": []},
            "success": False,
            "error": str(e)
        }

@router.get("/openai/status")
async def get_openai_status():
    """Check OpenAI service availability"""
    return {
        "available": get_openai_service().is_available(),
        "message": "OpenAI service is ready" if get_openai_service().is_available() else "OpenAI API key not configured"
    }