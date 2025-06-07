# src/shared/message_processing/service.py
from typing import Dict, Any, Optional
import json
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.message_processing.schemas import ProcessingResult
from src.shared.message_processing.db import store_processing_result, get_processing_result

logger = logging.getLogger(__name__)

class MessageProcessingService:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        
    async def process_message(
        self, 
        db: AsyncSession,
        message_id: str, 
        text: str, 
        user_id: str,
        feature: str
    ) -> ProcessingResult:
        """
        Process a message for appropriateness and grammar in one call.
        Stores the result in the database and returns it.
        """
        try:
            # Log the incoming message
            logger.info(f"Processing message {message_id} for feature '{feature}', text length: {len(text)}")
            
            # Create prompt for combined analysis - using f-string instead of .format() to avoid escaping issues
            prompt = f"""
            You are a content moderation and grammar correction API that only returns JSON.
            
            Analyze the following message for:
            1. Appropriateness: Determine if it contains inappropriate content (profanity, hate speech, etc.)
            2. Grammar: If appropriate, correct any grammar issues
            
            RESPOND WITH ONLY A VALID JSON OBJECT in the following format. 
            Do not include any explanation text outside the JSON object:
            {{
              "is_appropriate": true or false,
              "inappropriate_reason": "Reason if inappropriate, otherwise omit this field",
              "corrected_text": "The grammatically corrected version of the message",
              "grammar_feedback": "Brief explanation of grammar corrections made"
            }}
            
            Message: "{text}"
            """
            
            # Call LLM for combined analysis
            logger.info(f"Sending message {message_id} to LLM for analysis")
            # Use the NEW method designed for plain string prompts
            raw_response = await self.llm_client.generate_response_from_string(prompt)
            
            # Log the raw response for debugging
            logger.debug(f"Raw LLM response for message {message_id}: {raw_response}")
            
            # Parse JSON response
            try:
                # Try standard JSON parsing first
                result_data = json.loads(raw_response)
                logger.info(f"Successfully parsed JSON response for message {message_id}")
            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse LLM response as JSON for message {message_id}: {str(json_err)}")
                logger.error(f"Raw response: {raw_response}")
                
                # Try to extract JSON from possible text wrapper
                import re
                # More robust regex to find JSON-like content with balanced braces
                json_match = re.search(r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}', raw_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    logger.info(f"Extracted JSON-like string from response: {json_str}")
                    try:
                        result_data = json.loads(json_str)
                        logger.info(f"Successfully parsed extracted JSON for message {message_id}")
                    except json.JSONDecodeError as extract_err:
                        logger.error(f"Failed to parse extracted JSON: {str(extract_err)}")
                        # Try fixing common JSON errors
                        try:
                            # Replace single quotes with double quotes
                            fixed_json = json_str.replace("'", "\"")
                            # Ensure boolean values are lowercase
                            fixed_json = re.sub(r':\s*True', ': true', fixed_json)
                            fixed_json = re.sub(r':\s*False', ': false', fixed_json)
                            result_data = json.loads(fixed_json)
                            logger.info(f"Successfully parsed JSON after fixing common errors")
                        except:
                            logger.error("Failed to fix JSON format issues")
                            result_data = {
                                "is_appropriate": True,
                                "corrected_text": text,
                                "grammar_feedback": "Unable to analyze grammar due to technical issues."
                            }
                else:
                    logger.error(f"No JSON-like structure found in response for message {message_id}")
                    result_data = {
                        "is_appropriate": True,
                        "corrected_text": text,
                        "grammar_feedback": "Unable to analyze grammar due to technical issues."
                    }
            
            # Log the parsed result
            logger.info(f"Message {message_id} analysis result - is_appropriate: {result_data.get('is_appropriate', True)}")
            if result_data.get('is_appropriate', True) == False:
                logger.info(f"Message {message_id} flagged as inappropriate: {result_data.get('inappropriate_reason', 'No reason provided')}")
            
            if text != result_data.get('corrected_text', text):
                logger.info(f"Grammar corrections applied to message {message_id}")
                logger.debug(f"Original: '{text}' -> Corrected: '{result_data.get('corrected_text', text)}'")
            
            # Create processing result
            result = ProcessingResult(
                message_id=message_id,
                is_appropriate=result_data.get("is_appropriate", True),
                inappropriate_reason=result_data.get("inappropriate_reason"),
                corrected_text=result_data.get("corrected_text", text),
                grammar_feedback=result_data.get("grammar_feedback"),
                processed_at=datetime.now()
            )
            
            # Store result in database
            await store_processing_result(
                db=db,
                message_id=message_id,
                user_id=user_id,
                original_text=text,
                result=result,
                feature=feature
            )
            
            return result
        
        except Exception as e:
            # Log the error associated with this specific message processing attempt
            logger.error(f"Error processing message {message_id}: {str(e)}")
            # logger.error("Full exception details:") # Avoid duplicate logging if exception is re-raised or handled
            # logger.exception(e) # Avoid duplicate logging
            # Fallback: Assume appropriate, no corrections on error
            feedback = "Could not analyze message due to an internal error."
            # Construct a result object even in case of error to return something consistent
            result = ProcessingResult(
                message_id=message_id,
                is_appropriate=True,
                corrected_text=text,
                grammar_feedback=feedback,
                processed_at=datetime.now()
            )
            
            return result
    
    async def get_message_status(
        self, 
        db: AsyncSession,
        message_id: str
    ) -> Optional[ProcessingResult]:
        """Get the current processing status of a message"""
        return await get_processing_result(db, message_id)