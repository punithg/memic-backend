"""Repository for UserOrganization (member) entity."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.repositories.base_repository import BaseRepository
from app.models import UserOrganization, User
from app.models.user_organization import UserRole
from app.core.tenant_context import TenantContext


class MemberRepository(BaseRepository[UserOrganization]):
    """Repository for member (UserOrganization) operations."""
    
    def __init__(self, db: Session):
        super().__init__(UserOrganization, db)
    
    def get_member(
        self, 
        user_id: UUID, 
        org_id: UUID
    ) -> Optional[UserOrganization]:
        """
        Get member relationship between user and organization.
        
        Args:
            user_id: User ID
            org_id: Organization ID
            
        Returns:
            UserOrganization if found, None otherwise
        """
        return (
            self.db.query(UserOrganization)
            .filter(
                and_(
                    UserOrganization.user_id == user_id,
                    UserOrganization.organization_id == org_id
                )
            )
            .first()
        )
    
    def list_organization_members(self, org_id: UUID) -> List[tuple]:
        """
        List all members of an organization with user details.
        
        Args:
            org_id: Organization ID
            
        Returns:
            List of (UserOrganization, User) tuples
        """
        return (
            self.db.query(UserOrganization, User)
            .join(User, User.id == UserOrganization.user_id)
            .filter(UserOrganization.organization_id == org_id)
            .all()
        )
    
    def add_member(
        self,
        user_id: UUID,
        org_id: UUID,
        role: UserRole
    ) -> UserOrganization:
        """
        Add a member to an organization.
        
        Args:
            user_id: User ID
            org_id: Organization ID
            role: User role in organization
            
        Returns:
            Created UserOrganization
        """
        member = UserOrganization(
            user_id=user_id,
            organization_id=org_id,
            role=role
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def update_role(
        self,
        user_id: UUID,
        org_id: UUID,
        new_role: UserRole
    ) -> Optional[UserOrganization]:
        """
        Update member's role in organization.
        
        Args:
            user_id: User ID
            org_id: Organization ID
            new_role: New role for the member
            
        Returns:
            Updated UserOrganization if found, None otherwise
        """
        member = self.get_member(user_id, org_id)
        if member:
            member.role = new_role
            self.db.commit()
            self.db.refresh(member)
        return member
    
    def remove_member(
        self,
        user_id: UUID,
        org_id: UUID
    ) -> bool:
        """
        Remove a member from an organization.
        
        Args:
            user_id: User ID
            org_id: Organization ID
            
        Returns:
            True if removed, False if not found
        """
        member = self.get_member(user_id, org_id)
        if member:
            self.db.delete(member)
            self.db.commit()
            return True
        return False
    
    def is_member(self, user_id: UUID, org_id: UUID) -> bool:
        """
        Check if user is a member of organization.
        
        Args:
            user_id: User ID
            org_id: Organization ID
            
        Returns:
            True if user is member, False otherwise
        """
        return self.get_member(user_id, org_id) is not None
    
    def get_user_role(self, user_id: UUID, org_id: UUID) -> Optional[UserRole]:
        """
        Get user's role in organization.
        
        Args:
            user_id: User ID
            org_id: Organization ID
            
        Returns:
            UserRole if member, None otherwise
        """
        member = self.get_member(user_id, org_id)
        return member.role if member else None

