"""
Pipecat Service – Main Orchestrator.

Coordinates Pipecat call sessions while delegating all
transport-specific behavior to transport strategies.
"""

import logging
import uuid
from typing import Optional, Dict, Any

from app.schemas.pipeline import (
    PipelineConfig,
    PipecatCallRequest,
    TransportType,
)
from app.services.pipecat.session.session_manager import get_session_manager
from app.services.pipecat.transport.webrtc.daily_room_service import get_daily_room_service
from app.services.pipecat.utils.text_processor import get_text_processor
from .pipeline.pipeline_orchestrator import get_pipeline_orchestrator
from app.services.pipecat.call.call_completion_service import get_call_completion_service
from app.services.cost import get_cost_calculator
from app.services.pipecat.transport.registry import TransportRegistry
from app.services.pipecat.pipeline.pipeline_utils import PipecatSessionUtils

logger = logging.getLogger(__name__)


class PipecatService:
    """
    High-level Pipecat call coordinator.

    Responsibilities:
    - Session creation
    - Prompt preparation
    - Transport delegation
    - Lifecycle coordination
    """

    def __init__(self):
        self.session_manager = get_session_manager()
        self.text_processor = get_text_processor()
        self.pipeline_orchestrator = get_pipeline_orchestrator()
        self.call_completion_service = get_call_completion_service()
        self.cost_calculator = get_cost_calculator()

        self.transport_registry = TransportRegistry(
            daily_room_service=get_daily_room_service(),
            pipeline_orchestrator=self.pipeline_orchestrator,
        )

        logger.info("PipecatService initialized")

    async def start_call(
        self,
        request: PipecatCallRequest,
        agent_config: PipelineConfig,
        system_prompt: str,
        transport: TransportType,
    ):
        """
        Start a Pipecat call using selected transport.
        """

        session_id = str(uuid.uuid4())
        logger.info(f"[SERVICE] Starting Pipecat session {session_id}")

        # Fill prompt placeholders
        system_prompt_filled = self.text_processor.replace_placeholders(
            system_prompt,
            request,
        )

        # Create session
        session = self.session_manager.create_session(
            session_id=session_id,
            call_id=request.agent_id,
            config=agent_config,
            system_prompt=system_prompt_filled,
            transport=transport,
        )

        # Delegate to transport strategy
        transport_handler = self.transport_registry.get(transport)
        return await transport_handler.start(session)

    async def end_call(self, session_id: str) -> Dict[str, Any]:
        """
        End an active Pipecat session.

        This is part of the public service API and is used by API routes.
        """
        logger.info(f"[SERVICE] Ending Pipecat session {session_id}")

        # Get session (active or completed)
        session = self.session_manager.get_session(session_id)

        if not session:
            logger.warning(f"[SERVICE] Session {session_id} not found")
            return None

        # If already completed, just return metrics
        completed = self.session_manager.get_completed_session(session_id)
        if completed:
            return await PipecatSessionUtils.build_session_result(completed)

        # Cancel running pipeline if any
        await PipecatSessionUtils.cancel_pipeline_if_running(session)

        # Finalize metrics + DB update
        if not session.duration_seconds:
            session.calculate_duration()

        if not session.metrics_saved:
            await self.call_completion_service.complete_call(session_id, session)
            session.metrics_saved = True

        # Mark session completed
        self.session_manager.mark_completed(session_id)

        return await PipecatSessionUtils.build_session_result(session)
    
# =========================
# Singleton factory (MODULE LEVEL)
# =========================

_pipecat_service: Optional[PipecatService] = None


def get_pipecat_service() -> PipecatService:
    """
    Get or create the PipecatService singleton.
    """
    global _pipecat_service
    if _pipecat_service is None:
        _pipecat_service = PipecatService()
    return _pipecat_service

