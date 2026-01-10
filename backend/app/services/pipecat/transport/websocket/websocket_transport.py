"""
Pipecat-managed WebSocket Transport Handler.
"""

import asyncio
import logging
from app.schemas.pipeline import PipecatCallResponse
from ..base import PipecatTransport

logger = logging.getLogger(__name__)


class WebSocketPipecatTransport(PipecatTransport):
    """
    Handles Pipecat calls using server-managed WebSocket transport.
    """

    def __init__(self, pipeline_orchestrator):
        self.pipeline_orchestrator = pipeline_orchestrator

    async def start(self, session) -> PipecatCallResponse:
        logger.info(
            f"[TRANSPORT:WEBSOCKET] Initializing WS session {session.session_id}"
        )

        asyncio.create_task(
            self.pipeline_orchestrator.run_pipeline(session)
        )

        return PipecatCallResponse(
            session_id=session.session_id,
            websocket_url="pipecat-managed",
            status="initialized",
        )
