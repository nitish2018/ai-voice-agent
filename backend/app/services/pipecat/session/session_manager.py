"""
Session State Manager.

Manages the lifecycle and state of Pipecat call sessions,
including active and completed sessions.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field

from app.schemas.pipeline import PipelineConfig
from app.schemas.session import PipecatSessionData, SessionTransport, SessionMetrics
from app.schemas.pipeline import TransportType

logger = logging.getLogger(__name__)


@dataclass
class PipecatSessionState:
    """
    In-memory state for an active Pipecat session.
    
    This class maintains runtime state that cannot be easily
    serialized to Pydantic models (e.g., pipeline objects, tasks).
    
    Responsibilities:
    - Store runtime objects (transport, pipeline, task, runner)
    - Maintain transcript in real-time
    - Track session lifecycle state
    """
    # Core identifiers
    session_id: str
    call_id: str
    
    # Configuration
    config: PipelineConfig
    system_prompt: str
    
    # Transport details
    daily_room_url: Optional[str] = None
    daily_token: Optional[str] = None
    websocket_url: Optional[str] = None
    
    # Runtime objects (not serializable)
    transport: Optional[Any] = None
    pipeline: Optional[Any] = None
    task: Optional[Any] = None
    runner: Optional[Any] = None
    llm_context: Optional[Any] = None
    pipeline_background_task: Optional[asyncio.Task] = None
    
    # Conversation data
    transcript: List[Dict[str, str]] = field(default_factory=list)
    
    # Metrics
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    total_input_tokens: Optional[int] = None
    total_output_tokens: Optional[int] = None
    total_chars_spoken: Optional[int] = None
    
    # State flags
    metrics_saved: bool = False
    
    def add_transcript_message(self, message: Dict[str, str]):
        """
        Add a message to the transcript.
        
        Args:
            message: Dictionary with 'role' and 'content' keys
        """
        self.transcript.append(message)
        logger.debug(f"[SESSION {self.session_id}] Added {message['role']} message to transcript")
    
    def calculate_duration(self):
        """Calculate and set session duration."""
        if not self.end_time:
            self.end_time = datetime.utcnow()
        
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
    
    def to_data_model(self) -> PipecatSessionData:
        """
        Convert to Pydantic data model for serialization.
        
        Returns:
            PipecatSessionData with serializable fields
        """
        return PipecatSessionData(
            session_id=self.session_id,
            call_id=self.call_id,
            config=self.config,
            system_prompt=self.system_prompt,
            transport=SessionTransport(
                daily_room_url=self.daily_room_url,
                daily_token=self.daily_token,
                websocket_url=self.websocket_url
            ),
            transcript=[
                {"role": msg["role"], "content": msg["content"]}
                for msg in self.transcript
            ],
            metrics=SessionMetrics(
                duration_seconds=self.duration_seconds,
                total_input_tokens=self.total_input_tokens,
                total_output_tokens=self.total_output_tokens,
                total_chars_spoken=self.total_chars_spoken,
                start_time=self.start_time,
                end_time=self.end_time
            ),
            metrics_saved=self.metrics_saved
        )


class SessionManager:
    """
    Manages Pipecat call session lifecycle.
    
    Responsibilities:
    - Create and store new sessions
    - Track active sessions
    - Move completed sessions to history
    - Provide session lookup
    - Clean up old completed sessions
    """
    
    def __init__(self):
        """Initialize the session manager."""
        self.active_sessions: Dict[str, PipecatSessionState] = {}
        self.completed_sessions: Dict[str, PipecatSessionState] = {}
        logger.info("SessionManager initialized")
    
    def create_session(
        self,
        session_id: str,
        call_id: str,
        config: PipelineConfig,
        system_prompt: str,
        transport: TransportType
    ) -> PipecatSessionState:
        """
        Create a new session.
        
        Args:
            session_id: Unique session identifier
            call_id: Associated call record ID
            config: Pipeline configuration
            system_prompt: System prompt for LLM
            
        Returns:
            New PipecatSessionState instance
        """
        session = PipecatSessionState(
            session_id=session_id,
            call_id=call_id,
            config=config,
            system_prompt=system_prompt,
            transport=transport,
        )
        
        self.active_sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")
        
        return session
    
    def get_session(self, session_id: str) -> Optional[PipecatSessionState]:
        """
        Get a session by ID (checks both active and completed).
        
        Args:
            session_id: Session identifier
            
        Returns:
            PipecatSessionState if found, None otherwise
        """
        # Check active sessions first
        session = self.active_sessions.get(session_id)
        if session:
            return session
        
        # Check completed sessions
        return self.completed_sessions.get(session_id)
    
    def get_active_session(self, session_id: str) -> Optional[PipecatSessionState]:
        """
        Get an active session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            PipecatSessionState if active, None otherwise
        """
        return self.active_sessions.get(session_id)
    
    def get_completed_session(self, session_id: str) -> Optional[PipecatSessionState]:
        """
        Get a completed session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            PipecatSessionState if completed, None otherwise
        """
        return self.completed_sessions.get(session_id)
    
    def mark_completed(self, session_id: str):
        """
        Mark a session as completed and move it to completed sessions.
        
        Args:
            session_id: Session identifier
        """
        session = self.active_sessions.get(session_id)
        if not session:
            logger.warning(f"Cannot mark session {session_id} as completed - not found in active sessions")
            return
        
        # Calculate duration if not already done
        if not session.duration_seconds:
            session.calculate_duration()
        
        # Move to completed
        self.completed_sessions[session_id] = self.active_sessions.pop(session_id)
        logger.info(f"Session {session_id} marked as completed")
    
    def get_active_session_ids(self) -> List[str]:
        """
        Get list of all active session IDs.
        
        Returns:
            List of active session IDs
        """
        return list(self.active_sessions.keys())
    
    def get_active_session_count(self) -> int:
        """
        Get count of active sessions.
        
        Returns:
            Number of active sessions
        """
        return len(self.active_sessions)
    
    def cleanup_old_completed_sessions(self, max_age_hours: int = 24):
        """
        Remove old completed sessions to free memory.
        
        Args:
            max_age_hours: Maximum age in hours for completed sessions to keep
        """
        cutoff_time = datetime.utcnow()
        removed_count = 0
        
        for session_id in list(self.completed_sessions.keys()):
            session = self.completed_sessions[session_id]
            if session.end_time:
                age_hours = (cutoff_time - session.end_time).total_seconds() / 3600
                if age_hours > max_age_hours:
                    del self.completed_sessions[session_id]
                    removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old completed sessions")


# Singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Get or create the SessionManager singleton.
    
    Returns:
        Singleton instance of SessionManager
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
