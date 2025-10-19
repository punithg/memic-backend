"""Project service with organization-level access control."""

from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Project
from app.models.user_organization import UserRole
from app.repositories.project_repository import ProjectRepository
from app.repositories.member_repository import MemberRepository
from app.core.tenant_context import TenantContext
from app.dtos.project_dto import ProjectCreate, ProjectUpdate


class ProjectService:
    """Service for project operations with organization membership checks."""
    
    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.member_repo = MemberRepository(db)
    
    def create_project(
        self,
        org_id: UUID,
        project_data: ProjectCreate,
        context: TenantContext
    ) -> Project:
        """
        Create a new project under an organization (OWNER or ADMIN only).
        
        Args:
            org_id: Organization ID
            project_data: Project creation data
            context: Tenant context with user
            
        Returns:
            Created project
            
        Raises:
            HTTPException: 403 if user doesn't have permission
        """
        # Check user's role in organization
        role = self.member_repo.get_user_role(context.user_id, org_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found or access denied"
            )
        
        # Only OWNER or ADMIN can create projects
        if role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners and admins can create projects"
            )
        
        # Create project
        project = Project(
            name=project_data.name,
            organization_id=org_id,
            created_by_user_id=context.user_id,
            is_active=True
        )
        
        return self.project_repo.create(project)
    
    def list_organization_projects(
        self,
        org_id: UUID,
        context: TenantContext
    ) -> List[Project]:
        """
        List all projects in an organization (any member can view).
        
        Args:
            org_id: Organization ID
            context: Tenant context with user
            
        Returns:
            List of projects
        """
        return self.project_repo.list_by_organization(org_id, context)
    
    def get_project(
        self,
        org_id: UUID,
        project_id: UUID,
        context: TenantContext
    ) -> Project:
        """
        Get project details (any member can view).
        
        Args:
            org_id: Organization ID
            project_id: Project ID
            context: Tenant context with user
            
        Returns:
            Project
            
        Raises:
            HTTPException: 404 if not found or access denied
        """
        project = self.project_repo.get_by_id_and_organization(
            project_id,
            org_id,
            context
        )
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )
        
        return project
    
    def update_project(
        self,
        org_id: UUID,
        project_id: UUID,
        update_data: ProjectUpdate,
        context: TenantContext
    ) -> Project:
        """
        Update project (OWNER or ADMIN only).
        
        Args:
            org_id: Organization ID
            project_id: Project ID
            update_data: Update data
            context: Tenant context with user
            
        Returns:
            Updated project
            
        Raises:
            HTTPException: 403 if user doesn't have permission
        """
        # Check user's role
        role = self.member_repo.get_user_role(context.user_id, org_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        if role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners and admins can update projects"
            )
        
        # Get project
        project = self.project_repo.get_by_id_and_organization(
            project_id,
            org_id,
            context
        )
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Update project
        if update_data.name is not None:
            project.name = update_data.name
        if update_data.is_active is not None:
            project.is_active = update_data.is_active
        
        return self.project_repo.update(project)
    
    def delete_project(
        self,
        org_id: UUID,
        project_id: UUID,
        context: TenantContext
    ) -> bool:
        """
        Delete project (OWNER or ADMIN only).
        
        Args:
            org_id: Organization ID
            project_id: Project ID
            context: Tenant context with user
            
        Returns:
            True if deleted
            
        Raises:
            HTTPException: 403 if user doesn't have permission
        """
        # Check user's role
        role = self.member_repo.get_user_role(context.user_id, org_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        if role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners and admins can delete projects"
            )
        
        # Verify project belongs to organization
        project = self.project_repo.get_by_id_and_organization(
            project_id,
            org_id,
            context
        )
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return self.project_repo.delete(project_id)

