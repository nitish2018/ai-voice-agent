"""
Call API routes for triggering and managing voice calls.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas.call import (
    CallTriggerRequest,
    CallResponse,
    CallListResponse,
    CallStatus,
    CallResultsResponse,
)
from app.schemas.agent import VoiceSystem
from app.schemas.pipeline import PipecatCallRequest
from app.services.call_service import get_call_service
from app.services.agent_service import get_agent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calls", tags=["calls"])

# Check if Pipecat is available
try:
    from app.services.pipecat import get_pipecat_service
    PIPECAT_AVAILABLE = True
except ImportError:
    PIPECAT_AVAILABLE = False
    logger.warning("Pipecat service not available")


@router.post("/trigger", response_model=CallResponse, status_code=201)
async def trigger_call(request: CallTriggerRequest):
    """
    Trigger a new outbound call.
    
    This initiates a web call from the configured voice agent.
    The call is intelligently routed to either Retell or Pipecat
    based on the agent's voice_system configuration.
    
    Args:
        request: Call trigger request containing:
            - agent_id: ID of the agent to use
            - driver_name: Name of the driver
            - load_number: Load/shipment number for context
            - origin: Optional origin location
            - destination: Optional destination location
            - expected_eta: Optional expected arrival time
    
    Returns:
        Call response with call ID and status
    """
    try:
        agent_service = get_agent_service()
        agent = await agent_service.get_agent(request.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")

        call_service = get_call_service()

        if agent.voice_system == VoiceSystem.PIPECAT.value:
            logger.info(f"Routing call to Pipecat service for agent {request.agent_id}")
            if not PIPECAT_AVAILABLE:
                raise HTTPException(
                    status_code=503,
                    detail="Pipecat service is not available. Install pipecat dependencies: "
                           "pip install 'pipecat-ai[daily,deepgram,openai,anthropic,silero]'"
                )
            if not agent.pipeline_config:
                raise HTTPException(
                    status_code=400,
                    detail=f"Agent {request.agent_id} has no pipeline configuration"
                )

            pipecat_service = get_pipecat_service()
            pipecat_request = PipecatCallRequest(
                agent_id=request.agent_id,
                driver_name=request.driver_name,
                load_number=request.load_number,
                origin=request.origin,
                destination=request.destination,
                expected_eta=request.expected_eta,
                additional_context=request.additional_context
            )

            from app.schemas.pipeline import PipelineConfig
            logger.info(f"Agent pipeline_config from DB: {agent.pipeline_config}")
            pipeline_config = PipelineConfig(**agent.pipeline_config)
            
            # Detailed TTS logging
            if pipeline_config.tts_config.service == 'cartesia':
                logger.info(f"TTS Service: Cartesia")
                logger.info(f"Voice ID from config: {pipeline_config.tts_config.cartesia.voice_id}")
                logger.info(f"Model ID: {pipeline_config.tts_config.cartesia.model_id}")
                logger.info(f"Speed: {pipeline_config.tts_config.cartesia.speed}")
            else:
                logger.info(f"TTS Service: {pipeline_config.tts_config.service}")

            pipecat_response = await pipecat_service.start_call(
                request=pipecat_request,
                agent_config=pipeline_config,
                system_prompt=agent.system_prompt
            )

            # Create call record in database
            call_id = str(uuid.uuid4())
            now = datetime.utcnow()

            call_data = {
                "id": call_id,
                "agent_id": request.agent_id,
                "driver_name": request.driver_name,
                "load_number": request.load_number,
                "origin": request.origin,
                "destination": request.destination,
                "status": CallStatus.PENDING.value,
                "retell_call_id": pipecat_response.session_id,  # Store session_id here
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }

            # Store in database
            from app.db.database import get_supabase_client, Tables
            db = get_supabase_client()
            result = db.table(Tables.CALLS).insert(call_data).execute()

            # Return response
            call_record = result.data[0].copy()
            call_record["status"] = CallStatus(call_record["status"])
            call_record["created_at"] = datetime.fromisoformat(call_record["created_at"].replace("Z", "+00:00"))
            call_record["updated_at"] = datetime.fromisoformat(call_record["updated_at"].replace("Z", "+00:00"))
            response = CallResponse(**call_record)

            # Add URL for connecting (Daily or WebSocket)
            if pipecat_response.daily_room_url:
                response.access_token = pipecat_response.daily_room_url
            elif pipecat_response.websocket_url:
                response.access_token = pipecat_response.websocket_url

            logger.info(f"Triggered Pipecat call: {call_id} with session {pipecat_response.session_id}")

            return response

        elif agent.voice_system == VoiceSystem.RETELL.value:
            logger.info(f"Routing call to Retell service for agent {request.agent_id}")
            if not agent.retell_agent_id:
                raise ValueError(f"Agent {request.agent_id} not configured with Retell")
            return await call_service.trigger_call(request)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported voice system: {agent.voice_system}"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger call: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=CallListResponse)
async def list_calls(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    status: Optional[CallStatus] = Query(None, description="Filter by call status")
):
    """
    List all calls with optional filters.
    
    Returns a paginated list of calls with their status and results.
    """
    try:
        call_service = get_call_service()
        return await call_service.list_calls(
            skip=skip,
            limit=limit,
            agent_id=agent_id,
            status=status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(call_id: str):
    """
    Get a specific call by ID.
    
    Returns the full call details including transcript and structured results.
    """
    try:
        call_service = get_call_service()
        call = await call_service.get_call(call_id)
        
        if not call:
            raise HTTPException(status_code=404, detail=f"Call {call_id} not found")
        
        return call
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{call_id}/results", response_model=CallResultsResponse)
async def get_call_results(call_id: str):
    """
    Get structured results for a specific call.
    
    Returns the extracted key-value pairs from the call transcript.
    """
    try:
        call_service = get_call_service()
        
        # First verify call exists
        call = await call_service.get_call(call_id)
        if not call:
            raise HTTPException(status_code=404, detail=f"Call {call_id} not found")
        
        # Get results
        results = await call_service.get_call_results(call_id)
        
        if not results:
            raise HTTPException(
                status_code=404, 
                detail=f"Results not yet available for call {call_id}. Call may still be in progress."
            )
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{call_id}/reprocess", response_model=CallResultsResponse)
async def reprocess_call(call_id: str):
    """
    Reprocess a call's transcript to extract structured data.
    
    Useful if the initial extraction failed or needs to be updated.
    """
    try:
        call_service = get_call_service()
        
        # Get call
        call = await call_service.get_call(call_id)
        if not call:
            raise HTTPException(status_code=404, detail=f"Call {call_id} not found")
        
        if not call.transcript:
            raise HTTPException(
                status_code=400,
                detail=f"Call {call_id} has no transcript to process"
            )
        
        # Reprocess
        results = await call_service.process_call_completion(
            call_id=call_id,
            transcript=call.transcript,
            recording_url=call.recording_url,
            duration_seconds=call.duration_seconds
        )
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
