# AI Voice Agent Administration Platform

A comprehensive web application for configuring, testing, and reviewing calls made by an adaptive AI voice agent using Retell AI. Built with React, TypeScript, FastAPI, and Supabase.

## NOTE
- please go through provided Loom videos for more comprehensive understanding of the application

## 🎯 Features

### Agent Configuration
- Create an agent from UI
- Visual prompt editor for agent conversation logic
- Configurable voice settings (backchanneling, filler words, interruption sensitivity, denoising_mode, unresponsiveness timeout)
- Emergency protocol configuration
- Update agent configurations from UI

### Call Management
- Trigger test calls with driver context (name, phone, load number)
- Real-time call status tracking
- Structured call results extraction
- Full transcript viewing
- Auto call ending on unresponsiveness

### Logistics Scenarios
1. **Driver Check-in (Dispatch)**: End-to-end conversation for status updates, ETA, and arrival confirmation
2. **Emergency Protocol**: Dynamic emergency escalation handling with human dispatcher transfer

## 🏗️ Architecture

```
ai-voice-agent/
├── frontend/                 # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/       # UI components
│   │   │   ├── ui/          # Base UI components
│   │   │   ├── dashboard/   # Dashboard views
│   │   │   ├── agent/       # Agent configuration
│   │   │   └── call/        # Call management 
│   │   ├── lib/             # Utilities & API clients
│   │   ├── types/           # TypeScript types
│   │   └── styles/          # Global styles
│   └── public/
│
├── backend/                  # FastAPI
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/      # API endpoints
│   │   │   └── webhooks/    # Retell AI webhooks
│   │   ├── core/            # Config & security
│   │   ├── db/              # Database setup
│   │   ├── services/        # Business logic
│   │   ├── templates/       # prompt templates
│   │   └── schemas/         # Pydantic schemas
│   └── tests/
│
└── supabase/                 # Database migrations & config
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Supabase account
- Retell AI account with API key (Free tier as well)

### Environment Setup

1. **Clone and install dependencies:**
```bash
# Frontend
cd frontend
npm install

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

2. **Configure environment variables:**

Backend (`.env`): please refer to '.env.example'
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
RETELL_API_KEY=your_retell_api_key
OPENAI_API_KEY=your_openai_api_key
FROM_PHONE_NUMBER=your_retell_phone_number
WEBHOOK_BASE_URL=your_webhook_base_url
```

3. **Run the application:**
```bash
#ngrok
ngrok http 8000

# Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm run dev
```

## 📊 Database Schema

### Tables

- **agents**: Agent configurations and prompts
- **calls**: Call records with metadata
- **call_results**: Structured extraction results
- **prompts**: prompts used (currently not required)

## 🔌 API Endpoints

### Agents
- `GET /api/agents` - List all agents
- `POST /api/agents` - Create new agent
- `GET /api/agents/{id}` - Get agent details
- `PUT /api/agents/{id}` - Update agent
- `DELETE /api/agents/{id}` - Delete agent

### Calls
- `POST /api/calls/trigger` - Trigger a new call
- `GET /api/calls` - List all calls
- `GET /api/calls/{id}` - Get call details with results

### Webhooks
- `POST /webhooks/retell` - Retell AI webhook endpoint

## 🎙️ Voice Agent Configuration

### Optimal Voice Settings
```python
{
    "enable_backchannel": True,
    "backchannel_frequency": 0.8,
    "backchannel_words": ["yeah", "uh-huh", "I see", "right"],
    "interruption_sensitivity": 0.7,
    "responsiveness": 0.8,
    "voice_speed": 1.0,
    "ambient_sound": "office",
    "noise-and-background-speech-cancellation": True/False
    "unresponsiveness_timeout": configurable
}
```

### Emergency Trigger Phrases (configurable during agent creation)
- "accident"
- "blowout"
- "emergency"
- "breakdown"
- "medical"
- "help"

## 📝 License

MIT License
