"""DTOs for authentication endpoints."""

from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime


class SignupRequest(BaseModel):
    """Request body for user signup."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    name: str = Field(..., min_length=1, max_length=255, description="User full name")


class LoginRequest(BaseModel):
    """Request body for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Response body for authentication token."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry time in seconds")


class UserResponse(BaseModel):
    """Response body for user information (NO password!)."""
    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

