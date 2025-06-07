from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.features.auth.models import User
from src.features.auth.schemas import UserCreate
from src.core.security import get_password_hash, verify_password

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email"""
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username"""
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
       stmt = select(User).where(User.id == user_id)
       result = await db.execute(stmt)
       return result.scalar_one_or_none()
   
async def get_user_by_student_id(db: AsyncSession, student_id: str) -> Optional[User]:
       if hasattr(User, 'student_id'):
           stmt = select(User).where(User.student_id == student_id)
           result = await db.execute(stmt)
           return result.scalar_one_or_none()
       return None

async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Create new user"""
    hashed_password = get_password_hash(user_data.password)
    
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user

async def authenticate_user(db: AsyncSession, username_or_email: str, password: str) -> Optional[User]:
    """Authenticate user - works with either username or email"""
    user = None
    if '@' in username_or_email:
        user = await get_user_by_email(db, username_or_email)
    else:
        user = await get_user_by_username(db, username_or_email)
    
    if not user or not verify_password(password, user.password_hash):
        return None
        
    return user

async def update_password(db: AsyncSession, user: User, new_password: str) -> User:
       user.password_hash = get_password_hash(new_password)
       await db.commit()
       await db.refresh(user)
       return user
   
async def deactivate_user(db: AsyncSession, user_id: int) -> Optional[User]:
       user = await get_user_by_id(db, user_id)
       if not user:
           return None
       
       user.is_active = False
       await db.commit()
       await db.refresh(user)
       return user