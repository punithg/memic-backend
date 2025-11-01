"""
File conversion tasks for converting documents to PDF using LibreOffice.
Intelligently skips files that don't need conversion (PDF, XLSX, PPTX, audio, email).
"""
import logging
import os
import asyncio
from datetime import datetime, UTC
from uuid import UUID
from typing import Dict, Any

from app.celery_app import celery_app
from app.models.file import FileStatus
from app.database import SessionLocal
from app.repositories.file_repository import FileRepository
from app.core.storage import get_storage_client
from app.tasks.file_converter import needs_conversion, convert_file_to_pdf

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            # Loop is closed, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # No event loop in current thread, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)


@celery_app.task(
    bind=True,
    name="app.tasks.conversion_tasks.convert_file",
    max_retries=3,
    default_retry_delay=60
)
def convert_file_task(self, file_id: str, org_id: str, project_id: str) -> Dict[str, Any]:
    """
    Convert file to PDF if needed, otherwise mark as ready for parsing.
    
    Files that DON'T need conversion (skip immediately):
    - PDF, JSON
    - Modern Office formats (XLSX, PPTX)
    - Audio files (MP3, WAV, M4A, FLAC, OGG, AAC)
    - Email files (EML, MSG)
    
    Files that DO need conversion (LibreOffice):
    - Word documents (DOC, DOCX)
    - Old Office formats (XLS, PPT)
    - Images (JPG, JPEG, PNG)
    
    Args:
        file_id: File ID
        org_id: Organization ID
        project_id: Project ID
        
    Returns:
        Dict with conversion result
    """
    db = SessionLocal()
    storage_client = None
    
    try:
        logger.info(f"Starting conversion check for file {file_id}")
        
        file_repo = FileRepository(db)
        
        # Get file record
        file = file_repo.get(UUID(file_id))
        if not file:
            raise ValueError(f"File {file_id} not found")
        
        filename = file.original_filename
        logger.info(f"Processing file: {filename}")
        
        # Check if file needs conversion
        if not needs_conversion(filename):
            logger.info(f"File {filename} does not need conversion, skipping to parsing")
            
            # Update status to conversion_complete (skipped)
            file_repo.update_status(UUID(file_id), FileStatus.CONVERSION_COMPLETE)
            
            file = file_repo.get(UUID(file_id))
            if file:
                file.is_converted = False  # Not converted, using original
                file.converted_file_path = None  # Parser will use blob_storage_path
                file.conversion_started_at = datetime.now(UTC)
                file.conversion_completed_at = datetime.now(UTC)
                db.commit()
            
            logger.info(f"File {filename} marked as conversion complete (skipped)")

            # Chain to parsing task
            from app.tasks.parsing_tasks import parse_file_task
            parse_file_task.delay(file_id, org_id, project_id)
            logger.info(f"Triggered parsing task for file {file_id}")

            return {
                "file_id": file_id,
                "status": "conversion_complete",
                "converted": False,
                "message": f"File {filename} does not need conversion"
            }
        
        # File needs conversion
        logger.info(f"File {filename} requires conversion to PDF")
        
        # Update status to conversion_started
        file_repo.update_status(UUID(file_id), FileStatus.CONVERSION_STARTED)
        
        file = file_repo.get(UUID(file_id))
        if file:
            file.conversion_started_at = datetime.now(UTC)
            db.commit()
        
        # Initialize storage client
        storage_client = get_storage_client()
        
        # Download file from storage
        logger.info(f"Downloading file from: {file.blob_storage_path}")
        file_content = run_async(storage_client.download_file(file.blob_storage_path))
        logger.info(f"Downloaded {len(file_content)} bytes")
        
        # Convert to PDF using LibreOffice
        logger.info(f"Converting {filename} to PDF")
        pdf_content, pdf_filename = convert_file_to_pdf(file_content, filename)
        logger.info(f"Conversion complete: {pdf_filename} ({len(pdf_content)} bytes)")
        
        # Generate converted file path
        # Path format: org_id/project_id/file_id/converted/filename.pdf
        converted_blob_path = f"{org_id}/{project_id}/{file_id}/converted/{pdf_filename}"
        
        # Upload converted PDF to storage
        logger.info(f"Uploading converted PDF to: {converted_blob_path}")
        run_async(storage_client.upload_file(
            file_content=pdf_content,
            blob_path=converted_blob_path,
            content_type="application/pdf"
        ))
        logger.info("Upload complete")
        
        # Update file record
        file_repo.update_status(UUID(file_id), FileStatus.CONVERSION_COMPLETE)
        
        file = file_repo.get(UUID(file_id))
        if file:
            file.is_converted = True
            file.converted_file_path = converted_blob_path
            file.conversion_completed_at = datetime.now(UTC)
            db.commit()
        
        logger.info(f"File {filename} converted successfully to {pdf_filename}")

        # Chain to parsing task
        from app.tasks.parsing_tasks import parse_file_task
        parse_file_task.delay(file_id, org_id, project_id)
        logger.info(f"Triggered parsing task for file {file_id}")

        return {
            "file_id": file_id,
            "status": "conversion_complete",
            "converted": True,
            "converted_path": converted_blob_path,
            "message": f"File converted successfully to {pdf_filename}"
        }
        
    except Exception as e:
        logger.error(f"Error converting file {file_id}: {str(e)}", exc_info=True)
        
        # Update status to conversion_failed
        try:
            file_repo = FileRepository(db)
            file_repo.update_status(
                UUID(file_id),
                FileStatus.CONVERSION_FAILED,
                error_message=str(e)
            )
        except Exception as db_error:
            logger.error(f"Failed to update error status: {str(db_error)}")
        
        # Retry the task
        raise self.retry(exc=e)
        
    finally:
        db.close()

