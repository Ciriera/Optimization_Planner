from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.project import Project, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.base import BaseService
from app.services.instructor import InstructorService

class ProjectService(BaseService[Project, ProjectCreate, ProjectUpdate]):
    def __init__(self):
        super().__init__(Project)
        self.instructor_service = InstructorService()

    async def create_with_instructors(self, db: AsyncSession, *, obj_in: ProjectCreate) -> Project:
        """Proje ve öğretim elemanı ilişkilerini oluşturma"""
        # Proje oluştur
        db_obj = Project(
            title=obj_in.title,
            type=obj_in.type,
            is_makeup=obj_in.is_makeup,
            status=ProjectStatus.ACTIVE,
            responsible_id=obj_in.responsible_id,
            remaining_students=obj_in.remaining_students
        )
        
        # Sorumlu hocanın yükünü güncelle
        if obj_in.type == "bitirme":
            await self.instructor_service.update_load_counts(db, obj_in.responsible_id, bitirme_delta=1)
        else:
            await self.instructor_service.update_load_counts(db, obj_in.responsible_id, ara_delta=1)
        
        # Asistanları ekle
        for assistant_id in obj_in.assistant_ids:
            assistant = await self.instructor_service.get(db, assistant_id)
            if assistant:
                db_obj.assistants.append(assistant)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_with_relations(self, db: AsyncSession, id: int) -> Optional[Project]:
        """İlişkili verilerle birlikte proje getirme"""
        result = await db.execute(
            select(Project)
            .options(
                selectinload(Project.responsible_instructor),
                selectinload(Project.assistants),
                selectinload(Project.schedule)
            )
            .filter(Project.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_instructor(self, db: AsyncSession, instructor_id: int) -> List[Project]:
        """Öğretim elemanının projelerini getirme"""
        from sqlalchemy.sql.expression import or_
        result = await db.execute(
            select(Project)
            .filter(
                or_(
                    Project.responsible_id == instructor_id,
                    Project.assistants.any(id=instructor_id)
                )
            )
        )
        return result.scalars().all()

    async def mark_as_makeup(self, db: AsyncSession, id: int, remaining_students: int) -> Project:
        """Projeyi bütünleme olarak işaretleme"""
        project = await self.get(db, id)
        if project:
            project.is_makeup = True
            project.remaining_students = remaining_students
            project.status = ProjectStatus.MAKEUP
            db.add(project)
            await db.commit()
            await db.refresh(project)
        return project

    async def get_projects_by_type(self, db: AsyncSession, project_type: str, is_makeup: bool = False) -> List[Project]:
        """Türe göre projeleri getirme"""
        result = await db.execute(
            select(Project)
            .filter(Project.type == project_type)
            .filter(Project.is_makeup == is_makeup)
        )
        return result.scalars().all() 