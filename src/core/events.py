import logging
from typing import Callable
from fastapi import FastAPI

from src.shared.llm.client import LLMClient
# Redis service import path may have changed in the feature-based structure
# from src.shared.redis.service import RedisService
from src.core.db import init_db

logger = logging.getLogger(__name__)

def create_start_app_handler(app: FastAPI) -> Callable:
    """
    Creates a function that initializes services on app startup
    """
    async def start_app() -> None:
        logger.info("Initializing application services")
        
        # Initialize database
        await init_db()
        
        # Initialize and store Redis service
        # Redis service initialization commented out until correct import path is determined
        # app.state.redis_service = RedisService()
        # logger.info("Redis service initialized")
        
        # Initialize and store LLM client
        app.state.llm_client = LLMClient()
        logger.info("LLM client initialized")
        
        # Initialize and store Message Processing Service
        from src.shared.message_processing.service import MessageProcessingService
        app.state.message_processor = MessageProcessingService(app.state.llm_client)
        logger.info("Message processing service initialized")
        
        logger.info("Application startup complete")
    
    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    """
    Creates a function that cleans up services on app shutdown
    """
    async def stop_app() -> None:
        logger.info("Shutting down application services")
        
        # Clean up LLM client
        if hasattr(app.state, "llm_client") and app.state.llm_client:
            await app.state.llm_client.close()
            logger.info("LLM client closed")
        
        logger.info("Application shutdown complete")
    
    return stop_app