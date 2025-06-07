# src/shared/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Union
from datetime import datetime
import uuid

class BaseSessionResponse(BaseModel):
    """
    A shared base schema for session responses.
    
    Captures the common fields across all feature sessions to ensure
    consistency in the API.
    """
    id: Union[uuid.UUID, str]
    user_id: int
    created_at: datetime
    is_active: bool
    title: Optional[str] = None
    language_level: Optional[str] = None

    class Config:
        from_attributes = True

class BaseMessageResponse(BaseModel):
    """
    A shared base schema for message responses.
    
    Defines the core fields present in any message, whether from a user
    or an assistant, across different features.
    """
    id: Union[uuid.UUID, str]
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class GenericResponse(BaseModel):
    """A generic success/error response schema for simple API actions."""
    status: str
    message: str 