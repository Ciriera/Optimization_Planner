"""
Proje CRUD işlemleri
"""
from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.project import Project, ProjectStatus, ProjectType
from app.schemas.project import ProjectCreate, ProjectUpdate

class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    """Proje CRUD işlemleri sınıfı"""
    
    def create_with_advisor(
        self, db: Session, *, obj_in: ProjectCreate, advisor_id: int
    ) -> Project:
        obj_in_data = obj_in.model_dump()
        db_obj = Project(**obj_in_data, advisor_id=advisor_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_advisor(
        self, db: Session, *, advisor_id: int, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        return (
            db.query(Project)
            .filter(Project.advisor_id == advisor_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi_by_type(
        self, db: Session, *, project_type: ProjectType, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        return (
            db.query(Project)
            .filter(Project.type == project_type)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi_by_status(
        self, db: Session, *, status: ProjectStatus, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        return (
            db.query(Project)
            .filter(Project.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_available_projects(
        self, db: Session, *, project_type: Optional[ProjectType] = None
    ) -> List[Project]:
        """Get projects that are pending assignment"""
        query = db.query(Project).filter(Project.status == ProjectStatus.PENDING)
        if project_type:
            query = query.filter(Project.type == project_type)
        return query.all()

    def assign_students(
        self, db: Session, *, project_id: int, student_ids: List[int]
    ) -> Project:
        """Assign students to a project"""
        project = self.get(db, id=project_id)
        if not project:
            return None
        
        # Update project status and student assignments
        project.status = ProjectStatus.ASSIGNED
        project.students = student_ids
        
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def get_by_type(
        self,
        db: Session,
        *,
        type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Proje tipine göre projeleri getir"""
        return (
            db.query(Project)
            .filter(Project.type == type)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_instructor(
        self,
        db: Session,
        *,
        instructor_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Öğretim elemanına göre projeleri getir"""
        return (
            db.query(Project)
            .filter(Project.responsible_id == instructor_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    async def get_makeup_projects(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Bütünleme projelerini getir"""
        query = select(Project).filter(Project.is_makeup == True).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    def get_active_projects(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Aktif projeleri getir"""
        return (
            db.query(Project)
            .filter(Project.status == "active")
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_completed_projects(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Tamamlanmış projeleri getir"""
        return (
            db.query(Project)
            .filter(Project.status == "completed")
            .offset(skip)
            .limit(limit)
            .all()
        )

    async def get_projects_by_instructor(
        self,
        db: AsyncSession,
        *,
        instructor_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Belirli bir eğitmenin projelerini getir"""
        query = select(Project).filter(Project.responsible_id == instructor_id).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_projects_by_type(
        self,
        db: AsyncSession,
        *,
        project_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Belirli bir türdeki projeleri getir"""
        query = select(Project).filter(Project.type == project_type).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_instructor(
        self,
        db: AsyncSession,
        *,
        instructor_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Belirli bir eğitmenin projelerini getir"""
        return await self.get_projects_by_instructor(db, instructor_id=instructor_id, skip=skip, limit=limit)

    async def get_by_type(
        self,
        db: AsyncSession,
        *,
        type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """Belirli bir türdeki projeleri getir"""
        return await self.get_projects_by_type(db, project_type=type, skip=skip, limit=limit)

crud_project = CRUDProject(Project) 