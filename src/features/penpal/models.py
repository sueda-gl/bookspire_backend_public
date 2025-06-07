# Curriculum data models 
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from src.core.db import Base

class PenpalLetter(Base):
    __tablename__ = 'penpal_letters'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    letter_content = Column(Text, nullable=False)
    response_content = Column(Text, nullable=True)
    character_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    delivery_date = Column(DateTime, nullable=False)

    user = relationship('User', backref='penpal_letters')

    def to_dict(self):
        """Convert letter to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "letter_content": self.letter_content,
            "response_content": self.response_content,
            "character_name": self.character_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "student_name": f"{self.user.first_name} {self.user.last_name}" if self.user else None
        }

    def __repr__(self):
        return f"<PenpalLetter id={self.id} user_id={self.user_id}>" 