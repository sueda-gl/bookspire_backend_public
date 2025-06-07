# Chat routes
from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
import logging

from src.core.db import get_db
from src.features.auth.models import User
from src.core.security import get_current_active_user
from src.features.story_mode import schemas
from src.features.story_mode.service import StoryService
from src.features.story_mode.dependencies import get_story_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/story", tags=["story"])

@router.post("/sessions", response_model=schemas.StorySessionResponse)
async def create_session(
    session_data: schemas.StorySessionCreate,
    story_service: StoryService = Depends(get_story_service),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new story mode conversation session"""
    logger.info(f"Attempting to create story session. Received data: {session_data.dict()}")
    # When creating via REST API, don't send WebSocket messages
    # since the WebSocket connection likely doesn't exist yet
    try:
        session = await story_service.create_session(
            user_id=current_user.id,
            title=session_data.title,
            character_id=session_data.character_id,
            language_level=session_data.language_level
        )
        logger.info(f"Successfully created story session {session.id}")
        return session
    except Exception as e:
        logger.error(f"Error during story_service.create_session: {str(e)}", exc_info=True)
        # Re-raise a generic 500 or a more specific error if applicable
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create story session: {str(e)}"
        )

@router.get("/sessions", response_model=List[schemas.StorySessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all story mode sessions for the current user"""
    # This would need to be implemented in the service
    # Placeholder implementation:
    from sqlalchemy import select
    from src.features.story_mode.models import StorySession
    
    stmt = select(StorySession).where(StorySession.user_id == current_user.id)
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    
    return sessions

@router.get("/sessions/{session_id}", response_model=schemas.StoryConversationResponse)
async def get_session_conversation(
    session_id: str = Path(...),
    story_service: StoryService = Depends(get_story_service),
    current_user: User = Depends(get_current_active_user),
):
    """Get a story session with its messages and recent hints"""
    # Get the session
    session = await story_service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Verify ownership
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")
        
    # Get session messages
    messages = await story_service.get_session_messages(session_id)
    
    # Get latest hints
    recent_hints = await story_service.get_latest_hints(session_id)
    
    return {
        "session": session,
        "messages": messages,
        "recent_hints": recent_hints
    }

@router.post("/sessions/{session_id}/messages", response_model=schemas.StoryMessageResponse)
async def create_message(
    message_data: schemas.StoryMessageCreate,
    session_id: str = Path(...),
    story_service: StoryService = Depends(get_story_service),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new message in a session (fallback for when WebSockets are not available)"""
    # Verify session ownership
    session = await story_service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")
    
    # Process the message (this will both save the user message and generate a response)
    result = await story_service.process_user_message(
        session_id,
        message_data.content,
        str(uuid4()),
        message_data.character_id,
        str(current_user.id)
    )
    
    # Return the assistant's response message
    return result["assistant_message"]