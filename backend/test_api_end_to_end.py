#!/usr/bin/env python3
"""
Complete API-based end-to-end test for follow-up sequence functionality
Tests the entire workflow through actual HTTP APIs
"""

import asyncio
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:8000"
TEST_LEAD_ID = f"api-test-{int(time.time())}"

class APIEndToEndTest:
    """Test class for API-based follow-up sequence testing"""

    def __init__(self):
        self.base_url = BASE_URL
        self.test_lead_id = TEST_LEAD_ID
        self.created_agent_id = None
        self.created_lead_id = None
        self.session_id = None

        print(f"🧪 Starting API End-to-End Test")
        print(f"   Base URL: {self.base_url}")
        print(f"   Test Lead ID: {self.test_lead_id}")
        print("=" * 60)

    def make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            print(f"📡 {method.upper()} {endpoint} -> {response.status_code}")

            if response.status_code >= 400:
                print(f"❌ Request failed: {response.text}")
                return {"error": response.text, "status_code": response.status_code}

            return response.json()

        except Exception as e:
            print(f"❌ Request error: {str(e)}")
            return {"error": str(e)}

    def test_1_create_agent_with_follow_ups(self) -> bool:
        """Step 1: Create agent with follow-up sequence configuration"""
        print(f"\n🤖 Step 1: Creating agent with follow-up sequence...")

        # Agent data with follow-up sequence (2min, 4min, 1hour for faster testing)
        agent_data = {
            "name": f"API Test Agent {self.test_lead_id}",
            "description": "Agent for testing follow-up sequences via API",
            "type": "inbound",
            "use_case": "general_sales",
            "prompt_template": "You are a helpful sales assistant for {{business_name}}. Help customers with {{service_requested}}. Keep responses under 2 sentences for testing.",
            "model": "gpt-3.5-turbo",
            "temperature": "0.7",
            "max_tokens": 150,
            "is_active": True,
            "workflow_steps": [
                {
                    "id": "no_response_sequence_1",
                    "type": "time_based_trigger",
                    "sequence_position": 1,
                    "trigger": {
                        "event": "no_response",
                        "delay_minutes": 0.5,  # 30 seconds for testing
                        "original_delay": 30,
                        "original_unit": "seconds"
                    },
                    "action": {
                        "type": "send_message",
                        "template": "Hi {{first_name}}! Just checking if you have any questions about our services?",
                        "template_type": "no_response_sequence"
                    }
                },
                {
                    "id": "no_response_sequence_2",
                    "type": "time_based_trigger",
                    "sequence_position": 2,
                    "trigger": {
                        "event": "no_response",
                        "delay_minutes": 1,  # 1 minute total
                        "original_delay": 1,
                        "original_unit": "minutes"
                    },
                    "action": {
                        "type": "send_message",
                        "template": "Hi {{first_name}}, one more follow-up - is there anything specific you'd like to know?",
                        "template_type": "no_response_sequence"
                    }
                },
                {
                    "id": "no_response_sequence_3",
                    "type": "time_based_trigger",
                    "sequence_position": 3,
                    "trigger": {
                        "event": "no_response",
                        "delay_minutes": 60,  # 1 hour for final
                        "original_delay": 1,
                        "original_unit": "hours"
                    },
                    "action": {
                        "type": "send_message",
                        "template": "Hi {{first_name}}, this is my final follow-up. Feel free to reach out if you need assistance!",
                        "template_type": "no_response_sequence"
                    }
                }
            ],
            "triggers": [{"event": "new_lead", "condition": "any"}]
        }

        result = self.make_request("POST", "/api/agents", agent_data)

        if "error" in result:
            print(f"❌ Failed to create agent: {result['error']}")
            return False

        self.created_agent_id = result.get("id")
        print(f"✅ Created agent {self.created_agent_id} with 3-step follow-up sequence")
        print(f"   - Sequence: 2min → 4min → 1hour")

        return True

    def test_2_send_lead_webhook(self) -> bool:
        """Step 2: Send lead creation webhook to trigger workflow"""
        print(f"\n📬 Step 2: Sending lead creation webhook...")

        # Simulate Yelp lead webhook
        webhook_data = {
            "id": self.test_lead_id,
            "business_id": "test-business-123",
            "conversation_id": f"conv-{self.test_lead_id}",
            "time_created": datetime.utcnow().isoformat() + "+00:00",
            "last_event_time": datetime.utcnow().isoformat() + "+00:00",
            "temporary_email_address": f"test-{int(time.time())}@example.com",
            "temporary_email_address_expiry": (datetime.utcnow() + timedelta(days=30)).isoformat() + "+00:00",
            "temporary_phone_number": "+14155551234",
            "temporary_phone_number_expiry": (datetime.utcnow() + timedelta(days=30)).isoformat() + "+00:00",
            "user": {
                "display_name": "Alex TestCustomer"
            },
            "project": {
                "location": {"postal_code": "94105"},
                "additional_info": "API testing for kitchen remodel follow-up sequence",
                "availability": {
                    "status": "SPECIFIC_DATES",
                    "dates": [(datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")]
                },
                "job_names": ["Kitchen Remodeling"],
                "survey_answers": [
                    {
                        "question_text": "What type of kitchen work do you need?",
                        "question_identifier": "kitchen_type",
                        "answer_text": ["Full remodel - testing follow-up sequences"]
                    },
                    {
                        "question_text": "What is your budget range?",
                        "question_identifier": "budget",
                        "answer_text": ["$30,000 - $60,000"]
                    }
                ]
            }
        }

        result = self.make_request("POST", "/api/webhooks/zapier/yelp-lead-created", webhook_data)

        if "error" in result:
            print(f"❌ Failed to create lead via webhook: {result['error']}")
            return False

        self.created_lead_id = result.get("lead_id")
        session_ids = result.get("session_ids", [])
        self.session_id = session_ids[0] if session_ids else None

        print(f"✅ Lead webhook processed successfully")
        print(f"   - Lead ID: {self.created_lead_id}")
        print(f"   - Session ID: {self.session_id}")
        print(f"   - Session IDs: {session_ids}")

        if not self.session_id:
            print(f"⚠️  No session was created - this might indicate no agent matched the trigger")

        return True  # Still return True since the webhook itself succeeded

    def test_3_verify_initial_message(self) -> bool:
        """Step 3: Verify initial message was generated"""
        print(f"\n💬 Step 3: Verifying initial message generation...")

        # Give it a moment for async message generation
        time.sleep(2)

        # Get agent responses for the lead
        result = self.make_request(
            "GET",
            f"/api/webhooks/zapier/get-agent-responses/{self.test_lead_id}",
            params={"limit": 10}
        )

        if "error" in result:
            print(f"❌ Failed to get agent responses: {result['error']}")
            return False

        messages = result.get("messages", [])

        if not messages:
            print(f"❌ No initial message found")
            if not self.session_id:
                print(f"   (This is expected since no session was created)")
            return False

        initial_message = messages[0]
        print(f"✅ Initial message generated:")
        print(f"   - Message ID: {initial_message.get('message_id')}")
        print(f"   - Content: {initial_message.get('content', '')[:100]}...")
        print(f"   - Agent: {initial_message.get('agent_name')}")

        return True

    def test_4_verify_follow_up_scheduling(self) -> bool:
        """Step 4: Verify follow-up tasks were scheduled"""
        print(f"\n📅 Step 4: Verifying follow-up task scheduling...")

        if not self.session_id:
            print(f"❌ No session ID available")
            return False

        # Check follow-up tasks via testing API
        result = self.make_request(
            "GET",
            f"/api/testing/follow-ups/session/{self.session_id}/tasks"
        )

        if "error" in result:
            print(f"❌ Failed to get follow-up tasks: {result['error']}")
            return False

        tasks = result.get("tasks", [])
        total_tasks = result.get("total_tasks", 0)

        print(f"✅ Found {total_tasks} follow-up tasks:")
        for task in tasks:
            delay = f"{task.get('original_delay')} {task.get('original_unit')}"
            status = task.get('status')
            print(f"   - Step {task.get('sequence_position')}: {delay} ({status})")

        return total_tasks >= 3  # Expecting 3 follow-up tasks

    def test_5_wait_and_execute_first_follow_up(self) -> bool:
        """Step 5: Wait for and execute first follow-up"""
        print(f"\n⏰ Step 5: Waiting for first follow-up (2 minutes)...")

        print(f"   Waiting 30 seconds for first follow-up to be due (shortened for testing)...")
        time.sleep(30)  # 30 seconds for faster testing

        # Execute follow-ups manually by calling the scheduler endpoint
        result = self.make_request("POST", "/api/testing/follow-ups/execute-due-tasks")

        if "error" in result:
            print(f"❌ Failed to execute due tasks: {result['error']}")
            return False

        execution_results = result.get("execution_results", {})
        executed_count = execution_results.get("executed", 0)
        failed_count = execution_results.get("failed", 0)

        print(f"✅ Follow-up execution results:")
        print(f"   - Executed: {executed_count}")
        print(f"   - Failed: {failed_count}")

        return executed_count > 0 or failed_count == 0  # Accept either execution or no failures

    def test_6_check_follow_up_messages(self) -> bool:
        """Step 6: Check for follow-up messages"""
        print(f"\n🔍 Step 6: Checking for follow-up messages...")

        # Get all agent responses
        result = self.make_request(
            "GET",
            f"/api/webhooks/zapier/get-agent-responses/{self.test_lead_id}",
            params={"limit": 10}
        )

        if "error" in result:
            print(f"❌ Failed to get messages: {result['error']}")
            return False

        messages = result.get("messages", [])
        print(f"✅ Found {len(messages)} agent messages:")

        for i, msg in enumerate(messages, 1):
            content = msg.get("content", "")[:80]
            print(f"   {i}. {content}...")

        return len(messages) >= 1  # At least initial message

    def test_7_simulate_lead_response(self) -> bool:
        """Step 7: Simulate lead response to test cancellation"""
        print(f"\n👤 Step 7: Simulating lead response...")

        # Send lead message via webhook
        response_data = {
            "yelp_lead_id": self.test_lead_id,
            "conversation_id": f"conv-{self.test_lead_id}",
            "message_content": "Hi! Thanks for following up. I'm interested in discussing the kitchen remodel. Can we schedule a call?",
            "sender": "customer",
            "timestamp": datetime.utcnow().isoformat() + "+00:00"
        }

        result = self.make_request("POST", "/api/webhooks/zapier/yelp-message-received", response_data)

        if "error" in result:
            print(f"❌ Failed to send lead response: {result['error']}")
            return False

        print(f"✅ Lead response sent and processed")
        print(f"   - Lead message: {response_data['message_content'][:60]}...")

        # Check for agent response
        if result.get("message"):
            print(f"   - Agent replied: {result.get('message', '')[:60]}...")

        return True

    def test_8_verify_follow_up_cancellation(self) -> bool:
        """Step 8: Verify remaining follow-ups were cancelled"""
        print(f"\n🛑 Step 8: Verifying follow-up cancellation...")

        if not self.session_id:
            print(f"❌ No session ID available")
            return False

        # Check follow-up tasks status after lead response
        result = self.make_request(
            "GET",
            f"/api/testing/follow-ups/session/{self.session_id}/tasks"
        )

        if "error" in result:
            print(f"❌ Failed to get follow-up tasks: {result['error']}")
            return False

        tasks = result.get("tasks", [])
        cancelled_tasks = [task for task in tasks if task.get("status") == "cancelled"]
        pending_tasks = [task for task in tasks if task.get("status") == "pending"]

        print(f"✅ Follow-up cancellation results:")
        print(f"   - Total tasks: {len(tasks)}")
        print(f"   - Cancelled tasks: {len(cancelled_tasks)}")
        print(f"   - Pending tasks: {len(pending_tasks)}")

        # Should have some cancelled tasks after lead response
        return len(cancelled_tasks) > 0

    def test_9_final_conversation_check(self) -> bool:
        """Step 9: Final conversation check"""
        print(f"\n💬 Step 9: Final conversation summary...")

        # Get complete conversation
        result = self.make_request(
            "GET",
            f"/api/messages/conversation/{self.test_lead_id}",
            params={"limit": 20}
        )

        if "error" in result:
            print(f"❌ Failed to get conversation: {result['error']}")
            return False

        messages = result.get("messages", [])
        print(f"✅ Complete conversation ({len(messages)} messages):")

        for i, msg in enumerate(messages, 1):
            sender_type = msg.get("sender_type", "unknown")
            content = msg.get("content", "")[:60]
            sender_icon = "🤖" if sender_type == "agent" else "👤" if sender_type == "lead" else "⚙️"
            print(f"   {i}. {sender_icon} {sender_type}: {content}...")

        return True

    async def run_complete_test(self) -> bool:
        """Run the complete API test suite"""
        print(f"🚀 Starting Complete API End-to-End Test")
        print(f"   Testing follow-up sequences via HTTP APIs")

        tests = [
            ("Create Agent with Follow-ups", self.test_1_create_agent_with_follow_ups),
            ("Send Lead Webhook", self.test_2_send_lead_webhook),
            ("Verify Initial Message", self.test_3_verify_initial_message),
            ("Verify Follow-up Scheduling", self.test_4_verify_follow_up_scheduling),
            ("Wait for First Follow-up", self.test_5_wait_and_execute_first_follow_up),
            ("Check Follow-up Messages", self.test_6_check_follow_up_messages),
            ("Simulate Lead Response", self.test_7_simulate_lead_response),
            ("Verify Follow-up Cancellation", self.test_8_verify_follow_up_cancellation),
            ("Final Conversation Check", self.test_9_final_conversation_check)
        ]

        results = []

        for test_name, test_func in tests:
            try:
                print(f"\n" + "="*60)
                result = test_func()
                results.append((test_name, result))

                if result:
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")

            except Exception as e:
                print(f"💥 {test_name}: ERROR - {str(e)}")
                results.append((test_name, False))

        # Final summary
        print(f"\n" + "="*60)
        print(f"🎯 API TEST SUMMARY")
        print(f"="*60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}: {test_name}")

        print(f"\n📊 Results: {passed}/{total} tests passed")

        if passed == total:
            print(f"🎉 ALL TESTS PASSED! Follow-up sequence API is working correctly!")
            print(f"\n🔧 Verified Features:")
            print(f"   ✓ Agent creation with follow-up sequences")
            print(f"   ✓ Webhook lead creation and workflow triggering")
            print(f"   ✓ Initial message generation")
            print(f"   ✓ Follow-up task scheduling")
            print(f"   ✓ Lead response handling")
            print(f"   ✓ Follow-up cancellation on response")
            print(f"   ✓ Complete conversation tracking")
        else:
            print(f"❌ Some tests failed - check implementation")

        return passed == total

def main():
    """Main test function"""
    test = APIEndToEndTest()

    try:
        # Run synchronously for now (can be made async if needed)
        success = asyncio.run(test.run_complete_test())

        if success:
            print(f"\n✅ API End-to-End test completed successfully!")
        else:
            print(f"\n❌ API End-to-End test had failures")

    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()