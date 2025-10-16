#!/usr/bin/env python3
"""
Test script for inbound calling setup - Phase 1 Local Testing
This script validates the database setup and creates test data
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import create_tables, SessionLocal
from models.agent import Agent
from models.lead import Lead
from models.inbound_call import InboundCall
from services.inbound_call_service import InboundCallService

def test_database_migration():
    """Test that all tables can be created successfully"""
    print("🔧 Testing database migration...")
    try:
        create_tables()
        print("✅ Database migration successful - all tables created")
        return True
    except Exception as e:
        print(f"❌ Database migration failed: {str(e)}")
        return False

def create_test_inbound_agent():
    """Create a test inbound agent for testing"""
    print("🤖 Creating test inbound agent...")
    db = SessionLocal()
    try:
        # Check if inbound agent already exists
        existing_agent = db.query(Agent).filter(Agent.type == "inbound").first()
        if existing_agent:
            print(f"✅ Inbound agent already exists: {existing_agent.name} (ID: {existing_agent.id})")
            return existing_agent.id

        # Create new inbound agent
        inbound_agent = Agent(
            name="Test Inbound Agent",
            description="Test agent for handling inbound calls",
            type="inbound",
            use_case="phone_support",
            prompt_template="""
You are a friendly customer service representative for AILead Services.
You handle inbound calls from potential customers who are calling our phone number.

Your goals:
1. Greet the caller warmly
2. Ask how you can help them today
3. Gather their contact information if they're interested in our services
4. Provide helpful information about our lead management and automation services
5. Schedule a follow-up if appropriate

Be professional, helpful, and concise since this is a phone conversation.
            """.strip(),
            prompt_template_name="inbound_customer_service",
            personality_traits=["Professional", "Helpful", "Friendly"],
            personality_style="professional",
            response_length="brief",
            model="gpt-3.5-turbo",
            temperature="0.7",
            max_tokens=200,
            is_active=True,
            conversation_settings={
                "communicationMode": "voice",
                "enableTranscription": True,
                "enableSummary": True
            },
            created_by="test_script"
        )

        db.add(inbound_agent)
        db.commit()
        db.refresh(inbound_agent)

        print(f"✅ Created test inbound agent: {inbound_agent.name} (ID: {inbound_agent.id})")
        return inbound_agent.id

    except Exception as e:
        print(f"❌ Failed to create test inbound agent: {str(e)}")
        return None
    finally:
        db.close()

def test_inbound_call_service():
    """Test the InboundCallService functionality"""
    print("📞 Testing InboundCallService...")
    db = SessionLocal()
    try:
        service = InboundCallService(db)

        # Test agent validation
        can_handle, agent, reason = service.can_handle_inbound_call()
        if can_handle:
            print(f"✅ Can handle inbound calls - Agent: {agent.name}")
        else:
            print(f"❌ Cannot handle inbound calls: {reason}")
            return False

        # Test phone number validation
        test_phone = "+15551234567"
        validated = service.validate_phone_number(test_phone)
        if validated:
            print(f"✅ Phone validation works: {test_phone} -> {validated}")
        else:
            print(f"❌ Phone validation failed for: {test_phone}")

        return True

    except Exception as e:
        print(f"❌ InboundCallService test failed: {str(e)}")
        return False
    finally:
        db.close()

async def test_lead_creation():
    """Test automatic lead creation from phone number"""
    print("👤 Testing automatic lead creation...")
    db = SessionLocal()
    try:
        service = InboundCallService(db)

        test_phone = "+15551234567"
        lead = await service.find_or_create_lead(test_phone)

        if lead:
            print(f"✅ Lead creation successful: {lead.name} (ID: {lead.id}, Phone: {lead.phone})")
            return lead.id
        else:
            print("❌ Lead creation failed")
            return None

    except Exception as e:
        print(f"❌ Lead creation test failed: {str(e)}")
        return None
    finally:
        db.close()

def test_inbound_call_creation():
    """Test creating an inbound call record"""
    print("📋 Testing inbound call record creation...")
    db = SessionLocal()
    try:
        # Create a test inbound call
        test_call = InboundCall(
            caller_phone_number="+15551234567",
            inbound_phone_number="+17622437375",
            call_status="received",
            call_metadata={
                "test": True,
                "created_by": "test_script",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        db.add(test_call)
        db.commit()
        db.refresh(test_call)

        print(f"✅ Inbound call record created: ID {test_call.id}")

        # Clean up test record
        db.delete(test_call)
        db.commit()
        print("✅ Test record cleaned up")

        return True

    except Exception as e:
        print(f"❌ Inbound call creation test failed: {str(e)}")
        return False
    finally:
        db.close()

def check_environment():
    """Check required environment variables"""
    print("🔍 Checking environment configuration...")

    required_vars = [
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET"
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   LiveKit integration may not work without these")
    else:
        print("✅ All required environment variables are set")

    # Show current LiveKit config
    livekit_url = os.getenv("LIVEKIT_URL", "Not set")
    print(f"   LiveKit URL: {livekit_url}")

async def main():
    """Main test function"""
    print("🚀 Starting Inbound Calling Setup Tests")
    print("=" * 50)

    # Test 1: Environment check
    check_environment()
    print()

    # Test 2: Database migration
    if not test_database_migration():
        print("❌ Database migration failed - stopping tests")
        return
    print()

    # Test 3: Create test agent
    agent_id = create_test_inbound_agent()
    if not agent_id:
        print("❌ Failed to create test agent - stopping tests")
        return
    print()

    # Test 4: Service functionality
    if not test_inbound_call_service():
        print("❌ Service tests failed")
        return
    print()

    # Test 5: Lead creation
    lead_id = await test_lead_creation()
    if not lead_id:
        print("❌ Lead creation failed")
        return
    print()

    # Test 6: Inbound call record
    if not test_inbound_call_creation():
        print("❌ Inbound call creation failed")
        return
    print()

    print("🎉 All Phase 1 tests passed!")
    print("=" * 50)
    print("Next steps:")
    print("1. Start the backend server: cd backend && python main.py")
    print("2. Test API endpoints with curl or Postman")
    print("3. Run the LiveKit agent: cd backend/agent && python -m livekit.agents.cli start src.agent --dev")

if __name__ == "__main__":
    asyncio.run(main())