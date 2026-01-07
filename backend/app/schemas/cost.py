"""
Cost-related Pydantic schemas.

Defines data models for cost calculations and breakdowns
for voice call services (STT, TTS, LLM, Transport).
"""
from typing import Optional
from pydantic import BaseModel, Field


class ServiceCost(BaseModel):
    """
    Cost breakdown for a single service.
    
    Represents the cost calculation for one service component
    (e.g., STT, TTS, LLM, or Transport) with unit pricing details.
    """
    service_name: str = Field(..., description="Name of the service (e.g., 'Deepgram', 'Cartesia')")
    model: Optional[str] = Field(None, description="Specific model used (e.g., 'nova-2', 'gpt-4o')")
    units: float = Field(..., description="Number of units consumed (minutes, characters, tokens, etc.)")
    unit_type: str = Field(..., description="Type of units (e.g., 'minutes', 'characters', 'tokens')")
    cost_per_unit: float = Field(..., description="Cost per unit in USD")
    cost_usd: float = Field(..., description="Total cost for this service in USD")


class CostBreakdown(BaseModel):
    """
    Complete cost breakdown for a voice call.
    
    Aggregates costs from all service components with individual
    breakdowns and total cost calculation.
    """
    stt_cost: Optional[ServiceCost] = Field(None, description="Speech-to-Text service cost")
    tts_cost: Optional[ServiceCost] = Field(None, description="Text-to-Speech service cost")
    llm_cost: Optional[ServiceCost] = Field(None, description="LLM service cost")
    transport_cost: Optional[ServiceCost] = Field(None, description="Transport service cost (Daily.co)")
    total_cost_usd: float = Field(..., description="Total cost across all services in USD")
    duration_seconds: float = Field(..., description="Call duration in seconds")
