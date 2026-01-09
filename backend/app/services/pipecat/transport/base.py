"""
Base Transport Strategy.

Defines the interface that all Pipecat transports must implement.
"""

from abc import ABC, abstractmethod
from typing import Any
from app.schemas.pipeline import PipecatCallResponse


class PipecatTransport(ABC):
    """
    Abstract transport strategy.

    Each transport (Daily, WebSocket, etc.) must:
    - Prepare session-specific resources
    - Start the pipeline
    - Return access details
    """

    @abstractmethod
    async def start(self, session) -> PipecatCallResponse:
        """
        Start a Pipecat call using this transport.

        Args:
            session: Pipecat session state

        Returns:
            PipecatCallResponse
        """
        raise NotImplementedError
