"""
Embedding tasks for generating and storing vector embeddings.
This is a stub implementation that will be replaced with actual logic in Phase 2.
"""
import time
import logging
from datetime import datetime, UTC
from uuid import UUID

from app.celery_app import celery_app
from app.models.file import FileStatus
from app.database import SessionLocal
from app.repositories.file_repository import FileRepository, FileChunkRepository

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.embedding_tasks.embed_chunks",
    max_retries=3,
    default_retry_delay=60
)
def embed_chunks_task(self, file_id: str, project_id: str):
    """
    Dummy task for embedding generation (Phase 1 stub).
    In Phase 2, this will be replaced with actual embedding logic using
    Azure OpenAI and Pinecone from rag-embedding.
    
    Args:
        file_id: File ID
        project_id: Project ID
        
    Returns:
        Dict with embedding result
    """
    db = SessionLocal()
    try:
        logger.info(f"[STUB] Starting embedding for file {file_id}")
        
        file_repo = FileRepository(db)
        chunk_repo = FileChunkRepository(db)
        
        # Update status to embedding_started
        file_repo.update_status(UUID(file_id), FileStatus.EMBEDDING_STARTED)
        
        # Mark embedding start time
        file = file_repo.get(UUID(file_id))
        if file:
            file.embedding_started_at = datetime.now(UTC)
            db.commit()
        
        # Get all chunks for this file
        chunks = chunk_repo.get_by_file(UUID(file_id))
        
        # Simulate embedding work (Phase 1)
        time.sleep(2)
        logger.info(f"[STUB] Embedding simulation complete for file {file_id}")
        
        # Update vector IDs for chunks (dummy values)
        for i, chunk in enumerate(chunks):
            chunk.vector_id = f"vec_{file_id}_{i}"
        db.commit()
        
        # Update status to embedding_complete
        file_repo.update_status(UUID(file_id), FileStatus.EMBEDDING_COMPLETE)
        
        # Mark embedding complete time
        file = file_repo.get(UUID(file_id))
        if file:
            file.embedding_completed_at = datetime.now(UTC)
            db.commit()
        
        # Final status update to READY
        file_repo.update_status(UUID(file_id), FileStatus.READY)
        
        logger.info(f"[STUB] File {file_id} is now READY for retrieval")
        
        return {
            "file_id": file_id,
            "status": "ready",
            "total_embeddings": len(chunks),
            "message": "File embeddings created successfully (stub)"
        }
        
    except Exception as e:
        logger.error(f"Error embedding file {file_id}: {str(e)}")
        
        # Update status to embedding_failed
        file_repo = FileRepository(db)
        file_repo.update_status(
            UUID(file_id),
            FileStatus.EMBEDDING_FAILED,
            error_message=str(e)
        )
        
        # Retry the task
        raise self.retry(exc=e)
        
    finally:
        db.close()

