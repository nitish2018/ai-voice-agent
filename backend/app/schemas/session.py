"""
Session Models for Pipecat Call Sessions.

Defines Pydantic models for managing voice call session state,
including metrics, transcripts, and lifecycle information.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.schemas.pipeline import PipelineConfig


class TranscriptMessage(BaseModel):
    """A single message in the conversation transcript."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="When the message was captured")


class SessionMetrics(BaseModel):
    """Performance and usage metrics for a session."""
    duration_seconds: Optional[float] = Field(None, description="Total call duration in seconds")
    total_input_tokens: Optional[int] = Field(None, description="Total LLM input tokens consumed")
    total_output_tokens: Optional[int] = Field(None, description="Total LLM output tokens generated")
    total_chars_spoken: Optional[int] = Field(None, description="Total characters sent to TTS")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Session start timestamp")
    end_time: Optional[datetime] = Field(None, description="Session end timestamp")


class SessionTransport(BaseModel):
    """Transport connection details for a session."""
    daily_room_url: Optional[str] = Field(None, description="Daily.co room URL for WebRTC")
    daily_token: Optional[str] = Field(None, description="Authentication token for Daily.co")
    websocket_url: Optional[str] = Field(None, description="WebSocket URL for WebSocket transport")


class PipecatSessionData(BaseModel):
    """
    Complete session data model.
    
    Represents all state and metadata for an active or completed Pipecat call session.
    """
    # Core identifiers
    session_id: str = Field(..., description="Unique session identifier")
    call_id: str = Field(..., description="Associated call record ID")
    
    # Configuration
    config: PipelineConfig = Field(..., description="Pipeline configuration used for this session")
    system_prompt: str = Field(..., description="System prompt for LLM")
    
    # Transport details
    transport: SessionTransport = Field(default_factory=SessionTransport, description="Transport connection info")
    
    # Conversation data
    transcript: List[TranscriptMessage] = Field(default_factory=list, description="Conversation transcript")
    
    # Metrics
    metrics: SessionMetrics = Field(default_factory=SessionMetrics, description="Session performance metrics")
    
    # State tracking
    metrics_saved: bool = Field(default=False, description="Whether metrics have been persisted to database")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "call_id": "call_123",
                "config": {},
                "system_prompt": "You are a dispatcher agent...",
                "transport": {
                    "daily_room_url": "https://example.daily.co/room",
                    "daily_token": "token_abc123"
                },
                "transcript": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi, how can I help?"}
                ],
                "metrics": {
                    "duration_seconds": 120.5,
                    "total_input_tokens": 150,
                    "total_output_tokens": 200
                }
            }
        }


class DailyRoomConfig(BaseModel):
    """Configuration for creating a Daily.co room."""
    session_id: str = Field(..., description="Session ID to use in room name")
    expiry_hours: int = Field(default=1, ge=1, le=24, description="Room expiry time in hours")
    max_participants: int = Field(default=2, ge=2, le=10, description="Maximum number of participants")
    enable_chat: bool = Field(default=False, description="Whether to enable text chat")
    enable_emoji_reactions: bool = Field(default=False, description="Whether to enable emoji reactions")


class DailyRoomResponse(BaseModel):
    """Response from creating a Daily.co room."""
    room_url: str = Field(..., description="URL to join the Daily.co room")
    token: str = Field(..., description="Authentication token for joining")
    room_name: str = Field(..., description="Name of the created room")
    expires_at: datetime = Field(..., description="When the room will expire")
