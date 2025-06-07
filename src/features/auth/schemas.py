from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: str = Field(..., min_length=3, max_length=50)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = "user"  # Default role

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def password_strength(cls, v):
        # Simple password validation - can be enhanced
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user_type: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    subject: Optional[str] = None
    student_id: Optional[str] = None
    grade: Optional[str] = None
    section: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def password_strength(cls, v):
        # Simple password validation - can be enhanced
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class TestUserInfo(BaseModel):
    id: int
    username: str
    password: str

class TestUsersResponse(BaseModel):
    message: str
    student: TestUserInfo
    teacher: TestUserInfo

class LoginData(BaseModel):
    username: str
    password: str