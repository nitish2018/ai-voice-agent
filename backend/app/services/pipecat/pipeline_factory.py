"""
Pipeline Factory - Creates Pipecat service instances based on configuration.

This factory handles the instantiation of STT, TTS, and LLM services
from various providers based on the pipeline configuration.

Note: All services (STT, TTS, LLM) are now managed by dedicated factories
in their respective modules (stt/, tts/, llm/).
"""
import logging
from typing import Any

from app.schemas.pipeline import PipelineConfig
from .stt import get_stt_service_factory
from .tts import get_tts_service_factory
from .llm import get_llm_service_factory

logger = logging.getLogger(__name__)

# Check if Pipecat is available
try:
    import pipecat
    PIPECAT_AVAILABLE = True
except ImportError as e:
    logger.error(f"Pipecat not available: {e}")
    PIPECAT_AVAILABLE = False


class PipelineFactory:
    """
    Factory for creating Pipecat pipeline components.
    
    This factory delegates all service creation (STT, TTS, LLM) to
    specialized factories in their respective modules.
    """
    
    def __init__(self):
        """Initialize the pipeline factory."""
        if not PIPECAT_AVAILABLE:
            logger.warning("Pipecat not available")
        
        # Get specialized factories
        self.stt_factory = get_stt_service_factory()
        self.tts_factory = get_tts_service_factory()
        self.llm_factory = get_llm_service_factory()
    
    def create_stt_service(self, config: PipelineConfig) -> Any:
        """
        Create a Speech-to-Text service based on configuration.
        
        Delegates to the STTServiceFactory for service creation.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured STT service instance
            
        Raises:
            ValueError: If service not supported or API key missing
        """
        return self.stt_factory.create_stt_service(config)
    
    def create_tts_service(self, config: PipelineConfig) -> Any:
        """
        Create a Text-to-Speech service based on configuration.
        
        Delegates to the TTSServiceFactory for service creation.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured TTS service instance
            
        Raises:
            ValueError: If service not supported or API key missing
        """
        return self.tts_factory.create_tts_service(config)
    
    def create_llm_service(self, config: PipelineConfig) -> Any:
        """
        Create a Large Language Model service based on configuration.
        
        Delegates to the LLMServiceFactory for service creation.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured LLM service instance
            
        Raises:
            ValueError: If service not supported or API key missing
        """
        return self.llm_factory.create_llm_service(config)


# Singleton instance
_pipeline_factory: PipelineFactory = None


def get_pipeline_factory() -> PipelineFactory:
    """Get or create the PipelineFactory singleton."""
    global _pipeline_factory
    if _pipeline_factory is None:
        _pipeline_factory = PipelineFactory()
    return _pipeline_factory
