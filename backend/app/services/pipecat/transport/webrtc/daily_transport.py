"""
Daily WebRTC Transport Handler.
"""

import asyncio
import logging
from app.schemas.pipeline import PipecatCallResponse
from app.schemas.session import DailyRoomConfig
from ..base import PipecatTransport

logger = logging.getLogger(__name__)


class DailyPipecatTransport(PipecatTransport):
    """
    Handles Pipecat calls using Daily.co WebRTC transport.
    """

    def __init__(self, daily_room_service, pipeline_orchestrator):
        self.daily_room_service = daily_room_service
        self.pipeline_orchestrator = pipeline_orchestrator

    async def start(self, session) -> PipecatCallResponse:
        logger.info(
            f"[TRANSPORT:DAILY] Initializing Daily session {session.session_id}"
        )

        # Create Daily room
        room_config = DailyRoomConfig(
            session_id=session.session_id,
            expiry_hours=1,
            max_participants=2,
            enable_chat=False,
            enable_emoji_reactions=False,
        )

        daily_room = await self.daily_room_service.create_room(room_config)

        # Attach credentials to session
        session.daily_room_url = daily_room.room_url
        session.daily_token = daily_room.token

        # Start pipeline asynchronously
        asyncio.create_task(
            self.pipeline_orchestrator.run_pipeline(session)
        )

        # Small delay so bot joins cleanly
        await asyncio.sleep(2)

        logger.info(
            f"[TRANSPORT:DAILY] Session {session.session_id} ready"
        )

        return PipecatCallResponse(
            session_id=session.session_id,
            daily_room_url=session.daily_room_url,
            daily_token=session.daily_token,
            status="initialized",
        )
