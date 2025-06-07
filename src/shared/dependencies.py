# src/shared/dependencies.py
from fastapi import Request
from src.shared.message_processing.service import MessageProcessingService

def get_message_processor(request: Request) -> MessageProcessingService:
    """Dependency provider for MessageProcessingService"""
    return request.app.state.message_processor