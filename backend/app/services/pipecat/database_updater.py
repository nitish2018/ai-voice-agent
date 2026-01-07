"""
Database Updater Service (Legacy Adapter).

This module provides backward compatibility by wrapping the new
CallCompletionService with the old DatabaseUpdater interface.

DEPRECATED: Use CallCompletionService directly for new code.
This adapter exists only to maintain compatibility with existing code.
"""
import logging
from typing import Optional

from .session_manager import PipecatSessionState
from .call_completion_service import get_call_completion_service

logger = logging.getLogger(__name__)


class DatabaseUpdater:
    """
    Legacy adapter for database update operations.
    
    This class wraps the new CallCompletionService to maintain
    backward compatibility with existing code that uses DatabaseUpdater.
    
    DEPRECATED: New code should use CallCompletionService directly.
    
    Design Pattern: Adapter Pattern
    - Adapts CallCompletionService to DatabaseUpdater interface
    - Maintains backward compatibility during refactoring
    """
    
    def __init__(self):
        """
        Initialize the database updater adapter.
        
        Delegates to the new CallCompletionService.
        """
        self.call_completion_service = get_call_completion_service()
        logger.info("[DATABASE_UPDATER] Legacy adapter initialized (delegates to CallCompletionService)")
    
    async def update_call_completion(
        self,
        session_id: str,
        session: PipecatSessionState
    ) -> None:
        """
        Update database when a call completes.
        
        This method delegates to CallCompletionService.complete_call()
        to maintain backward compatibility.
        
        Args:
            session_id: Session ID to update
            session: Session state with metrics and transcript
        """
        logger.debug(f"[DATABASE_UPDATER] Delegating to CallCompletionService for session: {session_id}")
        
        # Delegate to new service
        await self.call_completion_service.complete_call(session_id, session)


# Singleton instance
_database_updater: Optional[DatabaseUpdater] = None


def get_database_updater() -> DatabaseUpdater:
    """
    Get or create the DatabaseUpdater singleton.
    
    DEPRECATED: Use get_call_completion_service() for new code.
    
    Returns:
        Singleton instance of DatabaseUpdater (legacy adapter)
    """
    global _database_updater
    if _database_updater is None:
        _database_updater = DatabaseUpdater()
    return _database_updater
