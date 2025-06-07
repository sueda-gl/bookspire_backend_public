from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Request Schemas
class PenpalLetterCreate(BaseModel):
    letter_content: str = Field(..., description="Content of the student's letter")
    character_name: str = Field(..., description="Name of the character to respond")

# Response Schemas
class PenpalLetterResponse(BaseModel):
    id: int
    user_id: int
    letter_content: str
    response_content: Optional[str] = None
    character_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    delivery_date: datetime
    student_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class PenpalLetterList(BaseModel):
    letters: List[PenpalLetterResponse]
    
    class Config:
        from_attributes = True 