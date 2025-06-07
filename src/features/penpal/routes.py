# Curriculum API endpoints 
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from src.core.db import get_db
from src.features.penpal.dependencies import (
    get_penpal_service, 
    get_current_user_with_role, 
    require_student_role
)
from src.features.penpal.schemas import PenpalLetterCreate, PenpalLetterResponse, PenpalLetterList
from src.features.penpal.service import PenpalService
from src.features.auth.models import User

router = APIRouter(prefix="/api/penpal", tags=["penpal"])
logger = logging.getLogger(__name__)

@router.post("", response_model=PenpalLetterResponse, status_code=status.HTTP_201_CREATED)
async def create_penpal_letter(
    letter_data: PenpalLetterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_student_role),
    penpal_service: PenpalService = Depends(get_penpal_service)
):
    """
    Create a new penpal letter (student only)
    """
    try:
        # Validate request data
        if not letter_data.letter_content.strip() or not letter_data.character_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Letter content and character name cannot be empty"
            )
            
        # Process the letter
        new_letter = await penpal_service.process_letter(
            db=db,
            user_id=current_user.id,
            letter_content=letter_data.letter_content,
            character_name=letter_data.character_name
        )
        
        return new_letter
    except Exception as e:
        logger.error(f"Error creating penpal letter: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process letter"
        )

@router.get("", response_model=PenpalLetterList)
async def list_penpal_letters(
    character_name: Optional[str] = Query(None),
    student_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role),
    penpal_service: PenpalService = Depends(get_penpal_service)
):
    """
    List penpal letters based on user role and filters
    """
    try:
        letters = await penpal_service.get_letters(
            db=db,
            user_id=current_user.id if current_user.role == 'student' else None,
            role=current_user.role,
            character_name=character_name,
            student_name=student_name
        )
        
        return {"letters": letters}
    except Exception as e:
        logger.error(f"Error listing penpal letters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve letters"
        ) 