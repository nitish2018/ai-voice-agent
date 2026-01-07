# Pipecat Service - Modular Architecture

This directory contains the refactored Pipecat service, organized following SOLID principles and the Single Responsibility Principle.

## Architecture Overview

The monolithic `pipecat_service.py` has been decomposed into specialized modules, each with a single, well-defined responsibility.

### Module Structure

```
pipecat/
├── __init__.py                    # Module initialization
├── pipecat_service.py             # Main service orchestrator
├── daily_room_service.py          # Daily.co room management
├── database_updater.py            # Database operations
├── pipeline_factory.py            # Pipeline component factory
├── pipeline_orchestrator.py       # Pipeline lifecycle management
├── session_manager.py             # Session state management
├── text_processor.py              # Text placeholder processing
├── transcript_capture.py          # Transcript capture processor
└── README.md                      # Documentation
```

## Components

### 1. **DailyRoomService** (`daily_room_service.py`)

**Responsibility**: Manage Daily.co room creation and authentication

**Key Features**:
- Creates Daily.co rooms with appropriate configuration
- Generates meeting tokens for bot authentication
- Handles API communication with Daily.co
- Configurable room expiry and participants

**Dependencies**:
- `aiohttp`: HTTP client for Daily.co API
- `app.core.config`: Application configuration
- `app.schemas.session`: Room configuration models

**Public API**:
- `create_room(config: DailyRoomConfig) -> DailyRoomResponse`
- `get_daily_room_service() -> DailyRoomService` (singleton)

---

### 2. **SessionManager** (`session_manager.py`)

**Responsibility**: Manage session lifecycle and state

**Key Features**:
- Creates and stores new sessions
- Tracks active and completed sessions
- Provides session lookup by ID
- Handles session state transitions
- Manages in-memory session storage
- Cleanup of old completed sessions

**Dependencies**:
- `app.schemas.pipeline`: Pipeline configuration
- `app.schemas.session`: Session data models

**Public API**:
- `create_session(...) -> PipecatSessionState`
- `get_session(session_id) -> Optional[PipecatSessionState]`
- `mark_completed(session_id)`
- `get_active_session_ids() -> List[str]`
- `get_session_manager() -> SessionManager` (singleton)

**Data Model**:
- `PipecatSessionState`: Runtime state (not serializable)
  - Stores pipeline objects, transport, tasks
  - Maintains transcript in real-time
  - Tracks metrics and lifecycle

---

### 3. **TranscriptCaptureProcessor** (`transcript_capture.py`)

**Responsibility**: Capture conversation transcripts from pipeline frames

**Key Features**:
- Intercepts `TranscriptionFrame` (user speech from STT)
- Intercepts `TextFrame` (bot responses from LLM)
- Stores messages with timestamps
- Passes frames through unchanged (transparent processor)

**Dependencies**:
- `pipecat.processors.frame_processor`: Base processor class
- `pipecat.frames.frames`: Frame types
- `app.services.pipecat.session_manager`: Session state

**Public API**:
- `create_transcript_processor(session) -> TranscriptCaptureProcessor`

**Integration**:
- Inserted into pipeline between STT→Context and LLM→TTS
- Two instances: one for user, one for assistant

---

### 4. **TextProcessor** (`text_processor.py`)

**Responsibility**: Process text placeholders for dynamic content

**Key Features**:
- Replace placeholders like `{{driver_name}}` with actual values
- Handle missing values with sensible defaults
- Support for multiple placeholder types
- Consistent placeholder format

**Supported Placeholders**:
- `{{driver_name}}`: Driver's name
- `{{load_number}}`: Load/shipment number
- `{{origin}}`: Origin location
- `{{destination}}`: Destination location
- `{{expected_eta}}`: Expected arrival time

**Dependencies**:
- `app.schemas.pipeline`: Call request models

**Public API**:
- `replace_placeholders(text, request) -> str`
- `get_text_processor() -> TextProcessor` (singleton)

---

### 5. **DatabaseUpdater** (`database_updater.py`)

**Responsibility**: Handle all database operations for sessions

**Key Features**:
- Update call status and metrics
- Store transcripts in formatted text
- Extract structured data from transcripts
- Calculate cost breakdowns
- Upsert call results with costs
- Graceful error handling

**Operations**:
1. Find call by session ID
2. Update call status and duration
3. Format and store transcript
4. Process transcript for structured extraction
5. Calculate service costs
6. Merge cost data into results
7. Upsert to database

**Dependencies**:
- `app.db.database`: Database client
- `app.services.transcript_processor`: Transcript extraction
- `app.services.cost_calculator`: Cost calculation
- `app.services.pipecat.session_manager`: Session state

**Public API**:
- `update_call_completion(session_id, session)`
- `get_database_updater() -> DatabaseUpdater` (singleton)

---

### 6. **PipelineFactory** (`pipeline_factory.py`)

**Responsibility**: Create Pipecat service instances based on configuration

**Key Features:**
- Factory pattern for creating STT, TTS, LLM services
- Supports multiple service providers
- Handles API key validation
- Configures services with appropriate parameters

**Supported Services:**
- **STT**: Deepgram (Azure, AssemblyAI planned)
- **TTS**: ElevenLabs, Cartesia (Azure planned)
- **LLM**: OpenAI, Anthropic

**Dependencies:**
- `app.schemas.pipeline`: Configuration models
- `app.core.config`: API keys
- `pipecat.services.*`: Service implementations

**Public API:**
- `create_stt_service(config) -> STTService`
- `create_tts_service(config) -> TTSService`
- `create_llm_service(config) -> LLMService`
- `get_pipeline_factory() -> PipelineFactory` (singleton)

---

### 7. **PipelineOrchestrator** (`pipeline_orchestrator.py`)

**Responsibility**: Orchestrate pipeline creation and execution

**Key Features**:
- Creates STT, TTS, LLM services via factory
- Configures Daily.co transport
- Assembles complete pipeline with transcript capture
- Creates LLM context with system prompt
- Runs pipeline with error handling
- Handles cleanup and finalization
- Updates database on completion
- Extracts transcript from LLM context as fallback

**Pipeline Assembly**:
```
transport.input() 
  → STT 
  → user_transcript_capture 
  → context_aggregator.user() 
  → LLM 
  → bot_transcript_capture 
  → TTS 
  → transport.output() 
  → context_aggregator.assistant()
```

**Dependencies**:
- `pipecat.pipeline.*`: Pipeline components
- `pipecat.transports.services.daily`: Daily transport
- `app.services.pipeline_factory`: Service factory
- `app.services.pipecat.session_manager`: Session management
- `app.services.pipecat.transcript_capture`: Transcript processor
- `app.services.pipecat.database_updater`: Database operations

**Public API**:
- `run_daily_pipeline(session)`
- `get_pipeline_orchestrator() -> PipelineOrchestrator` (singleton)

---

### 8. **PipecatService** (`pipecat_service.py` - Refactored)

**Responsibility**: Main orchestrator and public API

**Architectural Role**:
- Coordinates all specialized services
- Provides high-level API for call management
- Handles transport routing (Daily.co vs WebSocket)
- Validates Pipecat availability
- Manages service initialization

**Delegations**:
- Room creation → `DailyRoomService`
- Session management → `SessionManager`
- Text processing → `TextProcessor`
- Pipeline execution → `PipelineOrchestrator`
- Database operations → `DatabaseUpdater`
- Cost calculation → `CostCalculator`

**Public API**:
- `start_call(request, config, prompt) -> PipecatCallResponse`
- `end_call(session_id) -> Dict[str, Any]`
- `get_active_sessions() -> List[str]`
- `get_pipecat_service() -> PipecatService` (singleton)

---

## Data Models

### Session Models (`app/schemas/session.py`)

**New Pydantic Models**:

1. **TranscriptMessage**: Single message in transcript
   - `role`: "user" or "assistant"
   - `content`: Message text
   - `timestamp`: When captured

2. **SessionMetrics**: Performance metrics
   - `duration_seconds`: Call duration
   - `total_input_tokens`: LLM input tokens
   - `total_output_tokens`: LLM output tokens
   - `total_chars_spoken`: TTS characters
   - `start_time`, `end_time`: Timestamps

3. **SessionTransport**: Transport connection details
   - `daily_room_url`: Daily.co room URL
   - `daily_token`: Authentication token
   - `websocket_url`: WebSocket URL (if applicable)

4. **PipecatSessionData**: Complete serializable session data
   - Combines all above models
   - Used for API responses and persistence

5. **DailyRoomConfig**: Room creation configuration
   - `session_id`: Session identifier
   - `expiry_hours`: Room lifetime
   - `max_participants`: Participant limit
   - `enable_chat`, `enable_emoji_reactions`: Features

6. **DailyRoomResponse**: Room creation result
   - `room_url`: Room URL
   - `token`: Authentication token
   - `room_name`: Room name
   - `expires_at`: Expiry timestamp

---

## Design Principles Applied

### 1. Single Responsibility Principle (SRP)
Each module has exactly one reason to change:
- **DailyRoomService**: Changes only if Daily.co API changes
- **SessionManager**: Changes only if session lifecycle logic changes
- **DatabaseUpdater**: Changes only if database schema/operations change
- **PipelineOrchestrator**: Changes only if pipeline assembly changes
- **TextProcessor**: Changes only if placeholder logic changes
- **TranscriptCaptureProcessor**: Changes only if transcript capture logic changes

### 2. Dependency Inversion Principle (DIP)
- High-level `PipecatService` depends on abstractions (service interfaces)
- Low-level modules (`DailyRoomService`, etc.) implement those interfaces
- Dependencies injected via factory functions (singletons)

### 3. Open/Closed Principle (OCP)
- Services are open for extension (via inheritance/composition)
- Closed for modification (well-defined interfaces)
- Example: Can add new transcript processors without modifying existing code

### 4. Interface Segregation Principle (ISP)
- Each service exposes only the methods clients need
- No "fat interfaces" with unused methods
- Example: `TextProcessor` only exposes `replace_placeholders()`, not internal helpers

### 5. Proper Use of Pydantic Models
- All data transfer uses Pydantic models for validation
- Models in `app/schemas/` for API contracts
- Dataclasses for runtime state (not serializable)
- Clear separation of concerns

### 6. Comprehensive Documentation
- Docstrings for every module, class, and public method
- Type hints throughout
- Examples in docstrings where helpful
- Architecture documentation (this file)

---

## Benefits of Refactoring

### Before (Monolithic):
- ❌ 699 lines in single file
- ❌ Multiple responsibilities mixed
- ❌ Hard to test individual components
- ❌ Difficult to understand flow
- ❌ Tight coupling between concerns

### After (Modular):
- ✅ ~200 lines per module (manageable size)
- ✅ Single responsibility per module
- ✅ Easy to test each component in isolation
- ✅ Clear separation of concerns
- ✅ Loose coupling via dependency injection
- ✅ Better code reusability
- ✅ Easier to maintain and extend
- ✅ Self-documenting architecture

---

## Testing Strategy

Each module can be tested independently:

```python
# Test DailyRoomService
async def test_create_room():
    service = get_daily_room_service()
    config = DailyRoomConfig(session_id="test-123")
    room = await service.create_room(config)
    assert room.room_url is not None

# Test TextProcessor
def test_replace_placeholders():
    processor = get_text_processor()
    request = PipecatCallRequest(
        agent_id="1",
        driver_name="John",
        load_number="L456"
    )
    result = processor.replace_placeholders(
        "Hi {{driver_name}}, load {{load_number}}",
        request
    )
    assert result == "Hi John, load L456"

# Test SessionManager
def test_session_lifecycle():
    manager = get_session_manager()
    session = manager.create_session("test-1", "call-1", config, "prompt")
    assert "test-1" in manager.get_active_session_ids()
    manager.mark_completed("test-1")
    assert "test-1" not in manager.get_active_session_ids()
```

---

## Migration Notes

### Backward Compatibility

The public API of `PipecatService` remains **exactly the same**:

```python
# Old usage (still works)
service = get_pipecat_service()
response = await service.start_call(request, config, prompt)
metrics = await service.end_call(session_id)
active = service.get_active_sessions()
```

### No Breaking Changes

- All existing imports still work
- API signatures unchanged
- Return types unchanged
- Error handling behavior preserved

### Internal Changes Only

The refactoring is **internal only**:
- External callers see no difference
- Implementation delegated to specialized services
- Functionality preserved exactly

---

## Future Enhancements

With this modular architecture, future improvements are easier:

1. **WebSocket Transport**: Add to `PipelineOrchestrator` without touching other modules
2. **Alternative STT/TTS**: Extend `PipelineFactory` only
3. **Advanced Metrics**: Enhance `SessionMetrics` model and `DatabaseUpdater`
4. **Caching**: Add caching layer in `SessionManager`
5. **Retry Logic**: Add to `DailyRoomService` without affecting callers
6. **Transcript Analysis**: Extend `TranscriptCaptureProcessor` or add new processor

---

## Summary

This refactoring transforms a 699-line monolithic service into a clean, modular architecture with:

- **8 specialized modules** (avg ~150 lines each)
- **6 new Pydantic models** for data validation
- **Single Responsibility** for each component
- **Comprehensive documentation** (docstrings + this README)
- **Zero breaking changes** to public API
- **Easy testing** of individual components
- **SOLID principles** throughout
- **Maintainable** and **extensible** codebase

The functionality remains **exactly the same** - only the internal organization has improved.
