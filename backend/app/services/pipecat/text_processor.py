"""
Text Processing Utilities.

Handles text transformations such as placeholder replacement
for dynamic content injection in prompts and messages.
"""
import logging
from typing import Dict, Optional

from app.schemas.pipeline import PipecatCallRequest

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Utility class for text processing operations.
    
    Responsibilities:
    - Replace placeholders in text with actual values
    - Handle missing values gracefully with defaults
    - Maintain consistent placeholder format
    """
    
    # Default values for missing context
    DEFAULT_VALUES = {
        "driver_name": "driver",
        "load_number": "your load",
        "origin": "the origin",
        "destination": "the destination",
        "expected_eta": "the expected time"
    }
    
    def __init__(self):
        """Initialize the text processor."""
        logger.debug("TextProcessor initialized")
    
    def replace_placeholders(
        self,
        text: str,
        request: PipecatCallRequest
    ) -> str:
        """
        Replace placeholders in text with values from request.
        
        Placeholders follow the format: {{variable_name}}
        
        Supported placeholders:
        - {{driver_name}}: Driver's name
        - {{load_number}}: Load/shipment number
        - {{origin}}: Origin location
        - {{destination}}: Destination location
        - {{expected_eta}}: Expected arrival time
        
        Args:
            text: Text containing placeholders
            request: Call request with context values
            
        Returns:
            Text with placeholders replaced by actual values
            
        Example:
            >>> processor = TextProcessor()
            >>> text = "Hi {{driver_name}}, checking on load {{load_number}}"
            >>> request = PipecatCallRequest(
            ...     agent_id="123",
            ...     driver_name="John",
            ...     load_number="L456"
            ... )
            >>> processor.replace_placeholders(text, request)
            'Hi John, checking on load L456'
        """
        if not text:
            return text
        
        # Build replacement map from request
        replacements = self._build_replacements(request)
        
        # Apply replacements
        result = text
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        
        logger.debug(f"Replaced placeholders in text (length: {len(text)} -> {len(result)})")
        
        return result
    
    def _build_replacements(self, request: PipecatCallRequest) -> Dict[str, str]:
        """
        Build placeholder-to-value mapping from request.
        
        Args:
            request: Call request with context
            
        Returns:
            Dictionary mapping placeholders to values
        """
        return {
            "{{driver_name}}": request.driver_name or self.DEFAULT_VALUES["driver_name"],
            "{{load_number}}": request.load_number or self.DEFAULT_VALUES["load_number"],
            "{{origin}}": request.origin or self.DEFAULT_VALUES["origin"],
            "{{destination}}": request.destination or self.DEFAULT_VALUES["destination"],
            "{{expected_eta}}": request.expected_eta or self.DEFAULT_VALUES["expected_eta"],
        }
    
    def get_placeholder_value(
        self,
        placeholder_name: str,
        request: PipecatCallRequest
    ) -> Optional[str]:
        """
        Get the value for a specific placeholder.
        
        Args:
            placeholder_name: Name of placeholder (without braces)
            request: Call request with context
            
        Returns:
            Value for the placeholder or None if not found
        """
        replacements = self._build_replacements(request)
        placeholder_key = f"{{{{{placeholder_name}}}}}"
        return replacements.get(placeholder_key)


# Singleton instance
_text_processor: Optional[TextProcessor] = None


def get_text_processor() -> TextProcessor:
    """
    Get or create the TextProcessor singleton.
    
    Returns:
        Singleton instance of TextProcessor
    """
    global _text_processor
    if _text_processor is None:
        _text_processor = TextProcessor()
    return _text_processor
