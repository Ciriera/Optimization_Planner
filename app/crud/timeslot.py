"""
Zaman dilimi CRUD işlemleri
"""
from typing import List, Optional
from datetime import time
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.timeslot import TimeSlot
from app.schemas.timeslot import TimeSlotCreate, TimeSlotUpdate

class CRUDTimeSlot(CRUDBase[TimeSlot, TimeSlotCreate, TimeSlotUpdate]):
    """Zaman dilimi CRUD işlemleri sınıfı"""
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: TimeSlotCreate
    ) -> TimeSlot:
        """Zaman dilimi oluştur"""
        db_obj = TimeSlot(
            start_time=obj_in.start_time,
            end_time=obj_in.end_time,
            is_morning=obj_in.is_morning,
            is_active=obj_in.is_active
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_by_time(
        self,
        db: AsyncSession,
        *,
        start_time: time,
        end_time: time
    ) -> Optional[TimeSlot]:
        """Başlangıç ve bitiş zamanına göre zaman dilimi getir"""
        result = await db.execute(
            select(self.model)
            .filter(
                TimeSlot.start_time == start_time,
                TimeSlot.end_time == end_time
            )
        )
        return result.scalar_one_or_none()
    
    async def get_morning_slots(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[TimeSlot]:
        """Sabah zaman dilimlerini getir (09:00-12:00)"""
        result = await db.execute(
            select(self.model)
            .filter(TimeSlot.is_morning == True)
            .order_by(TimeSlot.start_time)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_afternoon_slots(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[TimeSlot]:
        """Öğleden sonra zaman dilimlerini getir (13:00-17:00)"""
        result = await db.execute(
            select(self.model)
            .filter(TimeSlot.is_morning == False)
            .order_by(TimeSlot.start_time)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_available(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[TimeSlot]:
        """Tüm zaman dilimlerini getir"""
        result = await db.execute(
            select(self.model)
            .offset(skip)
            .limit(limit)
            .order_by(TimeSlot.start_time)
        )
        return result.scalars().all()
        
    async def get_available_slots(
        self,
        db: AsyncSession,
        *,
        classroom_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[TimeSlot]:
        """Belirli bir sınıf için müsait zaman dilimlerini getir"""
        from app.models.schedule import Schedule
        
        query = (
            select(TimeSlot)
            .join(TimeSlot.schedules)
            .filter(Schedule.classroom_id == classroom_id)
        )
        result = await db.execute(query)
        busy_slots = result.scalars().all()
        
        busy_ids = [s.id for s in busy_slots]
        
        if busy_ids:
            query = (
                select(TimeSlot)
                .filter(TimeSlot.id.notin_(busy_ids))
                .order_by(TimeSlot.start_time)
                .offset(skip)
                .limit(limit)
            )
        else:
            query = (
                select(TimeSlot)
                .order_by(TimeSlot.start_time)
                .offset(skip)
                .limit(limit)
            )
            
        result = await db.execute(query)
        return result.scalars().all()

crud_timeslot = CRUDTimeSlot(TimeSlot) 