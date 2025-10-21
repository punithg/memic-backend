"""
Celery tasks for RAG pipeline processing.

This package contains all the asynchronous background tasks for:
- File conversion
- Document parsing
- Text chunking
- Vector embedding
"""

# Import all tasks to ensure they're registered with Celery
from app.tasks.file_tasks import process_file_pipeline_task, update_file_status_task
from app.tasks.conversion_tasks import convert_file_task
from app.tasks.parsing_tasks import parse_file_task
from app.tasks.chunking_tasks import chunk_file_task
from app.tasks.embedding_tasks import embed_chunks_task

__all__ = [
    'process_file_pipeline_task',
    'update_file_status_task',
    'convert_file_task',
    'parse_file_task',
    'chunk_file_task',
    'embed_chunks_task',
]

