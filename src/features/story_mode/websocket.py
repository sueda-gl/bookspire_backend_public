from fastapi import WebSocket, WebSocketDisconnect, Depends
import json
import logging
from typing import Dict, Any, List, Optional
import asyncio
import traceback
import time
import re
import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.story_mode.service import StoryService
from src.shared.websockets.manager import connection_manager
from src.features.story_mode.characters import get_character_config
from src.core.db import get_db, SessionLocal
from src.shared.llm.client import LLMClient
from src.core.security import decode_jwt_token
from src.shared.dependencies import get_message_processor
from src.shared.message_processing.service import MessageProcessingService

logger = logging.getLogger(__name__)

# Helper function to safely get the message processor
def get_message_processor_safely(websocket: WebSocket) -> Optional[MessageProcessingService]:
    """
    Safely retrieve the message processor from app state.
    
    This is a fallback mechanism for when dependency injection fails,
    which can happen in WebSocket contexts.
    
    Args:
        websocket: The active WebSocket connection
        
    Returns:
        MessageProcessingService or None if not available
    """
    try:
        # First, check if it exists in app state
        if hasattr(websocket, 'app') and hasattr(websocket.app, 'state'):
            if hasattr(websocket.app.state, 'message_processor'):
                processor = websocket.app.state.message_processor
                logger.info(f"Successfully retrieved message processor from app state: {type(processor)}")
                return processor
        
        # Alternative approach as fallback - try to recreate the processor
        try:
            from src.shared.dependencies import get_message_processor
            from src.shared.llm.client import LLMClient
            
            # Create a new LLM client specifically for message processing
            temp_llm_client = LLMClient()
            processor = MessageProcessingService(temp_llm_client)
            
            logger.info(f"Created new message processor with dedicated LLM client: {type(processor)}")
            return processor
        except Exception as create_err:
            logger.error(f"Failed to create message processor: {str(create_err)}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting message processor: {str(e)}")
        return None

async def process_websocket_message(
    websocket: WebSocket, 
    session_id: str, 
    user_id: str, 
    message: Dict[str, Any],
    llm_client: LLMClient,
    message_processor: MessageProcessingService
):
    """Process WebSocket messages from clients using shared services"""
    msg_type = message.get("type", "")
    message_id = message.get("messageId", str(uuid4()))
    
    if not msg_type:
        try:
            await connection_manager.send_message(
                session_id,
                user_id,
                {
                    "type": "ERROR",
                    "messageId": message_id,
                    "content": "Message type not specified"
                }
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {str(e)}")
        return
    
    try:
        if websocket.client_state.name != "CONNECTED":
            return
        
        if not user_id in connection_manager.active_connections.get(session_id, {}):
            return

        async with SessionLocal() as db:
            story_service = StoryService(llm_client, db)
            
            if msg_type == "USER_MESSAGE":
                content = message.get("content", "")
                character_id = message.get("characterId", "little-prince")
                
                if not content:
                    await connection_manager.send_message(session_id, user_id, {"type": "ERROR", "messageId": message_id, "content": "Message content is empty"})
                    return
                
                processing_task = None
                if message_processor:
                    processing_message_id = f"{session_id}_{character_id}_{message_id}_{datetime.datetime.now().isoformat()}"
                    processing_task = asyncio.create_task(
                        process_message_in_own_session(message_processor, processing_message_id, content, user_id, "story_mode", session_id, character_id, websocket)
                    )

                await story_service.save_message(session_id, "user", content, message_id, character_id)
                conversation = await story_service.get_conversation(session_id)
                assistant_message = ""
                async for chunk in story_service.stream_character_response(session_id, conversation, character_id):
                    if websocket.client_state.name != "CONNECTED":
                        raise WebSocketDisconnect()
                    assistant_message += chunk
                    await connection_manager.send_message(session_id, user_id, {"type": "MESSAGE_CHUNK", "messageId": message_id, "content": chunk, "isComplete": False, "timestamp": int(time.time() * 1000), "character": character_id})

                if websocket.client_state.name == "CONNECTED":
                    await connection_manager.send_message(session_id, user_id, {"type": "MESSAGE_CHUNK", "messageId": message_id, "content": "", "isComplete": True, "timestamp": int(time.time() * 1000), "character": character_id})

                if assistant_message:
                    await story_service.save_message(session_id, "assistant", assistant_message, message_id, character_id)

                if processing_task:
                    await processing_task

                if websocket.client_state.name == "CONNECTED":
                    hints = await story_service.generate_hints(session_id)
                    await connection_manager.send_message(session_id, user_id, {"type": "HINTS", "messageId": message_id, "hints": hints, "timestamp": int(time.time() * 1000)})
            
            elif msg_type == "GREETING":
                character_id = message.get("characterId", "little-prince")
                title = message.get("title")
                session_exists = await story_service.session_exists(session_id)
                if not session_exists:
                    await story_service.create_session(int(user_id), title, character_id)
                    character = get_character_config(character_id)
                    greeting = character["greeting"]
                    await story_service.save_message(session_id, "assistant", greeting, message_id, character_id)
                    await connection_manager.send_message(session_id, user_id, {"type": "MESSAGE_CHUNK", "messageId": message_id, "content": greeting, "isComplete": True, "timestamp": int(time.time() * 1000), "character": character_id})
                    hints = await story_service.generate_initial_hints(session_id)
                    await connection_manager.send_message(session_id, user_id, {"type": "HINTS", "messageId": message_id, "hints": hints, "timestamp": int(time.time() * 1000)})
                else:
                    conversation_history = await story_service.get_session_messages(session_id)
                    if conversation_history:
                        recent_message = conversation_history[-1]
                        await connection_manager.send_message(session_id, user_id, {"type": "MESSAGE_CHUNK", "messageId": recent_message.message_id, "content": recent_message.content, "isComplete": True, "timestamp": int(time.time() * 1000), "character": recent_message.character_id})
                        latest_hints = await story_service.get_latest_hints(session_id)
                        hint_texts = [hint.content for hint in latest_hints]
                        await connection_manager.send_message(session_id, user_id, {"type": "HINTS", "messageId": recent_message.message_id, "hints": hint_texts, "timestamp": int(time.time() * 1000)})

    except (WebSocketDisconnect, asyncio.CancelledError):
        raise
    except Exception as e:
        logger.error(f"Error processing WebSocket message: {str(e)}")
        logger.exception("Details:")
        if websocket.client_state.name == "CONNECTED":
            await connection_manager.send_message(session_id, user_id, {"type": "ERROR", "messageId": message_id, "content": f"Server error: {str(e)}"})

async def process_message_in_own_session(
    message_processor, message_id, text, user_id, feature, session_id=None, character_id=None, websocket=None
) -> Any:
    """
    Process a message with its own independent database session.
    
    If session_id, character_id, and websocket are provided, this function can send
    immediate notifications for inappropriate content directly to the client.
    
    Parameters:
    - message_processor: The message processing service
    - message_id: Unique identifier for the message
    - text: The message text to process
    - user_id: Current user identifier
    - feature: The feature using this processor (e.g., "story_mode")
    - session_id: Optional WebSocket session ID for immediate notifications
    - character_id: Optional character ID for the message context
    - websocket: Optional WebSocket connection for immediate streaming
    
    Returns:
    - Processing result object
    """
    if not message_processor or not hasattr(message_processor, 'process_message'):
        logger.error(f"Invalid message processor provided: {type(message_processor)}")
        from src.shared.message_processing.schemas import ProcessingResult
        return ProcessingResult(
            message_id=message_id,
            is_appropriate=True,
            corrected_text=text,
            grammar_feedback="Message processing unavailable.",
            processed_at=datetime.datetime.now()
        )
    
    processing_result = None
    
    async with SessionLocal() as proc_db:
        try:
            logger.info(f"Processing message {message_id} in its own database session")
            logger.info(f"Message processor type: {type(message_processor)}")
            
            processing_result = await message_processor.process_message(
                db=proc_db,
                message_id=message_id,
                text=text,
                user_id=user_id,
                feature=feature
            )
        except Exception as e:
            logger.error(f"Error in isolated message processing: {str(e)}")
            logger.exception("Details:")
            
            from src.shared.message_processing.schemas import ProcessingResult
            processing_result = ProcessingResult(
                message_id=message_id,
                is_appropriate=True,
                corrected_text=text,
                grammar_feedback="Error in message processing.",
                processed_at=datetime.datetime.now()
            )
    
    if processing_result and session_id and character_id and websocket:
        if not processing_result.is_appropriate:
            try:
                logger.info(f"🚨 Message {message_id} flagged as inappropriate, sending notification")
                
                await asyncio.create_task(
                    send_moderation_notification(
                        websocket,
                        session_id,
                        user_id,
                        character_id,
                        processing_result.inappropriate_reason
                    )
                )
            except Exception as ws_error:
                logger.error(f"Error sending inappropriate content notification: {str(ws_error)}")
                logger.exception("WebSocket notification error details:")
        
        if processing_result.corrected_text and processing_result.corrected_text != text:
            try:
                logger.info(f"📝 Grammar corrections available for message {message_id}")
                
                await asyncio.create_task(
                    send_grammar_suggestion(
                        websocket,
                        session_id,
                        user_id,
                        text,
                        processing_result.corrected_text,
                        processing_result.grammar_feedback
                    )
                )
            except Exception as ws_error:
                logger.error(f"Error sending grammar suggestion: {str(ws_error)}")
                logger.exception("WebSocket notification error details:")
    
    return processing_result

async def send_moderation_notification(
    websocket, session_id, user_id, character_id, reason=None
):
    """
    Send moderation notifications through WebSocket.
    This function is completely isolated from any database operations.
    
    Parameters:
    - websocket: The WebSocket connection
    - session_id: Current session identifier 
    - user_id: Current user identifier
    - character_id: Character identifier
    - reason: Reason for moderation, if any
    """
    try:
        await websocket.send_json({
            "type": "CONTENT_MODERATION",
            "messageId": str(uuid4()),
            "character": character_id,
            "is_appropriate": False,
            "message": "⚠️ This content may violate our community guidelines and has been flagged for review.",
            "reason": reason or "Content flagged as inappropriate",
            "timestamp": int(time.time() * 1000)
        })
        
        await connection_manager.send_message(
            session_id,
            user_id,
            {
                "type": "MODERATION_NOTICE",
                "character": character_id,
                "message": "This message has been logged due to potential policy violations",
                "reason": reason or "Content flagged as inappropriate",
                "timestamp": int(time.time() * 1000)
            }
        )
        
        logger.info(f"Moderation notifications sent for character {character_id}")
    except Exception as e:
        logger.error(f"Failed to send moderation notification: {str(e)}")
        logger.exception("Notification error details:")

async def send_grammar_suggestion(
    websocket, session_id, user_id, original_text, suggested_text, feedback
):
    """
    Send grammar suggestions through WebSocket.
    This function is completely isolated from any database operations.
    
    Parameters:
    - websocket: The WebSocket connection
    - session_id: Current session identifier
    - user_id: Current user identifier
    - original_text: The original message text
    - suggested_text: The corrected message text
    - feedback: Explanation of corrections
    """
    try:
        await connection_manager.send_message(
            session_id,
            user_id,
            {
                "type": "GRAMMAR_SUGGESTION",
                "messageId": str(uuid4()),
                "original_text": original_text,
                "suggested_text": suggested_text,
                "feedback": feedback or "Grammar improvements suggested",
                "timestamp": int(time.time() * 1000)
            }
        )
        
        logger.info(f"Grammar suggestion sent for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send grammar suggestion: {str(e)}")
        logger.exception("Notification error details:")

async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: str, 
    token: str
):
    """WebSocket endpoint for real-time story mode interactions"""
    # Get shared services from the application state
    llm_client = websocket.app.state.llm_client
    message_processor = websocket.app.state.message_processor
    
    # Validate token and extract user ID
    try:
        payload = decode_jwt_token(token)
        
        # Extract user_id correctly - previously was extracting username from 'sub'
        # First try to get the user_id directly (numeric)
        user_id = payload.get("user_id")
        
        # If user_id is not present, fall back to 'sub' (username) for backward compatibility
        if user_id is None:
            username = payload.get("sub")
            logger.warning(f"JWT token missing user_id field, using username '{username}' as user identifier")
            user_id = str(username)
        
        if not user_id:
            await websocket.close(code=1008, reason="Invalid authentication")
            return
            
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {str(e)}")
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    pending_tasks = set()
    await connection_manager.connect(websocket, session_id, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            task = asyncio.create_task(
                process_websocket_message(
                    websocket, 
                    session_id, 
                    user_id, 
                    message,
                    llm_client,
                    message_processor
                )
            )
            
            task.add_done_callback(lambda t: pending_tasks.discard(t))
            pending_tasks.add(task)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: user {user_id} from session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        logger.exception("Details:")
    finally:
        logger.info(f"Starting cleanup for WebSocket endpoint {session_id}")
        for task in pending_tasks:
            if not task.done() and not task.cancelled():
                task.cancel()
        
        if pending_tasks:
            await asyncio.wait(pending_tasks, timeout=2.0)
        
        await connection_manager.disconnect(session_id, user_id)
        logger.info(f"WebSocket endpoint cleanup completed for session {session_id}")