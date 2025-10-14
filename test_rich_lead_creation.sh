#!/bin/bash

# Test rich lead creation with comprehensive survey data and project information
curl -X POST "http://localhost:8000/api/leads/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "first_name": "John",
    "last_name": "Smith",
    "email": "john.smith.test@example.com",
    "phone": "+1-555-123-4567",
    "company": "Smith Home Services",
    "address": "123 Main St, Anytown, CA 90210",
    "external_id": "yelp_lead_12345",
    "source": "yelp",
    "status": "new",
    "project_data": {
      "job_names": ["Kitchen Remodeling", "Bathroom Renovation"],
      "additional_info": "Looking to renovate kitchen and master bathroom. High-end finishes preferred.",
      "location": {
        "postal_code": "90210",
        "city": "Beverly Hills",
        "state": "CA",
        "country": "USA",
        "full_address": "123 Main St, Beverly Hills, CA 90210"
      },
      "availability": {
        "status": "SPECIFIC_DATES",
        "dates": ["2024-03-15", "2024-03-16", "2024-03-22"],
        "time_preferences": {
          "morning": true,
          "afternoon": false,
          "weekend": true
        }
      },
      "survey_answers": [
        {
          "question_text": "What type of renovation are you looking for?",
          "question_identifier": "renovation_type",
          "answer_text": ["Kitchen Remodeling", "Bathroom Renovation"]
        },
        {
          "question_text": "What is your estimated budget range?",
          "question_identifier": "budget_range",
          "answer_text": ["$50,000 - $100,000"]
        },
        {
          "question_text": "When would you like to start the project?",
          "question_identifier": "start_timeline",
          "answer_text": ["Within 3 months"]
        },
        {
          "question_text": "Do you have any specific material preferences?",
          "question_identifier": "materials",
          "answer_text": ["Granite countertops", "Hardwood floors", "Subway tile backsplash"]
        },
        {
          "question_text": "Have you worked with contractors before?",
          "question_identifier": "experience",
          "answer_text": ["Yes, for previous home projects"]
        }
      ],
      "attachments": [
        {
          "id": "att_001",
          "url": "https://example.com/kitchen_inspiration.jpg",
          "resource_name": "kitchen_inspiration.jpg",
          "mime_type": "image/jpeg"
        },
        {
          "id": "att_002",
          "url": "https://example.com/bathroom_layout.pdf",
          "resource_name": "bathroom_layout_ideas.pdf",
          "mime_type": "application/pdf"
        }
      ],
      "budget_range": "$50,000 - $100,000",
      "timeline": "3-6 months",
      "special_requirements": "Must work around existing plumbing in bathroom. Kitchen has load-bearing wall considerations."
    },
    "platform_metadata": {
      "yelp_request_id": "req_abc123",
      "yelp_conversation_id": "conv_xyz789",
      "lead_source_campaign": "spring_renovation_2024"
    },
    "notes": [
      {
        "id": 1,
        "content": "Initial contact via Yelp platform. Customer seems very organized and has clear vision.",
        "timestamp": "2024-01-12T10:30:00Z",
        "author": "system",
        "type": "initial_contact"
      }
    ]
  }' \
  | jq '.'