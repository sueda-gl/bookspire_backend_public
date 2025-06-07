# Curriculum-specific dependencies 
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.security import get_current_user, get_current_active_user
from src.features.auth.models import User
from src.features.penpal.service import PenpalService
from src.shared.llm.client import LLMClient

# Service dependency
def get_penpal_service(request: Request) -> PenpalService:
    """Dependency to get an instance of the PenpalService."""
    # Use the shared LLMClient from the application state
    llm_client = request.app.state.llm_client
    return PenpalService(llm_client)

# Get current user with role information
async def get_current_user_with_role(
    current_user: User = Depends(get_current_active_user)
):
    return current_user

# Student-only access
async def require_student_role(
    current_user: User = Depends(get_current_user_with_role)
):
    if current_user.role != 'student':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this resource"
        )
    return current_user

# Teacher-only access
async def require_teacher_role(
    current_user: User = Depends(get_current_user_with_role)
):
    if current_user.role != 'teacher':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can access this resource"
        )
    return current_user 