"""Security utilities: authentication, password hashing, JWT tokens"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
# from fastapi.security import OAuth2AuthorizationCodeBearer


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends

security = HTTPBearer()

async def get_token_from_header(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract token from Authorization header"""
    return credentials.credentials