"""
Leads API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional
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
    NoteCreateSchema
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["leads"])

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
            valid_leads.append(LeadResponseSchema.from_orm(lead))
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
        return LeadResponseSchema.from_orm(lead)
    except ValidationError as e:
        logger.error(f"Lead {lead_id} has invalid data: {e}")
        raise HTTPException(status_code=422, detail=f"Lead data validation failed: {str(e)}")

@router.post("/", response_model=LeadResponseSchema)
async def create_lead(lead_data: LeadCreateSchema, db: Session = Depends(get_db)):
    """Create a new lead"""

    # Check if email already exists
    existing_lead = db.query(Lead).filter(Lead.email == lead_data.email).first()
    if existing_lead:
        raise HTTPException(status_code=400, detail="Lead with this email already exists")

    # Create new lead
    lead = Lead(
        name=lead_data.name,
        email=lead_data.email,
        phone=lead_data.phone,
        company=lead_data.company,
        service_requested=lead_data.service_requested,
        status=lead_data.status,
        source=lead_data.source,
        notes=lead_data.notes or [],
        interaction_history=lead_data.interaction_history or []
    )

    db.add(lead)
    db.commit()
    db.refresh(lead)

    try:
        return LeadResponseSchema.from_orm(lead)
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
        return LeadResponseSchema.from_orm(lead)
    except ValidationError as e:
        logger.error(f"Updated lead {lead_id} has invalid data: {e}")
        raise HTTPException(status_code=422, detail=f"Lead data validation failed: {str(e)}")

@router.delete("/{lead_id}")
async def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    """Delete a lead"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    db.delete(lead)
    db.commit()

    return {"message": "Lead deleted successfully"}

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