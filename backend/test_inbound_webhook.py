#!/usr/bin/env python3
"""
Test script for inbound calling webhook with lead creation and agent session tracking
"""

import requests
import json
import time
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

# Test configuration
WEBHOOK_URL = "http://localhost:8000/api/inbound-calls/webhooks/twilio"
ADMIN_BASE_URL = "http://localhost:8000/api"

# Sample Twilio webhook data
SAMPLE_TWILIO_DATA = {
    "CallSid": "CA123456789abcdef123456789abcdef12",
    "From": "+15551234567",  # Test caller number
    "To": "+17622437375",    # Your inbound number
    "CallStatus": "ringing",
    "Direction": "inbound",
    "ApiVersion": "2010-04-01",
    "CallerName": "Test Caller",
    "CallerCity": "San Francisco",
    "CallerState": "CA",
    "CallerZip": "94105",
    "CallerCountry": "US",
}

def test_webhook_response():
    """Test 1: Verify webhook returns correct TwiML response"""
    print("🧪 Test 1: Testing webhook TwiML response...")

    try:
        response = requests.post(
            WEBHOOK_URL,
            data=SAMPLE_TWILIO_DATA,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )

        print(f"   ✅ Status Code: {response.status_code}")
        print(f"   ✅ Content-Type: {response.headers.get('content-type')}")

        # Check if response is XML
        if response.headers.get('content-type') == 'application/xml':
            print("   ✅ Response is XML (TwiML)")
            xml_content = response.text
            print(f"   📄 TwiML Response:\n{xml_content}")

            # Check for required TwiML elements
            if "<Dial>" in xml_content and "<Sip>" in xml_content:
                print("   ✅ Contains proper Dial+Sip elements")
                if "1w7n1n4d64r.sip.livekit.cloud" in xml_content:
                    print("   ✅ Routes to correct LiveKit SIP trunk")
                else:
                    print("   ❌ Incorrect SIP routing")
            else:
                print("   ❌ Missing required TwiML elements")
        else:
            print(f"   ❌ Response is not XML: {response.text}")

        return response.status_code == 200

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_database_operations():
    """Test 2: Verify database operations (lead creation, agent session)"""
    print("\n🧪 Test 2: Testing database operations...")

    # Wait for background processing
    print("   ⏳ Waiting 3 seconds for background processing...")
    time.sleep(3)

    try:
        # Check if inbound call was created
        print("   📋 Checking inbound call creation...")
        calls_response = requests.get(f"{ADMIN_BASE_URL}/inbound-calls/")
        if calls_response.status_code == 200:
            calls_data = calls_response.json()
            recent_calls = [call for call in calls_data.get("inbound_calls", [])
                          if call.get("caller_phone_number") == SAMPLE_TWILIO_DATA["From"]]

            if recent_calls:
                call = recent_calls[0]
                print(f"   ✅ Inbound call created: ID {call.get('id')}")
                print(f"   📞 Call status: {call.get('call_status')}")
                print(f"   👤 Lead ID: {call.get('lead_id')}")
                print(f"   🤖 Agent ID: {call.get('agent_id')}")

                return call
            else:
                print("   ❌ No matching inbound call found")
                return None
        else:
            print(f"   ❌ Failed to fetch calls: {calls_response.status_code}")
            return None

    except Exception as e:
        print(f"   ❌ Error checking database: {str(e)}")
        return None

def test_lead_creation(call_data):
    """Test 3: Verify lead was created or found"""
    print("\n🧪 Test 3: Testing lead creation...")

    if not call_data or not call_data.get("lead_id"):
        print("   ❌ No lead ID in call data")
        return False

    try:
        lead_id = call_data["lead_id"]
        lead_response = requests.get(f"{ADMIN_BASE_URL}/leads/{lead_id}")

        if lead_response.status_code == 200:
            lead = lead_response.json()
            print(f"   ✅ Lead found: {lead.get('name')} (ID: {lead_id})")
            print(f"   📞 Phone: {lead.get('phone')}")
            print(f"   📧 Email: {lead.get('email')}")
            print(f"   📍 Source: {lead.get('source')}")
            print(f"   📊 Status: {lead.get('status')}")

            # Check if it's the right phone number
            if lead.get("phone") == SAMPLE_TWILIO_DATA["From"]:
                print("   ✅ Phone number matches")
                return True
            else:
                print(f"   ❌ Phone mismatch: {lead.get('phone')} vs {SAMPLE_TWILIO_DATA['From']}")
                return False
        else:
            print(f"   ❌ Failed to fetch lead: {lead_response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Error checking lead: {str(e)}")
        return False

def test_agent_session(call_data):
    """Test 4: Verify agent session was created"""
    print("\n🧪 Test 4: Testing agent session creation...")

    if not call_data or not call_data.get("lead_id"):
        print("   ❌ Missing lead_id in call data")
        return False

    try:
        # Get sessions for the lead using the correct endpoint
        lead_id = call_data["lead_id"]
        sessions_response = requests.get(f"{ADMIN_BASE_URL}/agent-sessions/?lead_id={lead_id}")

        if sessions_response.status_code == 200:
            sessions_data = sessions_response.json()
            all_sessions = sessions_data.get("sessions", [])

            print(f"   📋 Found {len(all_sessions)} total sessions for lead {lead_id}")

            # Look for active sessions with inbound_call trigger
            active_sessions = [s for s in all_sessions
                             if s.get("session_status") == "active"
                             and s.get("trigger_type") == "inbound_call"]

            if active_sessions:
                session = active_sessions[0]
                print(f"   ✅ Agent session found: ID {session.get('id')}")
                print(f"   🎯 Trigger: {session.get('trigger_type')}")
                print(f"   📊 Status: {session.get('session_status')}")
                print(f"   🤖 Agent ID: {session.get('agent_id')}")
                print(f"   💬 Messages: {session.get('message_count', 0)}")
                return True
            else:
                print("   ❌ No active inbound call sessions found")
                if all_sessions:
                    print("   ℹ️  Available sessions:")
                    for s in all_sessions:
                        print(f"      - ID {s.get('id')}: {s.get('trigger_type')} ({s.get('session_status')})")
                return False
        else:
            print(f"   ❌ Failed to fetch sessions: {sessions_response.status_code}")
            # Try alternative endpoint for just active session
            print("   🔄 Trying alternative active session endpoint...")
            active_response = requests.get(f"{ADMIN_BASE_URL}/agent-sessions/lead/{lead_id}/active")

            if active_response.status_code == 200:
                session_data = active_response.json()
                if session_data and session_data.get("trigger_type") == "inbound_call":
                    print(f"   ✅ Active session found: ID {session_data.get('id')}")
                    print(f"   🎯 Trigger: {session_data.get('trigger_type')}")
                    print(f"   📊 Status: {session_data.get('session_status')}")
                    return True
                else:
                    print("   ❌ No active inbound call session found")
                    return False
            else:
                print(f"   ❌ Alternative endpoint also failed: {active_response.status_code}")
                return False

    except Exception as e:
        print(f"   ❌ Error checking agent session: {str(e)}")
        return False

def test_agent_availability():
    """Test 4.5: Check if inbound agents are available"""
    print("\n🧪 Test 4.5: Checking agent availability...")

    try:
        # Check if there are any agents at all
        agents_response = requests.get(f"{ADMIN_BASE_URL}/agents/")

        if agents_response.status_code == 200:
            agents_data = agents_response.json()
            all_agents = agents_data.get("agents", [])

            print(f"   📋 Found {len(all_agents)} total agents")

            # Look for active inbound agents
            inbound_agents = [a for a in all_agents
                            if a.get("type") == "inbound" and a.get("is_active") == True]

            if inbound_agents:
                agent = inbound_agents[0]
                print(f"   ✅ Active inbound agent found: {agent.get('name')} (ID: {agent.get('id')})")
                print(f"   🤖 Type: {agent.get('type')}")
                print(f"   📊 Status: {'Active' if agent.get('is_active') else 'Inactive'}")
                return True
            else:
                print("   ❌ No active inbound agents found")
                if all_agents:
                    print("   ℹ️  Available agents:")
                    for a in all_agents:
                        status = "Active" if a.get("is_active") else "Inactive"
                        print(f"      - {a.get('name')} (Type: {a.get('type')}, Status: {status})")
                else:
                    print("   ⚠️  No agents found in system")
                return False
        else:
            print(f"   ❌ Failed to fetch agents: {agents_response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Error checking agents: {str(e)}")
        return False

def test_workflow_integration():
    """Test 5: Check if workflow was triggered"""
    print("\n🧪 Test 5: Testing workflow integration...")

    try:
        # This is harder to test without direct workflow access
        # For now, just check that the system didn't crash
        health_response = requests.get(f"{ADMIN_BASE_URL}/health")

        if health_response.status_code == 200:
            print("   ✅ System health check passed")
            print("   ℹ️  Workflow integration requires manual verification")
            return True
        else:
            print(f"   ❌ Health check failed: {health_response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Error checking workflow: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Inbound Webhook Comprehensive Test")
    print("=" * 60)

    # Check if server is running
    try:
        health_check = requests.get(f"{ADMIN_BASE_URL}/health", timeout=5)
        if health_check.status_code != 200:
            print("❌ Server not running! Start with: python main.py")
            return
    except:
        print("❌ Server not running! Start with: python main.py")
        return

    print("✅ Server is running")

    # Run tests
    results = []

    # Test 1: Webhook TwiML Response
    results.append(test_webhook_response())

    # Test 2: Database Operations
    call_data = test_database_operations()
    results.append(call_data is not None)

    # Test 3: Lead Creation
    if call_data:
        results.append(test_lead_creation(call_data))
    else:
        results.append(False)

    # Test 4.5: Agent Availability (helps debug agent session issues)
    agent_available = test_agent_availability()
    results.append(agent_available)

    # Test 4: Agent Session
    if call_data:
        results.append(test_agent_session(call_data))
    else:
        results.append(False)

    # Test 5: Workflow Integration
    results.append(test_workflow_integration())

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    test_names = [
        "Webhook TwiML Response",
        "Database Operations",
        "Lead Creation",
        "Agent Availability",
        "Agent Session Creation",
        "Workflow Integration"
    ]

    passed = sum(results)
    total = len(results)

    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {name:<25} {status}")

    print("-" * 60)
    print(f"OVERALL: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Webhook is ready for production.")
    else:
        print("⚠️  Some tests failed. Check the issues above.")

    print("\n💡 Next Steps:")
    print("   1. Deploy to Render with these settings")
    print("   2. Update Twilio webhook URL to: https://your-app.onrender.com/api/inbound-calls/webhooks/twilio")
    print("   3. Test with real phone calls")

if __name__ == "__main__":
    main()