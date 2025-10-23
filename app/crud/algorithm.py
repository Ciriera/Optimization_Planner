"""
Algoritma CRUD işlemleri
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.algorithm import AlgorithmRun
from app.schemas.algorithm import AlgorithmRunCreate, AlgorithmRunUpdate

class CRUDAlgorithm(CRUDBase[AlgorithmRun, AlgorithmRunCreate, AlgorithmRunUpdate]):
    """Algoritma CRUD işlemleri sınıfı"""
    
    def get_by_algorithm(
        self,
        db: Session,
        *,
        algorithm: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AlgorithmRun]:
        """Algoritma adına göre çalıştırmaları getir"""
        return (
            db.query(AlgorithmRun)
            .filter(AlgorithmRun.algorithm == algorithm)
            .order_by(AlgorithmRun.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_date_range(
        self,
        db: Session,
        *,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[AlgorithmRun]:
        """Tarih aralığına göre çalıştırmaları getir"""
        return (
            db.query(AlgorithmRun)
            .filter(
                AlgorithmRun.timestamp.between(start_date, end_date)
            )
            .order_by(AlgorithmRun.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_score_range(
        self,
        db: Session,
        *,
        min_score: float,
        max_score: float,
        skip: int = 0,
        limit: int = 100
    ) -> List[AlgorithmRun]:
        """Skor aralığına göre çalıştırmaları getir"""
        return (
            db.query(AlgorithmRun)
            .filter(
                AlgorithmRun.score.between(min_score, max_score)
            )
            .order_by(AlgorithmRun.score.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_best_run(
        self,
        db: Session,
        *,
        algorithm: Optional[str] = None
    ) -> Optional[AlgorithmRun]:
        """En yüksek skorlu çalıştırmayı getir"""
        query = db.query(AlgorithmRun)
        if algorithm:
            query = query.filter(AlgorithmRun.algorithm == algorithm)
        return query.order_by(AlgorithmRun.score.desc()).first()
    
    def get_latest_run(
        self,
        db: Session,
        *,
        algorithm: Optional[str] = None
    ) -> Optional[AlgorithmRun]:
        """En son çalıştırmayı getir"""
        query = db.query(AlgorithmRun)
        if algorithm:
            query = query.filter(AlgorithmRun.algorithm == algorithm)
        return query.order_by(AlgorithmRun.timestamp.desc()).first()

crud_algorithm = CRUDAlgorithm(AlgorithmRun) 