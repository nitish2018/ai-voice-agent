"""
Database Connector Interface.

Defines the abstract interface for database operations
following the Dependency Inversion Principle (DIP).
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from .models import CallUpdateData, CallResultsData, CallRecord


class DBConnector(ABC):
    """
    Abstract base class for database connectors.
    
    This interface defines all database operations required by the Pipecat service.
    Concrete implementations (e.g., SupabaseDBConnector) provide actual database logic.
    
    Design Principles Applied:
    - Dependency Inversion Principle (DIP): High-level modules depend on abstractions
    - Interface Segregation Principle (ISP): Focused interface for specific needs
    - Single Responsibility Principle (SRP): Only database operations, no business logic
    """
    
    @abstractmethod
    async def find_call_by_session_id(self, session_id: str) -> Optional[str]:
        """
        Find call ID by session ID.
        
        Args:
            session_id: Session ID to search for
            
        Returns:
            Call ID if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_call_by_id(self, call_id: str) -> Optional[CallRecord]:
        """
        Retrieve call record by ID.
        
        Args:
            call_id: Call record ID
            
        Returns:
            CallRecord if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update_call(self, call_id: str, update_data: CallUpdateData) -> bool:
        """
        Update call record with new data.
        
        Args:
            call_id: Call record ID to update
            update_data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def upsert_call_results(self, results_data: CallResultsData) -> bool:
        """
        Insert or update call results.
        
        Args:
            results_data: Results data to upsert
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_call_results(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve call results by call ID.
        
        Args:
            call_id: Call record ID
            
        Returns:
            Results dictionary if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete_call(self, call_id: str) -> bool:
        """
        Delete a call record.
        
        Args:
            call_id: Call record ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
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
            filters: Optional filters to apply
            
        Returns:
            List of CallRecord objects
        """
        pass
