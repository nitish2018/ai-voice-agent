# WebSocket Transport Guide

This guide explains how to use WebSocket transport with Pipecat for voice calls.

## Overview

WebSocket transport provides an alternative to Daily.co WebRTC for voice communication. It allows bidirectional audio streaming over WebSocket connections.

## Architecture

```
Client (Browser/App)
    ↓ WebSocket Connection
[FastAPI WebSocket Endpoint]
    ↓
[PipecatWebSocketTransport]
    ↓
[Pipecat Pipeline]
    ↓ (STT → LLM → TTS)
[PipecatWebSocketTransport]
    ↓
[FastAPI WebSocket Endpoint]
    ↓ WebSocket Connection
Client (Browser/App)
```

## API Endpoints

### 1. Start WebSocket Call

**Endpoint:** `POST /api/calls/trigger`

**Request Body:**
```json
{
  "agent_id": "your-agent-id",
  "driver_name": "John Doe",
  "load_number": "LOAD-123",
  "origin": "Dallas, TX",
  "destination": "Houston, TX"
}
```

**Note:** Make sure the agent's `pipeline_config.transport` is set to `"websocket"`.

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "websocket_url": "/api/pipecat/websocket/550e8400-e29b-41d4-a716-446655440000",
  "status": "initialized"
}
```

### 2. Connect to WebSocket

**Endpoint:** `ws://localhost:8000/api/pipecat/websocket/{session_id}`

**Protocol:** Binary audio frames

## Audio Format

The WebSocket transport expects and sends raw audio in the following format:

- **Sample Rate:** 16kHz
- **Bit Depth:** 16-bit
- **Channels:** Mono (1 channel)
- **Encoding:** PCM (Linear)

## Client Implementation

### JavaScript Example

```javascript
// Start call
const response = await fetch('/api/calls/trigger', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    agent_id: 'your-agent-id',
    driver_name: 'John Doe',
    load_number: 'LOAD-123'
  })
});

const { session_id, websocket_url } = await response.json();

// Connect to WebSocket
const ws = new WebSocket(`ws://localhost:8000${websocket_url}`);

ws.onopen = () => {
  console.log('WebSocket connected');
  
  // Start capturing audio from microphone
  startAudioCapture(ws);
};

ws.onmessage = (event) => {
  // Received audio from bot
  const audioData = event.data;
  playAudio(audioData);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket closed');
};

// Function to capture and send audio
async function startAudioCapture(ws) {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const audioContext = new AudioContext({ sampleRate: 16000 });
  const source = audioContext.createMediaStreamSource(stream);
  const processor = audioContext.createScriptProcessor(4096, 1, 1);
  
  processor.onaudioprocess = (e) => {
    const inputData = e.inputBuffer.getChannelData(0);
    
    // Convert Float32Array to Int16Array
    const pcmData = new Int16Array(inputData.length);
    for (let i = 0; i < inputData.length; i++) {
      pcmData[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
    }
    
    // Send binary audio data
    ws.send(pcmData.buffer);
  };
  
  source.connect(processor);
  processor.connect(audioContext.destination);
}

// Function to play received audio
function playAudio(audioData) {
  const audioContext = new AudioContext({ sampleRate: 16000 });
  
  // Convert Int16Array to Float32Array
  const int16Data = new Int16Array(audioData);
  const float32Data = new Float32Array(int16Data.length);
  for (let i = 0; i < int16Data.length; i++) {
    float32Data[i] = int16Data[i] / 32768;
  }
  
  // Create audio buffer
  const audioBuffer = audioContext.createBuffer(1, float32Data.length, 16000);
  audioBuffer.getChannelData(0).set(float32Data);
  
  // Play audio
  const source = audioContext.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(audioContext.destination);
  source.start();
}
```

### Python Example

```python
import asyncio
import websockets
import json

async def start_call():
    # Start call via REST API
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://localhost:8000/api/calls/trigger',
            json={
                'agent_id': 'your-agent-id',
                'driver_name': 'John Doe',
                'load_number': 'LOAD-123'
            }
        ) as response:
            data = await response.json()
            session_id = data['session_id']
            websocket_url = data['websocket_url']
    
    # Connect to WebSocket
    uri = f"ws://localhost:8000{websocket_url}"
    async with websockets.connect(uri) as websocket:
        # Send and receive audio frames
        audio_data = b'...'  # 16kHz, 16-bit PCM audio
        await websocket.send(audio_data)
        
        # Receive audio from bot
        response_audio = await websocket.recv()
        # Play or process response_audio

asyncio.run(start_call())
```

## Configuration

### Agent Configuration

When creating an agent, set the transport to WebSocket:

```json
{
  "name": "WebSocket Voice Agent",
  "voice_system": "pipecat",
  "pipeline_config": {
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
}
```

## Advantages of WebSocket Transport

1. **Lower Latency:** Direct connection without additional services
2. **Simplicity:** No need for Daily.co account or API keys
3. **Full Control:** Direct audio stream management
4. **Cost Savings:** No transport service fees

## Disadvantages Compared to WebRTC

1. **No Built-in NAT Traversal:** May have issues with some network configurations
2. **No Built-in Echo Cancellation:** Client needs to implement echo cancellation
3. **Less Browser Support:** Older browsers may have issues with Web Audio API

## Troubleshooting

### WebSocket Connection Fails

**Issue:** WebSocket connection closes immediately

**Solutions:**
1. Ensure session_id is valid and session exists
2. Check that backend is running
3. Verify firewall isn't blocking WebSocket connections
4. Check browser console for errors

### No Audio Received

**Issue:** WebSocket connected but no audio is received from bot

**Solutions:**
1. Verify audio format matches (16kHz, 16-bit, mono)
2. Check that you're sending actual audio data, not silence
3. Look at backend logs for pipeline errors
4. Ensure STT/TTS/LLM API keys are configured

### Audio Quality Issues

**Issue:** Audio is choppy, distorted, or has artifacts

**Solutions:**
1. Increase audio buffer size
2. Check network connection quality
3. Ensure sample rate conversion is correct
4. Implement jitter buffer on client side

### High Latency

**Issue:** Significant delay between speech and response

**Solutions:**
1. Use smaller audio chunks (e.g., 512 or 1024 samples)
2. Enable VAD (Voice Activity Detection)
3. Use faster models (e.g., gpt-4o-mini instead of gpt-4o)
4. Check network latency with ping tests

## Best Practices

1. **Chunking:** Send audio in chunks of 1024-4096 samples for best balance of latency and efficiency
2. **Error Handling:** Implement reconnection logic for dropped connections
3. **VAD:** Use Voice Activity Detection to avoid processing silence
4. **Echo Cancellation:** Implement client-side echo cancellation
5. **Monitoring:** Log connection status and errors for debugging

## Testing

Use the provided test client to verify WebSocket transport:

```bash
cd backend
python -m tests.test_websocket_client
```

## Related Files

- `backend/app/services/pipecat/websocket_transport.py` - WebSocket transport implementation
- `backend/app/services/pipecat/pipeline_orchestrator.py` - Pipeline orchestration including WebSocket
- `backend/app/api/routes/pipecat_calls.py` - WebSocket API endpoint
- `backend/app/services/pipecat/pipecat_service.py` - Main service with WebSocket support
