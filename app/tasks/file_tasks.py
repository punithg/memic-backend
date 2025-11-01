"""
Main orchestrator tasks for RAG file processing pipeline.
"""
from celery import chain
from app.celery_app import celery_app
from app.models.file import FileStatus
from app.database import SessionLocal
from app.repositories.file_repository import FileRepository
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.file_tasks.process_file_pipeline")
def process_file_pipeline_task(self, file_id: str, project_id: str):
    """
    Main orchestrator task that chains all processing steps.
    
    Args:
        file_id: File ID (as string for JSON serialization)
        project_id: Project ID (as string)
    """
    try:
        logger.info(f"Starting RAG pipeline for file {file_id}")
        
        # Import other tasks
        from app.tasks.conversion_tasks import convert_file_task
        from app.tasks.parsing_tasks import parse_file_task
        from app.tasks.chunking_tasks import chunk_file_task
        from app.tasks.embedding_tasks import embed_chunks_task
        from app.tasks.file_converter import needs_conversion
        from app.repositories.project_repository import ProjectRepository
        
        # Get file and project info
        db = SessionLocal()
        try:
            file_repo = FileRepository(db)
            project_repo = ProjectRepository(db)
            
            file = file_repo.get(UUID(file_id))
            if not file:
                raise ValueError(f"File {file_id} not found")
            
            project = project_repo.get(UUID(project_id))
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            org_id = str(project.organization_id)
            
            # Build task chain - always run conversion task (it will skip if not needed)
            # Use si() (signature immutable) so tasks ignore previous results
            task_chain = chain(
                convert_file_task.si(file_id, org_id, project_id),
                parse_file_task.si(file_id, org_id, project_id),
                chunk_file_task.si(file_id, project_id),
                embed_chunks_task.si(file_id, project_id)
            )
            
            # Execute the chain
            result = task_chain.apply_async()
            logger.info(f"Pipeline chain started for file {file_id}")
            
            return {
                "file_id": file_id,
                "status": "pipeline_started",
                "chain_id": str(result.id)
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in pipeline for file {file_id}: {str(e)}")
        
        # Update file status to error
        db = SessionLocal()
        try:
            file_repo = FileRepository(db)
            file_repo.update_status(
                UUID(file_id),
                FileStatus.UPLOAD_FAILED,
                error_message=str(e)
            )
        finally:
            db.close()
        
        raise


@celery_app.task(name="app.tasks.file_tasks.update_file_status")
def update_file_status_task(file_id: str, status: str, error_message: str = None):
    """
    Helper task to update file status.
    
    Args:
        file_id: File ID
        status: New status
        error_message: Optional error message
    """
    db = SessionLocal()
    try:
        file_repo = FileRepository(db)
        file_repo.update_status(
            UUID(file_id),
            FileStatus(status),
            error_message=error_message
        )
        logger.info(f"Updated file {file_id} status to {status}")
    finally:
        db.close()

