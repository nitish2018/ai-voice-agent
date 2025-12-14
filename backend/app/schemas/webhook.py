"""
Pydantic schemas for Retell AI webhook payloads.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class WebhookEventType(str, Enum):
    """Types of webhook events from Retell AI."""
    CALL_STARTED = "call_started"
    CALL_ENDED = "call_ended"
    CALL_ANALYZED = "call_analyzed"


class DisconnectionReason(str, Enum):
    """Reasons for call disconnection."""
    USER_HANGUP = "user_hangup"
    AGENT_HANGUP = "agent_hangup"
    CALL_TRANSFER = "call_transfer"
    VOICEMAIL_REACHED = "voicemail_reached"
    INACTIVITY = "inactivity"
    MACHINE_DETECTED = "machine_detected"
    MAX_DURATION = "max_duration"
    CONCURRENCY_LIMIT = "concurrency_limit"
    NO_VALID_PAYMENT = "no_valid_payment"
    SCAM_DETECTED = "scam_detected"
    ERROR_INBOUND = "error_inbound"
    DIAL_BUSY = "dial_busy"
    DIAL_FAILED = "dial_failed"
    DIAL_NO_ANSWER = "dial_no_answer"
    ERROR_LLM_WEBSOCKET = "error_llm_websocket"
    ERROR_FRONTEND = "error_frontend"
    ERROR_OTHER = "error_other"
    UNKNOWN = "unknown"


class TranscriptWord(BaseModel):
    """Word-level transcript data."""
    word: str
    start: float
    end: float


class TranscriptEntry(BaseModel):
    """Single entry in transcript."""
    role: str = Field(..., description="'agent' or 'user'")
    content: str
    words: Optional[List[TranscriptWord]] = None


class CallData(BaseModel):
    """Call data from Retell webhook."""
    call_type: str = Field(..., description="Type of call: 'phone_call' or 'web_call'")
    call_id: str = Field(..., description="Unique call identifier")
    agent_id: str = Field(..., description="Agent that handled the call")
    
    # Phone call specific
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    direction: Optional[str] = None  # 'inbound' or 'outbound'
    
    # Status
    call_status: str
    
    # Timestamps
    start_timestamp: Optional[int] = None  # milliseconds since epoch
    end_timestamp: Optional[int] = None
    
    # Disconnection
    disconnection_reason: Optional[str] = None
    
    # Transcript
    transcript: Optional[str] = None
    transcript_object: Optional[List[TranscriptEntry]] = None
    transcript_with_tool_calls: Optional[List[Dict[str, Any]]] = None
    
    # Recording
    recording_url: Optional[str] = None
    recording_multi_channel_url: Optional[str] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    retell_llm_dynamic_variables: Optional[Dict[str, Any]] = None
    
    # Analysis (if call_analyzed event)
    call_analysis: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"  # Allow additional fields


class RetellWebhookPayload(BaseModel):
    """Complete webhook payload from Retell AI."""
    event: WebhookEventType
    call: CallData


class WebhookResponse(BaseModel):
    """Response to send back to Retell webhook."""
    status: str = "ok"
    message: Optional[str] = None
