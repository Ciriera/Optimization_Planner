from celery import Celery
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Celery'nin çalışabildiğinden emin ol
try:
    celery_app = Celery(
        "app",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=["app.tasks"]
    )

    # Celery ayarları
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,  # 1 saat
        task_soft_time_limit=3300,  # 55 dakika
        worker_max_tasks_per_child=1000,
        worker_prefetch_multiplier=1
    )

    # Periyodik görevleri yükle
    celery_app.conf.beat_schedule = {
        "cleanup-old-runs": {
            "task": "app.tasks.cleanup_old_runs",
            "schedule": 86400.0,  # Her 24 saatte bir
            "args": (30,)  # 30 günden eski kayıtları temizle
        }
    }
except Exception as e:
    logger.warning(f"Celery başlatılamadı: {e}")
    
    # Mock celery app oluştur
    class MockCelery:
        def __init__(self):
            self.control = MockControl()
            
        def task(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    
    class MockControl:
        def ping(self):
            return None
    
    celery_app = MockCelery() 