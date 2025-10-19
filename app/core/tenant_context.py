"""
Tenant Context for multi-tenant data isolation.

This module provides a TenantContext that tracks the current user and their
access to organizations and projects. All repository queries use this context
to automatically filter data and prevent cross-tenant data leakage.
"""

from typing import Optional
from uuid import UUID
from dataclasses import dataclass

from app.models import User


@dataclass
class TenantContext:
    """
    Context object that holds current user and tenant information.
    Passed to all repository methods to enforce automatic tenant filtering.
    """
    
    user: User
    organization_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    
    def __post_init__(self):
        """Validate the context after initialization."""
        if not self.user:
            raise ValueError("TenantContext must have a user")
    
    @property
    def user_id(self) -> UUID:
        """Get the current user's ID."""
        return self.user.id
    
    def has_organization(self) -> bool:
        """Check if context has an organization set."""
        return self.organization_id is not None
    
    def has_project(self) -> bool:
        """Check if context has a project set."""
        return self.project_id is not None
    
    def with_organization(self, organization_id: UUID) -> "TenantContext":
        """Create a new context with the specified organization."""
        return TenantContext(
            user=self.user,
            organization_id=organization_id,
            project_id=self.project_id
        )
    
    def with_project(self, project_id: UUID) -> "TenantContext":
        """Create a new context with the specified project."""
        return TenantContext(
            user=self.user,
            organization_id=self.organization_id,
            project_id=project_id
        )

