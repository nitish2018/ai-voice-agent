"""
STT Service Base Module.

Defines base classes and utilities for Speech-to-Text service implementations.
"""
import logging
from typing import Protocol, Any
from app.schemas.pipeline import PipelineConfig

logger = logging.getLogger(__name__)


class STTServiceFactory(Protocol):
    """Protocol for STT service factories."""
    
    def create(self, config: PipelineConfig, api_key: str) -> Any:
        """
        Create an STT service instance.
        
        Args:
            config: Pipeline configuration
            api_key: API key for the service
            
        Returns:
            Configured STT service instance
        """
        ...


def validate_api_key(api_key: str, service_name: str) -> None:
    """
    Validate that an API key is present.
    
    Args:
        api_key: API key to validate
        service_name: Name of the service for error message
        
    Raises:
        ValueError: If API key is missing or empty
    """
    if not api_key:
        raise ValueError(f"{service_name}_API_KEY not configured")
    
    logger.debug(f"API key validated for {service_name}")
