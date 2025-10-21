"""
Document parsing tasks for extracting structure and content.
This is a stub implementation that will be replaced with actual logic in Phase 2.
"""
import time
import logging
from datetime import datetime, UTC
from uuid import UUID

from app.celery_app import celery_app
from app.models.file import FileStatus
from app.database import SessionLocal
from app.repositories.file_repository import FileRepository

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.parsing_tasks.parse_file",
    max_retries=3,
    default_retry_delay=60
)
def parse_file_task(self, file_id: str, project_id: str):
    """
    Dummy task for document parsing (Phase 1 stub).
    In Phase 2, this will be replaced with actual parsing logic using
    Azure Document Intelligence or other parsers.
    
    Args:
        file_id: File ID
        project_id: Project ID
        
    Returns:
        Dict with parsing result
    """
    db = SessionLocal()
    try:
        logger.info(f"[STUB] Starting parsing for file {file_id}")
        
        file_repo = FileRepository(db)
        
        # Update status to parsing_started
        file_repo.update_status(UUID(file_id), FileStatus.PARSING_STARTED)
        
        # Mark parsing start time
        file = file_repo.get(UUID(file_id))
        if file:
            file.parsing_started_at = datetime.now(UTC)
            db.commit()
        
        # Simulate parsing work (Phase 1)
        time.sleep(2)
        logger.info(f"[STUB] Parsing simulation complete for file {file_id}")
        
        # Update status to parsing_complete
        file_repo.update_status(UUID(file_id), FileStatus.PARSING_COMPLETE)
        
        # Mark parsing complete time and set enriched file path
        file = file_repo.get(UUID(file_id))
        if file:
            file.enriched_file_path = f"{file.blob_storage_path}/enriched.json"
            file.parsing_completed_at = datetime.now(UTC)
            db.commit()
        
        return {
            "file_id": file_id,
            "status": "parsing_complete",
            "message": "File parsed successfully (stub)"
        }
        
    except Exception as e:
        logger.error(f"Error parsing file {file_id}: {str(e)}")
        
        # Update status to parsing_failed
        file_repo = FileRepository(db)
        file_repo.update_status(
            UUID(file_id),
            FileStatus.PARSING_FAILED,
            error_message=str(e)
        )
        
        # Retry the task
        raise self.retry(exc=e)
        
    finally:
        db.close()

