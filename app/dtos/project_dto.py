"""DTOs for project management."""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class ProjectCreate(BaseModel):
    """Request body for creating a project."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name (e.g., dev, prod, uat)")


class ProjectUpdate(BaseModel):
    """Request body for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Project name")
    is_active: Optional[bool] = Field(None, description="Project active status")


class ProjectResponse(BaseModel):
    """Response body for project information."""
    id: UUID
    name: str
    organization_id: UUID
    created_by_user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

