"""
Pipeline Executor.

Responsible for running PipelineTasks and handling execution-time errors.
"""

import asyncio
import logging
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams

logger = logging.getLogger(__name__)


class PipelineExecutor:
    """
    Executes a pipeline using PipelineRunner.
    """

    async def run(self, pipeline, session) -> None:
        """
        Run a pipeline and wait for completion.
        """
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=session.config.enable_interruptions,
                enable_metrics=True,
            ),
        )
        session.task = task

        runner = PipelineRunner()
        session.runner = runner

        pipeline_task = asyncio.create_task(runner.run(task))
        session.pipeline_background_task = pipeline_task

        def on_done(fut):
            try:
                fut.result()
            except Exception as e:
                logger.error(
                    f"[PIPELINE] Pipeline failed for session {session.session_id}",
                    exc_info=True,
                )

        pipeline_task.add_done_callback(on_done)
        await pipeline_task
