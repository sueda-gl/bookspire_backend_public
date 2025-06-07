from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


from src.core.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(256))
    email = Column(String(120), unique=True, index=True, nullable=True)  # Made nullable to match existing schema
    is_active = Column(Boolean, default=True)
    
    # Additional user information
    first_name = Column(String(80), nullable=True)
    last_name = Column(String(80), nullable=True)
    role = Column(String(20), default="user")
    student_id = Column(String(80), unique=False, nullable=True, index=True)
    grade = Column(String(20), nullable=True)
    section = Column(String(20), nullable=True)
    subject = Column(String(80), nullable=True)  # For teachers
    phone = Column(String(20), nullable=True)  # Added phone field
    temp_password = Column(String(100), nullable=True)  # Added temp_password field
    
    created_at = Column(DateTime, default=func.now())

    # Relationships
    sandbox_sessions = relationship("SandboxSession", back_populates="user")
    journey_sessions = relationship("JourneySession", back_populates="user")
    message_processings = relationship("MessageProcessing", back_populates="user")
    story_sessions = relationship("StorySession", back_populates="user")
    
    def to_dict(self):
        """Convert user object to dictionary"""
        base_dict = {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'is_active': self.is_active
        }
        
        if hasattr(self, 'role') and self.role == 'student':
            base_dict.update({
                'student_id': self.student_id,
                'grade': self.grade,
                'section': self.section
            })
        elif hasattr(self, 'role') and self.role == 'teacher':
            base_dict.update({
                'email': self.email,
                'subject': self.subject,
                'phone': self.phone
            })
            
        return base_dict