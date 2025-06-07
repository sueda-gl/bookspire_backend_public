# This file will contain shared base services to promote code reuse. 

from typing import List, Dict, Any, Optional, Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import json
from uuid import uuid4

from src.core.db import Base
from src.shared.llm.client import LLMClient

logger = logging.getLogger(__name__)

# Define generic types for our database models
SessionModel = TypeVar("SessionModel", bound=Base)
MessageModel = TypeVar("MessageModel", bound=Base)

class BaseChatService:
    """
    A base service providing common chat functionalities.

    This service encapsulates shared logic for session and message management,
    LLM interaction, and conversation formatting to be reused by feature-specific
    services.
    """
    def __init__(
        self,
        llm_client: LLMClient,
        db: AsyncSession,
        session_model: Type[SessionModel],
        message_model: Type[MessageModel]
    ):
        self.llm_client = llm_client
        self.db = db
        self.session_model = session_model
        self.message_model = message_model
        logger.debug(f"{self.__class__.__name__} initialized")

    async def get_session(self, session_id: str) -> Optional[SessionModel]:
        """Get a session by its ID."""
        stmt = select(self.session_model).where(self.session_model.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_session_messages(self, session_id: str) -> List[MessageModel]:
        """Get all messages for a session, ordered by creation time."""
        stmt = select(self.message_model).where(
            self.message_model.session_id == session_id
        ).order_by(self.message_model.created_at)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_id: Optional[str] = None,
        character_id: str = "little-prince",
        is_complete: bool = True
    ) -> MessageModel:
        """Save a message to the database."""
        message = self.message_model(
            id=str(uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            message_id=message_id or str(uuid4()),
            character_id=character_id,
            is_complete=is_complete
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    def _format_conversation_for_llm(
        self,
        messages: List[MessageModel],
        system_prompt: str
    ) -> List[Dict[str, str]]:
        """Format conversation history for LLM input."""
        formatted_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            formatted_messages.append({"role": msg.role, "content": msg.content})
        return formatted_messages

    async def _generate_character_response(self, conversation: List[Dict[str, str]]) -> str:
        """Generate a response from the character LLM."""
        try:
            response = await self.llm_client.generate_text(json.dumps(conversation))
            return response
        except Exception as e:
            logger.error(f"Error generating character response: {str(e)}")
            # Provide a generic, user-friendly error message
            return "Oh! I'm sorry, I seem to be lost in my thoughts. Could you please repeat what you said?" 