"""
Retell AI Webhook Handler.

Receives and processes webhook events from Retell AI for call lifecycle management.
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException
import json

from app.core.security import verify_webhook_request
from app.schemas.webhook import (
    RetellWebhookPayload,
    WebhookEventType,
    WebhookResponse,
    DisconnectionReason,
)
from app.schemas.call import CallStatus
from app.services.call_service import get_call_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/retell", response_model=WebhookResponse)
async def handle_retell_webhook(
    request: Request,
    body: bytes = Depends(verify_webhook_request)
):
    """
    Handle incoming webhooks from Retell AI.
    
    Processes the following events:
    - call_started: Call has been initiated
    - call_ended: Call has completed with transcript
    - call_analyzed: Post-call analysis is ready
    """
    try:
        # Parse the webhook payload
        payload_dict = json.loads(body.decode('utf-8'))
        payload = RetellWebhookPayload(**payload_dict)
        
        logger.info(f"Received Retell webhook: {payload.event} for call {payload.call.call_id}")
        
        call_service = get_call_service()
        
        # Route to appropriate handler
        if payload.event == WebhookEventType.CALL_STARTED:
            await handle_call_started(payload, call_service)
        
        elif payload.event == WebhookEventType.CALL_ENDED:
            await handle_call_ended(payload, call_service)
        
        elif payload.event == WebhookEventType.CALL_ANALYZED:
            await handle_call_analyzed(payload, call_service)
        
        return WebhookResponse(status="ok", message=f"Processed {payload.event}")
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Return 200 to prevent Retell from retrying
        return WebhookResponse(status="error", message=str(e))


async def handle_call_started(payload: RetellWebhookPayload, call_service):
    """
    Handle call_started event.
    
    Updates the call status to IN_PROGRESS.
    """
    try:
        call = await call_service.get_call_by_retell_id(payload.call.call_id)
        
        if call:
            await call_service.update_call_status(
                call_id=call.id,
                status=CallStatus.IN_PROGRESS
            )
            logger.info(f"Call {call.id} started")
        else:
            logger.warning(f"Received call_started for unknown call: {payload.call.call_id}")
            
    except Exception as e:
        logger.error(f"Error handling call_started: {e}")
        raise


async def handle_call_ended(payload: RetellWebhookPayload, call_service):
    """
    Handle call_ended event.
    
    Updates call status based on disconnection reason and processes transcript.
    """
    try:
        call = await call_service.get_call_by_retell_id(payload.call.call_id)
        
        if not call:
            logger.warning(f"Received call_ended for unknown call: {payload.call.call_id}")
            return
        
        # Determine call status based on disconnection reason
        disconnection = payload.call.disconnection_reason
        if disconnection:
            try:
                reason = DisconnectionReason(disconnection)
            except ValueError:
                reason = DisconnectionReason.UNKNOWN
            
            # Map disconnection reasons to call status
            status_map = {
                DisconnectionReason.USER_HANGUP: CallStatus.COMPLETED,
                DisconnectionReason.AGENT_HANGUP: CallStatus.COMPLETED,
                DisconnectionReason.CALL_TRANSFER: CallStatus.COMPLETED,
                DisconnectionReason.VOICEMAIL_REACHED: CallStatus.VOICEMAIL,
                DisconnectionReason.DIAL_NO_ANSWER: CallStatus.NO_ANSWER,
                DisconnectionReason.DIAL_BUSY: CallStatus.BUSY,
                DisconnectionReason.DIAL_FAILED: CallStatus.FAILED,
                DisconnectionReason.INACTIVITY: CallStatus.COMPLETED,
                DisconnectionReason.MAX_DURATION: CallStatus.COMPLETED,
            }
            status = status_map.get(reason, CallStatus.COMPLETED)
        else:
            status = CallStatus.COMPLETED
        
        # Calculate duration
        duration_seconds = None
        if payload.call.start_timestamp and payload.call.end_timestamp:
            duration_seconds = int((payload.call.end_timestamp - payload.call.start_timestamp) / 1000)
        
        # Get transcript
        transcript = payload.call.transcript or ""
        
        # If we have a transcript and the call completed successfully, process it
        if transcript and status == CallStatus.COMPLETED:
            try:
                await call_service.process_call_completion(
                    call_id=call.id,
                    transcript=transcript,
                    recording_url=payload.call.recording_url,
                    duration_seconds=duration_seconds
                )
                logger.info(f"Call {call.id} ended and processed successfully")
            except Exception as e:
                logger.error(f"Error processing call transcript: {e}")
                # Still update the call status even if processing fails
                await call_service.update_call_status(
                    call_id=call.id,
                    status=status,
                    transcript=transcript,
                    recording_url=payload.call.recording_url,
                    duration_seconds=duration_seconds,
                    ended_at=datetime.utcnow()
                )
        else:
            # Update call status without processing
            await call_service.update_call_status(
                call_id=call.id,
                status=status,
                transcript=transcript,
                recording_url=payload.call.recording_url,
                duration_seconds=duration_seconds,
                ended_at=datetime.utcnow()
            )
            logger.info(f"Call {call.id} ended with status: {status.value}")
            
    except Exception as e:
        logger.error(f"Error handling call_ended: {e}")
        raise


async def handle_call_analyzed(payload: RetellWebhookPayload, call_service):
    """
    Handle call_analyzed event.
    
    This event is sent after Retell's post-call analysis is complete.
    Can be used to update results with additional analysis.
    """
    try:
        call = await call_service.get_call_by_retell_id(payload.call.call_id)
        
        if not call:
            logger.warning(f"Received call_analyzed for unknown call: {payload.call.call_id}")
            return
        
        # Log analysis data (can be extended to store additional insights)
        if payload.call.call_analysis:
            logger.info(f"Call {call.id} analysis received: {payload.call.call_analysis}")
            
    except Exception as e:
        logger.error(f"Error handling call_analyzed: {e}")
        raise


# Health check endpoint for webhook verification
@router.get("/retell/health")
async def webhook_health():
    """Health check endpoint for webhook configuration."""
    return {"status": "healthy", "service": "retell-webhook"}
