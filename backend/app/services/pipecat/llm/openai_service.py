"""
OpenAI LLM Service Implementation.

Handles creation and configuration of OpenAI Large Language Model services
for the Pipecat pipeline.
"""
import logging
from typing import Any

from app.schemas.pipeline import PipelineConfig
from .base import validate_api_key

logger = logging.getLogger(__name__)

# Import Pipecat OpenAI service
try:
    from pipecat.services.openai import OpenAILLMService
    OPENAI_AVAILABLE = True
except ImportError as e:
    logger.error(f"OpenAI LLM service not available: {e}")
    OPENAI_AVAILABLE = False


class OpenAIServiceFactory:
    """
    Factory for creating OpenAI LLM service instances.
    
    Responsibilities:
    - Validate OpenAI API key
    - Extract OpenAI configuration from pipeline config
    - Create configured OpenAI LLM service instance
    - Log service creation details
    
    Supported Models:
    - gpt-4o: Latest GPT-4 Omni model
    - gpt-4o-mini: Smaller, faster GPT-4 Omni
    - gpt-4-turbo: GPT-4 Turbo model
    - gpt-3.5-turbo: GPT-3.5 Turbo model
    
    Configuration:
    - model: Model name (e.g., "gpt-4o")
    - temperature: Sampling temperature (0.0 to 2.0)
    - max_tokens: Maximum tokens to generate (optional)
    """
    
    @staticmethod
    def create(config: PipelineConfig, api_key: str) -> Any:
        """
        Create an OpenAI LLM service instance.
        
        Args:
            config: Pipeline configuration containing OpenAI settings
            api_key: OpenAI API key
            
        Returns:
            Configured OpenAILLMService instance
            
        Raises:
            ValueError: If API key is missing
            ImportError: If OpenAI service is not available
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI LLM service not available. "
                "Install pipecat with openai support."
            )
        
        # Validate API key
        validate_api_key(api_key, "OPENAI")
        
        # Extract OpenAI-specific configuration
        openai_config = config.llm_config.openai
        
        logger.info(
            f"Creating OpenAI LLM service - "
            f"model: {openai_config.model}, "
            f"temperature: {openai_config.temperature}"
        )
        
        # Create and return OpenAI LLM service
        return OpenAILLMService(
            api_key=api_key,
            model=openai_config.model,
        )


def create_openai_llm(config: PipelineConfig, api_key: str) -> Any:
    """
    Convenience function to create OpenAI LLM service.
    
    Args:
        config: Pipeline configuration
        api_key: OpenAI API key
        
    Returns:
        Configured OpenAILLMService instance
    """
    factory = OpenAIServiceFactory()
    return factory.create(config, api_key)
