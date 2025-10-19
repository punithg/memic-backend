"""Authentication middleware and dependencies."""

from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.services.auth_service import AuthService
from app.core.tenant_context import TenantContext


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to extract and validate current user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials with JWT token
        db: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extract token
    token = credentials.credentials
    
    # Verify token and get user_id
    user_id_str = AuthService.verify_token(token)
    if user_id_str is None:
        raise credentials_exception
    
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception
    
    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_tenant_context(
    current_user: User = Depends(get_current_user)
) -> TenantContext:
    """
    Dependency to create tenant context from current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        TenantContext with user information
    """
    return TenantContext(user=current_user)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to optionally extract current user from JWT token.
    Returns None if no token or invalid token.
    
    Args:
        credentials: HTTP Bearer credentials (optional)
        db: Database session
        
    Returns:
        Current user if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_id_str = AuthService.verify_token(token)
        if user_id_str is None:
            return None
        
        user_id = UUID(user_id_str)
        user = db.query(User).filter(User.id == user_id).first()
        
        if user and user.is_active:
            return user
    except (ValueError, HTTPException):
        pass
    
    return None

