"""
Agent Service - Manages agent configurations in database and Retell AI.

Uses Retell's built-in LLM for conversation handling.
"""
import logging
from typing import Optional, List
from datetime import datetime
import uuid

from app.db.database import get_supabase_client, Tables
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentListResponse,
    VoiceSettings,
    AgentState,
    VoiceSystem,
)
from app.services.retell_service import get_retell_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing voice agents."""

    def __init__(self):
        """Initialize agent service."""
        self.db = get_supabase_client()
        self.retell = get_retell_service()

    async def create_agent(self, agent_data: AgentCreate) -> AgentResponse:
        """
        Create a new agent in both database and Retell AI.

        Flow:
        1. Create LLM in Retell with system_prompt
        2. Create Agent in Retell with LLM ID
        3. Save to database

        Args:
            agent_data: Agent creation data

        Returns:
            Created agent response
        """
        try:
            # Generate ID
            agent_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            # Initialize Retell IDs as None
            llm_id = None
            retell_agent_id = None

            # Only create Retell resources if using Retell voice system
            if agent_data.voice_system == VoiceSystem.RETELL:
                # Step 1: Create LLM in Retell
                llm_id = await self.retell.create_llm(
                    system_prompt=agent_data.system_prompt,
                    begin_message=agent_data.begin_message,
                    states=agent_data.states if agent_data.states else None,
                    starting_state=agent_data.starting_state,
                )

                # Step 2: Create Agent in Retell with LLM ID
                retell_agent = await self.retell.create_agent(
                    voice_settings=agent_data.voice_settings,
                    agent_name=agent_data.name,
                    llm_id=llm_id,
                )
                retell_agent_id = retell_agent.agent_id

            # Step 3: Prepare database record
            db_record = {
                "id": agent_id,
                "name": agent_data.name,
                "description": agent_data.description,
                "agent_type": agent_data.agent_type.value,
                "voice_system": agent_data.voice_system.value,
                "system_prompt": agent_data.system_prompt,
                "begin_message": agent_data.begin_message,
                "voice_settings": agent_data.voice_settings.model_dump(),
                "pipeline_config": agent_data.pipeline_config if agent_data.pipeline_config else None,
                "states": [s.model_dump() for s in agent_data.states] if agent_data.states else [],
                "starting_state": agent_data.starting_state,
                "emergency_triggers": agent_data.emergency_triggers,
                "is_active": agent_data.is_active,
                "retell_agent_id": retell_agent_id,
                "retell_llm_id": llm_id,
                "created_at": now,
                "updated_at": now,
            }

            # Insert into database
            result = self.db.table(Tables.AGENTS).insert(db_record).execute()

            logger.info(f"Created agent: {agent_id} with LLM: {llm_id}")

            return self._map_to_response(result.data[0])

        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise

    async def get_agent(self, agent_id: str) -> Optional[AgentResponse]:
        """
        Get an agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent response or None
        """
        try:
            result = self.db.table(Tables.AGENTS).select("*").eq("id", agent_id).execute()

            if not result.data:
                return None

            return self._map_to_response(result.data[0])

        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            raise

    async def list_agents(
            self,
            skip: int = 0,
            limit: int = 50,
            active_only: bool = False
    ) -> AgentListResponse:
        """
        List all agents with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            active_only: Only return active agents

        Returns:
            List of agents with total count
        """
        try:
            query = self.db.table(Tables.AGENTS).select("*", count="exact")

            if active_only:
                query = query.eq("is_active", True)

            query = query.order("created_at", desc=True)
            query = query.range(skip, skip + limit - 1)

            result = query.execute()

            agents = [self._map_to_response(row) for row in result.data]

            return AgentListResponse(
                agents=agents,
                total=result.count or len(agents)
            )

        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            raise

    async def update_agent(
            self,
            agent_id: str,
            agent_data: AgentUpdate
    ) -> Optional[AgentResponse]:
        """
        Update an existing agent.

        Args:
            agent_id: Agent ID to update
            agent_data: Update data

        Returns:
            Updated agent response or None
        """
        try:
            # Get existing agent
            existing = await self.get_agent(agent_id)
            if not existing:
                return None

            # Prepare update data
            update_dict = agent_data.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow().isoformat()

            # Handle nested objects
            if "voice_settings" in update_dict and update_dict["voice_settings"]:
                update_dict["voice_settings"] = update_dict["voice_settings"].model_dump() if hasattr(update_dict["voice_settings"], 'model_dump') else update_dict["voice_settings"]

            if "states" in update_dict and update_dict["states"]:
                update_dict["states"] = [s.model_dump() if hasattr(s, 'model_dump') else s for s in update_dict["states"]]

            if "agent_type" in update_dict and update_dict["agent_type"]:
                update_dict["agent_type"] = update_dict["agent_type"].value if hasattr(update_dict["agent_type"], 'value') else update_dict["agent_type"]
            
            if "voice_system" in update_dict and update_dict["voice_system"]:
                update_dict["voice_system"] = update_dict["voice_system"].value if hasattr(update_dict["voice_system"], 'value') else update_dict["voice_system"]

            # Only update Retell if using Retell voice system
            if existing.voice_system == VoiceSystem.RETELL:
                # Update LLM in Retell if prompt changed
                if existing.retell_llm_id and ("system_prompt" in update_dict or "begin_message" in update_dict):
                    states = None
                    if "states" in update_dict:
                        states = [AgentState(**s) if isinstance(s, dict) else s for s in update_dict["states"]]

                    await self.retell.update_llm(
                        llm_id=existing.retell_llm_id,
                        system_prompt=update_dict.get("system_prompt"),
                        begin_message=update_dict.get("begin_message"),
                        states=states,
                        starting_state=update_dict.get("starting_state"),
                    )

                # Update Agent in Retell if voice settings changed
                if existing.retell_agent_id and "voice_settings" in update_dict:
                    voice_settings = VoiceSettings(**update_dict["voice_settings"])
                    await self.retell.update_agent(
                        existing.retell_agent_id,
                        voice_settings=voice_settings,
                        agent_name=update_dict.get("name", existing.name)
                    )

            # Update database
            result = self.db.table(Tables.AGENTS).update(update_dict).eq("id", agent_id).execute()

            if not result.data:
                return None

            logger.info(f"Updated agent: {agent_id}")

            return self._map_to_response(result.data[0])

        except Exception as e:
            logger.error(f"Failed to update agent {agent_id}: {e}")
            raise

    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent.

        Args:
            agent_id: Agent ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            # Get existing agent
            existing = await self.get_agent(agent_id)
            if not existing:
                return False

            # Delete from Retell (Agent first, then LLM)
            if existing.retell_agent_id:
                try:
                    await self.retell.delete_agent(existing.retell_agent_id)
                except Exception as e:
                    logger.warning(f"Failed to delete Retell agent: {e}")

            if existing.retell_llm_id:
                try:
                    await self.retell.delete_llm(existing.retell_llm_id)
                except Exception as e:
                    logger.warning(f"Failed to delete Retell LLM: {e}")

            # Delete from database
            self.db.table(Tables.AGENTS).delete().eq("id", agent_id).execute()

            logger.info(f"Deleted agent: {agent_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            raise

    def _map_to_response(self, row: dict) -> AgentResponse:
        """Map database row to response schema."""
        # Parse voice_system, defaulting to RETELL if not specified
        voice_system_str = row.get("voice_system", "retell")
        try:
            voice_system = VoiceSystem(voice_system_str)
        except ValueError:
            logger.warning(f"Invalid voice_system '{voice_system_str}', defaulting to RETELL")
            voice_system = VoiceSystem.RETELL
        
        return AgentResponse(
            id=row["id"],
            name=row["name"],
            description=row.get("description"),
            agent_type=row["agent_type"],
            voice_system=voice_system,
            system_prompt=row["system_prompt"],
            begin_message=row.get("begin_message"),
            voice_settings=VoiceSettings(**row.get("voice_settings", {})),
            pipeline_config=row.get("pipeline_config"),
            states=row.get("states", []),
            starting_state=row.get("starting_state"),
            emergency_triggers=row.get("emergency_triggers", []),
            is_active=row.get("is_active", True),
            retell_agent_id=row.get("retell_agent_id"),
            retell_llm_id=row.get("retell_llm_id"),
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")),
        )


# Singleton instance
agent_service = AgentService()


def get_agent_service() -> AgentService:
    """Get agent service instance."""
    return agent_service