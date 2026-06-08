"""
Authentication Endpoints with Swagger Security
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.models.database import User, get_db
from app.models.schemas import (
    UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
)
from app.core.security import (
    get_password_hash, verify_password, create_access_token, 
    create_refresh_token, verify_token
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Security scheme for Swagger
security = HTTPBearer()

# ==================== REGISTER ====================

@router.post("/register", response_model=TokenResponse, summary="Register new user")
async def register(
    request: UserRegisterRequest, 
    db: Session = Depends(get_db)
):
    """
    Register a new user account
    
    **Returns JWT tokens for immediate login**
    
    Example:
    ```json
    {
        "email": "john@example.com",
        "password": "SecurePass123",
        "name": "John Doe"
    }
    ```
    """
    
    # Check if email already registered
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        logger.warning(f"Registration attempt with existing email: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=request.email,
        name=request.name,
        hashed_password=get_password_hash(request.password)
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"✅ User registered: {user.email}")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # Generate tokens
    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600
    )

# ==================== LOGIN ====================

@router.post("/login", response_model=TokenResponse, summary="Login user")
async def login(
    request: UserLoginRequest, 
    db: Session = Depends(get_db)
):
    """
    Login with email and password
    
    **Returns JWT tokens for API authentication**
    
    Example:
    ```json
    {
        "email": "john@example.com",
        "password": "SecurePass123"
    }
    ```
    
    Copy the `access_token` value and click the "Authorize" button at the top!
    """
    
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        logger.warning(f"Login attempt with non-existent email: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(request.password, user.hashed_password):
        logger.warning(f"Failed login for: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    logger.info(f"✅ User logged in: {user.email}")
    
    # Generate tokens
    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600
    )

# ==================== GET CURRENT USER ====================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    
    WHY:
    - Works automatically in Swagger UI after clicking Authorize
    - Validates token
    - Gets user from database
    """
    
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

@router.get("/me", response_model=UserResponse, summary="Get current user")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    **Requires Authorization**
    
    Click "Authorize" button first, paste your access_token!
    """
    return current_user

# ==================== REFRESH TOKEN ====================

@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    **Paste your refresh_token in the Authorization field**
    
    Access tokens expire in 1 hour. Use refresh tokens to get new access tokens.
    """
    
    token = credentials.credentials
    
    # Verify refresh token
    payload = verify_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Generate new access token
    access_token = create_access_token({"sub": user.id})
    refresh_token_new = create_refresh_token({"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_new,
        expires_in=3600
    )