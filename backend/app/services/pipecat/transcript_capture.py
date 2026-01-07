"""
Transcript Capture Processor.

Captures and stores conversation transcripts from voice calls
by intercepting frames in the Pipecat pipeline.
"""
import logging
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .session_manager import PipecatSessionState

logger = logging.getLogger(__name__)

# Import Pipecat components
try:
    from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
    from pipecat.frames.frames import Frame, TranscriptionFrame, TextFrame
    
    PIPECAT_AVAILABLE = True
except ImportError as e:
    logger.error(f"Pipecat not available: {e}")
    PIPECAT_AVAILABLE = False
    FrameProcessor = object  # Fallback for type checking


class TranscriptCaptureProcessor(FrameProcessor):
    """
    Frame processor that captures conversation transcripts.
    
    This processor intercepts frames in the pipeline to extract:
    - User speech (from TranscriptionFrame - STT output)
    - Bot responses (from TextFrame - LLM to TTS)
    
    Responsibilities:
    - Listen to pipeline frames
    - Extract text content from relevant frame types
    - Store messages in session transcript
    - Pass frames through unchanged
    """
    
    def __init__(self, session: 'PipecatSessionState'):
        """
        Initialize the transcript capture processor.
        
        Args:
            session: Session state object to store captured transcripts
        """
        if not PIPECAT_AVAILABLE:
            raise ImportError("Pipecat framework not available")
        
        super().__init__()
        self.session = session
        logger.info(f"[TRANSCRIPT] Initialized TranscriptCaptureProcessor for session {session.session_id}")
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """
        Process frames to capture transcript content.
        
        This method intercepts frames flowing through the pipeline:
        - TranscriptionFrame: Contains user speech from STT
        - TextFrame: Contains bot responses from LLM
        
        Args:
            frame: The frame to process
            direction: Direction of frame flow in pipeline
        """
        await super().process_frame(frame, direction)
        
        # Capture user speech from Speech-to-Text (STT)
        if isinstance(frame, TranscriptionFrame):
            await self._capture_user_speech(frame)
        
        # Capture bot responses from LLM
        elif isinstance(frame, TextFrame):
            await self._capture_bot_response(frame)
        
        # Always pass the frame through to next processor
        await self.push_frame(frame, direction)
    
    async def _capture_user_speech(self, frame: TranscriptionFrame):
        """
        Capture and store user speech from transcription frame.
        
        Args:
            frame: TranscriptionFrame containing user speech
        """
        text = frame.text
        
        # Only capture non-empty text
        if text and text.strip():
            logger.info(f"[TRANSCRIPT] Captured user speech: {text[:100]}")
            
            message = {
                "role": "user",
                "content": text.strip(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.session.add_transcript_message(message)
    
    async def _capture_bot_response(self, frame: TextFrame):
        """
        Capture and store bot responses from text frame.
        
        Args:
            frame: TextFrame containing bot response
        """
        text = frame.text
        
        # Only capture non-empty text
        if text and text.strip():
            logger.info(f"[TRANSCRIPT] Captured bot response: {text[:100]}")
            
            message = {
                "role": "assistant",
                "content": text.strip(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.session.add_transcript_message(message)


def create_transcript_processor(session: 'PipecatSessionState') -> TranscriptCaptureProcessor:
    """
    Factory function to create a transcript capture processor.
    
    Args:
        session: Session state object
        
    Returns:
        Configured TranscriptCaptureProcessor instance
        
    Raises:
        ImportError: If Pipecat is not available
    """
    if not PIPECAT_AVAILABLE:
        raise ImportError("Pipecat framework not available")
    
    return TranscriptCaptureProcessor(session)
