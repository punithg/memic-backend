"""
File conversion tasks for converting documents to PDF.
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
    name="app.tasks.conversion_tasks.convert_file",
    max_retries=3,
    default_retry_delay=60
)
def convert_file_task(self, file_id: str, project_id: str):
    """
    Dummy task for file conversion (Phase 1 stub).
    In Phase 2, this will be replaced with actual conversion logic.
    
    Args:
        file_id: File ID
        project_id: Project ID
        
    Returns:
        Dict with conversion result
    """
    db = SessionLocal()
    try:
        logger.info(f"[STUB] Starting conversion for file {file_id}")
        
        file_repo = FileRepository(db)
        
        # Update status to conversion_started
        file_repo.update_status(UUID(file_id), FileStatus.CONVERSION_STARTED)
        
        # Mark conversion start time
        file = file_repo.get(UUID(file_id))
        if file:
            file.conversion_started_at = datetime.now(UTC)
            db.commit()
        
        # Simulate conversion work (Phase 1)
        time.sleep(2)
        logger.info(f"[STUB] Conversion simulation complete for file {file_id}")
        
        # Update status to conversion_complete
        file_repo.update_status(UUID(file_id), FileStatus.CONVERSION_COMPLETE)
        
        # Mark conversion complete time
        file = file_repo.get(UUID(file_id))
        if file:
            file.is_converted = True
            file.converted_file_path = f"{file.blob_storage_path}/converted.pdf"
            file.conversion_completed_at = datetime.now(UTC)
            db.commit()
        
        return {
            "file_id": file_id,
            "status": "conversion_complete",
            "message": "File converted successfully (stub)"
        }
        
    except Exception as e:
        logger.error(f"Error converting file {file_id}: {str(e)}")
        
        # Update status to conversion_failed
        file_repo = FileRepository(db)
        file_repo.update_status(
            UUID(file_id),
            FileStatus.CONVERSION_FAILED,
            error_message=str(e)
        )
        
        # Retry the task
        raise self.retry(exc=e)
        
    finally:
        db.close()

