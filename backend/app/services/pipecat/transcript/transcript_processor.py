"""
Transcript Processor Service - Extracts structured data from call transcripts.
Uses OpenAI/Claude for intelligent extraction with fallback to pattern matching.
"""
import json
import logging
import re
from typing import Optional, Dict, Any, List
from openai import OpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.call import (
    CallOutcome,
    DriverStatus,
    EmergencyType,
    CallResultsCreate,
    RoutineCallResults,
    EmergencyCallResults,
)

logger = logging.getLogger(__name__)


class TranscriptProcessor:
    """Service for processing call transcripts and extracting structured data."""

    def __init__(self):
        """Initialize OpenAI client for transcript analysis."""
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

        # Emergency trigger patterns
        self.emergency_patterns = [
            r'\b(accident|crashed?|collision)\b',
            r'\b(blowout|flat tire|tire blew)\b',
            r'\b(breakdown|broke down|engine)\b',
            r'\b(medical|sick|hurt|injured|ambulance)\b',
            r'\b(emergency|help|911)\b',
            r'\b(fire|smoke|burning)\b',
        ]

        # Location patterns
        self.location_patterns = [
            r'(?:on|at|near)\s+([A-Z]-?\d+(?:\s+(?:north|south|east|west))?)',  # Highway
            r'mile\s*marker\s*(\d+)',
            r'exit\s*(\d+)',
            r'(?:in|at|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:,\s*[A-Z]{2})?)',  # City
        ]

        # ETA patterns
        self.eta_patterns = [
            r'(?:eta|arrive|arriving|get there)\s*(?:is|at|around|by)?\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)',
            r'(?:about|around|approximately)\s*(\d+)\s*(?:hours?|minutes?|mins?)',
            r'(?:tomorrow|tonight|this evening)\s*(?:at|around|by)?\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?',
        ]

    def detect_emergency(self, transcript: str) -> bool:
        """
        Detect if transcript contains emergency indicators.

        Args:
            transcript: Call transcript text

        Returns:
            True if emergency detected
        """
        transcript_lower = transcript.lower()

        for pattern in self.emergency_patterns:
            if re.search(pattern, transcript_lower):
                return True

        return False

    def classify_emergency_type(self, transcript: str) -> EmergencyType:
        """
        Classify the type of emergency from transcript.

        Args:
            transcript: Call transcript text

        Returns:
            Emergency type classification
        """
        transcript_lower = transcript.lower()

        if re.search(r'\b(accident|crashed?|collision|hit)\b', transcript_lower):
            return EmergencyType.ACCIDENT
        elif re.search(r'\b(blowout|flat|tire|breakdown|broke down|engine|mechanical)\b', transcript_lower):
            return EmergencyType.BREAKDOWN
        elif re.search(r'\b(medical|sick|hurt|injured|ambulance|heart|chest|breathing)\b', transcript_lower):
            return EmergencyType.MEDICAL
        else:
            return EmergencyType.OTHER

    def extract_location(self, transcript: str) -> Optional[str]:
        """
        Extract location from transcript using pattern matching.

        Args:
            transcript: Call transcript text

        Returns:
            Extracted location or None
        """
        for pattern in self.location_patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def extract_eta(self, transcript: str) -> Optional[str]:
        """
        Extract ETA from transcript.

        Args:
            transcript: Call transcript text

        Returns:
            Extracted ETA or None
        """
        for pattern in self.eta_patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    async def process_transcript_with_llm(
            self,
            transcript: str,
            call_context: Dict[str, Any],
            is_emergency: bool = False
    ) -> Dict[str, Any]:
        """
        Use LLM to extract structured data from transcript.

        Args:
            transcript: Call transcript text
            call_context: Context about the call (driver name, load number, etc.)
            is_emergency: Whether this is an emergency call

        Returns:
            Extracted structured data
        """
        try:
            if is_emergency:
                prompt = self._build_emergency_extraction_prompt(transcript, call_context)
                self._get_emergency_schema()
            else:
                prompt = self._build_routine_extraction_prompt(transcript, call_context)
                self._get_routine_schema()

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data extraction assistant. Extract structured information from call transcripts. Return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"LLM extraction successful: {result}")
            return result

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            # Fallback to pattern matching
            return self._fallback_extraction(transcript, is_emergency)

    def _build_routine_extraction_prompt(
            self,
            transcript: str,
            call_context: Dict[str, Any]
    ) -> str:
        """Build prompt for routine call data extraction."""
        return f"""Extract structured information from this logistics dispatch call transcript.

Call Context:
- Driver Name: {call_context.get('driver_name', 'Unknown')}
- Load Number: {call_context.get('load_number', 'Unknown')}
- Route: {call_context.get('origin', 'Unknown')} to {call_context.get('destination', 'Unknown')}

Transcript:
{transcript}

Extract the following information as JSON:
{{
    "call_outcome": "In-Transit Update" or "Arrival Confirmation" or "Incomplete" or "Unknown",
    "driver_status": "Driving" or "Delayed" or "Arrived" or "Unloading" or "Waiting" or "Unknown",
    "current_location": "string or null - where the driver currently is",
    "eta": "string or null - expected arrival time",
    "delay_reason": "string or null - reason for any delays (e.g., 'Heavy Traffic', 'Weather', 'Construction')",
    "unloading_status": "string or null - if arrived, unloading status (e.g., 'In Door 42', 'Waiting for Lumper', 'Detention')",
    "pod_reminder_acknowledged": true or false - did driver acknowledge POD reminder
}}

Return only valid JSON. Use null for unknown values."""

    def _build_emergency_extraction_prompt(
            self,
            transcript: str,
            call_context: Dict[str, Any]
    ) -> str:
        """Build prompt for emergency call data extraction."""
        return f"""Extract structured information from this emergency logistics call transcript.

Call Context:
- Driver Name: {call_context.get('driver_name', 'Unknown')}
- Load Number: {call_context.get('load_number', 'Unknown')}

Transcript:
{transcript}

Extract the following information as JSON:
{{
    "call_outcome": "Emergency Escalation",
    "emergency_type": "Accident" or "Breakdown" or "Medical" or "Other",
    "safety_status": "string - safety confirmation (e.g., 'Driver confirmed everyone is safe')",
    "injury_status": "string - injury information (e.g., 'No injuries reported', 'Driver reports minor injury')",
    "emergency_location": "string - specific location of emergency",
    "load_secure": true or false or null - is the cargo/load secure,
    "escalation_status": "string - escalation status (e.g., 'Connected to Human Dispatcher', 'Awaiting Transfer')"
}}

Return only valid JSON. Use null for unknown values."""

    def _get_routine_schema(self) -> Dict[str, Any]:
        """Get JSON schema for routine call extraction."""
        return {
            "type": "object",
            "properties": {
                "call_outcome": {"type": "string"},
                "driver_status": {"type": "string"},
                "current_location": {"type": ["string", "null"]},
                "eta": {"type": ["string", "null"]},
                "delay_reason": {"type": ["string", "null"]},
                "unloading_status": {"type": ["string", "null"]},
                "pod_reminder_acknowledged": {"type": "boolean"},
            },
            "required": ["call_outcome", "driver_status"]
        }

    def _get_emergency_schema(self) -> Dict[str, Any]:
        """Get JSON schema for emergency call extraction."""
        return {
            "type": "object",
            "properties": {
                "call_outcome": {"type": "string"},
                "emergency_type": {"type": "string"},
                "safety_status": {"type": ["string", "null"]},
                "injury_status": {"type": ["string", "null"]},
                "emergency_location": {"type": ["string", "null"]},
                "load_secure": {"type": ["boolean", "null"]},
                "escalation_status": {"type": "string"},
            },
            "required": ["call_outcome", "emergency_type", "escalation_status"]
        }

    def _fallback_extraction(
            self,
            transcript: str,
            is_emergency: bool
    ) -> Dict[str, Any]:
        """Fallback pattern-based extraction when LLM fails."""
        if is_emergency:
            return {
                "call_outcome": CallOutcome.EMERGENCY_ESCALATION.value,
                "emergency_type": self.classify_emergency_type(transcript).value,
                "safety_status": None,
                "injury_status": None,
                "emergency_location": self.extract_location(transcript),
                "load_secure": None,
                "escalation_status": "Pending Review",
            }
        else:
            # Determine call outcome
            transcript_lower = transcript.lower()
            if any(word in transcript_lower for word in ['arrived', 'at the dock', 'at destination']):
                outcome = CallOutcome.ARRIVAL_CONFIRMATION.value
                status = DriverStatus.ARRIVED.value
            elif any(word in transcript_lower for word in ['driving', 'on the road', 'en route']):
                outcome = CallOutcome.IN_TRANSIT_UPDATE.value
                status = DriverStatus.DRIVING.value
            else:
                outcome = CallOutcome.UNKNOWN.value
                status = DriverStatus.UNKNOWN.value

            return {
                "call_outcome": outcome,
                "driver_status": status,
                "current_location": self.extract_location(transcript),
                "eta": self.extract_eta(transcript),
                "delay_reason": None,
                "unloading_status": None,
                "pod_reminder_acknowledged": 'pod' in transcript_lower or 'proof of delivery' in transcript_lower,
            }

    async def process_call_transcript(
            self,
            call_id: str,
            transcript: str,
            call_context: Dict[str, Any]
    ) -> CallResultsCreate:
        """
        Process a call transcript and return structured results.

        Args:
            call_id: ID of the call
            transcript: Full transcript text
            call_context: Context about the call

        Returns:
            CallResultsCreate schema with extracted data
        """
        # First detect if emergency
        is_emergency = self.detect_emergency(transcript)

        # Extract structured data using LLM
        extracted_data = await self.process_transcript_with_llm(
            transcript,
            call_context,
            is_emergency
        )

        # Validate and build result using appropriate model
        if is_emergency:
            validated_results = self._validate_emergency_results(extracted_data)
            return CallResultsCreate(
                call_id=call_id,
                call_outcome=validated_results.call_outcome,
                is_emergency=True,
                emergency_type=validated_results.emergency_type,
                safety_status=validated_results.safety_status,
                injury_status=validated_results.injury_status,
                emergency_location=validated_results.emergency_location,
                load_secure=validated_results.load_secure,
                escalation_status=validated_results.escalation_status,
                raw_extraction=extracted_data,
                confidence_score=0.85,
            )
        else:
            validated_results = self._validate_routine_results(extracted_data)
            return CallResultsCreate(
                call_id=call_id,
                call_outcome=validated_results.call_outcome,
                is_emergency=False,
                driver_status=validated_results.driver_status,
                current_location=validated_results.current_location,
                eta=validated_results.eta,
                delay_reason=validated_results.delay_reason,
                unloading_status=validated_results.unloading_status,
                pod_reminder_acknowledged=validated_results.pod_reminder_acknowledged,
                raw_extraction=extracted_data,
                confidence_score=0.9,
            )

    def _validate_routine_results(self, extracted_data: Dict[str, Any]) -> RoutineCallResults:
        """
        Validate and normalize routine call results using Pydantic model.

        Args:
            extracted_data: Raw extracted data from LLM

        Returns:
            Validated RoutineCallResults
        """
        try:
            # Map string values to enums
            call_outcome_str = extracted_data.get("call_outcome", "Unknown")
            driver_status_str = extracted_data.get("driver_status", "Unknown")

            # Try to match enum values
            try:
                call_outcome = CallOutcome(call_outcome_str)
            except ValueError:
                call_outcome = CallOutcome.UNKNOWN

            try:
                driver_status = DriverStatus(driver_status_str)
            except ValueError:
                driver_status = DriverStatus.UNKNOWN

            return RoutineCallResults(
                call_outcome=call_outcome,
                driver_status=driver_status,
                current_location=extracted_data.get("current_location"),
                eta=extracted_data.get("eta"),
                delay_reason=extracted_data.get("delay_reason"),
                unloading_status=extracted_data.get("unloading_status"),
                pod_reminder_acknowledged=extracted_data.get("pod_reminder_acknowledged", False),
            )
        except ValidationError as e:
            logger.warning(f"Validation error for routine results: {e}")
            return RoutineCallResults()  # Return defaults

    def _validate_emergency_results(self, extracted_data: Dict[str, Any]) -> EmergencyCallResults:
        """
        Validate and normalize emergency call results using Pydantic model.

        Args:
            extracted_data: Raw extracted data from LLM

        Returns:
            Validated EmergencyCallResults
        """
        try:
            # Map string to enum
            emergency_type_str = extracted_data.get("emergency_type", "Other")
            try:
                emergency_type = EmergencyType(emergency_type_str)
            except ValueError:
                emergency_type = EmergencyType.OTHER

            return EmergencyCallResults(
                call_outcome=CallOutcome.EMERGENCY_ESCALATION,
                emergency_type=emergency_type,
                safety_status=extracted_data.get("safety_status"),
                injury_status=extracted_data.get("injury_status"),
                emergency_location=extracted_data.get("emergency_location"),
                load_secure=extracted_data.get("load_secure"),
                escalation_status=extracted_data.get("escalation_status", "Pending"),
            )
        except ValidationError as e:
            logger.warning(f"Validation error for emergency results: {e}")
            return EmergencyCallResults()  # Return defaults


# Singleton instance
transcript_processor = TranscriptProcessor()


def get_transcript_processor() -> TranscriptProcessor:
    """Get transcript processor instance."""
    return transcript_processor