"""
TTS (Text-to-Speech) Service Module.

Provides factory and service implementations for various TTS providers.

Structure:
- base.py: Base classes and utilities
- tts_factory.py: Main factory for creating TTS services
- elevenlabs_service.py: ElevenLabs TTS implementation
- cartesia_service.py: Cartesia TTS implementation
- azure_service.py: Azure TTS implementation (planned)

Usage:
    from app.services.pipecat.tts import get_tts_service_factory
    
    factory = get_tts_service_factory()
    tts_service = factory.create_tts_service(config)
"""

from .tts_factory import get_tts_service_factory, TTSServiceFactory

__all__ = ['get_tts_service_factory', 'TTSServiceFactory']
