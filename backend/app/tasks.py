from typing import Dict, Any
from datetime import datetime, timedelta
from celery import Task
from sqlalchemy.orm import Session

from app.core.celery import celery_app
from app.db.session import SessionLocal
from app.algorithms.factory import AlgorithmFactory
from app.models.algorithm import Algorithm

class AlgorithmTask(Task):
    _db = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None

@celery_app.task(base=AlgorithmTask, bind=True)
def run_algorithm(
    self,
    algorithm_run_id: int,
    algorithm_id: str,
    parameters: Dict[str, Any],
    projects: Dict[int, Dict],
    instructors: Dict[int, Dict]
) -> Dict[str, Any]:
    """Algoritma çalıştırma görevi"""
    try:
        # Algoritma kaydını getir
        algorithm_run = self.db.query(Algorithm).filter(Algorithm.id == algorithm_run_id).first()
        if not algorithm_run:
            raise ValueError(f"Algoritma kaydı bulunamadı: {algorithm_run_id}")

        # Durumu güncelle
        algorithm_run.status = "running"
        algorithm_run.started_at = datetime.utcnow()
        self.db.commit()

        # Algoritmayı oluştur ve çalıştır
        algorithm = AlgorithmFactory.create_algorithm(
            algorithm_id=algorithm_id,
            projects=projects,
            instructors=instructors,
            params=parameters
        )

        # Başlangıç zamanını kaydet
        start_time = datetime.utcnow()

        # Algoritmayı çalıştır
        result = algorithm.optimize()

        # Bitiş zamanını kaydet
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()

        # Metrikleri hesapla
        metrics = {
            "execution_time": execution_time,
            "quality": result.get("quality") or result.get("fitness") or result.get("energy"),
            "iterations": result.get("iterations", 0),
            "final_temperature": result.get("final_temperature", None)
        }

        # Sonuçları kaydet
        algorithm_run.status = "completed"
        algorithm_run.completed_at = end_time
        algorithm_run.results = result
        algorithm_run.metrics = metrics
        self.db.commit()

        return {
            "status": "success",
            "algorithm_run_id": algorithm_run_id,
            "results": result,
            "metrics": metrics
        }

    except Exception as e:
        # Hata durumunda
        if algorithm_run:
            algorithm_run.status = "failed"
            algorithm_run.error = str(e)
            algorithm_run.completed_at = datetime.utcnow()
            self.db.commit()

        return {
            "status": "error",
            "algorithm_run_id": algorithm_run_id,
            "error": str(e)
        }

@celery_app.task(base=AlgorithmTask, bind=True)
def cleanup_old_runs(self, days: int = 30) -> Dict[str, Any]:
    """Eski algoritma çalıştırma kayıtlarını temizle"""
    try:
        # X günden eski kayıtları bul
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_runs = self.db.query(Algorithm).filter(Algorithm.created_at < cutoff_date).all()

        # Kayıtları sil
        count = 0
        for run in old_runs:
            self.db.delete(run)
            count += 1

        self.db.commit()

        return {
            "status": "success",
            "deleted_count": count
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# Periyodik görevleri tanımla
@celery_app.task
def setup_periodic_tasks(sender):
    """Periyodik görevleri ayarla"""
    # Her gün gece yarısı eski sonuçları temizle
    sender.add_periodic_task(
        crontab(hour=0, minute=0),
        cleanup_old_runs.s(),
        name="cleanup_old_runs"
    ) 