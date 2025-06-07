from typing import List, Dict, Any, Optional, Tuple, AsyncIterator
import logging
import asyncio
import json
import time
from datetime import datetime
from sqlalchemy import select, and_, func, exists, text
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from src.features.sandbox.models import SandboxSession, SandboxMessage
from src.features.sandbox.characters import get_character_config
from src.shared.llm.client import LLMClient
from src.shared.services import BaseChatService

logger = logging.getLogger(__name__)

class SandboxService(BaseChatService):
    def __init__(self, llm_client: LLMClient, db: AsyncSession):
        """Initialize the sandbox service."""
        super().__init__(llm_client, db, SandboxSession, SandboxMessage)
        logger.debug("SandboxService initialized")
    
    async def create_session(self, db: AsyncSession, user_id: int, title: Optional[str] = None, character_id: str = "little-prince", language_level: str = "b1") -> SandboxSession:
        """Create a new sandbox session, storing the language level."""
        try:
            session_id = str(uuid4())
            # Fetch greeting first to separate blocking I/O from DB transaction
            greeting_content = self._get_character_greeting(character_id, language_level)
            final_title = title or f"Chat with {character_id} {datetime.now().strftime('%Y-%m-%d')}"
            
            # Try using direct SQL instead of ORM to avoid the updated_at issue
            
            # Check if the column exists to determine approach
            result = await db.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name = 'sandbox_sessions' AND column_name = 'updated_at'")
            )
            has_updated_at = result.scalar() is not None
            
            if has_updated_at:
                # Use the ORM approach if the column exists
                session = self.session_model(
                    id=session_id,
                    user_id=user_id,
                    title=final_title,
                    is_active=True,
                    language_level=language_level
                )
                db.add(session)
                await db.commit()
                await db.refresh(session)
            else:
                # Use direct SQL if the column doesn't exist
                now = datetime.utcnow()
                await db.execute(
                    text("INSERT INTO sandbox_sessions (id, user_id, created_at, is_active, title, language_level) VALUES (:id, :user_id, :created_at, :is_active, :title, :language_level)"),
                    {
                        "id": session_id,
                        "user_id": user_id,
                        "created_at": now,
                        "is_active": True,
                        "title": final_title,
                        "language_level": language_level
                    }
                )
                await db.commit()
                
                # Construct a session object for return
                result = await db.execute(select(self.session_model).where(self.session_model.id == session_id))
                session = result.scalar_one_or_none()
                
                if not session:
                    # Manual construction if query fails
                    session = self.session_model()
                    session.id = session_id
                    session.user_id = user_id
                    session.created_at = now
                    session.is_active = True
                    session.title = final_title
                    session.language_level = language_level
            
            # Now that session is committed (or creation attempted via SQL),
            # create and commit the greeting message.
            greeting_id = str(uuid4())
            greeting_message = self.message_model(
                session_id=session.id,
                role="assistant",
                content=greeting_content,
                message_id=greeting_id,
                character_id=str(character_id),
                is_complete=True
            )
            
            db.add(greeting_message)
            await db.commit()
            
            # Refresh the session object to load all attributes before returning
            # This prevents lazy-loading issues in the calling function (route handler)
            await db.refresh(session)
            
            return session
            
        except Exception as e:
            logger.error(f"Error in create_session: {str(e)}")
            logger.exception("Create session error details:")
            raise
            
    def _get_character_greeting(self, character_id: str, language_level: str = "b1") -> str:
        """Get greeting message for a character"""
        try:
            character = get_character_config(character_id, languageLevel=language_level)
            return character["greeting"]
        except:
            # Fallback greeting
            return "Hello! I'm here to chat with you."
    
    async def session_exists(self, db: AsyncSession, session_id: str) -> bool:
        """Check if a session exists"""
        stmt = select(exists().where(self.session_model.id == session_id))
        result = await db.execute(stmt)
        return result.scalar()
    
    async def session_has_messages(self, db: AsyncSession, session_id: str) -> bool:
        """Check if a session has any messages"""
        stmt = select(exists().where(self.message_model.session_id == session_id))
        result = await db.execute(stmt)
        return result.scalar()
    
    async def process_user_message(
        self, 
        db: AsyncSession, 
        session_id: str, 
        user_message: str, 
        message_id: str,
        character_id: str = "little-prince"
    ) -> Dict[str, Any]:
        """Process a user message, save it, get LLM response, and generate hint"""
        # First, get the session to ensure it exists and is active
        session = await self.get_session(db, session_id)
        if not session or not session.is_active:
            raise ValueError(f"Session {session_id} not found or inactive")
            
        # Save user message
        user_msg = await self.save_message(
            db, 
            session_id, 
            "user", 
            user_message, 
            message_id,
            character_id
        )
        
        # Get conversation history for context
        conversation_history = await self.get_session_messages(db, session_id)
        
        # Get character config
        character_config = get_character_config(character_id)
        
        # Format conversation history for the LLM
        formatted_conversation = self._format_conversation_for_llm(
            conversation_history, 
            character_config["system_prompt"]
        )
        
        # Get character response
        character_response = await self._generate_character_response(formatted_conversation)
        
        # Save character response with same message_id
        char_msg = await self.save_message(
            db, 
            session_id, 
            "assistant", 
            character_response, 
            message_id,
            character_id
        )
        
        # Generate hint (but don't save it)
        hint = await self._generate_hint(
            formatted_conversation + [
                {"role": "assistant", "content": character_response}
            ],
            character_config["hint_prompt"]
        )
        
        return {
            "user_message": user_msg,
            "assistant_message": char_msg,
            "hint": hint
        }
    
    def _format_conversation_for_llm(
        self, 
        messages: List[SandboxMessage], 
        system_prompt: str
    ) -> List[Dict[str, str]]:
        """Format conversation history for LLM input"""
        formatted_messages = [{"role": "system", "content": system_prompt}]
        
        for msg in messages:
            # Convert "user" and "assistant" roles directly
            formatted_messages.append({
                "role": msg.role,
                "content": msg.content
            })
            
        return formatted_messages
    
    async def _generate_character_response(self, conversation: List[Dict[str, str]]) -> str:
        """Generate a response from the character LLM"""
        try:
            response = await self.llm_client.generate_text(json.dumps(conversation))
            return response
        except Exception as e:
            logger.error(f"Error generating character response: {str(e)}")
            return "Oh! I'm sorry, I seem to be lost in my thoughts. Could you please repeat what you said?"
    
    async def _generate_hint(self, conversation: List[Dict[str, str]], hint_prompt: str) -> str:
        """Generate a hint for the user based on conversation history"""
        try:
            # Find the Little Prince's most recent message
            last_prince_message = None
            for msg in reversed(conversation):
                if msg.get("role") == "assistant":
                    last_prince_message = msg.get("content")
                    break
                    
            # Create a new prompt for the hint system
            hint_conversation = [
                {"role": "system", "content": hint_prompt},
                {"role": "user", "content": f"ONLY analyze the Little Prince's MOST RECENT message and provide ONE helpful hint that directly responds to what he just said. His last message is: \"{last_prince_message}\"\n\nMake sure the hint directly addresses something specific in this message. Format the hint as instructed in the system prompt."}
            ]
            
            raw_hint = await self.llm_client.generate_text(json.dumps(hint_conversation))
            
            # Process the response to ensure proper formatting
            import re
            
            # Clean up the hint
            # Strip any numbering, extra quotes, etc.
            hint = raw_hint.strip()
            
            # If the hint doesn't follow our format (starts with "You can" and has "using" for grammar guidance)
            if not (hint.startswith('"You can') or hint.startswith('You can')) or ' using ' not in hint.lower():
                # Generate a context-aware fallback hint based on whether the last message was a question
                if last_prince_message and "?" in last_prince_message:
                    return '"You can answer his question directly using present tense. \"I think...\""'
                else:
                    return '"You can respond to what he just said using present tense. \"I agree that...\""'
            
            # Ensure proper quote formatting - if not already properly quoted
            if not hint.startswith('"'):
                hint = f'"{hint}"'
                
            return hint
            
        except Exception as e:
            logger.error(f"Error generating hint: {str(e)}")
            return '"You can ask about his planet using question words. \"What is your planet...\""'
    
    async def stream_character_response(
        self, 
        session_id: str, 
        conversation: List[Dict[str, str]],
        character_id: str = "little-prince"
    ) -> AsyncIterator[str]:
        """Stream the character response chunks"""
        try:
            # Get character config
            character_config = get_character_config(character_id)
            
            # Format with character system prompt
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

    async def save_subtitle(
        self, 
        db: AsyncSession, 
        session_id: str, 
        content: str, 
        message_id: str,
        character: str,
        timestamp: Optional[int] = None
    ) -> Optional[SandboxMessage]:
        """Save a subtitle message directly to the database with fallback mechanisms"""
        try:
            # First try with the ORM approach
            message = self.message_model(
                id=str(uuid4()),
                session_id=session_id,
                role="assistant",
                content=content,
                message_id=message_id,
                character_id=character,
                is_complete=True,
                created_at=datetime.utcnow()
            )
            
            db.add(message)
            try:
                await db.commit()
                await db.refresh(message)
                logger.info(f"Stored subtitle in database with message_id {message_id}")
                return message
            except Exception as orm_error:
                logger.warning(f"ORM approach failed, trying direct SQL: {str(orm_error)}")
                await db.rollback()
                
                # Try with direct SQL as fallback
                now = datetime.utcnow()
                await db.execute(
                    text("""
                        INSERT INTO sandbox_messages 
                            (id, session_id, role, content, created_at, message_id, character_id, is_complete) 
                        VALUES 
                            (:id, :session_id, :role, :content, :created_at, :message_id, :character_id, :is_complete)
                    """),
                    {
                        "id": str(uuid4()),
                        "session_id": session_id,
                        "role": "assistant",
                        "content": content,
                        "created_at": now,
                        "message_id": message_id,
                        "character_id": character,
                        "is_complete": True
                    }
                )
                await db.commit()
                
                # Construct a message object for return
                result = await db.execute(
                    select(self.message_model).where(self.message_model.message_id == message_id)
                )
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.error(f"Error saving subtitle: {str(e)}")
            logger.exception("Subtitle save error details:")
            return None
