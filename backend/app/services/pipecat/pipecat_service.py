"""
Pipecat Service - Main Orchestrator.

Coordinates voice call sessions using the Pipecat framework with Daily.co transport.
This service acts as the main entry point, delegating specific responsibilities
to specialized service modules.

Architecture:
- Uses DailyRoomService for room management
- Uses SessionManager for state management
- Uses TextProcessor for placeholder replacement
- Uses PipelineOrchestrator for pipeline execution
- Uses DatabaseUpdater for persistence
"""
import logging
import uuid
import asyncio
from typing import Optional, Dict, Any, List

from app.schemas.pipeline import (
    PipelineConfig,
    PipecatCallRequest,
    PipecatCallResponse,
    TransportType,
)
from app.schemas.session import DailyRoomConfig
from .session_manager import get_session_manager
from .daily_room_service import get_daily_room_service
from .text_processor import get_text_processor
from .pipeline_orchestrator import get_pipeline_orchestrator
from .call_completion_service import get_call_completion_service
from app.services.cost_calculator import get_cost_calculator

logger = logging.getLogger(__name__)

# Check if Pipecat is available
try:
    from pipecat.pipeline.pipeline import Pipeline
    PIPECAT_AVAILABLE = True
except ImportError as e:
    logger.error(f"Pipecat not available: {e}")
    PIPECAT_AVAILABLE = False


class PipecatService:
    """
    Main service for managing Pipecat voice pipelines.
    
    This service coordinates multiple specialized services to:
    - Start voice call sessions
    - Manage session lifecycle
    - Handle transport (Daily.co WebRTC or WebSocket)
    - Process transcripts and results
    
    Responsibilities:
    - Validate Pipecat availability
    - Coordinate service components
    - Provide high-level API for call management
    - Handle errors and edge cases
    """
    
    def __init__(self):
        """Initialize the Pipecat service and its dependencies."""
        if not PIPECAT_AVAILABLE:
            logger.warning("Pipecat framework not available")
            return
        
        # Initialize service dependencies
        self.session_manager = get_session_manager()
        self.daily_room_service = get_daily_room_service()
        self.text_processor = get_text_processor()
        self.pipeline_orchestrator = get_pipeline_orchestrator()
        self.call_completion_service = get_call_completion_service()
        self.cost_calculator = get_cost_calculator()
        
        logger.info("PipecatService initialized with modular architecture")
    
    async def start_call(
        self,
        request: PipecatCallRequest,
        agent_config: PipelineConfig,
        system_prompt: str
    ) -> PipecatCallResponse:
        """
        Start a new Pipecat call session.
        
        This method:
        1. Generates unique session ID
        2. Processes text placeholders in prompts
        3. Creates session state
        4. Sets up transport (Daily.co or WebSocket)
        5. Starts pipeline in background
        
        Args:
            request: Call request with driver context
            agent_config: Pipeline configuration
            system_prompt: System prompt template for LLM
            
        Returns:
            PipecatCallResponse with session details and access credentials
            
        Raises:
            Exception: If Pipecat is not available or transport setup fails
        """
        if not PIPECAT_AVAILABLE:
            raise Exception("Pipecat not available")
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        logger.info(f"[SERVICE] Starting Pipecat call session: {session_id}")
        
        # Replace placeholders in system prompt with actual values
        system_prompt_filled = self.text_processor.replace_placeholders(
            system_prompt,
            request
        )
        logger.info(f"[SERVICE] System prompt prepared (length: {len(system_prompt_filled)})")
        
        # Create session state
        session = self.session_manager.create_session(
            session_id=session_id,
            call_id=request.agent_id,  # Will be updated with actual call ID
            config=agent_config,
            system_prompt=system_prompt_filled
        )
        
        # Route to appropriate transport
        if agent_config.transport == TransportType.DAILY_WEBRTC:
            return await self._start_daily_call(session)
        elif agent_config.transport == TransportType.WEBSOCKET:
            return await self._start_websocket_call(session)
        else:
            raise Exception(f"Unsupported transport type: {agent_config.transport}")
    
    async def _start_daily_call(self, session) -> PipecatCallResponse:
        """
        Start a call using Daily.co WebRTC transport.
        
        Args:
            session: Session state object
            
        Returns:
            PipecatCallResponse with Daily.co room details
        """
        logger.info(f"[SERVICE] Setting up Daily.co transport for session {session.session_id}")
        
        # Create Daily.co room
        room_config = DailyRoomConfig(
            session_id=session.session_id,
            expiry_hours=1,
            max_participants=2,
            enable_chat=False,
            enable_emoji_reactions=False
        )
        
        daily_room = await self.daily_room_service.create_room(room_config)
        
        # Update session with room details
        session.daily_room_url = daily_room.room_url
        session.daily_token = daily_room.token
        
        # Start pipeline in background
        logger.info(f"[SERVICE] Starting pipeline for session {session.session_id}")
        asyncio.create_task(self.pipeline_orchestrator.run_daily_pipeline(session))
        
        # Give the bot a moment to start joining
        await asyncio.sleep(2)
        
        logger.info(f"[SERVICE] Session {session.session_id} initialized successfully")
        
        return PipecatCallResponse(
            session_id=session.session_id,
            daily_room_url=session.daily_room_url,
            daily_token=session.daily_token,
            status="initialized"
        )
    
    async def _start_websocket_call(self, session) -> PipecatCallResponse:
        """
        Start a call using WebSocket transport.
        
        Args:
            session: Session state object
            
        Returns:
            PipecatCallResponse with WebSocket details
        """
        logger.info(f"[SERVICE] Setting up WebSocket transport for session {session.session_id}")
        
        # Generate WebSocket URL
        # The client will connect to: ws://localhost:8000/api/pipecat/websocket/{session_id}
        # session.websocket_url = f"/api/pipecat/websocket/{session.session_id}"
        
        # logger.info(f"[SERVICE] Session {session.session_id} initialized for WebSocket")
        
        # return PipecatCallResponse(
        #     session_id=session.session_id,
        #     websocket_url=session.websocket_url,
        #     status="initialized"
        # )
        logger.info(
            f"[SERVICE] Starting Pipecat-managed WebSocket for session {session.session_id}"
        )

        asyncio.create_task(
            self.pipeline_orchestrator.run_pipecat_managed_ws_pipeline(session)
        )

        # Pipecat manages host/port internally
        return PipecatCallResponse(
            session_id=session.session_id,
            websocket_url="pipecat-managed",
            status="initialized"
        )
    
    async def end_call(self, session_id: str) -> Dict[str, Any]:
        """
        End an active Pipecat call session.
        
        This method:
        1. Retrieves session state
        2. Cancels pipeline if still running
        3. Calculates metrics
        4. Updates database
        5. Returns session metrics
        
        Args:
            session_id: Session ID to end
            
        Returns:
            Dictionary with session metrics and transcript
            
        Raises:
            Exception: If session not found or cleanup fails
        """
        logger.info(f"[SERVICE] Ending session: {session_id}")
        
        # Get session (checks both active and completed)
        session = self.session_manager.get_session(session_id)
        
        if not session:
            logger.warning(f"[SERVICE] Session {session_id} not found")
            return None
        
        # Check if already completed
        completed_session = self.session_manager.get_completed_session(session_id)
        if completed_session:
            logger.info(f"[SERVICE] Session {session_id} already completed")
            return await self._get_session_metrics(completed_session)
        
        # Cancel pipeline if still running
        await self._cancel_pipeline_task(session)
        
        # Calculate duration
        if not session.duration_seconds:
            session.calculate_duration()
            
            # Update database if not already done
            if not session.metrics_saved:
                await self.call_completion_service.complete_call(session_id, session)
                session.metrics_saved = True
            
        # Mark as completed
        self.session_manager.mark_completed(session_id)
            
            # Return metrics
        return await self._get_session_metrics(session)
    
    async def _cancel_pipeline_task(self, session) -> None:
        """
        Cancel a running pipeline task.
        
        Args:
            session: Session with pipeline task
        """
        if session.pipeline_background_task and not session.pipeline_background_task.done():
            logger.info(f"[SERVICE] Cancelling pipeline task for session {session.session_id}")
            session.pipeline_background_task.cancel()
            
            try:
                await session.pipeline_background_task
            except asyncio.CancelledError:
                logger.info(f"[SERVICE] Pipeline task cancelled")
            except Exception as e:
                logger.warning(f"[SERVICE] Error during pipeline cancellation: {e}")
    
    async def _get_session_metrics(self, session) -> Dict[str, Any]:
        """
        Build session metrics response.
        
        Args:
            session: Session state with metrics
            
        Returns:
            Dictionary with metrics and cost breakdown
        """
        # Calculate cost breakdown
        cost_breakdown = self.cost_calculator.calculate_call_cost(
            stt_service=session.config.stt_config.service.value,
            tts_service=session.config.tts_config.service.value,
            llm_service=session.config.llm_config.service.value,
            transport_type=session.config.transport.value,
            duration_seconds=session.duration_seconds or 0,
            total_chars=session.total_chars_spoken or 0,
            total_tokens=(session.total_input_tokens or 0) + (session.total_output_tokens or 0),
            stt_model=session.config.stt_config.model or "nova-2",
            tts_model=session.config.tts_config.model or "sonic-english",
            llm_model=session.config.llm_config.model,
            input_tokens=session.total_input_tokens or 0,
            output_tokens=session.total_output_tokens or 0,
        )
        
        return {
            "session_id": session.session_id,
            "transcript": session.transcript,
            "duration_seconds": session.duration_seconds,
            "cost_breakdown": cost_breakdown.model_dump(),
            "status": "completed"
        }
    
    def get_active_sessions(self) -> List[str]:
        """
        Get list of active session IDs.
        
        Returns:
            List of active session IDs
        """
        return self.session_manager.get_active_session_ids()
    
    def get_active_session_count(self) -> int:
        """
        Get count of active sessions.
        
        Returns:
            Number of active sessions
        """
        return self.session_manager.get_active_session_count()


# Singleton instance
_pipecat_service: Optional[PipecatService] = None


def get_pipecat_service() -> PipecatService:
    """
    Get or create the PipecatService singleton.
    
    Returns:
        Singleton instance of PipecatService
    """
    global _pipecat_service
    if _pipecat_service is None:
        _pipecat_service = PipecatService()
    return _pipecat_service
