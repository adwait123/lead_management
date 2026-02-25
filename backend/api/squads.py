"""
Squad API endpoints for multi-agent orchestration configuration
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

from models.database import get_db
from models.squad import Squad

router = APIRouter(prefix="/api/squads", tags=["squads"])


# --- Pydantic Schemas ---

class SquadAgentSchema(BaseModel):
    key: str
    name: str
    prompt: str
    tools: List[str] = []
    allowed_handoffs: List[str] = []
    deterministic_routes: Dict[str, Any] = {}
    context_input: List[str] = []
    context_output: List[str] = []
    max_turns: int = 10


class SquadCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    agents: List[Dict[str, Any]] = []
    routing_config: Dict[str, Any] = {}
    shared_context_schema: Dict[str, Any] = {}
    entry_agent_key: str = "router"


class SquadUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    agents: Optional[List[Dict[str, Any]]] = None
    routing_config: Optional[Dict[str, Any]] = None
    shared_context_schema: Optional[Dict[str, Any]] = None
    entry_agent_key: Optional[str] = None


class SquadResponseSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    agents: List[Dict[str, Any]]
    routing_config: Dict[str, Any]
    shared_context_schema: Dict[str, Any]
    entry_agent_key: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SquadListResponseSchema(BaseModel):
    squads: List[SquadResponseSchema]
    total: int
    page: int
    per_page: int
    total_pages: int


# --- Endpoints ---

@router.get("/", response_model=SquadListResponseSchema)
async def get_squads(
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all squads with optional filtering"""
    query = db.query(Squad)

    if is_active is not None:
        query = query.filter(Squad.is_active == is_active)
    if search:
        query = query.filter(Squad.name.ilike(f"%{search}%"))

    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    squads = query.order_by(Squad.updated_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "squads": squads,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }


@router.get("/{squad_id}", response_model=SquadResponseSchema)
async def get_squad(squad_id: int, db: Session = Depends(get_db)):
    """Get a single squad with full agent definitions"""
    squad = db.query(Squad).filter(Squad.id == squad_id).first()
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")
    return squad


@router.post("/", response_model=SquadResponseSchema)
async def create_squad(squad_data: SquadCreateSchema, db: Session = Depends(get_db)):
    """Create a new squad"""
    squad = Squad(
        name=squad_data.name,
        description=squad_data.description,
        is_active=squad_data.is_active,
        agents=squad_data.agents,
        routing_config=squad_data.routing_config,
        shared_context_schema=squad_data.shared_context_schema,
        entry_agent_key=squad_data.entry_agent_key
    )
    db.add(squad)
    db.commit()
    db.refresh(squad)
    return squad


@router.put("/{squad_id}", response_model=SquadResponseSchema)
async def update_squad(squad_id: int, squad_data: SquadUpdateSchema, db: Session = Depends(get_db)):
    """Update an existing squad"""
    squad = db.query(Squad).filter(Squad.id == squad_id).first()
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")

    update_data = squad_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(squad, key, value)

    db.commit()
    db.refresh(squad)
    return squad


@router.delete("/{squad_id}")
async def delete_squad(squad_id: int, db: Session = Depends(get_db)):
    """Delete a squad"""
    squad = db.query(Squad).filter(Squad.id == squad_id).first()
    if not squad:
        raise HTTPException(status_code=404, detail="Squad not found")

    db.delete(squad)
    db.commit()
    return {"message": "Squad deleted successfully"}
