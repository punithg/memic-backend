"""Organization service with multi-tenant operations."""

from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Organization
from app.models.user_organization import UserRole
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.member_repository import MemberRepository
from app.core.tenant_context import TenantContext
from app.dtos.organization_dto import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationListResponse
)


class OrganizationService:
    """Service for organization operations with tenant isolation."""
    
    def __init__(self, db: Session):
        self.db = db
        self.org_repo = OrganizationRepository(db)
        self.member_repo = MemberRepository(db)
    
    def create_organization(
        self,
        org_data: OrganizationCreate,
        context: TenantContext
    ) -> Organization:
        """
        Create a new organization and automatically add creator as OWNER.
        
        Args:
            org_data: Organization creation data
            context: Tenant context with creator user
            
        Returns:
            Created organization
        """
        # Create organization
        org = Organization(
            name=org_data.name,
            created_by_user_id=context.user_id
        )
        
        created_org = self.org_repo.create(org)
        
        # Automatically add creator as OWNER
        self.member_repo.add_member(
            user_id=context.user_id,
            org_id=created_org.id,
            role=UserRole.OWNER
        )
        
        return created_org
    
    def list_user_organizations(
        self,
        context: TenantContext
    ) -> List[OrganizationListResponse]:
        """
        List all organizations where user is a member.
        
        Args:
            context: Tenant context with user
            
        Returns:
            List of organizations with user's role
        """
        org_tuples = self.org_repo.list_user_organizations(context)
        
        return [
            OrganizationListResponse(
                id=org.id,
                name=org.name,
                role=role.value,
                created_at=org.created_at
            )
            for org, role in org_tuples
        ]
    
    def get_organization(
        self,
        org_id: UUID,
        context: TenantContext
    ) -> Organization:
        """
        Get organization if user is a member.
        
        Args:
            org_id: Organization ID
            context: Tenant context with user
            
        Returns:
            Organization
            
        Raises:
            HTTPException: 404 if not found or user not a member
        """
        result = self.org_repo.get_user_organization(org_id, context)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found or access denied"
            )
        
        org, role = result
        return org
    
    def update_organization(
        self,
        org_id: UUID,
        update_data: OrganizationUpdate,
        context: TenantContext
    ) -> Organization:
        """
        Update organization (OWNER or ADMIN only).
        
        Args:
            org_id: Organization ID
            update_data: Update data
            context: Tenant context with user
            
        Returns:
            Updated organization
            
        Raises:
            HTTPException: 403 if user doesn't have permission
        """
        # Get organization and user's role
        result = self.org_repo.get_user_organization(org_id, context)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        org, role = result
        
        # Check permissions (OWNER or ADMIN)
        if role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners and admins can update organization"
            )
        
        # Update organization
        if update_data.name:
            org.name = update_data.name
        
        return self.org_repo.update(org)
    
    def delete_organization(
        self,
        org_id: UUID,
        context: TenantContext
    ) -> bool:
        """
        Delete organization (OWNER only).
        Cascades to delete projects and memberships.
        
        Args:
            org_id: Organization ID
            context: Tenant context with user
            
        Returns:
            True if deleted
            
        Raises:
            HTTPException: 403 if user is not OWNER
        """
        # Get user's role
        role = self.member_repo.get_user_role(context.user_id, org_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Only OWNER can delete
        if role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization owner can delete organization"
            )
        
        return self.org_repo.delete(org_id)

