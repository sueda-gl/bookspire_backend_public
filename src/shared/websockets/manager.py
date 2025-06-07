from fastapi import WebSocket
import json
import logging
from typing import Dict, Set, Any

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Manages WebSocket connections for the entire application.
    
    This manager handles connections on a per-session and per-user basis,
    allowing for targeted messaging and broadcasting.
    """
    def __init__(self):
        # A nested dictionary to store active connections:
        # {session_id: {user_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        """

        Accepts and registers a new WebSocket connection.
        Args:
            websocket: The FastAPI WebSocket object.
            session_id: The unique identifier for the session (e.g., chat session).
            user_id: The unique identifier for the user.
        """
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
        
        self.active_connections[session_id][user_id] = websocket
        logger.info(f"WebSocket connected and registered for user {user_id} in session {session_id}")

    async def disconnect(self, session_id: str, user_id: str):
        """
        Removes a WebSocket connection.
        
        Args:
            session_id: The session ID to disconnect from.
            user_id: The user ID to disconnect.
        """
        if session_id in self.active_connections and user_id in self.active_connections[session_id]:
            del self.active_connections[session_id][user_id]
            
            # Clean up the session dictionary if it's empty
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        logger.info(f"WebSocket disconnected for user {user_id} in session {session_id}")

    async def send_message(self, session_id: str, user_id: str, message: Dict[str, Any]):
        """
        Sends a JSON message to a specific user in a specific session.
        
        Args:
            session_id: The session ID to send the message to.
            user_id: The user ID to send the message to.
            message: The JSON-serializable dictionary to send.
        """
        if session_id in self.active_connections and user_id in self.active_connections[session_id]:
            websocket = self.active_connections[session_id][user_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id} in session {session_id}: {e}")
                # Consider auto-disconnecting on send failure
                await self.disconnect(session_id, user_id)

    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any], skip_user_id: str = None):
        """
        Broadcasts a message to all users in a session, with an option to skip one user.
        
        Args:
            session_id: The session to broadcast to.
            message: The JSON-serializable dictionary to send.
            skip_user_id: If provided, this user will not receive the broadcast.
        """
        if session_id in self.active_connections:
            # Create a list of tuples to avoid issues with dictionary size changing during iteration
            connections_to_send = list(self.active_connections[session_id].items())
            for user_id, websocket in connections_to_send:
                if user_id != skip_user_id:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"Failed to broadcast to user {user_id} in session {session_id}: {e}")
                        # Consider auto-disconnecting on send failure
                        await self.disconnect(session_id, user_id)

# Create a single global instance of the manager to be used across the application
connection_manager = WebSocketManager() 