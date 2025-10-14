# 🎯 Lead Management System - Comprehensive Test Plan

## Overview
This test plan validates the complete lead-to-conversation flow including:
1. **Lead Creation** - From Torkin website form submission
2. **Voice Agent Outbound Calling** - Automatic voice calls triggered by lead creation
3. **Text Agent Auto-Messaging** - Automated text conversations with back-and-forth handling

---

## 📋 Prerequisites & Setup

### 🔧 Environment Configuration
**Required API Keys in `.env`:**
```bash
# OpenAI (for agent responses)
OPENAI_API_KEY=your_openai_key

# LiveKit (for voice calling)
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_key
LIVEKIT_API_SECRET=your_livekit_secret
LIVEKIT_SIP_TRUNK_ID=your_sip_trunk_id

# Cartesia (for voice synthesis - if used)
CARTESIA_API_KEY=your_cartesia_key
```

### 🗄️ Database Setup
```bash
# Run migrations
cd backend
python migrate_calls_table.py
```

### 🤖 Agent Setup
```bash
# Create demo outbound agent
python create_demo_outbound_agent.py
```

### 🌐 URLs to Test
- **Torkin Website**: `https://lead-management-staging-frontend.onrender.com/frontend_demo/torkin_demo.html`
- **Backend API**: `https://lead-management-staging.onrender.com`
- **Frontend Dashboard**: `https://lead-management-staging-frontend.onrender.com`

---

## 🎭 Test Scenario 1: Voice Agent Outbound Calling

### 🎯 **Objective**: Test complete outbound calling flow from lead creation to voice conversation

### **Setup Requirements:**
1. ✅ Outbound voice agent created and active
2. ✅ LiveKit SIP trunk configured
3. ✅ Valid phone number for testing (your own)

### **Test Steps:**

#### **Step 1: Create Test Lead via Torkin Website**
1. Navigate to: `https://lead-management-staging-frontend.onrender.com/frontend_demo/torkin_demo.html`
2. Fill out contact form with:
   - **Name**: "Test User Voice"
   - **Phone**: `+12014860463` (test phone for voice calls)
   - **Email**: "test.voice@example.com"
   - **Service**: "Pest Control Inspection"
   - **Message**: "I need help with ants in my kitchen"
3. Submit form
4. **Verify**: Lead appears in dashboard with source "torkin website"

#### **Step 2: Trigger Outbound Call**
1. **API Call**: `POST /api/calls/trigger/{lead_id}`
```bash
curl -X POST "https://lead-management-staging.onrender.com/api/calls/trigger/{LEAD_ID}" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": null, "force_call": true}'
```
2. **Verify Response**:
```json
{
  "success": true,
  "call_id": 123,
  "message": "Outbound call scheduled for Test User Voice (+1234567890)",
  "agent": "Outbound Demo Agent"
}
```

#### **Step 3: Monitor Call Execution**
1. **Check Call Status**: `GET /api/calls/{call_id}`
2. **Expected Call Flow**:
   - Status: `pending` → `calling` → `in_progress` → `completed`
   - You should receive actual phone call
   - Agent introduces itself using Torkin branding
   - Agent references the pest control inquiry

#### **Step 4: Test Voice Conversation**
**Expected Agent Behavior:**
- "Hi Test User, this is [Agent Name] from Torkin Pest Control"
- "I see you're interested in pest control inspection for ants in your kitchen"
- Agent should ask qualifying questions:
  - "How severe is the ant problem?"
  - "When did you first notice them?"
  - "What's your timeline for getting this resolved?"

**Test Responses:**
- Provide realistic answers to test conversation flow
- Test agent's ability to handle follow-up questions
- Verify agent stays on topic and doesn't hallucinate services

#### **Step 5: Verify Call Data**
1. **Check Call Record**: `GET /api/calls/{call_id}`
2. **Expected Data**:
   - `call_duration` > 0
   - `transcript` contains conversation
   - `call_status` = "completed"
   - `call_summary` generated

### **✅ Success Criteria:**
- [ ] Lead created successfully from website
- [ ] Outbound call triggered automatically
- [ ] Phone call received within 2 minutes
- [ ] Agent uses correct branding (Torkin)
- [ ] Agent references specific lead details
- [ ] Conversation flows naturally for 2-3 exchanges
- [ ] Call data recorded in system
- [ ] Transcript generated and stored

---

## 💬 Test Scenario 2: Text Agent Auto-Messaging

### 🎯 **Objective**: Test automated text messaging with multi-turn conversations

### **Setup Requirements:**
1. 📱 Text-based agent configured for auto-messaging
2. 🔗 Lead creation triggers text agent activation
3. 📞 SMS/messaging capability (or simulated messaging)

### **Test Steps:**

#### **Step 1: Configure Text Agent**
1. **Create Text Agent** with these settings:
   - **Type**: "inbound" (for text messaging)
   - **Communication Mode**: "text" or "both"
   - **Use Case**: "lead_qualification"
   - **Auto-trigger**: Enable on lead creation

#### **Step 2: Create Test Lead for Text Messaging**
1. Use Torkin website or API to create lead:
   - **Name**: "Test User Text"
   - **Phone**: `+12014860463` (test phone for text messaging)
   - **Email**: "test.text@example.com"
   - **Service**: "Termite Inspection"
   - **Message**: "Concerned about termites in garage"

#### **Step 3: Verify Auto-Message Trigger**
1. **Check for Agent Session Creation**:
   - `GET /api/messages/lead/{lead_id}/active-session`
2. **Verify Initial Message Sent**:
   - `GET /api/messages/lead/{lead_id}/messages`
3. **Expected Initial Message**:
   > "Hi Test User! Thanks for reaching out about termite inspection. I'm [Agent Name] from Torkin and I'd love to help. What's driving your concern about termites in your garage right now?"

#### **Step 4: Simulate Customer Responses**
**Use the messaging simulation API or chat interface:**

**Response 1** (Customer):
```
"I found some wood damage and small holes. Not sure if it's termites but want to get it checked out soon."
```

**Expected Agent Response 1**:
- Acknowledges the concern
- Asks follow-up: timeline, extent of damage, previous treatments
- Shows expertise without being pushy

**Response 2** (Customer):
```
"It's been getting worse over the past month. What does an inspection involve and how much does it cost?"
```

**Expected Agent Response 2**:
- Explains inspection process briefly
- Asks about property details (age, size, construction type)
- Offers to schedule rather than providing exact pricing

**Response 3** (Customer)**:
```
"House is about 15 years old, 2000 sq ft. Can you come out this week?"
```

**Expected Agent Response 3**:
- Confirms urgency understanding
- Offers specific appointment times
- Collects final details for scheduling

#### **Step 5: Test Conversation Quality**
**Verify Agent Performance:**
- ✅ Stays in character as Torkin representative
- ✅ References specific lead details (garage, termites)
- ✅ Asks relevant follow-up questions
- ✅ Doesn't hallucinate services or pricing
- ✅ Maintains professional tone throughout
- ✅ Progresses toward scheduling/qualification goal

### **✅ Success Criteria:**
- [ ] Auto-message triggered within 1 minute of lead creation
- [ ] Agent uses correct branding and lead context
- [ ] Conversation maintains quality for 3+ exchanges
- [ ] Agent asks relevant qualifying questions
- [ ] Agent progresses toward business objective
- [ ] All messages stored in conversation history
- [ ] No hallucinated information or off-topic responses

---

## 🔄 Test Scenario 3: Integrated Workflow Testing

### 🎯 **Objective**: Test both voice and text agents working together

### **Test Steps:**

#### **Step 1: Lead with Both Communication Preferences**
Create lead indicating preference for both voice and text follow-up

#### **Step 2: Multi-Channel Engagement**
1. Text agent sends initial auto-message
2. If no response within X hours, voice agent calls
3. Both channels should reference previous touchpoints

#### **Step 3: Conversation Hand-off**
Test scenarios where conversation moves between text and voice channels

### **✅ Success Criteria:**
- [ ] Both agents reference shared lead context
- [ ] No duplicate or conflicting outreach
- [ ] Smooth hand-off between communication modes
- [ ] Consistent branding and messaging across channels

---

## 📊 Monitoring & Validation

### **Key Metrics to Track:**
1. **Lead Creation Rate**: Forms submitted successfully
2. **Call Success Rate**: Calls connected and completed
3. **Message Delivery Rate**: Auto-messages sent successfully
4. **Conversation Quality**: Agent stays on-topic and professional
5. **Response Time**: Speed of initial outreach after lead creation
6. **Data Integrity**: All interactions properly logged

### **Dashboard Verification:**
- [ ] Leads appear in real-time
- [ ] Call logs show accurate status and duration
- [ ] Message history displays complete conversations
- [ ] Agent performance metrics captured

### **Error Scenarios to Test:**
- [ ] Invalid phone numbers
- [ ] Incomplete form submissions
- [ ] API failures during call/message triggers
- [ ] Agent prompt issues or hallucinations
- [ ] Concurrent call/message scenarios

---

## 🚨 Troubleshooting Guide

### **Common Issues:**

**❌ Outbound calls not triggering:**
- Verify LiveKit credentials in `.env`
- Check agent has `type: "outbound"` and `communicationMode: "voice"`
- Confirm lead has valid phone number
- Check demo restriction for "torkin website" source

**❌ Auto-messages not sending:**
- Verify text agent configured with proper triggers
- Check agent session creation in database
- Confirm messaging service integration

**❌ Poor conversation quality:**
- Review agent prompt templates
- Check variable replacement in prompts
- Verify context data passed to agent
- Test with different conversation scenarios

### **Debug Commands:**
```bash
# Check recent calls
curl "https://lead-management-staging.onrender.com/api/calls?page=1&per_page=5"

# Check lead's conversation history
curl "https://lead-management-staging.onrender.com/api/messages/lead/{lead_id}/messages"

# Check active agent session
curl "https://lead-management-staging.onrender.com/api/messages/lead/{lead_id}/active-session"

# Get call transcript
curl "https://lead-management-staging.onrender.com/api/calls/{call_id}/transcript"
```

---

## ✅ Final Validation Checklist

### **End-to-End Workflow:**
- [ ] Torkin website accessible and functional
- [ ] Lead creation triggers both voice and text agents appropriately
- [ ] Voice calls connect and maintain quality conversations
- [ ] Text messages auto-trigger and handle multi-turn conversations
- [ ] All interactions properly logged and accessible via API/dashboard
- [ ] Agent responses stay professional and on-brand
- [ ] No system errors or failed integrations
- [ ] Performance meets acceptable response time thresholds

### **Production Readiness:**
- [ ] All API keys configured securely
- [ ] Error handling working correctly
- [ ] Monitoring and logging in place
- [ ] Backup and recovery procedures documented
- [ ] Load testing completed for expected volume

---

*📝 Document any issues found during testing and track resolution in project management system.*