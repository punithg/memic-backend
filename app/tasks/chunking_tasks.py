"""
Document chunking tasks for breaking documents into semantic chunks.
This is a stub implementation that will be replaced with actual logic in Phase 2.
"""
import time
import logging
from datetime import datetime, UTC
from uuid import UUID

from app.celery_app import celery_app
from app.models.file import FileStatus
from app.models.file_chunk import FileChunk
from app.database import SessionLocal
from app.repositories.file_repository import FileRepository, FileChunkRepository

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.chunking_tasks.chunk_file",
    max_retries=3,
    default_retry_delay=60
)
def chunk_file_task(self, file_id: str, project_id: str):
    """
    Dummy task for document chunking (Phase 1 stub).
    In Phase 2, this will be replaced with actual chunking logic using
    semantic chunking algorithms from rag-chunking.
    
    Args:
        file_id: File ID
        project_id: Project ID
        
    Returns:
        Dict with chunking result
    """
    db = SessionLocal()
    try:
        logger.info(f"[STUB] Starting chunking for file {file_id}")
        
        file_repo = FileRepository(db)
        chunk_repo = FileChunkRepository(db)
        
        # Update status to chunking_started
        file_repo.update_status(UUID(file_id), FileStatus.CHUNKING_STARTED)
        
        # Mark chunking start time
        file = file_repo.get(UUID(file_id))
        if file:
            file.chunking_started_at = datetime.now(UTC)
            db.commit()
        
        # Simulate chunking work (Phase 1)
        time.sleep(2)
        logger.info(f"[STUB] Chunking simulation complete for file {file_id}")
        
        # Create dummy chunks for testing
        # Note: chunk text is stored in blob storage (blob_storage_path), NOT in database
        dummy_chunks = []
        for i in range(3):
            # Generate proper blob path (remove /raw/filename from end, add /chunks/)
            base_path = file.blob_storage_path.rsplit('/', 2)[0]  # Remove /raw/filename
            chunk_blob_path = f"{base_path}/chunks/chunk_{i}.json"
            
            chunk = FileChunk(
                file_id=UUID(file_id),
                chunk_index=i,
                token_count=50,
                blob_storage_path=chunk_blob_path,
                chunk_metadata={"page": i + 1, "type": "text"}
            )
            dummy_chunks.append(chunk)
        
        # Save chunks
        for chunk in dummy_chunks:
            db.add(chunk)
        db.commit()
        
        # Update status to chunking_complete
        file_repo.update_status(UUID(file_id), FileStatus.CHUNKING_COMPLETE)
        
        # Mark chunking complete time and update total chunks
        file = file_repo.get(UUID(file_id))
        if file:
            file.total_chunks = len(dummy_chunks)
            file.chunking_completed_at = datetime.now(UTC)
            db.commit()
        
        return {
            "file_id": file_id,
            "status": "chunking_complete",
            "total_chunks": len(dummy_chunks),
            "message": "File chunked successfully (stub)"
        }
        
    except Exception as e:
        logger.error(f"Error chunking file {file_id}: {str(e)}")
        
        # Update status to chunking_failed
        file_repo = FileRepository(db)
        file_repo.update_status(
            UUID(file_id),
            FileStatus.CHUNKING_FAILED,
            error_message=str(e)
        )
        
        # Retry the task
        raise self.retry(exc=e)
        
    finally:
        db.close()

