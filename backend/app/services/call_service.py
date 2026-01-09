"""
Call Service - Manages call operations and records.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from app.db.database import get_supabase_client, Tables
from app.schemas.call import (
    CallTriggerRequest,
    CallCreate,
    CallResponse,
    CallListResponse,
    CallStatus,
    CallResultsCreate,
    CallResultsResponse,
)
from app.services.retell_service import get_retell_service
from app.services.agent_service import get_agent_service
from app.services.pipecat.transcript.transcript_processor import get_transcript_processor

logger = logging.getLogger(__name__)


class CallService:
    """Service for managing voice calls."""

    def __init__(self):
        """Initialize call service."""
        self.db = get_supabase_client()
        self.retell = get_retell_service()
        self.agent_service = get_agent_service()
        self.transcript_processor = get_transcript_processor()

    async def trigger_call(self, request: CallTriggerRequest) -> CallResponse:
        """
        Trigger a new web call.

        Args:
            request: Call trigger request with driver info

        Returns:
            Call response with call details and access token
        """
        try:
            # Get agent
            agent = await self.agent_service.get_agent(request.agent_id)
            if not agent:
                raise ValueError(f"Agent {request.agent_id} not found")

            if not agent.retell_agent_id:
                raise ValueError(f"Agent {request.agent_id} not configured with Retell")

            # Generate call ID
            call_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()

            # Prepare dynamic variables for prompt injection
            dynamic_variables = {
                "driver_name": request.driver_name,
                "load_number": request.load_number,
            }
            if request.origin:
                dynamic_variables["origin"] = request.origin
            if request.destination:
                dynamic_variables["destination"] = request.destination
            if request.expected_eta:
                dynamic_variables["expected_eta"] = request.expected_eta

            # Prepare metadata (includes agent_id for Custom LLM WebSocket)
            metadata = {
                "internal_call_id": call_id,
                "agent_id": request.agent_id,  # Needed by WebSocket handler to load prompts
                "driver_name": request.driver_name,
                "load_number": request.load_number,
                "origin": request.origin,
                "destination": request.destination,
                **(request.additional_context or {})
            }

            # Create web call in Retell (returns access_token for frontend)
            retell_call = await self.retell.create_web_call(
                agent_id=agent.retell_agent_id,
                metadata=metadata,
                dynamic_variables=dynamic_variables,
            )

            # Create database record
            db_record = {
                "id": call_id,
                "agent_id": request.agent_id,
                "retell_call_id": retell_call["call_id"],
                "access_token": retell_call["access_token"],
                "driver_name": request.driver_name,
                "load_number": request.load_number,
                "origin": request.origin,
                "destination": request.destination,
                "status": CallStatus.PENDING.value,
                "created_at": now,
                "updated_at": now,
            }

            result = self.db.table(Tables.CALLS).insert(db_record).execute()

            logger.info(f"Triggered web call: {call_id} -> Retell: {retell_call['call_id']}")

            return self._map_to_response(result.data[0])

        except Exception as e:
            logger.error(f"Failed to trigger call: {e}")
            raise

    async def get_call(self, call_id: str) -> Optional[CallResponse]:
        """
        Get a call by ID with results.

        Args:
            call_id: Internal call ID

        Returns:
            Call response with results or None
        """
        try:
            result = self.db.table(Tables.CALLS).select("*").eq("id", call_id).execute()

            if not result.data:
                return None

            call_data = result.data[0]

            # Get results if available
            results = await self.get_call_results(call_id)

            response = self._map_to_response(call_data)
            response.results = results

            return response

        except Exception as e:
            logger.error(f"Failed to get call {call_id}: {e}")
            raise

    async def get_call_by_retell_id(self, retell_call_id: str) -> Optional[CallResponse]:
        """
        Get a call by Retell call ID.

        Args:
            retell_call_id: Retell's call ID

        Returns:
            Call response or None
        """
        try:
            result = self.db.table(Tables.CALLS).select("*").eq("retell_call_id", retell_call_id).execute()

            if not result.data:
                return None

            return self._map_to_response(result.data[0])

        except Exception as e:
            logger.error(f"Failed to get call by Retell ID {retell_call_id}: {e}")
            raise

    async def list_calls(
            self,
            skip: int = 0,
            limit: int = 50,
            agent_id: Optional[str] = None,
            status: Optional[CallStatus] = None
    ) -> CallListResponse:
        """
        List calls with pagination and filters.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            agent_id: Filter by agent ID
            status: Filter by call status

        Returns:
            List of calls with total count
        """
        try:
            query = self.db.table(Tables.CALLS).select("*", count="exact")

            if agent_id:
                query = query.eq("agent_id", agent_id)

            if status:
                query = query.eq("status", status.value)

            query = query.order("created_at", desc=True)
            query = query.range(skip, skip + limit - 1)

            result = query.execute()

            calls = []
            for row in result.data:
                call_response = self._map_to_response(row)
                # Optionally fetch results for each call
                call_response.results = await self.get_call_results(row["id"])
                calls.append(call_response)

            return CallListResponse(
                calls=calls,
                total=result.count or len(calls)
            )

        except Exception as e:
            logger.error(f"Failed to list calls: {e}")
            raise

    async def update_call_status(
            self,
            call_id: str,
            status: CallStatus,
            transcript: Optional[str] = None,
            recording_url: Optional[str] = None,
            duration_seconds: Optional[int] = None,
            ended_at: Optional[datetime] = None
    ) -> Optional[CallResponse]:
        """
        Update call status and metadata.

        Args:
            call_id: Internal call ID
            status: New status
            transcript: Call transcript
            recording_url: Recording URL
            duration_seconds: Call duration
            ended_at: Call end time

        Returns:
            Updated call response
        """
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat(),
            }

            if transcript:
                update_data["transcript"] = transcript
            if recording_url:
                update_data["recording_url"] = recording_url
            if duration_seconds is not None:
                update_data["duration_seconds"] = duration_seconds
            if ended_at:
                update_data["ended_at"] = ended_at.isoformat()

            result = self.db.table(Tables.CALLS).update(update_data).eq("id", call_id).execute()

            if not result.data:
                return None

            logger.info(f"Updated call {call_id} status to {status.value}")

            return self._map_to_response(result.data[0])

        except Exception as e:
            logger.error(f"Failed to update call {call_id}: {e}")
            raise

    async def process_call_completion(
            self,
            call_id: str,
            transcript: str,
            recording_url: Optional[str] = None,
            duration_seconds: Optional[int] = None
    ) -> CallResultsResponse:
        """
        Process a completed call - extract structured data from transcript.

        Args:
            call_id: Internal call ID
            transcript: Full call transcript
            recording_url: Recording URL
            duration_seconds: Call duration

        Returns:
            Extracted call results
        """
        try:
            # Get call details
            call = await self.get_call(call_id)
            if not call:
                raise ValueError(f"Call {call_id} not found")

            # Update call with transcript
            await self.update_call_status(
                call_id,
                status=CallStatus.COMPLETED,
                transcript=transcript,
                recording_url=recording_url,
                duration_seconds=duration_seconds,
                ended_at=datetime.utcnow()
            )

            # Build context for extraction
            call_context = {
                "driver_name": call.driver_name,
                "load_number": call.load_number,
                "origin": call.origin,
                "destination": call.destination,
            }

            # Process transcript to extract structured data
            results = await self.transcript_processor.process_call_transcript(
                call_id=call_id,
                transcript=transcript,
                call_context=call_context
            )

            # Save results to database
            saved_results = await self.save_call_results(results)

            logger.info(f"Processed call {call_id} completion with outcome: {results.call_outcome}")

            return saved_results

        except Exception as e:
            logger.error(f"Failed to process call completion {call_id}: {e}")
            raise

    async def save_call_results(self, results: CallResultsCreate) -> CallResultsResponse:
        """
        Save call results to database.

        Args:
            results: Call results to save

        Returns:
            Saved results response
        """
        try:
            result_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()

            db_record = {
                "id": result_id,
                "call_id": results.call_id,
                "call_outcome": results.call_outcome.value,
                "is_emergency": results.is_emergency,
                "driver_status": results.driver_status.value if results.driver_status else None,
                "current_location": results.current_location,
                "eta": results.eta,
                "delay_reason": results.delay_reason,
                "unloading_status": results.unloading_status,
                "pod_reminder_acknowledged": results.pod_reminder_acknowledged,
                "emergency_type": results.emergency_type.value if results.emergency_type else None,
                "safety_status": results.safety_status,
                "injury_status": results.injury_status,
                "emergency_location": results.emergency_location,
                "load_secure": results.load_secure,
                "escalation_status": results.escalation_status,
                "raw_extraction": results.raw_extraction,
                "confidence_score": results.confidence_score,
                "created_at": now,
            }

            result = self.db.table(Tables.CALL_RESULTS).insert(db_record).execute()

            return self._map_results_to_response(result.data[0])

        except Exception as e:
            logger.error(f"Failed to save call results: {e}")
            raise

    async def get_call_results(self, call_id: str) -> Optional[CallResultsResponse]:
        """
        Get call results by call ID.

        Args:
            call_id: Internal call ID

        Returns:
            Call results or None
        """
        try:
            result = self.db.table(Tables.CALL_RESULTS).select("*").eq("call_id", call_id).execute()

            if not result.data:
                return None

            return self._map_results_to_response(result.data[0])

        except Exception as e:
            logger.error(f"Failed to get call results for {call_id}: {e}")
            raise

    def _map_to_response(self, row: dict) -> CallResponse:
        """Map database row to call response."""
        return CallResponse(
            id=row["id"],
            agent_id=row["agent_id"],
            retell_call_id=row.get("retell_call_id"),
            access_token=row.get("access_token"),
            driver_name=row["driver_name"],
            load_number=row["load_number"],
            origin=row.get("origin"),
            destination=row.get("destination"),
            status=CallStatus(row["status"]),
            duration_seconds=row.get("duration_seconds"),
            transcript=row.get("transcript"),
            recording_url=row.get("recording_url"),
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")),
            ended_at=datetime.fromisoformat(row["ended_at"].replace("Z", "+00:00")) if row.get("ended_at") else None,
            results=None,  # Will be populated separately
        )

    async def sync_call_from_retell(self, retell_call_id: str) -> Optional[CallResponse]:
        """
        Fetch call data from Retell API and update local database.

        Useful for manual sync when webhooks aren't available (local testing).

        Args:
            retell_call_id: Retell's call ID

        Returns:
            Updated call response with results
        """
        try:
            # Get our local call record
            local_call = await self.get_call_by_retell_id(retell_call_id)
            if not local_call:
                logger.error(f"No local call found for Retell call {retell_call_id}")
                return None

            # Fetch from Retell API
            retell_data = await self.retell.get_call(retell_call_id)

            logger.info(f"Fetched Retell call data: status={retell_data.get('call_status')}, has_transcript={bool(retell_data.get('transcript'))}")

            # Calculate duration if we have timestamps
            duration_seconds = None
            if retell_data.get("start_timestamp") and retell_data.get("end_timestamp"):
                duration_seconds = int(
                    (retell_data["end_timestamp"] - retell_data["start_timestamp"]) / 1000
                )

            # Map Retell status to our status
            retell_status = retell_data.get("call_status", "")
            if retell_status == "ended":
                new_status = CallStatus.COMPLETED
            elif retell_status == "error":
                new_status = CallStatus.FAILED
            elif retell_status in ["registered", "ongoing"]:
                new_status = CallStatus.IN_PROGRESS
            else:
                new_status = local_call.status

            # Update call record
            now = datetime.utcnow().isoformat()
            update_data = {
                "status": new_status.value,
                "transcript": retell_data.get("transcript"),
                "recording_url": retell_data.get("recording_url"),
                "duration_seconds": duration_seconds,
                "updated_at": now,
            }

            if new_status in [CallStatus.COMPLETED, CallStatus.FAILED]:
                update_data["ended_at"] = now

            self.db.table(Tables.CALLS).update(update_data).eq("id", local_call.id).execute()

            logger.info(f"Updated call {local_call.id} with Retell data")

            # Process transcript if available and call ended
            if retell_data.get("transcript") and new_status == CallStatus.COMPLETED:
                try:
                    await self.process_call_completion(
                        call_id=local_call.id,
                        transcript=retell_data["transcript"],
                        recording_url=retell_data.get("recording_url"),
                        duration_seconds=duration_seconds
                    )
                    logger.info(f"Processed transcript for call {local_call.id}")
                except Exception as e:
                    logger.error(f"Failed to process transcript: {e}")

            # Return updated call
            return await self.get_call(local_call.id)

        except Exception as e:
            logger.error(f"Failed to sync call from Retell: {e}")
            raise

    def _map_results_to_response(self, row: dict) -> CallResultsResponse:
        """Map database row to call results response."""
        from app.schemas.call import CallOutcome, DriverStatus, EmergencyType
        
        # Handle old invalid call_outcome values gracefully
        call_outcome_str = row.get("call_outcome", "Unknown")
        try:
            call_outcome = CallOutcome(call_outcome_str)
        except ValueError:
            logger.warning(f"Invalid call_outcome '{call_outcome_str}', using Unknown")
            call_outcome = CallOutcome.UNKNOWN  # Fallback to Unknown

        return CallResultsResponse(
            id=row["id"],
            call_id=row["call_id"],
            call_outcome=call_outcome,
            is_emergency=row.get("is_emergency", False),
            driver_status=DriverStatus(row["driver_status"]) if row.get("driver_status") else None,
            current_location=row.get("current_location"),
            eta=row.get("eta"),
            delay_reason=row.get("delay_reason"),
            unloading_status=row.get("unloading_status"),
            pod_reminder_acknowledged=row.get("pod_reminder_acknowledged"),
            emergency_type=EmergencyType(row["emergency_type"]) if row.get("emergency_type") else None,
            safety_status=row.get("safety_status"),
            injury_status=row.get("injury_status"),
            emergency_location=row.get("emergency_location"),
            load_secure=row.get("load_secure"),
            escalation_status=row.get("escalation_status"),
            raw_extraction=row.get("raw_extraction"),
            confidence_score=row.get("confidence_score"),
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
        )


# Singleton instance
call_service = CallService()


def get_call_service() -> CallService:
    """Get call service instance."""
    return call_service