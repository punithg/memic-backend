"""DTOs for member management."""

from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Literal


class MemberAdd(BaseModel):
    """Request body for adding a member to an organization."""
    email: EmailStr = Field(..., description="Email of user to add")
    role: Literal["owner", "admin", "member"] = Field(default="member", description="User role in organization")


class MemberUpdate(BaseModel):
    """Request body for updating a member's role."""
    role: Literal["owner", "admin", "member"] = Field(..., description="New role for the member")


class MemberResponse(BaseModel):
    """Response body for member information."""
    user_id: UUID
    email: str
    name: str
    role: str
    joined_at: datetime
    
    class Config:
        from_attributes = True


class MemberListResponse(BaseModel):
    """Response body for list of members."""
    members: list[MemberResponse]
    total: int

