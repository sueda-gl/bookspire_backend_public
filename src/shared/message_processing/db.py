# src/shared/message_processing/db.py
from typing import Optional
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.shared.message_processing.models import MessageProcessing
from src.shared.message_processing.schemas import ProcessingResult

logger = logging.getLogger(__name__)

async def store_processing_result(
    db: AsyncSession,
    message_id: str,
    user_id: str,
    original_text: str,
    result: ProcessingResult,
    feature: str
):
    """Store message processing result in database"""
    try:
        # Try to convert user_id to integer if it's a string
        converted_user_id = None
        if user_id:
            try:
                # Check if it's a numeric string that can be converted
                if isinstance(user_id, str) and user_id.isdigit():
                    converted_user_id = int(user_id)
                # If it's already an int, use it
                elif isinstance(user_id, int):
                    converted_user_id = user_id
                else:
                    # For non-numeric user IDs, set to None to avoid database errors
                    logger.warning(f"Non-numeric user_id '{user_id}' cannot be stored in message_processing table, setting to None")
            except (ValueError, TypeError) as e:
                logger.warning(f"Cannot convert user_id '{user_id}' to integer: {str(e)}")
        
        new_processing = MessageProcessing(
            id=message_id,
            user_id=converted_user_id,
            original_text=original_text,
            corrected_text=result.corrected_text,
            is_appropriate=result.is_appropriate,
            inappropriate_reason=result.inappropriate_reason,
            grammar_feedback=result.grammar_feedback,
            feature=feature,
            processed_at=result.processed_at
        )
        
        db.add(new_processing)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Error storing processing result: {e}")
        raise

async def get_processing_result(
    db: AsyncSession,
    message_id: str
) -> Optional[ProcessingResult]:
    """Retrieve processing result from database"""
    try:
        stmt = select(MessageProcessing).where(MessageProcessing.id == message_id)
        result = await db.execute(stmt)
        db_result = result.scalar_one_or_none()
        
        if not db_result:
            return None
            
        return ProcessingResult(
            message_id=db_result.id,
            is_appropriate=db_result.is_appropriate,
            inappropriate_reason=db_result.inappropriate_reason,
            corrected_text=db_result.corrected_text,
            grammar_feedback=db_result.grammar_feedback,
            processed_at=db_result.processed_at
        )
    except Exception as e:
        logger.error(f"Error getting processing result: {e}")
        raise

async def get_processing_results_by_response(
    db: AsyncSession,
    session_id: str,
    question_id: str
) -> list:
    """
    Retrieve all processing results related to a specific response by session_id and question_id.
    This is used to check if any messages for a particular question were flagged as inappropriate.
    
    Parameters:
    - db: The database session
    - session_id: The session identifier
    - question_id: The question identifier
    
    Returns:
    - List of MessageProcessing records or empty list if none found
    """
    try:
        # Create a message ID pattern to match
        message_id_pattern = f"{session_id}_{question_id}_%"
        
        # Query for all processing results matching the pattern
        stmt = select(MessageProcessing).where(
            MessageProcessing.id.like(message_id_pattern)
        ).order_by(MessageProcessing.processed_at.desc())
        
        result = await db.execute(stmt)
        records = result.scalars().all()
        
        logger.info(f"Found {len(records)} processing records for session {session_id}, question {question_id}")
        return list(records)
    except Exception as e:
        logger.error(f"Error getting processing results by response: {e}")
        logger.exception("Details:")
        return []