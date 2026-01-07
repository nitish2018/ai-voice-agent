"""
STT Service Factory.

Main factory for creating Speech-to-Text service instances
based on pipeline configuration.
"""
import logging
from typing import Any, Optional

from app.schemas.pipeline import PipelineConfig, STTService
from app.core.config import settings
from .deepgram_service import create_deepgram_stt

logger = logging.getLogger(__name__)


class STTServiceFactory:
    """
    Factory for creating STT service instances.
    
    This factory supports multiple STT providers and handles:
    - Service selection based on configuration
    - API key validation
    - Service-specific configuration
    - Error handling for unsupported services
    
    Supported Services:
    - Deepgram (nova-2, base models)
    - Azure Speech (planned)
    - AssemblyAI (planned)
    """
    
    def __init__(self):
        """Initialize the STT service factory."""
        logger.debug("STTServiceFactory initialized")
    
    def create_stt_service(self, config: PipelineConfig) -> Any:
        """
        Create an STT service based on pipeline configuration.
        
        This method routes to the appropriate service factory based on
        the STT service type specified in the configuration.
        
        Args:
            config: Pipeline configuration containing STT settings
            
        Returns:
            Configured STT service instance (varies by provider)
            
        Raises:
            ValueError: If service not supported or API key missing
            NotImplementedError: If service planned but not yet implemented
            
        Example:
            >>> factory = STTServiceFactory()
            >>> config = PipelineConfig(stt_config=STTConfig(service=STTService.DEEPGRAM))
            >>> stt = factory.create_stt_service(config)
        """
        service_type = config.stt_config.service
        
        logger.info(f"Creating STT service: {service_type.value}")
        
        # Route to appropriate service factory
        if service_type == STTService.DEEPGRAM:
            return self._create_deepgram(config)
        
        elif service_type == STTService.AZURE_SPEECH:
            return self._create_azure_speech(config)
        
        elif service_type == STTService.ASSEMBLYAI:
            return self._create_assemblyai(config)
        
        else:
            raise ValueError(f"Unsupported STT service: {service_type}")
    
    def _create_deepgram(self, config: PipelineConfig) -> Any:
        """
        Create Deepgram STT service.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured DeepgramSTTService instance
        """
        return create_deepgram_stt(config, settings.deepgram_api_key)
    
    def _create_azure_speech(self, config: PipelineConfig) -> Any:
        """
        Create Azure Speech STT service.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured Azure STT service instance
            
        Raises:
            NotImplementedError: Azure Speech not yet implemented
        """
        raise NotImplementedError(
            "Azure Speech STT not yet implemented. "
            "Use Deepgram or contribute an implementation!"
        )
    
    def _create_assemblyai(self, config: PipelineConfig) -> Any:
        """
        Create AssemblyAI STT service.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured AssemblyAI STT service instance
            
        Raises:
            NotImplementedError: AssemblyAI not yet implemented
        """
        raise NotImplementedError(
            "AssemblyAI STT not yet implemented. "
            "Use Deepgram or contribute an implementation!"
        )


# Singleton instance
_stt_factory: Optional[STTServiceFactory] = None


def get_stt_service_factory() -> STTServiceFactory:
    """
    Get or create the STTServiceFactory singleton.
    
    Returns:
        Singleton instance of STTServiceFactory
    """
    global _stt_factory
    if _stt_factory is None:
        _stt_factory = STTServiceFactory()
    return _stt_factory
