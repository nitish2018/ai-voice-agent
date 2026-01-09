"""
Pydantic schemas for Call-related data structures.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CallStatus(str, Enum):
    """Status of a call."""
    PENDING = "pending"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    VOICEMAIL = "voicemail"


class CallOutcome(str, Enum):
    """Outcome classification for logistics calls."""
    IN_TRANSIT_UPDATE = "In-Transit Update"
    ARRIVAL_CONFIRMATION = "Arrival Confirmation"
    EMERGENCY_ESCALATION = "Emergency Escalation"
    INCOMPLETE = "Incomplete"
    UNKNOWN = "Unknown"


class DriverStatus(str, Enum):
    """Driver status options."""
    DRIVING = "Driving"
    DELAYED = "Delayed"
    ARRIVED = "Arrived"
    UNLOADING = "Unloading"
    WAITING = "Waiting"
    UNKNOWN = "Unknown"


class EmergencyType(str, Enum):
    """Types of emergencies."""
    ACCIDENT = "Accident"
    BREAKDOWN = "Breakdown"
    MEDICAL = "Medical"
    OTHER = "Other"


# Request schemas
class CallTriggerRequest(BaseModel):
    """Schema for triggering a new web call."""
    agent_id: str = Field(..., description="ID of the agent to use")
    driver_name: str = Field(..., min_length=1, max_length=100, description="Driver's name")
    load_number: str = Field(..., min_length=1, max_length=50, description="Load/shipment number")

    # Optional context
    origin: Optional[str] = Field(None, description="Origin location")
    destination: Optional[str] = Field(None, description="Destination location")
    expected_eta: Optional[str] = Field(None, description="Expected arrival time")
    additional_context: Optional[Dict[str, Any]] = Field(None, description="Additional context data")
    transport: Optional[str] = Field(None, description="Transport type")


class CallBase(BaseModel):
    """Base call schema."""
    agent_id: str
    driver_name: str
    load_number: str
    origin: Optional[str] = None
    destination: Optional[str] = None


class CallCreate(CallBase):
    """Schema for creating a call record."""
    retell_call_id: Optional[str] = None
    access_token: Optional[str] = None
    status: CallStatus = CallStatus.PENDING


class CallResponse(CallBase):
    """Schema for call response with full details."""
    id: str
    retell_call_id: Optional[str]
    access_token: Optional[str] = None
    status: CallStatus
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None
    recording_url: Optional[str] = None
    transport: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    ended_at: Optional[datetime] = None

    # Extracted results
    results: Optional["CallResultsResponse"] = None

    class Config:
        from_attributes = True


class CallListResponse(BaseModel):
    """Schema for listing calls."""
    calls: List[CallResponse]
    total: int


# Call results schemas (structured data extraction)
class RoutineCallResults(BaseModel):
    """Structured results for routine check-in calls."""
    call_outcome: CallOutcome = CallOutcome.UNKNOWN
    driver_status: DriverStatus = DriverStatus.UNKNOWN
    current_location: Optional[str] = None
    eta: Optional[str] = None
    delay_reason: Optional[str] = None
    unloading_status: Optional[str] = None
    pod_reminder_acknowledged: bool = False


class EmergencyCallResults(BaseModel):
    """Structured results for emergency calls."""
    call_outcome: CallOutcome = CallOutcome.EMERGENCY_ESCALATION
    emergency_type: EmergencyType = EmergencyType.OTHER
    safety_status: Optional[str] = None
    injury_status: Optional[str] = None
    emergency_location: Optional[str] = None
    load_secure: Optional[bool] = None
    escalation_status: str = "Pending"


class CallResultsBase(BaseModel):
    """Base schema for call results."""
    call_id: str
    call_outcome: CallOutcome
    is_emergency: bool = False

    # Routine fields
    driver_status: Optional[DriverStatus] = None
    current_location: Optional[str] = None
    eta: Optional[str] = None
    delay_reason: Optional[str] = None
    unloading_status: Optional[str] = None
    pod_reminder_acknowledged: Optional[bool] = None

    # Emergency fields
    emergency_type: Optional[EmergencyType] = None
    safety_status: Optional[str] = None
    injury_status: Optional[str] = None
    emergency_location: Optional[str] = None
    load_secure: Optional[bool] = None
    escalation_status: Optional[str] = None

    # Raw extraction data
    raw_extraction: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None


class CallResultsCreate(CallResultsBase):
    """Schema for creating call results."""
    pass


class CallResultsResponse(CallResultsBase):
    """Schema for call results response."""
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Update forward reference
CallResponse.model_rebuild()


# Transcript schemas
class TranscriptMessage(BaseModel):
    """A single message in the transcript."""
    role: str = Field(..., description="'agent' or 'user'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[float] = None
    words: Optional[List[Dict[str, Any]]] = None


class TranscriptData(BaseModel):
    """Full transcript data from a call."""
    messages: List[TranscriptMessage]
    duration_seconds: Optional[int] = None