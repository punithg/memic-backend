"""
File service for handling file upload, processing, and retrieval operations.
"""
import os
import mimetypes
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
import math

from app.models.file import File, FileStatus
from app.repositories.file_repository import (
    FileRepository,
    FileChunkRepository
)
from app.core.storage import get_storage_client
from app.core.vector_store import get_vector_store
from app.dtos.file_dto import (
    FileUploadResponseDTO,
    FileStatusResponseDTO,
    FileListResponseDTO,
    FileListItemDTO,
    FileMetadataResponseDTO,
    FileSearchResultDTO,
    FileChunkResultDTO,
    FileDetailResponseDTO,
    FileInitUploadRequestDTO,
    FileInitUploadResponseDTO,
    FileMetadataRequestDTO
)
from app.tasks.file_tasks import process_file_pipeline_task
import logging

logger = logging.getLogger(__name__)


class FileService:
    """Service for file operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.file_repo = FileRepository(db)
        self.chunk_repo = FileChunkRepository(db)
        self.storage_client = get_storage_client()
    
    async def upload_file(
        self,
        file: UploadFile,
        project_id: UUID,
        organization_id: UUID,
        user_id: UUID
    ) -> FileUploadResponseDTO:
        """
        Upload a file and initiate RAG processing pipeline.
        
        Args:
            file: Uploaded file
            project_id: Project ID
            organization_id: Organization ID for storage path
            user_id: User ID who uploaded the file
            
        Returns:
            FileUploadResponseDTO with file details
        """
        try:
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(file.filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Create file record
            new_file = File(
                name=file.filename,
                original_filename=file.filename,
                size=file_size,
                mime_type=mime_type,
                project_id=project_id,
                uploaded_by_user_id=user_id,
                status=FileStatus.UPLOADING,
                blob_storage_path="",  # Will be set after upload
                is_converted=False,
                total_chunks=0
            )
            
            self.db.add(new_file)
            self.db.flush()  # Get the ID without committing
            
            # Generate blob storage path
            blob_path = self.storage_client.generate_blob_path(
                org_id=str(organization_id),
                project_id=str(project_id),
                file_id=str(new_file.id),
                stage="raw",
                filename=file.filename
            )
            
            # Update blob path
            new_file.blob_storage_path = blob_path
            self.db.commit()
            self.db.refresh(new_file)
            
            # Upload to blob storage
            logger.info(f"Uploading file {new_file.id} to blob storage: {blob_path}")
            await self.storage_client.upload_file(
                file_content=file_content,
                blob_path=blob_path,
                content_type=mime_type
            )
            
            # Update status to uploaded
            self.file_repo.update_status(new_file.id, FileStatus.UPLOADED)
            
            # Trigger RAG processing pipeline asynchronously
            logger.info(f"Triggering RAG pipeline for file {new_file.id}")
            try:
                task_result = process_file_pipeline_task.delay(str(new_file.id), str(project_id))
                logger.info(f"Task queued successfully! Task ID: {task_result.id}")
            except Exception as task_error:
                logger.error(f"Failed to queue task: {task_error}", exc_info=True)
                # Don't fail the upload, but log the error
            
            return FileUploadResponseDTO.model_validate(new_file)
            
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            if 'new_file' in locals():
                self.file_repo.update_status(
                    new_file.id,
                    FileStatus.UPLOAD_FAILED,
                    error_message=str(e)
                )
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
    
    def get_file_status(self, file_id: UUID, project_id: UUID) -> FileStatusResponseDTO:
        """
        Get detailed file processing status.
        
        Args:
            file_id: File ID
            project_id: Project ID for tenant isolation
            
        Returns:
            FileStatusResponseDTO with detailed status
        """
        file = self.file_repo.get_with_chunks(file_id, project_id)
        
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileStatusResponseDTO.model_validate(file)
    
    def list_files(
        self,
        project_id: UUID,
        page: int = 1,
        page_size: int = 50,
        status_filter: Optional[FileStatus] = None
    ) -> FileListResponseDTO:
        """
        List files in a project with pagination.
        
        Args:
            project_id: Project ID
            page: Page number (1-indexed)
            page_size: Number of items per page
            status_filter: Optional status filter
            
        Returns:
            FileListResponseDTO with paginated results
        """
        files, total = self.file_repo.get_by_project(
            project_id,
            page=page,
            page_size=page_size,
            status_filter=status_filter
        )
        
        items = [FileListItemDTO.model_validate(f) for f in files]
        total_pages = math.ceil(total / page_size)
        
        return FileListResponseDTO(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    def get_file_detail(self, file_id: UUID, project_id: UUID) -> FileDetailResponseDTO:
        """
        Get detailed file information including metadata.
        
        Args:
            file_id: File ID
            project_id: Project ID
            
        Returns:
            FileDetailResponseDTO with all file details
        """
        file = self.file_repo.get_with_chunks(file_id, project_id)
        
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileDetailResponseDTO.model_validate(file)
    
    async def delete_file(self, file_id: UUID, project_id: UUID) -> bool:
        """
        Delete a file from storage, vector DB, and database.
        
        Args:
            file_id: File ID
            project_id: Project ID
            
        Returns:
            True if successful
        """
        file = self.file_repo.get_with_chunks(file_id, project_id)
        
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        try:
            # Delete from blob storage
            await self.storage_client.delete_file(file.blob_storage_path)
            
            # Delete chunks from vector DB if they exist
            if file.chunks:
                vector_store = get_vector_store()
                vector_ids = [chunk.vector_id for chunk in file.chunks if chunk.vector_id]
                if vector_ids:
                    await vector_store.delete(vector_ids, namespace=str(project_id))
            
            # Delete from database (cascades to chunks and metadata)
            self.db.delete(file)
            self.db.commit()
            
            logger.info(f"Deleted file {file_id} and all associated data")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")
    
    def update_metadata(
        self,
        file_id: UUID,
        project_id: UUID,
        metadata: Dict[str, Any]
    ) -> FileMetadataResponseDTO:
        """
        Update or create metadata for a file.
        
        Args:
            file_id: File ID
            project_id: Project ID
            metadata: Metadata dictionary
            
        Returns:
            FileMetadataResponseDTO
        """
        # Verify file exists and belongs to project
        file = self.file_repo.get_with_chunks(file_id, project_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Update metadata directly on file
        file.file_metadata = metadata
        self.db.commit()
        self.db.refresh(file)
        
        # Return metadata response
        return FileMetadataResponseDTO(
            file_id=file.id,
            metadata=file.file_metadata or {},
            created_at=file.created_at,
            updated_at=file.updated_at
        )
    
    async def search_similar(
        self,
        query: str,
        project_id: UUID,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> FileSearchResultDTO:
        """
        Semantic search for similar content (stub for Phase 1).
        In Phase 2, this will use actual embeddings and Pinecone.
        
        Args:
            query: Search query
            project_id: Project ID
            top_k: Number of results
            filters: Optional filters
            
        Returns:
            FileSearchResultDTO with results
        """
        # Phase 1: Return placeholder results
        logger.info(f"[STUB] Semantic search for query: {query} in project {project_id}")
        
        # TODO: In Phase 2, implement actual semantic search:
        # 1. Generate embedding for query
        # 2. Query Pinecone with embedding
        # 3. Fetch chunks from database
        # 4. Return formatted results
        
        return FileSearchResultDTO(
            query=query,
            results=[],
            total_results=0
        )
    
    async def init_upload(
        self,
        request: FileInitUploadRequestDTO,
        project_id: UUID,
        organization_id: UUID,
        user_id: UUID
    ) -> FileInitUploadResponseDTO:
        """
        Initialize file upload and return presigned URL for direct upload.
        
        Args:
            request: File initialization request with filename, size, mime_type
            project_id: Project ID
            organization_id: Organization ID for storage path
            user_id: User ID who is uploading
            
        Returns:
            FileInitUploadResponseDTO with file_id and upload_url
        """
        try:
            # Create file record with UPLOADING status
            new_file = File(
                name=request.filename,
                original_filename=request.filename,
                size=request.size,
                mime_type=request.mime_type,
                project_id=project_id,
                uploaded_by_user_id=user_id,
                status=FileStatus.UPLOADING,
                blob_storage_path="",  # Will be set below
                is_converted=False,
                total_chunks=0
            )
            
            self.db.add(new_file)
            self.db.flush()  # Get the ID without committing
            
            # Generate blob storage path
            blob_path = self.storage_client.generate_blob_path(
                org_id=str(organization_id),
                project_id=str(project_id),
                file_id=str(new_file.id),
                stage="raw",
                filename=request.filename
            )
            
            # Update blob path
            new_file.blob_storage_path = blob_path
            self.db.commit()
            self.db.refresh(new_file)
            
            # Set metadata if provided
            if request.metadata:
                new_file.file_metadata = request.metadata
                self.db.commit()
            
            # Generate presigned upload URL
            logger.info(f"Generating presigned upload URL for file {new_file.id}")
            upload_url = await self.storage_client.get_upload_url(
                blob_path=blob_path,
                expiry_seconds=3600,  # 1 hour to upload
                content_type=request.mime_type
            )
            
            return FileInitUploadResponseDTO(
                file_id=new_file.id,
                upload_url=upload_url,
                expires_in=3600
            )
            
        except Exception as e:
            logger.error(f"Error initializing upload: {str(e)}")
            if 'new_file' in locals():
                self.file_repo.update_status(
                    new_file.id,
                    FileStatus.UPLOAD_FAILED,
                    error_message=str(e)
                )
            raise HTTPException(status_code=500, detail=f"Upload initialization failed: {str(e)}")
    
    async def confirm_upload(
        self,
        file_id: UUID,
        project_id: UUID
    ) -> FileUploadResponseDTO:
        """
        Confirm file upload completion and trigger RAG processing pipeline.
        
        Args:
            file_id: File ID
            project_id: Project ID for validation
            
        Returns:
            FileUploadResponseDTO with file details
        """
        try:
            # Get file record
            file = self.file_repo.get_with_chunks(file_id, project_id)
            
            if not file:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Verify file is in UPLOADING status
            if file.status != FileStatus.UPLOADING:
                raise HTTPException(
                    status_code=400,
                    detail=f"File is not in UPLOADING status. Current status: {file.status}"
                )
            
            # Verify file exists in storage
            file_exists = await self.storage_client.file_exists(file.blob_storage_path)
            if not file_exists:
                self.file_repo.update_status(
                    file_id,
                    FileStatus.UPLOAD_FAILED,
                    error_message="File not found in storage after upload"
                )
                raise HTTPException(
                    status_code=400,
                    detail="File not found in storage. Upload may have failed."
                )
            
            # Update status to UPLOADED
            self.file_repo.update_status(file_id, FileStatus.UPLOADED)
            
            # Trigger RAG processing pipeline asynchronously
            logger.info(f"Triggering RAG pipeline for file {file_id}")
            try:
                task_result = process_file_pipeline_task.delay(str(file_id), str(project_id))
                logger.info(f"Task queued successfully! Task ID: {task_result.id}")
            except Exception as task_error:
                logger.error(f"Failed to queue task: {task_error}", exc_info=True)
                # Don't fail the upload, but log the error
            
            # Refresh to get updated status
            self.db.refresh(file)
            
            return FileUploadResponseDTO.model_validate(file)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error confirming upload for file {file_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Upload confirmation failed: {str(e)}")
    
    async def get_download_url(
        self,
        file_id: UUID,
        project_id: UUID,
        expiry_seconds: int = 3600
    ) -> str:
        """
        Get presigned download URL for a file.
        
        Args:
            file_id: File ID
            project_id: Project ID for validation
            expiry_seconds: URL expiry time in seconds
            
        Returns:
            Presigned download URL
        """
        try:
            # Get file record
            file = self.file_repo.get_with_chunks(file_id, project_id)
            
            if not file:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Check if file is ready (uploaded at minimum)
            if file.status == FileStatus.UPLOADING:
                raise HTTPException(
                    status_code=400,
                    detail="File upload not confirmed yet"
                )
            
            # Generate presigned download URL
            logger.info(f"Generating presigned download URL for file {file_id}")
            download_url = await self.storage_client.get_file_url(
                blob_path=file.blob_storage_path,
                expiry_seconds=expiry_seconds
            )
            
            return download_url
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating download URL for file {file_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")

