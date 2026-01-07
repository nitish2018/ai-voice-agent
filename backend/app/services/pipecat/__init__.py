"""
Pipecat Service Module.

This module provides a modular architecture for managing Pipecat voice pipelines.

Structure:
- pipecat_service: Main service orchestrator (public API)
- session_manager: Manages session lifecycle and state
- daily_room_service: Handles Daily.co room creation
- transcript_capture: Captures conversation transcripts
- pipeline_orchestrator: Orchestrates pipeline creation and execution
- database_updater: Handles database operations
- text_processor: Processes text placeholders
"""

# Export main service for backward compatibility
from .pipecat_service import get_pipecat_service, PipecatService

__all__ = ['get_pipecat_service', 'PipecatService']
