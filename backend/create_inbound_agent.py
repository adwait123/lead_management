#!/usr/bin/env python3
"""
Create an inbound agent for testing if none exists
"""

import os
import sys
from sqlalchemy.orm import Session
from models.database import SessionLocal, create_tables
from models.agent import Agent

def create_inbound_agent():
    """Create an inbound agent for testing"""

    # Create tables if they don't exist
    create_tables()

    db = SessionLocal()

    try:
        # Check if inbound agent already exists
        existing_agent = db.query(Agent).filter(
            Agent.type == "inbound",
            Agent.is_active == True
        ).first()

        if existing_agent:
            print(f"✅ Active inbound agent already exists: {existing_agent.name} (ID: {existing_agent.id})")
            return existing_agent.id

        # Create new inbound agent
        inbound_agent = Agent(
            name="Inbound Call Agent",
            type="inbound",
            is_active=True,
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=500,
            prompt_template="""You are a friendly and professional customer service representative for AILead Services.

Your role is to:
1. Greet callers warmly and identify their needs
2. Gather basic information about their inquiry
3. Provide helpful information about our services
4. Schedule appointments or escalate to specialists when needed
5. Ensure customer satisfaction

Be conversational, empathetic, and solution-focused. Keep responses concise but thorough.

Customer Context:
- Name: {customer_name}
- Phone: {customer_phone}
- Previous interactions: {interaction_history}

Current call information:
- Caller phone: {caller_phone}
- Inbound number: {inbound_phone}
""",
            prompt_variables={
                "customer_name": "string",
                "customer_phone": "string",
                "interaction_history": "string",
                "caller_phone": "string",
                "inbound_phone": "string"
            },
            personality_traits=["helpful", "professional", "empathetic"],
            personality_style="professional",
            response_length="moderate",
            conversation_settings={
                "greeting_message": "Hello! Thank you for calling AILead Services. How can I help you today?",
                "escalation_triggers": ["technical_support", "billing_issue", "complaint"],
                "max_conversation_length": 20,
                "auto_summarize": True
            },
            custom_personality_instructions="Always maintain a warm, professional tone. Listen actively and ask clarifying questions to understand the caller's needs."
        )

        db.add(inbound_agent)
        db.commit()
        db.refresh(inbound_agent)

        print(f"✅ Created new inbound agent: {inbound_agent.name} (ID: {inbound_agent.id})")
        return inbound_agent.id

    except Exception as e:
        print(f"❌ Error creating inbound agent: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()

def main():
    """Main function"""
    print("🤖 Creating inbound agent for testing...")

    agent_id = create_inbound_agent()

    if agent_id:
        print(f"🎉 Inbound agent ready! Agent ID: {agent_id}")
        print("📞 You can now test inbound calling functionality")
    else:
        print("❌ Failed to create inbound agent")
        sys.exit(1)

if __name__ == "__main__":
    main()