from fastapi import WebSocket, WebSocketDisconnect, Depends, Query
import json
import logging
from typing import Dict, Any, List, Optional, AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import traceback
import time
from uuid import uuid4
from urllib.parse import parse_qs # Need this for parsing
from sqlalchemy import select

from src.features.sandbox.service import SandboxService
from src.core.db import get_db, SessionLocal
from src.core.security import decode_jwt_token
from src.shared.websockets.manager import connection_manager

logger = logging.getLogger(__name__)

# --- Feature-Specific State for Debouncing ---
# These dictionaries are specific to the sandbox feature for handling subtitle debouncing.
# They are kept at the module level to manage state for this specific feature's WebSocket logic.

# Buffer to track the latest subtitle for each character in each session
subtitle_buffers: Dict[str, Dict[str, Dict[str, Any]]] = {}
# Tasks for debounced processing
processing_tasks: Dict[str, Dict[str, asyncio.Task]] = {}

async def disconnect_sandbox_user(session_id: str, user_id: str):
    """Custom disconnect logic for the sandbox feature to clean up processing tasks."""
    # Cancel any pending processing tasks for the user
    if session_id in processing_tasks and user_id in processing_tasks[session_id]:
        task = processing_tasks[session_id][user_id]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass  # Expected cancellation
        del processing_tasks[session_id][user_id]
        if not processing_tasks[session_id]:
            del processing_tasks[session_id]

    # Clean up subtitle buffer for the user
    if session_id in subtitle_buffers:
        # Construct the buffer key prefix for the user
        user_buffer_keys = [key for key in subtitle_buffers[session_id] if key.endswith(f"_{user_id}")]
        for key in user_buffer_keys:
            del subtitle_buffers[session_id][key]
        if not subtitle_buffers[session_id]:
            del subtitle_buffers[session_id]

    # Call the master disconnect
    await connection_manager.disconnect(session_id, user_id)
    logger.info(f"Cleaned up sandbox-specific resources for user {user_id} in session {session_id}")

async def buffer_subtitle(session_id: str, user_id: str, message: Dict[str, Any]):
    """Buffer a subtitle and schedule it for delayed processing to avoid processing partial transcriptions"""
    character = message.get("character", "unknown")
    buffer_key = f"{character}_{user_id}"
    
    # Ensure we have a buffer for this session and character
    if session_id not in subtitle_buffers:
        subtitle_buffers[session_id] = {}
    
    # Store the latest subtitle
    subtitle_buffers[session_id][buffer_key] = message
    
    # Cancel previous processing task if it exists
    if session_id in processing_tasks and user_id in processing_tasks[session_id]:
        task = processing_tasks[session_id][user_id]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
    # Create a new processing task with debounce delay
    if session_id not in processing_tasks:
        processing_tasks[session_id] = {}
        
    processing_tasks[session_id][user_id] = asyncio.create_task(
        _process_subtitle_after_delay(session_id, user_id, buffer_key, 1.5)  # 1.5 second debounce
    )
        
async def _process_subtitle_after_delay(session_id: str, user_id: str, buffer_key: str, delay: float):
    """Process the subtitle after a delay to allow for rapid updates to settle"""
    try:
        # Wait for the debounce period
        await asyncio.sleep(delay)
        
        # Get the latest subtitle from the buffer
        if (session_id in subtitle_buffers and 
            buffer_key in subtitle_buffers[session_id]):
            
            # Get the message and remove it from the buffer
            message = subtitle_buffers[session_id].pop(buffer_key, None)
            
            # Process the subtitle if a message was found
            if message:
                logger.info(f"Processing debounced subtitle from {buffer_key} in session {session_id}")
                await process_final_subtitle(session_id, user_id, message)

    except asyncio.CancelledError:
        # Task was cancelled, likely due to a newer subtitle
        pass
    except Exception as e:
        logger.error(f"Error in debounced subtitle processing: {str(e)}")
        logger.exception("Debounced processing error details:")

async def process_final_subtitle(session_id: str, user_id: str, message: Dict[str, Any]):
    """Process the final version of a subtitle after debouncing, including level-aware hints"""
    content = message.get("content", "")
    character_name_from_message = message.get("character", "unknown") # Get the name from the message
    timestamp = message.get("timestamp", int(time.time() * 1000))
    message_id = message.get("messageId", str(uuid4()))
    
    logger.info(f"Processing final subtitle: '{content}' from character_name '{character_name_from_message}'")

    # --- Map character name back to ID --- 
    from src.features.sandbox.characters import get_character_config, CHARACTER_NAME_TO_ID_MAP
    from src.features.sandbox.service import SandboxService # Import service for session retrieval
    from src.features.sandbox.models import SandboxSession # Import model for type hint
    from src.shared.llm.client import LLMClient # Import LLMClient
    
    character_id_for_config = CHARACTER_NAME_TO_ID_MAP.get(character_name_from_message)
    if not character_id_for_config:
        logger.warning(f"Could not map character name '{character_name_from_message}' to an ID. Falling back to using the name itself.")
        character_id_for_config = character_name_from_message 
    else:
        logger.info(f"DEBUG: Mapped character name '{character_name_from_message}' to ID '{character_id_for_config}' for config lookup.")
    # --------------------------------------------

    # Generate a conversation hint using LLM - with database access for level
    llm_client: LLMClient = None # Reuse client if possible
    try:
        # Create a dedicated DB session scope for this background task
        async with SessionLocal() as db:

            # Create LLM client (Consider reusing one if performance becomes an issue)
            llm_client = LLMClient()

            # --- Fetch Session Language Level --- 
            # Use explicit select instead of db.get to potentially mitigate transaction visibility issues
            stmt = select(SandboxSession).where(SandboxSession.id == session_id)
            result = await db.execute(stmt)
            sandbox_session = result.scalar_one_or_none()

            if not sandbox_session:
                logger.warning(f"Could not find SandboxSession {session_id} to get language level. Defaulting to b1 for hints.")
                language_level = "b1"
            else:
                language_level = sandbox_session.language_level
                logger.info(f"Retrieved language level '{language_level}' from session {session_id} for hint generation.")
            # -------------------------------------
            
            # Get character configuration using the mapped ID and session language level
            character_config = get_character_config(
                character_id=character_id_for_config, 
                languageLevel=language_level
            )
            
            # Use the hint_prompt from the config
            hint_prompt = character_config.get("hint_prompt", f"You are an assistant helping someone practice conversation with {character_name_from_message}. Provide a short hint on how to respond.")
            
            # Create a conversation context with just this subtitle
            conversation = [
                {"role": "system", "content": hint_prompt},
                # Use original character name from message in user prompt for context
                {"role": "user", "content": f"Analyze the following message from {character_name_from_message} and provide ONE helpful hint that directly responds to what was just said: \"{content}\"\n\nFormat the hint as instructed in the system prompt."}
            ]
            
            # Generate hint using LLM
            logger.info(f"[_process_final_subtitle] Sending conversation to hint LLM: {json.dumps(conversation)}")
            raw_hint = await llm_client.generate_text(json.dumps(conversation))
            logger.info(f"[_process_final_subtitle] Raw response from hint LLM: {raw_hint}")
            
            # --- Simplified Hint Parsing (like Story Mode) --- 
            hints = [line.strip() for line in raw_hint.split('\n') if line.strip()]
            logger.info(f"[_process_final_subtitle] Parsed hints: {hints}")
            
            # Use the first hint if available, otherwise generate fallback
            if hints:
                hint_content = hints[0] # Take the first line as the hint
            else:
                logger.warning(f"Hint LLM returned empty response or parsing failed. Using fallback hint.")
                # Generate a context-aware fallback hint based on whether the last message was a question
                if content and "?" in content:
                    hint_content = f'"You can answer {character_name_from_message}\'s question using present tense. \"I think...\""'
                else:
                    hint_content = f'"You can respond to what {character_name_from_message} said using present tense. \"I agree that...\""'
            # --------------------------------------------------
            
            # Send the hint (within the DB session scope, although not strictly necessary for sending)
            hint_response = {
                "type": "conversation_hint",
                "content": hint_content, # Send the single processed hint
                "timestamp": int(time.time() * 1000)
            }
            logger.info(f"Sending LLM-generated conversation hint: {json.dumps(hint_response)}")
            await connection_manager.send_message(
                session_id,
                user_id,
                hint_response
            )
            logger.info(f"Sent conversation hint for final subtitle")

    except Exception as hint_error:
        logger.error(f"Error generating LLM hint: {str(hint_error)}")
        logger.exception("Hint generation error details:")
        # Fallback hint generation remains the same
        try:
            words = content.split()
            topic_words = " ".join(words[:3]) if len(words) > 3 else content
            fallback_hint_content = f"\"You can respond to what was said about '{topic_words}...' using present tense.\""
            await connection_manager.send_message(
                session_id,
                user_id,
                {
                    "type": "conversation_hint",
                    "content": fallback_hint_content,
                    "timestamp": int(time.time() * 1000)
                }
            )
            logger.info(f"Sent fallback conversation hint for final subtitle")
        except Exception as fallback_err:
            logger.error(f"Even fallback hint generation failed: {fallback_err}")
    finally:
        # Clean up LLM client resources if needed
        if llm_client and hasattr(llm_client, 'close') and callable(llm_client.close):
            await llm_client.close()
        # DB session is closed by the context manager `get_db_session_for_ws`

async def process_websocket_message(
    websocket: WebSocket, 
    session_id: str, 
    user_id: str, 
    message: Dict[str, Any]
):
    """Process WebSocket messages from clients according to frontend protocol"""
    msg_type = message.get("type", "")
    
    if not msg_type:
        await connection_manager.send_message(
            session_id,
            user_id,
            {
                "type": "ERROR",
                "content": "Message type not specified",
                "timestamp": int(time.time() * 1000)
            }
        )
        return
    
    # Log message receipt for debugging
    logger.info(f"Processing message type '{msg_type}' from user {user_id} in session {session_id}")
    
    # Handle different message types
    try:
        # Handle connection_test (ping) messages
        if msg_type == "connection_test":
            ping_id = message.get("id", str(uuid4()))
            current_timestamp = int(time.time() * 1000)
            logger.info(f"Received ping (id: {ping_id}) from user {user_id}")
            
            # Send pong response
            pong_response = {
                "type": "pong",
                "timestamp": current_timestamp,
                "id": ping_id
            }
            
            logger.info(f"Sending pong response: {json.dumps(pong_response)}")
            await connection_manager.send_message(
                session_id,
                user_id,
                pong_response
            )
            logger.info(f"Sent pong response (id: {ping_id}) to user {user_id}")
            return
            
        # Handle subtitle type from frontend
        elif msg_type == "subtitle":
            # Extract message data
            content = message.get("content", "")
            message_id = message.get("messageId", str(uuid4()))
            
            if not content:
                await connection_manager.send_message(
                    session_id,
                    user_id,
                    {
                        "type": "ERROR",
                        "messageId": message_id,
                        "content": "Subtitle content is empty",
                        "timestamp": int(time.time() * 1000)
                    }
                )
                return
            
            # Send immediate acknowledgment per the required protocol
            ack_response = {
                "type": "ack",
                "messageId": message_id,
                "timestamp": int(time.time() * 1000)
            }
            logger.info(f"Sending ack: {json.dumps(ack_response)}")
            await connection_manager.send_message(
                session_id,
                user_id,
                ack_response
            )
            logger.info(f"Sent ack for message {message_id}")
            
            # Buffer the subtitle and process it after debouncing
            await buffer_subtitle(session_id, user_id, message)
            logger.info(f"Buffered subtitle for debounced processing: '{content[:50]}...'")
        
        # Handle GET_HISTORY type for retrieving chat history (kept from original implementation)
        elif msg_type == "GET_HISTORY":
            async with SessionLocal() as db:
                try:
                    # Get all messages for this session
                    messages = await sandbox_service.get_session_messages(db, session_id)
                    
                    # Format messages for the frontend
                    formatted_messages = []
                    for msg in messages:
                        formatted_messages.append({
                            "messageId": msg.message_id,
                            "role": msg.role,
                            "content": msg.content,
                            "timestamp": int(msg.created_at.timestamp() * 1000),
                            "character": msg.character_id,
                            "isComplete": msg.is_complete
                        })
                    
                    # Send message history
                    await connection_manager.send_message(
                        session_id,
                        user_id,
                        {
                            "type": "HISTORY",
                            "messages": formatted_messages
                        }
                    )
                
                except Exception as e:
                    logger.error(f"Error retrieving message history: {str(e)}")
                    logger.exception("History retrieval error details:")
                    
                    await connection_manager.send_message(
                        session_id,
                        user_id,
                        {
                            "type": "ERROR",
                            "content": f"Failed to retrieve message history: {str(e)}"
                        }
                    )
        
        # Handle unsupported message types
        else:
            logger.warning(f"Unsupported message type: {msg_type}")
            await connection_manager.send_message(
                session_id,
                user_id,
                {
                    "type": "ERROR",
                    "content": f"Unsupported message type: {msg_type}",
                    "timestamp": int(time.time() * 1000)
                }
            )

    except Exception as e:
        logger.error(f"Unhandled error in websocket message processing: {str(e)}")
        error_details = traceback.format_exc()
        logger.error(f"Error details: {error_details}")
        
        message_id = message.get("messageId", str(uuid4()))
        await connection_manager.send_message(
            session_id,
            user_id,
            {
                "type": "ERROR",
                "messageId": message_id,
                "content": f"An unexpected error occurred: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }
        )

async def subtitle_websocket_endpoint(
    websocket: WebSocket,
    # Keep Query params for potential future use or if manual parsing fails
    session_id_query: Optional[str] = Query(None, alias="sessionId"), 
    token: Optional[str] = Query(None) 
):
    # <<< Manually parse session_id from raw query string >>>
    session_id = None
    try:
        query_string = websocket.scope.get('query_string', b'').decode()
        logger.info(f"[websocket_endpoint] Raw query string: {query_string}")
        parsed_params = parse_qs(query_string)
        # parse_qs returns a list for each value, get the first element
        if 'sessionId' in parsed_params:
            session_id = parsed_params['sessionId'][0]
        logger.info(f"[websocket_endpoint] Manually parsed session_id: {session_id}")
    except Exception as e:
        logger.error(f"[websocket_endpoint] Error parsing query string: {e}")
        session_id = None # Ensure session_id is None if parsing fails

    # Fallback to FastAPI binding if manual parsing failed (optional, for debugging)
    if not session_id and session_id_query:
         logger.warning(f"[websocket_endpoint] Manual parsing failed, falling back to FastAPI bound session_id: {session_id_query}")
         session_id = session_id_query

    # Check if session_id was actually found
    if not session_id:
        logger.error("[websocket_endpoint] CRITICAL: session_id not found in query parameters! Closing connection.")
        await websocket.close(code=1008, reason="Missing session_id")
        return

    # Verify token and get user if provided
    user_id = None
    
    try:
        # If token is provided, try to decode it
        if token:
            try:
                payload = decode_jwt_token(token)
                user_id = payload.get("user_id")
                logger.info(f"Authenticated WebSocket connection for user {user_id}")
            except Exception as e:
                logger.warning(f"Invalid token provided: {str(e)}")
                # Continue with anonymous user
        
        # If no valid user_id from token, use an anonymous ID
        if not user_id:
            user_id = f"anon-{str(uuid4())[:8]}"
            logger.info(f"Anonymous WebSocket connection assigned ID: {user_id}")
        
        # Note: websocket.accept() is now handled in the main.py route handler
        # to ensure we can send debug messages before any errors
        
        # Log connection
        logger.info(f"Subtitle WebSocket connected: user {user_id} for session {session_id}")
        
        # Register the connection with the manager
        await connection_manager.connect(websocket, session_id, user_id)
        
        # Send an initial connection confirmation
        await connection_manager.send_message(
            session_id,
            user_id,
            {
                "type": "connected",
                "timestamp": int(time.time() * 1000),
                "message": "Connection established with subtitle service"
            }
        )
        
        try:
            while True:
                # Wait for messages from client
                data = await websocket.receive()
                
                # Log raw message for debugging
                logger.info(f"Raw message received: {str(data)[:200]}...")
                
                # FastAPI/Starlette WebSockets wrap messages in a structure with type 'websocket.receive'
                if data.get("type") == "websocket.receive":
                    text_data = data.get("text", "{}")
                    logger.info(f"Text message content: {text_data[:200]}...")
                    
                    try:
                        # Parse the actual message from the text field
                        message = json.loads(text_data)
                        logger.info(f"Parsed JSON message: {str(message)[:200]}...")
                        
                        # Process the parsed message
                        await process_websocket_message(websocket, session_id, user_id, message)
                    except json.JSONDecodeError as json_err:
                        logger.error(f"Failed to parse JSON message: {str(json_err)}")
                        logger.error(f"Invalid JSON: {text_data[:200]}")
                        await connection_manager.send_message(
                            session_id,
                            user_id,
                            {
                                "type": "ERROR",
                                "content": "Invalid JSON format",
                                "timestamp": int(time.time() * 1000)
                            }
                        )
                    except Exception as process_err:
                        logger.error(f"Error processing message: {str(process_err)}")
                        logger.exception("Message processing error details:")
                        await connection_manager.send_message(
                            session_id,
                            user_id,
                            {
                                "type": "ERROR",
                                "content": f"Error processing message: {str(process_err)}",
                                "timestamp": int(time.time() * 1000)
                            }
                        )
                elif data.get("type") == "websocket.disconnect":
                    logger.info(f"WebSocket disconnect message received")
                    break
                else:
                    logger.warning(f"Received unknown message type: {data.get('type')}")
                
        except WebSocketDisconnect:
            logger.info(f"Subtitle WebSocket disconnected: user {user_id} for session {session_id}")
            await disconnect_sandbox_user(session_id, user_id)
        
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"Subtitle WebSocket error: {str(e)}\n{error_details}")
            await disconnect_sandbox_user(session_id, user_id)
            
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Subtitle WebSocket connection error: {str(e)}\n{error_details}")
        try:
            await websocket.close(code=1008, reason="Connection error")
        except:
            pass  # Already closed 