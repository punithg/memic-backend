"""Organization controller for organization management endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dtos.organization_dto import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse
)
from app.services.organization_service import OrganizationService
from app.core.auth import get_tenant_context
from app.core.tenant_context import TenantContext


router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    org_data: OrganizationCreate,
    context: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Create a new organization.
    
    Creator is automatically added as OWNER.
    
    - **name**: Organization name
    
    Requires authentication.
    """
    org_service = OrganizationService(db)
    org = org_service.create_organization(org_data, context)
    return OrganizationResponse.model_validate(org)


@router.get("/", response_model=List[OrganizationListResponse])
def list_user_organizations(
    context: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    List all organizations where current user is a member.
    
    Returns organizations with user's role in each.
    
    Requires authentication.
    """
    org_service = OrganizationService(db)
    return org_service.list_user_organizations(context)


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization(
    org_id: UUID,
    context: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Get organization details.
    
    User must be a member of the organization.
    
    Requires authentication.
    """
    org_service = OrganizationService(db)
    org = org_service.get_organization(org_id, context)
    return OrganizationResponse.model_validate(org)


@router.put("/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: UUID,
    update_data: OrganizationUpdate,
    context: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Update organization details.
    
    Only OWNER or ADMIN can update.
    
    - **name**: Optional new organization name
    
    Requires authentication.
    """
    org_service = OrganizationService(db)
    org = org_service.update_organization(org_id, update_data, context)
    return OrganizationResponse.model_validate(org)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    org_id: UUID,
    context: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Delete an organization.
    
    Only OWNER can delete. Cascades to delete projects and memberships.
    
    Requires authentication.
    """
    org_service = OrganizationService(db)
    org_service.delete_organization(org_id, context)
    return None

