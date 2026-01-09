"""
Transcript Formatting Service.

Handles formatting of conversation transcripts for storage and display.
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TranscriptFormatter:
    """
    Service for formatting conversation transcripts.
    
    Responsibilities:
    - Convert transcript list to readable string format
    - Handle different transcript formats
    - Ensure consistent formatting across the application
    
    Design Principles:
    - Single Responsibility: Only handles transcript formatting
    - Stateless: No internal state, pure transformations
    """
    
    @staticmethod
    def format_to_string(transcript: List[Dict[str, Any]]) -> str:
        """
        Format transcript list into a readable string.
        
        Converts a list of message dictionaries into a formatted string
        with clear role labels and message separation.
        
        Args:
            transcript: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            Formatted transcript string with role labels
            
        Example:
            Input: [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
            Output: "USER: Hello\n\nASSISTANT: Hi"
        """
        if not transcript:
            logger.warning("[TRANSCRIPT_FORMATTER] Empty transcript provided")
            return ""
        
        try:
            formatted_messages = []
            
            for msg in transcript:
                role = msg.get('role', 'unknown').upper()
                content = msg.get('content', '')
                
                if content:  # Only include messages with content
                    formatted_messages.append(f"{role}: {content}")
            
            result = "\n\n".join(formatted_messages)
            logger.debug(f"[TRANSCRIPT_FORMATTER] Formatted {len(formatted_messages)} messages")
            
            return result
            
        except Exception as e:
            logger.error(f"[TRANSCRIPT_FORMATTER] Error formatting transcript: {e}", exc_info=True)
            return ""
    
    @staticmethod
    def format_to_json(transcript: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Format transcript to clean JSON structure.
        
        Ensures transcript has consistent structure with only
        necessary fields.
        
        Args:
            transcript: List of message dictionaries
            
        Returns:
            List of cleaned message dictionaries
        """
        if not transcript:
            return []
        
        try:
            cleaned_messages = []
            
            for msg in transcript:
                cleaned_msg = {
                    "role": msg.get('role', 'unknown'),
                    "content": msg.get('content', ''),
                }
                
                # Include timestamp if available
                if 'timestamp' in msg:
                    cleaned_msg['timestamp'] = msg['timestamp']
                
                cleaned_messages.append(cleaned_msg)
            
            logger.debug(f"[TRANSCRIPT_FORMATTER] Cleaned {len(cleaned_messages)} messages")
            return cleaned_messages
            
        except Exception as e:
            logger.error(f"[TRANSCRIPT_FORMATTER] Error cleaning transcript: {e}", exc_info=True)
            return []
    
    @staticmethod
    def get_message_count(transcript: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get count of messages by role.
        
        Args:
            transcript: List of message dictionaries
            
        Returns:
            Dictionary with counts by role
        """
        if not transcript:
            return {"user": 0, "assistant": 0, "total": 0}
        
        try:
            counts = {"user": 0, "assistant": 0, "other": 0}
            
            for msg in transcript:
                role = msg.get('role', 'other')
                if role in counts:
                    counts[role] += 1
                else:
                    counts["other"] += 1
            
            counts["total"] = len(transcript)
            
            return counts
            
        except Exception as e:
            logger.error(f"[TRANSCRIPT_FORMATTER] Error counting messages: {e}", exc_info=True)
            return {"user": 0, "assistant": 0, "total": 0}


# Singleton instance (stateless, but following pattern for consistency)
_transcript_formatter: TranscriptFormatter = TranscriptFormatter()


def get_transcript_formatter() -> TranscriptFormatter:
    """
    Get the TranscriptFormatter instance.
    
    Returns:
        TranscriptFormatter instance
    """
    return _transcript_formatter
