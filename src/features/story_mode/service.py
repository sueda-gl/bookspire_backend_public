from typing import List, Dict, Any, Optional, Tuple, AsyncIterator
import logging
import json
import time
from datetime import datetime
from sqlalchemy import select, func, exists
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from src.features.story_mode.models import StorySession, StoryMessage, StoryHint
from src.features.story_mode.characters import get_character_config
from src.shared.llm.client import LLMClient
from src.shared.websockets.manager import connection_manager
from src.shared.services import BaseChatService

logger = logging.getLogger(__name__)

def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a text string.
    Uses a simple approximation of 4 characters per token."""
    return len(text) // 4 + 1

class StoryService(BaseChatService):
    def __init__(self, llm_client: LLMClient, db: AsyncSession):
        """Initialize the story service with a single LLM client and database session"""
        super().__init__(llm_client, db, StorySession, StoryMessage)
        logger.debug("StoryService initialized")
        
    async def create_session(self, user_id: int, title: Optional[str] = None, character_id: str = "little-prince", language_level: str = "b1") -> StorySession:
        """Create a new story session, storing the language level."""
        # Get character configuration (using the specified language level)
        character = get_character_config(character_id=character_id, languageLevel=language_level)
        
        # Create a new session, including the language level
        session = self.session_model(
            id=str(uuid4()),
            user_id=user_id,
            title=title or f"{character.get('name', 'Story')} {datetime.now().strftime('%Y-%m-%d')}", # Use character name in title
            is_active=True,
            language_level=language_level # Store the provided level
        )
        
        # Add session to database
        self.db.add(session)
        
        # Create greeting message
        greeting_id = str(uuid4())
        greeting_message = self.message_model(
            id=str(uuid4()),
            session_id=session.id,
            role="assistant",
            content=character["greeting"],
            message_id=greeting_id,
            character_id=character_id,
            is_complete=True
        )
        
        # Add greeting message to database
        self.db.add(greeting_message)
        
        # Generate hints
        # Get character name for hint generation
        character_name = character.get("name", "the character") # Use get with fallback
        hints = await self._generate_hints(
            [{"role": "assistant", "content": character["greeting"]}],
            character["hint_prompt"],
            character_name # Pass the character name
        )
        
        # Create StoryHint objects for each hint
        for hint_content in hints:
            hint = StoryHint(
                id=str(uuid4()),
                session_id=session.id,
                message_id=greeting_message.id,
                content=hint_content,
                is_used=False
            )
            # Add hint to database
            self.db.add(hint)
        
        # Commit all changes at once
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists"""
        stmt = select(exists().where(self.session_model.id == session_id))
        result = await self.db.execute(stmt)
        return result.scalar()
    
    async def session_has_messages(self, session_id: str) -> bool:
        """Check if a session has any messages"""
        stmt = select(exists().where(self.message_model.session_id == session_id))
        result = await self.db.execute(stmt)
        return result.scalar()
    
    async def get_latest_hints(self, session_id: str, limit: int = 3) -> List[StoryHint]:
        """Get the most recent hints for a session"""
        stmt = select(StoryHint).where(
            StoryHint.session_id == session_id
        ).order_by(StoryHint.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def save_hint(self, session_id: str, message_id: str, content: str) -> StoryHint:
        """Save a hint to the database"""
        hint = StoryHint(
            id=str(uuid4()),
            session_id=session_id,
            message_id=message_id,
            content=content,
            is_used=False
        )
        
        self.db.add(hint)
        await self.db.commit()
        await self.db.refresh(hint)
        
        return hint
    
    async def mark_hint_as_used(self, hint_id: str) -> bool:
        """Mark a hint as used by the user"""
        stmt = select(StoryHint).where(StoryHint.id == hint_id)
        result = await self.db.execute(stmt)
        hint = result.scalar_one_or_none()
        
        if hint:
            hint.is_used = True
            await self.db.commit()
            return True
        
        return False
    
    async def process_user_message(
        self, 
        session_id: str, 
        user_message: str, 
        message_id: str,
        character_id: str = "little-prince",
        user_id: str = None
    ) -> Dict[str, Any]:
        """Process a user message, get LLM response (using session language level), and generate hints"""
        # First, get the session to ensure it exists and is active, and get its level
        session = await self.get_session(session_id)
        if not session or not session.is_active:
            raise ValueError(f"Session {session_id} not found or inactive")
        session_language_level = session.language_level
        actual_character_id = character_id
            
        # Save user message
        user_msg = await self.save_message(
            session_id, 
            "user", 
            user_message, 
            message_id,
            actual_character_id
        )
        
        # Get conversation history for context
        conversation_history = await self.get_session_messages(session_id)
        
        # Get character config USING THE SESSION'S LANGUAGE LEVEL
        character_config = get_character_config(actual_character_id, languageLevel=session_language_level)
        
        # Format conversation history for the LLM
        formatted_conversation = self._format_conversation_for_llm(
            conversation_history, 
            character_config["system_prompt"]
        )
        
        # Get character response
        character_response = await self._generate_character_response(formatted_conversation)
        
        # Save character response with same message_id
        char_msg = await self.save_message(
            session_id, 
            "assistant", 
            character_response, 
            message_id,
            actual_character_id
        )
        
        # Generate hints using the hint LLM and save to database
        # Pass user_id if it's provided to send via WebSocket
        # Note: Hint generation currently uses the default hint_prompt from config
        await self._generate_and_send_hints(
            session_id,
            char_msg.id,
            formatted_conversation + [{"role": "assistant", "content": character_response}],
            actual_character_id,
            user_id
        )
        
        # Get the newly generated hints to return
        latest_hints = await self.get_latest_hints(session_id)
        
        return {
            "user_message": user_msg,
            "assistant_message": char_msg,
            "hints": [hint.content for hint in latest_hints]
        }
    
    async def _generate_and_send_hints(self, session_id: str, message_id: str, conversation: List[Dict[str, str]], character_id: str, user_id: Optional[str] = None):
        """Generate hints, save them to database, and optionally send via WebSocket"""
        character_config = get_character_config(character_id)
        
        # Generate hints
        hints = await self._generate_hints(conversation, character_config["hint_prompt"])
        
        # Create hint objects for database
        hint_objects = []
        for hint_content in hints:
            hint = StoryHint(
                id=str(uuid4()),
                session_id=session_id,
                message_id=message_id,
                content=hint_content,
                is_used=False
            )
            hint_objects.append(hint)
            self.db.add(hint)
        
        # Commit all changes at once
        await self.db.commit()
        
        # If user_id is provided, send via WebSocket
        if user_id:
            try:
                await self._send_hints_ws(session_id, user_id, message_id, hints)
            except Exception as e:
                logger.error(f"Error sending hints via WebSocket: {str(e)}")
                
        return hints
    
    async def _send_hints_ws(self, session_id: str, user_id: str, message_id: str, hints: List[str]):
        """Send hints via WebSocket without using the database session"""
        try:
            await connection_manager.send_message(
                session_id,
                user_id,
                {
                    "type": "HINTS",
                    "messageId": message_id,
                    "hints": hints,
                    "timestamp": int(time.time() * 1000)
                }
            )
        except Exception as e:
            logger.error(f"WebSocket send error: {str(e)}")
    
    async def _generate_hints(self, conversation: List[Dict[str, str]], hint_prompt: str, character_name: str) -> List[str]:
        """Generate multiple hints for the user based on conversation history"""
        try:
            # Find the character's most recent message
            last_prince_message = None
            for msg in reversed(conversation):
                if msg.get("role") == "assistant":
                    last_prince_message = msg.get("content")
                    break
            
            # Create a new prompt for the hint system
            hint_conversation = [
                {"role": "system", "content": hint_prompt},
                {"role": "user", "content": f"Analyze the character ({character_name})\'s MOST RECENT message (the very last assistant message) and provide exactly 3 different helpful hints that directly respond to what they just said. Their last message is: \"{last_prince_message}\"\n\nMake sure each hint directly addresses something specific in this message. Format each hint as instructed in the system prompt."}
            ]
            
            logger.info(f"[_generate_hints] Sending conversation to hint LLM: {json.dumps(hint_conversation)}")

            # Use the main LLM client
            raw_hints = await self.llm_client.generate_text(json.dumps(hint_conversation))
            
            logger.info(f"[_generate_hints] Raw response from hint LLM: {raw_hints}")

            # --- Simplified Hint Processing --- 
            # Directly use non-empty lines from the raw LLM response as hints.
            # Remove strict parsing that checked for specific formats.
            hints = [line.strip() for line in raw_hints.split('\n') if line.strip()]
            
            # Ensure we have at least one hint
            if not hints:
                # Generic fallback if parsing fails or LLM doesn't return valid hints
                logger.warning(f"[_generate_hints] Failed to parse hints from LLM response or response was invalid. Using fallback hints.")
                if last_prince_message and ("?" in last_prince_message): # Check if the last message was a question
                    processed_hints = [
                        f'"You can answer {character_name}\'s question using present tense. \"I think...\""' ,
                        f'"You can share a related experience using past tense. \"When I...\""' ,
                        f'"You can ask {character_name} a follow-up question. \"Why do you...\""'
                    ]
                else:
                    processed_hints = [
                        f'"You can respond to what {character_name} said using opinion phrases. \"I think that...\""' ,
                        f'"You can ask {character_name} a question about the topic. \"What about...\""' ,
                        f'"You can share something about your day using past tense. \"Today I...\""'
                    ]
            else:
                processed_hints = hints
            
            logger.info(f"[_generate_hints] Parsed hints: {processed_hints[:3]}")
            return processed_hints[:3]  # Limit to 3 hints
            
        except Exception as e:
            logger.error(f"Error generating hints: {str(e)}")
            logger.exception("[_generate_hints] Exception details:") # Log traceback
            return [
                '"You can ask about his planet using question words. \"What is your planet...\""',
                '"You can share your day using past tense. \"Today I went...\""',
                '"You can tell him about yourself using present tense. \"I am...\""'
            ]
    
    async def stream_character_response(
        self, 
        session_id: str, 
        conversation: List[Dict[str, str]],
        character_id: str = "little-prince"
    ) -> AsyncIterator[str]:
        """Stream the character response chunks using the session's language level"""
        try:
            # Get the session to retrieve its language level
            session = await self.get_session(session_id)
            session_language_level = session.language_level if session else "b1"
            logger.info(f"[stream_character_response] Retrieved session level: {session_language_level} for session {session_id}")
            actual_character_id = character_id

            # Get character config USING THE SESSION'S LANGUAGE LEVEL
            character_config = get_character_config(actual_character_id, languageLevel=session_language_level)
            
            # Format with character system prompt (level-adjusted)
            formatted_messages = [{"role": "system", "content": character_config["system_prompt"]}]
            formatted_messages.extend(conversation)
            
            async for chunk in self.llm_client.stream_generate(json.dumps(formatted_messages)):
                yield chunk
        except Exception as e:
            logger.error(f"Error streaming character response: {str(e)}")
            yield "I'm having trouble finding the right words. Could you please repeat what you said?"
            
    def get_timestamp(self) -> int:
        """Get current timestamp in milliseconds for frontend"""
        return int(time.time() * 1000)

    async def get_conversation(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get complete conversation history without summarization.
        Always returns the full history for maximum context fidelity.
        """
        messages = await self.get_session_messages(session_id)
        
        # Simply format and return all messages
        formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        # Log the conversation size
        message_count = len(messages)
        estimated_tokens = sum(estimate_tokens(msg.content) for msg in messages)
        logger.info(f"Returning full conversation history: {message_count} messages, ~{estimated_tokens} tokens")
        
        return formatted_messages

    async def generate_hints(self, session_id: str) -> List[str]:
        """Generate hints based on the current conversation (using session language level for config)"""
        # Get the session to retrieve its language level
        session = await self.get_session(session_id)
        session_language_level = session.language_level if session else "b1"
        logger.info(f"[generate_hints] Retrieved session level: {session_language_level} for session {session_id}")

        # Get the most recent messages
        messages = await self.get_session_messages(session_id)
        if not messages:
            # No messages yet, return default hints
            return [
                '"You can ask about his planet using question words. \"What is your planet...\""',
                '"You can introduce yourself using present tense. \"My name is...\""',
                '"You can ask about his rose using simple questions. \"Can you tell me about...\""'
            ]
        
        # Get the latest message
        latest_message = messages[-1]
        character_id = latest_message.character_id
        
        # Get character config USING THE SESSION'S LANGUAGE LEVEL
        character_config = get_character_config(character_id, languageLevel=session_language_level)
        
        # Format conversation for the hint generation (uses level-adjusted system_prompt)
        formatted_conversation = self._format_conversation_for_llm(
            messages, 
            character_config["system_prompt"]
        )
        
        # Generate and return hints (using the hint_prompt from config)
        # Pass character name for better prompt/fallback generation
        character_name = character_config.get("name", "the character")
        return await self._generate_hints(formatted_conversation, character_config["hint_prompt"], character_name)
    
    async def generate_initial_hints(self, session_id: str) -> List[str]:
        """Generate initial hints for a new session based on the greeting (using session language level for config)"""
        # Get the session to retrieve its language level
        session = await self.get_session(session_id)
        session_language_level = session.language_level if session else "b1"

        # Get the session messages (should only be the greeting)
        messages = await self.get_session_messages(session_id)
        if not messages:
            # No messages yet, return default hints
            return [
                '"You can introduce yourself using present tense. \"Hi, I\'m...\""',
                '"You can ask about his planet using question words. \"What is your planet...\""',
                '"You can share something you like using present tense. \"I like...\""'
            ]
        
        # Get the greeting message
        greeting = messages[0]
        character_id = greeting.character_id
        
        # Get character config USING THE SESSION'S LANGUAGE LEVEL
        character_config = get_character_config(character_id, languageLevel=session_language_level)
        
        # Generate hints based on the greeting
        # Pass character name for better prompt/fallback generation
        character_name = character_config.get("name", "the character")
        hints = await self._generate_hints(
            [{"role": "assistant", "content": greeting.content}],
            character_config["hint_prompt"],
            character_name
        )
        
        # Create and add all hints in a batch
        for hint_content in hints:
            hint = StoryHint(
                id=str(uuid4()),
                session_id=session_id,
                message_id=greeting.id,
                content=hint_content,
                is_used=False
            )
            self.db.add(hint)
        
        # Commit all at once
        await self.db.commit()
        
        return hints

    async def check_moderation_records(self, session_id: str, message_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if any messages in a session have been flagged for moderation.
        Used to display moderation warnings in UI.
        
        Parameters:
        - session_id: Session identifier
        - message_id: Message identifier
        
        Returns:
        - Tuple with (has_moderation_flags, inappropriate_reason)
        """
        try:
            from src.shared.message_processing.db import get_processing_results_by_response
            # Fetch any moderation flags for responses related to this message
            
            logger.info(f"Checking moderation records for session {session_id}, message {message_id}")
            
            try:
                moderation_records = await get_processing_results_by_response(
                    self.db, 
                    session_id, 
                    message_id
                )
            except ImportError:
                logger.error("Failed to import get_processing_results_by_response")
                return False, None
            except Exception as db_error:
                logger.error(f"Database error checking moderation records: {str(db_error)}")
                return False, None
            
            if not moderation_records:
                logger.info(f"No moderation records found for {session_id}, {message_id}")
                return False, None
                
            if any(not record.is_appropriate for record in moderation_records):
                # Get the first inappropriate record to use its reason
                inappropriate_record = next((r for r in moderation_records if not r.is_appropriate), None)
                inappropriate_reason = "Content moderation policy violation"
                
                if inappropriate_record and inappropriate_record.inappropriate_reason:
                    inappropriate_reason = inappropriate_record.inappropriate_reason
                    
                logger.info(f"Moderation flag found: {inappropriate_reason}")
                return True, inappropriate_reason
            
            return False, None
        except Exception as e:
            logger.error(f"Error checking moderation records: {str(e)}")
            logger.exception("Details:")
            return False, None 