"""
Pipecat Utility Helpers.

Contains reusable helper functions used by PipecatService.
These utilities are stateless and operate on session objects.

Responsibilities:
- Cancel running pipeline tasks
- Finalize session metrics
- Build response payloads
- Calculate cost breakdowns
"""

import asyncio
import logging
from typing import Dict, Any

from ...cost.cost_calculator import get_cost_calculator

logger = logging.getLogger(__name__)


class PipecatSessionUtils:
    """
    Utility helpers for Pipecat session lifecycle.
    """

    cost_calculator = get_cost_calculator()

    @staticmethod
    async def cancel_pipeline_if_running(session) -> None:
        """
        Cancel a running pipeline task if it exists.
        """
        task = getattr(session, "pipeline_background_task", None)

        if not task or task.done():
            return

        logger.info(
            f"[UTIL] Cancelling pipeline task for session {session.session_id}"
        )

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logger.info("[UTIL] Pipeline task cancelled")
        except Exception as e:
            logger.warning(f"[UTIL] Error cancelling pipeline task: {e}")

    @staticmethod
    async def finalize_session(session, call_completion_service) -> None:
        """
        Finalize session metrics and persist results.
        """
        if not session.duration_seconds:
            session.calculate_duration()

        if not session.metrics_saved:
            logger.info(
                f"[UTIL] Persisting session metrics for {session.session_id}"
            )
            await call_completion_service.complete_call(
                session.session_id, session
            )
            session.metrics_saved = True

    @classmethod
    def build_session_result(cls, session) -> Dict[str, Any]:
        """
        Build final session response payload.
        """
        cost = cls.cost_calculator.calculate_call_cost(
            stt_service=session.config.stt_config.service.value,
            tts_service=session.config.tts_config.service.value,
            llm_service=session.config.llm_config.service.value,
            transport_type=session.config.transport.value,
            duration_seconds=session.duration_seconds or 0,
            total_chars=session.total_chars_spoken or 0,
            total_tokens=(session.total_input_tokens or 0)
            + (session.total_output_tokens or 0),
            stt_model=session.config.stt_config.model,
            tts_model=session.config.tts_config.model,
            llm_model=session.config.llm_config.model,
            input_tokens=session.total_input_tokens or 0,
            output_tokens=session.total_output_tokens or 0,
        )

        return {
            "session_id": session.session_id,
            "transcript": session.transcript,
            "duration_seconds": session.duration_seconds,
            "cost_breakdown": cost.model_dump(),
            "status": "completed",
        }
