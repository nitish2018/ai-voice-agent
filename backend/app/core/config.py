"""
Core configuration module for the AI Voice Agent backend.
Handles environment variables and application settings.
"""
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Dispatcher Voice Agent API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Supabase
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_KEY")
    
    # Retell AI
    retell_api_key: str = Field(..., env="RETELL_API_KEY")
    retell_webhook_secret: Optional[str] = Field(None, env="RETELL_WEBHOOK_SECRET")
    
    # OpenAI (for transcript processing)
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Telephony
    from_phone_number: str = Field(..., env="FROM_PHONE_NUMBER")
    
    # Webhook
    webhook_base_url: Optional[str] = Field(None, env="WEBHOOK_BASE_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
