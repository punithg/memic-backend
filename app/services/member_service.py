"""Member management service for organization access control."""

from typing import List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_organization import UserRole
from app.repositories.member_repository import MemberRepository
from app.repositories.user_repository import UserRepository
from app.core.tenant_context import TenantContext
from app.dtos.member_dto import MemberAdd, MemberUpdate, MemberResponse


class MemberService:
    """Service for member management operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.member_repo = MemberRepository(db)
        self.user_repo = UserRepository(db)
    
    def add_member(
        self,
        org_id: UUID,
        member_data: MemberAdd,
        context: TenantContext
    ) -> MemberResponse:
        """
        Add a member to an organization (OWNER or ADMIN only).
        
        Args:
            org_id: Organization ID
            member_data: Member data with email and role
            context: Tenant context with current user
            
        Returns:
            Created member response
            
        Raises:
            HTTPException: 403 if user doesn't have permission, 404 if user not found
        """
        # Check current user's role
        current_role = self.member_repo.get_user_role(context.user_id, org_id)
        if not current_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        if current_role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners and admins can add members"
            )
        
        # Find user by email
        user = self.user_repo.get_by_email(member_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {member_data.email} not found"
            )
        
        # Check if user is already a member
        if self.member_repo.is_member(user.id, org_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization"
            )
        
        # Add member
        role = UserRole(member_data.role)
        member = self.member_repo.add_member(user.id, org_id, role)
        
        return MemberResponse(
            user_id=user.id,
            email=user.email,
            name=user.name,
            role=member.role.value,
            joined_at=member.joined_at
        )
    
    def list_members(
        self,
        org_id: UUID,
        context: TenantContext
    ) -> List[MemberResponse]:
        """
        List all members of an organization (any member can view).
        
        Args:
            org_id: Organization ID
            context: Tenant context with user
            
        Returns:
            List of members
            
        Raises:
            HTTPException: 403 if user is not a member
        """
        # Check if user is a member
        if not self.member_repo.is_member(context.user_id, org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get all members
        members = self.member_repo.list_organization_members(org_id)
        
        return [
            MemberResponse(
                user_id=user.id,
                email=user.email,
                name=user.name,
                role=member.role.value,
                joined_at=member.joined_at
            )
            for member, user in members
        ]
    
    def update_member_role(
        self,
        org_id: UUID,
        user_id: UUID,
        update_data: MemberUpdate,
        context: TenantContext
    ) -> MemberResponse:
        """
        Update a member's role (OWNER only).
        
        Args:
            org_id: Organization ID
            user_id: User ID to update
            update_data: New role data
            context: Tenant context with current user
            
        Returns:
            Updated member response
            
        Raises:
            HTTPException: 403 if user doesn't have permission
        """
        # Check current user's role (only OWNER can change roles)
        current_role = self.member_repo.get_user_role(context.user_id, org_id)
        if current_role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organization owner can change member roles"
            )
        
        # Update role
        new_role = UserRole(update_data.role)
        member = self.member_repo.update_role(user_id, org_id, new_role)
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Get user details
        user = self.user_repo.get(user_id)
        
        return MemberResponse(
            user_id=user.id,
            email=user.email,
            name=user.name,
            role=member.role.value,
            joined_at=member.joined_at
        )
    
    def remove_member(
        self,
        org_id: UUID,
        user_id: UUID,
        context: TenantContext
    ) -> bool:
        """
        Remove a member from an organization (OWNER or ADMIN only).
        Cannot remove the last owner.
        
        Args:
            org_id: Organization ID
            user_id: User ID to remove
            context: Tenant context with current user
            
        Returns:
            True if removed
            
        Raises:
            HTTPException: 403 if user doesn't have permission, 400 if last owner
        """
        # Check current user's role
        current_role = self.member_repo.get_user_role(context.user_id, org_id)
        if not current_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        if current_role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners and admins can remove members"
            )
        
        # Get member's role
        member_role = self.member_repo.get_user_role(user_id, org_id)
        if not member_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # ADMIN cannot remove OWNER
        if current_role == UserRole.ADMIN and member_role == UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admins cannot remove owners"
            )
        
        # Prevent removing last owner
        if member_role == UserRole.OWNER:
            members = self.member_repo.list_organization_members(org_id)
            owner_count = sum(1 for m, _ in members if m.role == UserRole.OWNER)
            if owner_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last owner of the organization"
                )
        
        return self.member_repo.remove_member(user_id, org_id)

