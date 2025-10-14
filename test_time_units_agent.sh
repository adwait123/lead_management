#!/bin/bash

# Test curl for creating agent with 40 minutes and 10 hours follow-up sequences
# This tests the time unit preservation fix

curl -X POST "http://localhost:8000/api/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Time Unit Test Agent",
    "prompt": "You are a friendly sales assistant helping with {{service_requested}} inquiries. Budget: {{budget_range}}, Timeline: {{timeline}}",
    "active": true,
    "workflow_config": {
      "triggers": [
        {
          "event_type": "lead_created",
          "conditions": {
            "source": "website"
          }
        }
      ]
    },
    "workflow_steps": [
      {
        "delay": 40,
        "unit": "minutes",
        "message": "Hi {{name}}, thanks for your interest in {{service_requested}}! I wanted to follow up on your inquiry. Based on your budget range of {{budget_range}} and timeline of {{timeline}}, I can help you get started right away."
      },
      {
        "delay": 10,
        "unit": "hours",
        "message": "Hello {{name}}, I hope you had a chance to review my previous message about {{service_requested}}. If you have any questions about the project timeline ({{timeline}}) or budget ({{budget_range}}), I am here to help!"
      }
    ]
  }'

echo -e "\n\nAgent created! You can test by:"
echo "1. Going to the agent configuration page in UI"
echo "2. Checking that follow-ups show as '40 minutes' and '10 hours'"
echo "3. Save and reload - they should still show as '40 minutes' and '10 hours'"
echo "4. NOT converted to '40 minutes' and '600 minutes'"