"""Repository for User entity."""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.repositories.base_repository import BaseRepository
from app.models import User
from app.core.tenant_context import TenantContext


class UserRepository(BaseRepository[User]):
    """Repository for User operations."""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def email_exists(self, email: str) -> bool:
        """
        Check if email already exists.
        
        Args:
            email: Email address to check
            
        Returns:
            True if email exists, False otherwise
        """
        return self.db.query(User).filter(User.email == email).count() > 0
    
    def _apply_tenant_filter(self, query, context: TenantContext):
        """
        Users don't need tenant filtering - they exist globally.
        Override to prevent filtering.
        """
        return query

