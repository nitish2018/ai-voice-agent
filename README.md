# AI Voice Agent Administration Platform

A comprehensive web application for configuring, testing, and reviewing calls made by an adaptive AI voice agent using Retell AI or PipeCat pipeline. Built with React, TypeScript, FastAPI, and Supabase.

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
│   │   │   ├── routes/      # API endpoints (agents.py, calls.py, pipecat_calls.py)
│   │   │   └── webhooks/    # Retell AI webhooks (retell.py)
│   │   ├── core/            # Config & security
│   │   ├── db/              # Database setup
│   │   ├── services/        # Business logic
│   │   │   ├── agent_service.py
│   │   │   ├── call_service.py
│   │   │   ├── retell_service.py
│   │   │   ├── transcript_processor.py
│   │   │   ├── cost_calculator.py
│   │   │   └── pipecat/     # Modular Pipecat services
│   │   │       ├── pipecat_service.py
│   │   │       ├── pipeline_factory.py
│   │   │       ├── pipeline_orchestrator.py
│   │   │       ├── daily_room_service.py
│   │   │       ├── session_manager.py
│   │   │       ├── transcript_capture.py
│   │   │       ├── text_processor.py
│   │   │       ├── database_updater.py
│   │   │       ├── stt/      # Speech-to-Text services
│   │   │       ├── tts/      # Text-to-Speech services
│   │   │       └── llm/      # LLM services
│   │   ├── templates/       # Prompt templates (agent_templates.py)
│   │   └── schemas/         # Pydantic schemas (agent.py, call.py, pipeline.py, etc.)
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

## 🎤 Pipecat Voice Framework

The application now supports **two voice system backends**:

1. **Retell AI**: Managed voice infrastructure with built-in LLM (original)
2. **Pipecat**: Open-source framework with flexible multi-service support (new)

### Why Pipecat?

- **Multi-Service Flexibility**: Choose your preferred STT, TTS, and LLM providers
- **Cost Optimization**: Mix and match services based on performance and budget
- **Vendor Independence**: Not locked into a single provider
- **Real-time Processing**: Low-latency voice pipeline

### Pipecat Architecture

#### Pipeline Flow

```
User Audio Input
    ↓
[Transport] ← Daily.co WebRTC or WebSocket
    ↓
[STT Service] ← Deepgram, Azure Speech, AssemblyAI
    ↓
[Transcript Capture] ← User message capture
    ↓
[LLM Context] ← OpenAI or Anthropic
    ↓
[Transcript Capture] ← Bot message capture
    ↓
[TTS Service] ← Cartesia, ElevenLabs, Azure TTS
    ↓
[Transport] → Audio Output
```

#### Transport Options

1. **Daily.co WebRTC** (Recommended)
   - Low latency, high quality
   - Built-in NAT traversal
   - Requires Daily.co API key
   - Better for production

2. **WebSocket**
   - Direct connection, simple setup
   - No additional service dependencies
   - Client handles audio encoding
   - Better for development/testing

#### Modular Service Structure

Following **SOLID principles** and **Single Responsibility Principle**, the Pipecat service is organized into specialized modules:

```
backend/app/services/pipecat/
├── __init__.py                    # Module exports
├── pipecat_service.py             # Main orchestrator (~330 lines)
├── pipeline_factory.py            # Service factory
├── pipeline_orchestrator.py       # Pipeline execution
├── daily_room_service.py          # Daily.co room management
├── session_manager.py             # Session lifecycle
├── transcript_capture.py          # Transcript processing
├── text_processor.py              # Text utilities
├── database_updater.py            # Database operations
├── stt/                          # Speech-to-Text
│   ├── base.py                   # STT protocol & utilities
│   ├── stt_factory.py            # STT service factory
│   └── deepgram_service.py       # Deepgram implementation
├── tts/                          # Text-to-Speech
│   ├── base.py                   # TTS protocol & utilities
│   ├── tts_factory.py            # TTS service factory
│   ├── elevenlabs_service.py     # ElevenLabs implementation
│   └── cartesia_service.py       # Cartesia implementation
└── llm/                          # Large Language Models
    ├── base.py                   # LLM protocol & utilities
    ├── llm_factory.py            # LLM service factory
    ├── openai_service.py         # OpenAI implementation
    └── anthropic_service.py      # Anthropic implementation
```

### Key Components

#### 1. **PipecatService** - Main Orchestrator
- Coordinates all specialized services
- Provides high-level API for call management
- Handles transport routing (Daily.co vs WebSocket)

#### 2. **PipelineFactory** - Service Creation
- Factory pattern for STT, TTS, LLM services
- Delegates to specialized factories (STT, TTS, LLM)
- Handles API key validation

#### 3. **PipelineOrchestrator** - Pipeline Execution
- Assembles complete pipeline with transcript capture
- Creates LLM context with system prompt
- Runs pipeline with error handling
- Updates database on completion

#### 4. **SessionManager** - Session Lifecycle
- Creates and stores new sessions
- Tracks active and completed sessions
- Manages in-memory session storage

#### 5. **DailyRoomService** - Room Management
- Creates Daily.co rooms with appropriate configuration
- Generates meeting tokens for bot authentication

#### 6. **TranscriptCaptureProcessor** - Transcript Capture
- Intercepts `TranscriptionFrame` (user speech from STT)
- Intercepts `TextFrame` (bot responses from LLM)
- Stores messages with timestamps

#### 7. **DatabaseUpdater** - Database Operations
- Updates call status and metrics
- Stores transcripts in formatted text
- Calculates cost breakdowns

#### 8. **TextProcessor** - Text Utilities
- Replaces placeholders like `{{driver_name}}` with actual values

### Supported Services

#### STT (Speech-to-Text) Providers

| Service | Models | Cost (per min) | Quality |
|---------|--------|----------------|---------|
| **Deepgram** | nova-2, base | $0.0043 | ⭐⭐⭐⭐⭐ |
| Azure Speech | default | $0.0167 | ⭐⭐⭐⭐ |
| AssemblyAI | default | $0.015 | ⭐⭐⭐⭐ |

#### TTS (Text-to-Speech) Providers

| Service | Cost (per char) | Quality |
|---------|-----------------|---------|
| **Cartesia** | $0.000015 | ⭐⭐⭐⭐ |
| **ElevenLabs** | $0.0003 | ⭐⭐⭐⭐⭐ |
| Azure TTS | $0.000016 | ⭐⭐⭐⭐ |

#### LLM Providers

| Service | Models | Cost (per 1K tokens) | Speed |
|---------|--------|---------------------|-------|
| **OpenAI** | gpt-4o, gpt-4o-mini | $0.0025 in / $0.01 out | Fast |
| **Anthropic** | claude-3-5-sonnet | $0.003 in / $0.015 out | Fast |

### Pipecat Configuration

#### Environment Variables

Add these to `backend/.env`:

```bash
# Pipecat Services (add as needed)
DEEPGRAM_API_KEY=your_deepgram_key
CARTESIA_API_KEY=your_cartesia_key
ELEVENLABS_API_KEY=your_elevenlabs_key
DAILY_API_KEY=your_daily_key  # Required for Daily.co WebRTC transport
ANTHROPIC_API_KEY=your_anthropic_key
```

**Note:** `DAILY_API_KEY` is only required if using Daily.co WebRTC transport. WebSocket transport doesn't require any additional API keys.

#### Example Pipeline Config

**Daily.co WebRTC Transport:**
```json
{
  "stt_config": {
    "service": "deepgram",
    "model": "nova-2"
  },
  "tts_config": {
    "service": "cartesia",
    "model": "sonic-english",
    "voice_id": "79a125e8-cd45-4c13-8a67-188112f4dd22"
  },
  "llm_config": {
    "service": "openai",
    "model": "gpt-4o"
  },
  "transport": "daily_webrtc",
  "enable_interruptions": true,
  "vad_enabled": true
}
```

**WebSocket Transport:**
```json
{
  "stt_config": {
    "service": "deepgram",
    "model": "nova-2"
  },
  "tts_config": {
    "service": "cartesia",
    "model": "sonic-english",
    "voice_id": "79a125e8-cd45-4c13-8a67-188112f4dd22"
  },
  "llm_config": {
    "service": "openai",
    "model": "gpt-4o"
  },
  "transport": "websocket",
  "enable_interruptions": true,
  "vad_enabled": true
}
```

#### WebSocket Usage

To use WebSocket transport:

1. **Start a call** with `transport: "websocket"` in the pipeline config
2. **Get the WebSocket URL** from the response: `/api/pipecat/websocket/{session_id}`
3. **Connect** using a WebSocket client: `ws://localhost:8000/api/pipecat/websocket/{session_id}`
4. **Send** raw audio data (16kHz, 16-bit PCM, mono)
5. **Receive** processed audio back from the bot

**Audio Format Requirements:**
- Sample Rate: 16kHz
- Bit Depth: 16-bit
- Channels: Mono
- Encoding: PCM (Linear)

**See full documentation:** `backend/app/services/pipecat/WEBSOCKET_GUIDE.md`

### Cost Tracking

The system automatically calculates operational costs:

**Example: 1-minute call with Deepgram + Cartesia + GPT-4o + Daily.co**
- STT: ~$0.0043 (1 min)
- TTS: ~$0.0045 (300 chars)
- LLM: ~$0.012 (400 tokens)
- Transport: ~$0.0015 (1 min)
- **Total: ~$0.022 per minute**

**Cost Optimization Tips:**
1. Use GPT-4o-mini instead of GPT-4o (4x cheaper)
2. Use Cartesia instead of ElevenLabs (20x cheaper TTS)
3. Keep calls focused to minimize duration

### Design Principles

The Pipecat refactoring follows **SOLID principles**:

#### Single Responsibility Principle (SRP)
Each module has exactly one reason to change:
- **DailyRoomService**: Changes only if Daily.co API changes
- **SessionManager**: Changes only if session lifecycle logic changes
- **DatabaseUpdater**: Changes only if database schema/operations change
- **PipelineOrchestrator**: Changes only if pipeline assembly changes

#### Benefits of Modular Architecture

**Before (Monolithic):**
- ❌ 699 lines in single file
- ❌ Multiple responsibilities mixed
- ❌ Hard to test individual components

**After (Modular):**
- ✅ ~200 lines per module (manageable size)
- ✅ Single responsibility per module
- ✅ Easy to test each component in isolation
- ✅ Clear separation of concerns
- ✅ Loose coupling via dependency injection

### Retell vs Pipecat Comparison

| Feature | Retell | Pipecat (WebRTC) | Pipecat (WebSocket) |
|---------|--------|------------------|---------------------|
| Setup Complexity | Low | Medium | Low |
| Service Flexibility | None | High | High |
| Cost Control | Fixed | Variable | Variable |
| Latency | Low | Low | Medium |
| Quality | High | High | Good |
| WebRTC Support | ✅ | ✅ | ❌ |
| WebSocket Support | ❌ | ❌ | ✅ |
| Phone Calls | ✅ | ❌ | ❌ |
| Multi-STT | ❌ | ✅ | ✅ |
| Multi-TTS | ❌ | ✅ | ✅ |
| Multi-LLM | ❌ | ✅ | ✅ |
| NAT Traversal | ✅ | ✅ | ❌ |
| External Dependencies | Retell API | Daily.co API | None |

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