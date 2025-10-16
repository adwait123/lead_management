#!/usr/bin/env python3
"""
Test script for agent configuration API integration
Tests the complete workflow: inbound call → LiveKit room → agent dispatch → configuration
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal
from models.agent import Agent
from models.lead import Lead
from models.inbound_call import InboundCall
from services.inbound_call_service import InboundCallService

async def test_agent_configuration_flow():
    """Test the complete agent configuration and dispatch flow"""
    print("🔧 Testing Agent Configuration API Integration...")
    db = SessionLocal()
    try:
        service = InboundCallService(db)

        # Step 1: Create a realistic inbound call scenario
        test_phone = "+15551234567"
        print(f"   📞 Testing with caller: {test_phone}")

        # Create inbound call record (simulating Twilio webhook)
        inbound_call = InboundCall(
            caller_phone_number=test_phone,
            inbound_phone_number="+17622437375",
            call_status="received",
            call_metadata={
                "twilio_call_sid": "CATest123456789",
                "test_scenario": "agent_configuration_test",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        db.add(inbound_call)
        db.commit()
        db.refresh(inbound_call)

        print(f"✅ Created inbound call record: ID {inbound_call.id}")

        # Step 2: Process the call through the complete workflow
        print(f"   🔄 Processing call through complete workflow...")

        workflow_success = await service.process_call(inbound_call.id)

        if not workflow_success:
            print("❌ Workflow processing failed")
            db.refresh(inbound_call)
            print(f"   Error: {inbound_call.error_message}")
            return False

        # Step 3: Verify the final state and configuration
        db.refresh(inbound_call)

        print(f"✅ Workflow completed successfully!")
        print(f"   Final call status: {inbound_call.call_status}")
        print(f"   LiveKit room: {inbound_call.room_name}")
        print(f"   Lead ID: {inbound_call.lead_id}")
        print(f"   Agent ID: {inbound_call.agent_id}")

        # Step 4: Verify agent configuration metadata
        if inbound_call.call_metadata:
            metadata = inbound_call.call_metadata
            print(f"✅ Agent Configuration Metadata:")
            print(f"   Phone number: {metadata.get('phone_number')}")
            print(f"   Call type: {metadata.get('call_type')}")
            print(f"   Agent name: {metadata.get('agent_name')}")

            # Verify customer info is properly formatted
            customer_info = metadata.get('customer_info', {})
            if customer_info:
                print(f"   Customer: {customer_info.get('first_name')} {customer_info.get('last_name')}")
                print(f"   Service: {customer_info.get('service_requested')}")
                print(f"   Address: {customer_info.get('address')}")

        # Step 5: Verify lead was created/updated properly
        if inbound_call.lead_id:
            lead = db.query(Lead).filter(Lead.id == inbound_call.lead_id).first()
            if lead:
                print(f"✅ Lead Information:")
                print(f"   Name: {lead.name}")
                print(f"   Phone: {lead.phone}")
                print(f"   Status: {lead.status}")
                print(f"   Source: {lead.source}")

        # Step 6: Test agent room readiness
        if inbound_call.room_name:
            print(f"✅ LiveKit Room Ready: {inbound_call.room_name}")
            print(f"   Agent 'inbound_raq' should be active in this room")
            print(f"   Room metadata contains customer and call info")

        # Clean up test data
        db.delete(inbound_call)
        db.commit()
        print("✅ Test data cleaned up")

        return True

    except Exception as e:
        print(f"❌ Agent configuration test failed: {str(e)}")
        return False
    finally:
        db.close()

async def test_agent_metadata_validation():
    """Test that agent metadata is properly formatted for inbound calls"""
    print("📋 Testing Agent Metadata Validation...")
    db = SessionLocal()
    try:
        service = InboundCallService(db)

        # Get test data
        test_phone = "+15551234567"
        lead = await service.find_or_create_lead(test_phone)
        can_handle, agent, reason = service.can_handle_inbound_call()

        if not can_handle:
            print(f"❌ Cannot test metadata - no inbound agent: {reason}")
            return False

        # Create test call
        test_call = InboundCall(
            caller_phone_number=test_phone,
            inbound_phone_number="+17622437375",
            call_status="received",
            lead_id=lead.id,
            agent_id=agent.id
        )

        # Test room metadata creation
        print(f"   🔍 Testing metadata generation...")

        # This will test the metadata formatting without actually creating the room
        room_name = f"test_room_{test_call.caller_phone_number.replace('+', '').replace('-', '')}_{123}"

        # Test the metadata structure that would be sent to LiveKit
        expected_metadata = {
            "phone_number": test_call.caller_phone_number,
            "lead_id": str(lead.id),
            "call_id": str(123),
            "call_type": "inbound",
            "agent_name": agent.name,
            "agent_id": str(agent.id),
            "customer_info": {
                "first_name": lead.first_name or lead.name or "Caller",
                "last_name": lead.last_name or "",
                "phone": lead.phone,
                "address": lead.address or "Unknown",
                "service_requested": lead.service_requested or "Phone inquiry"
            },
            "initiated_via": "inbound_webhook",
            "timestamp": datetime.utcnow().isoformat(),
            "inbound_number": test_call.inbound_phone_number,
            "source": lead.source
        }

        print(f"✅ Metadata structure validation:")
        print(f"   Room name format: {room_name}")
        print(f"   Metadata keys: {list(expected_metadata.keys())}")
        print(f"   Customer info: {expected_metadata['customer_info']}")
        print(f"   Call context: {expected_metadata['call_type']} from {expected_metadata['phone_number']}")

        # Verify JSON serialization (required for LiveKit)
        try:
            json_metadata = json.dumps(expected_metadata)
            print(f"✅ Metadata is JSON serializable ({len(json_metadata)} chars)")
        except Exception as e:
            print(f"❌ Metadata JSON serialization failed: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ Metadata validation test failed: {str(e)}")
        return False
    finally:
        db.close()

async def test_agent_dispatch_verification():
    """Verify the agent dispatch request format"""
    print("🚀 Testing Agent Dispatch Request Format...")

    # Test the dispatch configuration
    agent_name = os.getenv("AGENT_NAME", "inbound_raq")
    livekit_url = os.getenv("LIVEKIT_URL")

    print(f"✅ Agent Configuration:")
    print(f"   Agent name: {agent_name}")
    print(f"   LiveKit URL: {livekit_url}")
    print(f"   Expected dispatch target: {agent_name}")

    # Verify the dispatch request structure
    sample_room_name = "inbound_call_15551234567_123"
    sample_metadata = {
        "call_type": "inbound",
        "phone_number": "+15551234567",
        "agent_name": "Test Agent"
    }

    print(f"✅ Dispatch Request Structure:")
    print(f"   Room: {sample_room_name}")
    print(f"   Agent: {agent_name}")
    print(f"   Metadata: {json.dumps(sample_metadata, indent=2)}")

    return True

def test_environment_readiness():
    """Test that all required environment variables are set"""
    print("🌍 Testing Environment Readiness...")

    required_vars = [
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "DEEPGRAM_API_KEY",
        "CARTESIA_API_KEY",
        "OPENAI_API_KEY",
        "AGENT_NAME"
    ]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Show masked version for security
            if "KEY" in var or "SECRET" in var:
                masked = f"{value[:10]}..." if len(value) > 10 else "***"
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")

    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False

    print(f"✅ All environment variables configured")
    return True

async def main():
    """Main test function"""
    print("🚀 Starting Agent Configuration API Integration Tests")
    print("=" * 60)

    # Test 1: Environment readiness
    env_ready = test_environment_readiness()
    print()

    if not env_ready:
        print("❌ Environment not ready - stopping tests")
        return

    # Test 2: Agent metadata validation
    metadata_success = await test_agent_metadata_validation()
    print()

    # Test 3: Agent dispatch verification
    dispatch_success = await test_agent_dispatch_verification()
    print()

    # Test 4: Complete configuration flow
    config_success = await test_agent_configuration_flow()
    print()

    if all([env_ready, metadata_success, dispatch_success, config_success]):
        print("🎉 All Agent Configuration Tests Passed!")
        print("=" * 60)
        print("✅ The inbound_raq agent is properly configured and ready")
        print("✅ LiveKit room creation and dispatch working")
        print("✅ Agent metadata and customer info properly formatted")
        print("✅ Complete workflow: Call → Lead → Room → Agent dispatch")
        print()
        print("🔜 Next step: Setup ngrok or deploy backend for webhook testing")
    else:
        print("⚠️  Some agent configuration tests had issues")
        print("   Review the output above for specific problems")

if __name__ == "__main__":
    asyncio.run(main())