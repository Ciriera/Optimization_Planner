from typing import List, Optional, Dict, Any, Union

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate


class CRUDSchedule(CRUDBase[Schedule, ScheduleCreate, ScheduleUpdate]):
    """Schedule CRUD operations"""
    def get_by_project(self, db: Session, *, project_id: int) -> Optional[Schedule]:
        """Get schedule by project"""
        return db.query(self.model).filter(Schedule.project_id == project_id).first()
    
    def get_by_classroom(self, db: Session, *, classroom_id: int) -> List[Schedule]:
        """Get schedules by classroom"""
        return db.query(self.model).filter(Schedule.classroom_id == classroom_id).all()
    
    def get_by_timeslot(self, db: Session, *, timeslot_id: int) -> List[Schedule]:
        """Get schedules by timeslot"""
        return db.query(self.model).filter(Schedule.timeslot_id == timeslot_id).all()
    
    def get_by_instructor(self, db: Session, *, instructor_id: int) -> List[Schedule]:
        """Get schedules by instructor"""
        return db.query(self.model).filter(Schedule.instructors.contains([instructor_id])).all()
    
    def check_conflict(self, db: Session, *, classroom_id: int, timeslot_id: int) -> bool:
        """Check if there is a scheduling conflict"""
        return db.query(self.model).filter(
            Schedule.classroom_id == classroom_id,
            Schedule.timeslot_id == timeslot_id
        ).first() is not None

    def get_by_classroom_and_timeslot(self, db: Session, *, classroom_id: int, timeslot_id: int) -> Optional[Schedule]:
        """Get schedule occupying given classroom and timeslot (if any)."""
        return db.query(self.model).filter(
            Schedule.classroom_id == classroom_id,
            Schedule.timeslot_id == timeslot_id
        ).first()

    def create_with_instructors(
        self, db: Session, *, obj_in: ScheduleCreate, instructor_ids: List[int]
    ) -> Schedule:
        from app.models.instructor import Instructor
        
        db_obj = super().create(db, obj_in=obj_in)
        instructors = db.query(Instructor).filter(Instructor.id.in_(instructor_ids)).all()
        db_obj.instructors = instructors
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


crud_schedule = CRUDSchedule(Schedule) 