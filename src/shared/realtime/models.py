from pydantic import BaseModel, Field
from typing import Optional, Union, Any

class ClientSecret(BaseModel):
    """Model for the client secret value returned by OpenAI"""
    value: str
    expires_at: int = 0  # Default to 0 as seen in the responses

class OpenAITokenResponse(BaseModel):
    """Response model for the OpenAI token endpoint"""
    id: str
    client_secret: ClientSecret
    # Remove expires_at from here as it should be in ClientSecret 