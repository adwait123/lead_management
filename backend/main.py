"""
AI Lead Management Tool - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import models and database
from models.database import create_tables, SessionLocal
from api.leads import router as leads_router
from api.agents import router as agents_router
from api.agent_sessions import router as agent_sessions_router
from api.workflows import router as workflows_router
from api.messages import router as messages_router
from api.agent_internals import router as agent_internals_router
from api.prompt_templates import router as prompt_templates_router
from api.knowledge_base import router as knowledge_base_router
from api.webhooks import router as webhooks_router
from api.follow_up_testing import router as follow_up_testing_router
from api.calls import router as calls_router
from api.inbound_calls import router as inbound_calls_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="AI Lead Management API",
    description="Backend API for AI-powered lead management system",
    version="1.0.0"
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,https://lead-management-staging-frontend.onrender.com").split(",")

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

    # Start background follow-up processor
    logger = logging.getLogger(__name__)
    logger.info("Starting background follow-up task processor...")

    try:
        from services.follow_up_scheduler import FollowUpScheduler

        # Create a background task for the follow-up processor
        async def run_follow_up_processor():
            """Background task to process follow-up tasks"""
            db = SessionLocal()
            try:
                scheduler = FollowUpScheduler(db)
                await scheduler.start_background_processor(check_interval_seconds=60)
            except Exception as e:
                logger.error(f"Error in follow-up processor: {str(e)}")
            finally:
                db.close()

        # Start the background processor as a fire-and-forget task
        asyncio.create_task(run_follow_up_processor())
        logger.info("Background follow-up processor started successfully")

    except Exception as e:
        logger.error(f"Failed to start background follow-up processor: {str(e)}")

    # Start inbound calling agent worker in a background thread
    logger.info("Starting inbound calling agent worker in background thread...")
    try:
        import threading
        import sys
        agent_path = os.path.join(os.path.dirname(__file__), "agent", "src")
        sys.path.insert(0, agent_path)
        from agent import entrypoint
        from livekit import agents

        def run_agent_worker_in_thread():
            """Function to run the agent worker in a separate thread."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def run_worker():
                """Coroutine to run the agent worker."""
                try:
                    logger.info("Connecting to LiveKit as inbound agent...")
                    worker_opts = agents.WorkerOptions(
                        entrypoint_fnc=entrypoint,
                        agent_name="inbound_raq"  # Agent name for identification
                    )
                    worker = agents.Worker(worker_opts)
                    await worker.run()
                except Exception as e:
                    logger.error(f"Error in agent worker thread: {str(e)}")

            loop.run_until_complete(run_worker())

        # Create and start the background thread
        agent_thread = threading.Thread(target=run_agent_worker_in_thread, daemon=True)
        agent_thread.start()
        logger.info("Inbound calling agent worker thread started successfully.")

    except Exception as e:
        logger.error(f"Failed to start inbound calling agent worker thread: {str(e)}")

# Include API routers
app.include_router(leads_router)
app.include_router(agents_router)
app.include_router(agent_sessions_router)
app.include_router(workflows_router)
app.include_router(messages_router)
app.include_router(agent_internals_router)
app.include_router(prompt_templates_router)
app.include_router(knowledge_base_router)
app.include_router(webhooks_router)
app.include_router(follow_up_testing_router)
app.include_router(calls_router)
app.include_router(inbound_calls_router)


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