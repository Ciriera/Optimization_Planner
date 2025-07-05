from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "app",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    broker_connection_retry_on_startup=True
)

celery_app.conf.task_routes = {
    "app.tasks.*": {"queue": "default"},
    "app.tasks.algorithms.*": {"queue": "algorithms"},
    "app.tasks.reports.*": {"queue": "reports"},
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Istanbul",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 saat
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
)

celery_app.autodiscover_tasks(["app.tasks"]) 