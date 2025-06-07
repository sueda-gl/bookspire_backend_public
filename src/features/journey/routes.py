# Journey routes 

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
import logging

from src.core.db import get_db
from src.features.journey import schemas, service
from src.core.security import get_current_active_user
from src.features.auth.models import User

router = APIRouter(prefix="/journey", tags=["journey"])

# Add this after your imports
logger = logging.getLogger(__name__)

# Dependency to get JourneyService with shared LLMClient
def get_journey_service(request: Request) -> service.JourneyService:
    """Dependency to get an instance of the JourneyService."""
    llm_client = request.app.state.llm_client
    return service.JourneyService(llm_client)

@router.post("/sessions/{session_id}/responses", response_model=schemas.JourneyResponseDetail)
async def submit_response(
    session_id: str,
    response_data: schemas.JourneyResponseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    journey_service: service.JourneyService = Depends(get_journey_service),
):
    """Submit response to a question (fallback for WebSocket)"""
    session = await journey_service.get_session(db, session_id)
    
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session"
        )
        
    try:
        # Just save the response - WebSocket should be used for evaluation
        response = await journey_service.save_response(
            db, 
            session_id, 
            response_data.question_id, 
            response_data.response_text
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting response: {str(e)}"
        )

@router.post("/start")
async def start_journey(
    start_request: schemas.JourneyStartRequest, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    journey_service: service.JourneyService = Depends(get_journey_service),
):
    """Create a new journey session with character and language level"""
    try:
        # Pass character_id and language_level to create_session
        session = await journey_service.create_session(
            db, 
            current_user.id,
            start_request.character_id,
            start_request.language_level
        )
        
        # Return response in the specified format
        return {
            "success": True,
            "data": {
                "journey_id": session.id
            }
        }
    except Exception as e:
        # Log the error server-side for debugging
        logger.error(f"Error creating journey session: {str(e)}", exc_info=True)
        
        # Return user-friendly error response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": str(e)
            }
        ) 