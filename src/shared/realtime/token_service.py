"""Service for obtaining ephemeral tokens from OpenAI's Realtime API."""

import httpx
import logging
import json
from typing import Dict, Any, Optional

from src.core.config import settings
from .models import OpenAITokenResponse

logger = logging.getLogger(__name__)

class TokenError(Exception):
    """Exception raised for token-related errors"""
    pass

class TokenService:
    """Service for obtaining and managing ephemeral tokens from OpenAI's Realtime API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the token service.
        
        Args:
            api_key: Optional OpenAI API key. If not provided, uses the one from settings.
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/realtime"
        logger.info("TokenService initialized")
    
    async def create_token(self, 
                          model: str = "gpt-4o-realtime-preview-2024-12-17",
                          voice: Optional[str] = "verse",
                          instructions: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session and get an ephemeral token from OpenAI.
        
        Args:
            model: The model ID to use
            voice: Optional voice to use for responses
            instructions: Optional system instructions
            
        Returns:
            Raw JSON response from OpenAI API
            
        Raises:
            TokenError: If the token creation fails
        """
        try:
            # Create request parameters - NO OpenAI-Beta header needed for token generation
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Build payload
            payload = self._build_request_payload(model, voice, instructions)
            
            # Log request details (without API key)
            logger.info(f"Creating realtime session with URL: {self.base_url}/sessions")
            logger.info(f"Request payload: {json.dumps(payload)}")
            
            # Make request to OpenAI
            logger.info(f"Creating new realtime session for model={model}, voice={voice}")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sessions",
                    headers=headers,
                    json=payload,
                    timeout=30.0  # 30 second timeout
                )
                
                # Handle errors
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Failed to create token: {response.status_code}, {error_text}")
                    logger.error(f"Full response headers: {response.headers}")
                    
                    # Try to parse the error message if possible
                    try:
                        error_json = response.json()
                        if "error" in error_json:
                            error_message = error_json["error"].get("message", "Unknown error")
                            error_type = error_json["error"].get("type", "unknown")
                            logger.error(f"OpenAI API error: {error_type} - {error_message}")
                    except Exception:
                        logger.error(f"Could not parse error response: {error_text}")
                    
                    raise TokenError(f"Failed to create OpenAI token: {response.status_code}")
                
                # Return raw JSON response - NO Pydantic validation
                return response.json()
                
        except httpx.RequestError as e:
            logger.error(f"HTTP error creating token: {str(e)}")
            raise TokenError(f"Connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating token: {str(e)}")
            # Log traceback for better debugging
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise TokenError(f"Error creating token: {str(e)}")
    
    def _build_request_payload(self, 
                             model: str, 
                             voice: Optional[str], 
                             instructions: Optional[str]) -> Dict[str, Any]:
        """Build the request payload for the OpenAI API.
        
        Args:
            model: The model ID
            voice: Optional voice
            instructions: Optional system instructions
            
        Returns:
            Dictionary with the request payload
        """
        # Build simple payload matching the reference implementation
        payload = {
            "model": model
        }
        
        # Add voice without validation (to handle "verse" correctly)
        if voice:
            payload["voice"] = voice
            
        # Add instructions if provided
        if instructions:
            payload["instructions"] = instructions
            
        return payload
        
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session from OpenAI.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create request parameters - NO OpenAI-Beta header needed
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Make request to OpenAI
            logger.info(f"Deleting realtime session: {session_id}")
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/sessions/{session_id}",
                    headers=headers,
                    timeout=10.0
                )
                
                # Check response
                if response.status_code != 200:
                    logger.warning(f"Failed to delete session: {response.status_code}, {response.text}")
                    return False
                
                logger.info(f"Successfully deleted session: {session_id}")
                return True
                
        except Exception as e:
            logger.warning(f"Error deleting session {session_id}: {str(e)}")
            return False 