from fastapi import WebSocket, WebSocketDisconnect, Depends
import json
import logging
from typing import Dict, Set, Any
import asyncio
import traceback
from datetime import datetime
import sqlalchemy.exc

from src.features.journey.service import JourneyService
from src.core.db import get_db, SessionLocal
from src.shared.llm.client import LLMClient
from src.shared.dependencies import get_message_processor
from src.shared.message_processing.service import MessageProcessingService
from src.shared.websockets.manager import connection_manager

logger = logging.getLogger(__name__)

async def process_websocket_message(websocket: WebSocket, session_id: str, user_id: str, message: Dict[str, Any], llm_client: LLMClient, message_processor: MessageProcessingService):
    """
    Process a single WebSocket message with its own database session.
    
    This function implements a parallel processing approach:
    1. User responses are immediately saved and evaluated using the original text
    2. Content moderation and grammar checking happen in parallel without blocking evaluation
    3. After evaluation, moderation results are checked and notifications are sent as needed
    
    This approach ensures:
    - No delay in processing legitimate content while waiting for moderation
    - Original text is always used for evaluation
    - Grammar suggestions are provided separately from content evaluation
    - Inappropriate content is immediately flagged in the stream to users
    - Inappropriate content is still logged and flagged, but doesn't block the user experience
    
    Both the original text and any corrections are stored in separate databases:
    - Journey database stores the original user text for evaluation
    - Message Processing database stores both original and corrected versions
    
    Parameters:
    - websocket: The WebSocket connection
    - session_id: Current session identifier
    - user_id: Current user identifier
    - message: The WebSocket message to process
    - llm_client: The LLM client for generating evaluations
    - message_processor: Service for content moderation and grammar checking
    """
    msg_type = message.get("type")
    
    # Log the beginning of message processing
    logger.info(f"Processing WebSocket message type: {msg_type} for user {user_id}")
    
    try:
        # Create service with the existing LLM client - doesn't need a database session yet
        journey_service = JourneyService(llm_client)
        
        if msg_type == "get_question":
            # Get next question with its own session
            await get_next_question_in_session(journey_service, session_id, user_id)
        
        elif msg_type == "submit_response":
            # Extract response data
            question_id = message.get("data", {}).get("question_id")
            response_text = message.get("data", {}).get("response_text")
            should_stream = message.get("data", {}).get("stream", False) 
            
            if not question_id or not response_text:
                await connection_manager.send_message(
                    session_id,
                    user_id,
                    {
                        "type": "error",
                        "data": {"message": "Missing question_id or response_text"}
                    }
                )
                return
            
            # Generate a unique message ID
            message_id = f"{session_id}_{question_id}_{datetime.now().isoformat()}"
            logger.info(f"Starting parallel processing for message {message_id}")
            
            try:
                # Process steps with separate, independent database sessions
                processing_result = None
                response_data = None
                evaluation_result = None
                
                # Step 1: Start message processing in its own task with its own session
                # Pass WebSocket information for immediate inappropriate content notifications
                processing_task = asyncio.create_task(
                    process_message_in_own_session(
                        message_processor, 
                        message_id, 
                        response_text, 
                        user_id, 
                        "journey",
                        session_id,      # Pass session_id for immediate notifications
                        question_id,     # Pass question_id for immediate notifications
                        websocket        # Pass websocket for immediate notifications
                    )
                )
                
                # Step 2: Save the response in its own session - complete this operation fully
                try:
                    response_data = await save_and_evaluate_response(
                        journey_service,
                        session_id,
                        question_id,
                        response_text,
                        should_stream,
                        websocket,
                        user_id
                    )
                    
                    # Step 3: Send confirmation of received response
                    await connection_manager.send_message(
                        session_id,
                        user_id,
                        {
                            "type": "response_received",
                            "data": {
                                "response_id": response_data["id"],
                                "question_id": question_id
                            }
                        }
                    )
                except Exception as save_error:
                    logger.error(f"Error saving response: {str(save_error)}")
                    logger.exception("Save response error details:")
                    await connection_manager.send_message(
                        session_id,
                        user_id,
                        {
                            "type": "error",
                            "data": {"message": f"Error saving your response: {str(save_error)}"}
                        }
                    )
                    # Don't proceed with evaluation if we couldn't save the response
                    raise
                
                # Step 4: Evaluate response - complete this fully before proceeding
                # IMPORTANT: Do not create a task for this, to maintain SQLAlchemy greenlet context
                if response_data:
                    try:
                        logger.info(f"Starting evaluation with original text for message {message_id}")
                        evaluation_result = await evaluate_response_in_session(
                            journey_service,
                            response_data,
                            session_id,
                            user_id,
                            should_stream,
                            websocket
                        )
                    except Exception as eval_error:
                        logger.error(f"Error evaluating response: {str(eval_error)}")
                        logger.exception("Evaluation error details:")
                        await connection_manager.send_message(
                            session_id,
                            user_id,
                            {
                                "type": "error",
                                "data": {"message": f"Error evaluating your response: {str(eval_error)}"}
                            }
                        )
                        # Continue processing even if evaluation fails
                
                # Step 5: Wait for message processing results
                try:
                    logger.info(f"Waiting for message processing results for {message_id}")
                    processing_result = await processing_task
                    
                    # Log detailed processing results for debugging
                    if processing_result:
                        logger.info(f"Message processing complete for {message_id}:")
                        logger.info(f"  - Is appropriate: {processing_result.is_appropriate}")
                        
                        # Handle inappropriate content - this is now redundant with immediate notifications
                        # but we keep it for consistency and in case the immediate notification failed
                        if not processing_result.is_appropriate:
                            logger.info(f"  - Inappropriate reason: {processing_result.inappropriate_reason}")
                            logger.warning(f"Message {message_id} flagged as inappropriate: {processing_result.inappropriate_reason}")
                            
                            # Send moderation notice (may be a duplicate of the immediate notification)
                            await connection_manager.send_message(
                                session_id,
                                user_id,
                                {
                                    "type": "moderation_notice",
                                    "data": {
                                        "question_id": question_id,
                                        "message": "This message has been logged due to potential policy violations",
                                        "reason": processing_result.inappropriate_reason or "Content flagged as inappropriate"
                                    }
                                }
                            )
                        
                        # Handle grammar corrections
                        if processing_result.corrected_text != response_text:
                            logger.info(f"Grammar corrections available for message {message_id}")
                            logger.info(f"Original: '{response_text}'")
                            logger.info(f"Corrected: '{processing_result.corrected_text}'")
                            logger.info(f"Feedback: {processing_result.grammar_feedback}")
                            
                            # Send grammar suggestions
                            await connection_manager.send_message(
                                session_id,
                                user_id,
                                {
                                    "type": "grammar_suggestion",
                                    "data": {
                                        "question_id": question_id,
                                        "original_text": response_text,
                                        "suggested_text": processing_result.corrected_text,
                                        "feedback": processing_result.grammar_feedback or "Grammar improvements suggested"
                                    }
                                }
                            )
                            logger.info(f"Grammar suggestion sent for message {message_id}")
                    else:
                        logger.warning(f"Message processing task completed but returned None for {message_id}")
                
                except Exception as proc_error:
                    logger.error(f"Error processing message content: {str(proc_error)}")
                    logger.exception("Message processing error details:")
                    # Continue processing even if message processing fails
                
                # Step 6: Skip session statistics calculation (moved to frontend)
                # We've removed this step as it was causing greenlet context issues
                # and the functionality has been moved to the frontend
                
                # Step 7: Always get next question after processing a response
                try:
                    await get_next_question_in_session(
                        journey_service,
                        session_id,
                        user_id
                    )
                except Exception as question_error:
                    logger.error(f"Error getting next question: {str(question_error)}")
                    logger.exception("Next question error details:")
                    # This is the end of our processing, so we should report the error to the client
                    await connection_manager.send_message(
                        session_id,
                        user_id,
                        {
                            "type": "error",
                            "data": {"message": "Could not retrieve the next question. Please refresh the page."}
                        }
                    )
            
            except Exception as e:
                error_details = traceback.format_exc()
                logger.error(f"Error processing response: {str(e)}\n{error_details}")
                await connection_manager.send_message(
                    session_id,
                    user_id,
                    {
                        "type": "error",
                        "data": {"message": f"Error processing response: {str(e)}"}
                    }
                )
                
    except Exception as e:
        # Log detailed error
        error_details = traceback.format_exc()
        logger.error(f"Error processing message: {str(e)}\n{error_details}")
        
        # Notify client of error
        await connection_manager.send_message(
            session_id,
            user_id,
            {
                "type": "error",
                "data": {"message": f"Error processing message: {str(e)}"}
            }
        )

async def stream_evaluation(db, journey_service, session_id, user_id, response_id, websocket):
    """
    Stream the evaluation results back to the client in chunks as they become available.
    Note: The text content is the original user response, not the corrected version.
    This function is called with its own database session to prevent conflicts.
    
    If the response was previously flagged as inappropriate, this will add a notice
    about moderation in the evaluation stream as well.
    
    Parameters:
    - db: The database session (already created by the caller)
    - journey_service: The service for evaluating responses
    - session_id: Current session identifier
    - user_id: Current user identifier
    - response_id: The ID of the response to evaluate
    - websocket: The WebSocket connection for sending chunks
    
    Returns:
    - Evaluation results (score, feedback, response data)
    """
    # First, get all information we need from the database
    response_info = None
    moderation_records = []
    
    try:
        # Get response info - database operation
        response_info = await journey_service.get_response_info(db, response_id)
        if not response_info:
            logger.error(f"Cannot stream evaluation: Response {response_id} not found")
            # Use a separate async context for WebSocket error notification
            await websocket.send_text(json.dumps({
                "type": "error",
                "data": {"message": f"Response {response_id} not found"}
            }))
            return None
        
        logger.info(f"Starting streaming evaluation for response {response_id}")
        
        # Get moderation records - database operation
        try:
            from src.shared.message_processing.db import get_processing_results_by_response
            # Fetch any moderation flags for responses related to this question
            moderation_records = await get_processing_results_by_response(
                db, 
                session_id, 
                response_info['question_id']
            )
            logger.info(f"Found {len(moderation_records)} moderation records for session {session_id}, question {response_info['question_id']}")
        except Exception as check_error:
            # Don't fail if we can't check moderation status - just log and continue
            logger.error(f"Error checking moderation status: {str(check_error)}")
            logger.exception("Moderation check error details:")
    except Exception as db_error:
        logger.error(f"Database error during evaluation setup: {str(db_error)}")
        logger.exception("Details:")
        # Use a separate async context for WebSocket error notification
        await websocket.send_text(json.dumps({
            "type": "error",
            "data": {"message": f"Error preparing evaluation: {str(db_error)}"}
        }))
        raise
    
    # Now handle WebSocket operations separately from database operations
    try:        
        # Send moderation notice if needed
        if moderation_records and any(not record.is_appropriate for record in moderation_records):
            # Get the first inappropriate record to use its reason
            inappropriate_record = next((r for r in moderation_records if not r.is_appropriate), None)
            inappropriate_reason = "Content moderation policy violation"
            
            if inappropriate_record and inappropriate_record.inappropriate_reason:
                inappropriate_reason = inappropriate_record.inappropriate_reason
            
            # Send a moderation notice at the start of the evaluation - WebSocket operation
            await websocket.send_text(json.dumps({
                "type": "evaluation_chunk",
                "data": {
                    "response_id": response_id,
                    "question_id": response_info["question_id"],
                    "chunk": f"⚠️ Note: This evaluation is provided for educational purposes, but the content has been flagged for moderation ({inappropriate_reason}).\n\n",
                    "is_final": False,
                    "has_moderation_flag": True
                }
            }))
        
        # Start streaming with clear separation between database and WebSocket operations
        evaluation_results = None
        
        # Stream evaluation chunks - this combines database and WebSocket operations
        # but in a controlled way where each chunk is processed completely before the next
        async for chunk in journey_service.evaluate_response_streaming(db, response_id):
            # Send each chunk to the client - WebSocket operation
            await websocket.send_text(json.dumps({
                "type": "evaluation_chunk",
                "data": {
                    "response_id": response_id,
                    "question_id": response_info["question_id"],
                    "chunk": chunk,
                    "is_final": False
                }
            }))
        
        # After streaming is complete, get the final evaluation results - database operation
        evaluation_results = await journey_service.get_evaluation_results(db, response_id)
        score, feedback, eval_response_data = evaluation_results
        logger.info(f"Streaming evaluation complete for response {response_id}, score: {score}")
        
        # Send final evaluation message - WebSocket operation
        await connection_manager.send_message(
            session_id,
            user_id,
            {
                "type": "evaluation_complete",
                "data": {
                    "response_id": eval_response_data["id"],
                    "question_id": eval_response_data["question_id"],
                    "score": score,
                    "feedback": feedback,
                    "is_final": True
                }
            }
        )
        
        # Return the evaluation results for any further processing
        return evaluation_results
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error streaming evaluation: {str(e)}\n{error_details}")
        
        # Use a separate async context for WebSocket error notification
        await websocket.send_text(json.dumps({
            "type": "error",
            "data": {"message": f"Error during evaluation streaming: {str(e)}"}
        }))
        
        # Re-raise the exception so the caller knows something went wrong
        raise

async def journey_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str
):
    """WebSocket endpoint for real-time journey interactions"""
    # Get shared services from the application state
    llm_client = websocket.app.state.llm_client
    message_processor = websocket.app.state.message_processor

    try:
        from src.core.security import decode_jwt_token
        payload = decode_jwt_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            logger.error(f"WebSocket authentication failed: Invalid token payload")
            await websocket.close(code=1008, reason="Invalid authentication")
            return
            
        await connection_manager.connect(websocket, session_id, user_id)
        logger.info(f"WebSocket connected: user {user_id} for session {session_id}")
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process message using shared clients
                await process_websocket_message(websocket, session_id, str(user_id), message, llm_client, message_processor)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: user {user_id} for session {session_id}")
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"WebSocket error: {str(e)}\n{error_details}")
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"WebSocket authentication error: {str(e)}\n{error_details}")
        await websocket.close(code=1008, reason="Authentication error")
    finally:
        # Disconnect from manager on any exit
        if 'user_id' in locals() and user_id:
            await connection_manager.disconnect(session_id, user_id)

# Add these new helper functions for separate database sessions

async def process_message_in_own_session(
    message_processor, message_id, text, user_id, feature, session_id=None, question_id=None, websocket=None
) -> Any:
    """
    Process a message with its own independent database session.
    
    If session_id, question_id, and websocket are provided, this function can send
    immediate notifications for inappropriate content directly to the client.
    
    Parameters:
    - message_processor: The message processing service
    - message_id: Unique identifier for the message
    - text: The message text to process
    - user_id: Current user identifier
    - feature: The feature using this processor (e.g., "journey")
    - session_id: Optional WebSocket session ID for immediate notifications
    - question_id: Optional question ID for immediate notifications
    - websocket: Optional WebSocket connection for immediate streaming
    
    Returns:
    - Processing result object
    """
    # Process the message with its own database session
    processing_result = None
    
    try:
        async with SessionLocal() as db:
            logger.info(f"Processing message {message_id}")
            
            # Process the message
            processing_result = await message_processor.process_message(
                db=db,
                message_id=message_id,
                text=text,
                user_id=user_id,
                feature=feature
            )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        logger.exception("Details:")
        return None
    
    # IMPORTANT: Only after the database session is closed, handle WebSocket notifications
    # This ensures no interference between WebSocket operations and database contexts
    if processing_result and session_id and question_id and websocket:
        # Check if content is inappropriate and send notification
        if not processing_result.is_appropriate:
            try:
                # Use a separate async context for WebSocket operations
                logger.info(f"🚨 Message {message_id} flagged as inappropriate, sending notification")
                
                # This isolates the WebSocket operations from any database context
                await send_moderation_notification(
                    websocket,
                    session_id,
                    user_id,
                    question_id,
                    processing_result.inappropriate_reason
                )
            except Exception as ws_error:
                # Don't fail the whole process if notification fails
                logger.error(f"Error sending inappropriate content notification: {str(ws_error)}")
                logger.exception("WebSocket notification error details:")
    
    return processing_result

async def send_moderation_notification(
    websocket, session_id, user_id, question_id, reason=None
):
    """
    Send moderation notifications through WebSocket.
    This function is completely isolated from any database operations.
    
    Parameters:
    - websocket: The WebSocket connection
    - session_id: Current session identifier 
    - user_id: Current user identifier
    - question_id: Question identifier
    - reason: Reason for moderation, if any
    """
    try:
        # Direct stream notification for inappropriate content
        await websocket.send_text(json.dumps({
            "type": "content_moderation_stream",
            "data": {
                "question_id": question_id,
                "is_appropriate": False,
                "message": "⚠️ This content may violate our community guidelines and has been flagged for review.",
                "reason": reason or "Content flagged as inappropriate"
            }
        }))
        
        # Also send a standard WebSocket notification through the manager
        await connection_manager.send_message(
            session_id,
            user_id,
            {
                "type": "moderation_notice",
                "data": {
                    "question_id": question_id,
                    "message": "This message has been logged due to potential policy violations",
                    "reason": reason or "Content flagged as inappropriate"
                }
            }
        )
        
        logger.info(f"Moderation notifications sent for question {question_id}")
    except Exception as e:
        logger.error(f"Failed to send moderation notification: {str(e)}")
        logger.exception("Notification error details:")

async def save_and_evaluate_response(
    journey_service, session_id, question_id, response_text, should_stream, websocket, user_id
) -> Dict[str, Any]:
    """Save and evaluate a response with its own independent database session"""
    async with SessionLocal() as save_db:
        try:
            logger.info(f"Saving response in its own database session")
            # Save the response first
            response_data = await journey_service.save_response(
                save_db, 
                session_id, 
                question_id, 
                response_text
            )
            
            # Return the response data for further use
            return response_data
        except Exception as e:
            logger.error(f"Error in isolated response saving: {str(e)}")
            logger.exception("Details:")
            raise

async def evaluate_response_in_session(
    journey_service, response_data, session_id, user_id, should_stream, websocket
):
    """
    Evaluate a response with its own independent database session.
    
    Parameters:
    - journey_service: The service for evaluating responses
    - response_data: Dictionary containing response information
    - session_id: Current session identifier
    - user_id: Current user identifier
    - should_stream: Whether to stream evaluation results
    - websocket: The WebSocket connection

    Returns:
    - Evaluation results (score, feedback, response data) or None on error
    """
    try:
        async with SessionLocal() as db:
            logger.info(f"Evaluating response {response_data['id']}")
            
            if should_stream:
                # Handle streaming in this database session
                result = await stream_evaluation(
                    db, 
                    journey_service, 
                    session_id, 
                    user_id, 
                    response_data["id"],
                    websocket
                )
                return result
            else:
                # Regular evaluation
                score, feedback, eval_response_data = await journey_service.evaluate_response(
                    db, 
                    response_data["id"]
                )
                
                # Send evaluation results
                await connection_manager.send_message(
                    session_id,
                    user_id,
                    {
                        "type": "evaluation",
                        "data": {
                            "response_id": eval_response_data["id"],
                            "question_id": eval_response_data["question_id"],
                            "score": score,
                            "feedback": feedback
                        }
                    }
                )
                
                return score, feedback, eval_response_data
    except Exception as e:
        logger.error(f"Error evaluating response: {str(e)}")
        logger.exception("Details:")
        
        # Notify the client of the error
        await connection_manager.send_message(
            session_id,
            user_id,
            {
                "type": "error",
                "data": {"message": f"Error evaluating response: {str(e)}"}
            }
        )
        
        # Return None to indicate failure
        return None

async def get_next_question_in_session(
    journey_service, session_id, user_id
):
    """
    Get next question with its own independent database session.
    
    Parameters:
    - journey_service: The service for retrieving questions
    - session_id: Current session identifier
    - user_id: Current user identifier
    
    Returns:
    - Next question data or None if no more questions or on error
    """
    try:
        # Use simple async context manager
        async with SessionLocal() as db:
            logger.info(f"Getting next question for session {session_id}")
            
            # Get the next question
            next_question = await journey_service.get_next_question(
                db, 
                session_id
            )
            
            if next_question:
                # Send question to client
                await connection_manager.send_message(
                    session_id,
                    user_id,
                    {
                        "type": "question",
                        "data": next_question
                    }
                )
                logger.info(f"Sent next question {next_question.get('id')} to user {user_id}")
            else:
                logger.info(f"No more questions available for session {session_id}")
            
            return next_question
    except Exception as e:
        logger.error(f"Error getting next question: {str(e)}")
        logger.exception("Details:")
        
        # Notify client of the error
        await connection_manager.send_message(
            session_id,
            user_id,
            {
                "type": "error",
                "data": {"message": f"Error retrieving next question: {str(e)}"}
            }
        )
        
        # Return None to indicate failure
        return None