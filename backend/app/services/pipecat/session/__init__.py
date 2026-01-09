"""
Session Module.

This module provides session management and finalization services for Pipecat call sessions.
"""

from .session_finalizer import SessionFinalizer
from .session_manager import (
    SessionManager,
    PipecatSessionState,
    get_session_manager,
)

__all__ = [
    'SessionFinalizer',
    'SessionManager',
    'PipecatSessionState',
    'get_session_manager',
]
