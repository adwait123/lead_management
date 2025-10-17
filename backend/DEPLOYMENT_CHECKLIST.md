# 🚀 Render Deployment Checklist for Inbound Calling

## ✅ **Pre-Deployment Status**
- **Local Tests**: 6/6 PASSED ✅
- **Active Inbound Agents**: 9 agents available ✅
- **Requirements.txt**: Up to date ✅
- **TwiML Generation**: Working ✅
- **Database Operations**: Working ✅

## 🔧 **Step 1: Deploy to Render**

### **A. Push Code to Repository**
```bash
# Commit all changes
git add .
git commit -m "feat: add lead creation and agent session tracking to inbound webhook"
git push origin staging  # or main branch
```

### **B. Deploy on Render**
1. Go to your Render dashboard
2. Redeploy your service (should pick up new code automatically)
3. Wait for deployment to complete

## 🤖 **Step 2: Ensure Production Database Has Inbound Agents**

### **Option A: Check Production Database**
```bash
# SSH into Render service or use database console
# Check if inbound agents exist in production
```

### **Option B: Create Production Inbound Agent** (if needed)
```bash
# Upload and run the agent creation script on Render
# Or use the admin interface to create an inbound agent
```

**Required Agent Settings:**
- **Name**: "Inbound Call Agent" (or similar)
- **Type**: "inbound"
- **Status**: Active (is_active = True)
- **Model**: "gpt-3.5-turbo" or preferred
- **Prompt**: Voice-optimized customer service prompt

## 📞 **Step 3: Update Twilio Configuration**

### **A. Update Webhook URL**
1. Login to Twilio Console
2. Go to Phone Numbers → Manage → Active numbers
3. Click on your number: **+17622437375**
4. Update webhook URL to:
   ```
   https://your-app-name.onrender.com/api/inbound-calls/webhooks/twilio
   ```
5. Set HTTP method to **POST**
6. Save configuration

### **B. Verify SIP Trunk Settings**
Confirm your SIP trunk settings in Twilio:
- **Name**: inbound_call_raq (or your trunk name)
- **Termination URI**: `sip:1w7n1n4d64r.sip.livekit.cloud;transport=tcp`
- **Status**: Enabled

## 🧪 **Step 4: Test End-to-End Flow**

### **A. Production Health Check**
```bash
curl https://your-app-name.onrender.com/api/health
```

### **B. Test Webhook Endpoint**
```bash
curl -X POST https://your-app-name.onrender.com/api/inbound-calls/webhooks/twilio \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=TEST123&From=+15551234567&To=+17622437375&CallStatus=ringing"
```

### **C. Real Phone Call Test**
1. **Call +17622437375** from your phone
2. **Expected Flow**:
   - Call connects to LiveKit SIP trunk
   - Agent "inbound_raq" answers (if running)
   - Conversation with AI agent begins
   - Database records call, creates/finds lead, tracks session

### **D. Verify Database Operations**
Check via API or admin interface:
```bash
# Check if inbound call was created
curl https://your-app-name.onrender.com/api/inbound-calls/

# Check if lead was created/updated
curl https://your-app-name.onrender.com/api/leads/

# Check if agent session was created
curl https://your-app-name.onrender.com/api/agent-sessions/
```

## 🎯 **Step 5: Agent Deployment** (Critical!)

### **For Full Voice Functionality**
You need the `inbound_raq` agent running to handle calls:

**Option A: Deploy Agent on Render**
```bash
# Create separate Render service for the agent
# Point to: /agent directory
# Set AGENT_NAME=inbound_raq
```

**Option B: Run Agent Locally** (for testing)
```bash
cd agent
./start.sh
```

## ✅ **Success Criteria**

### **Webhook Working**:
- ✅ Returns TwiML with SIP routing
- ✅ HTTP 200 response within 3 seconds
- ✅ Creates inbound call record
- ✅ Processes lead creation/lookup in background

### **Database Operations**:
- ✅ Inbound call record created with Twilio CallSid
- ✅ Lead created (new callers) or found (existing callers)
- ✅ Agent session created for conversation tracking
- ✅ Background processing completes without errors

### **Voice Call Flow**:
- ✅ Calls route to LiveKit successfully
- ✅ Agent responds and has conversation
- ✅ Call quality is good
- ✅ Session data is tracked

## 🚨 **Troubleshooting**

### **Common Issues**:

**1. "No inbound agents available"**
- Create active inbound agent in production database
- Verify agent.type = "inbound" and agent.is_active = True

**2. "Twilio timeout (Error 11200)"**
- Check webhook URL is correct
- Verify Render service is responding quickly
- Test webhook endpoint directly

**3. "SIP connection fails"**
- Verify LiveKit SIP trunk configuration
- Check SIP URI format in TwiML
- Ensure LiveKit service is running

**4. "Agent session not created"**
- Check if agent exists and is active
- Verify background task processing
- Check database constraints

## 📝 **Production Configuration**

### **Environment Variables** (Render)
Ensure these are set:
```
LIVEKIT_URL=wss://inboundcallraq-99wxjr3c.livekit.cloud
LIVEKIT_API_KEY=your-key
LIVEKIT_API_SECRET=your-secret
SIP_INBOUND_TRUNK_ID=ST_VXdDdwyrHLtu
OPENAI_API_KEY=your-openai-key
DATABASE_URL=your-production-db-url
```

### **Monitoring**
- Monitor webhook response times
- Track inbound call success rates
- Monitor agent session creation
- Watch for background processing errors

## 🎉 **Ready for Production!**

Your inbound calling system now provides:
- ✅ **Fast webhook responses** (no Twilio timeouts)
- ✅ **LiveKit SIP integration** (voice connectivity)
- ✅ **Automatic lead management** (CRM integration)
- ✅ **Conversation tracking** (full history)
- ✅ **Background processing** (non-blocking architecture)

**Next**: Test with real calls and monitor performance! 📞