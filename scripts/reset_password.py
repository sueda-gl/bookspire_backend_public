import sys
import asyncio
import logging
from getpass import getpass
from sqlalchemy import update, text
from src.core.db import engine
from src.features.auth.models import User

# Adjust the path to correctly find the 'src' module from the 'scripts' directory
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

async def reset_password(username, new_password):
    """Reset a user's password"""
    logger.info(f"Resetting password for user: {username}")
    
    # Get password hash
    password_hash = User.get_password_hash(new_password)
    
    async with engine.begin() as conn:
        # First check if the user exists
        result = await conn.execute(
            text("SELECT id, username FROM users WHERE username = :username"),
            {"username": username}
        )
        user = result.fetchone()
        
        if not user:
            logger.error(f"User '{username}' not found!")
            return False
            
        # Update the password
        await conn.execute(
            text("UPDATE users SET password_hash = :password_hash WHERE username = :username"),
            {"username": username, "password_hash": password_hash}
        )
        
        logger.info(f"Password updated for user {username}")
        return True

async def main():
    if len(sys.argv) != 2:
        print("Usage: python reset_password.py <username>")
        return

    username = sys.argv[1]
    
    # Get new password securely (won't show on screen)
    while True:
        password = getpass("Enter new password (min 8 chars, 1 uppercase, 1 digit): ")
        if len(password) < 8:
            print("Password must be at least 8 characters long.")
            continue
        if not any(char.isdigit() for char in password):
            print("Password must contain at least one digit.")
            continue
        if not any(char.isupper() for char in password):
            print("Password must contain at least one uppercase letter.")
            continue
        
        # Confirm password
        confirm = getpass("Confirm new password: ")
        if password != confirm:
            print("Passwords don't match. Please try again.")
            continue
        
        break
    
    result = await reset_password(username, password)
    
    if result:
        print(f"\nPassword successfully reset for user '{username}'")
        print("You should now be able to log in with the new password")
    else:
        print("\nPassword reset failed")

if __name__ == "__main__":
    asyncio.run(main()) 