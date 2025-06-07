# src/shared/message_processing/models.py
from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.core.db import Base

class MessageProcessing(Base):
    """
    Database model for storing message processing results.
    Tracks both content moderation and grammar correction.
    """
    __tablename__ = "message_processing"
    
    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_text = Column(Text, nullable=False)
    corrected_text = Column(Text, nullable=True)
    is_appropriate = Column(Boolean, nullable=False, default=True)
    inappropriate_reason = Column(Text, nullable=True)
    grammar_feedback = Column(Text, nullable=True)
    feature = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="message_processings")