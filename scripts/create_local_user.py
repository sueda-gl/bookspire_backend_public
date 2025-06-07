# create_local_user.py
import asyncio
import logging
import sys
from getpass import getpass # To securely get password

# Adjust the path to correctly find the 'src' module from the 'scripts' directory
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Core/Auth imports
from src.core.db import SessionLocal # Get the session factory
from src.features.auth.service import create_user
from src.features.auth.schemas import UserCreate
from src.features.auth.models import User # Import User model itself

# --- ADD IMPORTS FOR RELATED MODELS --- 
# These imports are needed for SQLAlchemy to resolve relationships defined in User model
try:
    from src.features.sandbox.models import SandboxSession, SandboxMessage
    from src.features.journey.models import JourneySession, JourneyResponse
    from src.shared.message_processing.models import MessageProcessing
    from src.features.story_mode.models import StorySession, StoryMessage, StoryHint
    # Add any other related models if User links to more
except ImportError as e:
    print(f"Warning: Could not import some related models: {e}")
    print("This might be okay if not creating relationships, but could cause issues.")
# --- END ADDED IMPORTS ---

# Configure logging (optional, but helpful)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting user creation script...")

    # --- User Details ---
    # Modify these values for the user you want to create
    email = input("Enter user email: ")
    username = input("Enter username: ")
    
    # Get and validate password
    while True:
        password = getpass("Enter password (min 8 chars, 1 uppercase, 1 digit): ")
        if len(password) < 8:
            print("Password must be at least 8 characters long.")
            continue
        if not any(char.isdigit() for char in password):
            print("Password must contain at least one digit.")
            continue
        if not any(char.isupper() for char in password):
            print("Password must contain at least one uppercase letter.")
            continue
        # Add any other checks from the validator if needed
        break # Password is valid
        
    first_name = input("Enter first name: ")
    last_name = input("Enter last name: ")
    # Get role as a simple string
    role = input("Enter role (e.g., 'user', 'admin', 'student', 'teacher'): ")

    user_data = UserCreate(
        email=email,
        username=username,
        password=password, # Will be hashed by create_user
        first_name=first_name,
        last_name=last_name,
        role=role # Assign the string role here
    )
    # --- End User Details ---

    logger.info(f"Attempting to create user: {username} ({email})")

    # Get a database session
    async with SessionLocal() as db:
        try:
            # Check if user already exists (optional but good practice)
            # from src.features.auth.service import get_user_by_email, get_user_by_username
            # existing_email = await get_user_by_email(db, user_data.email)
            # existing_username = await get_user_by_username(db, user_data.username)
            # if existing_email or existing_username:
            #     logger.error("User with this email or username already exists.")
            #     return

            # Create the user
            new_user = await create_user(db=db, user_data=user_data)
            logger.info(f"Successfully created user: {new_user.username} (ID: {new_user.id})")
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            # If using transactions (which SessionLocal does by default),
            # the session will likely rollback automatically on error.
        finally:
            # The 'async with SessionLocal() as db:' context manager handles closing
            logger.info("Database session closed.")

if __name__ == "__main__":
    # Ensure the script is run with python create_local_user.py
    # or python -m create_local_user
    asyncio.run(main()) 