from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class FileChunk(Base):
    """
    FileChunk model for storing document chunks and their embeddings.
    Each chunk represents a semantic unit of the original document.
    """
    
    __tablename__ = "file_chunks"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key
    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Chunk Information
    chunk_index = Column(Integer, nullable=False)  # Order of chunk in document
    token_count = Column(Integer, nullable=False)  # Number of tokens in chunk
    
    # Storage
    # Chunk text is stored in blob storage, NOT in database for performance/cost
    # Path format: {org_id}/{project_id}/{file_id}/chunks/chunk_{index}.json
    blob_storage_path = Column(String(1000), nullable=False)  # REQUIRED: Path to chunk JSON in blob storage
    
    # Vector Database Reference
    vector_id = Column(String(255), nullable=True)  # ID in vector database (Pinecone)
    
    # Chunk Metadata (bounding box, page number, content type, etc.)
    chunk_metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
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
    file = relationship(
        "File",
        back_populates="chunks"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_file_chunks_file_id', 'file_id'),
        Index('idx_file_chunks_chunk_index', 'chunk_index'),
        Index('idx_file_chunks_vector_id', 'vector_id'),
    )
    
    def __repr__(self):
        return f"<FileChunk(id={self.id}, file_id={self.file_id}, chunk_index={self.chunk_index})>"

