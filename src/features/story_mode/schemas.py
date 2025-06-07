# Chat request/response schemas 
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.shared.schemas import BaseSessionResponse, BaseMessageResponse

class StorySessionCreate(BaseModel):
    """Schema for creating a new session"""
    title: Optional[str] = None
    character_id: str = "little-prince"
    language_level: Optional[str] = "b1"

    @field_validator('language_level')
    def validate_language_level(cls, v):
        if v is not None:
            # Convert to lowercase for case-insensitive validation
            v_lower = v.lower()
            if v_lower not in {"a1", "a2", "b1", "b2", "c1"}:
                raise ValueError('language_level must be one of a1, a2, b1, b2, c1 (case-insensitive)')
            # Return the canonicalized lowercase version
            return v_lower
        return "b1"  # Default value if None

class StorySessionResponse(BaseSessionResponse):
    """Schema for session response, inheriting from the shared base."""
    # This schema intentionally omits the 'updated_at' field for now
    # to maintain the existing API contract.
    pass

class StoryMessageResponse(BaseMessageResponse):
    """Schema for message response, inheriting from the shared base."""
    message_id: str
    character_id: str
    
    class Config:
        from_attributes = True

class StoryHintResponse(BaseModel):
    """Schema for hint response"""
    id: str
    content: str
    created_at: datetime
    is_used: bool
    
    class Config:
        from_attributes = True

class StoryMessageCreate(BaseModel):
    """Schema for creating a message"""
    content: str
    character_id: str = "little-prince"

class StoryMessageWithHints(BaseModel):
    """Schema for message with associated hints"""
    message: StoryMessageResponse
    hints: List[StoryHintResponse]
    
    class Config:
        from_attributes = True

class StoryConversationResponse(BaseModel):
    """Schema for retrieving a conversation"""
    session: StorySessionResponse
    messages: List[StoryMessageResponse]
    recent_hints: List[StoryHintResponse]
    
    class Config:
        from_attributes = True

class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages"""
    type: str
    content: Dict[str, Any]# Chat request/response schemas 