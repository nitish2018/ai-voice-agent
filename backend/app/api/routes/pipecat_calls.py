"""
Pipecat-specific call API routes.

These routes handle Pipecat voice pipeline operations including
session management and WebSocket audio streaming.
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.schemas.pipeline import (
    PipecatCallRequest,
    PipecatCallResponse,
    PipecatSessionMetrics,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipecat", tags=["pipecat"])


# Check if Pipecat is available
try:
    from app.services.pipecat import get_pipecat_service
    PIPECAT_AVAILABLE = True
except ImportError:
    PIPECAT_AVAILABLE = False
    logger.warning("Pipecat service not available")


@router.get("/sessions")
async def list_active_sessions():
    """
    List all active Pipecat sessions.
    
    Returns:
        List of active session IDs
        
    Raises:
        HTTPException: If Pipecat not available
    """
    if not PIPECAT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Pipecat service not available"
        )
    
    try:
        pipecat_service = get_pipecat_service()
        sessions = pipecat_service.get_active_sessions()
        return {"active_sessions": sessions}
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/end")
async def end_session(session_id: str):
    """
    End an active Pipecat session.
    
    Args:
        session_id: Session ID to end
        
    Returns:
        Session metrics, transcript, and cost breakdown
        
    Raises:
        HTTPException: If Pipecat not available or session not found
    """
    if not PIPECAT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Pipecat service not available"
        )
    
    try:
        pipecat_service = get_pipecat_service()
        result = await pipecat_service.end_call(session_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or could not be ended"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for Pipecat audio streaming.
    
    This endpoint is used for WebSocket-based transport (as opposed to WebRTC/Daily.co).
    
    Args:
        websocket: WebSocket connection
        session_id: Pipecat session ID
    """
    if not PIPECAT_AVAILABLE:
        await websocket.close(code=1003, reason="Pipecat service not available")
        return
    
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for session: {session_id}")
    
    try:
        # Get Pipecat service
        pipecat_service = get_pipecat_service()
        
        # TODO: Implement WebSocket audio streaming
        # This would involve:
        # 1. Getting the session from pipecat_service
        # 2. Setting up bidirectional audio streaming
        # 3. Handling binary audio data
        
        # For now, send a message that WebSocket transport is not yet implemented
        await websocket.send_json({
            "error": "WebSocket transport not yet implemented. Please use Daily.co WebRTC transport."
        })
        
        # Keep connection open and wait for messages
        while True:
            data = await websocket.receive()
            logger.debug(f"Received WebSocket data: {data}")
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass
