"""
Transport Registry.

Maps TransportType → Transport Strategy.
"""

from app.schemas.pipeline import TransportType
from .webrtc.daily_transport import DailyPipecatTransport
from .websocket.websocket_transport import WebSocketPipecatTransport


class TransportRegistry:
    """
    Central registry for Pipecat transport strategies.
    """

    def __init__(
        self,
        daily_room_service,
        pipeline_orchestrator,
    ):
        self._registry = {
            TransportType.DAILY_WEBRTC: DailyPipecatTransport(
                daily_room_service,
                pipeline_orchestrator,
            ),
            TransportType.WEBSOCKET: WebSocketPipecatTransport(
                pipeline_orchestrator
            ),
        }

    def get(self, transport_type):
        if transport_type not in self._registry:
            raise ValueError(f"Unsupported transport: {transport_type}")
        return self._registry[transport_type]
