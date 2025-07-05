from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, exists
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import Session, joinedload

from app.models.schedule import Schedule
from app.models.classroom import Classroom
from app.models.timeslot import TimeSlot
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate
from app.schemas.timeslot import TimeSlotCreate, TimeSlotUpdate
from app.services.base import BaseService
from datetime import time

class ScheduleService(BaseService[Schedule, ScheduleCreate, ScheduleUpdate]):
    def __init__(self):
        super().__init__(Schedule)

    async def get_schedule_with_relations(self, db: AsyncSession, id: int) -> Optional[Schedule]:
        """İlişkili verilerle birlikte planlamayı getirme"""
        result = await db.execute(
            select(Schedule)
            .options(
                selectinload(Schedule.project),
                selectinload(Schedule.classroom),
                selectinload(Schedule.timeslot)
            )
            .filter(Schedule.id == id)
        )
        return result.scalar_one_or_none()

    async def get_classroom_schedules(self, db: AsyncSession, classroom_id: int) -> List[Schedule]:
        """Sınıfa ait planlamaları getirme"""
        result = await db.execute(
            select(Schedule)
            .filter(Schedule.classroom_id == classroom_id)
        )
        return result.scalars().all()

    async def get_timeslot_schedules(self, db: AsyncSession, timeslot_id: int) -> List[Schedule]:
        """Zaman dilimine ait planlamaları getirme"""
        result = await db.execute(
            select(Schedule)
            .filter(Schedule.timeslot_id == timeslot_id)
        )
        return result.scalars().all()

    async def check_schedule_conflict(self, db: AsyncSession, classroom_id: int, timeslot_id: int) -> bool:
        """Çakışma kontrolü"""
        result = await db.execute(
            select(Schedule)
            .filter(
                Schedule.classroom_id == classroom_id,
                Schedule.timeslot_id == timeslot_id
            )
        )
        existing = result.scalar_one_or_none()
        return existing is not None

    async def get_filtered(
        self, db: AsyncSession, skip: int = 0, limit: int = 100, is_makeup: Optional[bool] = None
    ) -> List[Schedule]:
        """
        Filtrelenmiş kayıtları getir
        """
        query = select(Schedule).options(
            selectinload(Schedule.project),
            selectinload(Schedule.classroom),
            selectinload(Schedule.timeslot),
            selectinload(Schedule.instructors)
        )
        
        if is_makeup is not None:
            query = query.join(Schedule.project).filter(Schedule.project.is_makeup == is_makeup)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def check_availability(
        self, db: AsyncSession, classroom_id: int, timeslot_id: int, exclude_id: Optional[int] = None
    ) -> bool:
        """
        Belirli bir sınıf ve zaman dilimi için çakışma kontrolü
        """
        query = select(exists().where(
            and_(
                Schedule.classroom_id == classroom_id,
                Schedule.timeslot_id == timeslot_id
            )
        ))
        
        if exclude_id:
            query = query.where(Schedule.id != exclude_id)
            
        result = await db.execute(query)
        return not result.scalar_one()  # True döndürmek kullanılabilir demek

class ClassroomService(BaseService[Classroom, ClassroomCreate, ClassroomUpdate]):
    def __init__(self):
        super().__init__(Classroom)

    async def get_available_classrooms(self, db: AsyncSession, timeslot_id: int) -> List[Classroom]:
        """Belirli bir zaman diliminde müsait sınıfları getirme"""
        result = await db.execute(
            select(Schedule.classroom_id)
            .filter(Schedule.timeslot_id == timeslot_id)
        )
        used_classroom_ids = [row[0] for row in result.all()]
        
        result = await db.execute(
            select(Classroom)
            .filter(Classroom.id.notin_(used_classroom_ids if used_classroom_ids else [0]))
        )
        return result.scalars().all()

class TimeSlotService(BaseService[TimeSlot, TimeSlotCreate, TimeSlotUpdate]):
    def __init__(self):
        super().__init__(TimeSlot)

    async def create_default_slots(self, db: AsyncSession) -> List[TimeSlot]:
        """Varsayılan zaman dilimlerini oluşturma"""
        morning_slots = [
            ("09:00", "09:30"), ("09:30", "10:00"),
            ("10:00", "10:30"), ("10:30", "11:00"),
            ("11:00", "11:30"), ("11:30", "12:00")
        ]
        
        afternoon_slots = [
            ("13:00", "13:30"), ("13:30", "14:00"),
            ("14:00", "14:30"), ("14:30", "15:00"),
            ("15:00", "15:30"), ("15:30", "16:00"),
            ("16:00", "16:30"), ("16:30", "17:00")
        ]
        
        slots = []
        for start, end in morning_slots + afternoon_slots:
            slot = TimeSlot(
                start_time=time.fromisoformat(start),
                end_time=time.fromisoformat(end)
            )
            db.add(slot)
            slots.append(slot)
        
        await db.commit()
        for slot in slots:
            await db.refresh(slot)
        
        return slots 