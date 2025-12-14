"""
Agent API routes for managing voice agent configurations.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentListResponse,
)
from app.services.agent_service import get_agent_service

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(agent_data: AgentCreate):
    """
    Create a new voice agent.
    
    This creates both a local database record and configures the agent in Retell AI
    with the specified voice settings and prompts.
    """
    try:
        agent_service = get_agent_service()
        return await agent_service.create_agent(agent_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    active_only: bool = Query(False, description="Only return active agents")
):
    """
    List all configured voice agents.
    
    Returns a paginated list of agents with their configurations.
    """
    try:
        agent_service = get_agent_service()
        return await agent_service.list_agents(skip=skip, limit=limit, active_only=active_only)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """
    Get a specific agent by ID.
    
    Returns the full agent configuration including voice settings and prompts.
    """
    try:
        agent_service = get_agent_service()
        agent = await agent_service.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, agent_data: AgentUpdate):
    """
    Update an existing agent.
    
    Updates both the local configuration and syncs changes to Retell AI.
    """
    try:
        agent_service = get_agent_service()
        agent = await agent_service.update_agent(agent_id, agent_data)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str):
    """
    Delete an agent.
    
    Removes the agent from both the local database and Retell AI.
    """
    try:
        agent_service = get_agent_service()
        deleted = await agent_service.delete_agent(agent_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
