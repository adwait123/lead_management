"""
Seed script for Hatch-inspired AI Lead Management system
Populates database with realistic home services data
"""
from datetime import datetime, timedelta
import json
from models.database import SessionLocal, engine
from models import Base, Agent, Lead, Appointment, AppointmentType, BusinessProfile, FAQ

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

def seed_business_profiles():
    """Create sample business profiles"""
    db = SessionLocal()
    try:
        profiles = [
            {
                "company_name": "Acme Home Services",
                "service_area": "Dallas, TX and surrounding areas",
                "phone_number": "(555) 123-4567",
                "email": "contact@acmehomeservices.com",
                "website": "https://acmehomeservices.com",
                "business_hours": "Monday-Friday 8AM-6PM, Saturday 9AM-3PM",
                "emergency_hours": "24/7 for plumbing emergencies",
                "services_offered": "Plumbing repair and installation, HVAC maintenance, electrical work, appliance repair",
                "service_area_details": "We serve Dallas, Plano, Frisco, McKinney, and Allen. Travel fees may apply outside core service area.",
                "pricing_policy": "Free estimates, transparent pricing, no hidden fees. Payment due upon completion.",
                "warranty_policy": "1-year warranty on all installations, 90-day guarantee on repairs",
                "industry": "home_services",
                "business_type": "general_contractor",
                "preferred_contact_method": "phone",
                "response_time_expectation": "within 1 hour during business hours",
                "emergency_services_available": True,
                "setup_completed": True,
                "operating_schedule": {
                    "monday": {"start": "08:00", "end": "18:00", "closed": False},
                    "tuesday": {"start": "08:00", "end": "18:00", "closed": False},
                    "wednesday": {"start": "08:00", "end": "18:00", "closed": False},
                    "thursday": {"start": "08:00", "end": "18:00", "closed": False},
                    "friday": {"start": "08:00", "end": "18:00", "closed": False},
                    "saturday": {"start": "09:00", "end": "15:00", "closed": False},
                    "sunday": {"start": "00:00", "end": "00:00", "closed": True}
                }
            }
        ]

        for profile_data in profiles:
            profile = BusinessProfile(**profile_data)
            db.add(profile)

        db.commit()
        print("✅ Business profiles seeded")
    except Exception as e:
        print(f"❌ Error seeding business profiles: {e}")
        db.rollback()
    finally:
        db.close()

def seed_faqs():
    """Create sample FAQs"""
    db = SessionLocal()
    try:
        faqs = [
            {
                "question": "Do you offer emergency services?",
                "answer": "Yes, we provide 24/7 emergency services for urgent plumbing and electrical issues.",
                "category": "services",
                "is_popular": True,
                "usage_count": 45
            },
            {
                "question": "What forms of payment do you accept?",
                "answer": "We accept cash, check, and all major credit cards. Payment is due upon completion of work.",
                "category": "payment",
                "is_popular": True,
                "usage_count": 38
            },
            {
                "question": "Do you provide free estimates?",
                "answer": "Yes, we provide free estimates for all jobs. Our technician will assess the work and provide transparent pricing.",
                "category": "pricing",
                "is_popular": True,
                "usage_count": 52
            },
            {
                "question": "Are you licensed and insured?",
                "answer": "Yes, we are fully licensed and insured. All our technicians are certified professionals.",
                "category": "credentials",
                "is_popular": True,
                "usage_count": 29
            },
            {
                "question": "What is your service area?",
                "answer": "We serve Dallas, Plano, Frisco, McKinney, and Allen with same-day service. Other areas available with travel fees.",
                "category": "service_area",
                "is_popular": True,
                "usage_count": 33
            }
        ]

        for faq_data in faqs:
            faq = FAQ(**faq_data)
            db.add(faq)

        db.commit()
        print("✅ FAQs seeded")
    except Exception as e:
        print(f"❌ Error seeding FAQs: {e}")
        db.rollback()
    finally:
        db.close()

def seed_appointment_types():
    """Create appointment types"""
    db = SessionLocal()
    try:
        appointment_types = [
            {
                "name": "Free Estimate",
                "description": "On-site evaluation and quote",
                "default_duration": 60,
                "category": "estimate",
                "advance_booking_required": 4,
                "max_advance_booking": 168,
                "preparation_instructions": "Please ensure the area needing service is accessible"
            },
            {
                "name": "Repair Service",
                "description": "Fix existing issues",
                "default_duration": 120,
                "category": "repair",
                "advance_booking_required": 24,
                "max_advance_booking": 720
            },
            {
                "name": "Installation",
                "description": "New equipment or system install",
                "default_duration": 240,
                "category": "installation",
                "advance_booking_required": 48,
                "max_advance_booking": 1440,
                "requires_preparation": True,
                "preparation_instructions": "Please ensure installation area is clear and electrical access is available"
            },
            {
                "name": "Maintenance Visit",
                "description": "Routine checkup and service",
                "default_duration": 90,
                "category": "maintenance",
                "advance_booking_required": 24,
                "max_advance_booking": 2160
            },
            {
                "name": "Emergency Service",
                "description": "Urgent repairs (24/7)",
                "default_duration": 180,
                "category": "emergency",
                "advance_booking_required": 0,
                "max_advance_booking": 24,
                "business_hours_only": False
            }
        ]

        for apt_type_data in appointment_types:
            apt_type = AppointmentType(**apt_type_data)
            db.add(apt_type)

        db.commit()
        print("✅ Appointment types seeded")
    except Exception as e:
        print(f"❌ Error seeding appointment types: {e}")
        db.rollback()
    finally:
        db.close()

def seed_agents():
    """Create sample AI agents with Hatch-inspired configuration"""
    db = SessionLocal()
    try:
        agents = [
            {
                "name": "Sarah - Speed to Lead Assistant",
                "description": "Handles new customer inquiries and schedules estimates",
                "type": "inbound",
                "use_case": "speed_to_lead",
                "prompt_template": """You are Sarah, an AI assistant for Acme Home Services, a home services company serving Dallas, TX and surrounding areas.

PERSONALITY & COMMUNICATION:
- Be professional, friendly, helpful in all interactions
- Communication mode: voice and text
- Communication style: conversational

BUSINESS CONTEXT:
- Company: Acme Home Services
- Service Area: Dallas, TX and surrounding areas
- Services: Plumbing repair and installation, HVAC maintenance, electrical work, appliance repair
- Hours: Monday-Friday 8AM-6PM, Saturday 9AM-3PM

YOUR ROLE & GOAL:
Engage new leads instantly from website, Angi, and other sources

CONVERSATION FLOW:
1. Qualify homeowner status and property details
2. Assess service urgency (emergency vs planned)
3. Collect contact information
4. Schedule estimate appointment
5. Confirm appointment details

AVAILABLE TOOLS:
- Check Calendar Availability
- Book Appointment
- Transfer
- End Success
- End Bailout

SUCCESS CRITERIA:
Appointment scheduled successfully. Customer ready for estimate visit.

IMPORTANT GUIDELINES:
- Always confirm you're speaking with the property owner for service requests
- Be helpful but transfer complex technical questions to human experts
- Maintain professional boundaries while being friendly
- Follow company policies and pricing guidelines""",
                "prompt_template_name": "speed_to_lead",
                "personality_traits": ["professional", "friendly", "helpful"],
                "personality_style": "conversational",
                "response_length": "moderate",
                "model": "gpt-4",
                "temperature": "0.7",
                "max_tokens": 300,
                "knowledge": [
                    "Emergency services available 24/7 for plumbing issues",
                    "Free estimates provided for all services",
                    "Service area includes Dallas, Plano, Frisco, McKinney, Allen",
                    "Licensed and insured with certified technicians"
                ],
                "enabled_tools": ["Check_Calendar_Availability", "Book_Appointment", "Transfer", "End_Success", "End_Bailout"],
                "workflow_steps": [
                    "Qualify homeowner status and property details",
                    "Assess service urgency (emergency vs planned)",
                    "Collect contact information",
                    "Schedule estimate appointment",
                    "Confirm appointment details"
                ],
                "is_active": True,
                "total_interactions": 247,
                "success_rate": "78.5",
                "avg_response_time": "2.3"
            },
            {
                "name": "Mike - Appointment Coordinator",
                "description": "Handles appointment confirmations and rescheduling",
                "type": "outbound",
                "use_case": "appointment_confirmation",
                "prompt_template": """You are Mike, an AI assistant for Acme Home Services calling to confirm upcoming appointments.

PERSONALITY & COMMUNICATION:
- Be professional, efficient, friendly in all interactions
- Communication mode: voice calls
- Communication style: concise

BUSINESS CONTEXT:
- Company: Acme Home Services
- Service Area: Dallas, TX and surrounding areas
- Services: Plumbing repair and installation, HVAC maintenance, electrical work, appliance repair

YOUR ROLE & GOAL:
Request customer to confirm their upcoming appointment

CONVERSATION FLOW:
1. Greet customer and state purpose
2. Confirm appointment details
3. Handle confirmation or reschedule requests
4. Provide any preparation instructions
5. Send updated confirmation if needed

AVAILABLE TOOLS:
- Check Calendar Availability
- Reschedule Appointment
- Cancel Appointment
- End Success

SUCCESS CRITERIA:
Appointment confirmed or successfully rescheduled""",
                "prompt_template_name": "appointment_confirmation",
                "personality_traits": ["professional", "efficient", "helpful"],
                "personality_style": "concise",
                "response_length": "brief",
                "model": "gpt-3.5-turbo",
                "temperature": "0.5",
                "max_tokens": 200,
                "enabled_tools": ["Check_Calendar_Availability", "Reschedule_Appointment", "Cancel_Appointment", "End_Success"],
                "workflow_steps": [
                    "Greet customer and state purpose",
                    "Confirm appointment details",
                    "Handle confirmation or reschedule requests",
                    "Provide any preparation instructions",
                    "Send updated confirmation if needed"
                ],
                "is_active": True,
                "total_interactions": 189,
                "success_rate": "92.1",
                "avg_response_time": "1.8"
            }
        ]

        for agent_data in agents:
            agent = Agent(**agent_data)
            db.add(agent)

        db.commit()
        print("✅ Agents seeded")
    except Exception as e:
        print(f"❌ Error seeding agents: {e}")
        db.rollback()
    finally:
        db.close()

def seed_appointments():
    """Create sample appointments"""
    db = SessionLocal()
    try:
        # Get agent IDs for assignment
        agent_sarah = db.query(Agent).filter(Agent.name.contains("Sarah")).first()

        base_date = datetime.now()
        appointments = [
            {
                "customer_name": "John Smith",
                "customer_phone": "(555) 123-4567",
                "customer_email": "john.smith@email.com",
                "customer_address": "123 Oak Street, Dallas, TX 75201",
                "service_type": "plumbing",
                "appointment_type": "estimate",
                "service_description": "Kitchen sink leak - customer reported slow drip",
                "estimated_duration": 60,
                "scheduled_date": base_date + timedelta(days=1, hours=10),
                "status": "confirmed",
                "priority": "normal",
                "assigned_technician": "Tom Wilson",
                "assigned_team": "plumbing_team",
                "customer_notes": "Leak has been getting worse over the past week",
                "lead_source": "website",
                "agent_id": agent_sarah.id if agent_sarah else None
            },
            {
                "customer_name": "Sarah Johnson",
                "customer_phone": "(555) 987-6543",
                "customer_email": "s.johnson@email.com",
                "customer_address": "456 Pine Avenue, Plano, TX 75023",
                "service_type": "hvac",
                "appointment_type": "maintenance",
                "service_description": "Annual HVAC maintenance visit - VIP member",
                "estimated_duration": 90,
                "scheduled_date": base_date + timedelta(days=1, hours=14),
                "status": "confirmed",
                "priority": "normal",
                "assigned_technician": "Carlos Rodriguez",
                "assigned_team": "hvac_team",
                "customer_notes": "VIP customer - preferred time is afternoon",
                "lead_source": "referral",
                "agent_id": agent_sarah.id if agent_sarah else None
            },
            {
                "customer_name": "Mike Davis",
                "customer_phone": "(555) 456-7890",
                "customer_address": "789 Elm Drive, McKinney, TX 75070",
                "service_type": "electrical",
                "appointment_type": "installation",
                "service_description": "Ceiling fan installation in master bedroom",
                "estimated_duration": 240,
                "scheduled_date": base_date + timedelta(days=2, hours=9),
                "status": "pending",
                "priority": "normal",
                "assigned_team": "electrical_team",
                "customer_notes": "Customer will provide the ceiling fan",
                "lead_source": "angi",
                "agent_id": agent_sarah.id if agent_sarah else None
            },
            {
                "customer_name": "Lisa Wilson",
                "customer_phone": "(555) 321-0987",
                "customer_email": "lisa.w@email.com",
                "customer_address": "321 Maple Court, Frisco, TX 75034",
                "service_type": "plumbing",
                "appointment_type": "emergency",
                "service_description": "Water heater leak - emergency service required",
                "estimated_duration": 180,
                "scheduled_date": base_date + timedelta(days=2, hours=11, minutes=30),
                "status": "urgent",
                "priority": "urgent",
                "assigned_technician": "Emergency Team",
                "assigned_team": "emergency_team",
                "customer_notes": "Water damage prevention critical",
                "lead_source": "phone",
                "agent_id": agent_sarah.id if agent_sarah else None
            }
        ]

        for appointment_data in appointments:
            appointment = Appointment(**appointment_data)
            db.add(appointment)

        db.commit()
        print("✅ Appointments seeded")
    except Exception as e:
        print(f"❌ Error seeding appointments: {e}")
        db.rollback()
    finally:
        db.close()

def seed_leads():
    """Create sample leads"""
    db = SessionLocal()
    try:
        base_date = datetime.now()
        leads = [
            {
                "name": "Jennifer Clark",
                "email": "jennifer.clark@email.com",
                "phone": "(555) 111-2222",
                "company": None,
                "source": "website",
                "status": "new",
                "priority": "medium",
                "notes": "Interested in HVAC installation for new home",
                "lead_data": {
                    "service_interest": "hvac_installation",
                    "property_type": "single_family",
                    "timeline": "within_month",
                    "budget_range": "5000-10000"
                }
            },
            {
                "name": "Robert Martinez",
                "email": "r.martinez@email.com",
                "phone": "(555) 333-4444",
                "company": None,
                "source": "google_ads",
                "status": "contacted",
                "priority": "high",
                "notes": "Emergency plumbing service needed",
                "lead_data": {
                    "service_interest": "emergency_plumbing",
                    "urgency": "immediate",
                    "issue_description": "burst pipe in basement"
                }
            }
        ]

        for lead_data in leads:
            lead = Lead(**lead_data)
            db.add(lead)

        db.commit()
        print("✅ Leads seeded")
    except Exception as e:
        print(f"❌ Error seeding leads: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Run all seeding functions"""
    print("🌱 Starting database seeding for Hatch-inspired AI Lead Management System...")

    # Create tables first
    create_tables()

    # Seed data in order (considering dependencies)
    seed_business_profiles()
    seed_faqs()
    seed_appointment_types()
    seed_agents()
    seed_appointments()
    seed_leads()

    print("\n🎉 Database seeding completed successfully!")
    print("🚀 Your AI Lead Management System is ready with realistic home services data.")

if __name__ == "__main__":
    main()