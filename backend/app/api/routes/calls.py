"""
Call API routes for triggering and managing voice calls.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas.call import (
    CallTriggerRequest,
    CallResponse,
    CallListResponse,
    CallStatus,
    CallResultsResponse,
)
from app.services.call_service import get_call_service

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/trigger", response_model=CallResponse, status_code=201)
async def trigger_call(request: CallTriggerRequest):
    """
    Trigger a new outbound call.
    
    This initiates a web call from the configured voice agent.
    The driver's name, phone number, and load number provide context
    for the call.
    
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
        call_service = get_call_service()
        return await call_service.trigger_call(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
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
