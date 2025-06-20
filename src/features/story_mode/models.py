from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.core.db import Base

class StorySession(Base):
    """Represents a story mode conversation session"""
    __tablename__ = "story_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    title = Column(String(255), nullable=True)
    language_level = Column(String(5), default="b1", nullable=False)
    
    # Relationship to messages in this session
    messages = relationship("StoryMessage", back_populates="session", cascade="all, delete-orphan")
    
    # Relationship to hints in this session
    hints = relationship("StoryHint", back_populates="session", cascade="all, delete-orphan")
    
    # Relationship to user
    user = relationship("User", back_populates="story_sessions")

class StoryMessage(Base):
    """Stores messages exchanged in a story conversation"""
    __tablename__ = "story_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("story_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant' (Little Prince)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Fields for frontend integration
    message_id = Column(String(36), nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    character_id = Column(String(50), nullable=False, default="little-prince")
    is_complete = Column(Boolean, default=True)
    
    # Relationship to parent session
    session = relationship("StorySession", back_populates="messages")
    
    # Relationship to hints (one message can have multiple hints)
    hints = relationship("StoryHint", back_populates="message", cascade="all, delete-orphan")

class StoryHint(Base):
    """Stores hints generated by the conversational LLM"""
    __tablename__ = "story_hints"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("story_sessions.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(String(36), ForeignKey("story_messages.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_used = Column(Boolean, default=False)  # Track if the user used this hint
    
    # Relationships
    session = relationship("StorySession", back_populates="hints")
    message = relationship("StoryMessage", back_populates="hints") 