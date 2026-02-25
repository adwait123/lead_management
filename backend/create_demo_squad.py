"""
Seed script: Create the Torkin Pest Control inbound call squad.
Run: python create_demo_squad.py
"""
from models.database import SessionLocal, create_tables
from models.squad import Squad
from models.agent import Agent


ROUTER_PROMPT = """\
You are Mike, a friendly greeter for Torkin Pest Control.

GOAL: Greet the caller, determine if they are a new or existing customer, and classify their intent.

RULES:
- Introduce yourself once: "Hello, thank you for calling Torkin Pest Control. This is Mike, how can I help you today?"
- Ask for the caller's name and phone number.
- Determine intent: new service, existing job inquiry, billing, or complaint.
- Once intent is clear, hand off to the correct agent using the handoff_to_agent tool.
- For billing questions, set target_agent_key to "billing_transfer" — this triggers a deterministic hard transfer.
- Keep responses short (1-2 sentences). Do NOT attempt to answer service questions yourself.

CONTEXT VARIABLES TO COLLECT:
- customer_name, customer_type (new/existing), intent, phone, address (if mentioned)
"""

BOOKING_PROMPT = """\
You are continuing a call with {customer_name} at Torkin Pest Control. Do NOT re-introduce yourself. Continue naturally.

GOAL: Help the caller book a new pest control service appointment.

STEPS:
1. Confirm or collect the service address.
2. Ask about the pest type and urgency.
3. Use generate_appointment_slots to check availability.
4. Present 2-3 best options conversationally (day, time, technician).
5. Once the caller picks a slot, say "Perfect, let me confirm that booking for you." Then STOP — call book_appointment and wait for the result.
6. Read back ONLY what the tool returns: confirmation number, date/time, technician name, and cost.
7. If no slots work, use raise_callback_request to schedule a manager callback.

RULES:
- NEVER invent or guess confirmation numbers, technician names, or prices. Only read back what the tool returns.
- Do NOT say "Your confirmation is..." or name a technician before the tool result arrives.
- If the caller changes intent mid-conversation (mentions existing booking, payment, or complaint), hand off immediately.
- Keep responses conversational and concise.
"""

JOB_INQUIRY_PROMPT = """\
You are continuing a call with {customer_name} at Torkin Pest Control. Do NOT re-introduce yourself. Continue naturally.

GOAL: Help the caller check on an existing pest control job or service.

STEPS:
1. IMMEDIATELY call confirm_lead_details in your very first response — do not wait for more information.
2. Share what the tool returns: job number, service type, last treatment date, next scheduled visit, technician name.
3. Answer follow-up questions about the job status.
4. If the caller needs to reschedule, hand off to the booking agent.
5. If the caller expresses any dissatisfaction or complaint, hand off to the complaint agent.

RULES:
- ALWAYS call confirm_lead_details first, even if you only have a name/phone — never skip this step.
- Only share details the tool returns.
- Do NOT escalate directly — send complaints to the complaint agent first.
- Keep responses concise and helpful.
"""

COMPLAINT_PROMPT = """\
You are continuing a call with {customer_name} at Torkin Pest Control. Do NOT re-introduce yourself. Continue naturally.

GOAL: Handle the caller's complaint with empathy, following the mandatory compliance protocol.

PROTOCOL:
1. FIRST EXCHANGE: Acknowledge and sincerely apologize. "I'm really sorry to hear about that experience. That's not the standard we hold ourselves to."
2. Ask the caller to describe the issue in detail. Listen actively.
3. SECOND EXCHANGE: Attempt resolution — offer to reschedule, send a different technician, or provide a service credit.
4. If the caller is still unsatisfied after 2 exchanges, you MUST escalate. Use transfer_to_team with department="management".
5. When transferring, say: "I completely understand your frustration. Let me connect you with our management team right away."

RULES:
- NEVER argue, deflect, or minimize the complaint.
- ALWAYS apologize in the first response.
- After 2 exchanges, ALWAYS escalate — do not continue trying to resolve.
- You may ONLY use transfer_to_team with department="management".
"""


def create_demo_squad():
    """Create the Torkin Pest Control inbound call squad"""
    create_tables()
    db = SessionLocal()

    try:
        # Check if squad already exists — update in place rather than skipping
        existing = db.query(Squad).filter(Squad.name == "Torkin Pest Control Inbound Squad").first()

        agents_config = [
            {
                "key": "router",
                "name": "Router Agent",
                "prompt": ROUTER_PROMPT,
                "tools": [],
                "allowed_handoffs": ["booking", "job_inquiry", "complaint"],
                "deterministic_routes": {
                    "billing_transfer": {
                        "action": "transfer_to_team",
                        "department": "billing",
                        "reason": "Caller requested billing assistance"
                    }
                },
                "context_input": [],
                "context_output": ["customer_name", "customer_type", "intent", "phone", "address"],
                "max_turns": 6
            },
            {
                "key": "booking",
                "name": "Booking Agent",
                "prompt": BOOKING_PROMPT,
                "tools": ["generate_appointment_slots", "book_appointment", "raise_callback_request"],
                "allowed_handoffs": ["router", "complaint", "job_inquiry"],
                "deterministic_routes": {},
                "context_input": ["customer_name", "phone", "customer_type", "address"],
                "context_output": ["appointment_id", "appointment_date", "technician"],
                "max_turns": 15
            },
            {
                "key": "job_inquiry",
                "name": "Job Inquiry Agent",
                "prompt": JOB_INQUIRY_PROMPT,
                "tools": ["confirm_lead_details"],
                "allowed_handoffs": ["router", "booking", "complaint"],
                "deterministic_routes": {},
                "context_input": ["customer_name", "phone", "address"],
                "context_output": ["job_id", "job_status", "next_visit"],
                "max_turns": 10
            },
            {
                "key": "complaint",
                "name": "Complaint Agent",
                "prompt": COMPLAINT_PROMPT,
                "tools": ["transfer_to_team"],
                "allowed_handoffs": [],
                "deterministic_routes": {},
                "context_input": ["customer_name", "phone", "complaint_summary"],
                "context_output": ["escalation_status", "resolution"],
                "max_turns": 6
            }
        ]
        routing_config = {
            "deterministic_intents": {
                "billing": {
                    "action": "transfer_to_team",
                    "department": "billing",
                    "reason": "Billing inquiry — hard transfer, no LLM"
                }
            },
            "fallback_agent": "router",
            "max_total_handoffs": 5
        }
        shared_context_schema = {
            "customer_name": "string",
            "customer_type": "string",
            "intent": "string",
            "phone": "string",
            "address": "string",
            "complaint_summary": "string",
            "job_id": "string",
            "appointment_id": "string"
        }

        if existing:
            # Update prompts and config in place so re-running picks up changes
            existing.agents = agents_config
            existing.routing_config = routing_config
            existing.shared_context_schema = shared_context_schema
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(existing, 'agents')
            flag_modified(existing, 'routing_config')
            flag_modified(existing, 'shared_context_schema')
            db.commit()
            db.refresh(existing)
            squad = existing
            print(f"Updated squad: {squad.name} (ID: {squad.id})")
        else:
            squad = Squad(
                name="Torkin Pest Control Inbound Squad",
                description="Multi-agent squad for handling inbound pest control calls. Routes between greeting, booking, job inquiry, and complaint agents based on caller intent.",
                is_active=True,
                entry_agent_key="router",
                agents=agents_config,
                routing_config=routing_config,
                shared_context_schema=shared_context_schema,
            )
            db.add(squad)
            db.commit()
            db.refresh(squad)
            print(f"Created squad: {squad.name} (ID: {squad.id})")

        print(f"  Entry agent: {squad.entry_agent_key}")
        print(f"  Agents: {[a['key'] for a in squad.agents]}")

        # Link the active inbound agent to this squad (if one exists)
        inbound_agent = db.query(Agent).filter(
            Agent.type == "inbound",
            Agent.is_active == True
        ).first()

        if inbound_agent:
            inbound_agent.squad_id = squad.id
            db.commit()
            print(f"  Linked inbound agent '{inbound_agent.name}' (ID: {inbound_agent.id}) to squad")
        else:
            print("  No active inbound agent found to link. Create one first with create_inbound_agent.py")

        return squad.id

    finally:
        db.close()


if __name__ == "__main__":
    squad_id = create_demo_squad()
    print(f"\nDone. Squad ID: {squad_id}")
