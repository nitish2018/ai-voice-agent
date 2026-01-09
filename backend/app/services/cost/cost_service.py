import logging
from app.services.pipecat.session.session_manager import PipecatSessionState
from app.schemas.call import CallResultsCreate
from .cost_calculator import get_cost_calculator
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CostService:
    def __init__(self):
        self.cost_calculator = get_cost_calculator()

    @staticmethod
    def _calculate_cost_breakdown(session: PipecatSessionState) -> Dict[str, Any]:
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
        
        # Get cost calculator
        cost_calculator = get_cost_calculator()
        
        # Calculate cost breakdown
        cost_breakdown = cost_calculator.calculate_call_cost(
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
        

    @staticmethod
    def _merge_cost_breakdown(
        results_data: CallResultsCreate,
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

        logger.info(f"************************ results_data: {results_data} ************************")
        
        if isinstance(existing_raw, dict):
            existing_raw["cost_breakdown"] = cost_breakdown
        else:
            existing_raw = {"cost_breakdown": cost_breakdown}
        
        results_data.raw_extraction = existing_raw
        logger.debug(f"[CALL_COMPLETION] Merged cost breakdown into results")