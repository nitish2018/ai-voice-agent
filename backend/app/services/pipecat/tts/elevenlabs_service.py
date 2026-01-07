"""
ElevenLabs TTS Service Implementation.

Handles creation and configuration of ElevenLabs Text-to-Speech services
for the Pipecat pipeline.
"""
import logging
from typing import Any

from app.schemas.pipeline import PipelineConfig
from .base import validate_api_key

logger = logging.getLogger(__name__)

# Import Pipecat ElevenLabs service
try:
    from pipecat.services.elevenlabs import ElevenLabsTTSService
    ELEVENLABS_AVAILABLE = True
except ImportError as e:
    logger.error(f"ElevenLabs TTS service not available: {e}")
    ELEVENLABS_AVAILABLE = False


class ElevenLabsServiceFactory:
    """
    Factory for creating ElevenLabs TTS service instances.
    
    Responsibilities:
    - Validate ElevenLabs API key
    - Extract ElevenLabs configuration from pipeline config
    - Create configured ElevenLabs TTS service instance
    - Log service creation details
    
    Configuration:
    - voice_id: Voice to use (e.g., "21m00Tcm4TlvDq8ikWAM" for Rachel)
    - model_id: Model to use (e.g., "eleven_turbo_v2_5")
    - speed: Speech rate (0.25 to 4.0, default 1.0)
    - stability: Voice stability (0.0 to 1.0)
    - similarity_boost: Voice similarity (0.0 to 1.0)
    """
    
    @staticmethod
    def create(config: PipelineConfig, api_key: str) -> Any:
        """
        Create an ElevenLabs TTS service instance.
        
        Args:
            config: Pipeline configuration containing ElevenLabs settings
            api_key: ElevenLabs API key
            
        Returns:
            Configured ElevenLabsTTSService instance
            
        Raises:
            ValueError: If API key is missing
            ImportError: If ElevenLabs service is not available
        """
        if not ELEVENLABS_AVAILABLE:
            raise ImportError(
                "ElevenLabs TTS service not available. "
                "Install pipecat with elevenlabs support."
            )
        
        # Validate API key
        validate_api_key(api_key, "ELEVENLABS")
        
        # Extract ElevenLabs-specific configuration
        el_config = config.tts_config.eleven_labs
        
        logger.info(
            f"Creating ElevenLabs TTS service - "
            f"voice: {el_config.voice_id}, "
            f"model: {el_config.model_id}, "
            f"speed: {el_config.speed}"
        )
        
        # Create and return ElevenLabs TTS service
        # Note: speed parameter may not be supported in all Pipecat versions
        return ElevenLabsTTSService(
            api_key=api_key,
            voice_id=el_config.voice_id,
            model=el_config.model_id,
            # speed=el_config.speed,  # Uncomment if SDK supports it
        )


def create_elevenlabs_tts(config: PipelineConfig, api_key: str) -> Any:
    """
    Convenience function to create ElevenLabs TTS service.
    
    Args:
        config: Pipeline configuration
        api_key: ElevenLabs API key
        
    Returns:
        Configured ElevenLabsTTSService instance
    """
    factory = ElevenLabsServiceFactory()
    return factory.create(config, api_key)
