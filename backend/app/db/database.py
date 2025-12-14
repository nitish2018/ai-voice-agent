"""
Database connection and client management using Supabase.
"""
from functools import lru_cache
from supabase import create_client, Client
from app.core.config import settings


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get cached Supabase client instance.
    
    Returns:
        Supabase client
    """
    return create_client(
        settings.supabase_url,
        settings.supabase_key
    )


def get_db() -> Client:
    """
    Dependency for getting database client in routes.
    
    Returns:
        Supabase client
    """
    return get_supabase_client()


# Database table names
class Tables:
    """Database table names."""
    AGENTS = "agents"
    CALLS = "calls"
    CALL_RESULTS = "call_results"
    AGENT_STATES = "agent_states"
    PROMPTS = "prompts"
