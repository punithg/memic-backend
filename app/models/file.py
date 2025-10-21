from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from enum import Enum

from app.database import Base


class FileStatus(str, Enum):
    """Enum for file processing status."""
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    UPLOAD_FAILED = "upload_failed"
    CONVERSION_STARTED = "conversion_started"
    CONVERSION_COMPLETE = "conversion_complete"
    CONVERSION_FAILED = "conversion_failed"
    PARSING_STARTED = "parsing_started"
    PARSING_COMPLETE = "parsing_complete"
    PARSING_FAILED = "parsing_failed"
    CHUNKING_STARTED = "chunking_started"
    CHUNKING_COMPLETE = "chunking_complete"
    CHUNKING_FAILED = "chunking_failed"
    EMBEDDING_STARTED = "embedding_started"
    EMBEDDING_COMPLETE = "embedding_complete"
    EMBEDDING_FAILED = "embedding_failed"
    READY = "ready"


class File(Base):
    """
    File model representing uploaded documents for RAG processing.
    Each file goes through: upload → conversion → parsing → chunking → embedding → ready
    """
    
    __tablename__ = "files"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # File Information
    name = Column(String(255), nullable=False)
    original_filename = Column(String(500), nullable=False)
    size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String(100), nullable=False)
    
    # Foreign Keys
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    uploaded_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    
    # Processing Status
    status = Column(
        SQLEnum(FileStatus, name="file_status_enum", create_type=True),
        nullable=False,
        default=FileStatus.UPLOADING
    )
    
    # Storage Paths
    blob_storage_path = Column(String(1000), nullable=False)  # Path to raw file
    is_converted = Column(Boolean, default=False, nullable=False)
    converted_file_path = Column(String(1000), nullable=True)  # Path to converted file (if applicable)
    enriched_file_path = Column(String(1000), nullable=True)  # Path to enriched JSON
    
    # Chunk Information
    total_chunks = Column(Integer, default=0, nullable=False)
    
    # Status Tracking Timestamps
    conversion_started_at = Column(DateTime(timezone=True), nullable=True)
    conversion_completed_at = Column(DateTime(timezone=True), nullable=True)
    parsing_started_at = Column(DateTime(timezone=True), nullable=True)
    parsing_completed_at = Column(DateTime(timezone=True), nullable=True)
    chunking_started_at = Column(DateTime(timezone=True), nullable=True)
    chunking_completed_at = Column(DateTime(timezone=True), nullable=True)
    embedding_started_at = Column(DateTime(timezone=True), nullable=True)
    embedding_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    
    # Custom Metadata (user-defined key-value pairs)
    file_metadata = Column(JSONB, nullable=True, default=dict)
    
    # Standard Timestamps
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
    # Note: We use repository pattern for most queries, not ORM navigation
    # Only keep relationships that are actively used in business logic
    chunks = relationship(
        "FileChunk",
        back_populates="file",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_files_project_id', 'project_id'),
        Index('idx_files_uploaded_by_user_id', 'uploaded_by_user_id'),
        Index('idx_files_status', 'status'),
        Index('idx_files_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<File(id={self.id}, name={self.name}, status={self.status}, project_id={self.project_id})>"

