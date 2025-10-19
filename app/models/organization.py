from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Organization(Base):
    """Organization model representing a company or team."""
    
    __tablename__ = "organizations"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Organization Information
    name = Column(String(255), nullable=False)
    
    # Foreign Keys
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
    creator = relationship(
        "User", 
        back_populates="created_organizations",
        foreign_keys=[created_by_user_id]
    )
    projects = relationship(
        "Project", 
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    user_organizations = relationship(
        "UserOrganization", 
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_organizations_created_by_user_id', 'created_by_user_id'),
    )
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name})>"

