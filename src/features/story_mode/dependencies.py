# Chat-specific dependencies 
from typing import Optional, AsyncGenerator
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.core.db import get_db
from src.shared.llm.client import LLMClient
from src.features.story_mode.service import StoryService

logger = logging.getLogger(__name__)

async def get_story_service(request: Request, db: AsyncSession = Depends(get_db)) -> StoryService:
    """Dependency to get the StoryService instance."""
    # Use the shared LLM client from the application state
    llm_client = request.app.state.llm_client
    
    # Create the service
    service = StoryService(llm_client, db)
    
    return service 