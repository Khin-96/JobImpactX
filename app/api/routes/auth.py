"""
Authentication API Route.
User authentication and JWT token generation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.db.session import get_db
from app.db.models import User
from app.db.queries import get_user_by_username, get_user_by_email, create_user
from app.auth.security import (
    verify_password,
    hash_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """JWT token data."""
    username: Optional[str] = None
    role: Optional[str] = None


class UserCreate(BaseModel):
    """User creation request."""
    username: str
    email: EmailStr
    password: str
    role: str = "Analyst"


class UserResponse(BaseModel):
    """User information response."""
    id: str
    username: str
    email: str
    role: str
    is_active: bool


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate user with username and password.
    
    Args:
        db: Database session
        username: Username
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
    """
    user = get_user_by_username(db, username)
    
    if not user:
        return None
    
    if not user.is_active:
        logger.warning(f"Inactive user attempted login: {username}")
        return None
    
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Failed login attempt for user: {username}")
        return None
    
    return user


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Token:
    """
    OAuth2 compatible token login endpoint.
    
    Args:
        form_data: Username and password from OAuth2 form
        
    Returns:
        JWT access token
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in: {user.username} (role: {user.role})")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Register a new user account.
    
    Note: In production, this should be restricted or require admin approval.
    """
    
    # Check if username already exists
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate role
    valid_roles = ["Admin", "Analyst", "Viewer"]
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    # In production, only allow Viewer/Analyst registration
    # Admins should be created manually or through separate process
    if user_data.role == "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot register as Admin. Contact system administrator."
        )
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    try:
        user = create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role=user_data.role
        )
        
        logger.info(f"New user registered: {user.username} (role: {user.role})")
        
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active
        )
        
    except Exception as e:
        logger.error(f"User registration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_token: str,
    db: Session = Depends(get_db)
) -> Token:
    """
    Refresh an existing JWT token.
    
    Note: This is a simplified implementation. In production, consider using refresh tokens.
    """
    from app.auth.security import verify_token
    
    try:
        payload = verify_token(current_token)
        user_id = payload.get("sub")
        username = payload.get("username")
        role = payload.get("role")
        
        if not user_id or not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Generate new token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id, "username": username, "role": role},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    db: Session = Depends(get_db),
    token: str = Depends()
) -> UserResponse:
    """
    Get current user information from JWT token.
    
    Requires valid authentication token.
    """
    from app.auth.security import verify_token
    
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        from app.db.queries import get_user_by_id
        from uuid import UUID
        
        user = get_user_by_id(db, UUID(user_id))
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active
        )
        
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
