# Sandbox routes 
from fastapi import APIRouter, Depends, HTTPException, status, Request, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
import logging
import json
import traceback
from typing import Optional

from src.core.db import get_db
from src.features.sandbox import schemas, service
from src.core.security import get_current_active_user
from src.features.auth.models import User
from src.shared.realtime import TokenService, TokenError
from src.core.config import settings
# from src.utils.prompt_loader import load_book_character_prompt # <<< REMOVE or COMMENT OUT this line
from src.features.sandbox.characters import get_character_config
from src.shared.llm.client import LLMClient
from .websocket import subtitle_websocket_endpoint

router = APIRouter(prefix="/sandbox", tags=["sandbox"])

# Add this after your imports
logger = logging.getLogger(__name__)

# Initialize the token service
token_service = TokenService()

# --- Simple Voice ID Map --- 
# Now primarily for reference/backward compatibility
# The actual voice mapping is handled in get_character_config
CHARACTER_VOICE_MAP = {
    "102": "nova",  # Ankylosaurus
    "103": "shimmer", # Pterodactyl
    "little-prince": "alloy" # Example if Little Prince is also used here
}
DEFAULT_VOICE = "alloy"
# ---------------------------

@router.post("/sessions", response_model=schemas.SandboxSessionResponse)
async def create_session(
    session_data: schemas.SandboxSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new Little Prince conversation session"""
    try:
        # Create service directly in the function
        sandbox_service = service.SandboxService(LLMClient(), db)
        
        # Get language level from request, default to b1
        language_level = session_data.language_level or "b1"
        
        # Create session
        session = await sandbox_service.create_session(
            db, 
            current_user.id,
            session_data.title,
            language_level=language_level # Pass the level
        )
        
        return session
        
    except Exception as e:
        logger.error(f"Error creating sandbox session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating session: {str(e)}"
        )

@router.get("/sessions/{session_id}", response_model=schemas.SandboxSessionDetail)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get session details including messages"""
    try:
        # Create service directly in the function
        sandbox_service = service.SandboxService(LLMClient(), db)
        
        # Get session
        session = await sandbox_service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
            
        if session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this session"
            )
            
        # Get messages
        messages = await sandbox_service.get_session_messages(db, session_id)
        
        # Combine into response
        session_data = schemas.SandboxSessionDetail.from_orm(session)
        session_data.messages = [schemas.SandboxMessageResponse.from_orm(m) for m in messages]
        
        return session_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving sandbox session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving session: {str(e)}"
        )

@router.get("/sessions", response_model=list[schemas.SandboxSessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all sessions for the current user"""
    try:
        # Get all sessions for the current user
        from sqlalchemy import select
        from src.features.sandbox.models import SandboxSession
        
        stmt = select(SandboxSession).where(
            SandboxSession.user_id == current_user.id
        ).order_by(SandboxSession.created_at.desc())
        
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        
        return [schemas.SandboxSessionResponse.from_orm(s) for s in sessions]
        
    except Exception as e:
        logger.error(f"Error listing sandbox sessions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing sessions: {str(e)}"
        )

@router.patch("/sessions/{session_id}", response_model=schemas.SandboxSessionResponse)
async def update_session(
    session_id: str,
    session_data: schemas.SandboxSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update session details"""
    try:
        # Get session
        from sqlalchemy import select
        from src.features.sandbox.models import SandboxSession
        
        stmt = select(SandboxSession).where(SandboxSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
            
        if session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this session"
            )
            
        # Update fields
        for key, value in session_data.dict(exclude_unset=True).items():
            setattr(session, key, value)
            
        await db.commit()
        await db.refresh(session)
        
        return schemas.SandboxSessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sandbox session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating session: {str(e)}"
        )

@router.get("/realtime/token")
async def get_realtime_token(
    character_id: str = "little-prince",
    model: str = "gpt-4o-realtime-preview",
    languageLevel: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get an ephemeral token for the OpenAI Realtime API.
    
    Uses character_id and optional languageLevel to determine the system prompt and voice.
    """
    # --- VERY DETAILED LOGGING --- 
    logger.info(f"--- ENTERING get_realtime_token --- Character ID: '{character_id}', Language Level: '{languageLevel}' (Type: {type(languageLevel)}) ---")
    
    # Determine effective language level (default to b1 if None or invalid)
    effective_language_level = languageLevel if languageLevel in {"a1", "a2", "b1", "b2", "c1"} else "b1"
    if languageLevel != effective_language_level:
         logger.info(f"DEBUG: languageLevel '{languageLevel}' invalid or missing, using default '{effective_language_level}'")
         
    try:
        # Log the request parameters
        logger.info(f"Token request from user {current_user.id} for character='{character_id}', level='{effective_language_level}'")
        
        # Get character config using the effective language level
        from src.features.sandbox.characters import get_character_config
        logger.info(f"Calling get_character_config with ID: '{character_id}', Level: '{effective_language_level}'")
        character_config = get_character_config(character_id, languageLevel=effective_language_level)
        
        # --- Log the EXACT config returned --- 
        logger.info(f"Config returned from get_character_config: {character_config}")
        
        instructions = character_config.get("system_prompt", "ERROR: System prompt missing in config!")
        character_voice_data = character_config.get("voice", {})
        character_voice = character_voice_data.get("voice_id", "alloy") # Default to alloy if missing
        
        # --- Log the values being sent to OpenAI --- 
        logger.info(f"Extracted Voice ID: {character_voice}")
        logger.info(f"Extracted Instructions (first 100 chars): {instructions[:100]}...")
        logger.info(f"Calling token_service.create_token with model={model}, voice={character_voice}")
        
        # Get token from OpenAI
        token_data = await token_service.create_token(
            model=model,
            voice=character_voice,
            instructions=instructions
        )
        
        logger.info(f"Generated OpenAI token for user {current_user.id}, character {character_id}, level {effective_language_level}")
        logger.info(f"--- EXITING get_realtime_token SUCCESSFULLY --- ")
        # Return raw JSON response
        return token_data
        
    except TokenError as e:
        logger.error(f"TOKEN_ERROR in get_realtime_token for char '{character_id}', level '{effective_language_level}': {str(e)}")
        if settings.DEBUG:
            detail = f"OpenAI token error: {str(e)}"
        else:
            detail = "Failed to generate OpenAI token"
        raise HTTPException(status_code=500, detail=detail)
        
    except Exception as e:
        logger.error(f"UNEXPECTED_ERROR in get_realtime_token for char '{character_id}', level '{effective_language_level}': {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        if settings.DEBUG:
            detail = f"Error: {str(e)}, Type: {type(e).__name__}"
        else:
            detail = "An unexpected error occurred"
        raise HTTPException(status_code=500, detail=detail)

@router.delete("/realtime/sessions/{session_id}", response_model=schemas.GenericResponse)
async def delete_realtime_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a realtime session from OpenAI.
    
    This endpoint is used to clean up resources when a WebRTC session is no longer needed.
    """
    try:
        # Delete the session
        success = await token_service.delete_session(session_id)
        
        if success:
            logger.info(f"Deleted OpenAI session {session_id} for user {current_user.id}")
            return {"status": "success", "message": "Session deleted successfully"}
        else:
            logger.warning(f"Failed to delete OpenAI session {session_id} for user {current_user.id}")
            return {"status": "warning", "message": "Failed to delete session, it may already be expired"}
            
    except Exception as e:
        logger.error(f"Error deleting OpenAI session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete OpenAI session"
        )

@router.get("/realtime/test-token", response_model=schemas.GenericResponse)
async def test_realtime_token(
    current_user: User = Depends(get_current_active_user)
):
    """Test endpoint to get a token and verify its format"""
    try:
        # Get token from OpenAI
        token_data = await token_service.create_token(
            model="gpt-4o-realtime-preview-2024-12-17",
            voice="verse"
        )
        
        # Extract and analyze token structure (accessing raw JSON structure)
        session_id = token_data.get("id")
        token_value = token_data.get("client_secret", {}).get("value", "")
        expires_at = token_data.get("client_secret", {}).get("expires_at", 0)
        
        # Analyze token format
        token_structure = {
            "session_id": session_id,
            "token_length": len(token_value),
            "token_first_5": token_value[:5] if token_value else "",
            "token_last_5": token_value[-5:] if token_value else "",
            "expires_at": expires_at,
            "expires_at_type": str(type(expires_at))
        }
        
        # Check for OpenAI project API key format
        is_project_key = token_value.startswith("sk-") if token_value else False
        token_structure["appears_to_be_api_key"] = "Yes" if token_value and token_value.startswith("sk-") else "No"
        token_structure["appears_to_be_jwt"] = "Yes" if token_value and token_value.startswith("eyJ") else "No"
        
        logger.info(f"Token test result: {json.dumps(token_structure, indent=2)}")
        
        return {
            "status": "success", 
            "message": f"Token format analysis completed, check logs for details. Session ID: {session_id}"
        }
        
    except Exception as e:
        logger.error(f"Error in token test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing token: {str(e)}"
        )

@router.get("/openai/token", include_in_schema=False)
async def openai_token_alias(
    character_id: str = "little-prince",
    model: str = "gpt-4o-realtime-preview",
    languageLevel: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Alias endpoint for /openai/token if frontend calls this directly."""
    logger.info(f"Handling alias request for /openai/token with character_id={character_id}, languageLevel={languageLevel}")
    # Directly call the main endpoint implementation, passing languageLevel
    return await get_realtime_token(
        character_id=character_id, 
        model=model, 
        languageLevel=languageLevel,
        current_user=current_user
    )

@router.get("/realtime/check-api-key", response_model=schemas.GenericResponse)
async def check_api_key(
    current_user: User = Depends(get_current_active_user)
):
    """Check API key configuration without exposing the actual key"""
    from src.core.config import settings
    
    # Get API key securely
    api_key = settings.OPENAI_API_KEY
    
    # Analyze API key format safely
    key_info = {
        "starts_with": api_key[:5] + "...",
        "length": len(api_key),
        "format": "Project key" if api_key.startswith("sk-proj-") else "User key" if api_key.startswith("sk-") else "Unknown format",
        "appears_valid": len(api_key) > 30 and (api_key.startswith("sk-") or api_key.startswith("eyJ")),
    }
    
    logger.info(f"API key analysis: {json.dumps(key_info, indent=2)}")
    
    return {
        "status": "success",
        "message": f"API key appears to be a {key_info['format']} of length {key_info['length']} characters"
    }

@router.get("/subtitles/docs", response_model=schemas.GenericResponse)
async def get_subtitle_docs(
    current_user: User = Depends(get_current_active_user)
):
    """Get documentation for using the subtitle WebSocket API"""
    
    # Base URL for connecting to the WebSocket
    hostname = settings.APP_HOSTNAME or "api.yourdomain.com"
    protocol = "wss" if not settings.DEBUG else "ws"
    base_url = f"{protocol}://{hostname}"
    
    # Construct the API documentation
    docs = {
        "status": "success",
        "message": "Subtitle WebSocket API documentation",
        "connection": {
            "url": f"{base_url}/subtitles?token=YOUR_JWT_TOKEN&session_id=YOUR_SESSION_ID",
            "description": "Connect to this WebSocket endpoint with your JWT token and session ID"
        },
        "message_types": {
            "send": [
                {
                    "type": "subtitle",
                    "fields": {
                        "content": "The subtitle text content",
                        "character": "The character name",
                        "timestamp": "Timestamp in milliseconds",
                        "messageId": "Optional reference to correlate with conversation"
                    },
                    "example": {
                        "type": "subtitle",
                        "content": "Hello, how are you today?",
                        "character": "little-prince",
                        "timestamp": 1634567890123,
                        "messageId": "abc-123-def-456"
                    }
                },
                {
                    "type": "GET_HISTORY",
                    "description": "Request conversation history for the current session",
                    "example": {
                        "type": "GET_HISTORY"
                    }
                }
            ],
            "receive": [
                {
                    "type": "SUBTITLE_STORED",
                    "description": "Acknowledgment that subtitle was stored",
                    "fields": {
                        "messageId": "The message ID that was stored"
                    }
                },
                {
                    "type": "conversation_hint",
                    "description": "Hints for responding to the character",
                    "fields": {
                        "content": "The hint content",
                        "timestamp": "Timestamp in milliseconds"
                    }
                },
                {
                    "type": "ERROR",
                    "description": "Error message",
                    "fields": {
                        "content": "Error description",
                        "messageId": "Optional reference to the message ID"
                    }
                },
                {
                    "type": "HISTORY",
                    "description": "Conversation history response",
                    "fields": {
                        "messages": "Array of messages in the conversation"
                    }
                }
            ]
        }
    }
    
    return docs 

@router.post("/start", response_model=schemas.SandboxStartResponse)
async def start_session(
    start_data: schemas.SandboxStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Starts or initializes a sandbox session for video chat.
    Ensures a session exists with the correct user, character, and language level.
    Returns the session details, including the ID needed for WebSocket connections.
    """
    logger.info(f"Received /start request for user {current_user.id}, character {start_data.character_id}, level {start_data.language_level}")
    try:
        # --- Basic Validation --- 
        # Check if character ID is known (using the map from characters.py)
        from src.features.sandbox.characters import CHARACTER_CONTEXT_MAP
        if start_data.character_id not in CHARACTER_CONTEXT_MAP:
             logger.warning(f"Unknown character_id '{start_data.character_id}' received in /start request.")
             # Optional: Raise error if character must be pre-defined
             # raise HTTPException(status_code=400, detail=f"Invalid character_id: {start_data.character_id}")
             # Or proceed, letting get_character_config handle defaults later
        
        # Validate language level (optional, Pydantic might handle basic types)
        valid_levels = {"a1", "a2", "b1", "b2", "c1"}
        if start_data.language_level.lower() not in valid_levels:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid language_level: {start_data.language_level}. Must be one of {valid_levels}."
            )
        # ------------------------

        # Instantiate service 
        # (Consider dependency injection for LLMClient if used by service)
        from src.shared.llm.client import LLMClient # Ensure LLMClient is available
        sandbox_service = service.SandboxService(LLMClient(), db) 

        # Generate a title for the session
        title = f"Video Chat with {start_data.characterName or f'Character {start_data.character_id}'} ({start_data.language_level})"

        # Always create a NEW session for this endpoint
        # We pass character_id but it's currently only used by create_session 
        # to fetch the *greeting*, not stored on the session model itself yet.
        # Language level IS stored.
        new_session = await sandbox_service.create_session(
            db=db, 
            user_id=current_user.id,
            title=title,
            character_id=start_data.character_id, # Used for greeting
            language_level=start_data.language_level.lower() # Store lowercase canonical level
        )

        # Format the response
        response_session_data = schemas.SandboxStartResponseSession(
            id=new_session.id,
            user_id=new_session.user_id,
            created_at=new_session.created_at, 
            updated_at=new_session.updated_at,
            is_active=new_session.is_active,
            companion_type=start_data.characterName or new_session.title, # Use the correct attribute name
            language_level=new_session.language_level,
            character_id=str(start_data.character_id) # Convert character_id back to string for response schema if needed
        )
        
        logger.info(f"Successfully started sandbox session {new_session.id} for character {start_data.character_id}, level {new_session.language_level}")
        return schemas.SandboxStartResponse(session=response_session_data)

    except HTTPException as http_exc:
        # Re-raise validation errors directly
        raise http_exc
    except Exception as e:
        logger.error(f"Error processing /start request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start session: {str(e)}"
        ) 

@router.websocket("/ws/{session_id}")
async def websocket_sandbox(websocket: WebSocket, session_id: str, token: str = None):
     token = websocket.query_params.get("token")
     await subtitle_websocket_endpoint(websocket, session_id, token) 