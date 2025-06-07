from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings
import logging
from urllib.parse import urlparse, parse_qs
import ssl

logger = logging.getLogger(__name__)

# Parse the URL to handle SSL parameters properly
def get_engine_args():
    # Get the base URL without sslmode
    url = settings.DATABASE_URL
    parsed = urlparse(url)
    
    # Extract query parameters
    params = parse_qs(parsed.query)
    
    # Reconstruct the URL without query parameters
    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    # Convert to asyncpg format
    async_url = clean_url.replace("postgresql://", "postgresql+asyncpg://")
    
    # Connection args
    connect_args = {}
    
    # Handle SSL if needed
    if 'sslmode' in params:
        sslmode = params['sslmode'][0]
        if sslmode in ('require', 'verify-ca', 'verify-full'):
            # Create a proper SSLContext object
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Add the SSLContext to connect_args
            connect_args["ssl"] = ssl_context
    
    return async_url, connect_args

# Get URL and connection args
db_url, connect_args = get_engine_args()

# Create async SQLAlchemy engine
engine = create_async_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

# Create async session factory
SessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# Async dependency to get DB session
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Initialize database (create tables)
async def init_db():
    try:
        # Import models here
        from src.features.auth.models import User
        from src.shared.message_processing.models import MessageProcessing
        from src.features.sandbox.models import SandboxSession, SandboxMessage
        from src.features.journey.models import JourneySession, JourneyResponse
        # Add Story Mode models
        from src.features.story_mode.models import StorySession, StoryMessage, StoryHint
        
        # Get list of existing tables to avoid trying to create tables that already exist
        logger.info("Creating database tables if they don't exist")
        
        # Create tables that don't exist yet - use checkfirst=True to avoid errors on existing tables
        async with engine.begin() as conn:
            # This will skip tables that already exist
            await conn.run_sync(lambda schema: Base.metadata.create_all(schema, checkfirst=True))
            
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise