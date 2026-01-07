"""
Anthropic LLM Service Implementation.

Handles creation and configuration of Anthropic Large Language Model services
for the Pipecat pipeline.
"""
import logging
from typing import Any

from app.schemas.pipeline import PipelineConfig
from .base import validate_api_key

logger = logging.getLogger(__name__)

# Import Pipecat Anthropic service
try:
    from pipecat.services.anthropic import AnthropicLLMService
    ANTHROPIC_AVAILABLE = True
except ImportError as e:
    logger.error(f"Anthropic LLM service not available: {e}")
    ANTHROPIC_AVAILABLE = False


class AnthropicServiceFactory:
    """
    Factory for creating Anthropic LLM service instances.
    
    Responsibilities:
    - Validate Anthropic API key
    - Extract Anthropic configuration from pipeline config
    - Create configured Anthropic LLM service instance
    - Log service creation details
    
    Supported Models:
    - claude-3-5-sonnet-20241022: Latest Claude 3.5 Sonnet
    - claude-3-5-haiku-20241022: Fast and efficient Claude 3.5 Haiku
    - claude-3-opus: Most powerful Claude 3 model
    - claude-3-sonnet: Balanced Claude 3 model
    - claude-3-haiku: Fast Claude 3 model
    
    Configuration:
    - model: Model name (e.g., "claude-3-5-sonnet-20241022")
    - temperature: Sampling temperature (0.0 to 1.0)
    - max_tokens: Maximum tokens to generate
    """
    
    @staticmethod
    def create(config: PipelineConfig, api_key: str) -> Any:
        """
        Create an Anthropic LLM service instance.
        
        Args:
            config: Pipeline configuration containing Anthropic settings
            api_key: Anthropic API key
            
        Returns:
            Configured AnthropicLLMService instance
            
        Raises:
            ValueError: If API key is missing
            ImportError: If Anthropic service is not available
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic LLM service not available. "
                "Install pipecat with anthropic support."
            )
        
        # Validate API key
        validate_api_key(api_key, "ANTHROPIC")
        
        # Extract Anthropic-specific configuration
        anthropic_config = config.llm_config.anthropic
        
        logger.info(
            f"Creating Anthropic LLM service - "
            f"model: {anthropic_config.model}, "
            f"temperature: {anthropic_config.temperature}"
        )
        
        # Create and return Anthropic LLM service
        return AnthropicLLMService(
            api_key=api_key,
            model=anthropic_config.model,
        )


def create_anthropic_llm(config: PipelineConfig, api_key: str) -> Any:
    """
    Convenience function to create Anthropic LLM service.
    
    Args:
        config: Pipeline configuration
        api_key: Anthropic API key
        
    Returns:
        Configured AnthropicLLMService instance
    """
    factory = AnthropicServiceFactory()
    return factory.create(config, api_key)
