"""
TTS Service Factory.

Main factory for creating Text-to-Speech service instances
based on pipeline configuration.
"""
import logging
from typing import Any, Optional

from app.schemas.pipeline import PipelineConfig, TTSService
from app.core.config import settings
from .elevenlabs_service import create_elevenlabs_tts
from .cartesia_service import create_cartesia_tts

logger = logging.getLogger(__name__)


class TTSServiceFactory:
    """
    Factory for creating TTS service instances.
    
    This factory supports multiple TTS providers and handles:
    - Service selection based on configuration
    - API key validation
    - Service-specific configuration
    - Error handling for unsupported services
    
    Supported Services:
    - ElevenLabs (multiple voices and models)
    - Cartesia (sonic-english model)
    - Azure TTS (planned)
    """
    
    def __init__(self):
        """Initialize the TTS service factory."""
        logger.debug("TTSServiceFactory initialized")
    
    def create_tts_service(self, config: PipelineConfig) -> Any:
        """
        Create a TTS service based on pipeline configuration.
        
        This method routes to the appropriate service factory based on
        the TTS service type specified in the configuration.
        
        Args:
            config: Pipeline configuration containing TTS settings
            
        Returns:
            Configured TTS service instance (varies by provider)
            
        Raises:
            ValueError: If service not supported or API key missing
            NotImplementedError: If service planned but not yet implemented
            
        Example:
            >>> factory = TTSServiceFactory()
            >>> config = PipelineConfig(tts_config=TTSConfig(service=TTSService.CARTESIA))
            >>> tts = factory.create_tts_service(config)
        """
        service_type = config.tts_config.service
        
        logger.info(f"Creating TTS service: {service_type.value}")
        
        # Route to appropriate service factory
        if service_type == TTSService.ELEVEN_LABS:
            return self._create_elevenlabs(config)
        
        elif service_type == TTSService.CARTESIA:
            return self._create_cartesia(config)
        
        elif service_type == TTSService.AZURE_TTS:
            return self._create_azure_tts(config)
        
        else:
            raise ValueError(f"Unsupported TTS service: {service_type}")
    
    def _create_elevenlabs(self, config: PipelineConfig) -> Any:
        """
        Create ElevenLabs TTS service.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured ElevenLabsTTSService instance
        """
        return create_elevenlabs_tts(config, settings.elevenlabs_api_key)
    
    def _create_cartesia(self, config: PipelineConfig) -> Any:
        """
        Create Cartesia TTS service.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured CartesiaTTSService instance
        """
        return create_cartesia_tts(config, settings.cartesia_api_key)
    
    def _create_azure_tts(self, config: PipelineConfig) -> Any:
        """
        Create Azure TTS service.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured Azure TTS service instance
            
        Raises:
            NotImplementedError: Azure TTS not yet implemented
        """
        raise NotImplementedError(
            "Azure TTS not yet implemented. "
            "Use ElevenLabs or Cartesia, or contribute an implementation!"
        )


# Singleton instance
_tts_factory: Optional[TTSServiceFactory] = None


def get_tts_service_factory() -> TTSServiceFactory:
    """
    Get or create the TTSServiceFactory singleton.
    
    Returns:
        Singleton instance of TTSServiceFactory
    """
    global _tts_factory
    if _tts_factory is None:
        _tts_factory = TTSServiceFactory()
    return _tts_factory
