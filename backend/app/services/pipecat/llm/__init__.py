"""
LLM (Large Language Model) Service Module.

Provides factory and service implementations for various LLM providers.

Structure:
- base.py: Base classes and utilities
- llm_factory.py: Main factory for creating LLM services
- openai_service.py: OpenAI LLM implementation (GPT-4o, GPT-4 Turbo)
- anthropic_service.py: Anthropic LLM implementation (Claude 3.5)

Usage:
    from app.services.pipecat.llm import get_llm_service_factory
    
    factory = get_llm_service_factory()
    llm_service = factory.create_llm_service(config)
"""

from .llm_factory import get_llm_service_factory, LLMServiceFactory

__all__ = ['get_llm_service_factory', 'LLMServiceFactory']
