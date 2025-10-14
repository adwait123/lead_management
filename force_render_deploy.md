# Force Render Deployment Guide

## 🚨 Current Issue
Your Render staging server is still running old code with Pydantic v1 syntax. The latest changes haven't been deployed yet.

## 🔧 Solutions (Try in Order)

### **Option 1: Manual Redeploy via Render Dashboard**
1. Go to https://dashboard.render.com
2. Find your `lead-management-staging-backend` service
3. Click **"Manual Deploy"** → **"Deploy latest commit"**
4. Wait for deployment to complete (5-10 minutes)

### **Option 2: Force Deploy with Empty Commit**
```bash
# Create an empty commit to trigger deployment
git commit --allow-empty -m "Force Render redeployment for Pydantic v2 fixes"
git push origin staging
```

### **Option 3: Check Render Environment Variables**
Ensure your Render service has:
- **Build Command**: `cd backend && pip install -r requirements.txt`
- **Start Command**: `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Python Version**: 3.11 (or your preferred version)

### **Option 4: Clear Render Build Cache**
In Render Dashboard:
1. Go to your service
2. Settings → "Clear build cache"
3. Trigger a new deployment

## 🧪 Test Deployment Success

After redeployment, run these tests:

```bash
# 1. Check Pydantic version on staging
curl https://lead-management-staging-backend.onrender.com/api/agents/

# Should return agents list without errors

# 2. Run debug script in Render shell
python debug_pydantic_version.py

# Should show Pydantic v2 and model_validate available
```

## 📋 What Should Happen

✅ **Before Fix (Current Error):**
```
AttributeError: type object 'AgentResponseSchema' has no attribute 'model_validate'
```

✅ **After Fix (Expected Success):**
```json
{
  "agents": [...],
  "total": 5,
  "page": 1,
  "per_page": 20,
  "total_pages": 1
}
```

## 🚀 Next Steps After Successful Deployment

1. **Run migration**: `python migrate_agent_session_follow_up.py`
2. **Seed agents**: `python seed_agents_with_followups.py`
3. **Test follow-ups**: Use the API test commands
4. **Start end-to-end testing**: Create leads and verify follow-up sequences

## 💡 Why This Happened

Render sometimes caches builds and doesn't always pick up the latest changes immediately. The manual redeploy ensures:
- Fresh code checkout from your staging branch
- Clean pip install with updated dependencies
- Proper loading of updated Pydantic v2 schemas

Once this deploys successfully, your follow-up sequence system will be fully operational! 🎉

## 📦 Latest Deployment - Unified Architecture
- **Date**: January 15, 2025
- **Commit**: 24c7add - Unified lead management architecture with outbound webhooks
- **Features**:
  - All lead sources automatically trigger agents
  - Outbound webhook system for external integrations
  - Enhanced schemas with address and external_id fields
  - Real-time notifications for agent messages