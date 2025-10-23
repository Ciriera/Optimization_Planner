from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.algorithm import Algorithm, AlgorithmType
from app.schemas.algorithm import AlgorithmCreate, AlgorithmUpdate

class CRUDAlgorithm(CRUDBase[Algorithm, AlgorithmCreate, AlgorithmUpdate]):
    """Algorithm CRUD operations"""
    def get_by_type(self, db: Session, *, algorithm_type: AlgorithmType) -> List[Algorithm]:
        """Get algorithms by type"""
        return db.query(self.model).filter(Algorithm.type == algorithm_type).all()
    
    def get_best_performing(self, db: Session, *, limit: int = 5) -> List[Algorithm]:
        """Get best performing algorithms by score"""
        return db.query(self.model).order_by(Algorithm.score.desc()).limit(limit).all()
    
    def get_fastest(self, db: Session, *, limit: int = 5) -> List[Algorithm]:
        """Get fastest algorithms by execution time"""
        return db.query(self.model).order_by(Algorithm.execution_time).limit(limit).all()

crud_algorithm = CRUDAlgorithm(Algorithm) 