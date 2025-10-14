#!/usr/bin/env python3
"""
Create Demo Text Messaging Agent for Auto-Messaging Testing
"""

import os
import sys
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal
from models.agent import Agent

def create_demo_text_agent():
    """Create a demo text messaging agent for auto-messaging testing"""

    db = SessionLocal()

    try:
        # Check if demo text agent already exists
        existing_agent = db.query(Agent).filter(
            Agent.name == "Torkin Demo Text Agent",
            Agent.type == "inbound"
        ).first()

        if existing_agent:
            print(f"✅ Demo text agent already exists (ID: {existing_agent.id})")
            return existing_agent.id

        # Create demo text messaging agent
        demo_agent = Agent(
            name="Torkin Demo Text Agent",
            description="Demo agent for testing auto-messaging and text conversations",
            type="inbound",
            use_case="lead_qualification",

            # Text-focused prompt template using the new simplified format
            prompt_template="""You are a professional lead qualification specialist for {{business_name}}. Your name is {{agent_name}} and you help homeowners connect with the right home services.

## Core Objective
Qualify leads by understanding their project needs, timeline, and decision-making authority. Build rapport while gathering key information for follow-up.

## Key Responsibilities
- Ask targeted questions to understand their home service needs
- Assess project scope, timeline, and budget considerations
- Determine decision-making authority and urgency
- Schedule consultations for qualified leads
- Provide helpful information about our services

## Communication Style
- Professional yet friendly and approachable
- Concise responses (under 200 words)
- Natural conversation flow without repetitive phrases
- Focus on their needs, not our services initially

## Lead Information Available
- Name: {{first_name}} {{last_name}}
- Service Needed: {{service_requested}}
- Contact: {{email}}, {{phone}}
- Source: {{source}}

## First Message Structure
1. Warm greeting using their first name
2. Acknowledge their service request
3. Ask 1-2 key qualifying questions
4. Sign with your name

Example: "Hi {{first_name}}! Thanks for reaching out about {{service_requested}}. I'd love to help you with your project. What's driving your decision to move forward with this now? And what's your ideal timeline?

{{agent_name}}"

## Qualifying Questions Focus
- **Timeline**: "What's your ideal timeline for this project?"
- **Budget**: "Do you have a budget range in mind?"
- **Decision Making**: "Are you the primary decision maker for this project?"
- **Urgency**: "Is this something urgent or are you planning ahead?"
- **Scope**: "Can you tell me more about what you have in mind?"

## When to Schedule
If they show clear interest, have a reasonable timeline (within 6 months), and decision-making authority, offer to schedule a free consultation.

## Boundaries
- Only discuss services we actually provide
- Don't make pricing commitments beyond general ranges
- If the request is outside our capabilities, politely refer them elsewhere
- Keep conversations focused on their home service needs""",
            prompt_template_name="torkin_text_demo",

            # Text/messaging specific settings
            conversation_settings={
                "communicationMode": "text",
                "textSettings": {
                    "autoTrigger": True,
                    "maxResponseLength": 200,
                    "conversationTimeout": 1800  # 30 minutes
                }
            },

            # Demo personality for text interactions
            personality_traits=["Professional", "Consultative", "Trustworthy", "Detail-oriented"],
            personality_style="professional",
            response_length="detailed",

            # AI configuration optimized for text conversations
            model="gpt-3.5-turbo",
            temperature="0.3",
            max_tokens=600,

            # Auto-trigger settings for lead creation (matches WorkflowService expectations)
            triggers=[
                {
                    "event": "new_lead",
                    "condition": {
                        "source": "torkin website"
                    },
                    "active": True
                }
            ],

            # Tool configurations for business context
            tool_configs={
                "business_context": {
                    "name": "Torkin Pest Control",
                    "services": ["Pest Control", "Termite Inspection", "Rodent Control", "Preventive Treatment"],
                    "service_area": "New Jersey Area",
                    "emergency_availability": False
                }
            },

            # Mark as active and demo
            is_active=True,
            is_public=False,
            created_by="demo_setup"
        )

        db.add(demo_agent)
        db.commit()
        db.refresh(demo_agent)

        print(f"✅ Created demo text agent (ID: {demo_agent.id})")
        return demo_agent.id

    except Exception as e:
        print(f"❌ Error creating demo text agent: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating demo text messaging agent...")
    agent_id = create_demo_text_agent()
    if agent_id:
        print(f"🎉 Demo text agent setup complete! Agent ID: {agent_id}")
        print("This agent will:")
        print("  ✅ Auto-trigger on lead creation from 'torkin website'")
        print("  ✅ Send initial qualifying message within 30 seconds")
        print("  ✅ Handle 2-3 back-and-forth text conversations")
        print("  ✅ Use professional Torkin branding and context")
    else:
        print("💥 Demo text agent setup failed!")