"""
Pipecat Service - Manages Pipecat voice pipelines with Daily.co transport.

This service handles the full lifecycle of voice calls using the Pipecat framework,
including pipeline creation, Daily.co room management, and call orchestration.
"""
import logging
import uuid
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp
import time

from app.schemas.pipeline import (
    PipelineConfig,
    PipecatCallRequest,
    PipecatCallResponse,
    TransportType,
)
from app.core.config import settings
from app.services.pipeline_factory import get_pipeline_factory
from app.services.cost_calculator import get_cost_calculator

logger = logging.getLogger(__name__)

# Import Pipecat components
try:
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
    from pipecat.transports.services.daily import DailyParams, DailyTransport
    from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
    from pipecat.frames.frames import Frame, TranscriptionFrame, TextFrame
    
    class TranscriptCaptureProcessor(FrameProcessor):
        """
        Processor to capture transcripts from user speech and bot responses.
        """
        def __init__(self, session: 'PipecatSession'):
            super().__init__()
            self.session = session
            logger.info(f"[TRANSCRIPT] TranscriptCaptureProcessor initialized for session {session.session_id}")
        
        async def process_frame(self, frame: Frame, direction: FrameDirection):
            """Process frames to capture transcripts."""
            await super().process_frame(frame, direction)
            
            # Capture user speech (TranscriptionFrame from STT)
            if isinstance(frame, TranscriptionFrame):
                text = frame.text
                if text and text.strip():
                    logger.info(f"[TRANSCRIPT] Captured user speech: {text[:100]}")
                    self.session.transcript.append({
                        "role": "user",
                        "content": text.strip()
                    })
            
            # Capture bot responses (TextFrame from LLM to TTS)
            elif isinstance(frame, TextFrame):
                text = frame.text
                if text and text.strip():
                    logger.info(f"[TRANSCRIPT] Captured bot response: {text[:100]}")
                    self.session.transcript.append({
                        "role": "assistant",
                        "content": text.strip()
                    })
            
            # Always pass the frame through
            await self.push_frame(frame, direction)
    
    PIPECAT_AVAILABLE = True
except ImportError as e:
    logger.error(f"Pipecat not available: {e}")
    PIPECAT_AVAILABLE = False


@dataclass
class PipecatSession:
    """Represents an active Pipecat call session."""
    session_id: str
    call_id: str
    config: PipelineConfig
    system_prompt: str
    daily_room_url: Optional[str] = None
    daily_token: Optional[str] = None
    websocket_url: Optional[str] = None
    transport: Optional[Any] = None
    pipeline: Optional[Any] = None
    task: Optional[Any] = None
    runner: Optional[Any] = None
    llm_context: Optional[Any] = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    transcript: List[Dict[str, str]] = field(default_factory=list)
    total_input_tokens: Optional[int] = None
    total_output_tokens: Optional[int] = None
    total_chars_spoken: Optional[int] = None
    metrics_saved: bool = False
    pipeline_background_task: Optional[asyncio.Task] = None


class PipecatService:
    """Service for managing Pipecat voice pipelines."""
    
    def __init__(self):
        """Initialize the Pipecat service."""
        if not PIPECAT_AVAILABLE:
            logger.warning("Pipecat framework not available")
            return
        
        self.active_sessions: Dict[str, PipecatSession] = {}
        self.completed_sessions: Dict[str, PipecatSession] = {}
        self.factory = get_pipeline_factory()
        logger.info("PipecatService initialized")
    
    async def create_daily_room(self, session_id: str) -> Dict[str, Any]:
        """
        Create a Daily.co room for the session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Dictionary with room URL and token
            
        Raises:
            Exception: If room creation fails
        """
        if not settings.daily_api_key:
            raise Exception("DAILY_API_KEY not configured")
        
        # Create room
        room_name = f"dispatcher-{session_id[:8]}"
        
        # Calculate expiry time (1 hour from now) using time.time() for more reliable timestamp
        exp_timestamp = int(time.time()) + 3600
        
        room_config = {
            "name": room_name,
            "properties": {
                "exp": exp_timestamp,
                "enable_chat": False,
                "enable_emoji_reactions": False,
                "max_participants": 2,
            }
        }
        
        headers = {
            "Authorization": f"Bearer {settings.daily_api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            # Create room
            async with session.post(
                "https://api.daily.co/v1/rooms",
                json=room_config,
                headers=headers
            ) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise Exception(f"Failed to create Daily room: {error_text}")
                
                room_data = await response.json()
                room_url = room_data["url"]
            
            # Create meeting token for bot
            token_config = {
                "properties": {
                    "room_name": room_name,
                    "is_owner": True,
                    "exp": exp_timestamp,
                }
            }
            
            async with session.post(
                "https://api.daily.co/v1/meeting-tokens",
                json=token_config,
                headers=headers
            ) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise Exception(f"Failed to create meeting token: {error_text}")
                
                token_data = await response.json()
                token = token_data["token"]
        
        logger.info(f"Created Daily room: {room_url}")
        return {
            "room_url": room_url,
            "token": token
        }
    
    def _replace_placeholders(self, text: str, request: PipecatCallRequest) -> str:
        """
        Replace placeholders in text with actual values from the request.
        
        Args:
            text: Text containing placeholders like {{driver_name}}
            request: Call request with context values
            
        Returns:
            Text with placeholders replaced
        """
        if not text:
            return text
            
        replacements = {
            "{{driver_name}}": request.driver_name or "driver",
            "{{load_number}}": request.load_number or "your load",
            "{{origin}}": request.origin or "the origin",
            "{{destination}}": request.destination or "the destination",
            "{{expected_eta}}": request.expected_eta or "the expected time",
        }
        
        result = text
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        
        return result
    
    async def start_call(
        self,
        request: PipecatCallRequest,
        agent_config: PipelineConfig,
        system_prompt: str
    ) -> PipecatCallResponse:
        """
        Start a new Pipecat call session.
        
        Args:
            request: Call request with context
            agent_config: Pipeline configuration
            system_prompt: System prompt for the LLM
            
        Returns:
            Call response with session info
        """
        if not PIPECAT_AVAILABLE:
            raise Exception("Pipecat not available")
        
        session_id = str(uuid.uuid4())
        logger.info(f"Starting Pipecat call session: {session_id}")
        
        # Replace placeholders in prompts with actual values
        system_prompt_filled = self._replace_placeholders(system_prompt, request)
        
        logger.info(f"System prompt (first 100 chars): {system_prompt_filled[:100]}...")
        
        # Create session object
        session = PipecatSession(
            session_id=session_id,
            call_id=request.agent_id,  # Will be updated with actual call ID
            config=agent_config,
            system_prompt=system_prompt_filled
        )
        
        # Create Daily room if using WebRTC transport
        if agent_config.transport == TransportType.DAILY_WEBRTC:
            daily_room = await self.create_daily_room(session_id)
            session.daily_room_url = daily_room["room_url"]
            session.daily_token = daily_room["token"]
            
            # Store session
            self.active_sessions[session_id] = session
            
            # Start pipeline in background
            logger.info(f"Starting Daily pipeline for session {session_id}")
            asyncio.create_task(self._run_daily_pipeline(session))
            
            # Give the bot a moment to start joining
            await asyncio.sleep(2)
            
            return PipecatCallResponse(
                session_id=session_id,
                daily_room_url=session.daily_room_url,
                daily_token=session.daily_token,
                status="initialized"
            )
        else:
            # WebSocket transport
            raise NotImplementedError("WebSocket transport not yet implemented")
    
    async def _run_daily_pipeline(self, session: PipecatSession):
        """
        Run the Pipecat pipeline for a Daily.co session.
        
        Args:
            session: Pipecat session to run
        """
        logger.info(f"Starting Daily pipeline for session: {session.session_id}")
        logger.info(f"Room URL: {session.daily_room_url}")
        
        try:
            # Create services using factory
            logger.info("Creating STT service...")
            stt = self.factory.create_stt_service(session.config)
            logger.info("Creating TTS service...")
            tts = self.factory.create_tts_service(session.config)
            logger.info("Creating LLM service...")
            llm = self.factory.create_llm_service(session.config)
            
            # Create Daily transport
            logger.info("Creating Daily transport...")
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
            logger.info("Daily transport created successfully")
            
            session.transport = transport
            
            # Create LLM context with system prompt
            messages = [
                {
                    "role": "system",
                    "content": session.system_prompt
                }
            ]
            
            # Don't add begin_message to context - we'll trigger it with a user message
            
            context = OpenAILLMContext(messages=messages)
            context_aggregator = llm.create_context_aggregator(context)
            
            # Store context reference on session for transcript extraction later
            session.llm_context = context
            
            # Create transcript capture processors
            user_transcript_capture = TranscriptCaptureProcessor(session)
            bot_transcript_capture = TranscriptCaptureProcessor(session)
            
            # Build pipeline
            pipeline = Pipeline([
                transport.input(),  # Audio input from user
                stt,  # Speech-to-text
                user_transcript_capture,  # Capture user transcription
                context_aggregator.user(),  # Add user message to context
                llm,  # Generate response
                bot_transcript_capture,  # Capture bot response
                tts,  # Text-to-speech
                transport.output(),  # Audio output to user
                context_aggregator.assistant(),  # Add assistant message to context
            ])
            
            session.pipeline = pipeline
            
            # Create task
            task = PipelineTask(
                pipeline,
                params=PipelineParams(
                    allow_interruptions=session.config.enable_interruptions,
                    enable_metrics=True,
                )
            )
            
            session.task = task
            
            # Create and run pipeline runner
            logger.info("Creating pipeline runner...")
            runner = PipelineRunner()
            session.runner = runner
            
            # Start the pipeline in the background
            logger.info(f"Starting pipeline runner for session {session.session_id}...")
            pipeline_task_obj = asyncio.create_task(runner.run(task))
            session.pipeline_background_task = pipeline_task_obj
            
            # Add a done callback to catch exceptions from the background task
            def pipeline_done_callback(task_future):
                try:
                    task_future.result()  # This will raise if the task raised an exception
                except Exception as e:
                    logger.error(f"Pipeline task for session {session.session_id} failed: {e}", exc_info=True)
            
            pipeline_task_obj.add_done_callback(pipeline_done_callback)
            
            # Bot will speak when user speaks first, following the system prompt
            
            # Wait for the pipeline to complete
            await pipeline_task_obj
            
            logger.info(f"Pipeline completed for session: {session.session_id}")
            
        except Exception as e:
            logger.error(f"Pipeline error for session {session.session_id}: {e}", exc_info=True)
            raise  # Re-raise to see the full error in logs
        finally:
            logger.info(f"[PIPELINE CLEANUP] Pipeline finally block executing for session {session.session_id}")
            # Mark session as ended
            if not session.end_time:
                session.end_time = datetime.utcnow()
                session.duration_seconds = (session.end_time - session.start_time).total_seconds()
            
            logger.info(f"[PIPELINE CLEANUP] Session duration: {session.duration_seconds}s")
            
            # Check if transcript was captured by TranscriptCaptureProcessor
            captured_message_count = len(session.transcript) if session.transcript else 0
            logger.info(f"[PIPELINE CLEANUP] TranscriptCaptureProcessor captured {captured_message_count} messages")
            
            # If no transcript captured, fall back to LLM context extraction
            if captured_message_count == 0:
                logger.warning(f"[PIPELINE CLEANUP] No messages captured by processor, falling back to LLM context")
                if session.llm_context and hasattr(session.llm_context, 'messages'):
                    try:
                        # Skip system message and initial greeting, get actual conversation
                        conversation_messages = [
                            msg for msg in session.llm_context.messages
                            if msg.get('role') in ['user', 'assistant'] and 
                            msg.get('content') and
                            msg.get('content') != session.begin_message  # Skip initial greeting
                        ]
                        if conversation_messages:
                            session.transcript = conversation_messages
                            logger.info(f"[PIPELINE CLEANUP] Extracted {len(conversation_messages)} messages from LLM context")
                        else:
                            logger.warning(f"[PIPELINE CLEANUP] No conversation messages found in LLM context")
                    except Exception as transcript_err:
                        logger.error(f"[PIPELINE CLEANUP] Failed to extract transcript: {transcript_err}")
            else:
                logger.info(f"[PIPELINE CLEANUP] Using captured transcript with {captured_message_count} messages")
                # Log first few messages for debugging
                if session.transcript:
                    for i, msg in enumerate(session.transcript[:5]):  # Show first 5 messages
                        content_preview = msg.get('content', '')[:100]
                        logger.info(f"[PIPELINE CLEANUP] Message {i+1} ({msg.get('role')}): {content_preview}")
            
            # Update database status when pipeline ends
            logger.info(f"[PIPELINE CLEANUP] Calling database update for session {session.session_id}")
            await self._update_call_status_in_db(session.session_id, "completed", session)
            session.metrics_saved = True
            logger.info(f"[PIPELINE CLEANUP] Database update completed for session {session.session_id}")
            
            # Move to completed sessions for later access
            if session.session_id in self.active_sessions:
                self.completed_sessions[session.session_id] = self.active_sessions.pop(session.session_id)
                logger.info(f"[PIPELINE CLEANUP] Moved session {session.session_id} to completed sessions")
    
    async def _update_call_status_in_db(
        self,
        session_id: str,
        status: str,
        session: Optional['PipecatSession'] = None
    ) -> None:
        """
        Update call status in database.
        
        Args:
            session_id: Session ID to update
            status: New status (e.g., "completed")
            session: Optional session object with metrics
        """
        try:
            logger.info(f"[DB UPDATE] Starting database update for session {session_id} with status {status}")
            from app.db.database import get_supabase_client, Tables
            from app.schemas.call import CallStatus
            
            db = get_supabase_client()
            
            # Find the call by session_id (stored in retell_call_id field)
            logger.info(f"[DB UPDATE] Querying database for session {session_id}")
            call_result = db.table(Tables.CALLS).select("*").eq("retell_call_id", session_id).execute()
            
            if not call_result.data or len(call_result.data) == 0:
                logger.warning(f"[DB UPDATE] No call found with session_id {session_id}")
                return
            
            logger.info(f"[DB UPDATE] Found call record: {call_result.data[0].get('id')}")
            
            call_id = call_result.data[0]["id"]
            
            # Prepare update data
            update_data = {
                "status": CallStatus.COMPLETED.value if status == "completed" else status,
                "ended_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            
            # Add session metrics if available
            if session:
                if session.duration_seconds:
                    # Convert to integer since database expects integer type
                    update_data["duration_seconds"] = int(session.duration_seconds)
                if session.transcript and len(session.transcript) > 0:
                    # Convert transcript list to formatted string
                    transcript_text = "\n\n".join([
                        f"{msg['role'].upper()}: {msg['content']}"
                        for msg in session.transcript
                    ])
                    update_data["transcript"] = transcript_text
                    logger.info(f"[DB UPDATE] Transcript has {len(session.transcript)} messages")
            
            # Update call status in database
            logger.info(f"[DB UPDATE] Updating call {call_id} with data: {list(update_data.keys())}")
            db.table(Tables.CALLS).update(update_data).eq("id", call_id).execute()
            logger.info(f"[DB UPDATE] Successfully updated call {call_id} status to {status}")
            
            # Process transcript and calculate costs if session has metrics
            if session and session.duration_seconds and session.duration_seconds > 0:
                try:
                    # 1. Extract structured information from transcript (if available)
                    call_results_data = None
                    if update_data.get("transcript"):
                        logger.info(f"[DB UPDATE] Processing transcript for call {call_id}")
                        try:
                            from app.services.transcript_processor import get_transcript_processor
                            
                            # Get call details for context
                            call_result = db.table(Tables.CALLS).select("*").eq("id", call_id).execute()
                            if call_result.data:
                                call_record = call_result.data[0]
                                call_context = {
                                    "driver_name": call_record.get("driver_name"),
                                    "load_number": call_record.get("load_number"),
                                    "origin": call_record.get("origin"),
                                    "destination": call_record.get("destination"),
                                }
                                
                                processor = get_transcript_processor()
                                extracted_results = await processor.process_call_transcript(
                                    call_id=call_id,
                                    transcript=update_data["transcript"],
                                    call_context=call_context
                                )
                                
                                # Convert to dict for database insertion
                                call_results_data = extracted_results.model_dump()
                                call_results_data["call_id"] = call_id
                                logger.info(f"[DB UPDATE] Successfully extracted structured data from transcript")
                        except Exception as transcript_err:
                            logger.warning(f"[DB UPDATE] Failed to process transcript: {transcript_err}")
                            # Continue with default structure
                    
                    # 2. Calculate cost breakdown
                    logger.info(f"[DB UPDATE] Calculating cost breakdown for call {call_id}")
                    cost_calc = get_cost_calculator()
                    cost_breakdown = cost_calc.calculate_call_cost(
                        stt_service=session.config.stt_config.service.value,
                        tts_service=session.config.tts_config.service.value,
                        llm_service=session.config.llm_config.service.value,
                        transport_type=session.config.transport.value,
                        duration_seconds=session.duration_seconds,
                        total_chars=session.total_chars_spoken or int(session.duration_seconds / 60 * 300),
                        total_tokens=(session.total_input_tokens or 0) + (session.total_output_tokens or 0) or int(session.duration_seconds / 60 * 400),
                        stt_model=session.config.stt_config.model or "nova-2",
                        tts_model=session.config.tts_config.model or "sonic-english",
                        llm_model=session.config.llm_config.model,
                        input_tokens=session.total_input_tokens or int(session.duration_seconds / 60 * 240),
                        output_tokens=session.total_output_tokens or int(session.duration_seconds / 60 * 160),
                    )
                    
                    # 3. Merge extracted data with cost breakdown
                    if not call_results_data:
                        # No transcript extraction, use default structure
                        call_results_data = {
                            "call_id": call_id,
                            "call_outcome": "In-Transit Update",
                            "is_emergency": False,
                        }
                    
                    # Add cost breakdown to raw_extraction
                    existing_raw = call_results_data.get("raw_extraction") or {}
                    if isinstance(existing_raw, dict):
                        existing_raw["cost_breakdown"] = cost_breakdown.model_dump()
                    else:
                        existing_raw = {"cost_breakdown": cost_breakdown.model_dump()}
                    call_results_data["raw_extraction"] = existing_raw
                    
                    # 4. Store in database
                    logger.info(f"[DB UPDATE] Storing call results with cost breakdown for call {call_id}")
                    db.table(Tables.CALL_RESULTS).upsert(call_results_data).execute()
                    logger.info(f"[DB UPDATE] Successfully stored call results and cost breakdown for call {call_id}")
                except Exception as cost_err:
                    logger.error(f"[DB UPDATE] Failed to calculate/store results: {cost_err}", exc_info=True)
            
            logger.info(f"Updated call {call_id} status to {status} (session: {session_id})")
        except Exception as e:
            logger.error(f"Failed to update call status in DB: {e}", exc_info=True)
    
    async def end_call(self, session_id: str) -> Dict[str, Any]:
        """
        End an active Pipecat call session.
        
        Args:
            session_id: Session ID to end
            
        Returns:
            Session metrics and transcript
        """
        # Check active sessions first
        session = self.active_sessions.get(session_id)
        
        # If not in active, check completed sessions
        if not session:
            session = self.completed_sessions.get(session_id)
            if session:
                logger.info(f"Session {session_id} already completed naturally")
                # Ensure database is updated if not already done
                if not session.metrics_saved:
                    await self._update_call_status_in_db(session_id, "completed", session)
                    session.metrics_saved = True
                
                # Return metrics
                return self._build_session_metrics(session)
        
        if not session:
            logger.warning(f"Session {session_id} not found")
            return None
        
        logger.info(f"Ending Pipecat session: {session_id}")
        
        try:
            # Cancel pipeline task - this will trigger transport cleanup
            if session.pipeline_background_task and not session.pipeline_background_task.done():
                logger.info(f"Cancelling pipeline task for session {session_id}")
                session.pipeline_background_task.cancel()
                try:
                    await session.pipeline_background_task
                except asyncio.CancelledError:
                    logger.info(f"Pipeline task cancelled for session {session_id}")
                except Exception as e:
                    logger.warning(f"Error during pipeline cancellation: {e}")
            
            # Mark session as ended
            if not session.end_time:
                session.end_time = datetime.utcnow()
                session.duration_seconds = (session.end_time - session.start_time).total_seconds()
            
            # Update database if not already done
            if not session.metrics_saved:
                await self._update_call_status_in_db(session_id, "completed", session)
                session.metrics_saved = True
            
            # Move to completed sessions
            if session_id in self.active_sessions:
                self.completed_sessions[session_id] = self.active_sessions.pop(session_id)
            
            # Return metrics
            return self._build_session_metrics(session)
            
        except Exception as e:
            logger.error(f"Error ending session {session_id}: {e}", exc_info=True)
            raise
    
    def _build_session_metrics(self, session: PipecatSession) -> Dict[str, Any]:
        """Build session metrics response."""
        # Calculate cost breakdown
        cost_calc = get_cost_calculator()
        cost_breakdown = cost_calc.calculate_call_cost(
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
        """Get list of active session IDs."""
        return list(self.active_sessions.keys())


# Singleton instance
_pipecat_service: Optional[PipecatService] = None


def get_pipecat_service() -> PipecatService:
    """Get or create the PipecatService singleton."""
    global _pipecat_service
    if _pipecat_service is None:
        _pipecat_service = PipecatService()
    return _pipecat_service
