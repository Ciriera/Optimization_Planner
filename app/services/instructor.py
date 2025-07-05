from typing import List, Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, join
from sqlalchemy.orm import selectinload
import numpy as np
from datetime import date, datetime, time

from app.models.instructor import Instructor, InstructorType
from app.models.project import Project
from app.models.schedule import Schedule
from app.models.timeslot import TimeSlot
from app.models.classroom import Classroom
from app.schemas.instructor import InstructorCreate, InstructorUpdate
from app.schemas.availability import TimeSlotInfo, InstructorAvailability
from app.services.base import BaseService

class InstructorService(BaseService[Instructor, InstructorCreate, InstructorUpdate]):
    def __init__(self):
        super().__init__(Instructor)

    async def create(self, db: AsyncSession, *, obj_in: InstructorCreate) -> Instructor:
        """Create a new instructor with proper field mapping"""
        try:
            # Get data from schema
            create_data = obj_in.model_dump()
            print(f"Original create data: {create_data}")
            
            # Map fields from schema to model
            # The model uses name and type
            mapped_data = {}
            
            # Map name field
            if "name" in create_data:
                mapped_data["name"] = create_data["name"]
            elif "full_name" in create_data:
                mapped_data["name"] = create_data["full_name"]
                
            # Map type field
            if "type" in create_data:
                mapped_data["type"] = create_data["type"]
            elif "role" in create_data:
                # Convert role to type for backwards compatibility
                role_to_type = {
                    "instructor": "instructor",
                    "assistant": "assistant",
                    "professor": "instructor",
                    "research_assistant": "assistant",
                    "hoca": "instructor",
                    "aras_gor": "assistant"
                }
                mapped_data["type"] = role_to_type.get(create_data["role"], "instructor")
            
            # Map other fields
            for field in ["bitirme_count", "ara_count", "total_load", "department", "user_id"]:
                if field in create_data:
                    mapped_data[field] = create_data[field]
            
            print(f"Mapped data for Instructor creation: {mapped_data}")
            
            # Create the instructor object
            db_obj = Instructor(**mapped_data)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            import traceback
            print(f"Error creating instructor: {str(e)}")
            traceback.print_exc()
            await db.rollback()
            raise

    async def update(
        self, db: AsyncSession, *, db_obj: Instructor, obj_in: Union[InstructorUpdate, Dict[str, Any]]
    ) -> Instructor:
        """Update instructor with proper type handling"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        # Handle password update
        if "password" in update_data:
            from app.core.security import get_password_hash
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> Optional[Instructor]:
        """Kullanıcı ID'sine göre öğretim elemanı getirme"""
        result = await db.execute(select(Instructor).filter(Instructor.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_instructors_by_type(self, db: AsyncSession, type_value: str) -> List[Instructor]:
        """Type göre öğretim elemanlarını getirme"""
        result = await db.execute(select(Instructor).filter(Instructor.type == type_value))
        return result.scalars().all()

    async def update_load_counts(self, db: AsyncSession, instructor_id: int, bitirme_delta: int = 0, ara_delta: int = 0) -> Instructor:
        """Proje yükü sayılarını güncelleme"""
        instructor = await self.get(db, instructor_id)
        if instructor:
            instructor.bitirme_count += bitirme_delta
            instructor.ara_count += ara_delta
            instructor.total_load = instructor.bitirme_count + instructor.ara_count
            db.add(instructor)
            await db.commit()
            await db.refresh(instructor)
        return instructor

    async def get_available_instructors(self, db: AsyncSession, project_type: str) -> List[Instructor]:
        """Uygun öğretim elemanlarını getirme"""
        query = select(Instructor)
        if project_type == "bitirme":
            # Bitirme projeleri için en az 2 hoca gerekiyor
            query = query.filter(Instructor.type == InstructorType.INSTRUCTOR.value)
        result = await db.execute(query)
        return result.scalars().all()

    async def calculate_load_distribution(self, db: AsyncSession) -> Dict[str, Any]:
        """Yük dağılımı istatistiklerini hesaplama"""
        instructors = await self.get_multi(db)
        total_loads = [i.total_load for i in instructors]
        
        if not total_loads:
            return {
                "min_load": 0,
                "max_load": 0,
                "avg_load": 0,
                "std_dev": 0
            }

        return {
            "min_load": min(total_loads),
            "max_load": max(total_loads),
            "avg_load": float(np.mean(total_loads)),
            "std_dev": float(np.std(total_loads))
        }

    async def get_availability(self, db: AsyncSession, instructor_id: int, date: date) -> InstructorAvailability:
        """Öğretim elemanının belirli bir tarihteki müsaitlik durumunu getir"""
        try:
            # Öğretim elemanının projelerini al
            query = select(Project).filter(Project.responsible_id == instructor_id)
            result = await db.execute(query)
            projects = result.scalars().all()
            
            # Projelerin planlamalarını al
            project_ids = [p.id for p in projects]
            
            # Eğer proje yoksa boş bir müsaitlik listesi döndür
            if not project_ids:
                return InstructorAvailability(
                    instructor_id=instructor_id,
                    date=str(date),
                    busy_slots=[],
                    available_slots=[]
                )
            
            # Tüm zaman dilimlerini al
            query = select(TimeSlot)
            result = await db.execute(query)
            all_timeslots = result.scalars().all()
            
            # Öğretim elemanının meşgul olduğu zaman dilimlerini al
            query = select(Schedule).join(Project).filter(
                Project.responsible_id == instructor_id,
                Schedule.project_id.in_(project_ids)
            )
            result = await db.execute(query)
            schedules = result.scalars().all()
            
            # Meşgul zaman dilimlerinin ID'lerini al
            busy_slot_ids = [s.timeslot_id for s in schedules]
            
            # Müsait ve meşgul zaman dilimlerini ayır
            busy_slots = []
            available_slots = []
            
            for slot in all_timeslots:
                slot_info = TimeSlotInfo(
                    id=slot.id,
                    start_time=str(slot.start_time),
                    end_time=str(slot.end_time),
                    is_morning=slot.is_morning
                )
                
                if slot.id in busy_slot_ids:
                    busy_slots.append(slot_info)
                else:
                    available_slots.append(slot_info)
            
            return InstructorAvailability(
                instructor_id=instructor_id,
                date=str(date),
                busy_slots=busy_slots,
                available_slots=available_slots
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

    async def get_projects(self, db: AsyncSession, instructor_id: int) -> List[Dict[str, Any]]:
        """Öğretim elemanının projelerini getir"""
        # Öğretim elemanının projelerini al
        query = select(Project).filter(Project.responsible_id == instructor_id)
        result = await db.execute(query)
        projects = result.scalars().all()
        
        # Projeleri formatlayarak döndür
        return [
            {
                "id": p.id,
                "title": p.title,
                "type": p.type,
                "status": p.status,
                "is_active": p.is_active
            }
            for p in projects
        ]

    async def get_schedule(self, db: AsyncSession, instructor_id: int) -> List[Dict[str, Any]]:
        """Öğretim elemanının planlamasını getir"""
        # Öğretim elemanının projelerini al
        query = select(Project).filter(Project.responsible_id == instructor_id)
        result = await db.execute(query)
        projects = result.scalars().all()
        
        # Projelerin ID'lerini al
        project_ids = [p.id for p in projects]
        
        # Eğer proje yoksa boş bir liste döndür
        if not project_ids:
            return []
        
        # Projelerin planlamalarını al
        query = select(Schedule).filter(Schedule.project_id.in_(project_ids))
        result = await db.execute(query)
        schedules = result.scalars().all()
        
        # Planlamaları formatlayarak döndür
        schedule_list = []
        for schedule in schedules:
            project = await db.get(Project, schedule.project_id)
            timeslot = await db.get(TimeSlot, schedule.timeslot_id)
            classroom = await db.get(Classroom, schedule.classroom_id)
            
            schedule_list.append({
                "id": schedule.id,
                "project": {
                    "id": project.id,
                    "title": project.title,
                    "type": project.type
                },
                "timeslot": {
                    "id": timeslot.id,
                    "start_time": str(timeslot.start_time),
                    "end_time": str(timeslot.end_time)
                },
                "classroom": {
                    "id": classroom.id,
                    "name": classroom.name
                },
                "is_makeup": schedule.is_makeup
            })
        
        return schedule_list 