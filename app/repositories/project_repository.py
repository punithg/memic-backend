"""Repository for Project entity with organization filtering."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.repositories.base_repository import BaseRepository
from app.models import Project, UserOrganization
from app.core.tenant_context import TenantContext


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project operations with organization filtering."""
    
    def __init__(self, db: Session):
        super().__init__(Project, db)
    
    def list_by_organization(
        self, 
        org_id: UUID,
        context: TenantContext
    ) -> List[Project]:
        """
        List all projects in an organization.
        Validates that user has access to the organization.
        
        Args:
            org_id: Organization ID
            context: Tenant context with user
            
        Returns:
            List of projects in the organization
        """
        # Check if user is member of organization
        is_member = (
            self.db.query(UserOrganization)
            .filter(
                and_(
                    UserOrganization.organization_id == org_id,
                    UserOrganization.user_id == context.user_id
                )
            )
            .first()
        )
        
        if not is_member:
            return []
        
        return (
            self.db.query(Project)
            .filter(Project.organization_id == org_id)
            .all()
        )
    
    def get_by_id_and_organization(
        self,
        project_id: UUID,
        org_id: UUID,
        context: TenantContext
    ) -> Optional[Project]:
        """
        Get project by ID within an organization.
        Validates that user has access to the organization.
        
        Args:
            project_id: Project ID
            org_id: Organization ID
            context: Tenant context with user
            
        Returns:
            Project if found and user has access, None otherwise
        """
        # Check if user is member of organization
        is_member = (
            self.db.query(UserOrganization)
            .filter(
                and_(
                    UserOrganization.organization_id == org_id,
                    UserOrganization.user_id == context.user_id
                )
            )
            .first()
        )
        
        if not is_member:
            return None
        
        return (
            self.db.query(Project)
            .filter(
                and_(
                    Project.id == project_id,
                    Project.organization_id == org_id
                )
            )
            .first()
        )
    
    def _apply_tenant_filter(self, query, context: TenantContext):
        """
        Filter projects by organization membership.
        Only returns projects from organizations where user is a member.
        """
        return query.join(
            UserOrganization,
            UserOrganization.organization_id == Project.organization_id
        ).filter(UserOrganization.user_id == context.user_id)

