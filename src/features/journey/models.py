# Journey data models 
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from src.core.db import Base

class JourneySession(Base):
    __tablename__ = "journey_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    character_id = Column(String, nullable=True)  # Added character selection
    language_level = Column(String, nullable=True)  # Changed back from level
    questions_count = Column(Integer, default=0)
    current_attempt = Column(Integer, default=1)  # Track retries
    avg_score = Column(Float, nullable=True)
    is_completed = Column(Boolean, default=False)
    is_passed = Column(Boolean, nullable=True)
    
    # Relationships
    responses = relationship("JourneyResponse", back_populates="session", cascade="all, delete-orphan")
    user = relationship("User", back_populates="journey_sessions")

class JourneyResponse(Base):
    __tablename__ = "journey_responses" 
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("journey_sessions.id"), nullable=False)
    question_id = Column(String, nullable=False)  # References id in JOURNEY_QUESTIONS
    user_response = Column(Text, nullable=False)
    score = Column(Float, nullable=True)  # 0-10 score from LLM
    feedback = Column(Text, nullable=True)  # Detailed feedback from LLM
    created_at = Column(DateTime, server_default=func.now())
    evaluated_at = Column(DateTime, nullable=True)
    attempt = Column(Integer, default=1)  # Which attempt this was
    
    # Relationships
    session = relationship("JourneySession", back_populates="responses") 