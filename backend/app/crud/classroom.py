from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.classroom import Classroom
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate


class CRUDClassroom(CRUDBase[Classroom, ClassroomCreate, ClassroomUpdate]):
    """Classroom CRUD operations"""
    def get_by_name(self, db: Session, *, name: str) -> Optional[Classroom]:
        """Get classroom by name"""
        return db.query(self.model).filter(Classroom.name == name).first()
    
    def get_available(self, db: Session) -> List[Classroom]:
        """Get available classrooms"""
        return db.query(self.model).filter(Classroom.is_active == True).all()
    
    def get_by_capacity(self, db: Session, *, min_capacity: int = None, max_capacity: int = None) -> List[Classroom]:
        """Get classrooms by capacity range"""
        query = db.query(self.model)
        if min_capacity is not None:
            query = query.filter(Classroom.capacity >= min_capacity)
        if max_capacity is not None:
            query = query.filter(Classroom.capacity <= max_capacity)
        return query.all()

crud_classroom = CRUDClassroom(Classroom) 