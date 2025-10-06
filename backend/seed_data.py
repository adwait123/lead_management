"""
Seed data script for AI Lead Management system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from models.database import engine, create_tables
from models.lead import Lead
import random

# Create session
Session = sessionmaker(bind=engine)

def create_realistic_leads():
    """Create realistic lead data for demo purposes"""

    # Sample data
    names = [
        "Sarah Chen", "Mike Rodriguez", "Emily Johnson", "David Kim", "Jessica Williams",
        "Alex Thompson", "Maria Garcia", "James Wilson", "Ashley Brown", "Chris Lee",
        "Amanda Davis", "Kevin Martinez", "Lisa Anderson", "Ryan Taylor", "Nicole White",
        "Brandon Hall", "Stephanie Moore", "Daniel Jackson", "Melissa Clark", "Justin Lewis"
    ]

    companies = [
        "TechStart Inc", "Growth Co", "Innovate Labs", "Digital Solutions", "NextGen Systems",
        "CloudFirst", "DataDriven LLC", "ScaleUp Corp", "AgileWorks", "BrightFuture Co",
        "SmartBiz Solutions", "ProActive Systems", "VelocityTech", "OptimalFlow", "PeakPerformance",
        "EliteServices", "PrecisionCorp", "DynamicEdge", "QuantumLeap", "SynergyPro"
    ]

    services = [
        "CRM Implementation", "Digital Marketing", "Web Development", "Cloud Migration",
        "Data Analytics", "Mobile App Development", "SEO Optimization", "Social Media Management",
        "E-commerce Development", "Business Automation", "AI Integration", "Cybersecurity Audit",
        "Software Consulting", "System Integration", "User Experience Design"
    ]

    sources = ["Facebook Ads", "Google Ads", "Website", "Referral", "LinkedIn", "Email Campaign"]
    statuses = ["new", "contacted", "qualified", "won", "lost"]

    # Note templates
    note_templates = [
        "Initial contact made via phone. Very interested in our services.",
        "Sent proposal document. Waiting for review meeting.",
        "Had a great discovery call. They need implementation by Q1.",
        "Follow-up scheduled for next week to discuss budget.",
        "Decision maker will be back from vacation next Monday.",
        "Competitor comparison requested. Sent detailed feature matrix.",
        "Technical demo scheduled for Friday 2 PM.",
        "Budget approved! Moving to contract negotiation.",
        "Requested additional references from similar industry clients.",
        "Project timeline discussed. They prefer phased approach."
    ]

    # Interaction templates
    interaction_templates = [
        {
            "type": "email",
            "content": "Sent welcome email with company overview and next steps.",
        },
        {
            "type": "call",
            "content": "15-minute discovery call to understand their business needs.",
        },
        {
            "type": "demo",
            "content": "Product demonstration focusing on their key requirements.",
        },
        {
            "type": "follow_up",
            "content": "Follow-up email with proposal and pricing information.",
        },
        {
            "type": "meeting",
            "content": "In-person meeting with decision makers to discuss implementation.",
        }
    ]

    session = Session()

    try:
        # Clear existing data
        session.query(Lead).delete()
        session.commit()

        leads = []

        for i in range(len(names)):
            # Create realistic email
            name_parts = names[i].lower().split()
            email = f"{name_parts[0]}.{name_parts[1]}@{companies[i].lower().replace(' ', '').replace(',', '').replace('inc', '').replace('llc', '').replace('corp', '').replace('co', '')}{'tech' if len(companies[i].replace(' ', '')) < 8 else ''}.com"

            # Generate phone number
            phone = f"+1 ({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"

            # Random status with realistic distribution
            status_weights = [0.3, 0.25, 0.2, 0.15, 0.1]  # More new/contacted leads
            status = random.choices(statuses, weights=status_weights)[0]

            # Random dates (last 30 days)
            created_days_ago = random.randint(0, 30)
            created_at = datetime.utcnow() - timedelta(days=created_days_ago)
            updated_at = created_at + timedelta(days=random.randint(0, created_days_ago))

            # Generate notes based on status
            notes = []
            note_count = random.randint(1, 4)
            for j in range(note_count):
                note_date = created_at + timedelta(days=j, hours=random.randint(1, 23))
                notes.append({
                    "id": j + 1,
                    "content": random.choice(note_templates),
                    "timestamp": note_date.isoformat(),
                    "author": random.choice(["Sarah Thompson", "Mike Chen", "Lisa Rodriguez", "System"])
                })

            # Generate interaction history
            interactions = []
            interaction_count = random.randint(2, 6)
            for j in range(interaction_count):
                interaction_date = created_at + timedelta(days=j, hours=random.randint(1, 23))
                interaction = random.choice(interaction_templates).copy()
                interaction.update({
                    "id": j + 1,
                    "timestamp": interaction_date.isoformat(),
                    "agent_id": random.randint(1, 3),
                    "agent_name": random.choice(["Sales Bot", "Support Agent", "Lead Qualifier"])
                })
                interactions.append(interaction)

            # Create lead
            lead = Lead(
                name=names[i],
                email=email,
                phone=phone,
                company=companies[i],
                service_requested=random.choice(services),
                status=status,
                source=random.choice(sources),
                created_at=created_at,
                updated_at=updated_at,
                notes=notes,
                interaction_history=interactions
            )

            leads.append(lead)
            session.add(lead)

        session.commit()
        print(f"✅ Successfully created {len(leads)} realistic leads!")

        # Print some stats
        for status in statuses:
            count = len([l for l in leads if l.status == status])
            print(f"   {status.title()}: {count} leads")

        return leads

    except Exception as e:
        session.rollback()
        print(f"❌ Error creating seed data: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("🌱 Creating database tables...")
    create_tables()

    print("🌱 Seeding database with realistic lead data...")
    leads = create_realistic_leads()

    print("🎉 Database seeding completed!")
    print(f"💡 You can now test the API at http://localhost:8000/api/leads/")
    print(f"📚 API documentation available at http://localhost:8000/docs")