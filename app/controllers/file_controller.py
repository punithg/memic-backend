"""
File controller for handling file upload and RAG operations.
"""
from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.file import FileStatus
from app.services.file_service import FileService
from app.dtos.file_dto import (
    FileUploadResponseDTO,
    FileStatusResponseDTO,
    FileListResponseDTO,
    FileDetailResponseDTO,
    FileMetadataRequestDTO,
    FileMetadataResponseDTO,
    FileSearchRequestDTO,
    FileSearchResultDTO,
    FileInitUploadRequestDTO,
    FileInitUploadResponseDTO
)

router = APIRouter(prefix="/projects/{project_id}/files", tags=["Files"])


@router.post(
    "/init",
    response_model=FileInitUploadResponseDTO,
    status_code=201,
    summary="Initialize file upload (presigned URL)",
    description="Get a presigned URL for direct upload to storage (recommended for large files)"
)
async def init_file_upload(
    project_id: UUID,
    request: FileInitUploadRequestDTO,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize file upload and get presigned URL for direct upload.
    
    **Direct Upload Flow:**
    1. Call this endpoint with file metadata
    2. Get back `file_id` and `upload_url`
    3. PUT file directly to `upload_url` (doesn't go through server!)
    4. Call confirm endpoint with `file_id`
    
    **Benefits:**
    - Faster (no double network transfer)
    - More scalable (doesn't load server memory)
    - Supports larger files
    - Lower bandwidth costs
    """
    # TODO: Add project access check
    # Get organization_id from project
    from app.repositories.project_repository import ProjectRepository
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    file_service = FileService(db)
    return await file_service.init_upload(
        request=request,
        project_id=project_id,
        organization_id=project.organization_id,
        user_id=current_user.id
    )


@router.post(
    "/{file_id}/confirm",
    response_model=FileUploadResponseDTO,
    status_code=200,
    summary="Confirm file upload",
    description="Confirm file upload completion and trigger RAG processing"
)
async def confirm_file_upload(
    project_id: UUID,
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm that file upload is complete and trigger RAG processing.
    
    Call this after successfully uploading file to the presigned URL.
    This will:
    - Verify file exists in storage
    - Update status to UPLOADED
    - Trigger RAG processing pipeline
    """
    # TODO: Add project access check
    
    file_service = FileService(db)
    return await file_service.confirm_upload(file_id, project_id)


@router.get(
    "/{file_id}/download-url",
    response_model=dict,
    summary="Get download URL",
    description="Get a presigned URL for downloading the file"
)
async def get_file_download_url(
    project_id: UUID,
    file_id: UUID,
    expiry: int = Query(3600, description="URL expiry in seconds", ge=60, le=86400),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get presigned download URL for a file.
    
    The returned URL can be used to download the file directly from storage
    without going through the API server.
    
    URL expires after the specified time (default 1 hour).
    """
    # TODO: Add project access check
    
    file_service = FileService(db)
    download_url = await file_service.get_download_url(file_id, project_id, expiry)
    
    return {
        "file_id": str(file_id),
        "download_url": download_url,
        "expires_in": expiry
    }


@router.post(
    "",
    response_model=FileUploadResponseDTO,
    status_code=201,
    summary="Upload a file (legacy/small files)",
    description="Upload a file through the server (use /init for better performance)"
)
async def upload_file(
    project_id: UUID,
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a file and trigger RAG processing.
    
    The file will go through the following stages:
    1. Upload to blob storage
    2. Conversion (if needed)
    3. Parsing and enrichment
    4. Chunking
    5. Embedding generation
    
    Returns the file record with initial status.
    """
    # TODO: Add project access check (verify user has access to this project)
    # Get organization_id from project
    from app.repositories.project_repository import ProjectRepository
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    file_service = FileService(db)
    return await file_service.upload_file(
        file=file,
        project_id=project_id,
        organization_id=project.organization_id,
        user_id=current_user.id
    )


@router.get(
    "",
    response_model=FileListResponseDTO,
    summary="List files",
    description="Get a paginated list of files in a project"
)
def list_files(
    project_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    status: Optional[FileStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List files in a project with optional filtering and pagination.
    """
    # TODO: Add project access check
    
    file_service = FileService(db)
    return file_service.list_files(
        project_id=project_id,
        page=page,
        page_size=page_size,
        status_filter=status
    )


@router.get(
    "/{file_id}",
    response_model=FileDetailResponseDTO,
    summary="Get file details",
    description="Get detailed information about a file including metadata"
)
def get_file_detail(
    project_id: UUID,
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed file information including custom metadata.
    """
    # TODO: Add project access check
    
    file_service = FileService(db)
    return file_service.get_file_detail(file_id, project_id)


@router.get(
    "/{file_id}/status",
    response_model=FileStatusResponseDTO,
    summary="Get file processing status",
    description="Get detailed processing status and progress for a file"
)
def get_file_status(
    project_id: UUID,
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed file processing status including timestamps for each stage.
    """
    # TODO: Add project access check
    
    file_service = FileService(db)
    return file_service.get_file_status(file_id, project_id)


@router.put(
    "/{file_id}/metadata",
    response_model=FileMetadataResponseDTO,
    summary="Update file metadata",
    description="Update or create custom metadata for a file"
)
def update_file_metadata(
    project_id: UUID,
    file_id: UUID,
    metadata_request: FileMetadataRequestDTO,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update custom metadata for a file.
    Metadata is stored as JSON key-value pairs.
    """
    # TODO: Add project access check
    
    file_service = FileService(db)
    return file_service.update_metadata(
        file_id=file_id,
        project_id=project_id,
        metadata=metadata_request.metadata
    )


@router.delete(
    "/{file_id}",
    status_code=204,
    summary="Delete file",
    description="Delete a file from storage, vector database, and database"
)
async def delete_file(
    project_id: UUID,
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a file and all associated data:
    - Raw and processed files from blob storage
    - Vector embeddings from Pinecone
    - Database records (file, chunks, metadata)
    """
    # TODO: Add project access check
    
    file_service = FileService(db)
    await file_service.delete_file(file_id, project_id)
    return None


@router.post(
    "/search",
    response_model=FileSearchResultDTO,
    summary="Semantic search",
    description="Search for similar content across all files in a project"
)
async def search_files(
    project_id: UUID,
    search_request: FileSearchRequestDTO,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform semantic search across all files in a project.
    
    Returns the most relevant chunks with their scores and metadata.
    
    Note: In Phase 1, this is a stub. Phase 2 will implement actual
    semantic search using embeddings and Pinecone.
    """
    # TODO: Add project access check
    
    file_service = FileService(db)
    return await file_service.search_similar(
        query=search_request.query,
        project_id=project_id,
        top_k=search_request.top_k,
        filters=search_request.filters
    )

