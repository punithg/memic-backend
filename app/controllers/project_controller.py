"""Project controller for project management endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dtos.project_dto import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import ProjectService
from app.core.auth import get_tenant_context
from app.core.tenant_context import TenantContext


router = APIRouter(prefix="/organizations/{org_id}/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    org_id: UUID,
    project_data: ProjectCreate,
    context: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Create a new project under an organization.
    
    Only OWNER or ADMIN can create projects.
    
    - **name**: Project name (e.g., dev, prod, uat)
    
    Requires authentication.
    """
    project_service = ProjectService(db)
    project = project_service.create_project(org_id, project_data, context)
    return ProjectResponse.model_validate(project)


@router.get("/", response_model=List[ProjectResponse])
def list_organization_projects(
    org_id: UUID,
    context: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    List all projects in an organization.
    
    Any member of the organization can view projects.
    
    Requires authentication.
    """
    project_service = ProjectService(db)
    projects = project_service.list_organization_projects(org_id, context)
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    org_id: UUID,
    project_id: UUID,
    context: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Get project details.
    
    Any member of the organization can view project details.
    
    Requires authentication.
    """
    project_service = ProjectService(db)
    project = project_service.get_project(org_id, project_id, context)
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    org_id: UUID,
    project_id: UUID,
    update_data: ProjectUpdate,
    context: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Update project details.
    
    Only OWNER or ADMIN can update projects.
    
    - **name**: Optional new project name
    - **is_active**: Optional active status
    
    Requires authentication.
    """
    project_service = ProjectService(db)
    project = project_service.update_project(org_id, project_id, update_data, context)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    org_id: UUID,
    project_id: UUID,
    context: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Delete a project.
    
    Only OWNER or ADMIN can delete projects.
    
    Requires authentication.
    """
    project_service = ProjectService(db)
    project_service.delete_project(org_id, project_id, context)
    return None

