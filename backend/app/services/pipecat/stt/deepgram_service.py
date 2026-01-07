"""
Deepgram STT Service Implementation.

Handles creation and configuration of Deepgram Speech-to-Text services
for the Pipecat pipeline.
"""
import logging
from typing import Any

from app.schemas.pipeline import PipelineConfig
from .base import validate_api_key

logger = logging.getLogger(__name__)

# Import Pipecat Deepgram service
try:
    from pipecat.services.deepgram import DeepgramSTTService
    DEEPGRAM_AVAILABLE = True
except ImportError as e:
    logger.error(f"Deepgram STT service not available: {e}")
    DEEPGRAM_AVAILABLE = False


class DeepgramServiceFactory:
    """
    Factory for creating Deepgram STT service instances.
    
    Responsibilities:
    - Validate Deepgram API key
    - Extract Deepgram configuration from pipeline config
    - Create configured Deepgram STT service instance
    - Log service creation details
    """
    
    @staticmethod
    def create(config: PipelineConfig, api_key: str) -> Any:
        """
        Create a Deepgram STT service instance.
        
        Args:
            config: Pipeline configuration containing Deepgram settings
            api_key: Deepgram API key
            
        Returns:
            Configured DeepgramSTTService instance
            
        Raises:
            ValueError: If API key is missing
            ImportError: If Deepgram service is not available
        """
        if not DEEPGRAM_AVAILABLE:
            raise ImportError("Deepgram STT service not available. Install pipecat with deepgram support.")
        
        # Validate API key
        validate_api_key(api_key, "DEEPGRAM")
        
        # Extract Deepgram-specific configuration
        deepgram_config = config.stt_config.deepgram
        
        logger.info(
            f"Creating Deepgram STT service - "
            f"model: {deepgram_config.model}, "
            f"language: {deepgram_config.language}"
        )
        
        # Create and return Deepgram STT service
        return DeepgramSTTService(
            api_key=api_key,
            model=deepgram_config.model,
            language=deepgram_config.language,
        )


def create_deepgram_stt(config: PipelineConfig, api_key: str) -> Any:
    """
    Convenience function to create Deepgram STT service.
    
    Args:
        config: Pipeline configuration
        api_key: Deepgram API key
        
    Returns:
        Configured DeepgramSTTService instance
    """
    factory = DeepgramServiceFactory()
    return factory.create(config, api_key)
