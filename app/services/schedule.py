from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, exists
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import Session, joinedload

from app.models.schedule import Schedule
from app.models.project import Project
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
    ) -> List[Dict[str, Any]]:
        """
        Filtrelenmiş kayıtları getir ve dict formatında döndür - RAW SQL VERSION
        """
        # Raw SQL ile basit çözüm
        from sqlalchemy import text
        
        sql = """
            SELECT s.id, s.project_id, s.classroom_id, s.timeslot_id, s.is_makeup, s.instructors,
                   p.title, p.description, p.type, p.status, p.student_capacity, 
                   p.responsible_instructor_id, p.advisor_id, p.co_advisor_id, 
                   p.is_makeup as project_is_makeup, p.is_active,
                   c.name as classroom_name, c.capacity, c.location, c.is_active as classroom_is_active,
                   t.start_time, t.end_time, t.session_type, t.is_morning, t.is_active as timeslot_is_active
            FROM schedules s
            LEFT JOIN projects p ON s.project_id = p.id
            LEFT JOIN classrooms c ON s.classroom_id = c.id
            LEFT JOIN timeslots t ON s.timeslot_id = t.id
        """
        
        if is_makeup is not None:
            sql += f" WHERE p.is_makeup = {is_makeup}"
        
        sql += f" ORDER BY s.id LIMIT {limit} OFFSET {skip}"
        
        result = await db.execute(text(sql))
        rows = result.fetchall()
        
        # Her proje için jüri üyelerini al
        project_ids = [row.project_id for row in rows if row.project_id]
        jury_data = {}
        
        if project_ids:
            jury_sql = """
                SELECT pa.project_id, i.id, i.name, i.type
                FROM project_assistants pa
                JOIN instructors i ON pa.instructor_id = i.id
                WHERE pa.project_id = ANY(:project_ids)
            """
            jury_result = await db.execute(text(jury_sql), {"project_ids": project_ids})
            jury_rows = jury_result.fetchall()
            
            for jury_row in jury_rows:
                project_id = jury_row.project_id
                if project_id not in jury_data:
                    jury_data[project_id] = []
                jury_data[project_id].append({
                    "id": jury_row.id,
                    "name": jury_row.name,
                    "type": jury_row.type
                })
        
        # Instructor detaylarını al (schedule.instructors array'inden)
        # Placeholder'ları da dahil et (mixed format: [id1, id2, {"id": -1, "name": "...", "is_placeholder": true}])
        all_instructor_ids = set()
        
        for row in rows:
            if row.instructors and isinstance(row.instructors, list):
                for inst_item in row.instructors:
                    # Placeholder kontrolü: dict formatında ve is_placeholder = true ise - direkt row.instructors içinde işlenecek
                    if isinstance(inst_item, int):
                        # Gerçek instructor ID'si
                        all_instructor_ids.add(inst_item)
        
        instructor_details = {}
        if all_instructor_ids:
            instructor_sql = """
                SELECT id, name, type
                FROM instructors
                WHERE id = ANY(:instructor_ids)
            """
            instructor_result = await db.execute(text(instructor_sql), {"instructor_ids": list(all_instructor_ids)})
            instructor_rows = instructor_result.fetchall()
            
            for inst_row in instructor_rows:
                instructor_details[inst_row.id] = {
                    "id": inst_row.id,
                    "name": inst_row.name,
                    "full_name": inst_row.name,  # Frontend compatibility
                    "type": inst_row.type,
                    "role": "hoca" if inst_row.type == "instructor" else "asistan"  # Frontend compatibility
                }
        
        # Raw SQL sonuçlarını dict'e çevir
        schedule_dicts = []
        for row in rows:
            project_jury = jury_data.get(row.project_id, []) if row.project_id else []
            
            # Schedule'dan gelen instructors array'i ile instructor detaylarını birleştir
            schedule_instructors = []
            
            # First, add the responsible instructor
            if row.responsible_instructor_id and row.responsible_instructor_id in instructor_details:
                responsible_instructor = instructor_details[row.responsible_instructor_id].copy()
                responsible_instructor['role'] = 'responsible'  # Mark as responsible
                schedule_instructors.append(responsible_instructor)
            
            # Then, add the jury members from schedule.instructors (excluding responsible instructor)
            # Placeholder'ları da dahil et
            # DEBUG: Log instructors array
            if row.instructors and isinstance(row.instructors, list):
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Schedule {row.id}: Processing {len(row.instructors)} instructors: {row.instructors}")
                for inst_item in row.instructors:
                    # Placeholder kontrolü
                    if isinstance(inst_item, dict) and inst_item.get('is_placeholder', False):
                        # Placeholder'ı jury olarak ekle
                        placeholder_member = {
                            "id": inst_item.get('id', -1),
                            "name": inst_item.get('name', '[Araştırma Görevlisi]'),
                            "full_name": inst_item.get('name', '[Araştırma Görevlisi]'),
                            "type": "assistant",
                            "role": "jury",
                            "is_placeholder": True
                        }
                        schedule_instructors.append(placeholder_member)
                    elif isinstance(inst_item, int):
                        # Gerçek instructor ID'si (int formatında)
                        inst_id = inst_item
                        # Skip if this is the responsible instructor (avoid duplication)
                        if inst_id != row.responsible_instructor_id and inst_id in instructor_details:
                            jury_member = instructor_details[inst_id].copy()
                            jury_member['role'] = 'jury'  # Mark as jury
                            schedule_instructors.append(jury_member)
                        elif inst_id != row.responsible_instructor_id:
                            # Instructor details'te bulunamadı - fallback olarak ID ile oluştur
                            logger.warning(f"Instructor {inst_id} not found in instructor_details but marked as jury for project {row.project_id}")
                            schedule_instructors.append({
                                "id": inst_id,
                                "name": f"Instructor {inst_id}",
                                "full_name": f"Instructor {inst_id}",
                                "type": "instructor",
                                "role": "jury"
                            })
                    elif isinstance(inst_item, str):
                        # String formatında placeholder olabilir (Phase 2/3'ten gelen)
                        if inst_item == '[Araştırma Görevlisi]':
                            placeholder_member = {
                                "id": -1,
                                "name": '[Araştırma Görevlisi]',
                                "full_name": '[Araştırma Görevlisi]',
                                "type": "assistant",
                                "role": "jury",
                                "is_placeholder": True
                            }
                            schedule_instructors.append(placeholder_member)
                    elif isinstance(inst_item, dict):
                        # Dict formatında instructor (CP-SAT normalize etmiş veya Phase 2'den gelmiş)
                        inst_id = inst_item.get('id')
                        # Placeholder kontrolü (zaten yukarıda kontrol edildi ama tekrar kontrol)
                        if inst_item.get('is_placeholder', False):
                            # Placeholder'ı jury olarak ekle
                            placeholder_member = {
                                "id": inst_item.get('id', -1),
                                "name": inst_item.get('name', '[Araştırma Görevlisi]'),
                                "full_name": inst_item.get('full_name', inst_item.get('name', '[Araştırma Görevlisi]')),
                                "type": inst_item.get('type', 'assistant'),
                                "role": "jury",
                                "is_placeholder": True
                            }
                            schedule_instructors.append(placeholder_member)
                        elif inst_id and inst_id != row.responsible_instructor_id:
                            # KRİTİK DÜZELTME: CP-SAT normalize etmiş object'i direkt kullan
                            # Eğer object'te zaten name/full_name varsa onları kullan, lookup'a gerek yok!
                            if inst_item.get('name') and inst_item.get('full_name'):
                                # CP-SAT'in normalize ettiği object - direkt kullan
                                jury_member = inst_item.copy()
                                jury_member['role'] = 'jury'  # Mark as jury
                                schedule_instructors.append(jury_member)
                                logger.debug(f"Using normalized instructor object for {inst_id}: {inst_item.get('name')}")
                            elif inst_id in instructor_details:
                                # Fallback: instructor_details'ten lookup
                                jury_member = instructor_details[inst_id].copy()
                                jury_member['role'] = 'jury'  # Mark as jury
                                schedule_instructors.append(jury_member)
                            else:
                                # Fallback: Object'teki bilgileri kullan veya default oluştur
                                schedule_instructors.append({
                                    "id": inst_id,
                                    "name": inst_item.get('name', f"Instructor {inst_id}"),
                                    "full_name": inst_item.get('full_name', inst_item.get('name', f"Instructor {inst_id}")),
                                    "type": inst_item.get('type', 'instructor'),
                                    "role": "jury"
                                })
                                logger.warning(f"Instructor {inst_id} (dict) not found in instructor_details, using object data for project {row.project_id}")
            
            # DEBUG: Final instructors count
            logger.debug(f"Schedule {row.id}: Final schedule_instructors count: {len(schedule_instructors)}, Jury count: {len([i for i in schedule_instructors if i.get('role') == 'jury'])}")
            
            schedule_dict = {
                "id": row.id,
                "project_id": row.project_id,
                "classroom_id": row.classroom_id,
                "timeslot_id": row.timeslot_id,
                "is_makeup": row.is_makeup,
                "instructors": schedule_instructors,  # Jüri üyeleri (schedule'dan)
                "project": {
                    "id": row.project_id,
                    "title": row.title,
                    "description": row.description,
                    "type": row.type,
                    "project_type": row.type,  # Frontend compatibility
                    "status": row.status,
                    "student_capacity": row.student_capacity,
                    "responsible_id": row.responsible_instructor_id,
                    "responsible_instructor_id": row.responsible_instructor_id,  # Frontend compatibility
                    "advisor_id": row.advisor_id,
                    "co_advisor_id": row.co_advisor_id,
                    "is_makeup": row.project_is_makeup,
                    "is_active": row.is_active,
                    "assistant_instructors": project_jury,  # Jüri üyeleri eklendi
                } if row.project_id else None,
                "classroom": {
                    "id": row.classroom_id,
                    "name": row.classroom_name,
                    "capacity": row.capacity,
                    "location": row.location,
                    "is_active": row.classroom_is_active,
                } if row.classroom_id else None,
                "timeslot": {
                    "id": row.timeslot_id,
                    "start_time": str(row.start_time)[:5] if row.start_time else None,  # HH:MM format
                    "end_time": str(row.end_time)[:5] if row.end_time else None,  # HH:MM format
                    "time_range": f"{str(row.start_time)[:5]}-{str(row.end_time)[:5]}" if row.start_time and row.end_time else None,
                    "session_type": row.session_type,
                    "is_morning": row.is_morning,
                    "is_active": row.timeslot_is_active,
                } if row.timeslot_id else None,
            }
            schedule_dicts.append(schedule_dict)

        return schedule_dicts
    
    def _get_assistant_instructors_for_project(self, project) -> List[Dict[str, Any]]:
        """
        Proje için assistant instructor bilgilerini getir
        """
        try:
            if not project:
                return []
            
            assistants = []
            
            # project_assistants ilişkisinden assistant'ları al
            if hasattr(project, 'assistants') and project.assistants:
                for assistant in project.assistants:
                    if assistant and hasattr(assistant, 'id'):
                        assistants.append({
                            "id": assistant.id,
                            "name": getattr(assistant, 'name', f'Hoca {assistant.id}'),
                            "full_name": getattr(assistant, 'full_name', getattr(assistant, 'name', f'Hoca {assistant.id}')),
                            "role": "hoca" if getattr(assistant, 'type', 'instructor') == 'instructor' else "arastirma_gorevlisi",
                            "department": getattr(assistant, 'department', 'Bölüm Yok')
                        })
            
            # advisor_id ve co_advisor_id varsa onları da ekle
            if hasattr(project, 'advisor_id') and project.advisor_id:
                # Bu ID'ye sahip instructor'ı bulmak için database query gerekir
                # Şimdilik ID'yi ekleyelim, frontend'de isim çözümlemesi yapılacak
                assistants.append({
                    "id": project.advisor_id,
                    "name": f"Hoca {project.advisor_id}",
                    "full_name": f"Hoca {project.advisor_id}",
                    "role": "hoca",
                    "department": "Bölüm Yok"
                })
            
            if hasattr(project, 'co_advisor_id') and project.co_advisor_id:
                assistants.append({
                    "id": project.co_advisor_id,
                    "name": f"Hoca {project.co_advisor_id}",
                    "full_name": f"Hoca {project.co_advisor_id}",
                    "role": "hoca",
                    "department": "Bölüm Yok"
                })
            
            return assistants
            
        except Exception as e:
            print(f"Error getting assistant instructors: {e}")
            return []
    
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