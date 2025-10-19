"""DTOs for organization management."""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class OrganizationCreate(BaseModel):
    """Request body for creating an organization."""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")


class OrganizationUpdate(BaseModel):
    """Request body for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Organization name")


class OrganizationResponse(BaseModel):
    """Response body for organization information."""
    id: UUID
    name: str
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    """Response body for list of organizations with user role."""
    id: UUID
    name: str
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True

