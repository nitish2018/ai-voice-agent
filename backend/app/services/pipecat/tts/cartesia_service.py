"""
Cartesia TTS Service Implementation.

Handles creation and configuration of Cartesia Text-to-Speech services
for the Pipecat pipeline.
"""
import logging
from typing import Any

from app.schemas.pipeline import PipelineConfig
from .base import validate_api_key

logger = logging.getLogger(__name__)

# Import Pipecat Cartesia service
try:
    from pipecat.services.cartesia import CartesiaTTSService
    CARTESIA_AVAILABLE = True
except ImportError as e:
    logger.error(f"Cartesia TTS service not available: {e}")
    CARTESIA_AVAILABLE = False


class CartesiaServiceFactory:
    """
    Factory for creating Cartesia TTS service instances.
    
    Responsibilities:
    - Validate Cartesia API key
    - Extract Cartesia configuration from pipeline config
    - Create configured Cartesia TTS service instance
    - Log service creation details
    
    Configuration:
    - voice_id: Voice to use (e.g., "47c38ca4-5f35-497b-b1a3-415245fb35e1" for English Man)
    - model_id: Model to use (e.g., "sonic-english")
    - speed: Speech rate (0.5 to 2.0, default 1.0)
    - language: Language code (e.g., "en")
    """
    
    @staticmethod
    def create(config: PipelineConfig, api_key: str) -> Any:
        """
        Create a Cartesia TTS service instance.
        
        Args:
            config: Pipeline configuration containing Cartesia settings
            api_key: Cartesia API key
            
        Returns:
            Configured CartesiaTTSService instance
            
        Raises:
            ValueError: If API key is missing
            ImportError: If Cartesia service is not available
        """
        if not CARTESIA_AVAILABLE:
            raise ImportError(
                "Cartesia TTS service not available. "
                "Install pipecat with cartesia support."
            )
        
        # Validate API key
        validate_api_key(api_key, "CARTESIA")
        
        # Extract Cartesia-specific configuration
        cartesia_config = config.tts_config.cartesia
        
        logger.info(
            f"Creating Cartesia TTS service - "
            f"voice_id: {cartesia_config.voice_id}, "
            f"model: {cartesia_config.model_id}, "
            f"speed: {cartesia_config.speed}, "
            f"language: {cartesia_config.language}"
        )
        
        logger.debug(f"Full Cartesia config: {cartesia_config}")
        
        # Create and return Cartesia TTS service
        # Note: Cartesia supports speed parameter (0.5 to 2.0)
        return CartesiaTTSService(
            api_key=api_key,
            voice_id=cartesia_config.voice_id,
            model_id=cartesia_config.model_id,
            speed=cartesia_config.speed,
        )


def create_cartesia_tts(config: PipelineConfig, api_key: str) -> Any:
    """
    Convenience function to create Cartesia TTS service.
    
    Args:
        config: Pipeline configuration
        api_key: Cartesia API key
        
    Returns:
        Configured CartesiaTTSService instance
    """
    factory = CartesiaServiceFactory()
    return factory.create(config, api_key)
