# Pipecat Integration Guide

This document provides comprehensive information about the Pipecat voice framework integration in the Dispatcher Voice Agent system.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Setup](#setup)
- [Configuration](#configuration)
- [Supported Services](#supported-services)
- [API Keys](#api-keys)
- [Usage](#usage)
- [Cost Tracking](#cost-tracking)
- [Troubleshooting](#troubleshooting)

## Overview

The Dispatcher Voice Agent now supports **two voice system backends**:

1. **Retell AI**: Managed voice infrastructure with built-in LLM (original implementation)
2. **Pipecat**: Open-source voice framework with flexible multi-service support (new integration)

### Why Pipecat?

Pipecat provides:
- **Multi-Service Flexibility**: Choose your preferred STT, TTS, and LLM providers
- **Cost Optimization**: Mix and match services based on performance and budget
- **Vendor Independence**: Not locked into a single provider
- **WebRTC & WebSocket**: Support for multiple transport protocols
- **Real-time Processing**: Low-latency voice pipeline

## Architecture

### Pipecat Pipeline Flow

```
User Audio Input
    ↓
[Transport] ← Daily.co WebRTC or WebSocket
    ↓
[STT Service] ← Deepgram, Azure Speech, or AssemblyAI
    ↓
[LLM Service] ← OpenAI or Anthropic
    ↓
[TTS Service] ← Cartesia, ElevenLabs, or Azure TTS
    ↓
[Transport] → Audio Output
```

### Key Components

**Backend:**
- `pipecat_service.py`: Core pipeline orchestration and session management
- `pipeline_factory.py`: Creates service instances based on configuration
- `cost_calculator.py`: Tracks operational costs for all services
- `pipecat_calls.py`: API routes for Pipecat-specific operations

**Frontend:**
- `PipecatCallInterface.tsx`: React component using `@pipecat-ai/client-react`
- `AgentConfigForm.tsx`: UI for configuring pipeline services
- `Dashboard.tsx`: Intelligent routing between Retell and Pipecat

## Setup

### 1. Backend Dependencies

Install Pipecat and service dependencies:

```bash
cd backend
source venv/bin/activate  # or create new venv
pip install -r requirements.txt
```

The `requirements.txt` includes:
```
pipecat-ai[daily,deepgram,openai,anthropic,cartesia,silero]>=0.0.40
```

### 2. Frontend Dependencies

Install Pipecat client packages:

```bash
cd frontend
npm install
```

The `package.json` includes:
```json
{
  "@pipecat-ai/client-js": "^0.2.0",
  "@pipecat-ai/client-react": "^0.2.0",
  "@pipecat-ai/daily-transport": "^0.2.0",
  "@daily-co/daily-js": "^0.71.0"
}
```

### 3. Database Migration

Run the Supabase migration to add Pipecat support:

```bash
# In Supabase dashboard or CLI
supabase migration up
```

Or manually run:
```sql
-- Add voice_system and pipeline_config columns
ALTER TABLE agents
ADD COLUMN voice_system TEXT DEFAULT 'retell',
ADD COLUMN pipeline_config JSONB;
```

### 4. Environment Variables

Add these to `backend/.env`:

```bash
# Existing (required for all)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key
RETELL_API_KEY=your_retell_key
FROM_PHONE_NUMBER=your_phone

# Pipecat Services (add as needed)
DEEPGRAM_API_KEY=your_deepgram_key
CARTESIA_API_KEY=your_cartesia_key
ELEVENLABS_API_KEY=your_elevenlabs_key
DAILY_API_KEY=your_daily_key
ANTHROPIC_API_KEY=your_anthropic_key
```

## Configuration

### Creating a Pipecat Agent

1. **Navigate to Agent Configuration**
2. **Select Voice System**: Choose "Pipecat"
3. **Configure Pipeline**:

#### STT (Speech-to-Text)
- **Service**: Deepgram (recommended), Azure Speech, or AssemblyAI
- **Model**: `nova-2` (Deepgram), custom models supported

#### TTS (Text-to-Speech)
- **Service**: Cartesia (recommended for cost), ElevenLabs (best quality), or Azure TTS
- **Voice ID**: Voice identifier from your chosen service
- **Model**: `sonic-english` (Cartesia), `eleven_turbo_v2_5` (ElevenLabs)

#### LLM (Language Model)
- **Service**: OpenAI (recommended), or Anthropic
- **Model**: `gpt-4o`, `gpt-4o-mini`, `claude-3-5-sonnet-20241022`, etc.

#### Transport
- **Daily.co WebRTC** (recommended): Better quality, lower latency
- **WebSocket**: Alternative (not yet fully implemented)

### Example Configuration

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

## Supported Services

### STT Providers

| Service | Models | Cost (per min) | Quality |
|---------|--------|----------------|---------|
| **Deepgram** | nova-2, base | $0.0043 | ⭐⭐⭐⭐⭐ |
| Azure Speech | default | $0.0167 | ⭐⭐⭐⭐ |
| AssemblyAI | default | $0.015 | ⭐⭐⭐⭐ |

### TTS Providers

| Service | Popular Voices | Cost (per char) | Quality |
|---------|---------------|-----------------|---------|
| **Cartesia** | British Lady, etc. | $0.000015 | ⭐⭐⭐⭐ |
| **ElevenLabs** | Rachel, etc. | $0.0003 | ⭐⭐⭐⭐⭐ |
| Azure TTS | Neural voices | $0.000016 | ⭐⭐⭐⭐ |

### LLM Providers

| Service | Models | Cost (per 1K tokens) | Speed |
|---------|--------|---------------------|-------|
| **OpenAI** | gpt-4o, gpt-4o-mini | $0.0025 in / $0.01 out | Fast |
| **Anthropic** | claude-3-5-sonnet | $0.003 in / $0.015 out | Fast |

### Transport

| Transport | Latency | Quality | Complexity |
|-----------|---------|---------|------------|
| **Daily.co WebRTC** | Low | High | Medium |
| WebSocket | Medium | Medium | Low |

## API Keys

### How to Obtain

**Deepgram**: https://console.deepgram.com/
- Sign up → API Keys → Create new key
- Free tier: $200 credit

**Cartesia**: https://play.cartesia.ai/
- Sign up → Settings → API Keys
- Free tier: 1M characters

**ElevenLabs**: https://elevenlabs.io/
- Sign up → Profile → API Key
- Free tier: 10K characters/month

**Daily.co**: https://dashboard.daily.co/
- Sign up → Developers → API Keys
- Free tier: 10K participant minutes/month

**Anthropic**: https://console.anthropic.com/
- Sign up → API Keys
- Pay-as-you-go pricing

## Usage

### Making a Pipecat Call

1. **Create a Pipecat Agent** (see Configuration above)
2. **Trigger a Call**:
   - Go to "Calls" tab
   - Fill in driver details
   - Select your Pipecat agent
   - Click "Create Web Call"

3. **During the Call**:
   - The UI shows connection status
   - Mute/unmute your microphone
   - Visual indicator when bot is speaking
   - End call when finished

4. **View Results**:
   - Extracted conversation data
   - Full transcript
   - **Cost breakdown** showing per-service costs

### API Endpoints

#### Start Pipecat Call
```http
POST /api/calls/trigger
Content-Type: application/json

{
  "agent_id": "uuid",
  "driver_name": "John Doe",
  "load_number": "LOAD-123",
  "origin": "Dallas, TX",
  "destination": "Houston, TX"
}
```

#### End Session
```http
POST /api/pipecat/sessions/{session_id}/end
```

Returns:
```json
{
  "session_id": "uuid",
  "transcript": [...],
  "duration_seconds": 45.2,
  "cost_breakdown": {
    "stt_cost": {...},
    "tts_cost": {...},
    "llm_cost": {...},
    "transport_cost": {...},
    "total_cost_usd": 0.0234
  }
}
```

## Cost Tracking

The system automatically calculates and displays operational costs for each call:

### Cost Components

1. **STT**: Based on audio duration (minutes)
2. **TTS**: Based on characters spoken by bot
3. **LLM**: Based on tokens (input + output)
4. **Transport**: Based on connection duration

### Example Costs

**1-minute call with Deepgram + Cartesia + GPT-4o + Daily.co**:
- STT: ~$0.0043 (1 min)
- TTS: ~$0.0045 (300 chars)
- LLM: ~$0.012 (400 tokens)
- Transport: ~$0.0015 (1 min)
- **Total: ~$0.022 per minute**

### Cost Optimization Tips

1. **Use GPT-4o-mini** instead of GPT-4o (4x cheaper)
2. **Use Cartesia** instead of ElevenLabs (20x cheaper TTS)
3. **Keep calls focused** to minimize duration
4. **Use shorter prompts** to reduce LLM tokens

## Troubleshooting

### Common Issues

#### 1. "Pipecat service not available"
**Solution**: Install dependencies
```bash
pip install 'pipecat-ai[daily,deepgram,openai,anthropic,cartesia,silero]'
```

#### 2. "DAILY_API_KEY not configured"
**Solution**: Add Daily.co API key to `.env`
```bash
DAILY_API_KEY=your_key_here
```

#### 3. "Failed to create Daily room"
**Check**:
- API key is correct
- You haven't exceeded Daily.co free tier limits
- Room name is unique

#### 4. No audio during call
**Check**:
- Microphone permissions granted in browser
- `PipecatClientAudio` component is rendered
- Daily room URL is valid

#### 5. Bot doesn't respond
**Check**:
- LLM API key is valid
- System prompt is not empty
- Check backend logs for errors

#### 6. Call status stuck in "pending"
**Solution**: Check backend logs
```bash
tail -f ~/logs/backend.log
```
Ensure `end_session` API is being called.

### Debug Logging

**Backend**: Logs to `~/logs/backend.log`
```bash
tail -f ~/logs/backend.log | grep -E "PIPELINE|TRANSCRIPT|DB UPDATE"
```

**Frontend**: Check browser console
```javascript
// Look for [Pipecat] logs
console.log('[Pipecat] ...')
```

### Known Limitations

1. **WebSocket transport**: Not yet fully implemented (use Daily.co)
2. **Recording**: Daily.co recording not enabled by default
3. **Phone calls**: WebRTC calls only (no PSTN)

## Comparison: Retell vs Pipecat

| Feature | Retell | Pipecat |
|---------|--------|---------|
| Setup Complexity | Low | Medium |
| Service Flexibility | None | High |
| Cost Control | Fixed | Variable |
| Latency | Low | Low |
| Quality | High | High |
| WebRTC Support | ✅ | ✅ |
| Phone Calls | ✅ | ❌ |
| Multi-STT | ❌ | ✅ |
| Multi-TTS | ❌ | ✅ |
| Multi-LLM | ❌ | ✅ |

## Support

For issues or questions:
1. Check this guide first
2. Review backend logs: `~/logs/backend.log`
3. Check browser console for frontend errors
4. Review Pipecat docs: https://docs.pipecat.ai/

## License

This integration follows the same license as the main Dispatcher Voice Agent project.
