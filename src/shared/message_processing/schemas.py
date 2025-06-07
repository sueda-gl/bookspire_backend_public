# src/shared/message_processing/schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProcessingResult(BaseModel):
    message_id: str
    is_appropriate: bool
    inappropriate_reason: Optional[str] = None
    corrected_text: Optional[str] = None
    grammar_feedback: Optional[str] = None
    processed_at: datetime = datetime.now()