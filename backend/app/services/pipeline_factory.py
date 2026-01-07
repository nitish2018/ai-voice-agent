"""
Pipeline Factory - Creates Pipecat service instances based on configuration.

This factory handles the instantiation of STT, TTS, and LLM services
from various providers based on the pipeline configuration.
"""
import logging
from typing import Any

from app.schemas.pipeline import (
    PipelineConfig,
    STTService,
    TTSService,
    LLMService,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

# Import Pipecat service modules
try:
    # STT Services
    from pipecat.services.deepgram import DeepgramSTTService
    # from pipecat.services.azure import AzureSTTService  # Not yet implemented
    # from pipecat.services.assemblyai import AssemblyAISTTService  # Not yet implemented
    
    # TTS Services
    from pipecat.services.elevenlabs import ElevenLabsTTSService
    from pipecat.services.cartesia import CartesiaTTSService
    # from pipecat.services.azure import AzureTTSService  # Not yet implemented
    
    # LLM Services
    from pipecat.services.openai import OpenAILLMService
    from pipecat.services.anthropic import AnthropicLLMService
    
    PIPECAT_AVAILABLE = True
except ImportError as e:
    logger.error(f"Pipecat services not available: {e}")
    PIPECAT_AVAILABLE = False


class PipelineFactory:
    """Factory for creating Pipecat pipeline components."""
    
    def __init__(self):
        """Initialize the pipeline factory."""
        if not PIPECAT_AVAILABLE:
            logger.warning("Pipecat services not available")
    
    def create_stt_service(self, config: PipelineConfig) -> Any:
        """
        Create a Speech-to-Text service based on configuration.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured STT service instance
            
        Raises:
            ValueError: If service not supported or API key missing
        """
        service_type = config.stt_config.service
        
        if service_type == STTService.DEEPGRAM:
            if not settings.deepgram_api_key:
                raise ValueError("DEEPGRAM_API_KEY not configured")
            
            deepgram_config = config.stt_config.deepgram
            logger.info(f"Creating Deepgram STT service with model: {deepgram_config.model}")
            
            return DeepgramSTTService(
                api_key=settings.deepgram_api_key,
                model=deepgram_config.model,
                language=deepgram_config.language,
            )
        
        elif service_type == STTService.AZURE_SPEECH:
            raise NotImplementedError("Azure Speech STT not yet implemented")
        
        elif service_type == STTService.ASSEMBLYAI:
            raise NotImplementedError("AssemblyAI STT not yet implemented")
        
        else:
            raise ValueError(f"Unsupported STT service: {service_type}")
    
    def create_tts_service(self, config: PipelineConfig) -> Any:
        """
        Create a Text-to-Speech service based on configuration.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured TTS service instance
            
        Raises:
            ValueError: If service not supported or API key missing
        """
        service_type = config.tts_config.service
        
        if service_type == TTSService.ELEVEN_LABS:
            if not settings.elevenlabs_api_key:
                raise ValueError("ELEVENLABS_API_KEY not configured")
            
            el_config = config.tts_config.eleven_labs
            logger.info(f"Creating ElevenLabs TTS service with voice: {el_config.voice_id}, speed: {el_config.speed}")
            
            # Note: ElevenLabs uses 'speed' parameter (0.25 to 4.0)
            return ElevenLabsTTSService(
                api_key=settings.elevenlabs_api_key,
                voice_id=el_config.voice_id,
                model=el_config.model_id,
                # speed=el_config.speed,  # Uncomment if ElevenLabs SDK supports it
            )
        
        elif service_type == TTSService.CARTESIA:
            if not settings.cartesia_api_key:
                raise ValueError("CARTESIA_API_KEY not configured")
            
            cartesia_config = config.tts_config.cartesia
            logger.info(f"Creating Cartesia TTS service with voice_id: {cartesia_config.voice_id}, model: {cartesia_config.model_id}, speed: {cartesia_config.speed}")
            logger.info(f"Full Cartesia config: {cartesia_config}")
            
            # Note: Cartesia uses 'speed' parameter (typically 0.5 to 2.0)
            return CartesiaTTSService(
                api_key=settings.cartesia_api_key,
                voice_id=cartesia_config.voice_id,
                model_id=cartesia_config.model_id,
                speed=cartesia_config.speed,  # Pass speed to Cartesia
            )
        
        elif service_type == TTSService.AZURE_TTS:
            raise NotImplementedError("Azure TTS not yet implemented")
        
        else:
            raise ValueError(f"Unsupported TTS service: {service_type}")
    
    def create_llm_service(self, config: PipelineConfig) -> Any:
        """
        Create a Large Language Model service based on configuration.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured LLM service instance
            
        Raises:
            ValueError: If service not supported or API key missing
        """
        service_type = config.llm_config.service
        
        if service_type == LLMService.OPENAI:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            
            openai_config = config.llm_config.openai
            logger.info(f"Creating OpenAI LLM service with model: {openai_config.model}")
            
            return OpenAILLMService(
                api_key=settings.openai_api_key,
                model=openai_config.model,
            )
        
        elif service_type == LLMService.ANTHROPIC:
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            
            anthropic_config = config.llm_config.anthropic
            logger.info(f"Creating Anthropic LLM service with model: {anthropic_config.model}")
            
            return AnthropicLLMService(
                api_key=settings.anthropic_api_key,
                model=anthropic_config.model,
            )
        
        else:
            raise ValueError(f"Unsupported LLM service: {service_type}")


# Singleton instance
_pipeline_factory: PipelineFactory = None


def get_pipeline_factory() -> PipelineFactory:
    """Get or create the PipelineFactory singleton."""
    global _pipeline_factory
    if _pipeline_factory is None:
        _pipeline_factory = PipelineFactory()
    return _pipeline_factory
