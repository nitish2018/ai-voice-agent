"""
Call Completion Service.

Orchestrates the completion workflow for Pipecat calls,
coordinating between database, transcript processing, and cost calculation.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .session_manager import PipecatSessionState
from .db import get_db_connector
from .db.models import CallUpdateData, CallResultsData, CallContext
from .transcript_formatter import get_transcript_formatter
from app.schemas.call import CallStatus
from app.services.cost_calculator import get_cost_calculator

logger = logging.getLogger(__name__)


class CallCompletionService:
    """
    Service for completing Pipecat call sessions.
    
    This service orchestrates the completion workflow by coordinating
    multiple specialized services to update the database with call results.
    
    Responsibilities:
    - Coordinate call completion workflow
    - Orchestrate database updates
    - Manage transcript processing
    - Calculate and store cost breakdowns
    - Handle errors gracefully
    
    Design Principles:
    - Single Responsibility: Orchestrates completion workflow only
    - Dependency Injection: Depends on abstractions (DBConnector interface)
    - Separation of Concerns: Delegates specific tasks to specialized services
    """
    
    def __init__(self):
        """
        Initialize the call completion service.
        
        Injects dependencies for database, formatting, and cost calculation.
        """
        self.db_connector = get_db_connector()
        self.transcript_formatter = get_transcript_formatter()
        self.cost_calculator = get_cost_calculator()
        logger.info("[CALL_COMPLETION] Service initialized")
    
    async def complete_call(
        self,
        session_id: str,
        session: PipecatSessionState
    ) -> bool:
        """
        Complete a call session and update database.
        
        This method orchestrates the entire completion workflow:
        1. Find call record by session ID
        2. Update call status and transcript
        3. Extract structured data from transcript
        4. Calculate cost breakdown
        5. Store results in database
        
        Args:
            session_id: Session ID to complete
            session: Session state with metrics and transcript
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"[CALL_COMPLETION] Starting completion for session: {session_id}")
            
            # Step 1: Find call record
            call_id = await self.db_connector.find_call_by_session_id(session_id)
            if not call_id:
                logger.warning(f"[CALL_COMPLETION] No call found for session: {session_id}")
                return False
            
            logger.info(f"[CALL_COMPLETION] Found call record: {call_id}")
            
            # Step 2: Update call status and basic metrics
            await self._update_call_status(call_id, session)
            
            # Step 3: Process and store results if call had meaningful duration
            if session.duration_seconds and session.duration_seconds > 0:
                await self._process_and_store_results(call_id, session)
            else:
                logger.info(f"[CALL_COMPLETION] Skipping results processing (zero duration)")
            
            logger.info(f"[CALL_COMPLETION] Successfully completed call: {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"[CALL_COMPLETION] Error completing call: {e}", exc_info=True)
            return False
    
    async def _update_call_status(
        self,
        call_id: str,
        session: PipecatSessionState
    ) -> None:
        """
        Update call status and basic metrics.
        
        Args:
            call_id: Call record ID
            session: Session state with metrics
        """
        logger.info(f"[CALL_COMPLETION] Updating call status: {call_id}")
        
        # Prepare update data
        update_data = CallUpdateData(
            status=CallStatus.COMPLETED.value,
            ended_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            duration_seconds=int(session.duration_seconds) if session.duration_seconds else None,
            transcript=None  # Will be set if transcript exists
        )
        
        # Format and add transcript if available
        if session.transcript and len(session.transcript) > 0:
            transcript_text = self.transcript_formatter.format_to_string(session.transcript)
            update_data.transcript = transcript_text
            
            message_counts = self.transcript_formatter.get_message_count(session.transcript)
            logger.info(f"[CALL_COMPLETION] Transcript: {message_counts['total']} messages "
                       f"({message_counts['user']} user, {message_counts['assistant']} assistant)")
        
        # Update database
        success = await self.db_connector.update_call(call_id, update_data)
        
        if success:
            logger.info(f"[CALL_COMPLETION] Successfully updated call status: {call_id}")
        else:
            logger.error(f"[CALL_COMPLETION] Failed to update call status: {call_id}")
    
    async def _process_and_store_results(
        self,
        call_id: str,
        session: PipecatSessionState
    ) -> None:
        """
        Process transcript and store structured results with cost breakdown.
        
        Args:
            call_id: Call record ID
            session: Session state with transcript and metrics
        """
        try:
            logger.info(f"[CALL_COMPLETION] Processing results for call: {call_id}")
            
            # Step 1: Extract structured data from transcript
            results_data = await self._extract_structured_data(call_id, session)
            
            # Step 2: Calculate cost breakdown
            cost_breakdown = self._calculate_cost_breakdown(session)
            
            # Step 3: Merge cost breakdown into results
            self._merge_cost_breakdown(results_data, cost_breakdown)
            
            # Step 4: Store in database
            success = await self.db_connector.upsert_call_results(results_data)
            
            if success:
                logger.info(f"[CALL_COMPLETION] Successfully stored results: {call_id}")
            else:
                logger.error(f"[CALL_COMPLETION] Failed to store results: {call_id}")
            
        except Exception as e:
            logger.error(f"[CALL_COMPLETION] Error processing results: {e}", exc_info=True)
    
    async def _extract_structured_data(
        self,
        call_id: str,
        session: PipecatSessionState
    ) -> CallResultsData:
        """
        Extract structured information from transcript.
        
        Uses the transcript processor service to extract structured data
        like driver status, location, ETA, etc.
        
        Args:
            call_id: Call record ID
            session: Session state with transcript
            
        Returns:
            CallResultsData with extracted information
        """
        # Return default results if no transcript
        if not session.transcript or len(session.transcript) == 0:
            logger.info(f"[CALL_COMPLETION] No transcript available for extraction")
            return self._get_default_results(call_id)
        
        try:
            from app.services.transcript_processor import get_transcript_processor
            
            # Get call details for context
            call_record = await self.db_connector.get_call_by_id(call_id)
            
            if not call_record:
                logger.warning(f"[CALL_COMPLETION] Could not fetch call details")
                return self._get_default_results(call_id)
            
            # Build call context
            call_context = CallContext(
                driver_name=call_record.driver_name,
                load_number=call_record.load_number,
                origin=call_record.origin,
                destination=call_record.destination,
            )
            
            # Format transcript for processor
            transcript_text = self.transcript_formatter.format_to_string(session.transcript)
            
            # Extract structured data using transcript processor
            logger.info(f"[CALL_COMPLETION] Extracting structured data from transcript")
            processor = get_transcript_processor()
            extracted_results = await processor.process_call_transcript(
                call_id=call_id,
                transcript=transcript_text,
                call_context=call_context.model_dump()
            )
            
            # Convert to CallResultsData
            results_data = CallResultsData(
                call_id=call_id,
                **extracted_results.model_dump()
            )
            
            logger.info(f"[CALL_COMPLETION] Successfully extracted structured data")
            return results_data
            
        except Exception as e:
            logger.warning(f"[CALL_COMPLETION] Failed to extract data: {e}")
            return self._get_default_results(call_id)
    
    def _get_default_results(self, call_id: str) -> CallResultsData:
        """
        Get default results when extraction fails or no transcript available.
        
        Args:
            call_id: Call record ID
            
        Returns:
            CallResultsData with default values
        """
        return CallResultsData(
            call_id=call_id,
            call_outcome="In-Transit Update",
            is_emergency=False,
        )
    
    def _calculate_cost_breakdown(self, session: PipecatSessionState) -> Dict[str, Any]:
        """
        Calculate cost breakdown for the session.
        
        Uses actual metrics if available, otherwise estimates based on duration.
        
        Args:
            session: Session state with metrics and configuration
            
        Returns:
            Cost breakdown dictionary
        """
        logger.info(f"[CALL_COMPLETION] Calculating cost breakdown")
        
        # Calculate estimates if actual metrics not available
        duration_minutes = (session.duration_seconds or 0) / 60
        estimated_chars = int(duration_minutes * 300)  # ~300 chars per minute of speech
        estimated_total_tokens = int(duration_minutes * 400)  # ~400 tokens per minute
        estimated_input_tokens = int(duration_minutes * 240)  # ~60% input
        estimated_output_tokens = int(duration_minutes * 160)  # ~40% output
        
        # Use actual values or estimates
        total_chars = session.total_chars_spoken or estimated_chars
        input_tokens = session.total_input_tokens or estimated_input_tokens
        output_tokens = session.total_output_tokens or estimated_output_tokens
        total_tokens = (session.total_input_tokens or 0) + (session.total_output_tokens or 0) or estimated_total_tokens
        
        logger.debug(f"[CALL_COMPLETION] Metrics - Duration: {session.duration_seconds}s, "
                    f"Chars: {total_chars}, Tokens: {total_tokens}")
        
        # Calculate cost breakdown
        cost_breakdown = self.cost_calculator.calculate_call_cost(
            stt_service=session.config.stt_config.service.value,
            tts_service=session.config.tts_config.service.value,
            llm_service=session.config.llm_config.service.value,
            transport_type=session.config.transport.value,
            duration_seconds=session.duration_seconds or 0,
            total_chars=total_chars,
            total_tokens=total_tokens,
            stt_model=session.config.stt_config.model or "nova-2",
            tts_model=session.config.tts_config.model or "sonic-english",
            llm_model=session.config.llm_config.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        
        logger.info(f"[CALL_COMPLETION] Total cost: ${cost_breakdown.total_cost_usd:.4f}")
        
        return cost_breakdown.model_dump()
    
    def _merge_cost_breakdown(
        self,
        results_data: CallResultsData,
        cost_breakdown: Dict[str, Any]
    ) -> None:
        """
        Merge cost breakdown into results data.
        
        Adds cost breakdown to the raw_extraction field for storage.
        
        Args:
            results_data: Results data to update (modified in place)
            cost_breakdown: Cost breakdown to merge
        """
        # Get existing raw extraction or create new dict
        existing_raw = results_data.raw_extraction or {}
        
        if isinstance(existing_raw, dict):
            existing_raw["cost_breakdown"] = cost_breakdown
        else:
            existing_raw = {"cost_breakdown": cost_breakdown}
        
        results_data.raw_extraction = existing_raw
        logger.debug(f"[CALL_COMPLETION] Merged cost breakdown into results")


# Singleton instance
_call_completion_service: Optional[CallCompletionService] = None


def get_call_completion_service() -> CallCompletionService:
    """
    Get or create the CallCompletionService singleton.
    
    Returns:
        Singleton instance of CallCompletionService
    """
    global _call_completion_service
    if _call_completion_service is None:
        _call_completion_service = CallCompletionService()
    return _call_completion_service
