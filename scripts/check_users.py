import sys
import asyncio
import logging
from sqlalchemy import select, text
from src.core.db import SessionLocal, engine

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

async def check_users():
    """List all users in the database directly with SQL query instead of ORM"""
    logger.info("Checking users in database...")
    
    async with engine.begin() as conn:
        # Direct SQL query to avoid relationship loading issues
        result = await conn.execute(text("""
            SELECT id, username, email, is_active, role, first_name, last_name, 
                   student_id, grade, section
            FROM users
        """))
        
        users = result.fetchall()
        
        if not users:
            logger.info("No users found in the database!")
            return
        
        logger.info(f"Found {len(users)} users in the database:")
        print("\n" + "="*100)
        print(f"{'ID':4} | {'Username':<20} | {'Email':<30} | {'Role':<10} | {'Name':<20} | {'Active'}")
        print("-"*100)
        
        for user in users:
            name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            print(f"{user.id:4} | {user.username:<20} | {(user.email or 'N/A'):<30} | {user.role or 'N/A':<10} | {name:<20} | {user.is_active}")
            
            # Print student info if available
            if user.student_id or user.grade or user.section:
                print(f"     └─ Student: ID={user.student_id or 'N/A'}, Grade={user.grade or 'N/A'}, Section={user.section or 'N/A'}")
        
        print("="*100 + "\n")

async def main():
    await check_users()

if __name__ == "__main__":
    asyncio.run(main()) 