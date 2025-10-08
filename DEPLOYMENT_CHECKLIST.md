# Staging → Main Deployment Checklist

## 🎯 Overview
This checklist covers deployment of Yelp webhook integration and related features from staging to production.

## 📋 Pre-Merge Requirements

### ✅ Database Schema Changes
- [x] **Lead Model Updated**: Added `external_id`, `first_name`, `last_name` fields
- [x] **Migration Script Created**: `backend/migrate_lead_schema.py`
- [ ] **⚠️ CRITICAL: Run migration on production DB BEFORE deployment**
  ```bash
  python backend/migrate_lead_schema.py
  ```

### ✅ New Files Added
- [x] `backend/api/webhooks.py` - Yelp webhook endpoints
- [x] `backend/migrate_lead_schema.py` - Database migration
- [x] `DEPLOYMENT_CHECKLIST.md` - This checklist

### ⚠️ Environment Configuration Changes to Revert
- [ ] **CORS Origins**: Change back from staging to production URLs
  - Current: `https://lead-management-staging-frontend.onrender.com`
  - Revert to: Production frontend URL
- [ ] **Frontend API URLs**: Revert all hardcoded staging URLs back to production
  - Files to update: `frontend/src/lib/api.js`, `.env.production`, and component files

### ✅ Features Implemented
- [x] **Webhook Infrastructure**: `/api/webhooks/zapier/yelp-lead-created`
- [x] **Lead Creation**: Rich Yelp data storage in notes field
- [x] **Agent Configuration**: "Yelp Lead Specialist" with proper triggers
- [x] **Auto-Engagement**: Workflow triggers for new leads

## 🚀 Production Deployment Steps

### Step 1: Database Migration (CRITICAL FIRST)
```bash
# Connect to production environment
# Run migration script
python backend/migrate_lead_schema.py

# Verify schema
# Should show: external_id, first_name, last_name columns added
```

### Step 2: Environment Configuration
- [ ] Update `backend/main.py` CORS origins for production
- [ ] Update `frontend/src/lib/api.js` base URL to production
- [ ] Update all hardcoded URLs in frontend components
- [ ] Update `.env.production` with production API URL

### Step 3: Code Deployment
- [ ] Create PR: staging → main
- [ ] Review all changes
- [ ] Deploy to production
- [ ] Verify deployment successful

### Step 4: Verification Testing
- [ ] **Health Check**: `GET /api/health` returns healthy
- [ ] **Webhook Endpoint**: `GET /api/webhooks/test/yelp-sample` returns sample data
- [ ] **Agent Exists**: `GET /api/agents/` shows Yelp Lead Specialist
- [ ] **Complete Flow**: Test webhook → lead creation → agent session

### Step 5: Zapier Configuration (Post-Deployment)
- [ ] Update Zapier webhook URLs to production endpoints
- [ ] Test Zapier → Production webhook flow
- [ ] Verify agent auto-engagement works
- [ ] Monitor for webhook delivery issues

## 🔍 Files Changed in This Release

### Backend Files Modified:
- `backend/models/lead.py` - Added new fields
- `backend/main.py` - Added webhook router, updated CORS
- `backend/api/webhooks.py` - NEW: Yelp webhook endpoints

### Frontend Files Modified:
- `frontend/src/lib/api.js` - Updated API base URL
- `frontend/.env.production` - Updated API URL
- `frontend/src/components/wizard/tabs/AIInstructionsTab.jsx` - Updated URLs
- `frontend/src/components/wizard/HatchAgentEdit.jsx` - Updated URLs
- `frontend/src/components/wizard/HatchWizardContext.jsx` - Updated URLs
- `frontend/src/components/modals/AgentTestingModal.jsx` - Updated URLs
- `frontend/src/pages/Workflows.jsx` - Updated URLs

## ⚠️ Critical Notes

1. **Database Migration is MANDATORY** - Must run before code deployment
2. **URL Reversion Required** - All staging URLs must be changed back to production
3. **Zapier Integration** - Will need production webhook URLs after deployment
4. **Backward Compatibility** - All existing functionality should continue working

## 📞 Rollback Plan
If issues occur:
1. **Code Rollback**: Revert to previous main branch commit
2. **Database Rollback**: New fields are nullable, so no data loss
3. **Zapier Rollback**: Point webhooks back to old endpoints if needed

## ✅ Post-Deployment Verification
- [ ] All existing leads still accessible
- [ ] Agent creation/editing still works
- [ ] Workflow system functions normally
- [ ] New Yelp webhook integration working
- [ ] Frontend connects to backend successfully

---
**Last Updated**: 2025-10-08
**Staging Branch**: ready for merge
**Database Migration**: Required before deployment