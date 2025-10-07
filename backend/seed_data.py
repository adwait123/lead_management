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

    # Sample data - Yelp Request a Quote style home service leads
    names = [
        "Sarah Chen", "Mike Rodriguez", "Emily Johnson", "David Kim", "Jessica Williams",
        "Alex Thompson", "Maria Garcia", "James Wilson", "Ashley Brown", "Chris Lee",
        "Amanda Davis", "Kevin Martinez", "Lisa Anderson", "Ryan Taylor", "Nicole White",
        "Brandon Hall", "Stephanie Moore", "Daniel Jackson", "Melissa Clark", "Justin Lewis",
        "Robert Brown", "Jennifer Miller", "Michael Davis", "Karen Wilson", "Steven Garcia",
        "Linda Martinez", "William Anderson", "Patricia Taylor", "Richard Thomas", "Mary Jackson"
    ]

    # Home addresses instead of companies for residential leads
    addresses = [
        "1425 Oak Street, San Francisco, CA 94102", "892 Pine Avenue, Los Angeles, CA 90210",
        "567 Elm Drive, San Diego, CA 92101", "234 Maple Lane, Sacramento, CA 95814",
        "789 Cedar Court, Fresno, CA 93701", "456 Birch Way, Oakland, CA 94601",
        "123 Willow Street, San Jose, CA 95110", "678 Ash Boulevard, Long Beach, CA 90802",
        "345 Spruce Road, Bakersfield, CA 93301", "901 Fir Avenue, Anaheim, CA 92801",
        "112 Cherry Lane, Santa Ana, CA 92701", "223 Walnut Drive, Riverside, CA 92501",
        "334 Hickory Court, Stockton, CA 95202", "445 Poplar Street, Irvine, CA 92602",
        "556 Sycamore Way, Fremont, CA 94536", "667 Magnolia Road, San Bernardino, CA 92401",
        "778 Dogwood Lane, Modesto, CA 95350", "889 Redwood Avenue, Oxnard, CA 93030",
        "990 Palm Drive, Fontana, CA 92335", "111 Cypress Court, Moreno Valley, CA 92553",
        "222 Juniper Street, Huntington Beach, CA 92648", "333 Laurel Way, Glendale, CA 91201",
        "444 Olive Boulevard, Santa Clarita, CA 91350", "555 Peach Lane, Fullerton, CA 92831",
        "666 Plum Road, Thousand Oaks, CA 91360", "777 Lemon Avenue, Visalia, CA 93277",
        "888 Orange Drive, Concord, CA 94518", "999 Apple Court, Simi Valley, CA 93063",
        "101 Grape Street, Vallejo, CA 94590", "202 Berry Lane, Victorville, CA 92392"
    ]

    # Home service categories
    services = [
        "Plumbing Repair", "HVAC Installation", "Electrical Work", "Roofing Repair", "Kitchen Remodel",
        "Bathroom Renovation", "Flooring Installation", "Painting (Interior)", "Painting (Exterior)",
        "Landscaping", "Tree Removal", "Fence Installation", "Deck Building", "Garage Door Repair",
        "Window Replacement", "Gutter Cleaning", "Carpet Cleaning", "House Cleaning", "Pest Control",
        "Pool Maintenance", "Driveway Repair", "Concrete Work", "Tile Installation", "Hardwood Refinishing",
        "Appliance Repair", "Water Heater Installation", "Solar Panel Installation", "Security System Install",
        "Basement Waterproofing", "Chimney Cleaning"
    ]

    sources = ["Yelp", "Yelp", "Yelp", "Yelp", "Angie's List", "HomeAdvisor", "Thumbtack", "Google Local", "Nextdoor"]  # More Yelp leads
    statuses = ["new", "contacted", "qualified", "won", "lost"]

    # Note templates
    note_templates = [
        "Responded to Yelp quote request within 30 minutes. Very responsive homeowner.",
        "Scheduled in-home estimate for next Tuesday at 2 PM.",
        "Homeowner comparing quotes from 3 contractors. Emphasized our 5-star Yelp rating.",
        "Follow-up call scheduled to discuss project timeline and budget details.",
        "Homeowner mentioned they found us through Yelp reviews. Great referral source!",
        "Sent detailed estimate via email. Waiting for their decision by Friday.",
        "Project approved! Scheduling work to begin next month.",
        "Homeowner wants to add additional scope to original Yelp request.",
        "Left voicemail with project details. Yelp leads are very active.",
        "Competitor comparison requested. Highlighted our local expertise and licensing."
    ]

    # Interaction templates
    interaction_templates = [
        {
            "type": "yelp_response",
            "content": "Responded to Yelp quote request with initial pricing and availability.",
        },
        {
            "type": "phone_call",
            "content": "Called homeowner to discuss project details and schedule estimate.",
        },
        {
            "type": "estimate_visit",
            "content": "Conducted in-home estimate and provided detailed quote.",
        },
        {
            "type": "follow_up_email",
            "content": "Follow-up email with written estimate and project timeline.",
        },
        {
            "type": "contract_discussion",
            "content": "Discussed contract terms and project start date with homeowner.",
        },
        {
            "type": "yelp_message",
            "content": "Exchanged messages through Yelp platform to clarify project scope.",
        }
    ]

    session = Session()

    try:
        # Clear existing data
        session.query(Lead).delete()
        session.commit()

        leads = []

        for i in range(len(names)):
            # Create realistic email for homeowner
            name_parts = names[i].lower().split()
            email_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com"]
            email = f"{name_parts[0]}.{name_parts[1]}@{random.choice(email_domains)}"

            # Generate phone number
            phone = f"+1 ({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"

            # Random status with realistic distribution for home service quotes
            status_weights = [0.4, 0.3, 0.15, 0.1, 0.05]  # More new/contacted for quote requests
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
                    "agent_id": random.randint(1, 5),
                    "agent_name": random.choice(["Yelp Quote Specialist", "HomeAdvisor Pro Assistant", "Follow-up Champion", "Support Hero", "Demo Scheduler"])
                })
                interactions.append(interaction)

            # Create lead
            lead = Lead(
                name=names[i],
                email=email,
                phone=phone,
                company=addresses[i],  # Using address field for home address
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