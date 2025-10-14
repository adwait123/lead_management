#!/usr/bin/env python3
"""
Create Demo Outbound Calling Agent for Testing
"""

import os
import sys
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal
from models.agent import Agent

def create_demo_outbound_agent():
    """Create a demo outbound calling agent for testing"""

    db = SessionLocal()

    try:
        # Check if demo agent already exists
        existing_agent = db.query(Agent).filter(
            Agent.name == "Torkin Demo Outbound Agent",
            Agent.type == "outbound"
        ).first()

        if existing_agent:
            print(f"✅ Demo outbound agent already exists (ID: {existing_agent.id})")
            return existing_agent.id

        # Create demo outbound calling agent
        demo_agent = Agent(
            name="Torkin Demo Outbound Agent",
            description="Demo agent for testing outbound calling functionality",
            type="outbound",
            use_case="outbound_campaigns",

            # Hardcoded prompt for demo
            prompt_template="""
            You are Sarah, the Torkin Home Services Assistant. You call customers who submitted requests on the website to schedule Free In-Home Design Consultations.

            Be professional, friendly, and focused on booking appointments. Always confirm details and repeat back what you hear.
            """,
            prompt_template_name="torkin_outbound_demo",

            # Voice/calling specific settings
            conversation_settings={
                "communicationMode": "voice",
                "voiceSettings": {
                    "voice": "sonic-2",
                    "speed": 1.1,
                    "model": "cartesia"
                }
            },

            # Demo personality
            personality_traits=["Professional", "Friendly", "Efficient"],
            personality_style="professional",
            response_length="moderate",

            # AI configuration
            model="gpt-4",
            temperature="0.3",
            max_tokens=150,

            # Workflow settings (matches WorkflowService expectations)
            triggers=[
                {
                    "event": "new_lead",
                    "condition": {
                        "source": "torkin"
                    },
                    "active": True
                }
            ],

            # Mark as active and demo
            is_active=True,
            is_public=False,
            created_by="demo_setup"
        )

        db.add(demo_agent)
        db.commit()
        db.refresh(demo_agent)

        print(f"✅ Created demo outbound agent (ID: {demo_agent.id})")
        return demo_agent.id

    except Exception as e:
        print(f"❌ Error creating demo agent: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating demo outbound calling agent...")
    agent_id = create_demo_outbound_agent()
    if agent_id:
        print(f"🎉 Demo setup complete! Agent ID: {agent_id}")
    else:
        print("💥 Demo setup failed!")