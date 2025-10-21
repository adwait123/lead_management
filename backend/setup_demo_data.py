#!/usr/bin/env python3
"""
Setup Demo Data for AILead Application
Creates realistic demo leads and agents for demonstration purposes.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime, timedelta

# Base URL for API calls
BASE_URL = "https://lead-management-staging-backend.onrender.com"

def check_api_connection():
    """Check if the API is available"""
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            print("✅ API connection successful")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API at {BASE_URL}: {str(e)}")
        print("Make sure the backend server is running")
        return False

def check_database_empty():
    """Check if database is empty (no leads or agents exist)"""
    try:
        # Check leads count
        leads_response = requests.get(f"{BASE_URL}/api/leads/")
        if leads_response.status_code == 200:
            leads_data = leads_response.json()
            leads_count = len(leads_data.get('leads', []))
        else:
            print(f"⚠️  Could not check leads count: {leads_response.status_code}")
            leads_count = 0

        # Check agents count
        agents_response = requests.get(f"{BASE_URL}/api/agents/")
        if agents_response.status_code == 200:
            agents_data = agents_response.json()
            agents_count = len(agents_data.get('agents', []))
        else:
            print(f"⚠️  Could not check agents count: {agents_response.status_code}")
            agents_count = 0

        print(f"📊 Current database state: {leads_count} leads, {agents_count} agents")

        if leads_count == 0 and agents_count == 0:
            print("✅ Database is empty - proceeding with demo data creation")
            return True
        else:
            print(f"⚠️  Database not empty - skipping demo data creation")
            print(f"   Found {leads_count} existing leads and {agents_count} existing agents")
            return False

    except Exception as e:
        print(f"❌ Error checking database state: {str(e)}")
        print("⚠️  Assuming database is not empty to avoid data conflicts")
        return False

def create_demo_leads():
    """Create 15 demo leads across different sources"""
    print("\n📋 Creating demo leads...")

    demo_leads = [
        # Yelp Leads (4)
        {
            "name": "Mario Rossi",
            "email": "mario@mariosrestaurant.com",
            "phone": "+15551234567",
            "company": "Mario's Restaurant",
            "address": "123 Main Street, Downtown",
            "service_requested": "Commercial Pest Control",
            "source": "yelp",
            "status": "new",
            "notes": "Commercial kitchen roach problem. Health inspection next month. Needs immediate professional treatment.",
            "interaction_history": {
                "initial_contact": "Yelp business inquiry about commercial pest control",
                "urgency": "high",
                "property_type": "restaurant"
            }
        },
        {
            "name": "Jennifer Wilson",
            "email": "j.wilson@email.com",
            "phone": "+15551234568",
            "company": "",
            "address": "456 Oak Avenue, Suburbia",
            "service_requested": "Termite Inspection",
            "source": "yelp",
            "status": "new",
            "notes": "Buying new home. Realtor recommended termite inspection before closing. Needs inspection within 2 weeks.",
            "interaction_history": {
                "initial_contact": "Yelp inquiry for home purchase termite inspection",
                "timeline": "2 weeks",
                "realtor": "Sunrise Realty"
            }
        },
        {
            "name": "David Chen",
            "email": "dchen@techstart.com",
            "phone": "+15551234569",
            "company": "TechStart Office",
            "address": "789 Business Park, Suite 300",
            "service_requested": "Office Pest Control",
            "source": "yelp",
            "status": "new",
            "notes": "3rd floor ant infestation in office building. Employees complaining. Need discrete professional service.",
            "interaction_history": {
                "initial_contact": "Yelp business page inquiry about office ant problem",
                "floor": "3rd floor",
                "employee_count": "25"
            }
        },
        {
            "name": "Sarah Martinez",
            "email": "sarah@gardenapts.com",
            "phone": "+15551234570",
            "company": "Garden Apartments",
            "address": "321 Residential Drive",
            "service_requested": "Property Management Contract",
            "source": "yelp",
            "status": "new",
            "notes": "Property manager seeking quarterly pest prevention contract for 48-unit apartment complex.",
            "interaction_history": {
                "initial_contact": "Yelp business inquiry for property management services",
                "units": "48",
                "frequency": "quarterly"
            }
        },

        # Google LSA Leads (4)
        {
            "name": "Emergency Call - Robert Taylor",
            "email": "rtaylor@email.com",
            "phone": "+15551234571",
            "company": "",
            "address": "555 Elm Street, Backyard",
            "service_requested": "Emergency Wasp Removal",
            "source": "google_lsa",
            "status": "new",
            "notes": "Large wasp nest in backyard tree. Outdoor graduation party tomorrow. Need same-day removal service.",
            "interaction_history": {
                "initial_contact": "Google LSA emergency wasp removal",
                "urgency": "same-day",
                "event": "graduation party tomorrow"
            }
        },
        {
            "name": "Mike Rodriguez",
            "email": "m.rodriguez@warehouse123.com",
            "phone": "+15551234572",
            "company": "Metro Warehouse",
            "address": "100 Industrial Boulevard",
            "service_requested": "Commercial Rodent Control",
            "source": "google_lsa",
            "status": "new",
            "notes": "Warehouse facility rodent problem in loading dock area. Health inspection scheduled for next week.",
            "interaction_history": {
                "initial_contact": "Google LSA commercial rodent control",
                "area": "loading dock",
                "inspection": "next week"
            }
        },
        {
            "name": "Lisa Thompson",
            "email": "lisa.t@grandhotel.com",
            "phone": "+15551234573",
            "company": "Grand Hotel",
            "address": "200 Hospitality Lane, Room 305",
            "service_requested": "Bed Bug Treatment",
            "source": "google_lsa",
            "status": "new",
            "notes": "Hotel room bed bug issue. Need discrete treatment to protect reputation. Guest reported bites.",
            "interaction_history": {
                "initial_contact": "Google LSA hotel bed bug treatment",
                "room": "305",
                "discretion": "required"
            }
        },
        {
            "name": "James Wilson",
            "email": "jwilson@newbuild.com",
            "phone": "+15551234574",
            "company": "Wilson Construction",
            "address": "777 New Development Drive",
            "service_requested": "New Construction Prevention",
            "source": "google_lsa",
            "status": "new",
            "notes": "New construction project needs monthly pest prevention plan. Builder recommendation for ongoing protection.",
            "interaction_history": {
                "initial_contact": "Google LSA new construction prevention",
                "frequency": "monthly",
                "project_type": "residential development"
            }
        },

        # Website Leads (3)
        {
            "name": "Amanda Johnson",
            "email": "amanda.johnson@email.com",
            "phone": "+15551234575",
            "company": "",
            "address": "888 Seller Street",
            "service_requested": "Home Sale Pest Inspection",
            "source": "website",
            "status": "new",
            "notes": "Selling home, need pest clearance letter for closing. Realtor requires professional inspection report.",
            "interaction_history": {
                "initial_contact": "Website contact form for home sale inspection",
                "closing_date": "in 3 weeks",
                "realtor_requirement": "yes"
            }
        },
        {
            "name": "Tom Parker",
            "email": "tparker@email.com",
            "phone": "+15551234576",
            "company": "",
            "address": "999 Homeowner Lane, Garage",
            "service_requested": "Termite Treatment Quote",
            "source": "website",
            "status": "new",
            "notes": "Found termite damage in garage during renovation. Need treatment estimate and repair recommendations.",
            "interaction_history": {
                "initial_contact": "Website quote request for termite damage",
                "location": "garage",
                "discovered_during": "renovation"
            }
        },
        {
            "name": "Rachel Green",
            "email": "rachel.green@email.com",
            "phone": "+15551234577",
            "company": "",
            "address": "111 Family Circle",
            "service_requested": "Pet-Safe Pest Control",
            "source": "website",
            "status": "new",
            "notes": "Family with toddlers and pets. Need completely safe pest control options. Ant problem in kitchen.",
            "interaction_history": {
                "initial_contact": "Website inquiry about pet-safe treatments",
                "children": "toddlers",
                "pets": "yes",
                "location": "kitchen"
            }
        },

        # Phone Call Leads (4)
        {
            "name": "Emergency - Carol Davis",
            "email": "carol.davis@email.com",
            "phone": "+15551234578",
            "company": "",
            "address": "222 Safety Street, Basement",
            "service_requested": "Emergency Spider Control",
            "source": "phone_call",
            "status": "new",
            "notes": "Black widow spiders found in basement. Safety concern with children in home. Need immediate treatment.",
            "interaction_history": {
                "initial_contact": "Direct phone call about black widow emergency",
                "location": "basement",
                "safety_concern": "children present"
            }
        },
        {
            "name": "Steve Adams",
            "email": "steve.adams@email.com",
            "phone": "+15551234579",
            "company": "",
            "address": "333 Referral Road",
            "service_requested": "Home Protection Plan",
            "source": "phone_call",
            "status": "new",
            "notes": "Friend referral from satisfied customer. Interested in general home protection and prevention plan.",
            "interaction_history": {
                "initial_contact": "Phone call from friend referral",
                "referral_source": "satisfied customer",
                "interest": "prevention plan"
            }
        },
        {
            "name": "Patricia Brown",
            "email": "patricia.brown@email.com",
            "phone": "+15551234580",
            "company": "",
            "address": "444 Follow-up Avenue",
            "service_requested": "Treatment Scheduling",
            "source": "phone_call",
            "status": "new",
            "notes": "Follow-up from quote provided last month. Ready to schedule treatment. Decided on full home treatment.",
            "interaction_history": {
                "initial_contact": "Phone follow-up on previous quote",
                "quote_date": "last month",
                "decision": "ready to schedule"
            }
        },
        {
            "name": "Carlos Mendez",
            "email": "carlos@tacostand.com",
            "phone": "+15551234581",
            "company": "Carlos Taco Stand",
            "address": "555 Commercial Kitchen Ave",
            "service_requested": "Restaurant Prep",
            "source": "phone_call",
            "status": "new",
            "notes": "Restaurant kitchen prep for health inspection. Commercial pest control needed within 48 hours.",
            "interaction_history": {
                "initial_contact": "Phone call for restaurant inspection prep",
                "business_type": "restaurant",
                "timeline": "48 hours"
            }
        }
    ]

    created_leads = []
    for i, lead_data in enumerate(demo_leads, 1):
        try:
            # Convert notes and interaction_history to proper structure as expected by API
            api_data = lead_data.copy()

            # Convert notes to proper format: [{"id": 1, "content": "...", "timestamp": "...", "author": "..."}]
            if lead_data.get("notes"):
                api_data["notes"] = [{
                    "id": 1,
                    "content": lead_data["notes"],
                    "timestamp": datetime.now().isoformat(),
                    "author": "Demo Setup"
                }]
            else:
                api_data["notes"] = []

            # Convert interaction_history to proper format: [{"id": 1, "type": "email", "content": "...", "timestamp": "...", "agent_id": 1}]
            if lead_data.get("interaction_history"):
                api_data["interaction_history"] = [{
                    "id": 1,
                    "type": "initial_contact",
                    "content": str(lead_data["interaction_history"]),
                    "timestamp": datetime.now().isoformat(),
                    "agent_id": None
                }]
            else:
                api_data["interaction_history"] = []

            response = requests.post(f"{BASE_URL}/api/leads/", json=api_data)
            if response.status_code == 200:
                lead = response.json()
                created_leads.append(lead)
                print(f"  ✅ Created lead {i}/15: {lead_data['name']} ({lead_data['source']})")
            else:
                print(f"  ❌ Failed to create lead {i}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"  ❌ Error creating lead {i}: {str(e)}")

        # Small delay to avoid overwhelming the API
        time.sleep(0.1)

    print(f"\n📋 Successfully created {len(created_leads)}/15 demo leads")
    return created_leads

def create_demo_agents():
    """Create 3 specialized demo agents"""
    print("\n🤖 Creating demo agents...")

    demo_agents = [
        # Agent 1: Yelp Business Specialist (with follow-ups)
        {
            "name": "Yelp Business Specialist",
            "description": "Specialized agent for handling Yelp business inquiries with automated follow-up capabilities",
            "type": "inbound",
            "use_case": "general_sales",
            "prompt_template": "You are a professional pest control specialist for Acme Pest Control (established 2015). You handle Yelp business inquiries and have AUTOMATED FOLLOW-UP capabilities to ensure no lead goes cold.\n\nCOMPANY INFORMATION:\n- Acme Pest Control - Licensed & Insured (License #PC-12345)\n- 8+ years serving residential and commercial customers\n- 24/7 emergency services, eco-friendly treatments\n- Free inspections, 100% satisfaction guarantee\n\nSERVICES & PRICING:\n- Residential: $150-250 (home size/pest dependent)\n- Commercial: $200-400 (square footage/frequency)\n- Emergency: $300-500 (same-day/after-hours)\n- Prevention plans: $75-125/month\n- Termite treatment: $800-1500 (fumigation/spot)\n\nYOUR FOLLOW-UP SYSTEM:\n- IMMEDIATE: Respond to initial inquiry professionally\n- 15 MINUTES: If no response, send gentle follow-up checking if they need clarification\n- 1 HOUR: If still no response, offer limited-time discount or emphasize urgency of pest problems\n\nFOLLOW-UP MESSAGING:\n15-minute follow-up: 'Hi {customer_name}, I wanted to follow up on your pest control inquiry. Do you have any questions about our services or pricing? I'm here to help address any concerns.'\n\n1-hour follow-up: 'Hi {customer_name}, I understand pest problems can be stressful and you might be comparing options. We're offering a 10% discount on your first service this week. Pest issues typically worsen over time, so early treatment saves money long-term. Would you like to schedule a free inspection?'\n\nCONVERSATION STYLE:\n- Professional, knowledgeable, solution-focused\n- Ask property details (size, pest type, urgency)\n- Emphasize free inspection and guarantee\n- Reference excellent Yelp reviews and local reputation\n- Always provide specific next steps\n\nLead context: {lead_context}\nPrevious interactions: {interaction_history}",
            "prompt_template_name": None,
            "prompt_variables": {},
            "personality_traits": [
                "professional",
                "knowledgeable",
                "solution-focused",
                "follow-up-oriented"
            ],
            "personality_style": "professional",
            "response_length": "moderate",
            "custom_personality_instructions": "Always maintain professional expertise while being approachable. Use follow-up system to ensure no Yelp leads go cold. Reference company credentials and local reputation.",
            "model": "gpt-4o-mini",
            "temperature": "0.7",
            "max_tokens": 500,
            "is_active": True,
            "is_public": True,
            "knowledge": [
                {
                    "type": "business_profile",
                    "content": {},
                    "name": "Business Profile"
                }
            ],
            "enabled_tools": [],
            "tool_configs": {},
            "conversation_settings": {
                "voice_enabled": False,
                "text_enabled": True,
                "response_time": "normal",
                "language": "en"
            },
            "triggers": [
                {
                    "event": "new_lead",
                    "active": True
                }
            ],
            "actions": [],
            "workflow_steps": [
                {
                    "type": "time_based_trigger",
                    "trigger": {
                        "event": "no_response",
                        "delay_minutes": 10
                    },
                    "action": {
                        "type": "send_message",
                        "message_template": "Hi {customer_name}, I wanted to follow up on your pest control inquiry. Do you have any questions about our services or pricing? I'm here to help address any concerns."
                    },
                    "sequence_position": 1
                },
                {
                    "type": "time_based_trigger",
                    "trigger": {
                        "event": "no_response",
                        "delay_minutes": 60
                    },
                    "action": {
                        "type": "send_message",
                        "message_template": "Hi {customer_name}, I understand pest problems can be stressful and you might be comparing options. We're offering a 10% discount on your first service this week. Pest issues typically worsen over time, so early treatment saves money long-term. Would you like to schedule a free inspection?"
                    },
                    "sequence_position": 2
                }
            ],
            "integrations": [],
            "sample_conversations": [],
            "total_interactions": 0,
            "success_rate": "0.0",
            "avg_response_time": "0.0",
            "created_by": "user"
        },

        # Agent 2: Outbound Website Follow-up Voice Agent
        {
            "name": "Website Follow-up Specialist",
            "description": "Outbound voice agent for following up on website inquiries and converting leads to appointments",
            "type": "outbound",
            "prompt_template": """You are a professional outbound specialist for Acme Pest Control. You call website leads within 15 minutes of form submission to convert them into appointments.

CALL STRUCTURE:
Opening: 'Hi {customer_name}, this is [your name] from Acme Pest Control. You just submitted an inquiry on our website about pest control. I'm calling to discuss your needs and see how we can help. Do you have a quick minute?'

QUALIFICATION PROCESS:
1. What pest problem are you experiencing?
2. How long have you noticed this issue?
3. Which areas of your property are affected?
4. Have you tried any treatments yourself?
5. How urgent is this - immediate service needed?
6. Best time for free inspection?

KEY MESSAGING:
- FREE inspection with no obligation
- Same-day service available for emergencies
- Licensed professionals with 8+ years experience
- Eco-friendly, pet-safe treatments
- 100% satisfaction guarantee

OBJECTION RESPONSES:
- 'Too expensive' → 'Our free inspection helps us provide accurate pricing. Many customers find we're competitive and offer more value'
- 'Need to think' → 'I understand. What specific concerns can I address? Pest problems typically worsen, so early action saves money'
- 'Not ready' → 'When would be better? I can set a reminder to follow up'

CONVERSATION GOALS:
- Schedule specific appointment time
- Build trust and rapport
- Address price concerns proactively
- Create urgency around pest problems
- Get commitment before ending call

Lead context: {lead_context}
Form submission data: {form_data}
Call timing: {call_metadata}""",
            "personality_traits": ["persuasive", "empathetic", "goal-oriented", "professional"],
            "personality_style": "professional",
            "response_length": "moderate",
            "model": "gpt-4o-mini",
            "temperature": "0.8",
            "max_tokens": 400,
            "conversation_settings": {
                "greeting_message": "Hi there! I'm calling about your recent website inquiry regarding pest control services.",
                "escalation_triggers": ["not_interested", "pricing_concern", "competitor_mention"],
                "max_conversation_length": 15,
                "auto_summarize": True,
                "voice_only": True
            },
            "custom_personality_instructions": "Focus on quick conversion to appointments. Be respectful but persistent. Address concerns immediately and create urgency around pest problems.",
            "is_active": True,
            "is_public": True
        },

        # Agent 3: Inbound Voice Reception Agent
        {
            "name": "Acme Reception Agent",
            "description": "Primary inbound voice reception agent for all customer calls to Acme Pest Control",
            "type": "inbound",
            "prompt_template": """You are the primary reception agent for Acme Pest Control, handling all incoming calls as the professional first point of contact.

GREETING PROTOCOL:
'Thank you for calling Acme Pest Control, this is [your name]. How can I help you today?'

COMPANY OVERVIEW:
- Licensed pest control since 2015
- Residential & commercial specialists
- Eco-friendly, family/pet-safe treatments
- Same-day emergency service
- Free inspections, competitive pricing

CALL CATEGORIES:
1. NEW CUSTOMERS: Problems, quotes, service questions
2. EXISTING CUSTOMERS: Scheduling, follow-ups, billing
3. EMERGENCIES: Immediate threats (wasps, aggressive pests)
4. GENERAL INQUIRIES: Service areas, methods, pricing

INFORMATION COLLECTION:
- Customer name and contact details
- Property address and type
- Pest problem description and affected areas
- Timeline and urgency level
- Previous treatment history
- Preferred appointment times

EMERGENCY ESCALATION:
For urgent issues (stings, health risks, aggressive pests):
- Prioritize same-day service slots
- Get detailed safety information
- Provide immediate safety guidance
- Escalate to emergency response team
- Follow up within 2 hours

PROFESSIONAL STANDARDS:
- Empathetic tone (pest problems are stressful!)
- Clear, appropriate pace speech
- Confirm all information before ending
- Always thank customers for choosing Acme
- Provide realistic timelines and expectations

APPOINTMENT SCHEDULING:
- Offer multiple time options
- Confirm address and contact info
- Explain what to expect during visit
- Send confirmation text/email
- Provide technician arrival window

Caller information: {caller_details}
Call context: {call_metadata}
System notes: {internal_notes}""",
            "personality_traits": ["helpful", "professional", "empathetic", "efficient"],
            "personality_style": "professional",
            "response_length": "moderate",
            "model": "gpt-4o-mini",
            "temperature": "0.7",
            "max_tokens": 450,
            "conversation_settings": {
                "greeting_message": "Thank you for calling Acme Pest Control, how can I help you today?",
                "escalation_triggers": ["emergency", "complaint", "technical_question"],
                "max_conversation_length": 20,
                "auto_summarize": True,
                "voice_only": True
            },
            "custom_personality_instructions": "Be the professional face of Acme Pest Control. Handle emergencies with urgency, regular calls with efficiency, and always maintain empathy for customer concerns.",
            "is_active": True,
            "is_public": True
        }
    ]

    created_agents = []
    for i, agent_data in enumerate(demo_agents, 1):
        try:
            response = requests.post(f"{BASE_URL}/api/agents/", json=agent_data)
            if response.status_code == 200:
                agent = response.json()
                created_agents.append(agent)
                print(f"  ✅ Created agent {i}/3: {agent_data['name']} ({agent_data['type']})")
            else:
                print(f"  ❌ Failed to create agent {i}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"  ❌ Error creating agent {i}: {str(e)}")

        # Small delay to avoid overwhelming the API
        time.sleep(0.1)

    print(f"\n🤖 Successfully created {len(created_agents)}/3 demo agents")
    return created_agents

def main():
    """Main function to setup all demo data"""
    print("🚀 Setting up AILead Demo Data...")
    print("=" * 50)

    # Check API connection first
    if not check_api_connection():
        sys.exit(1)

    # Check if database is empty - only proceed if no existing data
    if not check_database_empty():
        print("\n🛑 Demo data setup skipped - database contains existing data")
        print("💡 To force demo data creation, manually delete existing leads and agents first")
        sys.exit(0)

    # Create leads first (to avoid workflow triggers when agents are created)
    leads = create_demo_leads()

    # Create agents second
    agents = create_demo_agents()

    print("\n" + "=" * 50)
    print("🎉 Demo data setup complete!")
    print(f"📋 Created {len(leads)} demo leads")
    print(f"🤖 Created {len(agents)} demo agents")
    print("\nYou can now view the demo data in the application:")
    print(f"- Leads: {BASE_URL}/leads")
    print(f"- Agents: {BASE_URL}/agents")
    print(f"- Dashboard: {BASE_URL}/")

if __name__ == "__main__":
    main()