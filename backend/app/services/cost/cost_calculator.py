"""
Cost Calculator - Calculates operational costs for Pipecat voice calls.

This service calculates the cost breakdown for STT, TTS, LLM, and transport
services based on actual usage metrics.

Pricing is based on publicly available pricing from service websites as of Jan 2026:
- Deepgram: https://deepgram.com/pricing
- Cartesia: https://cartesia.ai/pricing
- ElevenLabs: https://elevenlabs.io/pricing
- OpenAI: https://openai.com/api/pricing
- Anthropic: https://www.anthropic.com/pricing
- Daily.co: https://www.daily.co/pricing
"""
import logging
from typing import Optional

from app.schemas.cost import ServiceCost, CostBreakdown

logger = logging.getLogger(__name__)


class CostCalculator:
    """Calculator for voice call operational costs."""
    
    # STT Pricing (per minute of audio)
    STT_PRICES = {
        "deepgram": {
            "nova-2": 0.0043,  # $0.0043 per minute
            "base": 0.0125,    # $0.0125 per minute
        },
        "azure_speech": {
            "default": 1.00 / 60,  # $1.00 per hour = ~$0.0167 per minute
        },
        "assemblyai": {
            "default": 0.00025,  # $0.00025 per second = $0.015 per minute
        }
    }
    
    # TTS Pricing (per character)
    TTS_PRICES = {
        "cartesia": {
            "sonic": 0.000015,  # $15 per 1M characters = $0.000015 per character
        },
        "eleven_labs": {
            "turbo_v2_5": 0.0003,  # $0.30 per 1K characters = $0.0003 per character
            "turbo_v2": 0.0003,
            "multilingual_v2": 0.0003,
        },
        "azure_tts": {
            "neural": 0.000016,  # $16 per 1M characters = $0.000016 per character
        }
    }
    
    # LLM Pricing (per 1K tokens)
    LLM_PRICES = {
        "openai": {
            "gpt-4o": {
                "input": 0.0025,   # $2.50 per 1M input tokens = $0.0025 per 1K
                "output": 0.01,    # $10.00 per 1M output tokens = $0.01 per 1K
            },
            "gpt-4o-mini": {
                "input": 0.00015,  # $0.15 per 1M input tokens = $0.00015 per 1K
                "output": 0.0006,  # $0.60 per 1M output tokens = $0.0006 per 1K
            },
            "gpt-4-turbo": {
                "input": 0.01,
                "output": 0.03,
            }
        },
        "anthropic": {
            "claude-3-5-sonnet-20241022": {
                "input": 0.003,    # $3.00 per 1M input tokens = $0.003 per 1K
                "output": 0.015,   # $15.00 per 1M output tokens = $0.015 per 1K
            },
            "claude-3-5-haiku-20241022": {
                "input": 0.001,    # $1.00 per 1M input tokens = $0.001 per 1K
                "output": 0.005,   # $5.00 per 1M output tokens = $0.005 per 1K
            }
        }
    }
    
    # Transport Pricing (per minute)
    TRANSPORT_PRICES = {
        "daily_webrtc": 0.0015,  # $0.0015 per participant minute (developer tier)
        "websocket": 0.0,  # No additional cost for WebSocket
    }
    
    def calculate_stt_cost(
        self,
        service: str,
        duration_seconds: float,
        model: Optional[str] = None
    ) -> ServiceCost:
        """
        Calculate STT cost based on audio duration.
        
        Args:
            service: STT service name (e.g., "deepgram")
            duration_seconds: Audio duration in seconds
            model: Optional model name for pricing lookup
            
        Returns:
            ServiceCost with breakdown
        """
        minutes = duration_seconds / 60.0
        
        # Get pricing
        service_prices = self.STT_PRICES.get(service, {})
        if model and model in service_prices:
            price_per_minute = service_prices[model]
        else:
            # Use first available price or default
            price_per_minute = next(iter(service_prices.values()), 0.01)
        
        cost = minutes * price_per_minute
        
        return ServiceCost(
            service_name=service,
            model=model,
            units=minutes,
            unit_type="minutes",
            cost_per_unit=price_per_minute,
            cost_usd=cost
        )
    
    def calculate_tts_cost(
        self,
        service: str,
        total_chars: int,
        model: Optional[str] = None
    ) -> ServiceCost:
        """
        Calculate TTS cost based on characters spoken.
        
        Args:
            service: TTS service name (e.g., "cartesia")
            total_chars: Total characters spoken
            model: Optional model name for pricing lookup
            
        Returns:
            ServiceCost with breakdown
        """
        # Get pricing
        service_prices = self.TTS_PRICES.get(service, {})
        if model and model in service_prices:
            price_per_char = service_prices[model]
        elif "default" in service_prices:
            price_per_char = service_prices["default"]
        else:
            # Use first available price or default
            price_per_char = next(iter(service_prices.values()), 0.00002)
        
        cost = total_chars * price_per_char
        
        return ServiceCost(
            service_name=service,
            model=model,
            units=float(total_chars),
            unit_type="characters",
            cost_per_unit=price_per_char,
            cost_usd=cost
        )
    
    def calculate_llm_cost(
        self,
        service: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> ServiceCost:
        """
        Calculate LLM cost based on token usage.
        
        Args:
            service: LLM service name (e.g., "openai")
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            ServiceCost with breakdown
        """
        # Get pricing
        service_prices = self.LLM_PRICES.get(service, {})
        model_prices = service_prices.get(model, {})
        
        if not model_prices:
            # Try to find a close match or use default
            for key in service_prices.keys():
                if key in model or model in key:
                    model_prices = service_prices[key]
                    break
        
        # Default prices if not found
        input_price_per_1k = model_prices.get("input", 0.001)
        output_price_per_1k = model_prices.get("output", 0.002)
        
        # Calculate cost
        input_cost = (input_tokens / 1000.0) * input_price_per_1k
        output_cost = (output_tokens / 1000.0) * output_price_per_1k
        total_cost = input_cost + output_cost
        
        total_tokens = input_tokens + output_tokens
        avg_price_per_1k = (total_cost / total_tokens * 1000.0) if total_tokens > 0 else 0
        
        return ServiceCost(
            service_name=service,
            model=model,
            units=float(total_tokens),
            unit_type="tokens",
            cost_per_unit=avg_price_per_1k,
            cost_usd=total_cost
        )
    
    def calculate_transport_cost(
        self,
        transport_type: str,
        duration_seconds: float
    ) -> ServiceCost:
        """
        Calculate transport cost based on connection duration.
        
        Args:
            transport_type: Transport type (e.g., "daily_webrtc")
            duration_seconds: Connection duration in seconds
            
        Returns:
            ServiceCost with breakdown
        """
        minutes = duration_seconds / 60.0
        price_per_minute = self.TRANSPORT_PRICES.get(transport_type, 0.0)
        cost = minutes * price_per_minute
        
        return ServiceCost(
            service_name=transport_type,
            model=None,
            units=minutes,
            unit_type="minutes",
            cost_per_unit=price_per_minute,
            cost_usd=cost
        )
    
    def calculate_call_cost(
        self,
        stt_service: str,
        tts_service: str,
        llm_service: str,
        transport_type: str,
        duration_seconds: float,
        total_chars: int,
        total_tokens: int,
        stt_model: Optional[str] = None,
        tts_model: Optional[str] = None,
        llm_model: str = "gpt-4o",
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
    ) -> CostBreakdown:
        """
        Calculate complete cost breakdown for a call.
        
        Args:
            stt_service: STT service name
            tts_service: TTS service name
            llm_service: LLM service name
            transport_type: Transport type
            duration_seconds: Call duration in seconds
            total_chars: Total characters spoken by bot
            total_tokens: Total LLM tokens used
            stt_model: Optional STT model name
            tts_model: Optional TTS model name
            llm_model: LLM model name
            input_tokens: LLM input tokens (if None, estimated from total)
            output_tokens: LLM output tokens (if None, estimated from total)
            
        Returns:
            Complete cost breakdown
        """
        # Calculate individual costs
        stt_cost = self.calculate_stt_cost(stt_service, duration_seconds, stt_model)
        tts_cost = self.calculate_tts_cost(tts_service, total_chars, tts_model)
        
        # Estimate input/output token split if not provided (typical ratio is ~60/40)
        if input_tokens is None or output_tokens is None:
            input_tokens = int(total_tokens * 0.6)
            output_tokens = int(total_tokens * 0.4)
        
        llm_cost = self.calculate_llm_cost(llm_service, llm_model, input_tokens, output_tokens)
        transport_cost = self.calculate_transport_cost(transport_type, duration_seconds)
        
        # Calculate total
        total = (
            stt_cost.cost_usd +
            tts_cost.cost_usd +
            llm_cost.cost_usd +
            transport_cost.cost_usd
        )
        
        logger.info(
            f"Cost breakdown: STT=${stt_cost.cost_usd:.4f}, "
            f"TTS=${tts_cost.cost_usd:.4f}, "
            f"LLM=${llm_cost.cost_usd:.4f}, "
            f"Transport=${transport_cost.cost_usd:.4f}, "
            f"Total=${total:.4f}"
        )
        
        return CostBreakdown(
            stt_cost=stt_cost,
            tts_cost=tts_cost,
            llm_cost=llm_cost,
            transport_cost=transport_cost,
            total_cost_usd=total,
            duration_seconds=duration_seconds
        )


# Singleton instance
_cost_calculator: Optional[CostCalculator] = None


def get_cost_calculator() -> CostCalculator:
    """Get or create the CostCalculator singleton."""
    global _cost_calculator
    if _cost_calculator is None:
        _cost_calculator = CostCalculator()
    return _cost_calculator
