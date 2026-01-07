"""
WebSocket Transport for Pipecat.

Implements bidirectional audio streaming over WebSocket connections.
"""
import asyncio
import logging
from typing import Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)

try:
    from pipecat.transports.base_transport import BaseTransport, TransportParams
    from pipecat.frames.frames import AudioRawFrame, Frame
    from pipecat.processors.frame_processor import FrameDirection
    
    PIPECAT_AVAILABLE = True
except ImportError as e:
    logger.error(f"Pipecat not available: {e}")
    PIPECAT_AVAILABLE = False


class PipecatWebSocketTransport(BaseTransport):
    """
    WebSocket-based transport for Pipecat pipelines.
    
    Handles bidirectional audio streaming:
    - Receives audio from WebSocket client
    - Sends audio back to WebSocket client
    - Manages connection lifecycle
    """
    
    def __init__(self, websocket: WebSocket, params: TransportParams):
        """
        Initialize WebSocket transport.
        
        Args:
            websocket: FastAPI WebSocket connection
            params: Transport parameters
        """
        super().__init__(params=params)
        self.websocket = websocket
        self._running = False
        self._receive_task: Optional[asyncio.Task] = None
        logger.info("[WS_TRANSPORT] WebSocket transport initialized")
    
    async def start(self):
        """Start the WebSocket transport."""
        if self._running:
            logger.warning("[WS_TRANSPORT] Transport already running")
            return
        
        self._running = True
        logger.info("[WS_TRANSPORT] Starting WebSocket transport")
        
        # Accept the WebSocket connection if not already accepted
        try:
            await self.websocket.accept()
            logger.info("[WS_TRANSPORT] WebSocket connection accepted")
        except RuntimeError:
            # Already accepted
            logger.info("[WS_TRANSPORT] WebSocket already accepted")
        
        # Start receiving audio frames
        self._receive_task = asyncio.create_task(self._receive_loop())
    
    async def stop(self):
        """Stop the WebSocket transport."""
        if not self._running:
            return
        
        self._running = False
        logger.info("[WS_TRANSPORT] Stopping WebSocket transport")
        
        # Cancel receive task
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket connection
        try:
            await self.websocket.close()
            logger.info("[WS_TRANSPORT] WebSocket connection closed")
        except Exception as e:
            logger.error(f"[WS_TRANSPORT] Error closing WebSocket: {e}")
    
    async def _receive_loop(self):
        """
        Continuously receive audio data from WebSocket.
        
        Receives audio frames from the client and pushes them into the pipeline.
        """
        logger.info("[WS_TRANSPORT] Starting receive loop")
        
        try:
            while self._running:
                # Receive audio data from WebSocket
                data = await self.websocket.receive_bytes()
                
                if not data:
                    logger.warning("[WS_TRANSPORT] Received empty data")
                    continue
                
                # Create audio frame
                # Assuming 16kHz, 16-bit PCM, mono
                frame = AudioRawFrame(
                    audio=data,
                    sample_rate=16000,
                    num_channels=1
                )
                
                # Push frame into pipeline
                await self.push_frame(frame, FrameDirection.DOWNSTREAM)
                
        except asyncio.CancelledError:
            logger.info("[WS_TRANSPORT] Receive loop cancelled")
        except Exception as e:
            logger.error(f"[WS_TRANSPORT] Error in receive loop: {e}", exc_info=True)
        finally:
            logger.info("[WS_TRANSPORT] Receive loop ended")
    
    async def send_frame(self, frame: Frame, direction: FrameDirection):
        """
        Send a frame through the transport.
        
        Args:
            frame: Frame to send
            direction: Direction of the frame
        """
        # Only send audio frames to WebSocket
        if isinstance(frame, AudioRawFrame) and direction == FrameDirection.DOWNSTREAM:
            try:
                # Send audio data to WebSocket client
                await self.websocket.send_bytes(frame.audio)
            except Exception as e:
                logger.error(f"[WS_TRANSPORT] Error sending frame: {e}")
        
        # Pass other frames through
        await self.push_frame(frame, direction)
    
    def input(self):
        """
        Get input processor for the pipeline.
        
        Returns:
            Self, as this transport handles input
        """
        return self
    
    def output(self):
        """
        Get output processor for the pipeline.
        
        Returns:
            Self, as this transport handles output
        """
        return self
