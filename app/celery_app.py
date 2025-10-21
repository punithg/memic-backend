from celery import Celery
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "memic_rag",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    'app.tasks'
])

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes max
    task_soft_time_limit=1500,  # 25 minutes soft limit
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    
    # Task routing
    task_routes={
        "app.tasks.file_tasks.*": {"queue": "files"},
        "app.tasks.conversion_tasks.*": {"queue": "conversion"},
        "app.tasks.parsing_tasks.*": {"queue": "parsing"},
        "app.tasks.chunking_tasks.*": {"queue": "chunking"},
        "app.tasks.embedding_tasks.*": {"queue": "embedding"}
    }
)

logger.info("Celery app configured successfully")

# Explicitly import tasks to ensure they're registered
from app.tasks import file_tasks, conversion_tasks, parsing_tasks, chunking_tasks, embedding_tasks

