from sqlalchemy import Column, DateTime, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """Enum for user roles within an organization."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class UserOrganization(Base):
    """
    Many-to-many relationship between Users and Organizations with role-based access control.
    Tracks which users belong to which organizations and their roles.
    """
    
    __tablename__ = "user_organizations"
    
    # Composite Primary Key
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        primary_key=True
    )
    organization_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("organizations.id", ondelete="CASCADE"), 
        primary_key=True
    )
    
    # Role Information
    role = Column(
        Enum(UserRole, name="user_role_enum", create_type=True), 
        nullable=False, 
        default=UserRole.MEMBER
    )
    
    # Timestamp (stored in UTC)
    joined_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    # Relationships
    user = relationship(
        "User", 
        back_populates="user_organizations"
    )
    organization = relationship(
        "Organization", 
        back_populates="user_organizations"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_user_organizations_user_id', 'user_id'),
        Index('idx_user_organizations_organization_id', 'organization_id'),
        Index('idx_user_organizations_role', 'role'),
    )
    
    def __repr__(self):
        return f"<UserOrganization(user_id={self.user_id}, organization_id={self.organization_id}, role={self.role})>"

