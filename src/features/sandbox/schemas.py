from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from src.shared.schemas import BaseSessionResponse, BaseMessageResponse, GenericResponse

class SandboxMessageCreate(BaseModel):
    """Schema for creating a new message"""
    content: str = Field(..., description="The message content from the user")

class SandboxMessageResponse(BaseMessageResponse):
    """Schema for message response, inheriting from the shared base."""
    class Config:
        from_attributes = True

class SandboxSessionCreate(BaseModel):
    """Schema for creating a new session"""
    title: Optional[str] = Field(None, description="Optional title for the session")
    language_level: Optional[str] = Field("b1", description="Desired language level (e.g., a1, b1, c1)")

class SandboxSessionUpdate(BaseModel):
    """Schema for updating session details"""
    title: Optional[str] = None
    is_active: Optional[bool] = None

class SandboxSessionResponse(BaseSessionResponse):
    """Schema for session response, inheriting from the shared base."""
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SandboxSessionDetail(SandboxSessionResponse):
    """Schema for detailed session response including messages"""
    messages: List[SandboxMessageResponse] = []
    
    class Config:
        from_attributes = True

class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages"""
    type: str  # "message", "hint", "error"
    data: Dict[str, Any]

class LittlePrinceResponse(BaseModel):
    """Schema for Little Prince LLM response"""
    message: str
    hint: Optional[str] = None
    is_active: bool
    companion_type: Optional[str] = None
    language_level: str
    character_id: str

    class Config:
        from_attributes = True

# New schemas for subtitle WebSocket communication
class SubtitlePayload(BaseModel):
    """Schema for subtitle data sent from frontend"""
    type: str = Field("subtitle", description="Message type")
    content: str = Field(..., description="The subtitle text content")
    character: str = Field(..., description="The character name")
    timestamp: int = Field(..., description="Timestamp in milliseconds")
    messageId: Optional[str] = Field(None, description="Optional reference to the message ID")

class ConversationHintResponse(BaseModel):
    """Schema for conversation hints sent to frontend"""
    type: str = Field("conversation_hint", description="Message type")
    content: str = Field(..., description="The hint content")
    timestamp: int = Field(..., description="Timestamp in milliseconds")

class AcknowledgmentResponse(BaseModel):
    """Schema for message acknowledgment"""
    type: str = Field("ack", description="Message type")
    messageId: str = Field(..., description="The message ID that was acknowledged")
    timestamp: int = Field(..., description="Timestamp in milliseconds")

class PongResponse(BaseModel):
    """Schema for pong response to connection_test"""
    type: str = Field("pong", description="Message type")
    id: str = Field(..., description="The original ping ID")
    timestamp: int = Field(..., description="Timestamp in milliseconds")

class ConnectionTestPayload(BaseModel):
    """Schema for connection test (ping) from frontend"""
    type: str = Field("connection_test", description="Message type")
    id: str = Field(..., description="Unique identifier for this ping")
    timestamp: int = Field(..., description="Timestamp in milliseconds")

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    type: str = Field("ERROR", description="Message type")
    content: str = Field(..., description="Error message")
    messageId: Optional[str] = Field(None, description="Optional reference to the message ID")

# --- Schemas for /start endpoint --- 

class SandboxStartRequest(BaseModel):
    """Request body for starting/initializing a sandbox session."""
    characterName: Optional[str] = Field(None, alias="companion_type", description="Character name/type (e.g., Agnes the Invisible)")
    character_id: int = Field(..., description="Unique character identifier (e.g., 101)")
    language_level: str = Field(..., description="Desired language level (e.g., a1, b1)")
    book_title: Optional[str] = None
    book_author: Optional[str] = None

    class Config:
        allow_population_by_field_name = True

class SandboxStartResponseSession(BaseModel):
    """Session details included in the /start response."""
    id: uuid.UUID
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    companion_type: Optional[str] = None
    language_level: str
    character_id: str

    class Config:
        from_attributes = True

class SandboxStartResponse(BaseModel):
    """Response body for the /start endpoint."""
    session: SandboxStartResponseSession

# -------------------------------------
