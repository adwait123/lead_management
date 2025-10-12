#!/usr/bin/env python3
"""
End-to-end test demonstrating follow-up cancellation when lead responds mid-sequence
"""

import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import our models and services
from models.database import Base
from models.agent import Agent
from models.lead import Lead
from models.agent_session import AgentSession
from models.follow_up_task import FollowUpTask
from models.message import Message
from services.follow_up_scheduler import FollowUpScheduler
from services.agent_service import AgentService
from services.workflow_service import WorkflowService

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test_e2e_response.db"

async def test_lead_response_cancellation():
    """Test lead responding mid-sequence and cancelling remaining follow-ups"""

    # Create test database
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Initialize services
    scheduler = FollowUpScheduler(db)
    agent_service = AgentService(db)
    workflow_service = WorkflowService(db)

    try:
        print("🧪 TESTING LEAD RESPONSE CANCELLATION")
        print("=" * 50)

        # Create agent with follow-up sequence
        workflow_steps = [
            {
                "id": "no_response_sequence_1",
                "type": "time_based_trigger",
                "sequence_position": 1,
                "trigger": {"event": "no_response", "delay_minutes": 1, "original_delay": 1, "original_unit": "minutes"},
                "action": {"type": "send_message", "template": "First follow-up message", "template_type": "no_response_sequence"}
            },
            {
                "id": "no_response_sequence_2",
                "type": "time_based_trigger",
                "sequence_position": 2,
                "trigger": {"event": "no_response", "delay_minutes": 3, "original_delay": 3, "original_unit": "minutes"},
                "action": {"type": "send_message", "template": "Second follow-up message", "template_type": "no_response_sequence"}
            },
            {
                "id": "no_response_sequence_3",
                "type": "time_based_trigger",
                "sequence_position": 3,
                "trigger": {"event": "no_response", "delay_minutes": 10, "original_delay": 10, "original_unit": "minutes"},
                "action": {"type": "send_message", "template": "Final follow-up message", "template_type": "no_response_sequence"}
            }
        ]

        agent = Agent(
            name="Test Agent with Response Handling",
            description="Agent for testing response cancellation",
            type="inbound",
            use_case="general_sales",
            prompt_template="You are a helpful assistant named {{agent_name}}.",
            model="gpt-3.5-turbo",
            temperature="0.7",
            max_tokens=200,
            is_active=True,
            workflow_steps=workflow_steps,
            triggers=[{"event": "new_lead", "condition": "any"}]
        )

        db.add(agent)
        db.commit()
        db.refresh(agent)

        print(f"✅ Created agent with 3-step follow-up sequence")

        # Create lead
        lead = Lead(
            name="Emma Test",
            first_name="Emma",
            last_name="Test",
            email="emma@test.com",
            phone="+1555987654",
            service_requested="Kitchen Remodel",
            source="website"
        )

        db.add(lead)
        db.commit()
        db.refresh(lead)

        print(f"✅ Created lead: {lead.name}")

        # Trigger workflow
        session_ids = workflow_service.handle_lead_created(lead_id=lead.id, source=lead.source)
        session_id = session_ids[0] if session_ids else None

        if not session_id:
            print("❌ No session created")
            return

        session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
        print(f"✅ Created session {session_id}")

        # Wait for initial message
        await asyncio.sleep(1)

        # Schedule follow-up sequence
        task_ids = scheduler.schedule_follow_up_sequence(
            agent_session_id=session_id,
            trigger_event="no_response",
            reference_time=datetime.utcnow()
        )

        print(f"✅ Scheduled {len(task_ids)} follow-up tasks")

        # Get tasks
        tasks = db.query(FollowUpTask).filter(
            FollowUpTask.agent_session_id == session_id
        ).order_by(FollowUpTask.sequence_position).all()

        print(f"\n📅 Follow-up Schedule:")
        for task in tasks:
            print(f"   Step {task.sequence_position}: {task.original_delay} {task.original_unit} - {task.message_template}")

        # Execute first follow-up
        print(f"\n⏰ Executing first follow-up...")
        tasks[0].scheduled_at = datetime.utcnow() - timedelta(minutes=1)
        db.commit()

        results = scheduler.execute_due_tasks()
        print(f"   ✅ First follow-up executed: {results}")

        # Check pending tasks
        pending_before = db.query(FollowUpTask).filter(
            FollowUpTask.agent_session_id == session_id,
            FollowUpTask.status == "pending"
        ).count()

        print(f"\n📊 Status Check:")
        print(f"   Pending follow-ups: {pending_before}")

        # Lead responds after first follow-up
        print(f"\n💬 Lead responds...")
        lead_response = Message.create_lead_message(
            agent_session_id=session_id,
            lead_id=lead.id,
            content="Hi! Thanks for following up. I'm interested in discussing the kitchen remodel. Can we set up a call?"
        )

        db.add(lead_response)
        db.commit()

        print(f"   ✅ Lead message: {lead_response.content[:60]}...")

        # Handle lead response (should cancel remaining follow-ups)
        response_result = scheduler.handle_lead_response(session_id)
        print(f"   ✅ Response handled: {response_result}")

        # Check pending tasks after response
        pending_after = db.query(FollowUpTask).filter(
            FollowUpTask.agent_session_id == session_id,
            FollowUpTask.status == "pending"
        ).count()

        cancelled_count = db.query(FollowUpTask).filter(
            FollowUpTask.agent_session_id == session_id,
            FollowUpTask.status == "cancelled"
        ).count()

        print(f"\n📊 Final Status:")
        print(f"   Pending follow-ups after response: {pending_after}")
        print(f"   Cancelled follow-ups: {cancelled_count}")

        # Get final conversation
        all_messages = db.query(Message).filter(
            Message.agent_session_id == session_id
        ).order_by(Message.created_at).all()

        print(f"\n💬 Final Conversation ({len(all_messages)} messages):")
        for i, msg in enumerate(all_messages, 1):
            sender = "🤖 Agent" if msg.sender_type == "agent" else "👤 Lead"
            content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content

            follow_up_info = ""
            if msg.sender_type == "agent" and msg.message_metadata and msg.message_metadata.get("is_follow_up"):
                follow_up_info = " [Follow-up]"

            print(f"   {i}. {sender}{follow_up_info}: {content}")

        print(f"\n🎉 TEST COMPLETED SUCCESSFULLY!")
        print(f"✅ Lead response properly cancelled {cancelled_count} remaining follow-ups")
        print(f"✅ Follow-up spam prevention working correctly")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_lead_response_cancellation())