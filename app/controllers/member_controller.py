"""Member controller for organization member management endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dtos.member_dto import MemberAdd, MemberUpdate, MemberResponse
from app.services.member_service import MemberService
from app.core.auth import get_tenant_context
from app.core.tenant_context import TenantContext


router = APIRouter(prefix="/organizations/{org_id}/members", tags=["Members"])


@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def add_member(
    org_id: UUID,
    member_data: MemberAdd,
    context: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Add a member to an organization.
    
    Only OWNER or ADMIN can add members.
    
    - **email**: Email of user to add (must be registered)
    - **role**: Role to assign (owner, admin, member)
    
    Requires authentication.
    """
    member_service = MemberService(db)
    return member_service.add_member(org_id, member_data, context)


@router.get("/", response_model=List[MemberResponse])
def list_members(
    org_id: UUID,
    context: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    List all members of an organization.
    
    Any member can view the list.
    
    Requires authentication.
    """
    member_service = MemberService(db)
    return member_service.list_members(org_id, context)


@router.put("/{user_id}", response_model=MemberResponse)
def update_member_role(
    org_id: UUID,
    user_id: UUID,
    update_data: MemberUpdate,
    context: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Update a member's role.
    
    Only OWNER can change roles.
    
    - **role**: New role (owner, admin, member)
    
    Requires authentication.
    """
    member_service = MemberService(db)
    return member_service.update_member_role(org_id, user_id, update_data, context)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    org_id: UUID,
    user_id: UUID,
    context: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Remove a member from an organization.
    
    Only OWNER or ADMIN can remove members.
    Cannot remove the last owner.
    
    Requires authentication.
    """
    member_service = MemberService(db)
    member_service.remove_member(org_id, user_id, context)
    return None

