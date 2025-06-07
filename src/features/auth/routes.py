from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta
from typing import Optional

from src.core.db import get_db
from src.features.auth import schemas, service
from src.core.security import create_access_token, get_current_user, get_current_active_user, oauth2_scheme, verify_password
from src.features.auth.models import User
from src.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=schemas.UserResponse)
async def register_user(user_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    # Check if user with this email already exists
    user = await service.get_user_by_email(db, user_data.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username is taken
    if await service.get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    return await service.create_user(db, user_data)

@router.post("/login", response_model=schemas.Token)
async def login(
    login_data: schemas.LoginData,
    db: AsyncSession = Depends(get_db)
):
    """Log in and get access token"""
    username = login_data.username
    password = login_data.password
    
    print(f"Login endpoint hit with username: {username}")  # Debug log
    
    # Try to find user by username first
    user = await service.get_user_by_username(db, username)
    
    # If not found by username and contains @, try email
    if not user and '@' in username:
        user = await service.get_user_by_email(db, username)
    
    # If still not found, try student_id (if applicable to your model)
    if not user:
        user = await service.get_user_by_student_id(db, username)
    
    # Verify credentials
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with additional claims
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Include all relevant claims
    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "role": getattr(user, "role", "user")  # Default to "user" if role not defined
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    print(f"Created token for user: {user.id}")  # Debug log
    
    # Prepare the response - match the Flask implementation more closely
    response = {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": user.role,
        "name": f"{user.first_name} {user.last_name}"
    }
    
    # Add role-specific information like in Flask implementation
    if user.role == "teacher":
        response.update({
            "email": user.email,
            "subject": getattr(user, "subject", None)
        })
    elif user.role == "student":
        response.update({
            "student_id": getattr(user, "student_id", None),
            "grade": getattr(user, "grade", None),
            "section": getattr(user, "section", None)
        })
    
    return response

@router.get("/me", response_model=schemas.UserResponse)
async def get_user_me(current_user = Depends(get_current_active_user)):
    """Get current user information"""
    print(f"Current user ID: {current_user.id}")  # Debug log
    return current_user

@router.post("/create-test-users", response_model=schemas.TestUsersResponse)
async def create_test_users(db: AsyncSession = Depends(get_db)):
    """Create test users for development"""
    try:
        # Check if users already exist
        student = await service.get_user_by_username(db, "test_student")
        teacher = await service.get_user_by_username(db, "test_teacher")
        
        # Create test student if not exists
        if not student:
            student_data = schemas.UserCreate(
                username="test_student",
                email="student@test.com",
                password="test123",
                first_name="Test",
                last_name="Student"
            )
            student = await service.create_user(db, student_data)
            
            # Set additional fields if your model supports them
            # This will depend on your specific User model implementation
            # student.role = "student"
            # student.student_id = "ST123"
            # student.grade = "10"
            # student.section = "A"
            # await db.commit()
        
        # Create test teacher if not exists
        if not teacher:
            teacher_data = schemas.UserCreate(
                username="test_teacher",
                email="teacher@test.com",
                password="test123",
                first_name="Test",
                last_name="Teacher"
            )
            teacher = await service.create_user(db, teacher_data)
            
            # Set additional fields if your model supports them
            # teacher.role = "teacher"
            # teacher.subject = "Mathematics"
            # await db.commit()
        
        return {
            "message": "Test users ready",
            "student": {
                "id": student.id,
                "username": "test_student",
                "password": "test123"
            },
            "teacher": {
                "id": teacher.id,
                "username": "test_teacher",
                "password": "test123"
            }
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating test users: {str(e)}"
        )

@router.get("/debug-token")
async def debug_token(current_user = Depends(get_current_active_user)):
    """Debug endpoint to check the current user's identity from JWT token"""
    # Get user details
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "role": getattr(current_user, "role", "user")  # Default to "user" if role not defined
    }

@router.post("/change-password", response_model=schemas.UserResponse)
async def change_password(
    password_data: schemas.PasswordChange,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    updated_user = await service.update_password(db, current_user, password_data.new_password)
    return updated_user

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """OAuth2 compatible token login endpoint, used for OAuth2 clients"""
    # Convert the form data to our LoginData schema
    login_data = schemas.LoginData(
        username=form_data.username,
        password=form_data.password
    )
    
    # Reuse the login logic by calling our JSON-based login endpoint
    return await login(login_data=login_data, db=db)
