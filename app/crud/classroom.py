"""
Sınıf CRUD işlemleri
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.classroom import Classroom
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate

class CRUDClassroom(CRUDBase[Classroom, ClassroomCreate, ClassroomUpdate]):
    """Sınıf CRUD işlemleri sınıfı"""
    
    def get_by_name(
        self,
        db: Session,
        *,
        name: str
    ) -> Optional[Classroom]:
        """İsme göre sınıf getir"""
        return db.query(Classroom).filter(Classroom.name == name).first()
    
    def get_by_location(
        self,
        db: Session,
        *,
        location: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Classroom]:
        """Konuma göre sınıfları getir"""
        return (
            db.query(Classroom)
            .filter(Classroom.location == location)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_capacity(
        self,
        db: Session,
        *,
        min_capacity: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Classroom]:
        """Minimum kapasiteye göre sınıfları getir"""
        return (
            db.query(Classroom)
            .filter(Classroom.capacity >= min_capacity)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_available_classrooms(
        self,
        db: Session,
        *,
        timeslot_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Classroom]:
        """Belirli bir zaman diliminde müsait sınıfları getir"""
        busy_classrooms = (
            db.query(Classroom)
            .join(Classroom.schedules)
            .filter(Schedule.timeslot_id == timeslot_id)
            .all()
        )
        busy_ids = [c.id for c in busy_classrooms]
        return (
            db.query(Classroom)
            .filter(Classroom.id.notin_(busy_ids))
            .offset(skip)
            .limit(limit)
            .all()
        )

crud_classroom = CRUDClassroom(Classroom) 