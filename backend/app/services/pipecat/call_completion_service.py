"""
Call Completion Service.

Orchestrates the completion workflow for Pipecat calls,
coordinating between database, transcript processing, and cost calculation.
"""
import logging
from typing import Optional
from datetime import datetime

from app.services.cost.cost_service import CostService

from .session_manager import PipecatSessionState
from .db import get_db_connector
from .db.models import CallUpdateData, CallResultsData, CallContext
from .transcript_formatter import get_transcript_formatter
from app.schemas.call import CallResultsCreate, CallStatus
from app.services.cost.cost_calculator import get_cost_calculator

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
            cost_breakdown = CostService._calculate_cost_breakdown(session)
            
            # Step 3: Merge cost breakdown into results
            CostService._merge_cost_breakdown(results_data, cost_breakdown)
            
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
    ) -> CallResultsCreate:
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
            
            # Exclude call_id from extracted_results since we're passing it explicitly
            logger.info(f"[CALL_COMPLETION] Successfully extracted structured data")
            return extracted_results
            
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
