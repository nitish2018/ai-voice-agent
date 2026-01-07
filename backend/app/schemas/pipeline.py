"""
Pipecat Pipeline Configuration Schemas.

Defines the configuration models for building Pipecat voice pipelines with
different service providers (STT, TTS, LLM, Transport).
"""
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class STTService(str, Enum):
    """Supported Speech-to-Text services."""
    DEEPGRAM = "deepgram"
    AZURE_SPEECH = "azure_speech"
    ASSEMBLYAI = "assemblyai"


class TTSService(str, Enum):
    """Supported Text-to-Speech services."""
    ELEVEN_LABS = "eleven_labs"
    AZURE_TTS = "azure_tts"
    CARTESIA = "cartesia"


class LLMService(str, Enum):
    """Supported Large Language Model services."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class TransportType(str, Enum):
    """Supported transport types."""
    WEBSOCKET = "websocket"
    DAILY_WEBRTC = "daily_webrtc"


class CartesiaVoice(str, Enum):
    """Supported Cartesia voice IDs."""
    ENGLISH_MAN = "47c38ca4-5f35-497b-b1a3-415245fb35e1"
    BRITISH_MAN = "0ad65e7f-006c-47cf-bd31-52279d487913"
    ENGLISH_GIRL = "e07c00bc-4134-4eae-9ea4-1a55fb45746b"


# STT Configuration Models

class DeepgramConfig(BaseModel):
    """Deepgram STT configuration."""
    model: str = "nova-2"
    language: str = "en-US"
    interim_results: bool = True


class AzureSpeechConfig(BaseModel):
    """Azure Speech STT configuration."""
    language: str = "en-US"
    recognition_mode: str = "conversation"


class AssemblyAIConfig(BaseModel):
    """AssemblyAI STT configuration."""
    language: str = "en_us"


class STTConfig(BaseModel):
    """Speech-to-Text service configuration."""
    service: STTService = Field(default=STTService.DEEPGRAM)
    model: Optional[str] = Field(default=None, description="Optional model override")
    deepgram: Optional[DeepgramConfig] = Field(default_factory=lambda: DeepgramConfig())
    azure_speech: Optional[AzureSpeechConfig] = Field(default_factory=lambda: AzureSpeechConfig())
    assemblyai: Optional[AssemblyAIConfig] = Field(default_factory=lambda: AssemblyAIConfig())


# TTS Configuration Models

class ElevenLabsConfig(BaseModel):
    """ElevenLabs TTS configuration."""
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default: Rachel
    model_id: str = "eleven_turbo_v2_5"
    stability: float = 0.5
    similarity_boost: float = 0.75
    speed: float = 1.0  # 0.25 to 4.0, default 1.0


class AzureTTSConfig(BaseModel):
    """Azure TTS configuration."""
    voice: str = "en-US-AriaNeural"
    language: str = "en-US"
    speed: float = 1.0  # 0.5 to 2.0, default 1.0


class CartesiaConfig(BaseModel):
    """Cartesia TTS configuration."""
    voice_id: str = CartesiaVoice.BRITISH_MAN  # Default: British Man
    model_id: str = "sonic-english"
    language: str = "en"
    speed: float = 1.0  # 0.5 to 2.0, default 1.0 (normal speed)


class TTSConfig(BaseModel):
    """Text-to-Speech service configuration."""
    service: TTSService = Field(default=TTSService.CARTESIA)
    model: Optional[str] = Field(default=None, description="Optional model override")
    eleven_labs: Optional[ElevenLabsConfig] = Field(default_factory=lambda: ElevenLabsConfig())
    azure_tts: Optional[AzureTTSConfig] = Field(default_factory=lambda: AzureTTSConfig())
    cartesia: Optional[CartesiaConfig] = Field(default_factory=lambda: CartesiaConfig())


# LLM Configuration Models

class OpenAIConfig(BaseModel):
    """OpenAI LLM configuration."""
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: Optional[int] = None


class AnthropicConfig(BaseModel):
    """Anthropic LLM configuration."""
    model: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    max_tokens: int = 1024


class LLMConfig(BaseModel):
    """Large Language Model service configuration."""
    service: LLMService = Field(default=LLMService.OPENAI)
    model: str = Field(default="gpt-4o")
    openai: Optional[OpenAIConfig] = Field(default_factory=lambda: OpenAIConfig())
    anthropic: Optional[AnthropicConfig] = Field(default_factory=lambda: AnthropicConfig())


# Pipeline Configuration

class PipelineConfig(BaseModel):
    """Complete pipeline configuration for Pipecat."""
    stt_config: STTConfig = Field(default_factory=lambda: STTConfig())
    tts_config: TTSConfig = Field(default_factory=lambda: TTSConfig())
    llm_config: LLMConfig = Field(default_factory=lambda: LLMConfig())
    transport: TransportType = Field(default=TransportType.DAILY_WEBRTC)
    enable_interruptions: bool = Field(default=True)
    vad_enabled: bool = Field(default=True)


# Request/Response Models

class PipecatCallRequest(BaseModel):
    """Request to initiate a Pipecat call."""
    agent_id: str
    driver_name: str
    load_number: str
    origin: Optional[str] = None
    destination: Optional[str] = None
    expected_eta: Optional[str] = None
    additional_context: Optional[str] = None


class PipecatCallResponse(BaseModel):
    """Response from initiating a Pipecat call."""
    session_id: str
    daily_room_url: Optional[str] = None
    daily_token: Optional[str] = None
    websocket_url: Optional[str] = None
    status: str = "initialized"


class PipecatSessionMetrics(BaseModel):
    """Metrics from a completed Pipecat session."""
    session_id: str
    duration_seconds: float
    transcript: list = Field(default_factory=list)
    total_input_tokens: Optional[int] = None
    total_output_tokens: Optional[int] = None
    total_chars_spoken: Optional[int] = None
    status: str = "completed"
