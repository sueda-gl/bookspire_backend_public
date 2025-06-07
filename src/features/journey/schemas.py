from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.shared.schemas import BaseSessionResponse

# Request schemas
class JourneyStartRequest(BaseModel):
    character_id: str
    language_level: str

class JourneyResponseCreate(BaseModel):
    question_id: str
    response_text: str

# Response schemas
class Question(BaseModel):
    id: str
    question: str
    book_reference: str

class JourneyResponseDetail(BaseModel):
    id: str
    question_id: str
    user_response: str
    score: Optional[float] = None
    feedback: Optional[str] = None
    evaluated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SessionStatus(BaseModel):
    id: str
    questions_count: int
    current_attempt: int
    avg_score: Optional[float] = None
    is_completed: bool
    is_passed: Optional[bool] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    character_id: Optional[str] = None
    language_level: Optional[str] = None
    
    class Config:
        from_attributes = True

class SessionDetail(SessionStatus):
    responses: List[JourneyResponseDetail]
    
    class Config:
        from_attributes = True

class EvaluationResult(BaseModel):
    response_id: str
    score: float
    feedback: str
    is_evaluation_complete: bool

class WebSocketMessage(BaseModel):
    type: str  # "question", "evaluation", "session_complete", "error"
    data: Dict[str, Any]