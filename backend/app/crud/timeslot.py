from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import time

from app.crud.base import CRUDBase
from app.models.timeslot import TimeSlot
from app.schemas.timeslot import TimeSlotCreate, TimeSlotUpdate


class CRUDTimeSlot(CRUDBase[TimeSlot, TimeSlotCreate, TimeSlotUpdate]):
    """TimeSlot CRUD operations"""
    def get_by_time(self, db: Session, *, start_time: time, end_time: time) -> Optional[TimeSlot]:
        """Get timeslot by time range"""
        return (
            db.query(self.model)
            .filter(TimeSlot.start_time == start_time)
            .filter(TimeSlot.end_time == end_time)
            .first()
        )
    
    def get_morning_slots(self, db: Session) -> List[TimeSlot]:
        """Get morning timeslots"""
        return db.query(self.model).filter(TimeSlot.is_morning == True).all()
    
    def get_afternoon_slots(self, db: Session) -> List[TimeSlot]:
        """Get afternoon timeslots"""
        return db.query(self.model).filter(TimeSlot.is_morning == False).all()
    
    def get_available_slots(self, db: Session) -> List[TimeSlot]:
        """Get available timeslots"""
        return db.query(self.model).filter(TimeSlot.is_available == True).all()

crud_timeslot = CRUDTimeSlot(TimeSlot) 