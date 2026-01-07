"""
Supabase Database Connector Implementation.

Concrete implementation of DBConnector interface for Supabase database.
Handles all Supabase-specific database operations.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.db.database import get_supabase_client, Tables
from .db_connector import DBConnector
from .models import CallUpdateData, CallResultsData, CallRecord

logger = logging.getLogger(__name__)


class SupabaseDBConnector(DBConnector):
    """
    Supabase implementation of the DBConnector interface.
    
    This class handles all database operations using Supabase as the backend.
    It follows the Single Responsibility Principle by only handling database
    operations without any business logic.
    
    Responsibilities:
    - Execute CRUD operations on Supabase
    - Handle database errors gracefully
    - Convert between Supabase responses and Pydantic models
    - Log database operations for debugging
    """
    
    def __init__(self):
        """
        Initialize the Supabase connector.
        
        Gets the Supabase client instance for database operations.
        """
        self.db = get_supabase_client()
        logger.info("[SUPABASE_CONNECTOR] Initialized")
    
    async def find_call_by_session_id(self, session_id: str) -> Optional[str]:
        """
        Find call ID by session ID.
        
        The session ID is stored in the 'retell_call_id' field for
        compatibility with existing schema.
        
        Args:
            session_id: Session ID to search for
            
        Returns:
            Call ID if found, None otherwise
        """
        try:
            logger.debug(f"[SUPABASE_CONNECTOR] Finding call with session_id: {session_id}")
            
            result = self.db.table(Tables.CALLS)\
                .select("id")\
                .eq("retell_call_id", session_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                call_id = result.data[0]["id"]
                logger.info(f"[SUPABASE_CONNECTOR] Found call ID: {call_id}")
                return call_id
            
            logger.warning(f"[SUPABASE_CONNECTOR] No call found for session_id: {session_id}")
            return None
            
        except Exception as e:
            logger.error(f"[SUPABASE_CONNECTOR] Error finding call: {e}", exc_info=True)
            return None
    
    async def get_call_by_id(self, call_id: str) -> Optional[CallRecord]:
        """
        Retrieve call record by ID.
        
        Args:
            call_id: Call record ID
            
        Returns:
            CallRecord if found, None otherwise
        """
        try:
            logger.debug(f"[SUPABASE_CONNECTOR] Fetching call: {call_id}")
            
            result = self.db.table(Tables.CALLS)\
                .select("*")\
                .eq("id", call_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                call_data = result.data[0]
                logger.info(f"[SUPABASE_CONNECTOR] Retrieved call: {call_id}")
                
                # Convert to Pydantic model
                return CallRecord(**call_data)
            
            logger.warning(f"[SUPABASE_CONNECTOR] Call not found: {call_id}")
            return None
            
        except Exception as e:
            logger.error(f"[SUPABASE_CONNECTOR] Error fetching call: {e}", exc_info=True)
            return None
    
    async def update_call(self, call_id: str, update_data: CallUpdateData) -> bool:
        """
        Update call record with new data.
        
        Args:
            call_id: Call record ID to update
            update_data: Pydantic model with update data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"[SUPABASE_CONNECTOR] Updating call: {call_id}")
            
            # Convert Pydantic model to dict, excluding None values
            update_dict = update_data.model_dump(exclude_none=True)
            
            # Convert datetime objects to ISO format strings
            for key, value in update_dict.items():
                if isinstance(value, datetime):
                    update_dict[key] = value.isoformat()
            
            logger.debug(f"[SUPABASE_CONNECTOR] Update fields: {list(update_dict.keys())}")
            
            # Execute update
            result = self.db.table(Tables.CALLS)\
                .update(update_dict)\
                .eq("id", call_id)\
                .execute()
            
            logger.info(f"[SUPABASE_CONNECTOR] Successfully updated call: {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"[SUPABASE_CONNECTOR] Error updating call: {e}", exc_info=True)
            return False
    
    async def upsert_call_results(self, results_data: CallResultsData) -> bool:
        """
        Insert or update call results.
        
        Uses Supabase's upsert functionality to insert new results
        or update existing ones based on call_id.
        
        Args:
            results_data: Pydantic model with results data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"[SUPABASE_CONNECTOR] Upserting call results for: {results_data.call_id}")
            
            # Convert Pydantic model to dict, excluding None values
            results_dict = results_data.model_dump(exclude_none=True)
            
            logger.debug(f"[SUPABASE_CONNECTOR] Results fields: {list(results_dict.keys())}")
            
            # Execute upsert
            result = self.db.table(Tables.CALL_RESULTS)\
                .upsert(results_dict)\
                .execute()
            
            logger.info(f"[SUPABASE_CONNECTOR] Successfully upserted call results: {results_data.call_id}")
            return True
            
        except Exception as e:
            logger.error(f"[SUPABASE_CONNECTOR] Error upserting results: {e}", exc_info=True)
            return False
    
    async def get_call_results(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve call results by call ID.
        
        Args:
            call_id: Call record ID
            
        Returns:
            Results dictionary if found, None otherwise
        """
        try:
            logger.debug(f"[SUPABASE_CONNECTOR] Fetching call results: {call_id}")
            
            result = self.db.table(Tables.CALL_RESULTS)\
                .select("*")\
                .eq("call_id", call_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"[SUPABASE_CONNECTOR] Retrieved call results: {call_id}")
                return result.data[0]
            
            logger.warning(f"[SUPABASE_CONNECTOR] No results found for call: {call_id}")
            return None
            
        except Exception as e:
            logger.error(f"[SUPABASE_CONNECTOR] Error fetching results: {e}", exc_info=True)
            return None
    
    async def delete_call(self, call_id: str) -> bool:
        """
        Delete a call record.
        
        Args:
            call_id: Call record ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"[SUPABASE_CONNECTOR] Deleting call: {call_id}")
            
            # Delete call results first (foreign key constraint)
            self.db.table(Tables.CALL_RESULTS)\
                .delete()\
                .eq("call_id", call_id)\
                .execute()
            
            # Delete call record
            result = self.db.table(Tables.CALLS)\
                .delete()\
                .eq("id", call_id)\
                .execute()
            
            logger.info(f"[SUPABASE_CONNECTOR] Successfully deleted call: {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"[SUPABASE_CONNECTOR] Error deleting call: {e}", exc_info=True)
            return False
    
    async def list_calls(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[CallRecord]:
        """
        List call records with optional filtering.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            filters: Optional filters to apply (e.g., {"status": "completed"})
            
        Returns:
            List of CallRecord objects
        """
        try:
            logger.debug(f"[SUPABASE_CONNECTOR] Listing calls (limit={limit}, offset={offset})")
            
            # Build query
            query = self.db.table(Tables.CALLS).select("*")
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            # Apply pagination
            result = query.range(offset, offset + limit - 1).execute()
            
            # Convert to Pydantic models
            calls = [CallRecord(**call_data) for call_data in result.data]
            
            logger.info(f"[SUPABASE_CONNECTOR] Retrieved {len(calls)} calls")
            return calls
            
        except Exception as e:
            logger.error(f"[SUPABASE_CONNECTOR] Error listing calls: {e}", exc_info=True)
            return []


# Singleton instance
_db_connector: Optional[SupabaseDBConnector] = None


def get_db_connector() -> SupabaseDBConnector:
    """
    Get or create the SupabaseDBConnector singleton.
    
    Returns:
        Singleton instance of SupabaseDBConnector
    """
    global _db_connector
    if _db_connector is None:
        _db_connector = SupabaseDBConnector()
    return _db_connector
