"""
Daily.co Room Management Service.

Handles creation and management of Daily.co video/audio rooms
for WebRTC-based voice calls.
"""
import logging
import time
from typing import Dict, Any
import aiohttp

from app.core.config import settings
from app.schemas.session import DailyRoomConfig, DailyRoomResponse
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DailyRoomService:
    """
    Service for managing Daily.co rooms.
    
    Responsibilities:
    - Create Daily.co rooms with appropriate configuration
    - Generate meeting tokens for bot authentication
    - Handle API communication with Daily.co
    """
    
    def __init__(self):
        """Initialize the Daily room service."""
        if not settings.daily_api_key:
            logger.warning("DAILY_API_KEY not configured - Daily.co rooms will not be available")
        
        self.api_base_url = "https://api.daily.co/v1"
        self.api_key = settings.daily_api_key
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for Daily.co API requests.
        
        Returns:
            Dictionary of HTTP headers with authorization
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_room(self, config: DailyRoomConfig) -> DailyRoomResponse:
        """
        Create a Daily.co room for a voice call session.
        
        Args:
            config: Configuration for room creation
            
        Returns:
            DailyRoomResponse with room URL and token
            
        Raises:
            Exception: If Daily API key is not configured or room creation fails
        """
        if not self.api_key:
            raise Exception("DAILY_API_KEY not configured")
        
        logger.info(f"Creating Daily.co room for session: {config.session_id}")
        
        # Generate room name from session ID (use first 8 chars for brevity)
        room_name = f"dispatcher-{config.session_id[:8]}"
        
        # Calculate expiry timestamp
        exp_timestamp = int(time.time()) + (config.expiry_hours * 3600)
        expires_at = datetime.utcnow() + timedelta(hours=config.expiry_hours)
        
        # Prepare room configuration
        room_config = {
            "name": room_name,
            "properties": {
                "exp": exp_timestamp,
                "enable_chat": config.enable_chat,
                "enable_emoji_reactions": config.enable_emoji_reactions,
                "max_participants": config.max_participants,
            }
        }
        
        async with aiohttp.ClientSession() as session:
            # Step 1: Create the room
            room_url = await self._create_room_api(session, room_config)
            
            # Step 2: Create meeting token for bot authentication
            token = await self._create_meeting_token_api(
                session,
                room_name,
                exp_timestamp
            )
        
        logger.info(f"Successfully created Daily.co room: {room_url}")
        
        return DailyRoomResponse(
            room_url=room_url,
            token=token,
            room_name=room_name,
            expires_at=expires_at
        )
    
    async def _create_room_api(
        self,
        session: aiohttp.ClientSession,
        room_config: Dict[str, Any]
    ) -> str:
        """
        Call Daily.co API to create a room.
        
        Args:
            session: aiohttp client session
            room_config: Room configuration dictionary
            
        Returns:
            Room URL
            
        Raises:
            Exception: If API request fails
        """
        url = f"{self.api_base_url}/rooms"
        
        async with session.post(
            url,
            json=room_config,
            headers=self._get_headers()
        ) as response:
            if response.status not in [200, 201]:
                error_text = await response.text()
                logger.error(f"Failed to create Daily room: {error_text}")
                raise Exception(f"Failed to create Daily room: {error_text}")
            
            room_data = await response.json()
            return room_data["url"]
    
    async def _create_meeting_token_api(
        self,
        session: aiohttp.ClientSession,
        room_name: str,
        exp_timestamp: int
    ) -> str:
        """
        Call Daily.co API to create a meeting token.
        
        Args:
            session: aiohttp client session
            room_name: Name of the room
            exp_timestamp: Expiry timestamp
            
        Returns:
            Meeting token string
            
        Raises:
            Exception: If API request fails
        """
        url = f"{self.api_base_url}/meeting-tokens"
        
        token_config = {
            "properties": {
                "room_name": room_name,
                "is_owner": True,
                "exp": exp_timestamp,
            }
        }
        
        async with session.post(
            url,
            json=token_config,
            headers=self._get_headers()
        ) as response:
            if response.status not in [200, 201]:
                error_text = await response.text()
                logger.error(f"Failed to create meeting token: {error_text}")
                raise Exception(f"Failed to create meeting token: {error_text}")
            
            token_data = await response.json()
            return token_data["token"]


# Singleton instance
_daily_room_service: DailyRoomService = None


def get_daily_room_service() -> DailyRoomService:
    """
    Get or create the DailyRoomService singleton.
    
    Returns:
        Singleton instance of DailyRoomService
    """
    global _daily_room_service
    if _daily_room_service is None:
        _daily_room_service = DailyRoomService()
    return _daily_room_service
