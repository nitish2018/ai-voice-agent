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


@router.websocket("/websocket/{session_id}")
async def websocket_audio_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for Pipecat audio streaming.
    
    This endpoint handles bidirectional audio streaming for Pipecat sessions using WebSocket transport.
    The client should send raw audio data (16kHz, 16-bit PCM, mono) and will receive the same format back.
    
    Args:
        websocket: WebSocket connection
        session_id: Pipecat session ID
    """
    if not PIPECAT_AVAILABLE:
        await websocket.close(code=1003, reason="Pipecat service not available")
        return
    
    logger.info(f"[WEBSOCKET] Connection request for session: {session_id}")
    
    try:
        # Get Pipecat service and session
        pipecat_service = get_pipecat_service()
        session_manager = pipecat_service.session_manager
        pipeline_orchestrator = pipecat_service.pipeline_orchestrator
        
        # Get session
        session = session_manager.get_session(session_id)
        if not session:
            logger.error(f"[WEBSOCKET] Session {session_id} not found")
            await websocket.close(code=1008, reason="Session not found")
            return
        
        logger.info(f"[WEBSOCKET] Starting pipeline for session: {session_id}")
        
        # Run WebSocket pipeline
        await pipeline_orchestrator.run_websocket_pipeline(session, websocket)
        
        logger.info(f"[WEBSOCKET] Pipeline completed for session: {session_id}")
        
    except WebSocketDisconnect:
        logger.info(f"[WEBSOCKET] Client disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"[WEBSOCKET] Error for session {session_id}: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception as close_error:
            logger.error(f"[WEBSOCKET] Error closing WebSocket: {close_error}")
