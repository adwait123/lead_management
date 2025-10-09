#!/usr/bin/env python3
"""
Setup script to create test agents in staging database
Creates agents with proper triggers for Phase 3 testing
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import DATABASE_URL
from models.agent import Agent

def create_test_agents():
    """Create test agents for Phase 3 functionality"""

    # Create database engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Agent 1: Lead Qualification Agent
        lead_qualification_agent = Agent(
            name="Sarah - Lead Qualification Agent",
            use_case="lead_qualification",
            type="conversational",
            prompt_template="""You are Sarah, a friendly and professional lead qualification specialist for a home renovation company.

Your primary goals are to:
1. Warmly welcome new leads and thank them for their interest
2. Understand their specific renovation project needs
3. Gather important project details (timeline, budget, requirements)
4. Build rapport and trust
5. Schedule a consultation when appropriate

Be conversational, helpful, and show genuine interest in their project. Ask relevant follow-up questions to better understand their needs. Always maintain a professional yet friendly tone.""",
            triggers=[
                {
                    "event_type": "new_lead",
                    "active": True
                }
            ],
            is_active=True
        )

        # Agent 2: General Sales Agent (backup)
        general_sales_agent = Agent(
            name="Alex - General Sales Agent",
            use_case="general_sales",
            type="conversational",
            prompt_template="""You are Alex, a knowledgeable sales representative for a home renovation company.

Your goals are to:
1. Engage with potential customers professionally
2. Understand their renovation needs and budget
3. Provide helpful information about services
4. Guide them towards booking a consultation
5. Close leads when possible

Be professional, knowledgeable, and solution-focused. Help customers understand how your services can meet their renovation goals.""",
            triggers=[
                {
                    "event_type": "new_lead",
                    "active": True
                },
                {
                    "event_type": "form_submission",
                    "active": True
                }
            ],
            is_active=True
        )

        # Check if agents already exist
        existing_agents = db.query(Agent).filter(
            Agent.name.in_([
                "Sarah - Lead Qualification Agent",
                "Alex - General Sales Agent"
            ])
        ).all()

        if existing_agents:
            print(f"Found {len(existing_agents)} existing agents. Updating...")
            for agent in existing_agents:
                if "Sarah" in agent.name:
                    agent.prompt_template = lead_qualification_agent.prompt_template
                    agent.triggers = lead_qualification_agent.triggers
                    agent.is_active = True
                elif "Alex" in agent.name:
                    agent.prompt_template = general_sales_agent.prompt_template
                    agent.triggers = general_sales_agent.triggers
                    agent.is_active = True
        else:
            print("Creating new test agents...")
            db.add(lead_qualification_agent)
            db.add(general_sales_agent)

        db.commit()

        # Verify agents were created
        all_agents = db.query(Agent).filter(Agent.is_active == True).all()
        print(f"\n✅ Success! {len(all_agents)} active agents in database:")

        for agent in all_agents:
            print(f"\n📋 Agent: {agent.name}")
            print(f"   Use Case: {agent.use_case}")
            print(f"   Triggers: {len(agent.triggers) if agent.triggers else 0}")
            if agent.triggers:
                for trigger in agent.triggers:
                    if isinstance(trigger, dict):
                        event_type = trigger.get('event_type') or trigger.get('event') or trigger.get('type')
                        print(f"     - {event_type}")

        print(f"\n🎉 Staging database is ready for Phase 3 testing!")
        return True

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating agents: {e}")
        return False

    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("STAGING AGENTS SETUP SCRIPT")
    print("=" * 60)
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Local'}")
    print()

    success = create_test_agents()

    if success:
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("- Test webhook lead creation")
        print("- Verify agent sessions are created")
        print("- Test two-way messaging flow")
    else:
        print("\n❌ Setup failed!")
        print("Check the error messages above and try again.")