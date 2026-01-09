"""
Session Finalizer.

Handles cleanup, transcript extraction, and DB updates after pipeline completion.
"""

import logging

logger = logging.getLogger(__name__)


class SessionFinalizer:
    """
    Finalizes a session after pipeline execution.
    """

    def __init__(self, call_completion_service):
        self.call_completion_service = call_completion_service

    async def finalize(self, session) -> None:
        """
        Finalize session lifecycle.
        """
        logger.info(f"[PIPELINE CLEANUP] Finalizing session {session.session_id}")

        if not session.end_time:
            session.calculate_duration()

        if not session.transcript:
            self._extract_from_context(session)

        if not session.metrics_saved:
            await self.call_completion_service.complete_call(
                session.session_id,
                session,
            )
            session.metrics_saved = True
            logger.info("[PIPELINE CLEANUP] Database updated")

    def _extract_from_context(self, session):
        """
        Fallback transcript extraction from LLM context.
        """
        if not session.llm_context:
            return

        session.transcript = [
            msg
            for msg in session.llm_context.messages
            if msg.get("role") in ("user", "assistant") and msg.get("content")
        ]
