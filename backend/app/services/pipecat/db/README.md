# Database Layer Architecture

This directory contains the database abstraction layer for Pipecat services, following SOLID principles and clean architecture patterns.

## Overview

The database layer has been refactored to separate concerns and follow proper low-level design principles:

1. **Interface (DBConnector)** - Abstract interface defining database operations
2. **Implementation (SupabaseDBConnector)** - Concrete Supabase implementation
3. **Models** - Pydantic models for data validation and transfer
4. **Business Logic** - Separated into specialized services

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ARCHITECTURE LAYERS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │         Business Logic Layer                           │     │
│  │  (CallCompletionService, TranscriptFormatter)          │     │
│  └────────────────────────────────────────────────────────┘     │
│                          │                                       │
│                          ▼                                       │
│  ┌────────────────────────────────────────────────────────┐     │
│  │         Database Abstraction Layer                     │     │
│  │              (DBConnector Interface)                   │     │
│  └────────────────────────────────────────────────────────┘     │
│                          │                                       │
│                          ▼                                       │
│  ┌────────────────────────────────────────────────────────┐     │
│  │         Database Implementation Layer                  │     │
│  │           (SupabaseDBConnector)                        │     │
│  └────────────────────────────────────────────────────────┘     │
│                          │                                       │
│                          ▼                                       │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              Supabase Database                         │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Design Principles Applied

### 1. **Single Responsibility Principle (SRP)**

Each class has one reason to change:

- **DBConnector**: Interface definition only
- **SupabaseDBConnector**: Database operations only (no business logic)
- **CallCompletionService**: Orchestrates completion workflow
- **TranscriptFormatter**: Formats transcripts only
- **Models**: Data validation and transfer only

### 2. **Dependency Inversion Principle (DIP)**

High-level modules depend on abstractions:

```python
# High-level service depends on abstraction
class CallCompletionService:
    def __init__(self):
        self.db_connector: DBConnector = get_db_connector()  # Depends on interface
```

### 3. **Interface Segregation Principle (ISP)**

Focused interface with only needed methods:

```python
class DBConnector(ABC):
    @abstractmethod
    async def find_call_by_session_id(self, session_id: str) -> Optional[str]:
        pass
    
    @abstractmethod
    async def update_call(self, call_id: str, update_data: CallUpdateData) -> bool:
        pass
    
    # ... only methods actually needed
```

### 4. **Open/Closed Principle (OCP)**

Open for extension, closed for modification:

- Can add new database implementations (PostgreSQL, MongoDB, etc.) without changing existing code
- Just implement DBConnector interface

### 5. **Separation of Concerns**

Clear separation between:

- **Data Access**: SupabaseDBConnector
- **Business Logic**: CallCompletionService
- **Data Formatting**: TranscriptFormatter
- **Cost Calculation**: CostCalculator (external)
- **Transcript Processing**: TranscriptProcessor (external)

## File Structure

```
db/
├── __init__.py                 # Module exports
├── README.md                   # This file
├── models.py                   # Pydantic models for DB operations
├── db_connector.py             # Abstract interface
└── supabase_connector.py       # Concrete implementation
```

## Components

### 1. DBConnector (Interface)

**File**: `db_connector.py`

Abstract base class defining all database operations:

```python
class DBConnector(ABC):
    @abstractmethod
    async def find_call_by_session_id(self, session_id: str) -> Optional[str]:
        """Find call ID by session ID"""
        pass
    
    @abstractmethod
    async def get_call_by_id(self, call_id: str) -> Optional[CallRecord]:
        """Retrieve call record by ID"""
        pass
    
    @abstractmethod
    async def update_call(self, call_id: str, update_data: CallUpdateData) -> bool:
        """Update call record"""
        pass
    
    @abstractmethod
    async def upsert_call_results(self, results_data: CallResultsData) -> bool:
        """Insert or update call results"""
        pass
    
    # ... other methods
```

**Benefits**:
- Easy to mock for testing
- Can swap implementations without changing business logic
- Clear contract for database operations

### 2. SupabaseDBConnector (Implementation)

**File**: `supabase_connector.py`

Concrete implementation for Supabase:

```python
class SupabaseDBConnector(DBConnector):
    def __init__(self):
        self.db = get_supabase_client()
    
    async def find_call_by_session_id(self, session_id: str) -> Optional[str]:
        result = self.db.table(Tables.CALLS)\
            .select("id")\
            .eq("retell_call_id", session_id)\
            .execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]["id"]
        return None
    
    # ... other implementations
```

**Responsibilities**:
- Execute Supabase queries
- Handle Supabase-specific errors
- Convert between Supabase responses and Pydantic models
- Log database operations

**Does NOT**:
- Calculate costs
- Process transcripts
- Make business decisions
- Format data for display

### 3. Pydantic Models

**File**: `models.py`

Data transfer objects (DTOs) for database operations:

```python
class CallUpdateData(BaseModel):
    """Data for updating call records"""
    status: str
    ended_at: datetime
    updated_at: datetime
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None

class CallResultsData(BaseModel):
    """Extracted call results"""
    call_id: str
    call_outcome: str
    is_emergency: bool
    driver_status: Optional[str] = None
    # ... other fields

class CallRecord(BaseModel):
    """Call record from database"""
    id: str
    agent_id: str
    driver_name: Optional[str] = None
    # ... other fields
```

**Benefits**:
- Type safety
- Automatic validation
- Clear data contracts
- Easy serialization/deserialization

### 4. CallCompletionService

**File**: `../call_completion_service.py`

Orchestrates the call completion workflow:

```python
class CallCompletionService:
    def __init__(self):
        self.db_connector = get_db_connector()  # Depends on interface
        self.transcript_formatter = get_transcript_formatter()
        self.cost_calculator = get_cost_calculator()
    
    async def complete_call(self, session_id: str, session: PipecatSessionState) -> bool:
        # 1. Find call record
        call_id = await self.db_connector.find_call_by_session_id(session_id)
        
        # 2. Update call status
        await self._update_call_status(call_id, session)
        
        # 3. Process and store results
        await self._process_and_store_results(call_id, session)
```

**Responsibilities**:
- Orchestrate completion workflow
- Coordinate between services
- Handle business logic
- Error handling and logging

### 5. TranscriptFormatter

**File**: `../transcript_formatter.py`

Formats conversation transcripts:

```python
class TranscriptFormatter:
    @staticmethod
    def format_to_string(transcript: List[Dict[str, Any]]) -> str:
        """Convert transcript list to formatted string"""
        return "\n\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in transcript
        ])
```

**Responsibilities**:
- Format transcripts for storage
- Format transcripts for display
- Count messages by role

## Usage Examples

### Basic Usage

```python
from app.services.pipecat.db import get_db_connector
from app.services.pipecat.db.models import CallUpdateData
from datetime import datetime

# Get database connector
db = get_db_connector()

# Find call by session ID
call_id = await db.find_call_by_session_id("session-123")

# Update call
update_data = CallUpdateData(
    status="completed",
    ended_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
    duration_seconds=120
)
success = await db.update_call(call_id, update_data)
```

### Using CallCompletionService

```python
from app.services.pipecat.call_completion_service import get_call_completion_service

# Get service
completion_service = get_call_completion_service()

# Complete call (orchestrates everything)
success = await completion_service.complete_call(session_id, session_state)
```

### Formatting Transcripts

```python
from app.services.pipecat.transcript_formatter import get_transcript_formatter

formatter = get_transcript_formatter()

# Format to string
transcript_text = formatter.format_to_string(transcript_list)

# Get message counts
counts = formatter.get_message_count(transcript_list)
print(f"Total: {counts['total']}, User: {counts['user']}, Assistant: {counts['assistant']}")
```

## Testing

### Mocking the Database

The interface makes testing easy:

```python
from unittest.mock import AsyncMock
from app.services.pipecat.db import DBConnector
from app.services.pipecat.call_completion_service import CallCompletionService

# Create mock
mock_db = AsyncMock(spec=DBConnector)
mock_db.find_call_by_session_id.return_value = "call-123"
mock_db.update_call.return_value = True

# Inject mock
service = CallCompletionService()
service.db_connector = mock_db

# Test
await service.complete_call("session-123", session_state)

# Verify
mock_db.find_call_by_session_id.assert_called_once_with("session-123")
mock_db.update_call.assert_called_once()
```

## Migration Guide

### Old Code (Before Refactoring)

```python
from app.services.pipecat.database_updater import get_database_updater

updater = get_database_updater()
await updater.update_call_completion(session_id, session)
```

### New Code (After Refactoring)

```python
from app.services.pipecat.call_completion_service import get_call_completion_service

completion_service = get_call_completion_service()
await completion_service.complete_call(session_id, session)
```

**Note**: The old `DatabaseUpdater` still works as a legacy adapter, but new code should use `CallCompletionService`.

## Benefits of This Architecture

### 1. **Testability**

- Easy to mock database for unit tests
- Can test business logic without database
- Clear boundaries between components

### 2. **Maintainability**

- Each class has single responsibility
- Easy to understand and modify
- Changes are localized

### 3. **Flexibility**

- Can swap database implementations
- Can add new database backends
- Easy to extend functionality

### 4. **Type Safety**

- Pydantic models provide validation
- Type hints throughout
- Catch errors at development time

### 5. **Reusability**

- Components can be reused independently
- Clear interfaces for integration
- Modular design

## Future Enhancements

1. **Add PostgreSQL Connector**: Implement `PostgreSQLDBConnector` for direct PostgreSQL access
2. **Add Caching Layer**: Implement caching decorator for frequently accessed data
3. **Add Batch Operations**: Support bulk inserts/updates for performance
4. **Add Transaction Support**: Implement transaction management for complex operations
5. **Add Query Builder**: Create fluent query builder for complex queries

## Related Documentation

- [Pipecat Service Architecture](../README.md)
- [WebSocket Transport Guide](../WEBSOCKET_GUIDE.md)
- [Cost Calculator Documentation](../../cost_calculator.py)
