from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Project(Base):
    """
    Project model representing an environment (dev, prod, uat) within an organization.
    Each project is a separate tenant for data isolation.
    """
    
    __tablename__ = "projects"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Project Information
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Foreign Keys
    organization_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("organizations.id", ondelete="CASCADE"), 
        nullable=False
    )
    created_by_user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="RESTRICT"), 
        nullable=False
    )
    
    # Timestamps (stored in UTC)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    # Relationships
    organization = relationship(
        "Organization", 
        back_populates="projects"
    )
    creator = relationship(
        "User", 
        back_populates="created_projects",
        foreign_keys=[created_by_user_id]
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_projects_organization_id', 'organization_id'),
        Index('idx_projects_created_by_user_id', 'created_by_user_id'),
        Index('idx_projects_is_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, organization_id={self.organization_id})>"

