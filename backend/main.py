"""
AI Lead Management Tool - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Import models and database
from models.database import create_tables
from api.leads import router as leads_router
from api.agents import router as agents_router
from api.agent_sessions import router as agent_sessions_router
from api.workflows import router as workflows_router
from api.messages import router as messages_router
from api.agent_internals import router as agent_internals_router
from api.prompt_templates import router as prompt_templates_router
from api.knowledge_base import router as knowledge_base_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="AI Lead Management API",
    description="Backend API for AI-powered lead management system",
    version="1.0.0"
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

# Include API routers
app.include_router(leads_router)
app.include_router(agents_router)
app.include_router(agent_sessions_router)
app.include_router(workflows_router)
app.include_router(messages_router)
app.include_router(agent_internals_router)
app.include_router(prompt_templates_router)
app.include_router(knowledge_base_router)


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "message": "AI Lead Management API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Dashboard endpoints
@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics():
    """Get dashboard metrics"""
    return {
        "total_leads": 47,
        "active_leads": 23,
        "conversion_rate": 31.5,
        "agent_interactions": 127,
        "pending_appointments": 12,
        "emergency_calls": 3,
        "average_response_time": "2.3 minutes"
    }


@app.get("/api/dashboard/recent-leads")
async def get_recent_leads():
    """Get recent leads for dashboard"""
    return [
        {
            "id": 1,
            "name": "Sarah Johnson",
            "property": "1245 Oak Street",
            "status": "new",
            "service_needed": "Plumbing Repair",
            "source": "Google Search",
            "created_at": "2024-10-03T10:30:00Z"
        },
        {
            "id": 2,
            "name": "Mike Rodriguez",
            "property": "567 Pine Avenue",
            "status": "contacted",
            "service_needed": "HVAC Maintenance",
            "source": "Facebook Ads",
            "created_at": "2024-10-03T09:15:00Z"
        },
        {
            "id": 3,
            "name": "Lisa Thompson",
            "property": "890 Maple Drive",
            "status": "scheduled",
            "service_needed": "Electrical Repair",
            "source": "Referral",
            "created_at": "2024-10-03T08:45:00Z"
        }
    ]


@app.get("/api/dashboard/activity")
async def get_recent_activity():
    """Get recent activity feed"""
    return [
        {
            "id": 1,
            "type": "lead_created",
            "message": "New homeowner lead: Sarah Johnson needs plumbing repair",
            "timestamp": "2024-10-03T10:30:00Z"
        },
        {
            "id": 2,
            "type": "agent_interaction",
            "message": "Home Services Bot scheduled HVAC service with Mike Rodriguez",
            "timestamp": "2024-10-03T10:25:00Z"
        },
        {
            "id": 3,
            "type": "appointment_scheduled",
            "message": "Emergency electrical repair scheduled for Lisa Thompson",
            "timestamp": "2024-10-03T10:20:00Z"
        },
        {
            "id": 4,
            "type": "service_completed",
            "message": "Plumbing installation completed at 123 Elm Street",
            "timestamp": "2024-10-03T09:45:00Z"
        }
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)