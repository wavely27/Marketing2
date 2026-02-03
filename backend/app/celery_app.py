"""Celery application configuration for async task processing"""
from celery import Celery
import os

# Redis broker and backend configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery instance
celery_app = Celery(
    "marketing2_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.workflow_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,
    
    # Task execution settings
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    
    # Queue routing
    task_routes={
        "app.tasks.workflow_tasks.generate_script_task": {"queue": "ai_generation"},
        "app.tasks.workflow_tasks.generate_media_task": {"queue": "ai_generation"},
        "app.tasks.workflow_tasks.render_video_task": {"queue": "video_processing"},
    },
    
    # Retry settings
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,
    
    # Rate limiting for AI tasks
    task_annotations={
        "app.tasks.workflow_tasks.generate_script_task": {"rate_limit": "10/m"},
        "app.tasks.workflow_tasks.generate_media_task": {"rate_limit": "20/m"},
    }
)

# Optional: Configure multiple queues
celery_app.conf.task_queues = {
    "default": {
        "exchange": "default",
        "routing_key": "default",
    },
    "ai_generation": {
        "exchange": "ai_generation",
        "routing_key": "ai_generation",
    },
    "video_processing": {
        "exchange": "video_processing",
        "routing_key": "video_processing",
    }
}

if __name__ == "__main__":
    celery_app.start()
