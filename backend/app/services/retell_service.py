"""
Retell AI Service - Handles all interactions with Retell AI API.

Uses Retell's built-in LLM for conversation handling.
"""
import logging
from typing import Optional, Dict, Any, List
from retell import Retell
from retell.types import AgentResponse as RetellAgentResponse

from app.core.config import settings
from app.schemas.agent import VoiceSettings, AgentState, DenoisingMode

logger = logging.getLogger(__name__)


class RetellService:
    """Service for interacting with Retell AI API."""

    def __init__(self):
        """Initialize Retell client."""
        self.client = Retell(api_key=settings.retell_api_key)

    async def create_llm(
            self,
            system_prompt: str,
            begin_message: Optional[str] = None,
            states: Optional[List[AgentState]] = None,
            starting_state: Optional[str] = None,
            model: str = "gpt-4o"
    ) -> str:
        """
        Create a Retell LLM configuration.

        Args:
            system_prompt: Main system prompt
            begin_message: Initial greeting message
            states: Multi-state conversation configuration
            starting_state: Initial state name
            model: LLM model to use

        Returns:
            LLM ID
        """
        try:
            # Build states configuration if provided
            states_config = None
            if states:
                states_config = [
                    {
                        "name": state.name,
                        "state_prompt": state.state_prompt,
                        "transitions": state.transitions,
                        "tools": state.tools
                    }
                    for state in states
                ]

            llm_response = self.client.llm.create(
                model=model,
                general_prompt=system_prompt,
                begin_message=begin_message,
                states=states_config,
                starting_state=starting_state,
            )

            logger.info(f"Created Retell LLM: {llm_response.llm_id}")
            return llm_response.llm_id

        except Exception as e:
            logger.error(f"Failed to create Retell LLM: {e}")
            raise

    async def create_agent(
            self,
            voice_settings: VoiceSettings,
            agent_name: str,
            llm_id: str,
            webhook_url: Optional[str] = None
    ) -> RetellAgentResponse:
        """
        Create a Retell voice agent with Retell's LLM.

        Args:
            voice_settings: Voice configuration
            agent_name: Name for the agent
            llm_id: Retell LLM ID to use
            webhook_url: Webhook URL for call events

        Returns:
            Retell agent response
        """
        try:
            agent_response = self.client.agent.create(
                response_engine={
                    "type": "retell-llm",
                    "llm_id": llm_id
                },
                voice_id=voice_settings.voice_id,
                agent_name=agent_name,

                # Voice settings
                voice_speed=voice_settings.voice_speed,
                voice_temperature=voice_settings.voice_temperature,
                volume=voice_settings.volume,

                # Conversation settings for natural experience
                enable_backchannel=voice_settings.enable_backchannel,
                backchannel_frequency=voice_settings.backchannel_frequency,
                backchannel_words=voice_settings.backchannel_words,

                # Responsiveness
                responsiveness=voice_settings.responsiveness,
                interruption_sensitivity=voice_settings.interruption_sensitivity,

                # Ambient
                ambient_sound=voice_settings.ambient_sound,
                ambient_sound_volume=voice_settings.ambient_sound_volume,

                # Language
                language=voice_settings.language,

                # Speech recognition boost
                boosted_keywords=voice_settings.boosted_keywords,

                # Denoising mode (noisy environment handling)
                denoising_mode=DenoisingMode.NOISE_AND_BACKGROUND_SPEECH_CANCELLATION if voice_settings.enable_background_speech_cancellation else DenoisingMode.NOISE_CANCELLATION,

                # End call after silence
                end_call_after_silence_ms=int(voice_settings.end_call_after_silence_seconds * 1000),

                # Webhook
                webhook_url=webhook_url or settings.webhook_base_url,
            )

            logger.info(f"Created Retell agent: {agent_response.agent_id}")
            return agent_response

        except Exception as e:
            logger.error(f"Failed to create Retell agent: {e}")
            raise

    async def update_llm(
            self,
            llm_id: str,
            system_prompt: Optional[str] = None,
            begin_message: Optional[str] = None,
            states: Optional[List[AgentState]] = None,
            starting_state: Optional[str] = None,
            model: Optional[str] = None
    ) -> str:
        """
        Update an existing Retell LLM configuration.

        Args:
            llm_id: ID of the LLM to update
            system_prompt: New system prompt
            begin_message: New greeting message
            states: New states configuration
            starting_state: New starting state
            model: New model

        Returns:
            Updated LLM ID
        """
        try:
            update_params: Dict[str, Any] = {}

            if system_prompt:
                update_params["general_prompt"] = system_prompt

            if begin_message:
                update_params["begin_message"] = begin_message

            if model:
                update_params["model"] = model

            if states:
                update_params["states"] = [
                    {
                        "name": state.name,
                        "state_prompt": state.state_prompt,
                        "transitions": state.transitions,
                        "tools": state.tools
                    }
                    for state in states
                ]

            if starting_state:
                update_params["starting_state"] = starting_state

            llm_response = self.client.llm.update(
                llm_id=llm_id,
                **update_params
            )

            logger.info(f"Updated Retell LLM: {llm_id}")
            return llm_response.llm_id

        except Exception as e:
            logger.error(f"Failed to update Retell LLM: {e}")
            raise

    async def update_agent(
            self,
            agent_id: str,
            voice_settings: Optional[VoiceSettings] = None,
            agent_name: Optional[str] = None,
            webhook_url: Optional[str] = None
    ) -> RetellAgentResponse:
        """
        Update an existing Retell agent.

        Args:
            agent_id: ID of the agent to update
            voice_settings: New voice configuration
            agent_name: New agent name
            webhook_url: New webhook URL

        Returns:
            Updated agent response
        """
        try:
            update_params: Dict[str, Any] = {}

            if agent_name:
                update_params["agent_name"] = agent_name

            if webhook_url:
                update_params["webhook_url"] = webhook_url

            if voice_settings:
                update_params.update({
                    "voice_id": voice_settings.voice_id,
                    "voice_speed": voice_settings.voice_speed,
                    "voice_temperature": voice_settings.voice_temperature,
                    "volume": voice_settings.volume,
                    "enable_backchannel": voice_settings.enable_backchannel,
                    "backchannel_frequency": voice_settings.backchannel_frequency,
                    "backchannel_words": voice_settings.backchannel_words,
                    "responsiveness": voice_settings.responsiveness,
                    "interruption_sensitivity": voice_settings.interruption_sensitivity,
                    "ambient_sound": voice_settings.ambient_sound,
                    "ambient_sound_volume": voice_settings.ambient_sound_volume,
                    "language": voice_settings.language,
                    "boosted_keywords": voice_settings.boosted_keywords,
                    "denoising_mode": "noise-and-background-speech-cancellation" if voice_settings.enable_background_speech_cancellation else None,
                    "end_call_after_silence_ms": int(voice_settings.end_call_after_silence_seconds * 1000),
                })

            agent_response = self.client.agent.update(
                agent_id=agent_id,
                **update_params
            )

            logger.info(f"Updated Retell agent: {agent_id}")
            return agent_response

        except Exception as e:
            logger.error(f"Failed to update Retell agent: {e}")
            raise

    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete a Retell agent.

        Args:
            agent_id: ID of the agent to delete

        Returns:
            True if deletion was successful
        """
        try:
            self.client.agent.delete(agent_id=agent_id)
            logger.info(f"Deleted Retell agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Retell agent: {e}")
            raise

    async def delete_llm(self, llm_id: str) -> bool:
        """
        Delete a Retell LLM configuration.

        Args:
            llm_id: ID of the LLM to delete

        Returns:
            True if deletion was successful
        """
        try:
            self.client.llm.delete(llm_id=llm_id)
            logger.info(f"Deleted Retell LLM: {llm_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Retell LLM: {e}")
            raise

    async def create_web_call(
            self,
            agent_id: str,
            metadata: Optional[Dict[str, Any]] = None,
            dynamic_variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Create a web call for browser-based interaction.

        Args:
            agent_id: ID of the agent to use
            metadata: Optional call metadata
            dynamic_variables: Variables to inject into prompts

        Returns:
            Dict with call_id and access_token
        """
        try:
            call_response = self.client.call.create_web_call(
                agent_id=agent_id,
                metadata=metadata,
                retell_llm_dynamic_variables=dynamic_variables,
            )

            logger.info(f"Created web call: {call_response.call_id}")
            return {
                "call_id": call_response.call_id,
                "access_token": call_response.access_token
            }

        except Exception as e:
            logger.error(f"Failed to create web call: {e}")
            raise

    async def get_call(self, call_id: str) -> Dict[str, Any]:
        """
        Get call details from Retell.

        Args:
            call_id: ID of the call

        Returns:
            Call details including transcript
        """
        try:
            call = self.client.call.retrieve(call_id=call_id)
            return {
                "call_id": call.call_id,
                "agent_id": call.agent_id,
                "call_status": call.call_status,
                "start_timestamp": call.start_timestamp,
                "end_timestamp": call.end_timestamp,
                "transcript": call.transcript,
                "recording_url": getattr(call, "recording_url", None),
                "disconnection_reason": getattr(call, "disconnection_reason", None),
            }
        except Exception as e:
            logger.error(f"Failed to get call {call_id}: {e}")
            raise


# Singleton instance
_retell_service: Optional[RetellService] = None


def get_retell_service() -> RetellService:
    """Get or create RetellService singleton."""
    global _retell_service
    if _retell_service is None:
        _retell_service = RetellService()
    return _retell_service