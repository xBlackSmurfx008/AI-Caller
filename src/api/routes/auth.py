"""Authentication routes"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext
import uuid

from src.database.database import get_db
from src.database.models import User
from src.database.schemas import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
    TokenRefresh,
)
from src.api.middleware.auth import get_current_user
from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)  # Refresh tokens last 30 days
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """Authenticate user and return JWT token"""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    # Store refresh token in user metadata
    # TODO: Consider moving to Redis or separate table for better scalability
    if user.meta_data is None:
        user.meta_data = {}
    user.meta_data["refresh_token"] = refresh_token
    db.commit()
    
    logger.info("user_logged_in", user_id=user.id, email=user.email)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: TokenRefresh,
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token"""
    try:
        payload = jwt.decode(
            refresh_data.refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        user_id: str = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Verify refresh token matches stored token
    stored_token = user.meta_data.get("refresh_token") if user.meta_data else None
    if stored_token != refresh_data.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Create new access token
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logout user and invalidate refresh token"""
    # Remove refresh token from user metadata
    if current_user.meta_data:
        current_user.meta_data.pop("refresh_token", None)
        db.commit()
    
    logger.info("user_logged_out", user_id=current_user.id)
    return {"message": "Successfully logged out"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    
    # Create new user
    user = User(
        id=str(uuid.uuid4()),
        email=user_data.email,
        name=user_data.name,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        is_superuser=False,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info("user_registered", user_id=user.id, email=user.email)
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user information"""
    return UserResponse.model_validate(current_user)


@router.post("/forgot-password")
async def forgot_password(
    email: str,
    db: Session = Depends(get_db),
):
    """Request password reset"""
    user = db.query(User).filter(User.email == email).first()
    
    # Don't reveal if user exists (security best practice)
    if user:
        # Generate reset token
        reset_token = create_access_token(
            data={"sub": user.id, "type": "password_reset"},
            expires_delta=timedelta(hours=1)  # Reset token expires in 1 hour
        )
        
        # Store reset token in metadata
        if user.meta_data is None:
            user.meta_data = {}
        user.meta_data["password_reset_token"] = reset_token
        db.commit()
        
        # Send email with reset link
        try:
            from src.services.email_service import email_service
            email_sent = email_service.send_password_reset_email(
                to_email=email,
                reset_token=reset_token
            )
            if not email_sent:
                logger.warning("password_reset_email_failed", user_id=user.id, email=email)
        except Exception as e:
            logger.error("password_reset_email_error", error=str(e), user_id=user.id, email=email)
        
        logger.info("password_reset_requested", user_id=user.id, email=email)
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db),
):
    """Reset password using reset token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type",
            )
        user_id: str = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Verify token matches stored token
    stored_token = user.meta_data.get("password_reset_token") if user.meta_data else None
    if stored_token != token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    # Remove reset token
    if user.meta_data:
        user.meta_data.pop("password_reset_token", None)
    db.commit()
    
    logger.info("password_reset_completed", user_id=user.id)
    return {"message": "Password has been reset successfully"}

