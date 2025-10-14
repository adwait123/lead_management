#!/usr/bin/env python3
"""
Comprehensive Integration Test Script for Lead Management Workflow
Tests voice calling and text messaging agents triggered by lead creation
"""

import os
import sys
import json
import time
import requests
import asyncio
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal

# Configuration
BASE_URL = "https://lead-management-staging.onrender.com"
FRONTEND_URL = "https://lead-management-staging-frontend.onrender.com"
TEST_PHONE = "+12014860463"

class LeadWorkflowTester:
    """Comprehensive test suite for lead workflow integration"""

    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.created_lead_ids = []

    def log_result(self, test_name: str, success: bool, message: str, details: dict = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {json.dumps(details, indent=2)}")

    def setup_test_environment(self):
        """Set up test environment by creating demo agents"""
        print("\n🔧 Setting up test environment...")

        try:
            # Create demo outbound agent
            from create_demo_outbound_agent import create_demo_outbound_agent
            outbound_agent_id = create_demo_outbound_agent()

            # Create demo text agent
            from create_demo_text_agent import create_demo_text_agent
            text_agent_id = create_demo_text_agent()

            self.log_result(
                "Environment Setup",
                True,
                f"Created agents: outbound={outbound_agent_id}, text={text_agent_id}"
            )

            return outbound_agent_id, text_agent_id

        except Exception as e:
            self.log_result("Environment Setup", False, str(e))
            return None, None

    def create_test_lead_via_api(self, test_name: str, phone: str = TEST_PHONE):
        """Create a test lead via API"""
        print(f"\n📝 Creating test lead via API: {test_name}")

        lead_data = {
            "name": f"Test User {test_name}",
            "first_name": "Test",
            "last_name": f"User {test_name}",
            "email": f"test.{test_name.lower().replace(' ', '')}@torkin.example.com",
            "phone": phone,
            "company": "Test Company",
            "service_requested": "Pest Control Inspection",
            "status": "new",
            "source": "torkin website",
            "notes": [
                {
                    "id": 1,
                    "content": f"Test lead created for {test_name} integration testing",
                    "timestamp": datetime.now().isoformat(),
                    "author": "test_script"
                }
            ]
        }

        try:
            response = self.session.post(f"{self.base_url}/api/leads", json=lead_data)

            if response.status_code == 200:
                lead = response.json()
                lead_id = lead["id"]
                self.created_lead_ids.append(lead_id)

                self.log_result(
                    f"Lead Creation - {test_name}",
                    True,
                    f"Created lead ID {lead_id}",
                    {"lead_id": lead_id, "phone": phone}
                )
                return lead_id
            else:
                self.log_result(
                    f"Lead Creation - {test_name}",
                    False,
                    f"API error: {response.status_code}",
                    {"response": response.text}
                )
                return None

        except Exception as e:
            self.log_result(f"Lead Creation - {test_name}", False, str(e))
            return None

    def verify_agent_session_created(self, lead_id: int, expected_agents: int = 2):
        """Verify that agent sessions were created for the lead"""
        print(f"\n🤖 Checking agent sessions for lead {lead_id}")

        try:
            # Wait a moment for workflow processing
            time.sleep(3)

            response = self.session.get(f"{self.base_url}/api/messages/lead/{lead_id}/active-session")

            if response.status_code == 200:
                session_data = response.json()
                if session_data.get("has_active_session"):
                    self.log_result(
                        "Agent Session Creation",
                        True,
                        f"Active session found for lead {lead_id}",
                        {"session": session_data.get("session")}
                    )
                    return session_data.get("session")
                else:
                    self.log_result(
                        "Agent Session Creation",
                        False,
                        f"No active session found for lead {lead_id}"
                    )
                    return None
            else:
                self.log_result(
                    "Agent Session Creation",
                    False,
                    f"API error: {response.status_code}"
                )
                return None

        except Exception as e:
            self.log_result("Agent Session Creation", False, str(e))
            return None

    def verify_auto_message_sent(self, lead_id: int):
        """Verify that an auto-message was sent to the lead"""
        print(f"\n💬 Checking auto-messages for lead {lead_id}")

        try:
            # Wait for initial message generation
            time.sleep(5)

            response = self.session.get(f"{self.base_url}/api/messages/lead/{lead_id}/messages")

            if response.status_code == 200:
                messages_data = response.json()
                if messages_data.get("success") and messages_data.get("messages"):
                    messages = messages_data["messages"]
                    agent_messages = [msg for msg in messages if msg.get("sender_type") == "agent"]

                    if agent_messages:
                        first_message = agent_messages[0]
                        self.log_result(
                            "Auto-Message Generation",
                            True,
                            f"Auto-message sent: '{first_message.get('content', '')[:100]}...'",
                            {"message_count": len(agent_messages), "first_message": first_message}
                        )
                        return agent_messages
                    else:
                        self.log_result(
                            "Auto-Message Generation",
                            False,
                            "No agent messages found"
                        )
                        return []
                else:
                    self.log_result(
                        "Auto-Message Generation",
                        False,
                        "No messages found or API error"
                    )
                    return []
            else:
                self.log_result(
                    "Auto-Message Generation",
                    False,
                    f"API error: {response.status_code}"
                )
                return []

        except Exception as e:
            self.log_result("Auto-Message Generation", False, str(e))
            return []

    def simulate_lead_response(self, lead_id: int, response_text: str):
        """Simulate a lead responding to the auto-message"""
        print(f"\n💭 Simulating lead response: '{response_text[:50]}...'")

        try:
            # Using the message simulation endpoint
            response = self.session.post(
                f"{self.base_url}/api/messages/simulate/lead-message",
                params={"lead_id": lead_id, "message": response_text}
            )

            if response.status_code == 200:
                self.log_result(
                    "Lead Response Simulation",
                    True,
                    f"Simulated response from lead {lead_id}",
                    {"response_text": response_text}
                )
                return True
            else:
                self.log_result(
                    "Lead Response Simulation",
                    False,
                    f"API error: {response.status_code}",
                    {"response": response.text}
                )
                return False

        except Exception as e:
            self.log_result("Lead Response Simulation", False, str(e))
            return False

    def verify_agent_response(self, lead_id: int, expected_min_messages: int = 2):
        """Verify that agent responded to lead message"""
        print(f"\n🤖 Checking agent responses for lead {lead_id}")

        try:
            # Wait for agent response generation
            time.sleep(3)

            response = self.session.get(f"{self.base_url}/api/messages/lead/{lead_id}/messages")

            if response.status_code == 200:
                messages_data = response.json()
                if messages_data.get("success") and messages_data.get("messages"):
                    messages = messages_data["messages"]
                    agent_messages = [msg for msg in messages if msg.get("sender_type") == "agent"]

                    if len(agent_messages) >= expected_min_messages:
                        latest_message = agent_messages[-1]
                        self.log_result(
                            "Agent Response Generation",
                            True,
                            f"Agent responded ({len(agent_messages)} messages total)",
                            {
                                "latest_response": latest_message.get("content", "")[:200],
                                "total_agent_messages": len(agent_messages)
                            }
                        )
                        return agent_messages
                    else:
                        self.log_result(
                            "Agent Response Generation",
                            False,
                            f"Expected {expected_min_messages}+ messages, got {len(agent_messages)}"
                        )
                        return agent_messages
                else:
                    self.log_result(
                        "Agent Response Generation",
                        False,
                        "No messages found"
                    )
                    return []
            else:
                self.log_result(
                    "Agent Response Generation",
                    False,
                    f"API error: {response.status_code}"
                )
                return []

        except Exception as e:
            self.log_result("Agent Response Generation", False, str(e))
            return []

    def check_outbound_call_triggered(self, lead_id: int):
        """Check if outbound call was triggered for the lead"""
        print(f"\n📞 Checking outbound calls for lead {lead_id}")

        try:
            # Wait for call scheduling
            time.sleep(2)

            response = self.session.get(f"{self.base_url}/api/calls/lead/{lead_id}")

            if response.status_code == 200:
                calls_data = response.json()
                if calls_data.get("calls"):
                    calls = calls_data["calls"]
                    self.log_result(
                        "Outbound Call Trigger",
                        True,
                        f"Found {len(calls)} call(s) for lead {lead_id}",
                        {
                            "calls": [
                                {
                                    "id": call.get("id"),
                                    "status": call.get("call_status"),
                                    "phone": call.get("phone_number")
                                }
                                for call in calls
                            ]
                        }
                    )
                    return calls
                else:
                    self.log_result(
                        "Outbound Call Trigger",
                        False,
                        f"No calls found for lead {lead_id}"
                    )
                    return []
            else:
                self.log_result(
                    "Outbound Call Trigger",
                    False,
                    f"API error: {response.status_code}"
                )
                return []

        except Exception as e:
            self.log_result("Outbound Call Trigger", False, str(e))
            return []

    def run_voice_agent_test(self):
        """Test voice agent outbound calling workflow"""
        print("\n🎯 === VOICE AGENT TEST ===")

        lead_id = self.create_test_lead_via_api("Voice Test")
        if not lead_id:
            return False

        # Check if outbound call was triggered
        calls = self.check_outbound_call_triggered(lead_id)

        # Check if agent session was created
        session = self.verify_agent_session_created(lead_id)

        return len(calls) > 0 and session is not None

    def run_text_agent_test(self):
        """Test text agent auto-messaging workflow"""
        print("\n🎯 === TEXT AGENT TEST ===")

        lead_id = self.create_test_lead_via_api("Text Test")
        if not lead_id:
            return False

        # Check if agent session was created
        session = self.verify_agent_session_created(lead_id)
        if not session:
            return False

        # Check if auto-message was sent
        messages = self.verify_auto_message_sent(lead_id)
        if not messages:
            return False

        # Simulate lead responses and verify agent replies
        test_responses = [
            "I found some wood damage and small holes. Not sure if it's termites but want to get it checked out soon.",
            "It's been getting worse over the past month. What does an inspection involve and how much does it cost?",
            "House is about 15 years old, 2000 sq ft. Can you come out this week?"
        ]

        for i, response in enumerate(test_responses, 1):
            print(f"\n--- Round {i} of conversation ---")

            # Simulate lead response
            if not self.simulate_lead_response(lead_id, response):
                return False

            # Verify agent responds
            expected_messages = i + 1  # Initial message + responses
            agent_messages = self.verify_agent_response(lead_id, expected_messages)
            if len(agent_messages) < expected_messages:
                return False

        return True

    def run_integrated_workflow_test(self):
        """Test both voice and text agents working together"""
        print("\n🎯 === INTEGRATED WORKFLOW TEST ===")

        lead_id = self.create_test_lead_via_api("Integrated Test")
        if not lead_id:
            return False

        # Both agents should be triggered
        session = self.verify_agent_session_created(lead_id)
        calls = self.check_outbound_call_triggered(lead_id)
        messages = self.verify_auto_message_sent(lead_id)

        integration_success = session and len(calls) > 0 and len(messages) > 0

        self.log_result(
            "Integrated Workflow",
            integration_success,
            "Both voice and text agents triggered" if integration_success else "Not all agents triggered",
            {
                "session_created": session is not None,
                "calls_triggered": len(calls) > 0,
                "messages_sent": len(messages) > 0
            }
        )

        return integration_success

    def cleanup_test_data(self):
        """Clean up test leads created during testing"""
        print(f"\n🧹 Cleaning up {len(self.created_lead_ids)} test leads...")

        cleaned_count = 0
        for lead_id in self.created_lead_ids:
            try:
                response = self.session.delete(f"{self.base_url}/api/leads/{lead_id}")
                if response.status_code == 200:
                    cleaned_count += 1
            except Exception as e:
                print(f"   Failed to clean up lead {lead_id}: {e}")

        print(f"   Cleaned up {cleaned_count}/{len(self.created_lead_ids)} test leads")

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📊 === TEST REPORT ===")

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")

        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")

        print(f"\n📁 Test Results JSON saved to: test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        # Save detailed results to file
        report_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": passed_tests/total_tests*100
                },
                "results": self.test_results,
                "test_configuration": {
                    "base_url": self.base_url,
                    "test_phone": TEST_PHONE,
                    "timestamp": datetime.now().isoformat()
                }
            }, f, indent=2)

        return passed_tests == total_tests

    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting Comprehensive Lead Workflow Integration Tests")
        print(f"🌐 Base URL: {self.base_url}")
        print(f"📞 Test Phone: {TEST_PHONE}")
        print("=" * 60)

        # Setup
        outbound_agent_id, text_agent_id = self.setup_test_environment()
        if not outbound_agent_id or not text_agent_id:
            print("❌ Failed to set up test environment. Exiting.")
            return False

        try:
            # Run individual tests
            voice_success = self.run_voice_agent_test()
            text_success = self.run_text_agent_test()
            integration_success = self.run_integrated_workflow_test()

            # Generate report
            all_passed = self.generate_test_report()

            return all_passed

        finally:
            # Cleanup
            self.cleanup_test_data()

def main():
    """Main test execution"""
    tester = LeadWorkflowTester()

    try:
        success = tester.run_all_tests()
        if success:
            print("\n🎉 All tests passed! System is ready for production.")
            sys.exit(0)
        else:
            print("\n💥 Some tests failed. Please review the report.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Test execution cancelled by user.")
        tester.cleanup_test_data()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        tester.cleanup_test_data()
        sys.exit(1)

if __name__ == "__main__":
    main()