"""
Leads API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List, Dict, Any
import math
import logging
from datetime import datetime
from pydantic import ValidationError

from models.database import get_db
from models.lead import Lead
from models.schemas import (
    LeadCreateSchema,
    LeadUpdateSchema,
    LeadResponseSchema,
    LeadListResponseSchema,
    LeadFiltersSchema,
    NoteCreateSchema,
    ProjectDataSchema
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["leads"])

def create_notes_from_project_data(project_data: ProjectDataSchema) -> List[Dict[str, Any]]:
    """Convert project data to structured notes"""
    notes = []
    note_id = 1

    if project_data.survey_answers:
        # Create survey Q&A note
        qa_content = "Survey Questions & Answers:\n\n"
        for qa in project_data.survey_answers:
            qa_content += f"Q: {qa.question_text}\n"
            qa_content += f"A: {', '.join(qa.answer_text)}\n\n"

        notes.append({
            "id": note_id,
            "content": qa_content,
            "timestamp": datetime.utcnow().isoformat(),
            "author": "system",
            "type": "survey_responses",
            "survey_data": [qa.dict() for qa in project_data.survey_answers]
        })
        note_id += 1

    if project_data.job_names:
        notes.append({
            "id": note_id,
            "content": f"Requested Services: {', '.join(project_data.job_names)}",
            "timestamp": datetime.utcnow().isoformat(),
            "author": "system",
            "type": "services_requested"
        })
        note_id += 1

    if project_data.additional_info:
        notes.append({
            "id": note_id,
            "content": f"Additional Information: {project_data.additional_info}",
            "timestamp": datetime.utcnow().isoformat(),
            "author": "system",
            "type": "project_details"
        })
        note_id += 1

    if project_data.location:
        location_details = []
        if project_data.location.postal_code:
            location_details.append(f"Postal Code: {project_data.location.postal_code}")
        if project_data.location.city:
            location_details.append(f"City: {project_data.location.city}")
        if project_data.location.state:
            location_details.append(f"State: {project_data.location.state}")

        if location_details:
            notes.append({
                "id": note_id,
                "content": f"Project Location: {', '.join(location_details)}",
                "timestamp": datetime.utcnow().isoformat(),
                "author": "system",
                "type": "location"
            })
            note_id += 1

    if project_data.availability:
        avail_content = f"Availability: {project_data.availability.status}"
        if project_data.availability.dates:
            avail_content += f"\nPreferred Dates: {', '.join(project_data.availability.dates)}"

        notes.append({
            "id": note_id,
            "content": avail_content,
            "timestamp": datetime.utcnow().isoformat(),
            "author": "system",
            "type": "availability"
        })
        note_id += 1

    if project_data.attachments:
        attachment_list = []
        for att in project_data.attachments:
            attachment_list.append(f"{att.resource_name} ({att.mime_type})")

        notes.append({
            "id": note_id,
            "content": f"Attachments ({len(project_data.attachments)}): {', '.join(attachment_list)}",
            "timestamp": datetime.utcnow().isoformat(),
            "author": "system",
            "type": "attachments",
            "attachments": [att.dict() for att in project_data.attachments]
        })
        note_id += 1

    if project_data.budget_range:
        notes.append({
            "id": note_id,
            "content": f"Budget Range: {project_data.budget_range}",
            "timestamp": datetime.utcnow().isoformat(),
            "author": "system",
            "type": "budget"
        })
        note_id += 1

    if project_data.timeline:
        notes.append({
            "id": note_id,
            "content": f"Timeline: {project_data.timeline}",
            "timestamp": datetime.utcnow().isoformat(),
            "author": "system",
            "type": "timeline"
        })
        note_id += 1

    return notes

@router.get("/", response_model=LeadListResponseSchema)
async def get_leads(
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all leads with filtering and pagination"""

    # Build query
    query = db.query(Lead)

    # Apply filters
    if status:
        query = query.filter(Lead.status == status)
    if source:
        query = query.filter(Lead.source == source)
    if company:
        query = query.filter(Lead.company.ilike(f"%{company}%"))
    if search:
        query = query.filter(
            or_(
                Lead.name.ilike(f"%{search}%"),
                Lead.email.ilike(f"%{search}%"),
                Lead.company.ilike(f"%{search}%")
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    leads = query.order_by(Lead.created_at.desc()).offset(offset).limit(per_page).all()

    # Calculate total pages
    total_pages = math.ceil(total / per_page)

    # Convert leads to response schema with error handling
    valid_leads = []
    for lead in leads:
        try:
            valid_leads.append(LeadResponseSchema.model_validate(lead))
        except ValidationError as e:
            logger.warning(f"Skipping lead {lead.id} due to validation error: {e}")
            continue

    return LeadListResponseSchema(
        leads=valid_leads,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/{lead_id}", response_model=LeadResponseSchema)
async def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a specific lead by ID"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        return LeadResponseSchema.model_validate(lead)
    except ValidationError as e:
        logger.error(f"Lead {lead_id} has invalid data: {e}")
        raise HTTPException(status_code=422, detail=f"Lead data validation failed: {str(e)}")

@router.post("/", response_model=LeadResponseSchema)
async def create_lead(lead_data: LeadCreateSchema, db: Session = Depends(get_db)):
    """Create a new lead and automatically trigger agent workflows"""

    # Check if email already exists
    existing_lead = db.query(Lead).filter(Lead.email == lead_data.email).first()
    if existing_lead:
        raise HTTPException(status_code=400, detail="Lead with this email already exists")

    # Process project data and create structured notes
    combined_notes = lead_data.notes or []
    if lead_data.project_data:
        project_notes = create_notes_from_project_data(lead_data.project_data)
        # Append project notes to existing notes
        combined_notes.extend(project_notes)

    # Enhance service_requested from project data if not provided
    service_requested = lead_data.service_requested
    if not service_requested and lead_data.project_data and lead_data.project_data.job_names:
        service_requested = ", ".join(lead_data.project_data.job_names)

    # Create new lead
    lead = Lead(
        name=lead_data.name,
        first_name=lead_data.first_name,
        last_name=lead_data.last_name,
        email=lead_data.email,
        phone=lead_data.phone,
        company=lead_data.company,
        address=lead_data.address,
        external_id=lead_data.external_id,
        service_requested=service_requested,
        status=lead_data.status,
        source=lead_data.source,
        notes=combined_notes,
        interaction_history=lead_data.interaction_history or []
    )

    db.add(lead)
    db.commit()
    db.refresh(lead)

    # Trigger agent workflows for new lead
    try:
        from services.workflow_service import WorkflowService
        workflow_service = WorkflowService(db)

        # Create event data for workflow detection
        form_data = {
            "service_requested": service_requested,
            "company": lead_data.company,
            "phone": lead_data.phone,
            "address": lead_data.address
        }

        # Add rich project data to form_data for agent context
        if lead_data.project_data:
            form_data.update({
                "project_data": lead_data.project_data.dict(),
                "platform_metadata": lead_data.platform_metadata
            })

        # Trigger workflow for new lead
        session_ids = workflow_service.handle_lead_created(
            lead_id=lead.id,
            source=lead_data.source,
            form_data=form_data
        )

        if session_ids:
            logger.info(f"Created {len(session_ids)} agent sessions for lead {lead.id}: {session_ids}")
        else:
            logger.info(f"No agent workflows triggered for lead {lead.id}")

    except Exception as e:
        logger.error(f"Failed to trigger workflows for lead {lead.id}: {str(e)}")
        # Don't fail the lead creation if workflow triggering fails

    # Send webhook notification for lead creation
    try:
        import asyncio
        from services.webhook_service import WebhookService
        webhook_service = WebhookService(db)

        # Send webhook asynchronously
        asyncio.create_task(webhook_service.send_lead_created_webhook(lead.id))
        logger.info(f"Scheduled webhook notification for lead {lead.id}")

    except Exception as e:
        logger.error(f"Failed to send webhook for lead {lead.id}: {str(e)}")
        # Don't fail the lead creation if webhook sending fails

    # Trigger outbound call for Torkin leads via web service API
    try:
        if lead_data.source == "torkin" and lead.phone:
            from services.outbound_web_service import OutboundWebService
            from models.agent import Agent
            from models.call import Call

            # Find an active outbound calling agent
            outbound_agent = db.query(Agent).filter(
                Agent.is_active == True,
                Agent.type == "outbound"
            ).first()

            if outbound_agent:
                # Create call record
                call = Call(
                    lead_id=lead.id,
                    agent_id=outbound_agent.id,
                    phone_number=lead.phone,
                    call_status="pending",
                    call_metadata={
                        "lead_source": lead.source,
                        "triggered_by": "lead_creation",
                        "agent_name": outbound_agent.name,
                        "demo_mode": True,
                        "auto_triggered": True,
                        "dispatch_method": "web_service"
                    }
                )

                db.add(call)
                db.commit()
                db.refresh(call)

                # Schedule the call dispatch via web service
                web_service = OutboundWebService(db)
                asyncio.create_task(web_service.dispatch_call(call.id))

                logger.info(f"Scheduled web service outbound call {call.id} for Torkin lead {lead.id}")
            else:
                logger.warning(f"No outbound calling agent found for lead {lead.id}")

    except Exception as e:
        logger.error(f"Failed to trigger outbound call for lead {lead.id}: {str(e)}")
        # Don't fail the lead creation if outbound calling fails

    try:
        return LeadResponseSchema.model_validate(lead)
    except ValidationError as e:
        logger.error(f"Created lead {lead.id} has invalid data: {e}")
        raise HTTPException(status_code=422, detail=f"Lead data validation failed: {str(e)}")

@router.put("/{lead_id}", response_model=LeadResponseSchema)
async def update_lead(lead_id: int, lead_data: LeadUpdateSchema, db: Session = Depends(get_db)):
    """Update an existing lead"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Update only provided fields
    update_data = lead_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)

    try:
        return LeadResponseSchema.model_validate(lead)
    except ValidationError as e:
        logger.error(f"Updated lead {lead_id} has invalid data: {e}")
        raise HTTPException(status_code=422, detail=f"Lead data validation failed: {str(e)}")

@router.delete("/{lead_id}")
async def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    """Delete a lead and all related records safely"""
    from sqlalchemy import text

    # Check if lead exists
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    deletion_summary = {
        "lead_id": lead_id,
        "lead_name": lead.name,
        "deleted_records": {
            "messages": 0,
            "sessions": 0,
            "calls": 0,
            "lead": 0
        },
        "total_deleted": 0
    }

    try:
        # Start transaction
        db.begin()

        # 1. Delete messages first (they reference lead_id)
        messages_result = db.execute(
            text("DELETE FROM messages WHERE lead_id = :lead_id"),
            {"lead_id": lead_id}
        )
        deletion_summary["deleted_records"]["messages"] = messages_result.rowcount

        # 2. Delete agent sessions
        sessions_result = db.execute(
            text("DELETE FROM agent_sessions WHERE lead_id = :lead_id"),
            {"lead_id": lead_id}
        )
        deletion_summary["deleted_records"]["sessions"] = sessions_result.rowcount

        # 3. Delete inbound calls
        calls_result = db.execute(
            text("DELETE FROM inbound_calls WHERE lead_id = :lead_id"),
            {"lead_id": lead_id}
        )
        deletion_summary["deleted_records"]["calls"] = calls_result.rowcount

        # 4. Finally delete the lead itself
        lead_result = db.execute(
            text("DELETE FROM leads WHERE id = :lead_id"),
            {"lead_id": lead_id}
        )
        deletion_summary["deleted_records"]["lead"] = lead_result.rowcount

        # Calculate total deleted records
        deletion_summary["total_deleted"] = sum(deletion_summary["deleted_records"].values())

        # Commit transaction
        db.commit()

        return {
            "message": "Lead deleted successfully",
            "summary": deletion_summary
        }

    except Exception as e:
        # Rollback on error
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete lead: {str(e)}"
        )

@router.post("/{lead_id}/notes")
async def add_note(lead_id: int, note_data: NoteCreateSchema, db: Session = Depends(get_db)):
    """Add a note to a lead"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Get existing notes or initialize empty list
    notes = lead.notes or []

    # Create new note
    new_note = {
        "id": len(notes) + 1,
        "content": note_data.content,
        "timestamp": datetime.utcnow().isoformat(),
        "author": note_data.author
    }

    notes.append(new_note)
    lead.notes = notes

    db.commit()
    db.refresh(lead)

    return {"message": "Note added successfully", "note": new_note}

@router.get("/{lead_id}/interactions")
async def get_lead_interactions(lead_id: int, db: Session = Depends(get_db)):
    """Get all interactions for a lead"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {"interactions": lead.interaction_history or []}

# Lead statistics endpoints
@router.get("/stats/overview")
async def get_lead_stats(db: Session = Depends(get_db)):
    """Get lead statistics overview"""
    total_leads = db.query(Lead).count()
    active_leads = db.query(Lead).filter(Lead.status.in_(["new", "contacted", "qualified"])).count()
    won_leads = db.query(Lead).filter(Lead.status == "won").count()

    conversion_rate = (won_leads / total_leads * 100) if total_leads > 0 else 0

    return {
        "total_leads": total_leads,
        "active_leads": active_leads,
        "won_leads": won_leads,
        "conversion_rate": round(conversion_rate, 1)
    }

@router.get("/stats/by-source")
async def get_leads_by_source(db: Session = Depends(get_db)):
    """Get lead count by source"""
    from sqlalchemy import func

    results = db.query(
        Lead.source,
        func.count(Lead.id).label("count")
    ).group_by(Lead.source).all()

    return [{"source": result.source, "count": result.count} for result in results]

@router.get("/stats/by-status")
async def get_leads_by_status(db: Session = Depends(get_db)):
    """Get lead count by status"""
    from sqlalchemy import func

    results = db.query(
        Lead.status,
        func.count(Lead.id).label("count")
    ).group_by(Lead.status).all()

    return [{"status": result.status, "count": result.count} for result in results]