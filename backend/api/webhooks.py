"""
Webhook API endpoints for external integrations (Zapier, Yelp, etc.)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from pydantic import BaseModel
# import requests  # Not used in this file

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

        # Trigger workflow for agent engagement synchronously
        session_ids = []
        try:
            workflow_service = WorkflowService(db)
            session_ids = workflow_service.handle_lead_created(
                lead_id=lead.id,
                source="yelp",
                form_data=project_details
            )
            logger.info(f"Triggered workflow for lead {lead.id}, created sessions: {session_ids}")

            # Initial messages are now generated automatically by the workflow service
            # No need for duplicate message generation here
            logger.info(f"Workflow service will handle initial message generation for sessions: {session_ids}")

        except Exception as e:
            logger.error(f"Failed to trigger workflow for lead {lead.id}: {str(e)}")
            # Don't fail the webhook if workflow fails, just log the error
            session_ids = []

        return WebhookResponse(
            success=True,
            message=f"Yelp lead {webhook_data.id} created successfully",
            lead_id=lead.id,
            session_ids=session_ids
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
    Routes message to existing agent session and generates response
    """
    logger.info(f"Received Yelp message for lead {webhook_data.yelp_lead_id}")

    try:
        # Find lead by external_id
        lead = db.query(Lead).filter(Lead.external_id == webhook_data.yelp_lead_id).first()
        if not lead:
            logger.error(f"Lead not found for Yelp ID: {webhook_data.yelp_lead_id}")
            raise HTTPException(status_code=404, detail=f"Lead not found: {webhook_data.yelp_lead_id}")

        # Import services
        from services.message_router import MessageRouter
        from services.agent_service import AgentService
        from models.message import Message

        # Route the message
        message_router = MessageRouter(db)
        routing_result = message_router.route_message(
            lead_id=lead.id,
            message=webhook_data.message_content,
            message_type="text",
            metadata={
                "yelp_conversation_id": webhook_data.conversation_id,
                "sender": webhook_data.sender,
                "timestamp": webhook_data.timestamp,
                "platform": "yelp"
            }
        )

        if not routing_result["success"]:
            logger.error(f"Message routing failed: {routing_result.get('error')}")
            raise HTTPException(status_code=500, detail="Failed to route message")

        agent_response = None
        agent_response_content = ""

        # If message was routed successfully and should get a response
        if routing_result["should_respond"]:
            session_id = routing_result["session_id"]
            agent_id = routing_result["agent_id"]

            # Check if session is taken over by business owner
            from models.agent_session import AgentSession
            session = db.query(AgentSession).filter(AgentSession.id == session_id).first()

            if session and session.session_status == "taken_over":
                logger.info(f"Session {session_id} is taken over by business owner - skipping agent response")
                agent_response_content = "Agent response skipped - session taken over by business owner"
            else:
                logger.info(f"Generating agent response for session {session_id}")

            # Create the incoming message record
            incoming_message = Message.create_lead_message(
                agent_session_id=session_id,
                lead_id=lead.id,
                content=webhook_data.message_content,
                external_conversation_id=webhook_data.conversation_id,
                metadata={
                    "yelp_conversation_id": webhook_data.conversation_id,
                    "sender": webhook_data.sender,
                    "timestamp": webhook_data.timestamp,
                    "platform": "yelp"
                },
                external_platform="yelp"
            )

            # Save incoming message
            db.add(incoming_message)
            db.commit()
            db.refresh(incoming_message)

            # Generate agent response only if not taken over
            if session and session.session_status != "taken_over":
                agent_service = AgentService(db)
                response_message = await agent_service.generate_response_message(
                    agent_session_id=session_id,
                    incoming_message=webhook_data.message_content
                )

                if response_message:
                    agent_response_content = response_message.content
                    logger.info(f"Generated response for session {session_id}: {response_message.id}")
                else:
                    logger.error(f"Failed to generate agent response for session {session_id}")

        # Prepare response with agent message for Zapier
        response_data = WebhookResponse(
            success=True,
            message=f"Message processed for lead {lead.id}",
            lead_id=lead.id,
            session_ids=[routing_result.get("session_id")] if routing_result.get("session_id") else []
        )

        # Add agent response to the webhook response if available
        if agent_response_content:
            # Include the agent response in the response for Zapier to send back
            response_data.message = agent_response_content

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Yelp message webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.get("/zapier/get-agent-responses/{lead_external_id}")
async def get_agent_responses_for_lead(
    lead_external_id: str,
    since_timestamp: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get recent agent responses for a lead (for Zapier to send to external platforms)

    Args:
        lead_external_id: External ID of the lead (e.g., Yelp lead ID)
        since_timestamp: ISO timestamp to get messages after this time
        limit: Maximum number of messages to return
    """
    try:
        # Find lead by external_id
        lead = db.query(Lead).filter(Lead.external_id == lead_external_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead not found: {lead_external_id}")

        from models.message import Message
        from datetime import datetime

        # Build query for agent messages
        query = db.query(Message).filter(
            Message.lead_id == lead.id,
            Message.sender_type == "agent"
        ).filter(
            (Message.delivery_status != "delivered") | (Message.delivery_status.is_(None))
        )

        # Filter by timestamp if provided
        if since_timestamp:
            try:
                since_dt = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
                query = query.filter(Message.created_at > since_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid timestamp format")

        # Get messages ordered by creation time
        messages = query.order_by(Message.created_at.asc()).limit(limit).all()

        # Format response for Zapier
        response_messages = []
        for message in messages:
            response_messages.append({
                "message_id": message.id,
                "content": message.content,
                "agent_name": message.sender_name,
                "created_at": message.created_at.isoformat() if message.created_at else None,
                "conversation_id": message.external_conversation_id,
                "metadata": message.message_metadata or {}
            })

        return {
            "success": True,
            "lead_external_id": lead_external_id,
            "lead_id": lead.id,
            "messages": response_messages,
            "total_messages": len(response_messages),
            "retrieved_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent responses for lead {lead_external_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent responses: {str(e)}")

@router.post("/zapier/mark-delivered/{message_id}")
async def mark_message_delivered(
    message_id: int,
    external_message_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Mark a message as delivered to external platform

    Args:
        message_id: ID of the message that was delivered
        external_message_id: ID from the external platform (optional)
    """
    try:
        from models.message import Message

        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found")

        # Mark as delivered
        message.mark_delivered(external_message_id)
        db.commit()

        return {
            "success": True,
            "message_id": message_id,
            "status": "delivered",
            "external_message_id": external_message_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking message {message_id} as delivered: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to mark message as delivered: {str(e)}")

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