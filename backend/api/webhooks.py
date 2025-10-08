"""
Webhook API endpoints for external integrations (Zapier, Yelp, etc.)
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from pydantic import BaseModel
import requests

from models.database import get_db
from models.lead import Lead
from services.workflow_service import WorkflowService

# Configure logging
logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

# Pydantic schemas for webhook payloads
class YelpLeadCreatedWebhook(BaseModel):
    """Schema for Yelp lead creation webhook from Zapier"""
    # Basic lead info
    id: str  # Yelp lead ID
    business_id: str
    conversation_id: str
    time_created: str
    last_event_time: str

    # Temporary contact info
    temporary_email_address: Optional[str] = None
    temporary_email_address_expiry: Optional[str] = None
    temporary_phone_number: Optional[str] = None
    temporary_phone_number_expiry: Optional[str] = None

    # Customer info
    user: Dict[str, Any]  # {"display_name": "Jeremy S."}

    # Project details
    project: Dict[str, Any]  # Rich project data with location, job, survey answers, etc.

class YelpMessageReceivedWebhook(BaseModel):
    """Schema for Yelp message received webhook from Zapier"""
    yelp_lead_id: str  # Maps to external_id in Lead
    conversation_id: str
    message_content: str
    sender: str  # "customer" or "business"
    timestamp: str

class WebhookResponse(BaseModel):
    """Standard webhook response"""
    success: bool
    message: str
    lead_id: Optional[int] = None
    session_ids: Optional[List[int]] = []

@router.post("/zapier/yelp-lead-created", response_model=WebhookResponse)
async def handle_yelp_lead_created(
    webhook_data: YelpLeadCreatedWebhook,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle new Yelp lead creation from Zapier
    Creates lead record and triggers agent workflow
    """
    logger.info(f"Received Yelp lead creation webhook: {webhook_data.id}")

    try:
        # Check if lead already exists
        existing_lead = db.query(Lead).filter(Lead.external_id == webhook_data.id).first()
        if existing_lead:
            logger.warning(f"Lead with external_id {webhook_data.id} already exists")
            return WebhookResponse(
                success=True,
                message=f"Lead {webhook_data.id} already exists",
                lead_id=existing_lead.id
            )

        # Parse customer name
        customer_name = webhook_data.user.get("display_name", "")
        first_name = ""
        last_name = ""
        if customer_name:
            name_parts = customer_name.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        # Extract contact info (prefer temporary contact)
        email = webhook_data.temporary_email_address or ""
        phone = webhook_data.temporary_phone_number or ""

        # Extract project details for notes
        project_details = {
            "yelp_data": {
                "conversation_id": webhook_data.conversation_id,
                "business_id": webhook_data.business_id,
                "time_created": webhook_data.time_created,
                "last_event_time": webhook_data.last_event_time,
                "temporary_contact_expiry": {
                    "email": webhook_data.temporary_email_address_expiry,
                    "phone": webhook_data.temporary_phone_number_expiry
                }
            },
            "project": webhook_data.project
        }

        # Determine service requested from project data
        service_requested = ""
        if "job_names" in webhook_data.project and webhook_data.project["job_names"]:
            service_requested = ", ".join(webhook_data.project["job_names"])

        # Create Lead record
        lead = Lead(
            external_id=webhook_data.id,
            first_name=first_name,
            last_name=last_name,
            name=customer_name,  # Keep full name for backward compatibility
            email=email,
            phone=phone,
            company=None,  # Individual customers from Yelp
            service_requested=service_requested,
            status="new",
            source="yelp",
            notes=[{
                "id": 1,
                "content": f"Yelp lead created: {service_requested}",
                "timestamp": datetime.utcnow().isoformat(),
                "author": "system",
                "type": "yelp_creation",
                "project_details": project_details
            }]
        )

        db.add(lead)
        db.commit()
        db.refresh(lead)

        logger.info(f"Created lead {lead.id} for Yelp lead {webhook_data.id}")

        # Trigger workflow for agent engagement in background
        def trigger_workflow():
            try:
                workflow_service = WorkflowService(db)
                session_ids = workflow_service.handle_lead_created(
                    lead_id=lead.id,
                    source="yelp",
                    form_data=project_details
                )
                logger.info(f"Triggered workflow for lead {lead.id}, created sessions: {session_ids}")
                return session_ids
            except Exception as e:
                logger.error(f"Failed to trigger workflow for lead {lead.id}: {str(e)}")
                return []

        # Add workflow trigger to background tasks
        background_tasks.add_task(trigger_workflow)

        return WebhookResponse(
            success=True,
            message=f"Yelp lead {webhook_data.id} created successfully",
            lead_id=lead.id
        )

    except Exception as e:
        logger.error(f"Error processing Yelp lead webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process Yelp lead: {str(e)}")

@router.post("/zapier/yelp-message-received", response_model=WebhookResponse)
async def handle_yelp_message_received(
    webhook_data: YelpMessageReceivedWebhook,
    db: Session = Depends(get_db)
):
    """
    Handle incoming message from Yelp customer via Zapier
    Routes message to existing agent session or creates new one
    """
    logger.info(f"Received Yelp message for lead {webhook_data.yelp_lead_id}")

    try:
        # Find lead by external_id
        lead = db.query(Lead).filter(Lead.external_id == webhook_data.yelp_lead_id).first()
        if not lead:
            logger.error(f"Lead not found for Yelp ID: {webhook_data.yelp_lead_id}")
            raise HTTPException(status_code=404, detail=f"Lead not found: {webhook_data.yelp_lead_id}")

        # TODO: Route message to MessageRouter service
        # This will be implemented in Phase 4
        logger.info(f"Message routing for lead {lead.id} - to be implemented in Phase 4")

        return WebhookResponse(
            success=True,
            message=f"Message received for lead {lead.id} - routing to be implemented",
            lead_id=lead.id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Yelp message webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.get("/test/yelp-sample")
async def get_yelp_sample_data():
    """
    Return sample Yelp webhook data for testing
    """
    return {
        "yelp_lead_sample": {
            "id": "18kPq7GPye-YQ3LyKyAZPw",
            "business_id": "VXi7gzRqPKp63X0u6fUtbg",
            "conversation_id": "E24Bu-vMhVpueQpU8mpRPw",
            "temporary_email_address": "gbtUf6u0X36pKPqRzg7iXV@messaging.yelp.com",
            "temporary_email_address_expiry": "2022-01-02T03:04:05+00:00",
            "temporary_phone_number": "+14166666666",
            "temporary_phone_number_expiry": "2022-07-06T00:00:00+00:00",
            "time_created": "2022-01-02T03:04:05+00:00",
            "last_event_time": "2022-01-02T04:04:05+00:00",
            "user": {
                "display_name": "Jeremy S."
            },
            "project": {
                "location": {
                    "postal_code": "12345"
                },
                "additional_info": "Moving items out of my storage unit in Louisburg to Red Oak",
                "availability": {
                    "status": "SPECIFIC_DATES",
                    "dates": [
                        "2024-08-01",
                        "2024-08-02",
                        "2024-08-06"
                    ]
                },
                "job_names": [
                    "In-state moving"
                ],
                "survey_answers": [
                    {
                        "question_text": "Where are you moving to?",
                        "question_identifier": "moving_to",
                        "answer_text": [
                            "Red Oak, NC"
                        ]
                    },
                    {
                        "question_text": "What is the size of your move?",
                        "question_identifier": "move_size",
                        "answer_text": [
                            "3 bedroom home"
                        ]
                    },
                    {
                        "question_text": "Do you need items moved up or down floors at your current location? If so, how many floors?",
                        "question_identifier": "current_floors",
                        "answer_text": [
                            "1 floor"
                        ]
                    },
                    {
                        "question_text": "Do you need items moved up or down floors at your destination? If so, how many floors?",
                        "question_identifier": "destination_floors",
                        "answer_text": [
                            "None (unit is on the ground floor)"
                        ]
                    },
                    {
                        "question_text": "Do you need any assistance preparing for your move? (e.g. furniture disassembly, packing items into boxes, etc)",
                        "question_identifier": None,
                        "answer_text": [
                            "No"
                        ]
                    }
                ],
                "attachments": [
                    {
                        "id": "Tm-b0FNkwrfM-GTPFYWvfg",
                        "url": "https://yelp.com/image.jpg",
                        "resource_name": "image.jpg",
                        "mime_type": "image/jpeg"
                    }
                ]
            }
        },
        "message_sample": {
            "yelp_lead_id": "18kPq7GPye-YQ3LyKyAZPw",
            "conversation_id": "E24Bu-vMhVpueQpU8mpRPw",
            "message_content": "Hi, I'd like to get a quote for my move. When can you come out to assess?",
            "sender": "customer",
            "timestamp": "2024-08-01T10:30:00+00:00"
        }
    }