# AI Lead Management Tool

A full-stack AI-powered lead generation and management system with intelligent conversation capabilities and automated appointment booking.

## 🚀 Tech Stack

- **Backend**: Python FastAPI + SQLAlchemy + SQLite
- **Frontend**: React + Vite + Tailwind CSS
- **AI Integration**: OpenAI API
- **Database**: SQLite (production-ready with migrations)
- **UI**: Tailwind CSS with custom components

## 📁 Project Structure

```
AILead/
├── backend/                # FastAPI application
│   ├── api/               # API endpoints
│   │   ├── agents.py      # Agent management
│   │   ├── leads.py       # Lead management
│   │   ├── messages.py    # Chat system
│   │   └── workflows.py   # Workflow automation
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   ├── main.py            # FastAPI app entry
│   ├── requirements.txt   # Python dependencies
│   └── .env.example       # Environment variables template
├── frontend/              # React application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Main application pages
│   │   └── services/      # API client
│   ├── package.json       # Node dependencies
│   └── tailwind.config.js # Tailwind configuration
└── README.md              # This file
```

## 🔧 Local Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn
- OpenAI API key

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key

# Run database migrations and seed data
python seed_data.py

# Start the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install

# Copy environment variables
cp .env.example .env
# Edit .env if needed (default backend URL should work)

# Start the frontend development server
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

## 🚀 Deployment on Render

### Prerequisites for Deployment
- GitHub account with your code repository
- Render account (free tier available)
- OpenAI API key

### Step 1: Prepare Your Repository
1. Ensure your code is pushed to GitHub
2. Make sure `.env` files are not committed (they should be in `.gitignore`)
3. Verify `.env.example` files are present for reference

### Step 2: Deploy Backend on Render

1. **Create New Web Service**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Backend Service**
   ```
   Name: ailead-backend
   Environment: Python 3
   Build Command: pip install -r backend/requirements.txt
   Start Command: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

3. **Set Environment Variables**
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `DATABASE_URL`: sqlite:///./leads.db (Render will handle SQLite)
   - `CORS_ORIGINS`: https://your-frontend-url.onrender.com

4. **Advanced Settings**
   - Instance Type: Free tier
   - Root Directory: Leave empty (we use `cd backend` in start command)

### Step 3: Deploy Frontend on Render

1. **Create New Static Site**
   - Click "New +" → "Static Site"
   - Connect the same GitHub repository

2. **Configure Frontend Service**
   ```
   Name: ailead-frontend
   Build Command: cd frontend && npm install && npm run build
   Publish Directory: frontend/dist
   ```

3. **Set Environment Variables**
   - `VITE_API_URL`: https://your-backend-service.onrender.com

### Step 4: Update CORS Settings

After both services are deployed:

1. Note your frontend URL (e.g., `https://ailead-frontend.onrender.com`)
2. Update your backend environment variables on Render:
   - Set `CORS_ORIGINS` to your frontend URL
3. Restart your backend service

### Step 5: Initialize Database

After backend deployment:
1. Go to your backend service on Render
2. Open the Shell tab
3. Run: `python seed_data.py` to initialize the database with sample data

### Production Configuration Notes

- **Database**: For production, consider upgrading to PostgreSQL using Render's database service
- **File Storage**: SQLite files on Render's free tier are ephemeral
- **Environment Variables**: Never commit real API keys; always use environment variables
- **CORS**: Make sure to update CORS settings when you get your final frontend URL

### Troubleshooting Deployment

**Backend Issues:**
- Check logs in Render dashboard
- Verify all environment variables are set
- Ensure `requirements.txt` includes all dependencies

**Frontend Issues:**
- Verify `VITE_API_URL` points to your backend service
- Check that build command completes successfully
- Ensure `dist` folder is being published

**CORS Issues:**
- Update `CORS_ORIGINS` in backend environment variables
- Restart backend service after updating CORS settings

### Post-Deployment

Once deployed, your application will be available at:
- Frontend: `https://your-app-name.onrender.com`
- Backend API: `https://your-backend-name.onrender.com`
- API Docs: `https://your-backend-name.onrender.com/docs`

The free tier includes:
- Automatic deploys from GitHub
- Custom domains (optional)
- SSL certificates
- Basic monitoring

## 🎯 Key Features

### Dashboard
- Real-time lead metrics and performance tracking
- Recent activity feed with AI interaction history
- Agent performance monitoring
- Calendar integration for appointment management

### AI-Powered Lead Management
- Intelligent lead scoring and qualification
- Automated conversation handling with natural language processing
- Dynamic response generation based on lead context
- Conversation history and timeline tracking

### Smart Agent System
- Pre-configured industry-specific agents (real estate, healthcare, SaaS, e-commerce)
- Customizable agent personalities and conversation flows
- Multi-modal communication (text, voice simulation ready)
- Agent performance analytics and optimization

### Automated Workflows
- Lead nurturing sequences with conditional logic
- Appointment booking and calendar management
- Follow-up automation based on lead behavior
- Integration-ready for CRM systems

### Business Intelligence
- Lead source tracking and ROI analysis
- Conversion funnel visualization
- Agent effectiveness metrics
- Performance reporting and insights

## 🔧 Technical Features

- **RESTful API**: Comprehensive FastAPI backend with automatic documentation
- **Real-time Updates**: WebSocket support for live notifications
- **Data Persistence**: SQLite with SQLAlchemy ORM for reliable data storage
- **AI Integration**: OpenAI API integration for natural language processing
- **Responsive Design**: Mobile-first UI with Tailwind CSS
- **Type Safety**: Full TypeScript support in frontend components

## 📊 Project Status

✅ **Core Backend APIs**: Lead management, agent system, messaging
✅ **Database Models**: Complete schema with relationships and migrations
✅ **Frontend Foundation**: React app with routing and API integration
✅ **AI Integration**: OpenAI service for intelligent responses
✅ **Sample Data**: Realistic seed data for immediate testing
🚀 **Production Ready**: Configured for deployment on Render platform

## 🎯 Getting Started

1. **Clone and Setup**: Follow the local development setup above
2. **Configure AI**: Add your OpenAI API key to backend/.env
3. **Initialize Data**: Run seed scripts to populate sample leads and agents
4. **Start Development**: Launch both frontend and backend servers
5. **Deploy**: Use the Render deployment guide for production hosting

## 📝 License

This project is built for demonstration purposes. Please ensure you have proper licenses for any production use of AI services and third-party integrations.
