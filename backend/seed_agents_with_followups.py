#!/usr/bin/env python3
"""
Seed Agents with Follow-up Sequences
Creates sample agents with different follow-up configurations for testing
"""

import os
import sys
import json
from datetime import datetime
from sqlalchemy.orm import Session

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import get_db, engine
from models.agent import Agent

def create_lead_qualification_agent():
    """Create a lead qualification agent with progressive follow-ups"""
    return {
        "name": "Lead Qualification Specialist",
        "description": "Specialized agent for qualifying new leads with progressive follow-up sequences",
        "type": "text",
        "use_case": "lead_qualification",

        # Prompt configuration
        "prompt_template": """You are a professional lead qualification specialist for {{business_name}}.
Your goal is to qualify leads and understand their project needs while building rapport.

Key objectives:
- Understand their specific needs and timeline
- Assess budget and decision-making authority
- Schedule a consultation if they're qualified
- Provide helpful information about our services

Lead Information:
- Name: {{first_name}} {{last_name}}
- Company: {{company}}
- Service Requested: {{service_requested}}
- Source: {{source}}

Be professional, helpful, and focus on understanding their needs.""",

        "prompt_template_name": "lead_qualification_v1",
        "prompt_variables": {},

        # Personality configuration
        "personality_traits": ["professional", "helpful", "consultative", "knowledgeable"],
        "personality_style": "professional",
        "response_length": "moderate",
        "custom_personality_instructions": "Be warm but professional. Ask thoughtful questions to understand their needs. Provide value in every interaction.",

        # AI Model configuration
        "model": "gpt-3.5-turbo",
        "temperature": "0.7",
        "max_tokens": 400,

        # Knowledge Base
        "knowledge": [
            {
                "type": "company_info",
                "title": "Service Offerings",
                "content": "We provide comprehensive home renovation services including kitchen remodeling, bathroom renovation, flooring, painting, and general contracting."
            },
            {
                "type": "process",
                "title": "Our Process",
                "content": "1. Initial consultation, 2. Design and planning, 3. Permit acquisition, 4. Construction, 5. Final walkthrough"
            }
        ],

        # Tools and Actions
        "enabled_tools": ["calendar_booking", "document_sharing"],
        "tool_configs": {
            "calendar_booking": {
                "calendar_link": "https://calendly.com/your-business",
                "available_slots": ["consultation", "estimate"]
            }
        },

        # Conversation Settings
        "conversation_settings": {
            "max_response_time": 300,
            "escalation_triggers": ["angry", "complex_technical", "high_value"]
        },

        # Workflow configuration with follow-up sequences
        "triggers": [
            {
                "event": "new_lead",
                "condition": "any",
                "active": True
            }
        ],

        "workflow_steps": [
            {
                "id": "no_response_sequence_1",
                "type": "time_based_trigger",
                "sequence_position": 1,
                "trigger": {
                    "event": "no_response",
                    "delay_minutes": 2,
                    "original_delay": 2,
                    "original_unit": "hours"
                },
                "action": {
                    "type": "send_message",
                    "template": "Hi {{first_name}}! I wanted to follow up on your {{service_requested}} inquiry. Do you have any questions about our services or process?",
                    "template_type": "no_response_sequence"
                }
            },
            {
                "id": "no_response_sequence_2",
                "type": "time_based_trigger",
                "sequence_position": 2,
                "trigger": {
                    "event": "no_response",
                    "delay_minutes": 6,
                    "original_delay": 6,
                    "original_unit": "hours"
                },
                "action": {
                    "type": "send_message",
                    "template": "Hello {{first_name}}, I understand you're considering your options for {{service_requested}}. I'd be happy to provide a free consultation to discuss your project. Would you like to schedule a brief call?",
                    "template_type": "no_response_sequence"
                }
            },
            {
                "id": "no_response_sequence_3",
                "type": "time_based_trigger",
                "sequence_position": 3,
                "trigger": {
                    "event": "no_response",
                    "delay_minutes": 1440,
                    "original_delay": 24,
                    "original_unit": "hours"
                },
                "action": {
                    "type": "send_message",
                    "template": "Hi {{first_name}}, this is my final follow-up regarding your {{service_requested}} project. If you'd like to discuss your needs in the future, please don't hesitate to reach out. We're here to help when you're ready!",
                    "template_type": "no_response_sequence"
                }
            }
        ],

        "actions": [],
        "integrations": [],
        "sample_conversations": [
            {
                "scenario": "Kitchen remodel inquiry",
                "messages": [
                    {
                        "role": "agent",
                        "content": "Hello! Thank you for your interest in kitchen remodeling. I'd love to learn more about your project. What's driving your decision to remodel your kitchen?"
                    },
                    {
                        "role": "lead",
                        "content": "We're looking to update our 20-year-old kitchen. It feels outdated and we need more storage."
                    },
                    {
                        "role": "agent",
                        "content": "That sounds like an exciting project! Updating a 20-year-old kitchen can really transform your home. What's your timeline for this project, and do you have a budget range in mind?"
                    }
                ]
            }
        ],

        # Status
        "is_active": True,
        "is_public": False,
        "created_by": "system_seed"
    }

def create_customer_support_agent():
    """Create a customer support agent with rapid response follow-ups"""
    return {
        "name": "Customer Support Specialist",
        "description": "Customer support agent with rapid follow-up sequences for service issues",
        "type": "text",
        "use_case": "customer_support",

        "prompt_template": """You are a customer support specialist for {{business_name}}.
Your goal is to resolve customer issues quickly and professionally.

Customer Information:
- Name: {{first_name}} {{last_name}}
- Issue Type: {{issue_type}}
- Priority: {{priority_level}}

Always:
- Acknowledge their concern immediately
- Provide clear next steps
- Follow up to ensure resolution
- Escalate when necessary""",

        "prompt_template_name": "customer_support_v1",
        "personality_traits": ["empathetic", "solution-focused", "responsive"],
        "personality_style": "professional",
        "response_length": "concise",

        "model": "gpt-3.5-turbo",
        "temperature": "0.6",
        "max_tokens": 300,

        "knowledge": [
            {
                "type": "support_procedures",
                "title": "Common Issues",
                "content": "Warranty claims, scheduling changes, payment questions, project delays"
            }
        ],

        "enabled_tools": ["ticket_creation", "escalation"],
        "tool_configs": {},
        "conversation_settings": {
            "max_response_time": 120,
            "escalation_triggers": ["angry", "urgent", "unresolved"]
        },

        "triggers": [
            {
                "event": "support_ticket",
                "condition": "any",
                "active": True
            }
        ],

        "workflow_steps": [
            {
                "id": "no_response_sequence_1",
                "type": "time_based_trigger",
                "sequence_position": 1,
                "trigger": {
                    "event": "no_response",
                    "delay_minutes": 1,
                    "original_delay": 1,
                    "original_unit": "hours"
                },
                "action": {
                    "type": "send_message",
                    "template": "Hi {{first_name}}, I wanted to check in about your support request. Do you need any additional assistance or clarification?",
                    "template_type": "no_response_sequence"
                }
            },
            {
                "id": "no_response_sequence_2",
                "type": "time_based_trigger",
                "sequence_position": 2,
                "trigger": {
                    "event": "no_response",
                    "delay_minutes": 240,
                    "original_delay": 4,
                    "original_unit": "hours"
                },
                "action": {
                    "type": "send_message",
                    "template": "Hello {{first_name}}, I'm following up on your support request. If this issue is resolved, please let me know. If you need further assistance, I'm here to help!",
                    "template_type": "no_response_sequence"
                }
            }
        ],

        "actions": [],
        "integrations": [],
        "sample_conversations": [],

        "is_active": True,
        "is_public": False,
        "created_by": "system_seed"
    }

def create_appointment_booking_agent():
    """Create an appointment booking agent with immediate follow-ups"""
    return {
        "name": "Appointment Booking Assistant",
        "description": "Specialized in booking appointments with immediate follow-up for scheduling",
        "type": "text",
        "use_case": "appointment_booking",

        "prompt_template": """You are an appointment booking assistant for {{business_name}}.
Your primary goal is to schedule appointments efficiently.

Available Services:
- Free consultations (60 minutes)
- Project estimates (30 minutes)
- Design reviews (45 minutes)

Be helpful, flexible with scheduling, and confirm all details clearly.""",

        "prompt_template_name": "appointment_booking_v1",
        "personality_traits": ["efficient", "organized", "accommodating"],
        "personality_style": "professional",
        "response_length": "concise",

        "model": "gpt-3.5-turbo",
        "temperature": "0.5",
        "max_tokens": 250,

        "knowledge": [
            {
                "type": "scheduling",
                "title": "Available Times",
                "content": "Monday-Friday 9AM-6PM, Saturday 10AM-4PM. Consultations, estimates, and design reviews available."
            }
        ],

        "enabled_tools": ["calendar_booking"],
        "tool_configs": {
            "calendar_booking": {
                "auto_confirm": True,
                "send_reminders": True
            }
        },

        "conversation_settings": {
            "max_response_time": 180
        },

        "triggers": [
            {
                "event": "appointment_request",
                "condition": "any",
                "active": True
            }
        ],

        "workflow_steps": [
            {
                "id": "no_response_sequence_1",
                "type": "time_based_trigger",
                "sequence_position": 1,
                "trigger": {
                    "event": "no_response",
                    "delay_minutes": 0.5,
                    "original_delay": 30,
                    "original_unit": "minutes"
                },
                "action": {
                    "type": "send_message",
                    "template": "Hi {{first_name}}! I have your appointment request. Are you still available for {{preferred_time}}? I can also suggest alternative times if needed.",
                    "template_type": "no_response_sequence"
                }
            },
            {
                "id": "no_response_sequence_2",
                "type": "time_based_trigger",
                "sequence_position": 2,
                "trigger": {
                    "event": "no_response",
                    "delay_minutes": 2,
                    "original_delay": 2,
                    "original_unit": "hours"
                },
                "action": {
                    "type": "send_message",
                    "template": "Hello {{first_name}}, I'm still holding some time slots for you. Please let me know your availability so we can get your appointment scheduled!",
                    "template_type": "no_response_sequence"
                }
            }
        ],

        "actions": [],
        "integrations": [],
        "sample_conversations": [],

        "is_active": True,
        "is_public": False,
        "created_by": "system_seed"
    }

def create_general_sales_agent():
    """Create a general sales agent with extended follow-up sequence"""
    return {
        "name": "General Sales Representative",
        "description": "General sales agent with comprehensive follow-up sequences for lead nurturing",
        "type": "text",
        "use_case": "general_sales",

        "prompt_template": """You are a sales representative for {{business_name}}.
Your goal is to understand customer needs and guide them toward a purchase decision.

Focus on:
- Building rapport and trust
- Understanding their specific needs
- Presenting relevant solutions
- Overcoming objections professionally
- Moving toward next steps

Customer: {{first_name}} {{last_name}}
Interest: {{service_requested}}""",

        "prompt_template_name": "general_sales_v1",
        "personality_traits": ["persuasive", "trustworthy", "knowledgeable", "persistent"],
        "personality_style": "professional",
        "response_length": "moderate",

        "model": "gpt-3.5-turbo",
        "temperature": "0.7",
        "max_tokens": 350,

        "knowledge": [
            {
                "type": "sales_materials",
                "title": "Product Benefits",
                "content": "Quality workmanship, licensed contractors, 5-year warranty, free estimates"
            }
        ],

        "enabled_tools": ["quote_generation", "calendar_booking"],
        "tool_configs": {},
        "conversation_settings": {},

        "triggers": [
            {
                "event": "new_lead",
                "condition": "any",
                "active": True
            }
        ],

        "workflow_steps": [
            {
                "id": "no_response_sequence_1",
                "type": "time_based_trigger",
                "sequence_position": 1,
                "trigger": {
                    "event": "no_response",
                    "delay_minutes": 3,
                    "original_delay": 3,
                    "original_unit": "hours"
                },
                "action": {
                    "type": "send_message",
                    "template": "Hi {{first_name}}! I wanted to follow up about your {{service_requested}} inquiry. I'd love to help you with your project. Do you have any questions I can answer?",
                    "template_type": "no_response_sequence"
                }
            },
            {
                "id": "no_response_sequence_2",
                "type": "time_based_trigger",
                "sequence_position": 2,
                "trigger": {
                    "event": "no_response",
                    "delay_minutes": 12,
                    "original_delay": 12,
                    "original_unit": "hours"
                },
                "action": {
                    "type": "send_message",
                    "template": "Hello {{first_name}}, I hope you're doing well! I wanted to share that we're currently offering free consultations for {{service_requested}} projects. Would you be interested in learning more?",
                    "template_type": "no_response_sequence"
                }
            },
            {
                "id": "no_response_sequence_3",
                "type": "time_based_trigger",
                "sequence_position": 3,
                "trigger": {
                    "event": "no_response",
                    "delay_minutes": 2880,
                    "original_delay": 48,
                    "original_unit": "hours"
                },
                "action": {
                    "type": "send_message",
                    "template": "Hi {{first_name}}, I understand you may be exploring your options for {{service_requested}}. We're here whenever you're ready to move forward. Feel free to reach out with any questions!",
                    "template_type": "no_response_sequence"
                }
            },
            {
                "id": "no_response_sequence_4",
                "type": "time_based_trigger",
                "sequence_position": 4,
                "trigger": {
                    "event": "no_response",
                    "delay_minutes": 10080,
                    "original_delay": 7,
                    "original_unit": "days"
                },
                "action": {
                    "type": "send_message",
                    "template": "Hello {{first_name}}, this is my final follow-up regarding your {{service_requested}} project. Thank you for considering us. If your plans change in the future, please don't hesitate to contact us!",
                    "template_type": "no_response_sequence"
                }
            }
        ],

        "actions": [],
        "integrations": [],
        "sample_conversations": [],

        "is_active": True,
        "is_public": False,
        "created_by": "system_seed"
    }

def create_test_agent():
    """Create a test agent with very short follow-up sequences for testing"""
    return {
        "name": "Test Agent - Quick Follow-ups",
        "description": "Test agent with 30-second follow-up intervals for testing purposes",
        "type": "text",
        "use_case": "general_sales",

        "prompt_template": "You are a test agent for {{business_name}}. Respond professionally to {{first_name}} about their {{service_requested}} inquiry.",
        "prompt_template_name": "test_agent_v1",
        "personality_traits": ["friendly", "responsive"],
        "personality_style": "casual",
        "response_length": "short",

        "model": "gpt-3.5-turbo",
        "temperature": "0.7",
        "max_tokens": 200,

        "knowledge": [],
        "enabled_tools": [],
        "tool_configs": {},
        "conversation_settings": {},

        "triggers": [
            {
                "event": "new_lead",
                "condition": "any",
                "active": True
            }
        ],

        "workflow_steps": [
            {
                "id": "no_response_sequence_1",
                "type": "time_based_trigger",
                "sequence_position": 1,
                "trigger": {
                    "event": "no_response",
                    "delay_minutes": 0.5,
                    "original_delay": 30,
                    "original_unit": "seconds"
                },
                "action": {
                    "type": "send_message",
                    "template": "Quick follow-up: Any questions about our services?",
                    "template_type": "no_response_sequence"
                }
            },
            {
                "id": "no_response_sequence_2",
                "type": "time_based_trigger",
                "sequence_position": 2,
                "trigger": {
                    "event": "no_response",
                    "delay_minutes": 1,
                    "original_delay": 1,
                    "original_unit": "minutes"
                },
                "action": {
                    "type": "send_message",
                    "template": "Still here to help if you need anything!",
                    "template_type": "no_response_sequence"
                }
            }
        ],

        "actions": [],
        "integrations": [],
        "sample_conversations": [],

        "is_active": True,
        "is_public": False,
        "created_by": "system_seed"
    }

def seed_agents():
    """Create all seed agents"""
    print("🌱 Creating seed agents with follow-up sequences...")

    # Get database session
    db = next(get_db())

    # Agent creation functions
    agent_creators = [
        ("Lead Qualification Specialist", create_lead_qualification_agent),
        ("Customer Support Specialist", create_customer_support_agent),
        ("Appointment Booking Assistant", create_appointment_booking_agent),
        ("General Sales Representative", create_general_sales_agent),
        ("Test Agent - Quick Follow-ups", create_test_agent)
    ]

    created_agents = []

    for agent_name, creator_func in agent_creators:
        try:
            # Check if agent already exists
            existing_agent = db.query(Agent).filter(Agent.name == agent_name).first()
            if existing_agent:
                print(f"⚠️  Agent '{agent_name}' already exists (ID: {existing_agent.id})")
                created_agents.append(existing_agent)
                continue

            # Create agent data
            agent_data = creator_func()

            # Create agent instance
            agent = Agent(
                name=agent_data["name"],
                description=agent_data["description"],
                type=agent_data["type"],
                use_case=agent_data["use_case"],
                prompt_template=agent_data["prompt_template"],
                prompt_template_name=agent_data["prompt_template_name"],
                prompt_variables=agent_data["prompt_variables"],
                personality_traits=agent_data["personality_traits"],
                personality_style=agent_data["personality_style"],
                response_length=agent_data["response_length"],
                custom_personality_instructions=agent_data.get("custom_personality_instructions"),
                model=agent_data["model"],
                temperature=agent_data["temperature"],
                max_tokens=agent_data["max_tokens"],
                knowledge=agent_data["knowledge"],
                enabled_tools=agent_data["enabled_tools"],
                tool_configs=agent_data["tool_configs"],
                conversation_settings=agent_data["conversation_settings"],
                triggers=agent_data["triggers"],
                actions=agent_data["actions"],
                workflow_steps=agent_data["workflow_steps"],
                integrations=agent_data["integrations"],
                sample_conversations=agent_data["sample_conversations"],
                is_active=agent_data["is_active"],
                is_public=agent_data["is_public"],
                created_by=agent_data["created_by"]
            )

            # Add to database
            db.add(agent)
            db.commit()
            db.refresh(agent)

            created_agents.append(agent)
            print(f"✅ Created agent '{agent_name}' (ID: {agent.id}) with {len(agent_data['workflow_steps'])} follow-up steps")

        except Exception as e:
            print(f"❌ Error creating agent '{agent_name}': {str(e)}")
            db.rollback()
            continue

    db.close()
    return created_agents

def print_agent_summary(agents):
    """Print summary of created agents"""
    print("\n" + "="*70)
    print("🤖 SEED AGENTS SUMMARY")
    print("="*70)

    for agent in agents:
        workflow_count = len(agent.workflow_steps) if agent.workflow_steps else 0
        print(f"\n📋 {agent.name} (ID: {agent.id})")
        print(f"   Use Case: {agent.use_case}")
        print(f"   Follow-up Steps: {workflow_count}")

        if workflow_count > 0:
            print("   Follow-up Sequence:")
            for i, step in enumerate(agent.workflow_steps, 1):
                delay = step.get('trigger', {}).get('original_delay', 0)
                unit = step.get('trigger', {}).get('original_unit', 'minutes')
                print(f"     {i}. After {delay} {unit} → {step.get('action', {}).get('template', 'N/A')[:50]}...")

def main():
    """Main seeding function"""
    print("="*70)
    print("🌱 SEED AGENTS WITH FOLLOW-UP SEQUENCES")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Create agents
        agents = seed_agents()

        # Print summary
        print_agent_summary(agents)

        print(f"\n✅ Successfully created {len(agents)} agents with follow-up sequences!")
        print("\n🚀 Next steps:")
        print("- Test agent creation in your UI")
        print("- Send test leads via webhook")
        print("- Monitor follow-up sequence execution")
        print("- Adjust timing and messaging as needed")

        return True

    except Exception as e:
        print(f"❌ Error during seeding: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Seeding completed successfully!")
        else:
            print("\n💥 Seeding failed!")
    except KeyboardInterrupt:
        print("\n⚠️ Seeding interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")