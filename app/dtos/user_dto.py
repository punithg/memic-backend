"""DTOs for user management."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserUpdate(BaseModel):
    """Request body for updating user profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="User full name")
    email: Optional[EmailStr] = Field(None, description="User email address")
    
    class Config:
        from_attributes = True

