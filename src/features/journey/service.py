from typing import List, Dict, Any, Optional, Tuple, AsyncIterator
import random
import logging
import asyncio
import json
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from sqlalchemy.orm import selectinload
import os

from src.features.journey.models import JourneySession, JourneyResponse
from src.features.journey.questions import JOURNEY_QUESTIONS
from src.shared.llm.client import LLMClient

logger = logging.getLogger(__name__)

class JourneyService:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.questions_dict = {q["id"]: q for q in JOURNEY_QUESTIONS}
        self.prompt_base_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'journey')
        
    async def _load_and_format_evaluation_prompt(
        self,
        character_id: str,
        language_level: str,
        question_details: Dict[str, Any],
        user_response: str
    ) -> str:
        """Loads and formats the evaluation prompt from a file."""
        prompt_filename = f"eval_char{character_id}_lang{language_level.upper()}.txt" 
        prompt_filepath = os.path.join(self.prompt_base_path, prompt_filename)
        
        default_prompt_filepath = os.path.join(self.prompt_base_path, "eval_default.txt")
        
        final_prompt_filepath = prompt_filepath
        
        if not os.path.exists(prompt_filepath):
            logger.warning(f"Prompt file not found: {prompt_filepath}. Falling back to default.")
            final_prompt_filepath = default_prompt_filepath
            if not os.path.exists(default_prompt_filepath):
                logger.error(f"Default prompt file not found: {default_prompt_filepath}. Cannot generate prompt.")
                return "Error: Evaluation prompt template not found."

        try:
            with open(final_prompt_filepath, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except Exception as e:
            logger.error(f"Error reading prompt file {final_prompt_filepath}: {e}")
            return "Error: Could not read evaluation prompt template."
        
        try:
            formatted_prompt = prompt_template.format(
                character_id=character_id,
                language_level=language_level,
                question=question_details.get('question', '[Question not found]'),
                context=question_details.get('context', '[Context not found]'),
                user_response=user_response
            )
            return formatted_prompt
        except KeyError as e:
            logger.error(f"Missing placeholder in prompt template {final_prompt_filepath}: {e}")
            return f"Error: Prompt template {final_prompt_filepath} is missing placeholder: {e}"
        except Exception as e:
            logger.error(f"Error formatting prompt template {final_prompt_filepath}: {e}")
            return "Error: Could not format evaluation prompt."

    async def create_session(self, db: AsyncSession, user_id: str, character_id: str, language_level: str) -> JourneySession:
        """Create a new journey session with character and language level"""
        session = JourneySession(
            id=str(uuid4()),
            user_id=user_id,
            character_id=character_id,
            language_level=language_level,
            questions_count=0,
            current_attempt=1,
            is_completed=False
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        logger.info(f"Created JourneySession {session.id} for user {user_id} with character {character_id} and language_level {language_level}")
        return session
    
    async def get_session(self, db: AsyncSession, session_id: str) -> Optional[JourneySession]:
        """Get journey session by id, including character and language level"""
        stmt = select(JourneySession).where(JourneySession.id == session_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_next_question(self, db: AsyncSession, session_id: str) -> Optional[Dict[str, Any]]:
        """Get next random question based on session's character and language level, excluding answered ones"""
        stmt = select(JourneySession).where(JourneySession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            logger.warning(f"Session {session_id} not found in get_next_question")
            return None

        session_character_id = session.character_id
        session_language_level = session.language_level
        
        if not session_character_id or not session_language_level:
            logger.warning(f"Session {session_id} is missing character_id or language_level")
            return None 
            
        stmt = select(JourneyResponse.question_id).where(
            and_(
                JourneyResponse.session_id == session_id,
                JourneyResponse.attempt == session.current_attempt
            )
        )
        result = await db.execute(stmt)
        answered_ids = set(result.scalars().all())
        
        available_questions = [
            q for q in JOURNEY_QUESTIONS 
            if q.get("character_id") == session_character_id 
            and (q.get("language_level") or "").lower() == (session_language_level or "").lower()
            and q["id"] not in answered_ids
        ]
        
        if not available_questions:
            logger.info(f"No more questions available for session {session_id}, character {session_character_id}, language_level {session_language_level}, attempt {session.current_attempt}")
            return None
            
        selected_question = random.choice(available_questions)
        
        return {
            "id": selected_question["id"],
            "question": selected_question["question"],
            "book_reference": selected_question["book_reference"]
        }
    
    async def save_response(self, db: AsyncSession, session_id: str, question_id: str, 
                          response_text: str) -> Dict[str, Any]:
        """Save user's response to a question and return a dict with primitive values"""
        stmt = select(JourneySession).where(JourneySession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        current_attempt = session.current_attempt
        
        logger.info(f"Saving original user response for session {session_id}, question {question_id}")
            
        response = JourneyResponse(
            id=str(uuid4()),
            session_id=session_id,
            question_id=question_id,
            user_response=response_text,
            attempt=current_attempt
        )
        
        db.add(response)
        await db.commit()
        await db.refresh(response)
        
        response_data = {
            "id": response.id,
            "session_id": response.session_id,
            "question_id": response.question_id,
            "user_response": response.user_response,
            "attempt": response.attempt
        }
        
        stmt = select(JourneySession).where(JourneySession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if session:
            session.questions_count += 1
            await db.commit()
        
        return response_data
    
    async def evaluate_response(self, db: AsyncSession, response_id: str) -> Tuple[float, str, Dict[str, Any]]:
        """Evaluate user response using LLM, adapting prompt based on character/language level"""
        stmt = select(JourneyResponse).options(selectinload(JourneyResponse.session)).where(JourneyResponse.id == response_id)
        result = await db.execute(stmt)
        response = result.scalar_one_or_none()
        
        if not response:
            raise ValueError(f"Response {response_id} not found")
        if not response.session:
             raise ValueError(f"Session data not found for response {response_id}")

        session_character_id = response.session.character_id
        session_language_level = response.session.language_level
        user_response_text = response.user_response
        
        response_data = {
            "id": response.id,
            "question_id": response.question_id
        }
        
        logger.info(f"Evaluating response {response_id} for character {session_character_id}, language_level {session_language_level}")
            
        question_details = self.questions_dict.get(response.question_id)
        if not question_details:
            raise ValueError(f"Question {response.question_id} not found in questions_dict")
            
        prompt_string = await self._load_and_format_evaluation_prompt(
            character_id=session_character_id,
            language_level=session_language_level,
            question_details=question_details,
            user_response=user_response_text
        )
        
        if prompt_string.startswith("Error:"):
             logger.error(f"Failed to load/format prompt for response {response_id}: {prompt_string}")
             response.score = 5.0
             response.feedback = prompt_string 
             response.evaluated_at = datetime.now()
             await db.commit()
             return 5.0, prompt_string, response_data
        
        prompt_messages = [{"role": "user", "content": prompt_string}]
        
        prompt_json_string = json.dumps(prompt_messages)
        
        try:
            evaluation = await self.llm_client.generate(prompt_json_string, expect_json=True)
            
            score = float(evaluation.get("score", 0))
            feedback = evaluation.get("feedback", "No feedback provided.")
            
            response.score = score
            response.feedback = feedback
            response.evaluated_at = datetime.now()
            await db.commit()
            
            return score, feedback, response_data
            
        except Exception as e:
            logger.error(f"Error evaluating response {response_id}: {str(e)}")
            
            response.score = 5.0
            response.feedback = "I was unable to fully evaluate your response due to a technical issue. Your answer receives a neutral score of 5/10."
            response.evaluated_at = datetime.now()
            await db.commit()
            
            return 5.0, "Evaluation error: " + str(e), response_data
    
    async def get_response_info(self, db: AsyncSession, response_id: str) -> Optional[Dict[str, Any]]:
        """Get basic information about a response"""
        stmt = select(JourneyResponse).where(JourneyResponse.id == response_id)
        result = await db.execute(stmt)
        response = result.scalar_one_or_none()
        
        if not response:
            return None
            
        return {
            "id": response.id,
            "question_id": response.question_id,
            "session_id": response.session_id,
            "attempt": response.attempt
        }
    
    async def evaluate_response_streaming(self, db: AsyncSession, response_id: str) -> AsyncIterator[str]:
        """
        Evaluate user response using LLM with streaming, adapting prompt based on character/language_level.
        """
        stmt = select(JourneyResponse).options(selectinload(JourneyResponse.session)).where(JourneyResponse.id == response_id)
        result = await db.execute(stmt)
        response = result.scalar_one_or_none()
        
        if not response:
            raise ValueError(f"Response {response_id} not found")
        if not response.session:
             raise ValueError(f"Session data not found for response {response_id}")

        session_character_id = response.session.character_id
        session_language_level = response.session.language_level
        user_response_text = response.user_response
        
        logger.info(f"Streaming evaluation for response {response_id}, character {session_character_id}, language_level {session_language_level}")
            
        question_details = self.questions_dict.get(response.question_id)
        if not question_details:
            raise ValueError(f"Question {response.question_id} not found in questions_dict")
            
        prompt_string = await self._load_and_format_evaluation_prompt(
            character_id=session_character_id,
            language_level=session_language_level,
            question_details=question_details,
            user_response=user_response_text
        )
        
        if prompt_string.startswith("Error:"):
            logger.error(f"Failed to load/format prompt for streaming response {response_id}: {prompt_string}")
            yield prompt_string 
            response.score = 5.0
            response.feedback = prompt_string 
            response.evaluated_at = datetime.now()
            await db.commit()
            return 
        
        prompt_messages = [{"role": "user", "content": prompt_string}]

        prompt_json_string = json.dumps(prompt_messages)

        full_response = ""
        score = 5.0  
        feedback = ""  
        
        try:
            async for chunk in self.llm_client.stream_generate(prompt_json_string):
                full_response += chunk
                yield chunk
                
            try:
                evaluation = json.loads(full_response)
                score = float(evaluation.get("score", 5.0))
                feedback = evaluation.get("feedback", "No feedback provided.")
            except json.JSONDecodeError:
                logger.warning(f"Could not parse LLM JSON response for {response_id}: {full_response}")
                feedback = full_response 
                
            response.score = score
            response.feedback = feedback
            response.evaluated_at = datetime.now()
            await db.commit()
                
        except Exception as e:
            logger.error(f"Error in streaming evaluation for response {response_id}: {str(e)}")
            yield f"Evaluation error: {str(e)}" 
            
            response.score = score 
            response.feedback = feedback if feedback else f"Evaluation error: {str(e)}"
            response.evaluated_at = datetime.now()
            await db.commit()
    
    async def get_evaluation_results(self, db: AsyncSession, response_id: str) -> Tuple[float, str, Dict[str, Any]]:
        """Get the final evaluation results after streaming is complete"""
        stmt = select(JourneyResponse).where(JourneyResponse.id == response_id)
        result = await db.execute(stmt)
        response = result.scalar_one_or_none()
        
        if not response:
            raise ValueError(f"Response {response_id} not found")
        
        response_data = {
            "id": response.id,
            "question_id": response.question_id,
            "session_id": response.session_id,
            "attempt": response.attempt
        }
        
        return response.score or 5.0, response.feedback or "No feedback available", response_data