"""
Transport Factory.

Creates transport implementations for Pipecat pipelines.
"""

import logging
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.transports.websocket.server import (
    WebsocketServerTransport,
    WebsocketServerParams,
)
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.audio.vad.silero import SileroVADAnalyzer
from app.services.pipecat.transport.base import PipecatTransport
from app.services.pipecat.session.session_manager import PipecatSessionState
from app.schemas.pipeline import TransportType

logger = logging.getLogger(__name__)


class TransportFactory:
    """
    Factory responsible for transport instantiation.
    """
    def create_transport(self, session: PipecatSessionState) -> PipecatTransport:
        """
        Create a transport based on the pipeline configuration.
        """
        if session.transport == TransportType.DAILY_WEBRTC:
            return self.create_daily(session)
        elif session.transport == TransportType.WEBSOCKET:
            return self.create_pipecat_managed_ws()
        else:
            raise ValueError(f"Unsupported transport: {session.transport}")

    def create_daily(self, session: PipecatSessionState) -> DailyTransport:
        """
        Create Daily WebRTC transport.
        """
        transport = DailyTransport(
            room_url=session.daily_room_url,
            token=session.daily_token,
            bot_name="Dispatcher Agent",
            params=DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_enabled=True,
                transcription_enabled=False,
            ),
        )

        logger.info("[PIPELINE] Daily transport created")
        return transport

    def create_pipecat_managed_ws(self) -> WebsocketServerTransport:
        """
        Create Pipecat-managed WebSocket transport.
        """
        transport = WebsocketServerTransport(
            params=WebsocketServerParams(
                serializer=ProtobufFrameSerializer(),
                audio_in_enabled=True,
                audio_out_enabled=True,
                add_wav_header=False,
                vad_analyzer=SileroVADAnalyzer(),
                session_timeout=180,
            )
        )

        logger.info("[PIPELINE] Pipecat-managed WS transport created")
        return transport
