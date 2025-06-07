import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import datetime

from src.core.db import Base

class SandboxSession(Base):
    """Represents a conversation session with the Little Prince character"""
    __tablename__ = "sandbox_sessions"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    is_active = Column(Boolean, default=True)
    title = Column(String(255), nullable=True)
    language_level = Column(String(10), default="b1", nullable=False)
    
    # Relationship to messages in this session
    messages = relationship("SandboxMessage", back_populates="session", cascade="all, delete-orphan")
    
    # Relationship to user
    user = relationship("User", back_populates="sandbox_sessions")

class SandboxMessage(Base):
    """Stores messages exchanged in a Little Prince conversation"""
    __tablename__ = "sandbox_messages"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(PG_UUID(as_uuid=True), ForeignKey("sandbox_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant' (Little Prince)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # New fields for frontend integration
    message_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True, default=uuid.uuid4)
    character_id = Column(String(50), nullable=False, default="little-prince")
    is_complete = Column(Boolean, default=True)
    
    # Relationship to parent session
    session = relationship("SandboxSession", back_populates="messages")
