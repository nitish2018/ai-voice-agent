"""
Database Update Service.

Handles all database operations for Pipecat sessions,
including status updates, transcript storage, and cost calculations.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.db.database import get_supabase_client, Tables
from app.schemas.call import CallStatus
from .session_manager import PipecatSessionState
from app.services.cost_calculator import get_cost_calculator

logger = logging.getLogger(__name__)


class DatabaseUpdater:
    """
    Service for updating database records for Pipecat sessions.
    
    Responsibilities:
    - Update call status in database
    - Store transcripts
    - Process and extract structured data from transcripts
    - Calculate and store cost breakdowns
    - Handle error cases gracefully
    """
    
    def __init__(self):
        """Initialize the database updater service."""
        self.db = get_supabase_client()
        self.cost_calculator = get_cost_calculator()
        logger.info("DatabaseUpdater initialized")
    
    async def update_call_completion(
        self,
        session_id: str,
        session: PipecatSessionState
    ) -> None:
        """
        Update database when a call completes.
        
        This performs several operations:
        1. Update call status to completed
        2. Store transcript
        3. Extract structured data from transcript
        4. Calculate cost breakdown
        5. Store all results
        
        Args:
            session_id: Session ID to update
            session: Session state with metrics and transcript
        """
        try:
            logger.info(f"[DB UPDATE] Starting database update for session {session_id}")
            
            # Find call by session_id (stored in retell_call_id field)
            call_id = await self._find_call_id(session_id)
            if not call_id:
                logger.warning(f"[DB UPDATE] No call found with session_id {session_id}")
                return
            
            logger.info(f"[DB UPDATE] Found call record: {call_id}")
            
            # Update call status and basic metrics
            await self._update_call_status(call_id, session)
            
            # Process transcript and store results if available
            if session.duration_seconds and session.duration_seconds > 0:
                await self._process_and_store_results(call_id, session)
            
            logger.info(f"[DB UPDATE] Successfully completed database update for call {call_id}")
            
        except Exception as e:
            logger.error(f"[DB UPDATE] Failed to update database: {e}", exc_info=True)
    
    async def _find_call_id(self, session_id: str) -> Optional[str]:
        """
        Find call ID by session ID.
        
        Args:
            session_id: Session ID stored in retell_call_id field
            
        Returns:
            Call ID if found, None otherwise
        """
        try:
            result = self.db.table(Tables.CALLS).select("id").eq("retell_call_id", session_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]["id"]
            
            return None
            
        except Exception as e:
            logger.error(f"[DB UPDATE] Error finding call ID: {e}")
            return None
    
    async def _update_call_status(
        self,
        call_id: str,
        session: PipecatSessionState
    ) -> None:
        """
        Update call status and basic metrics in database.
        
        Args:
            call_id: Call record ID
            session: Session state with metrics
        """
        update_data = {
            "status": CallStatus.COMPLETED.value,
            "ended_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        # Add duration if available
        if session.duration_seconds:
            update_data["duration_seconds"] = int(session.duration_seconds)
        
        # Add transcript if available
        if session.transcript and len(session.transcript) > 0:
            transcript_text = self._format_transcript(session.transcript)
            update_data["transcript"] = transcript_text
            logger.info(f"[DB UPDATE] Transcript has {len(session.transcript)} messages")
        
        # Update database
        logger.info(f"[DB UPDATE] Updating call {call_id} with data: {list(update_data.keys())}")
        self.db.table(Tables.CALLS).update(update_data).eq("id", call_id).execute()
        logger.info(f"[DB UPDATE] Successfully updated call {call_id}")
    
    def _format_transcript(self, transcript: list) -> str:
        """
        Format transcript list into a readable string.
        
        Args:
            transcript: List of message dictionaries
            
        Returns:
            Formatted transcript string
        """
        return "\n\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in transcript
        ])
    
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
            # Extract structured data from transcript
            call_results_data = await self._extract_structured_data(call_id, session)
            
            # Calculate cost breakdown
            cost_breakdown = self._calculate_cost_breakdown(session)
            
            # Merge cost breakdown into results
            self._merge_cost_breakdown(call_results_data, cost_breakdown)
            
            # Store in database
            logger.info(f"[DB UPDATE] Storing call results with cost breakdown for call {call_id}")
            self.db.table(Tables.CALL_RESULTS).upsert(call_results_data).execute()
            logger.info(f"[DB UPDATE] Successfully stored call results for call {call_id}")
            
        except Exception as e:
            logger.error(f"[DB UPDATE] Failed to process and store results: {e}", exc_info=True)
    
    async def _extract_structured_data(
        self,
        call_id: str,
        session: PipecatSessionState
    ) -> Dict[str, Any]:
        """
        Extract structured information from transcript.
        
        Args:
            call_id: Call record ID
            session: Session state with transcript
            
        Returns:
            Dictionary with extracted call results
        """
        # Only extract if transcript exists
        if not session.transcript or len(session.transcript) == 0:
            logger.info(f"[DB UPDATE] No transcript available for extraction")
            return self._get_default_results(call_id)
        
        try:
            from app.services.transcript_processor import get_transcript_processor
            
            # Get call details for context
            call_result = self.db.table(Tables.CALLS).select("*").eq("id", call_id).execute()
            
            if not call_result.data:
                logger.warning(f"[DB UPDATE] Could not fetch call details for context")
                return self._get_default_results(call_id)
            
            call_record = call_result.data[0]
            call_context = {
                "driver_name": call_record.get("driver_name"),
                "load_number": call_record.get("load_number"),
                "origin": call_record.get("origin"),
                "destination": call_record.get("destination"),
            }
            
            # Format transcript for processor
            transcript_text = self._format_transcript(session.transcript)
            
            # Extract structured data
            logger.info(f"[DB UPDATE] Processing transcript for call {call_id}")
            processor = get_transcript_processor()
            extracted_results = await processor.process_call_transcript(
                call_id=call_id,
                transcript=transcript_text,
                call_context=call_context
            )
            
            # Convert to dict
            results_dict = extracted_results.model_dump()
            results_dict["call_id"] = call_id
            logger.info(f"[DB UPDATE] Successfully extracted structured data from transcript")
            
            return results_dict
            
        except Exception as e:
            logger.warning(f"[DB UPDATE] Failed to process transcript: {e}")
            return self._get_default_results(call_id)
    
    def _get_default_results(self, call_id: str) -> Dict[str, Any]:
        """
        Get default results structure when extraction fails.
        
        Args:
            call_id: Call record ID
            
        Returns:
            Default results dictionary
        """
        return {
            "call_id": call_id,
            "call_outcome": "In-Transit Update",
            "is_emergency": False,
        }
    
    def _calculate_cost_breakdown(self, session: PipecatSessionState) -> Dict[str, Any]:
        """
        Calculate cost breakdown for the session.
        
        Args:
            session: Session state with metrics and configuration
            
        Returns:
            Cost breakdown dictionary
        """
        logger.info(f"[DB UPDATE] Calculating cost breakdown")
        
        # Estimate tokens/chars if not available
        duration_minutes = (session.duration_seconds or 0) / 60
        estimated_chars = int(duration_minutes * 300)  # ~300 chars per minute
        estimated_total_tokens = int(duration_minutes * 400)  # ~400 tokens per minute
        estimated_input_tokens = int(duration_minutes * 240)  # ~60% input
        estimated_output_tokens = int(duration_minutes * 160)  # ~40% output
        
        cost_breakdown = self.cost_calculator.calculate_call_cost(
            stt_service=session.config.stt_config.service.value,
            tts_service=session.config.tts_config.service.value,
            llm_service=session.config.llm_config.service.value,
            transport_type=session.config.transport.value,
            duration_seconds=session.duration_seconds or 0,
            total_chars=session.total_chars_spoken or estimated_chars,
            total_tokens=(session.total_input_tokens or 0) + (session.total_output_tokens or 0) or estimated_total_tokens,
            stt_model=session.config.stt_config.model or "nova-2",
            tts_model=session.config.tts_config.model or "sonic-english",
            llm_model=session.config.llm_config.model,
            input_tokens=session.total_input_tokens or estimated_input_tokens,
            output_tokens=session.total_output_tokens or estimated_output_tokens,
        )
        
        return cost_breakdown.model_dump()
    
    def _merge_cost_breakdown(
        self,
        results_data: Dict[str, Any],
        cost_breakdown: Dict[str, Any]
    ) -> None:
        """
        Merge cost breakdown into results data.
        
        Args:
            results_data: Results dictionary to update
            cost_breakdown: Cost breakdown to merge
        """
        existing_raw = results_data.get("raw_extraction") or {}
        
        if isinstance(existing_raw, dict):
            existing_raw["cost_breakdown"] = cost_breakdown
        else:
            existing_raw = {"cost_breakdown": cost_breakdown}
        
        results_data["raw_extraction"] = existing_raw


# Singleton instance
_database_updater: Optional[DatabaseUpdater] = None


def get_database_updater() -> DatabaseUpdater:
    """
    Get or create the DatabaseUpdater singleton.
    
    Returns:
        Singleton instance of DatabaseUpdater
    """
    global _database_updater
    if _database_updater is None:
        _database_updater = DatabaseUpdater()
    return _database_updater
