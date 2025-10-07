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
            "name": "Yelp Quote Specialist",
            "description": "Expert agent for handling Yelp 'Request a Quote' leads for home services. Specializes in qualifying homeowners and scheduling service estimates.",
            "type": "lead_qualifier",
            "use_case": "yelp_quote_qualification",
            "prompt_template": "You are a professional home service specialist handling Yelp quote requests. Your goal is to quickly qualify homeowners, understand their project needs, timeline, and budget to provide accurate estimates. Be friendly but efficient, ask the right questions to gather project details, and guide them toward scheduling an in-home consultation when appropriate.",
            "personality_traits": ["Professional", "Efficient", "Helpful"],
            "personality_style": "professional",
            "response_length": "moderate",
            "custom_personality_instructions": "Always ask about project timeline, budget range, and specific requirements. Mention our 5-star Yelp rating and local expertise.",
            "model": "gpt-4",
            "temperature": "0.4",
            "max_tokens": 500,
            "knowledge": [
                {"title": "Yelp Best Practices", "content": "Always respond within 1 hour to Yelp quotes for best ranking"},
                {"title": "Home Service Pricing", "content": "Standard pricing ranges for common home improvement projects"},
                {"title": "Seasonal Considerations", "content": "Project timing recommendations based on California weather"}
            ],
            "enabled_tools": ["calendar_scheduler", "price_calculator", "project_estimator"],
            "tool_configs": {
                "calendar_scheduler": {"integration": "calendly", "buffer_time": 30},
                "price_calculator": {"markup_percentage": 15, "include_materials": True}
            },
            "triggers": [
                {"event": "yelp_quote_request", "condition": "source=Yelp"},
                {"event": "new_lead", "condition": "source=Yelp AND service_type=home_improvement"}
            ],
            "actions": [
                {"type": "send_initial_response", "template": "yelp_quote_response", "delay": "immediate"},
                {"type": "schedule_estimate", "condition": "qualified=true"},
                {"type": "update_lead_score", "formula": "project_size * urgency * budget_fit"}
            ],
            "workflow_steps": [
                {"step": 1, "action": "acknowledge_request", "description": "Thank them for their Yelp quote request"},
                {"step": 2, "action": "gather_project_details", "description": "Ask about project scope, timeline, and location"},
                {"step": 3, "action": "assess_budget_fit", "description": "Understand their budget expectations"},
                {"step": 4, "action": "provide_initial_estimate", "description": "Give ballpark pricing if possible"},
                {"step": 5, "action": "schedule_consultation", "description": "Book in-home estimate appointment"}
            ],
            "integrations": [
                {"service": "yelp_api", "config": {"auto_respond": True, "response_template": "professional"}},
                {"service": "calendly", "config": {"calendar_type": "estimate_appointments"}},
                {"service": "quickbooks", "config": {"auto_create_estimate": True}}
            ],
            "sample_conversations": [
                {
                    "id": 1,
                    "messages": [
                        {"role": "user", "content": "I need a quote for kitchen remodeling in my 1200 sq ft home"},
                        {"role": "assistant", "content": "Thank you for your Yelp quote request! I'd be happy to help with your kitchen remodel. To provide you with an accurate estimate, could you tell me what specific updates you're looking for? For example, are you thinking full renovation with new cabinets and appliances, or more of a refresh with countertops and paint?"}
                    ]
                }
            ],
            "total_interactions": 89,
            "success_rate": "92.1",
            "avg_response_time": "0.8"
        },
        {
            "name": "HomeAdvisor Pro Assistant",
            "description": "Specialized AI agent for managing HomeAdvisor leads and converting them into booked appointments for home service projects.",
            "type": "conversational",
            "use_case": "homeadvisor_lead_conversion",
            "prompt_template": "You are a professional home service representative specializing in HomeAdvisor leads. Your goal is to quickly build rapport with homeowners, understand their project needs, and convert them into scheduled consultations. Be knowledgeable about home improvement projects, pricing, and timelines. Always emphasize our expertise and customer satisfaction ratings.",
            "personality_traits": ["Knowledgeable", "Trustworthy", "Results-oriented"],
            "personality_style": "professional",
            "response_length": "moderate",
            "custom_personality_instructions": "Reference our HomeAdvisor Pro status and customer reviews. Focus on building trust quickly and getting to an appointment booking.",
            "model": "gpt-3.5-turbo",
            "temperature": "0.5",
            "max_tokens": 450,
            "knowledge": [
                {"title": "HomeAdvisor Lead Quality", "content": "HomeAdvisor leads are pre-screened and have expressed specific interest"},
                {"title": "Trust Building", "content": "Emphasize licensing, insurance, and customer testimonials"},
                {"title": "Project Timelines", "content": "Standard timelines for different home improvement projects"}
            ],
            "enabled_tools": ["appointment_scheduler", "project_calculator", "review_displayer"],
            "tool_configs": {
                "appointment_scheduler": {"service": "acuity", "buffer_days": 2},
                "review_displayer": {"min_rating": 4, "max_reviews": 5}
            },
            "triggers": [
                {"event": "new_lead", "condition": "source=HomeAdvisor"},
                {"event": "lead_response", "condition": "platform=HomeAdvisor"}
            ],
            "actions": [
                {"type": "immediate_response", "template": "homeadvisor_greeting"},
                {"type": "share_credentials", "content": "license_and_insurance"},
                {"type": "schedule_estimate", "priority": "high"}
            ],
            "workflow_steps": [
                {"step": 1, "action": "express_gratitude", "description": "Thank them for choosing us on HomeAdvisor"},
                {"step": 2, "action": "establish_credibility", "description": "Share credentials and customer reviews"},
                {"step": 3, "action": "understand_project", "description": "Ask detailed questions about their project"},
                {"step": 4, "action": "provide_expertise", "description": "Share relevant experience and insights"},
                {"step": 5, "action": "book_consultation", "description": "Schedule in-home estimate"}
            ],
            "integrations": [
                {"service": "homeadvisor_api", "config": {"auto_accept_leads": True}},
                {"service": "google_calendar", "config": {"estimate_calendar": "home_estimates"}},
                {"service": "twilio", "config": {"follow_up_sms": True}}
            ],
            "sample_conversations": [
                {
                    "id": 1,
                    "messages": [
                        {"role": "user", "content": "I submitted a request for bathroom renovation on HomeAdvisor"},
                        {"role": "assistant", "content": "Thank you for choosing us for your bathroom renovation project! We're excited to help bring your vision to life. We're licensed, fully insured, and have completed over 200 bathroom renovations with a 4.9-star rating. Could you tell me more about what you're hoping to achieve with this renovation?"}
                    ]
                }
            ],
            "total_interactions": 156,
            "success_rate": "88.5",
            "avg_response_time": "1.2"
        },
        {
            "name": "Follow-up Champion",
            "description": "Persistent but polite AI agent that maintains engagement with prospects through strategic follow-ups",
            "type": "follow_up",
            "use_case": "lead_nurturing",
            "prompt_template": "You are a follow-up specialist focused on maintaining positive relationships with prospects. Your goal is to re-engage leads who haven't responded, provide additional value, and move them back into the sales process. Always be helpful and never pushy.",
            "personality_traits": ["Friendly", "Persistent", "Helpful"],
            "personality_style": "friendly",
            "response_length": "concise",
            "custom_personality_instructions": "Never be pushy or aggressive. Always provide value before asking for anything.",
            "model": "gpt-3.5-turbo",
            "temperature": "0.6",
            "max_tokens": 350,
            "knowledge": [
                {"title": "Follow-up Timing", "content": "Best practices for follow-up timing and frequency"},
                {"title": "Value-Added Content", "content": "Resources and content to share with prospects"},
                {"title": "Re-engagement Strategies", "content": "Proven methods to re-activate cold leads"}
            ],
            "enabled_tools": ["email_templates", "content_library", "reminder_scheduler"],
            "tool_configs": {
                "email_templates": {"category": "follow_up", "personalization": True},
                "reminder_scheduler": {"default_delay": "7_days", "max_attempts": 5}
            },
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
            "use_case": "customer_support",
            "prompt_template": "You are a helpful customer support representative. Your goal is to resolve customer issues quickly and effectively. If you can't solve a problem, escalate it to human support with clear context. Always maintain a positive, solution-focused attitude.",
            "personality_traits": ["Professional", "Patient", "Solution-focused"],
            "personality_style": "professional",
            "response_length": "detailed",
            "custom_personality_instructions": "Always remain calm and helpful, even with frustrated customers. Focus on solving problems efficiently.",
            "model": "gpt-3.5-turbo",
            "temperature": "0.4",
            "max_tokens": 500,
            "knowledge": [
                {"title": "Common Issues", "content": "Database of frequently reported issues and solutions"},
                {"title": "Escalation Procedures", "content": "When and how to escalate issues to human support"},
                {"title": "Customer Satisfaction", "content": "Best practices for maintaining high customer satisfaction"}
            ],
            "enabled_tools": ["ticket_system", "knowledge_base", "escalation_manager"],
            "tool_configs": {
                "ticket_system": {"auto_create": True, "priority_detection": True},
                "escalation_manager": {"timeout_minutes": 10, "complexity_threshold": 7}
            },
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
                use_case=agent_data.get("use_case", "general_sales"),

                # Prompt configuration
                prompt_template=agent_data["prompt_template"],
                prompt_template_name=agent_data.get("prompt_template_name"),
                prompt_variables=agent_data.get("prompt_variables", {}),

                # Personality configuration (use new fields)
                personality_traits=agent_data.get("personality_traits", []),
                personality_style=agent_data.get("personality_style", "professional"),
                response_length=agent_data.get("response_length", "moderate"),
                custom_personality_instructions=agent_data.get("custom_personality_instructions"),

                # AI Model configuration
                model=agent_data["model"],
                temperature=agent_data["temperature"],
                max_tokens=agent_data["max_tokens"],

                # Knowledge Base
                knowledge=agent_data.get("knowledge", []),

                # Tools and Actions
                enabled_tools=agent_data.get("enabled_tools", []),
                tool_configs=agent_data.get("tool_configs", {}),

                # Conversation Settings
                conversation_settings=agent_data.get("conversation_settings", {}),

                # Workflow configuration
                triggers=agent_data.get("triggers", []),
                actions=agent_data.get("actions", []),
                workflow_steps=agent_data.get("workflow_steps", []),
                integrations=agent_data.get("integrations", []),
                sample_conversations=agent_data.get("sample_conversations", []),

                # Status and performance
                total_interactions=agent_data.get("total_interactions", 0),
                success_rate=agent_data.get("success_rate", "0.0"),
                avg_response_time=agent_data.get("avg_response_time", "0.0"),
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