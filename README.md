# AI Voice Agent Administration Platform

A comprehensive web application for configuring, testing, and reviewing calls made by an adaptive AI voice agent using Retell AI. Built with React, TypeScript, FastAPI, and Supabase.

## NOTE
- Please go through provided Loom videos for more comprehensive understanding of the application

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

### Dynamic Response Handling (Task B)
1. **Uncooperative Driver**: Probes for information with specific questions, offers options, ends call gracefully
2. **Noisy Environment**: Uses background noise cancellation feature

---

## 🏛️ System Design

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              SYSTEM ARCHITECTURE                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌─────────────┐       ┌─────────────┐       ┌─────────────────────────┐   │
│    │   Browser   │       │   FastAPI   │       │       Retell AI         │   │
│    │   (React)   │◄─────►│   Backend   │◄─────►│    (Voice Platform)     │   │
│    └─────────────┘  REST └─────────────┘  API  └─────────────────────────┘   │
│          │                     │                          │                  │
│          │                     │                          │                  │
│          │                     ▼                          │                  │
│          │              ┌─────────────┐                   │                  │
│          │              │  Supabase   │                   │                  │
│          │              │ (PostgreSQL)│                   │                  │
│          │              └─────────────┘                   │                  │
│          │                     │                          │                  │
│          │                     ▼                          │                  │
│          │              ┌─────────────┐                   │                  │
│          └─────────────►│   OpenAI    │◄──────────────────┘                  │
│             (Results)   │(Extraction) │   (Transcript)                       │
│                         └─────────────┘                                      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CALL FLOW SEQUENCE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. USER TRIGGERS CALL                                                      │
│     ┌────────┐      ┌─────────┐      ┌────────┐      ┌─────────┐           │
│     │  User  │─────►│ Frontend│─────►│ Backend│─────►│ Retell  │           │
│     └────────┘      └─────────┘      └────────┘      └─────────┘           │
│                     POST /calls/trigger              create_web_call()      │
│                                                                             │
│  2. CALL IN PROGRESS                                                        │
│     ┌────────┐      ┌─────────┐      ┌────────────────────────┐            │
│     │  User  │◄────►│ Browser │◄────►│ Retell AI (Voice/LLM)  │            │
│     │ (Voice)│      │(WebRTC) │      │ Uses system_prompt     │            │
│     └────────┘      └─────────┘      └────────────────────────┘            │
│                                                                             │
│  3. CALL ENDS - WEBHOOK                                                     │
│     ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐         │
│     │ Retell  │─────►│ Backend │─────►│ OpenAI  │─────►│Supabase │         │
│     └─────────┘      └─────────┘      └─────────┘      └─────────┘         │
│     POST /webhooks   Process         Extract          Save                  │
│     /retell          Transcript      Results          Results               │
│                                                                             │
│  4. USER VIEWS RESULTS                                                      │
│     ┌────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐         │
│     │  User  │◄─────│ Frontend│◄─────│ Backend │◄─────│Supabase │         │
│     └────────┘      └─────────┘      └─────────┘      └─────────┘         │
│                     GET /calls/{id}                   Fetch Results         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Low-Level Design

### Class Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLASS STRUCTURE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐      ┌─────────────────────┐                       │
│  │    AgentService     │      │    RetellService    │                       │
│  ├─────────────────────┤      ├─────────────────────┤                       │
│  │ - db: SupabaseClient│      │ - client: Retell    │                       │
│  │ - retell: RetellSvc │      ├─────────────────────┤                       │
│  ├─────────────────────┤      │ + create_llm()      │                       │
│  │ + create_agent()    │─────►│ + create_agent()    │                       │
│  │ + get_agent()       │      │ + update_agent()    │                       │
│  │ + update_agent()    │      │ + delete_agent()    │                       │
│  │ + delete_agent()    │      │ + create_web_call() │                       │
│  │ + list_agents()     │      │ + get_call()        │                       │
│  └─────────────────────┘      └─────────────────────┘                       │
│            │                            │                                   │
│            │                            │                                   │
│            ▼                            ▼                                   │
│  ┌─────────────────────┐      ┌─────────────────────┐                       │
│  │     CallService     │      │ TranscriptProcessor │                       │
│  ├─────────────────────┤      ├─────────────────────┤                       │
│  │ - db: SupabaseClient│      │ - client: OpenAI    │                       │
│  │ - retell: RetellSvc │      ├─────────────────────┤                       │
│  ├─────────────────────┤      │ + process_call()    │                       │
│  │ + trigger_call()    │      │ + _extract_routine()│                       │
│  │ + get_call()        │      │ + _extract_emergency│                       │
│  │ + list_calls()      │      │ + _validate_results │                       │
│  │ + update_call()     │      └─────────────────────┘                       │
│  └─────────────────────┘                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Pydantic Models

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SCHEMA MODELS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐      ┌─────────────────────────┐              │
│  │      VoiceSettings      │      │       AgentCreate       │              │
│  ├─────────────────────────┤      ├─────────────────────────┤              │
│  │ voice_id: str           │      │ name: str               │              │
│  │ voice_speed: float      │      │ description: str?       │              │
│  │ voice_temperature: float│      │ system_prompt: str      │              │
│  │ enable_backchannel: bool│◄─────│ begin_message: str?     │              │
│  │ backchannel_frequency   │      │ voice_settings          │──────┐       │
│  │ responsiveness: float   │      │ emergency_triggers: []  │      │       │
│  │ interruption_sensitivity│      │ is_active: bool         │      │       │
│  │ denoising_mode: bool    │      └─────────────────────────┘      │       │
│  │ end_call_after_silence  │                                       │       │
│  └─────────────────────────┘                                       │       │
│                                                                    │       │
│  ┌─────────────────────────┐      ┌─────────────────────────┐     │       │
│  │    CallTriggerRequest   │      │       CallResults       │     │       │
│  ├─────────────────────────┤      ├─────────────────────────┤     │       │
│  │ agent_id: str           │      │ call_outcome: enum      │     │       │
│  │ driver_name: str        │      │ is_emergency: bool      │     │       │
│  │ load_number: str        │      │ driver_status: enum?    │     │       │
│  │ origin: str?            │      │ current_location: str?  │     │       │
│  │ destination: str?       │      │ eta: str?               │     │       │
│  │ expected_eta: str?      │      │ delay_reason: str?      │     │       │
│  └─────────────────────────┘      │ emergency_type: enum?   │     │       │
│                                   │ confidence_score: float │     │       │
│                                   └─────────────────────────┘     │       │
│                                                                    │       │
│  ┌─────────────────────────┐                                      │       │
│  │      AgentResponse      │◄─────────────────────────────────────┘       │
│  ├─────────────────────────┤                                              │
│  │ id: str                 │                                              │
│  │ retell_agent_id: str?   │                                              │
│  │ retell_llm_id: str?     │                                              │
│  │ created_at: datetime    │                                              │
│  │ updated_at: datetime    │                                              │
│  └─────────────────────────┘                                              │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### Enums

```python
class CallOutcome(str, Enum):
    IN_TRANSIT_UPDATE = "In-Transit Update"
    ARRIVAL_CONFIRMATION = "Arrival Confirmation"
    EMERGENCY_ESCALATION = "Emergency Escalation"
    INCOMPLETE = "Incomplete"
    UNKNOWN = "Unknown"

class DriverStatus(str, Enum):
    DRIVING = "Driving"
    DELAYED = "Delayed"
    ARRIVED = "Arrived"
    UNLOADING = "Unloading"
    WAITING = "Waiting"
    UNKNOWN = "Unknown"

class EmergencyType(str, Enum):
    ACCIDENT = "Accident"
    BREAKDOWN = "Breakdown"
    MEDICAL = "Medical"
    OTHER = "Other"
```

---

## 🔄 Webhook Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WEBHOOK PROCESSING                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Retell AI                         Backend                                  │
│     │                                 │                                     │
│     │  POST /webhooks/retell          │                                     │
│     │  {                              │                                     │
│     │    "event": "call_ended",       │                                     │
│     │    "call_id": "...",            │                                     │
│     │    "transcript": "...",         │                                     │
│     │    "metadata": {...}            │                                     │
│     │  }                              │                                     │
│     │─────────────────────────────────►                                     │
│     │                                 │                                     │
│     │                                 │  1. Validate webhook                │
│     │                                 │  2. Update call status              │
│     │                                 │  3. Extract results (OpenAI)        │
│     │                                 │  4. Validate with Pydantic          │
│     │                                 │  5. Save to database                │
│     │                                 │                                     │
│     │         200 OK                  │                                     │
│     │◄─────────────────────────────────                                     │
│     │                                 │                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE SCHEMA                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐         ┌─────────────────┐         ┌───────────────┐ │
│  │     agents      │         │      calls      │         │  call_results │ │
│  ├─────────────────┤         ├─────────────────┤         ├───────────────┤ │
│  │ id (PK)         │◄────────│ agent_id (FK)   │         │ id (PK)       │ │
│  │ name            │    1:N  │ id (PK)         │◄────────│ call_id (FK)  │ │
│  │ description     │         │ retell_call_id  │    1:1  │ call_outcome  │ │
│  │ agent_type      │         │ driver_name     │         │ is_emergency  │ │
│  │ system_prompt   │         │ load_number     │         │ driver_status │ │
│  │ begin_message   │         │ origin          │         │ location      │ │
│  │ voice_settings  │         │ destination     │         │ eta           │ │
│  │ emergency_triggers│       │ status          │         │ delay_reason  │ │
│  │ is_active       │         │ duration        │         │ emergency_type│ │
│  │ retell_agent_id │         │ transcript      │         │ confidence    │ │
│  │ retell_llm_id   │         │ recording_url   │         │ raw_extraction│ │
│  │ created_at      │         │ created_at      │         │ created_at    │ │
│  │ updated_at      │         │ updated_at      │         └───────────────┘ │
│  └─────────────────┘         │ ended_at        │                           │
│                              └─────────────────┘                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tables

- **agents**: Agent configurations and prompts
- **calls**: Call records with metadata
- **call_results**: Structured extraction results
- **prompts**: Prompts used (currently not required)

---

## 🏗️ Project Structure

```
ai-voice-agent/
├── frontend/                 # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/       # UI components
│   │   │   ├── ui/          # Base UI components (Button, Input, Card)
│   │   │   ├── dashboard/   # Dashboard views
│   │   │   ├── agent/       # Agent configuration (AgentConfigForm)
│   │   │   └── call/        # Call management (WebCallInterface, CallResultsView)
│   │   ├── lib/             # Utilities & API clients
│   │   ├── types/           # TypeScript types
│   │   └── styles/          # Global styles
│   └── public/
│
├── backend/                  # FastAPI
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/      # API endpoints (agents.py, calls.py)
│   │   │   └── webhooks/    # Retell AI webhooks (retell.py)
│   │   ├── core/            # Config & security
│   │   ├── db/              # Database setup
│   │   ├── services/        # Business logic
│   │   │   ├── agent_service.py
│   │   │   ├── call_service.py
│   │   │   ├── retell_service.py
│   │   │   └── transcript_processor.py
│   │   ├── templates/       # Prompt templates (agent_templates.py)
│   │   └── schemas/         # Pydantic schemas (agent.py, call.py)
│   └── tests/
│
└── supabase/                 # Database migrations & config
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Supabase account
- Retell AI account with API key (Free tier as well)
- ngrok (for local webhook testing)

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
WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok-free.app/webhooks/retell
```

3. **Run the application:**
```bash
# Start ngrok tunnel (for webhooks)
ngrok http 8000

# Backend (update WEBHOOK_BASE_URL with ngrok URL)
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm run dev
```

---

## 🔌 API Endpoints

### Agents
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/agents` | List all agents |
| POST | `/api/agents` | Create new agent |
| GET | `/api/agents/{id}` | Get agent details |
| PUT | `/api/agents/{id}` | Update agent |
| DELETE | `/api/agents/{id}` | Delete agent |

### Calls
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/calls/trigger` | Trigger a new call |
| GET | `/api/calls` | List all calls |
| GET | `/api/calls/{id}` | Get call details with results |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks/retell` | Retell AI webhook endpoint |

---

## 🎙️ Voice Agent Configuration

### Optimal Voice Settings
```python
{
    "voice_id": "11labs-Adrian",
    "enable_backchannel": True,
    "backchannel_frequency": 0.8,
    "backchannel_words": ["yeah", "uh-huh", "I see", "right"],
    "interruption_sensitivity": 0.7,
    "responsiveness": 0.8,
    "voice_speed": 1.0,
    "ambient_sound": "office",
    "enable_background_speech_cancellation": True/False,
    "end_call_after_silence_seconds": 30.0
}
```

### Dynamic Variables (Injected into Prompts)
```
{{driver_name}}    - Driver's name
{{load_number}}    - Load/shipment number
{{origin}}         - Origin location
{{destination}}    - Destination location
{{expected_eta}}   - Expected arrival time
```

### Emergency Trigger Phrases (Configurable)
- "accident", "crash", "collision"
- "blowout", "flat tire", "breakdown"
- "medical", "hurt", "injured"
- "emergency", "help", "911"

---

## 🧪 Testing Scenarios

### 1. Normal Driver Check-in
```
Agent: "Hi John, this is Dispatch checking on load 12345. How's it going?"
Driver: "Everything's good, I'm about 2 hours out."
Agent: "Great! What's your current location?"
Driver: "Just passed Columbus on I-70."
Agent: "Perfect. Don't forget to get that POD signed when you arrive!"
```

### 2. Uncooperative Driver (Task B)
```
Agent: "Can you give me a status update?"
Driver: "Fine."
Agent: "What city or highway are you on right now?" [PROBE 1]
Driver: "Yeah."
Agent: "Are you on I-95, I-80, or a different route?" [PROBE 2 - Options]
Driver: "Ok."
Agent: "Alright, I'll let you focus on driving. Safe travels!" [END GRACEFULLY]
```

### 3. Emergency Protocol
```
Agent: "Hi, how's the delivery going?"
Driver: "I've been in an accident!"
Agent: "Oh no! Are you okay? Is anyone hurt?"
Driver: "I'm fine but the truck is damaged."
Agent: "I'm glad you're safe. What's your exact location?"
Driver: "Mile marker 45 on I-95 northbound."
Agent: "Got it. I'm connecting you to a human dispatcher right now."
```

---

## 📝 License

MIT License