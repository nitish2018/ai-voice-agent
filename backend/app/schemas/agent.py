"""
Pydantic schemas for Agent-related data structures.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class AgentType(str, Enum):
    """Types of voice agents."""
    DISPATCH_CHECKIN = "dispatch_checkin"
    EMERGENCY_PROTOCOL = "emergency_protocol"
    CUSTOM = "custom"


class VoiceSystem(str, Enum):
    """Voice system backend to use."""
    RETELL = "retell"
    PIPECAT = "pipecat"


class VoiceSettings(BaseModel):
    """Voice configuration settings for natural conversation."""
    voice_id: str = Field(default="11labs-Adrian", description="Retell voice ID")
    voice_speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech rate")
    voice_temperature: float = Field(default=1.0, ge=0, le=2, description="Voice stability")
    volume: float = Field(default=1.0, ge=0, le=2, description="Voice volume")

    # Natural conversation settings
    enable_backchannel: bool = Field(default=True, description="Enable 'uh-huh', 'yeah' responses")
    backchannel_frequency: float = Field(default=0.8, ge=0, le=1, description="How often to backchannel")
    backchannel_words: List[str] = Field(
        default=["yeah", "uh-huh", "I see", "right", "okay"],
        description="Words used for backchanneling"
    )

    # Responsiveness
    responsiveness: float = Field(default=0.8, ge=0, le=1, description="Response speed after user stops")
    interruption_sensitivity: float = Field(default=0.7, ge=0, le=1, description="How easily user can interrupt")

    # Ambient settings
    ambient_sound: Optional[str] = Field(default="office", description="Background ambient sound")
    ambient_sound_volume: float = Field(default=0.3, ge=0, le=1, description="Ambient sound volume")

    # Language
    language: str = Field(default="en-US", description="Agent language")

    # Keywords for speech recognition
    boosted_keywords: List[str] = Field(
        default=[],
        description="Words to boost in speech recognition"
    )

    # Background speech cancellation (for noisy environments)
    enable_background_speech_cancellation: bool = Field(
        default=False,
        description="Filter out background conversations and noise"
    )

    # End call after silence
    end_call_after_silence_seconds: float = Field(
        default=30.0,
        ge=10.0,
        le=120.0,
        description="Automatically end call after this many seconds of silence"
    )


class AgentState(BaseModel):
    """A single state in the agent's conversation flow."""
    name: str = Field(..., description="State name identifier")
    state_prompt: str = Field(..., description="Prompt for this conversation state")
    transitions: Dict[str, str] = Field(
        default={},
        description="Mapping of conditions to next state names"
    )
    tools: List[Dict[str, Any]] = Field(
        default=[],
        description="Tools available in this state"
    )


class AgentBase(BaseModel):
    """Base agent schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Agent display name")
    description: Optional[str] = Field(None, max_length=500, description="Agent description")
    agent_type: AgentType = Field(default=AgentType.CUSTOM, description="Type of agent")
    
    # Voice system selection
    voice_system: VoiceSystem = Field(default=VoiceSystem.RETELL, description="Voice system backend to use")

    # Main prompt
    system_prompt: str = Field(..., description="Main system prompt for the agent")
    begin_message: Optional[str] = Field(None, description="Initial greeting message")

    # Voice settings (for Retell)
    voice_settings: VoiceSettings = Field(default_factory=VoiceSettings)
    
    # Pipecat pipeline configuration (for Pipecat)
    pipeline_config: Optional[Dict[str, Any]] = Field(None, description="Pipecat pipeline configuration")

    # Multi-state configuration
    states: List[AgentState] = Field(default=[], description="Conversation states")
    starting_state: Optional[str] = Field(None, description="Initial state name")

    # Emergency handling
    emergency_triggers: List[str] = Field(
        default=["accident", "blowout", "emergency", "breakdown", "medical", "help", "crash"],
        description="Phrases that trigger emergency protocol"
    )

    # Metadata
    is_active: bool = Field(default=True, description="Whether agent is active")


class AgentCreate(AgentBase):
    """Schema for creating a new agent."""
    pass


class AgentUpdate(BaseModel):
    """Schema for updating an existing agent."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    agent_type: Optional[AgentType] = None
    voice_system: Optional[VoiceSystem] = None
    system_prompt: Optional[str] = None
    begin_message: Optional[str] = None
    voice_settings: Optional[VoiceSettings] = None
    pipeline_config: Optional[Dict[str, Any]] = None
    states: Optional[List[AgentState]] = None
    starting_state: Optional[str] = None
    emergency_triggers: Optional[List[str]] = None
    is_active: Optional[bool] = None


class AgentResponse(AgentBase):
    """Schema for agent response with database fields."""
    id: str = Field(..., description="Unique agent ID")
    voice_system: VoiceSystem = Field(default=VoiceSystem.RETELL)
    pipeline_config: Optional[Dict[str, Any]] = Field(None)
    retell_agent_id: Optional[str] = Field(None, description="Retell AI agent ID")
    retell_llm_id: Optional[str] = Field(None, description="Retell LLM ID")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """Schema for listing agents."""
    agents: List[AgentResponse]
    total: int


class DenoisingMode(str, Enum):
    """Enum for denoising mode for agent"""
    NOISE_AND_BACKGROUND_SPEECH_CANCELLATION = "noise-and-background-speech-cancellation"
    NOISE_CANCELLATION = "noise-cancellation"