"""
Pydantic Models for Database Operations.

Defines data transfer objects (DTOs) for database CRUD operations
in the Pipecat service layer.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class CallUpdateData(BaseModel):
    """
    Data model for updating call records.
    
    Used when updating call status, duration, and transcript
    after a Pipecat session completes.
    """
    status: str = Field(..., description="Call status (e.g., 'completed', 'failed')")
    ended_at: datetime = Field(..., description="Timestamp when call ended")
    updated_at: datetime = Field(..., description="Timestamp of last update")
    duration_seconds: Optional[int] = Field(None, description="Call duration in seconds")
    transcript: Optional[str] = Field(None, description="Formatted transcript text")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "status": "completed",
                "ended_at": "2024-01-08T12:00:00Z",
                "updated_at": "2024-01-08T12:00:00Z",
                "duration_seconds": 120,
                "transcript": "USER: Hello\n\nASSISTANT: Hi, how can I help?"
            }
        }

class EmergencyType(str, Enum):
    """Types of emergencies."""
    ACCIDENT = "Accident"
    BREAKDOWN = "Breakdown"
    MEDICAL = "Medical"
    OTHER = "Other"

class CallResultsData(BaseModel):
    """
    Data model for call results with extracted information.
    
    Stores structured data extracted from transcripts,
    including outcomes, driver status, and cost breakdowns.
    """
    call_id: str = Field(..., description="Associated call record ID")
    call_outcome: str = Field(..., description="Outcome of the call")
    is_emergency: bool = Field(default=False, description="Whether this was an emergency call")
    driver_status: Optional[str] = Field(None, description="Driver status if available")
    current_location: Optional[str] = Field(None, description="Driver's current location")
    eta: Optional[str] = Field(None, description="Estimated time of arrival")
    delay_reason: Optional[str] = Field(None, description="Reason for delay if any")
    emergency_type: Optional[str] = Field(None, description="Type of emergency if applicable")
    confidence_score: Optional[float] = Field(None, description="Confidence in extraction")
    raw_extraction: Optional[Dict[str, Any]] = Field(None, description="Raw extraction data including cost")
    emergency_type: EmergencyType = EmergencyType.OTHER
    safety_status: Optional[str] = None
    injury_status: Optional[str] = None
    emergency_location: Optional[str] = None
    load_secure: Optional[bool] = None
    escalation_status: str = "Pending"
    pod_reminder_acknowledged: bool = False
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "call_id": "call_123",
                "call_outcome": "In-Transit Update",
                "is_emergency": False,
                "driver_status": "Driving",
                "current_location": "I-95 near Baltimore",
                "eta": "2 hours",
                "confidence_score": 0.95,
                "raw_extraction": {
                    "cost_breakdown": {
                        "total_cost_usd": 0.025
                    }
                }
            }
        }


class CallRecord(BaseModel):
    """
    Data model for call record retrieved from database.
    
    Represents a call record with all associated metadata.
    """
    id: str = Field(..., description="Call record ID")
    agent_id: str = Field(..., description="Agent ID used for the call")
    driver_name: Optional[str] = Field(None, description="Driver name")
    load_number: Optional[str] = Field(None, description="Load/shipment number")
    origin: Optional[str] = Field(None, description="Origin location")
    destination: Optional[str] = Field(None, description="Destination location")
    status: str = Field(..., description="Current call status")
    created_at: datetime = Field(..., description="When call was created")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "call_123",
                "agent_id": "agent_456",
                "driver_name": "John Doe",
                "load_number": "LOAD-789",
                "origin": "Dallas, TX",
                "destination": "Houston, TX",
                "status": "in_progress",
                "created_at": "2024-01-08T11:00:00Z"
            }
        }


class CallContext(BaseModel):
    """
    Context information for a call.
    
    Used for providing context to transcript processing
    and extraction services.
    """
    driver_name: Optional[str] = Field(None, description="Driver name")
    load_number: Optional[str] = Field(None, description="Load/shipment number")
    origin: Optional[str] = Field(None, description="Origin location")
    destination: Optional[str] = Field(None, description="Destination location")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "driver_name": "John Doe",
                "load_number": "LOAD-789",
                "origin": "Dallas, TX",
                "destination": "Houston, TX"
            }
        }


class TranscriptMessage(BaseModel):
    """
    A single message in a conversation transcript.
    
    Represents one turn in the conversation between
    user and assistant.
    """
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="When message was captured")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "I'm about 30 minutes out",
                "timestamp": "2024-01-08T11:05:00Z"
            }
        }
