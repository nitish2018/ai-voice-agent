"""
STT (Speech-to-Text) Service Module.

Provides factory and service implementations for various STT providers.

Structure:
- base.py: Base classes and utilities
- stt_factory.py: Main factory for creating STT services
- deepgram_service.py: Deepgram STT implementation
- azure_service.py: Azure Speech implementation (planned)
- assemblyai_service.py: AssemblyAI implementation (planned)

Usage:
    from app.services.pipecat.stt import get_stt_service_factory
    
    factory = get_stt_service_factory()
    stt_service = factory.create_stt_service(config)
"""

from .stt_factory import get_stt_service_factory, STTServiceFactory

__all__ = ['get_stt_service_factory', 'STTServiceFactory']
