"""Repository for Organization entity with tenant filtering."""

from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.repositories.base_repository import BaseRepository
from app.models import Organization, UserOrganization
from app.core.tenant_context import TenantContext


class OrganizationRepository(BaseRepository[Organization]):
    """Repository for Organization operations with user membership filtering."""
    
    def __init__(self, db: Session):
        super().__init__(Organization, db)
    
    def list_user_organizations(self, context: TenantContext) -> List[tuple]:
        """
        List all organizations where the user is a member.
        
        Args:
            context: Tenant context with user
            
        Returns:
            List of (Organization, role) tuples
        """
        return (
            self.db.query(Organization, UserOrganization.role)
            .join(UserOrganization, UserOrganization.organization_id == Organization.id)
            .filter(UserOrganization.user_id == context.user_id)
            .all()
        )
    
    def get_user_organization(
        self, 
        org_id: UUID, 
        context: TenantContext
    ) -> tuple[Organization, str] | None:
        """
        Get organization if user is a member, along with their role.
        
        Args:
            org_id: Organization ID
            context: Tenant context with user
            
        Returns:
            (Organization, role) tuple if user is member, None otherwise
        """
        result = (
            self.db.query(Organization, UserOrganization.role)
            .join(UserOrganization, UserOrganization.organization_id == Organization.id)
            .filter(
                and_(
                    Organization.id == org_id,
                    UserOrganization.user_id == context.user_id
                )
            )
            .first()
        )
        return result
    
    def _apply_tenant_filter(self, query, context: TenantContext):
        """
        Filter organizations by user membership.
        Only returns organizations where the context user is a member.
        """
        return query.join(
            UserOrganization,
            UserOrganization.organization_id == Organization.id
        ).filter(UserOrganization.user_id == context.user_id)

