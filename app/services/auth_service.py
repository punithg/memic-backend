"""Authentication service for JWT and password management."""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings


# Password hashing context with bcrypt (cost factor 12)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> tuple[str, int]:
        """
        Create a JWT access token.
        
        Args:
            user_id: User ID to encode in token
            expires_delta: Optional custom expiry time
            
        Returns:
            Tuple of (token, expires_in_seconds)
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
            expires_in = int(expires_delta.total_seconds())
        else:
            expires_in = settings.jwt_expiry_hours * 3600
            expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiry_hours)
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        # Use JWT secret from settings
        if not settings.jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY not configured")
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        return encoded_jwt, expires_in
    
    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            User ID from token if valid, None otherwise
        """
        try:
            if not settings.jwt_secret_key:
                return None
            
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            
            return user_id
        
        except JWTError:
            return None

