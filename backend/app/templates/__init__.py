"""Templates module initialization."""
from .agent_templates import (
    OPTIMAL_VOICE_SETTINGS,
    DISPATCH_CHECKIN_PROMPT,
    EMERGENCY_PROTOCOL_PROMPT,
    get_dispatch_checkin_template,
    get_emergency_protocol_template,
    AGENT_TEMPLATES,
)

__all__ = [
    "OPTIMAL_VOICE_SETTINGS",
    "DISPATCH_CHECKIN_PROMPT",
    "EMERGENCY_PROTOCOL_PROMPT",
    "get_dispatch_checkin_template",
    "get_emergency_protocol_template",
    "AGENT_TEMPLATES",
]
