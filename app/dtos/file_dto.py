from pydantic import BaseModel, Field, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.file import FileStatus


class FileInitUploadRequestDTO(BaseModel):
    """Request DTO for initializing file upload (presigned URL approach)."""
    filename: str = Field(..., description="Original filename", min_length=1, max_length=500)
    size: int = Field(..., description="File size in bytes", gt=0)
    mime_type: str = Field(..., description="MIME type of the file")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")


class FileInitUploadResponseDTO(BaseModel):
    """Response DTO for file upload initialization."""
    file_id: UUID4
    upload_url: str
    expires_in: int = Field(default=3600, description="URL expiry in seconds")
    
    class Config:
        from_attributes = True


class FileConfirmUploadRequestDTO(BaseModel):
    """Request DTO for confirming file upload completion."""
    file_id: UUID4


class FileUploadResponseDTO(BaseModel):
    """Response DTO for file upload."""
    id: UUID4
    name: str
    original_filename: str
    size: int
    mime_type: str
    project_id: UUID4
    status: FileStatus
    blob_storage_path: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class FileStatusResponseDTO(BaseModel):
    """Detailed status response for file processing."""
    id: UUID4
    name: str
    original_filename: str
    status: FileStatus
    project_id: UUID4
    
    # File paths
    blob_storage_path: str
    is_converted: bool
    converted_file_path: Optional[str] = None
    enriched_file_path: Optional[str] = None
    
    # Progress tracking
    total_chunks: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    conversion_started_at: Optional[datetime] = None
    conversion_completed_at: Optional[datetime] = None
    parsing_started_at: Optional[datetime] = None
    parsing_completed_at: Optional[datetime] = None
    chunking_started_at: Optional[datetime] = None
    chunking_completed_at: Optional[datetime] = None
    embedding_started_at: Optional[datetime] = None
    embedding_completed_at: Optional[datetime] = None
    
    # Error handling
    error_message: Optional[str] = None
    
    # Custom metadata
    file_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class FileListItemDTO(BaseModel):
    """List item DTO for file listing."""
    id: UUID4
    name: str
    original_filename: str
    size: int
    mime_type: str
    status: FileStatus
    total_chunks: int
    created_at: datetime
    updated_at: datetime
    file_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class FileListResponseDTO(BaseModel):
    """Paginated response for file listing."""
    items: List[FileListItemDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class FileMetadataRequestDTO(BaseModel):
    """Request DTO for updating file metadata."""
    metadata: Dict[str, Any] = Field(
        ...,
        description="Custom metadata as key-value pairs"
    )


class FileMetadataResponseDTO(BaseModel):
    """Response DTO for file metadata."""
    file_id: UUID4
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FileSearchRequestDTO(BaseModel):
    """Request DTO for semantic search."""
    query: str = Field(..., description="Search query text", min_length=1)
    top_k: int = Field(default=10, description="Number of results to return", ge=1, le=100)
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata filters"
    )


class FileChunkResultDTO(BaseModel):
    """Individual chunk result in search response."""
    chunk_id: UUID4
    file_id: UUID4
    file_name: str
    chunk_index: int
    chunk_text: str  # Fetched from blob storage, not from DB
    score: float
    chunk_metadata: Optional[Dict[str, Any]] = None
    blob_storage_path: Optional[str] = None  # Path to chunk in blob storage
    
    class Config:
        from_attributes = True


class FileSearchResultDTO(BaseModel):
    """Response DTO for semantic search."""
    query: str
    results: List[FileChunkResultDTO]
    total_results: int
    

class FileDetailResponseDTO(BaseModel):
    """Detailed file information with metadata."""
    id: UUID4
    name: str
    original_filename: str
    size: int
    mime_type: str
    project_id: UUID4
    uploaded_by_user_id: UUID4
    status: FileStatus
    
    # File paths
    blob_storage_path: str
    is_converted: bool
    converted_file_path: Optional[str] = None
    enriched_file_path: Optional[str] = None
    
    # Progress
    total_chunks: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Metadata
    metadata_records: List[FileMetadataResponseDTO] = []
    
    # Error
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

