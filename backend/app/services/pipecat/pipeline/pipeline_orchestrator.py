"""
Pipeline Orchestrator.

Acts as the SINGLE public entry point for running Pipecat pipelines.
Coordinates pipeline creation, execution, and cleanup while delegating
actual work to SRP-compliant collaborators.
"""

import logging
from typing import Optional

from app.services.pipecat.pipeline.pipeline_builder import PipelineBuilder
from app.services.pipecat.transport.transport_factory import TransportFactory
from app.services.pipecat.pipeline.pipeline_executor import PipelineExecutor
from app.services.pipecat.session.session_finalizer import SessionFinalizer
from app.services.pipecat.pipeline.pipeline_factory import get_pipeline_factory
from app.services.pipecat.call.call_completion_service import get_call_completion_service

logger = logging.getLogger(__name__)

_pipeline_orchestrator: Optional["PipelineOrchestrator"] = None


class PipelineOrchestrator:
    """
    High-level coordinator for Pipecat pipelines.

    Responsibilities:
    - Choose pipeline type (Daily / Pipecat-managed WS)
    - Coordinate build → run → finalize lifecycle
    - Act as a façade for external callers
    """

    def __init__(self):
        self.pipeline_factory = get_pipeline_factory()
        self.transport_factory = TransportFactory()
        self.pipeline_builder = PipelineBuilder(
            self.pipeline_factory,
            self.transport_factory
        )
        self.pipeline_executor = PipelineExecutor()
        self.session_finalizer = SessionFinalizer(
            get_call_completion_service()
        )

        logger.info("PipelineOrchestrator initialized")
    
    async def run_pipeline(self, session) -> None:
        """
        Run a pipeline.

        Execution flow:
        1. Build pipeline
        2. Execute pipeline
        3. Finalize session (always)
        """
        logger.info(f"[PIPELINE] Starting {session.transport.name} pipeline for session {session.session_id}")
        
        try:
            pipeline = self.pipeline_builder.build(session)
            session.pipeline = pipeline
            await self.pipeline_executor.run(pipeline, session)
        finally:
            await self.session_finalizer.finalize(session)


def get_pipeline_orchestrator() -> PipelineOrchestrator:
    """
    Singleton accessor.

    Ensures exactly one orchestrator instance exists per process.
    """
    global _pipeline_orchestrator
    if _pipeline_orchestrator is None:
        _pipeline_orchestrator = PipelineOrchestrator()
    return _pipeline_orchestrator
