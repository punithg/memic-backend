"""
Document parsing tasks for extracting structure and content.

This module converts documents (PDF, Excel, PowerPoint) into enriched JSON
"digital twins" with structured sections, viewport coordinates, and optional
LLM-enriched metadata.
"""

import asyncio
import logging
from datetime import datetime, UTC
from uuid import UUID

from app.celery_app import celery_app
from app.models.file import FileStatus
from app.database import SessionLocal
from app.repositories.file_repository import FileRepository
from app.core.storage import get_storage_client

from .parsing import PDFParser, ExcelParser, PowerPointParser
from .parsing.utils.storage_helper import ParsingStorageHelper
from .parsing import config as parsing_config

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async functions in Celery tasks."""
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


def get_parser_for_file(
    file_content: bytes, filename: str, document_id: str
) -> PDFParser | ExcelParser | PowerPointParser:
    """
    Select appropriate parser based on file extension.

    Args:
        file_content: File bytes
        filename: Original filename
        document_id: Document UUID

    Returns:
        Parser instance

    Raises:
        ValueError: If file type is not supported
    """
    filename_lower = filename.lower()

    if filename_lower.endswith(".pdf"):
        return PDFParser(file_content, filename, document_id)
    elif filename_lower.endswith((".xlsx", ".xls")):
        return ExcelParser(file_content, filename, document_id)
    elif filename_lower.endswith((".pptx", ".ppt")):
        return PowerPointParser(file_content, filename, document_id)
    else:
        raise ValueError(
            f"Unsupported file type for parsing: {filename}. "
            f"Supported types: PDF, Excel (.xlsx, .xls), PowerPoint (.pptx, .ppt)"
        )


@celery_app.task(
    bind=True,
    name="app.tasks.parsing_tasks.parse_file",
    max_retries=3,
    default_retry_delay=60,
)
def parse_file_task(self, file_id: str, org_id: str, project_id: str):
    """
    Parse document into enriched JSON digital twin.

    This task:
    1. Downloads file from Azure Blob Storage
    2. Selects appropriate parser (PDF/Excel/PowerPoint)
    3. Extracts content with viewport coordinates
    4. Optionally enriches with LLM metadata
    5. Uploads enriched JSON to storage
    6. Updates database with results

    Args:
        file_id: File UUID
        org_id: Organization UUID
        project_id: Project UUID

    Returns:
        dict: Parsing result with status and enriched_path

    Raises:
        Exception: Re-raises for Celery retry mechanism
    """
    db = SessionLocal()
    storage_client = None

    try:
        logger.info(f"Starting parsing for file {file_id}")

        # Validate configuration
        config_status = parsing_config.validate_config()
        if not config_status.get("azure_form_recognizer"):
            raise RuntimeError(
                "Azure Form Recognizer not configured. "
                "Please set AZURE_AFR_ENDPOINT and AZURE_AFR_API_KEY"
            )

        # Log enabled features for monitoring
        enabled_features = parsing_config.get_enabled_features()
        logger.info(f"Parsing with features: {enabled_features or 'basic only'}")

        # Initialize repositories and clients
        file_repo = FileRepository(db)
        storage_client = get_storage_client()
        storage_helper = ParsingStorageHelper(storage_client)

        # Get file record
        file = file_repo.get(UUID(file_id))
        if not file:
            raise ValueError(f"File not found: {file_id}")

        # Update status to parsing_started
        file_repo.update_status(UUID(file_id), FileStatus.PARSING_STARTED)
        file.parsing_started_at = datetime.now(UTC)
        db.commit()

        # Determine which file to parse (converted or original)
        if file.is_converted and file.converted_file_path:
            blob_path = file.converted_file_path
            # Use converted filename for parser selection (e.g., sample.pdf instead of sample.docx)
            parse_filename = blob_path.split('/')[-1]  # Get filename from path
            logger.info(f"Parsing converted file: {blob_path} as {parse_filename}")
        else:
            blob_path = file.blob_storage_path
            parse_filename = file.original_filename
            logger.info(f"Parsing original file: {blob_path}")

        # Download file from storage
        file_content = run_async(storage_helper.download_file(blob_path))

        # Get appropriate parser based on actual file type
        parser = get_parser_for_file(
            file_content=file_content,
            filename=parse_filename,  # Use converted filename if file was converted
            document_id=file_id,
        )

        logger.info(f"Using parser: {parser.__class__.__name__}")

        # Parse document
        enriched_json = run_async(parser.parse())

        # Generate enriched JSON path
        enriched_path = storage_helper.generate_enriched_json_path(
            org_id=org_id,
            project_id=project_id,
            file_id=file_id,
        )

        # Upload enriched JSON to storage
        run_async(storage_helper.upload_enriched_json(enriched_json, enriched_path))

        # Update file record
        file_repo.update_status(UUID(file_id), FileStatus.PARSING_COMPLETE)
        file.enriched_file_path = enriched_path
        file.parsing_completed_at = datetime.now(UTC)

        # Store enriched_metadata if available (for easy querying)
        enriched_metadata = enriched_json.get("enriched_metadata", {})
        if enriched_metadata:
            file.document_metadata = enriched_metadata
            logger.info(
                f"Stored enriched metadata: type={enriched_metadata.get('document_type')}"
            )

        db.commit()

        logger.info(f"Parsing completed successfully for file {file_id}")

        return {
            "file_id": file_id,
            "status": "parsing_complete",
            "enriched_path": enriched_path,
            "document_type": enriched_metadata.get("document_type"),
            "total_sections": enriched_json.get("metadata", {}).get(
                "total_sections", 0
            ),
        }

    except Exception as e:
        logger.error(f"Error parsing file {file_id}: {str(e)}", exc_info=True)

        # Update status to parsing_failed
        try:
            file_repo = FileRepository(db)
            file_repo.update_status(
                UUID(file_id), FileStatus.PARSING_FAILED, error_message=str(e)
            )
            db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status: {str(db_error)}")

        # Retry the task
        raise self.retry(exc=e)

    finally:
        db.close()

