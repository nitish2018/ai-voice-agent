"""
Pipeline Builder.

Responsible ONLY for assembling Pipecat Pipeline graphs.
Does NOT run pipelines or manage lifecycle.
"""

import logging
from pipecat.pipeline.pipeline import Pipeline
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

from ..transcript_capture import create_transcript_processor
from ..transport.transport_factory import TransportFactory

logger = logging.getLogger(__name__)


class PipelineBuilder:
    """
    Builds pipelines for different transports.

    Responsibilities:
    - Create STT, TTS, LLM services
    - Assemble processors into a Pipeline
    - Attach transport input/output
    """

    def __init__(self, pipeline_factory, transport_factory: TransportFactory):
        self.pipeline_factory = pipeline_factory
        self.transport_factory = transport_factory

    def _create_llm_context(self, session):
        """
        Create initial LLM context seeded with system prompt.
        """
        context = OpenAILLMContext(messages=[
            {"role": "system", "content": session.system_prompt}
        ])
        logger.info("[PIPELINE] LLM context created")
        return context

    def build_daily(self, session) -> Pipeline:
        """
        Build a Daily WebRTC pipeline.
        """
        stt = self.pipeline_factory.create_stt_service(session.config)
        tts = self.pipeline_factory.create_tts_service(session.config)
        llm = self.pipeline_factory.create_llm_service(session.config)

        transport = self.transport_factory.create_daily(session)
        session.transport = transport

        context = self._create_llm_context(session)
        context_agg = llm.create_context_aggregator(context)
        session.llm_context = context

        user_tx = create_transcript_processor(session)
        bot_tx = create_transcript_processor(session)

        pipeline = Pipeline([
            transport.input(),
            stt,
            user_tx,
            context_agg.user(),
            llm,
            bot_tx,
            tts,
            transport.output(),
            context_agg.assistant(),
        ])

        logger.info("[PIPELINE] Daily pipeline assembled")
        return pipeline

    async def build_pipecat_ws(self, session) -> Pipeline:
        """
        Build a Pipecat-managed WebSocket pipeline.
        """
        ws_transport = self.transport_factory.create_pipecat_managed_ws()

        stt = self.pipeline_factory.create_stt_service(session.config)
        tts = self.pipeline_factory.create_tts_service(session.config)
        llm = self.pipeline_factory.create_llm_service(session.config)

        context = self._create_llm_context(session)
        context_agg = llm.create_context_aggregator(context)
        session.llm_context = context

        user_tx = create_transcript_processor(session)
        bot_tx = create_transcript_processor(session)

        pipeline = Pipeline([
            ws_transport.input(),
            stt,
            user_tx,
            context_agg.user(),
            llm,
            bot_tx,
            tts,
            ws_transport.output(),
            context_agg.assistant(),
        ])

        logger.info("[PIPELINE] Pipecat-managed WS pipeline assembled")
        return pipeline
