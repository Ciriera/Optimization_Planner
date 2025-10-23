"""
Planlama CRUD işlemleri
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.crud.base import CRUDBase
from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.models.project import Project

class CRUDSchedule(CRUDBase[Schedule, ScheduleCreate, ScheduleUpdate]):
    """Planlama CRUD işlemleri sınıfı"""
    
    async def create_with_validation(
        self,
        db: AsyncSession,
        *,
        obj_in: ScheduleCreate
    ) -> Schedule:
        """Çakışma kontrolü yaparak planlama oluştur"""
        # Sınıf ve zaman dilimi çakışması kontrolü
        query = select(Schedule).filter(
            Schedule.classroom_id == obj_in.classroom_id,
            Schedule.timeslot_id == obj_in.timeslot_id
        )
        result = await db.execute(query)
        existing_schedule = result.scalar_one_or_none()
        
        if existing_schedule:
            raise ValueError("Bu sınıf ve zaman dilimi için planlama mevcut")
        
        # Proje sorumlusu müsaitlik kontrolü
        # Önce projeyi al
        query = select(Project).filter(Project.id == obj_in.project_id)
        result = await db.execute(query)
        project = result.scalar_one_or_none()
        
        if project:
            # Öğretim elemanının aynı zaman diliminde başka bir planlaması var mı kontrol et
            query = select(Schedule).join(Project).filter(
                Schedule.timeslot_id == obj_in.timeslot_id,
                Project.responsible_id == project.responsible_id
            )
            result = await db.execute(query)
            instructor_schedule = result.scalar_one_or_none()
            
            if instructor_schedule:
                raise ValueError(f"Öğretim elemanı (ID: {project.responsible_id}) bu zaman diliminde müsait değil")
        
        return await super().create(db, obj_in=obj_in)
    
    async def get_by_project(
        self,
        db: AsyncSession,
        *,
        project_id: int
    ) -> Optional[Schedule]:
        """Projeye göre planlama getir"""
        query = select(Schedule).filter(Schedule.project_id == project_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_instructor(
        self,
        db: AsyncSession,
        *,
        instructor_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Schedule]:
        """Öğretim elemanına göre planlamaları getir"""
        query = select(Schedule).filter(
            Schedule.instructors.any(id=instructor_id)
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_classroom(
        self,
        db: AsyncSession,
        *,
        classroom_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Schedule]:
        """Sınıfa göre planlamaları getir"""
        query = select(Schedule).filter(Schedule.classroom_id == classroom_id).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_timeslot(
        self,
        db: AsyncSession,
        *,
        timeslot_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Schedule]:
        """Zaman dilimine göre planlamaları getir"""
        query = select(Schedule).filter(Schedule.timeslot_id == timeslot_id).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

crud_schedule = CRUDSchedule(Schedule) 