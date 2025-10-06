"""
Seed data script for AI Agents
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from models.database import engine, create_tables
from models.agent import Agent
import random

# Create session
Session = sessionmaker(bind=engine)

def create_realistic_agents():
    """Create realistic agent data for demo purposes"""

    agents_data = [
        {
            "name": "Sales Bot",
            "description": "Friendly AI assistant specialized in lead qualification and initial sales conversations",
            "type": "conversational",
            "prompt_template": "You are a friendly and professional sales assistant. Your goal is to help potential customers understand our services and qualify their needs. Always be helpful, ask relevant questions, and guide them toward scheduling a consultation.",
            "personality": "friendly",
            "response_style": "concise",
            "model": "gpt-3.5-turbo",
            "temperature": "0.7",
            "max_tokens": 400,
            "triggers": [
                {"event": "new_lead", "condition": "source=website"},
                {"event": "form_submission", "condition": "interest=sales"}
            ],
            "actions": [
                {"type": "send_email", "template": "welcome_email"},
                {"type": "schedule_follow_up", "delay": "24h"}
            ],
            "workflow_steps": [
                {"step": 1, "action": "greet_visitor", "description": "Welcome the visitor warmly"},
                {"step": 2, "action": "qualify_needs", "description": "Ask about their business needs"},
                {"step": 3, "action": "present_solutions", "description": "Suggest relevant services"},
                {"step": 4, "action": "schedule_call", "description": "Offer to schedule a consultation"}
            ],
            "integrations": [
                {"service": "calendly", "config": {"calendar_id": "sales-team"}},
                {"service": "mailchimp", "config": {"list_id": "prospects"}}
            ],
            "sample_conversations": [
                {
                    "id": 1,
                    "messages": [
                        {"role": "user", "content": "I'm interested in your CRM services"},
                        {"role": "assistant", "content": "Great! I'd love to help you find the perfect CRM solution. Can you tell me a bit about your business size and current challenges?"}
                    ]
                }
            ],
            "total_interactions": 127,
            "success_rate": "85.5",
            "avg_response_time": "1.2"
        },
        {
            "name": "Lead Qualifier Pro",
            "description": "Advanced AI agent that expertly qualifies leads using BANT methodology and scores prospects",
            "type": "lead_qualifier",
            "prompt_template": "You are a lead qualification specialist. Use the BANT (Budget, Authority, Need, Timeline) framework to qualify leads. Ask strategic questions to determine if prospects are a good fit for our services. Be thorough but respectful of their time.",
            "personality": "professional",
            "response_style": "detailed",
            "model": "gpt-4",
            "temperature": "0.3",
            "max_tokens": 600,
            "triggers": [
                {"event": "lead_status_change", "condition": "status=contacted"},
                {"event": "demo_request", "condition": "any"}
            ],
            "actions": [
                {"type": "update_lead_score", "threshold": 70},
                {"type": "assign_to_sales", "condition": "score>80"},
                {"type": "add_to_nurture", "condition": "score<50"}
            ],
            "workflow_steps": [
                {"step": 1, "action": "assess_budget", "description": "Determine budget range and decision timeline"},
                {"step": 2, "action": "identify_authority", "description": "Confirm decision-making authority"},
                {"step": 3, "action": "understand_needs", "description": "Deep dive into business needs and pain points"},
                {"step": 4, "action": "establish_timeline", "description": "Understand implementation timeline"},
                {"step": 5, "action": "calculate_score", "description": "Score lead based on BANT criteria"}
            ],
            "integrations": [
                {"service": "salesforce", "config": {"lead_scoring": True}},
                {"service": "hubspot", "config": {"auto_assign": True}}
            ],
            "sample_conversations": [
                {
                    "id": 1,
                    "messages": [
                        {"role": "user", "content": "We need a better way to manage our customer data"},
                        {"role": "assistant", "content": "I understand you're looking to improve customer data management. To help me recommend the best solution, could you share your approximate budget range for this project?"}
                    ]
                }
            ],
            "total_interactions": 89,
            "success_rate": "91.2",
            "avg_response_time": "2.1"
        },
        {
            "name": "Follow-up Champion",
            "description": "Persistent but polite AI agent that maintains engagement with prospects through strategic follow-ups",
            "type": "follow_up",
            "prompt_template": "You are a follow-up specialist focused on maintaining positive relationships with prospects. Your goal is to re-engage leads who haven't responded, provide additional value, and move them back into the sales process. Always be helpful and never pushy.",
            "personality": "friendly",
            "response_style": "concise",
            "model": "gpt-3.5-turbo",
            "temperature": "0.6",
            "max_tokens": 350,
            "triggers": [
                {"event": "no_response", "condition": "days>3"},
                {"event": "email_opened", "condition": "no_click"},
                {"event": "meeting_missed", "condition": "any"}
            ],
            "actions": [
                {"type": "send_follow_up", "template": "value_add_email"},
                {"type": "schedule_reminder", "delay": "7d"},
                {"type": "update_lead_status", "status": "following_up"}
            ],
            "workflow_steps": [
                {"step": 1, "action": "analyze_last_interaction", "description": "Review previous conversation context"},
                {"step": 2, "action": "craft_personalized_message", "description": "Create relevant follow-up message"},
                {"step": 3, "action": "provide_additional_value", "description": "Share useful resources or insights"},
                {"step": 4, "action": "gentle_call_to_action", "description": "Suggest next steps without pressure"}
            ],
            "integrations": [
                {"service": "email_marketing", "config": {"sequence_id": "follow_up_series"}},
                {"service": "calendar", "config": {"auto_reschedule": True}}
            ],
            "sample_conversations": [
                {
                    "id": 1,
                    "messages": [
                        {"role": "assistant", "content": "Hi! I wanted to follow up on our conversation about CRM solutions. I came across this helpful case study that might interest you - would you like me to share it?"},
                        {"role": "user", "content": "Sure, that would be helpful"}
                    ]
                }
            ],
            "total_interactions": 234,
            "success_rate": "67.8",
            "avg_response_time": "0.8"
        },
        {
            "name": "Support Hero",
            "description": "Customer support specialist that handles inquiries, resolves issues, and escalates when needed",
            "type": "conversational",
            "prompt_template": "You are a helpful customer support representative. Your goal is to resolve customer issues quickly and effectively. If you can't solve a problem, escalate it to human support with clear context. Always maintain a positive, solution-focused attitude.",
            "personality": "professional",
            "response_style": "detailed",
            "model": "gpt-3.5-turbo",
            "temperature": "0.4",
            "max_tokens": 500,
            "triggers": [
                {"event": "support_ticket", "condition": "priority=low"},
                {"event": "chat_initiated", "condition": "page=support"}
            ],
            "actions": [
                {"type": "create_ticket", "priority": "auto"},
                {"type": "search_knowledge_base", "scope": "all"},
                {"type": "escalate_to_human", "condition": "unsolved>10min"}
            ],
            "workflow_steps": [
                {"step": 1, "action": "understand_issue", "description": "Listen and clarify the customer's problem"},
                {"step": 2, "action": "search_solutions", "description": "Look for known solutions in knowledge base"},
                {"step": 3, "action": "provide_solution", "description": "Offer step-by-step resolution"},
                {"step": 4, "action": "confirm_resolution", "description": "Verify the issue is resolved"},
                {"step": 5, "action": "gather_feedback", "description": "Ask for feedback on support experience"}
            ],
            "integrations": [
                {"service": "zendesk", "config": {"auto_ticket": True}},
                {"service": "knowledge_base", "config": {"search_enabled": True}}
            ],
            "sample_conversations": [
                {
                    "id": 1,
                    "messages": [
                        {"role": "user", "content": "I'm having trouble logging into my account"},
                        {"role": "assistant", "content": "I'm sorry to hear you're having login issues. Let me help you resolve this quickly. Can you confirm the email address associated with your account?"}
                    ]
                }
            ],
            "total_interactions": 156,
            "success_rate": "93.6",
            "avg_response_time": "1.5"
        },
        {
            "name": "Demo Scheduler",
            "description": "Specialized agent that focuses on scheduling product demonstrations and technical calls",
            "type": "conversational",
            "prompt_template": "You are a demo scheduling specialist. Your primary goal is to understand the prospect's needs and schedule appropriate product demonstrations. Be enthusiastic about our product capabilities while being respectful of their time and requirements.",
            "personality": "enthusiastic",
            "response_style": "concise",
            "model": "gpt-3.5-turbo",
            "temperature": "0.5",
            "max_tokens": 400,
            "triggers": [
                {"event": "demo_request", "condition": "any"},
                {"event": "qualified_lead", "condition": "score>75"}
            ],
            "actions": [
                {"type": "check_calendar", "resource": "demo_team"},
                {"type": "send_calendar_invite", "template": "demo_invite"},
                {"type": "prepare_demo_notes", "context": "lead_profile"}
            ],
            "workflow_steps": [
                {"step": 1, "action": "understand_use_case", "description": "Learn about their specific needs"},
                {"step": 2, "action": "suggest_demo_format", "description": "Recommend best demo approach"},
                {"step": 3, "action": "find_available_times", "description": "Check calendar availability"},
                {"step": 4, "action": "confirm_appointment", "description": "Send confirmation and prep materials"}
            ],
            "integrations": [
                {"service": "calendly", "config": {"demo_calendar": True}},
                {"service": "zoom", "config": {"auto_create_meeting": True}}
            ],
            "sample_conversations": [
                {
                    "id": 1,
                    "messages": [
                        {"role": "user", "content": "I'd like to see how your platform works"},
                        {"role": "assistant", "content": "Excellent! I'd love to show you our platform in action. What specific features or use cases are you most interested in seeing during the demo?"}
                    ]
                }
            ],
            "total_interactions": 78,
            "success_rate": "88.5",
            "avg_response_time": "1.1",
            "is_active": True
        }
    ]

    session = Session()

    try:
        # Clear existing agents
        session.query(Agent).delete()
        session.commit()

        agents = []

        for agent_data in agents_data:
            # Add some randomization to timestamps
            created_days_ago = random.randint(1, 30)
            created_at = datetime.utcnow() - timedelta(days=created_days_ago)
            last_used_hours_ago = random.randint(1, 48)
            last_used_at = datetime.utcnow() - timedelta(hours=last_used_hours_ago)

            agent = Agent(
                name=agent_data["name"],
                description=agent_data["description"],
                type=agent_data["type"],
                use_case="general_sales",  # Default use case

                # Prompt configuration
                prompt_template=agent_data["prompt_template"],
                prompt_template_name=None,
                prompt_variables={},

                # Personality configuration (map old fields to new structure)
                personality_traits=[agent_data["personality"]] if agent_data.get("personality") else [],
                personality_style=agent_data.get("personality", "professional"),
                response_length=agent_data.get("response_style", "moderate"),
                custom_personality_instructions=None,

                # AI Model configuration
                model=agent_data["model"],
                temperature=agent_data["temperature"],
                max_tokens=agent_data["max_tokens"],

                # Knowledge Base
                knowledge=[],

                # Tools and Actions
                enabled_tools=[],
                tool_configs={},

                # Conversation Settings
                conversation_settings={},

                # Workflow configuration
                triggers=agent_data["triggers"],
                actions=agent_data["actions"],
                workflow_steps=agent_data["workflow_steps"],
                integrations=agent_data["integrations"],
                sample_conversations=agent_data["sample_conversations"],

                # Status and performance
                total_interactions=agent_data["total_interactions"],
                success_rate=agent_data["success_rate"],
                avg_response_time=agent_data["avg_response_time"],
                is_active=agent_data.get("is_active", True),
                is_public=random.choice([True, False]),
                created_by=random.choice(["Sarah Thompson", "Mike Chen", "Admin", "System"]),
                created_at=created_at,
                updated_at=created_at,
                last_used_at=last_used_at
            )

            agents.append(agent)
            session.add(agent)

        session.commit()
        print(f"✅ Successfully created {len(agents)} realistic agents!")

        # Print some stats
        agent_types = {}
        for agent in agents:
            agent_types[agent.type] = agent_types.get(agent.type, 0) + 1

        for agent_type, count in agent_types.items():
            print(f"   {agent_type.title()}: {count} agents")

        return agents

    except Exception as e:
        session.rollback()
        print(f"❌ Error creating agent seed data: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("🤖 Creating database tables...")
    create_tables()

    print("🤖 Seeding database with AI agent data...")
    agents = create_realistic_agents()

    print("🎉 Agent seeding completed!")
    print(f"💡 You can now test the API at http://localhost:8000/api/agents/")
    print(f"📚 API documentation available at http://localhost:8000/docs")