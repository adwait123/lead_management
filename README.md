# AI Lead Management Tool

A full-stack prototype application for demonstrating AI-powered lead management capabilities. Built for executive demos with production-ready UI and mock data.

## 🚀 Tech Stack

- **Backend**: Python FastAPI + SQLAlchemy + SQLite
- **Frontend**: React + Vite + TypeScript + Tailwind CSS + shadcn/ui
- **Workflow Builder**: react-flow
- **Icons**: lucide-react
- **Database**: SQLite (with realistic mock data)

## 📁 Project Structure

```
ai-lead-management/
├── backend/                # FastAPI application
│   ├── app/
│   ├── models/            # Database models
│   ├── api/               # API endpoints
│   ├── services/          # Business logic
│   ├── seeds/             # Seed data scripts
│   ├── main.py            # FastAPI app entry
│   ├── requirements.txt   # Python dependencies
│   └── .env.example       # Environment variables template
├── frontend/              # React application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Main application pages
│   │   ├── hooks/         # Custom React hooks
│   │   ├── lib/           # Utilities and API client
│   │   └── types/         # TypeScript type definitions
│   ├── package.json       # Node dependencies
│   └── tailwind.config.js # Tailwind configuration
└── README.md              # This file
```

## 🔧 Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup
```bash
cd backend
source venv/bin/activate  # Virtual environment already exists
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Quick Start (Both)
```bash
# Terminal 1 - Backend
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend && npm run dev
```

Application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🎯 Features

### Dashboard
- Real-time metrics cards (Total Leads, Active Leads, Conversion Rate)
- Recent leads table with quick actions
- Agent activity feed
- Performance charts

### Leads Management
- Advanced search and filtering
- Detailed lead profiles with interaction timeline
- AI conversation history
- Notes and status management
- Bulk operations

### AI Agents Builder ⭐ (Star Feature)
- **8-Step Agent Creation Wizard**:
  1. Basic Information (Name, Description, Mode)
  2. Voice Settings (Provider, Model, Language, Speed, Pitch)
  3. Text Settings (Tone, Style, Response Length)
  4. Personality & Instructions
  5. Business Knowledge Base
  6. Available Tools & Functions
  7. Integration Connections
  8. Review & Live Testing

- **Agent Management**:
  - Live testing interface (chat/voice simulation)
  - Performance metrics and analytics
  - Clone and edit existing agents
  - Agent status monitoring

### Workflow Builder
- Visual drag-and-drop workflow designer
- Pre-built templates (Lead Nurturing, Follow-up Sequences)
- Workflow execution simulator with animations
- Trigger and action node library
- Conditional logic support

### Integrations
- Mock connections to popular CRMs (Salesforce, HubSpot, GoHighLevel)
- Ad platform integrations (Facebook, Google, LinkedIn)
- Communication tools (Twilio, SendGrid, Slack)
- OAuth-style connection flows
- Integration status monitoring

## 🧪 Demo Features

- **Demo Reset**: Restore all data to initial state
- **Mock AI Responses**: Keyword-based intelligent responses
- **Simulated Real-time Updates**: Live activity feeds
- **Realistic Data**: 15+ diverse leads with interaction histories
- **Voice Testing**: Mock audio playbook with waveform visualization

## 📊 Current Status

✅ **Backend dependencies installed and working**
✅ **Frontend structure ready and UI shell complete**
✅ **Navigation, routing, and API integration working**
✅ **Dashboard with real data from backend**
🔄 **Ready for next iteration: Leads module or Agents module**

## 🎯 Demo Script

1. **Dashboard Overview**: Show real-time metrics and recent activity
2. **Lead Management**: Filter leads, open detailed profile, show interaction timeline
3. **Agent Builder**: Create new agent through full wizard, test live chat
4. **Workflow Designer**: Build automation flow, run simulation
5. **Integrations**: Show connection status, mock OAuth flow
6. **Demo Reset**: Reset to fresh state for next demo

## Note

This is a prototype using mock data only. No real external API integrations.
