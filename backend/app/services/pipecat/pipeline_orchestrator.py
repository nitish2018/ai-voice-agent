"""
Pipeline Orchestrator.

Orchestrates the creation and execution of Pipecat voice pipelines,
managing the lifecycle from initialization to cleanup.
"""
import logging
import asyncio
from typing import Optional

from .session_manager import PipecatSessionState
from .transcript_capture import create_transcript_processor
from .database_updater import get_database_updater
from .pipeline_factory import get_pipeline_factory

logger = logging.getLogger(__name__)

# Import Pipecat components
try:
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
    from pipecat.transports.services.daily import DailyParams, DailyTransport
    from pipecat.transports.base_transport import BaseTransport, TransportParams
    
    PIPECAT_AVAILABLE = True
except ImportError as e:
    logger.error(f"Pipecat not available: {e}")
    PIPECAT_AVAILABLE = False


class PipelineOrchestrator:
    """
    Orchestrates Pipecat pipeline lifecycle.
    
    Responsibilities:
    - Create and configure pipeline components (STT, TTS, LLM)
    - Set up transport (Daily.co WebRTC or WebSocket)
    - Build complete pipeline with transcript capture
    - Run pipeline with proper error handling
    - Handle cleanup and finalization
    - Update database on completion
    """
    
    def __init__(self):
        """Initialize the pipeline orchestrator."""
        if not PIPECAT_AVAILABLE:
            logger.warning("Pipecat framework not available")
            return
        
        self.factory = get_pipeline_factory()
        self.db_updater = get_database_updater()
        logger.info("PipelineOrchestrator initialized")
    
    async def run_daily_pipeline(self, session: PipecatSessionState) -> None:
        """
        Run a complete Daily.co pipeline for a session.
        
        This method:
        1. Creates all pipeline components (STT, TTS, LLM, transport)
        2. Assembles the pipeline with transcript capture
        3. Runs the pipeline
        4. Handles errors and cleanup
        5. Updates database on completion
        
        Args:
            session: Session state with configuration and context
        """
        if not PIPECAT_AVAILABLE:
            raise Exception("Pipecat not available")
        
        logger.info(f"[PIPELINE] Starting Daily pipeline for session: {session.session_id}")
        logger.info(f"[PIPELINE] Room URL: {session.daily_room_url}")
        
        try:
            # Create pipeline components
            pipeline = await self._create_pipeline(session)
            session.pipeline = pipeline
            
            # Create and configure task
            task = self._create_pipeline_task(pipeline, session)
            session.task = task
            
            # Run pipeline
            await self._run_pipeline_task(task, session)
            
            logger.info(f"[PIPELINE] Pipeline completed for session: {session.session_id}")
            
        except Exception as e:
            logger.error(f"[PIPELINE] Pipeline error for session {session.session_id}: {e}", exc_info=True)
            raise
        
        finally:
            # Always perform cleanup and database update
            await self._finalize_session(session)
    
    async def run_websocket_pipeline(self, session: PipecatSessionState, websocket) -> None:
        """
        Run a complete WebSocket pipeline for a session.
        
        This method:
        1. Creates all pipeline components (STT, TTS, LLM, WebSocket transport)
        2. Assembles the pipeline with transcript capture
        3. Runs the pipeline
        4. Handles errors and cleanup
        5. Updates database on completion
        
        Args:
            session: Session state with configuration and context
            websocket: WebSocket connection object
        """
        if not PIPECAT_AVAILABLE:
            raise Exception("Pipecat not available")
        
        logger.info(f"[PIPELINE] Starting WebSocket pipeline for session: {session.session_id}")
        
        try:
            # Create pipeline components
            pipeline = await self._create_websocket_pipeline(session, websocket)
            session.pipeline = pipeline
            
            # Create and configure task
            task = self._create_pipeline_task(pipeline, session)
            session.task = task
            
            # Run pipeline
            await self._run_pipeline_task(task, session)
            
            logger.info(f"[PIPELINE] WebSocket pipeline completed for session: {session.session_id}")
            
        except Exception as e:
            logger.error(f"[PIPELINE] WebSocket pipeline error for session {session.session_id}: {e}", exc_info=True)
            raise
        
        finally:
            # Always perform cleanup and database update
            await self._finalize_session(session)
    
    async def _create_pipeline(self, session: PipecatSessionState) -> Pipeline:
        """
        Create and assemble the complete pipeline.
        
        Args:
            session: Session state with configuration
            
        Returns:
            Configured Pipeline instance
        """
        logger.info("[PIPELINE] Creating pipeline components...")
        
        # Create services using factory
        logger.info("[PIPELINE] Creating STT service...")
        stt = self.factory.create_stt_service(session.config)
        
        logger.info("[PIPELINE] Creating TTS service...")
        tts = self.factory.create_tts_service(session.config)
        
        logger.info("[PIPELINE] Creating LLM service...")
        llm = self.factory.create_llm_service(session.config)
        
        # Create Daily transport
        logger.info("[PIPELINE] Creating Daily transport...")
        transport = self._create_daily_transport(session)
        session.transport = transport
        
        # Create LLM context with system prompt
        context = self._create_llm_context(session)
        context_aggregator = llm.create_context_aggregator(context)
        session.llm_context = context
        
        # Create transcript capture processors
        user_transcript_capture = create_transcript_processor(session)
        bot_transcript_capture = create_transcript_processor(session)
        
        # Assemble pipeline
        logger.info("[PIPELINE] Assembling pipeline...")
        pipeline = Pipeline([
            transport.input(),              # Audio input from user
            stt,                            # Speech-to-text
            user_transcript_capture,        # Capture user transcription
            context_aggregator.user(),      # Add user message to context
            llm,                            # Generate response
            bot_transcript_capture,         # Capture bot response
            tts,                            # Text-to-speech
            transport.output(),             # Audio output to user
            context_aggregator.assistant(), # Add assistant message to context
        ])
        
        logger.info("[PIPELINE] Pipeline created successfully")
        return pipeline
    
    async def _create_websocket_pipeline(self, session: PipecatSessionState, websocket) -> Pipeline:
        """
        Create and assemble the complete WebSocket pipeline.
        
        Args:
            session: Session state with configuration
            websocket: WebSocket connection object
            
        Returns:
            Configured Pipeline instance
        """
        logger.info("[PIPELINE] Creating WebSocket pipeline components...")
        
        # Create services using factory
        logger.info("[PIPELINE] Creating STT service...")
        stt = self.factory.create_stt_service(session.config)
        
        logger.info("[PIPELINE] Creating TTS service...")
        tts = self.factory.create_tts_service(session.config)
        
        logger.info("[PIPELINE] Creating LLM service...")
        llm = self.factory.create_llm_service(session.config)
        
        # Create WebSocket transport
        logger.info("[PIPELINE] Creating WebSocket transport...")
        transport = await self._create_websocket_transport(session, websocket)
        session.transport = transport
        
        # Create LLM context with system prompt
        context = self._create_llm_context(session)
        context_aggregator = llm.create_context_aggregator(context)
        session.llm_context = context
        
        # Create transcript capture processors
        user_transcript_capture = create_transcript_processor(session)
        bot_transcript_capture = create_transcript_processor(session)
        
        # Assemble pipeline
        logger.info("[PIPELINE] Assembling WebSocket pipeline...")
        pipeline = Pipeline([
            transport.input(),              # Audio input from user via WebSocket
            stt,                            # Speech-to-text
            user_transcript_capture,        # Capture user transcription
            context_aggregator.user(),      # Add user message to context
            llm,                            # Generate response
            bot_transcript_capture,         # Capture bot response
            tts,                            # Text-to-speech
            transport.output(),             # Audio output to user via WebSocket
            context_aggregator.assistant(), # Add assistant message to context
        ])
        
        logger.info("[PIPELINE] WebSocket pipeline created successfully")
        return pipeline
    
    def _create_daily_transport(self, session: PipecatSessionState) -> DailyTransport:
        """
        Create Daily.co transport for WebRTC communication.
        
        Args:
            session: Session state with Daily.co credentials
            
        Returns:
            Configured DailyTransport instance
        """
        transport = DailyTransport(
            room_url=session.daily_room_url,
            token=session.daily_token,
            bot_name="Dispatcher Agent",
            params=DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_enabled=True,
                vad_analyzer=None,  # Use Daily's built-in VAD
                transcription_enabled=False,
            )
        )
        
        logger.info("[PIPELINE] Daily transport created successfully")
        return transport
    
    async def _create_websocket_transport(self, session: PipecatSessionState, websocket) -> BaseTransport:
        """
        Create WebSocket transport for bidirectional audio communication.
        
        Args:
            session: Session state
            websocket: FastAPI WebSocket connection
            
        Returns:
            Configured BaseTransport instance for WebSocket
        """
        from .websocket_transport import PipecatWebSocketTransport
        
        transport = PipecatWebSocketTransport(
            websocket=websocket,
            params=TransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_enabled=session.config.vad_enabled if hasattr(session.config, 'vad_enabled') else True,
            )
        )
        
        logger.info("[PIPELINE] WebSocket transport created successfully")
        return transport
    
    def _create_llm_context(self, session: PipecatSessionState) -> OpenAILLMContext:
        """
        Create LLM context with system prompt.
        
        Args:
            session: Session state with system prompt
            
        Returns:
            Configured OpenAILLMContext instance
        """
        messages = [
            {
                "role": "system",
                "content": session.system_prompt
            }
        ]
        
        context = OpenAILLMContext(messages=messages)
        logger.info("[PIPELINE] LLM context created with system prompt")
        
        return context
    
    def _create_pipeline_task(
        self,
        pipeline: Pipeline,
        session: PipecatSessionState
    ) -> PipelineTask:
        """
        Create pipeline task with appropriate parameters.
        
        Args:
            pipeline: Assembled pipeline
            session: Session state with configuration
            
        Returns:
            Configured PipelineTask instance
        """
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=session.config.enable_interruptions,
                enable_metrics=True,
            )
        )
        
        logger.info("[PIPELINE] Pipeline task created")
        return task
    
    async def _run_pipeline_task(
        self,
        task: PipelineTask,
        session: PipecatSessionState
    ) -> None:
        """
        Run the pipeline task with proper error handling.
        
        Args:
            task: Pipeline task to run
            session: Session state
        """
        logger.info(f"[PIPELINE] Starting pipeline runner for session {session.session_id}...")
        
        # Create runner
        runner = PipelineRunner()
        session.runner = runner
        
        # Start the pipeline in the background
        pipeline_task_obj = asyncio.create_task(runner.run(task))
        session.pipeline_background_task = pipeline_task_obj
        
        # Add done callback for error logging
        def pipeline_done_callback(task_future):
            try:
                task_future.result()
            except Exception as e:
                logger.error(
                    f"[PIPELINE] Pipeline task for session {session.session_id} failed: {e}",
                    exc_info=True
                )
        
        pipeline_task_obj.add_done_callback(pipeline_done_callback)
        
        # Wait for completion
        await pipeline_task_obj
    
    async def _finalize_session(self, session: PipecatSessionState) -> None:
        """
        Finalize session after pipeline completion.
        
        This includes:
        - Calculate session duration
        - Extract transcript if needed
        - Update database
        
        Args:
            session: Session state to finalize
        """
        logger.info(f"[PIPELINE CLEANUP] Finalizing session {session.session_id}")
        
        # Calculate duration
        if not session.end_time:
            session.calculate_duration()
        
        logger.info(f"[PIPELINE CLEANUP] Session duration: {session.duration_seconds}s")
        
        # Check transcript
        captured_message_count = len(session.transcript) if session.transcript else 0
        logger.info(f"[PIPELINE CLEANUP] Captured {captured_message_count} messages")
        
        # Fall back to LLM context if no transcript captured
        if captured_message_count == 0:
            self._extract_transcript_from_context(session)
        else:
            logger.info(f"[PIPELINE CLEANUP] Using captured transcript")
            # Log sample messages for debugging
            self._log_transcript_sample(session)
        
        # Update database
        if not session.metrics_saved:
            logger.info(f"[PIPELINE CLEANUP] Updating database for session {session.session_id}")
            await self.db_updater.update_call_completion(session.session_id, session)
            session.metrics_saved = True
            logger.info(f"[PIPELINE CLEANUP] Database update completed")
    
    def _extract_transcript_from_context(self, session: PipecatSessionState) -> None:
        """
        Extract transcript from LLM context as fallback.
        
        Args:
            session: Session state with LLM context
        """
        logger.warning(f"[PIPELINE CLEANUP] No messages captured, falling back to LLM context")
        
        if not session.llm_context or not hasattr(session.llm_context, 'messages'):
            logger.warning(f"[PIPELINE CLEANUP] No LLM context available")
            return
        
        try:
            # Extract conversation messages (skip system messages)
            conversation_messages = [
                msg for msg in session.llm_context.messages
                if msg.get('role') in ['user', 'assistant'] and msg.get('content')
            ]
            
            if conversation_messages:
                session.transcript = conversation_messages
                logger.info(
                    f"[PIPELINE CLEANUP] Extracted {len(conversation_messages)} messages from LLM context"
                )
            else:
                logger.warning(f"[PIPELINE CLEANUP] No conversation messages found in LLM context")
                
        except Exception as e:
            logger.error(f"[PIPELINE CLEANUP] Failed to extract transcript: {e}")
    
    def _log_transcript_sample(self, session: PipecatSessionState) -> None:
        """
        Log sample transcript messages for debugging.
        
        Args:
            session: Session state with transcript
        """
        if not session.transcript:
            return
        
        # Log first few messages
        for i, msg in enumerate(session.transcript[:5]):
            content_preview = msg.get('content', '')[:100]
            logger.info(
                f"[PIPELINE CLEANUP] Message {i+1} ({msg.get('role')}): {content_preview}"
            )


# Singleton instance
_pipeline_orchestrator: Optional[PipelineOrchestrator] = None


def get_pipeline_orchestrator() -> PipelineOrchestrator:
    """
    Get or create the PipelineOrchestrator singleton.
    
    Returns:
        Singleton instance of PipelineOrchestrator
    """
    global _pipeline_orchestrator
    if _pipeline_orchestrator is None:
        _pipeline_orchestrator = PipelineOrchestrator()
    return _pipeline_orchestrator
