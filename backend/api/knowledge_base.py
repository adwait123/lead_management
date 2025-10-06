from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from models.database import get_db
from models.agent import Agent
import json

router = APIRouter(prefix="/api", tags=["knowledge-base"])

# Pydantic models for knowledge base items
class KnowledgeBaseItem(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    category: str
    tags: List[str] = []
    enabled: bool = True

class KnowledgeBaseItemCreate(BaseModel):
    title: str
    content: str
    category: str
    tags: List[str] = []
    enabled: bool = True

class KnowledgeBaseItemUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    enabled: Optional[bool] = None

@router.get("/agents/{agent_id}/knowledge", response_model=List[KnowledgeBaseItem])
def get_agent_knowledge(agent_id: int, db: Session = Depends(get_db)):
    """Get all knowledge base items for an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Parse the knowledge JSON field
    knowledge_items = []
    if agent.knowledge:
        try:
            knowledge_data = json.loads(agent.knowledge) if isinstance(agent.knowledge, str) else agent.knowledge
            if isinstance(knowledge_data, list):
                knowledge_items = knowledge_data
        except json.JSONDecodeError:
            # If parsing fails, return empty list
            pass

    return knowledge_items

@router.post("/agents/{agent_id}/knowledge", response_model=KnowledgeBaseItem)
def create_knowledge_item(
    agent_id: int,
    item: KnowledgeBaseItemCreate,
    db: Session = Depends(get_db)
):
    """Create a new knowledge base item for an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Parse existing knowledge
    knowledge_items = []
    if agent.knowledge:
        try:
            knowledge_data = json.loads(agent.knowledge) if isinstance(agent.knowledge, str) else agent.knowledge
            if isinstance(knowledge_data, list):
                knowledge_items = knowledge_data
        except json.JSONDecodeError:
            knowledge_items = []

    # Generate new ID
    import uuid
    new_item = {
        "id": str(uuid.uuid4()),
        "title": item.title,
        "content": item.content,
        "category": item.category,
        "tags": item.tags,
        "enabled": item.enabled
    }

    # Add new item
    knowledge_items.append(new_item)

    # Update agent
    agent.knowledge = json.dumps(knowledge_items)
    db.commit()
    db.refresh(agent)

    return KnowledgeBaseItem(**new_item)

@router.get("/agents/{agent_id}/knowledge/search")
def search_knowledge(
    agent_id: int,
    q: str = "",
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Search knowledge base items"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    knowledge_items = []
    if agent.knowledge:
        try:
            knowledge_data = json.loads(agent.knowledge) if isinstance(agent.knowledge, str) else agent.knowledge
            if isinstance(knowledge_data, list):
                knowledge_items = knowledge_data
        except json.JSONDecodeError:
            pass

    # Filter items
    filtered_items = []
    for item in knowledge_items:
        # Skip disabled items
        if not item.get("enabled", True):
            continue

        # Category filter
        if category and item.get("category") != category:
            continue

        # Search query
        if q:
            search_text = f"{item.get('title', '')} {item.get('content', '')} {' '.join(item.get('tags', []))}"
            if q.lower() not in search_text.lower():
                continue

        filtered_items.append(item)

    return {"items": filtered_items, "total": len(filtered_items)}

@router.get("/agents/{agent_id}/knowledge/categories")
def get_knowledge_categories(agent_id: int, db: Session = Depends(get_db)):
    """Get all unique categories for an agent's knowledge base"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    categories = set()
    if agent.knowledge:
        try:
            knowledge_data = json.loads(agent.knowledge) if isinstance(agent.knowledge, str) else agent.knowledge
            if isinstance(knowledge_data, list):
                for item in knowledge_data:
                    if item.get("category"):
                        categories.add(item["category"])
        except json.JSONDecodeError:
            pass

    return {"categories": sorted(list(categories))}

@router.get("/agents/{agent_id}/knowledge/{item_id}", response_model=KnowledgeBaseItem)
def get_knowledge_item(agent_id: int, item_id: str, db: Session = Depends(get_db)):
    """Get a specific knowledge base item"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Parse knowledge and find item
    if agent.knowledge:
        try:
            knowledge_data = json.loads(agent.knowledge) if isinstance(agent.knowledge, str) else agent.knowledge
            if isinstance(knowledge_data, list):
                for item in knowledge_data:
                    if item.get("id") == item_id:
                        return KnowledgeBaseItem(**item)
        except json.JSONDecodeError:
            pass

    raise HTTPException(status_code=404, detail="Knowledge item not found")

@router.put("/agents/{agent_id}/knowledge/{item_id}", response_model=KnowledgeBaseItem)
def update_knowledge_item(
    agent_id: int,
    item_id: str,
    item_update: KnowledgeBaseItemUpdate,
    db: Session = Depends(get_db)
):
    """Update a knowledge base item"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Parse knowledge
    knowledge_items = []
    if agent.knowledge:
        try:
            knowledge_data = json.loads(agent.knowledge) if isinstance(agent.knowledge, str) else agent.knowledge
            if isinstance(knowledge_data, list):
                knowledge_items = knowledge_data
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse knowledge data")

    # Find and update item
    item_found = False
    for i, item in enumerate(knowledge_items):
        if item.get("id") == item_id:
            # Update fields that are provided
            if item_update.title is not None:
                item["title"] = item_update.title
            if item_update.content is not None:
                item["content"] = item_update.content
            if item_update.category is not None:
                item["category"] = item_update.category
            if item_update.tags is not None:
                item["tags"] = item_update.tags
            if item_update.enabled is not None:
                item["enabled"] = item_update.enabled

            knowledge_items[i] = item
            item_found = True
            break

    if not item_found:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    # Update agent
    agent.knowledge = json.dumps(knowledge_items)
    db.commit()
    db.refresh(agent)

    # Return updated item
    updated_item = next(item for item in knowledge_items if item.get("id") == item_id)
    return KnowledgeBaseItem(**updated_item)

@router.delete("/agents/{agent_id}/knowledge/{item_id}")
def delete_knowledge_item(agent_id: int, item_id: str, db: Session = Depends(get_db)):
    """Delete a knowledge base item"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Parse knowledge
    knowledge_items = []
    if agent.knowledge:
        try:
            knowledge_data = json.loads(agent.knowledge) if isinstance(agent.knowledge, str) else agent.knowledge
            if isinstance(knowledge_data, list):
                knowledge_items = knowledge_data
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse knowledge data")

    # Remove item
    original_length = len(knowledge_items)
    knowledge_items = [item for item in knowledge_items if item.get("id") != item_id]

    if len(knowledge_items) == original_length:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    # Update agent
    agent.knowledge = json.dumps(knowledge_items)
    db.commit()
    db.refresh(agent)

    return {"message": "Knowledge item deleted successfully"}

