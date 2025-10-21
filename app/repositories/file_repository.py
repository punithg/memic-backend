from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.file import File, FileStatus
from app.models.file_chunk import FileChunk
from app.repositories.base_repository import BaseRepository
from app.core.tenant_context import TenantContext


class FileRepository(BaseRepository[File]):
    """Repository for File operations."""
    
    def __init__(self, db: Session):
        super().__init__(File, db)
    
    def get_by_project(
        self,
        project_id: UUID,
        page: int = 1,
        page_size: int = 50,
        status_filter: Optional[FileStatus] = None
    ) -> tuple[List[File], int]:
        """
        Get files by project with pagination and optional status filter.
        
        Args:
            project_id: Project ID
            page: Page number (1-indexed)
            page_size: Number of items per page
            status_filter: Optional status filter
            
        Returns:
            Tuple of (files list, total count)
        """
        query = self.db.query(File).filter(File.project_id == project_id)
        
        if status_filter:
            query = query.filter(File.status == status_filter)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and sorting
        files = query.order_by(desc(File.created_at))\
                    .offset((page - 1) * page_size)\
                    .limit(page_size)\
                    .all()
        
        return files, total
    
    def get_with_chunks(self, file_id: UUID, project_id: UUID) -> Optional[File]:
        """
        Get file with all its chunks.
        
        Args:
            file_id: File ID
            project_id: Project ID for tenant isolation
            
        Returns:
            File with chunks if found
        """
        return self.db.query(File)\
                    .filter(and_(
                        File.id == file_id,
                        File.project_id == project_id
                    ))\
                    .first()
    
    def update_status(
        self,
        file_id: UUID,
        status: FileStatus,
        error_message: Optional[str] = None
    ) -> Optional[File]:
        """
        Update file status.
        
        Args:
            file_id: File ID
            status: New status
            error_message: Optional error message
            
        Returns:
            Updated file if found
        """
        file = self.db.query(File).filter(File.id == file_id).first()
        if file:
            file.status = status
            if error_message:
                file.error_message = error_message
            self.db.commit()
            self.db.refresh(file)
        return file
    
    def get_by_status(
        self,
        project_id: UUID,
        status: FileStatus
    ) -> List[File]:
        """
        Get all files in a project with specific status.
        
        Args:
            project_id: Project ID
            status: File status
            
        Returns:
            List of files
        """
        return self.db.query(File)\
                    .filter(and_(
                        File.project_id == project_id,
                        File.status == status
                    ))\
                    .all()


class FileChunkRepository(BaseRepository[FileChunk]):
    """Repository for FileChunk operations."""
    
    def __init__(self, db: Session):
        super().__init__(FileChunk, db)
    
    def get_by_file(self, file_id: UUID) -> List[FileChunk]:
        """
        Get all chunks for a file.
        
        Args:
            file_id: File ID
            
        Returns:
            List of chunks ordered by chunk_index
        """
        return self.db.query(FileChunk)\
                    .filter(FileChunk.file_id == file_id)\
                    .order_by(FileChunk.chunk_index)\
                    .all()
    
    def get_by_vector_ids(self, vector_ids: List[str]) -> List[FileChunk]:
        """
        Get chunks by their vector IDs.
        
        Args:
            vector_ids: List of vector IDs from Pinecone
            
        Returns:
            List of matching chunks
        """
        return self.db.query(FileChunk)\
                    .filter(FileChunk.vector_id.in_(vector_ids))\
                    .all()
    
    def bulk_create(self, chunks: List[FileChunk]) -> List[FileChunk]:
        """
        Bulk create chunks.
        
        Args:
            chunks: List of FileChunk objects
            
        Returns:
            Created chunks
        """
        self.db.bulk_save_objects(chunks)
        self.db.commit()
        return chunks
    
    def update_vector_id(self, chunk_id: UUID, vector_id: str) -> Optional[FileChunk]:
        """
        Update the vector ID for a chunk after embedding.
        
        Args:
            chunk_id: Chunk ID
            vector_id: Vector ID in Pinecone
            
        Returns:
            Updated chunk if found
        """
        chunk = self.db.query(FileChunk).filter(FileChunk.id == chunk_id).first()
        if chunk:
            chunk.vector_id = vector_id
            self.db.commit()
            self.db.refresh(chunk)
        return chunk

