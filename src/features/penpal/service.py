# Curriculum business logic 

import os
import logging
from datetime import datetime, timedelta
from sqlalchemy import or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.features.penpal.models import PenpalLetter
from src.features.auth.models import User
from src.shared.llm.client import LLMClient

logger = logging.getLogger(__name__)

class PenpalService:
    def __init__(self, llm_client: LLMClient):
        """Initialize the penpal service."""
        self.llm_client = llm_client
        logger.info("PenpalService initialized with shared LLMClient.")

    def get_next_monday(self):
        # For testing: return current time plus 30 seconds
        return datetime.utcnow() + timedelta(seconds=30)

    async def process_letter(self, db: AsyncSession, user_id: int, letter_content: str, character_name: str):
        """
        Process a student's letter through an LLM and store both letter and response.
        """
        try:
            # Add delivery date when creating letter
            new_letter = PenpalLetter(
                user_id=user_id,
                letter_content=letter_content,
                character_name=character_name,
                delivery_date=self.get_next_monday()
            )
            db.add(new_letter)
            await db.commit()
            await db.refresh(new_letter)

            # Prepare prompt for OpenAI with character context
            prompt = f"""You are {character_name}, a friendly penpal responding to a letter from a student. 
            Write a warm, encouraging response that engages with their specific message, 
            staying in character as {character_name}:

            Student's Letter: {letter_content}

            Response (as {character_name}):"""

            try:
                # Call LLM to generate response using the shared client
                response = await self.get_response(prompt, character_name)
            
            except Exception as e:
                logger.error(f"LLM API error: {str(e)}")
                new_letter.response_content = "I apologize, but I couldn't generate a response at this time. Please try again later."
                await db.commit()
                return new_letter

            # Store the AI response
            new_letter.response_content = response
            new_letter.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(new_letter)

            return new_letter

        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing letter: {str(e)}")
            raise

    async def get_response(self, prompt, character=None, conversation_history=None):
        """Get a response from the penpal character using the shared LLMClient."""
        try:
            # Prepare messages
            if conversation_history:
                messages = conversation_history + [{"role": "user", "content": prompt}]
            else:
                system_message = f"You are a penpal character named {character}. Write a friendly letter response to the user."
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
            
            # Use the shared LLMClient's generate_text method
            # The client expects a JSON string of the message list
            import json
            prompt_json = json.dumps(messages)
            response = await self.llm_client.generate_text(prompt_json)
            return response
                
        except Exception as e:
            logger.error(f"Error getting penpal response: {e}")
            return "I'm sorry, I couldn't generate a response at the moment."

    async def get_letters(self, db: AsyncSession, user_id=None, role=None, character_name=None, student_name=None):
        """
        Get letters based on user role and filters.
        """
        try:
            logger.info(f"Starting get_letters with user_id: {user_id}, role: {role}, character_name: {character_name}")
            query = select(PenpalLetter)

            if role == 'student':
                # Base filter for students: their own letters that are delivered
                query = query.where(
                    PenpalLetter.user_id == user_id,
                    PenpalLetter.delivery_date <= datetime.utcnow()
                )
                
                # Add character filter if specified
                if character_name:
                    query = query.where(PenpalLetter.character_name == character_name)
                    
            elif role == 'teacher':
                # Join with User table only if we need to search by student name
                if student_name:
                    query = query.join(PenpalLetter.user)
                    search_term = f"%{student_name}%"
                    query = query.where(
                        or_(
                            func.lower(User.first_name).like(func.lower(search_term)),
                            func.lower(User.last_name).like(func.lower(search_term)),
                            func.lower(func.concat(User.first_name, ' ', User.last_name))
                            .like(func.lower(search_term))
                        )
                    )
                
                # Add character filter for teachers if specified
                if character_name:
                    query = query.where(PenpalLetter.character_name == character_name)
            
            # Order by creation date, newest first
            query = query.order_by(PenpalLetter.created_at.desc())
            
            result = await db.execute(query)
            letters = result.scalars().all()
            
            logger.info(f"Found {len(letters)} letters matching criteria")
            return letters

        except Exception as e:
            logger.error(f"Error retrieving letters: {str(e)}")
            raise 