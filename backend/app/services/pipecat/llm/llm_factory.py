"""
LLM Service Factory.

Main factory for creating Large Language Model service instances
based on pipeline configuration.
"""
import logging
from typing import Any, Optional

from app.schemas.pipeline import PipelineConfig, LLMService
from app.core.config import settings
from .openai_service import create_openai_llm
from .anthropic_service import create_anthropic_llm

logger = logging.getLogger(__name__)


class LLMServiceFactory:
    """
    Factory for creating LLM service instances.
    
    This factory supports multiple LLM providers and handles:
    - Service selection based on configuration
    - API key validation
    - Service-specific configuration
    - Error handling for unsupported services
    
    Supported Services:
    - OpenAI (GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo)
    - Anthropic (Claude 3.5 Sonnet, Claude 3.5 Haiku)
    """
    
    def __init__(self):
        """Initialize the LLM service factory."""
        logger.debug("LLMServiceFactory initialized")
    
    def create_llm_service(self, config: PipelineConfig) -> Any:
        """
        Create an LLM service based on pipeline configuration.
        
        This method routes to the appropriate service factory based on
        the LLM service type specified in the configuration.
        
        Args:
            config: Pipeline configuration containing LLM settings
            
        Returns:
            Configured LLM service instance (varies by provider)
            
        Raises:
            ValueError: If service not supported or API key missing
            
        Example:
            >>> factory = LLMServiceFactory()
            >>> config = PipelineConfig(llm_config=LLMConfig(service=LLMService.OPENAI))
            >>> llm = factory.create_llm_service(config)
        """
        service_type = config.llm_config.service
        
        logger.info(f"Creating LLM service: {service_type.value}")
        
        # Route to appropriate service factory
        if service_type == LLMService.OPENAI:
            return self._create_openai(config)
        
        elif service_type == LLMService.ANTHROPIC:
            return self._create_anthropic(config)
        
        else:
            raise ValueError(f"Unsupported LLM service: {service_type}")
    
    def _create_openai(self, config: PipelineConfig) -> Any:
        """
        Create OpenAI LLM service.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured OpenAILLMService instance
        """
        return create_openai_llm(config, settings.openai_api_key)
    
    def _create_anthropic(self, config: PipelineConfig) -> Any:
        """
        Create Anthropic LLM service.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured AnthropicLLMService instance
        """
        return create_anthropic_llm(config, settings.anthropic_api_key)


# Singleton instance
_llm_factory: Optional[LLMServiceFactory] = None


def get_llm_service_factory() -> LLMServiceFactory:
    """
    Get or create the LLMServiceFactory singleton.
    
    Returns:
        Singleton instance of LLMServiceFactory
    """
    global _llm_factory
    if _llm_factory is None:
        _llm_factory = LLMServiceFactory()
    return _llm_factory
