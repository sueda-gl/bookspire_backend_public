import logging
from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from uuid import uuid4
import uvicorn
import json  # Add explicit import
import time  # Add explicit import

from src.core.config import settings
from src.core.events import create_start_app_handler, create_stop_app_handler
from src.core.exceptions import add_exception_handlers
from src.core.db import engine, Base

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events"""
    # Startup
    logger.info("Starting up application")
    start_handler = create_start_app_handler(app)
    await start_handler()
    
    await startup_event()
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    stop_handler = create_stop_app_handler(app)
    await stop_handler()

def create_application() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://bookspire-7ipqv.ondigitalocean.app", *settings.CORS_ORIGINS],
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add application-wide exception handlers
    add_exception_handlers(app)
    
    # --- API Router Setup ---
    # Central router for all versioned API endpoints
    api_router = APIRouter(prefix="/api")

    # Import and include feature routers
    from src.features.auth.routes import router as auth_router
    from src.features.journey.routes import router as journey_router
    from src.features.sandbox.routes import router as sandbox_router
    from src.features.penpal.routes import router as penpal_router
    from src.features.story_mode.routes import router as story_router
    
    api_router.include_router(auth_router)
    api_router.include_router(journey_router)
    api_router.include_router(sandbox_router)
    api_router.include_router(penpal_router)
    api_router.include_router(story_router)
    
    app.include_router(api_router)

    # --- Root-level and Alias Endpoints ---
    # These are kept for backward compatibility with the frontend.

    @app.get("/health")
    async def health_check():
        """Simple health check endpoint"""
        return {
            "status": "healthy",
            "message": "Application is running"
        }
    
    # --- WebSocket Endpoints ---
    # Centralized for clarity. All paths are preserved.
    from src.features.story_mode.websocket import websocket_endpoint as story_ws_endpoint
    from src.features.journey.websocket import journey_websocket_endpoint
    from src.features.sandbox.websocket import subtitle_websocket_endpoint

    @app.websocket("/api/story/ws/{session_id}")
    async def websocket_story(websocket: WebSocket, session_id: str):
        token = websocket.query_params.get("token")
        await story_ws_endpoint(websocket, session_id, token)

    @app.websocket("/ws/journey/{session_id}")
    async def websocket_journey(websocket: WebSocket, session_id: str):
        token = websocket.query_params.get("token")
        await journey_websocket_endpoint(websocket, session_id, token)
    
    # Alias for sandbox websocket, used by frontend
    @app.websocket("/subtitles")
    async def subtitle_websocket_alias(websocket: WebSocket):
        token = websocket.query_params.get("token")
        session_id = websocket.query_params.get("session_id", str(uuid4()))
        await subtitle_websocket_endpoint(websocket, session_id, token)

    # Note: The original /ws/sandbox/{session_id} is preserved via the sandbox router
    # if it's defined there. If not, it can be added here for full compatibility.

    return app

app = create_application()

# Debug print of all routes
for route in app.routes:
    if hasattr(route, 'methods'):
        logger.info(f"Registered route: {route.path} [{', '.join(route.methods)}]")
    else:
        # This is for WebSocket routes which don't have methods
        logger.info(f"Registered WebSocket route: {route.path}")

@app.on_event("startup")
async def startup_event():
    """Initialize the database on startup"""
    from src.core.db import init_db
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Initialize database with seed data if needed
    await init_db()

if __name__ == "__main__":
    # Make sure we're running on port 5000 to match the frontend expectation
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)