"""
Öğretim elemanı CRUD işlemleri
"""
from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.instructor import Instructor, InstructorType
from app.schemas.instructor import InstructorCreate, InstructorUpdate
from app.core.security import get_password_hash, verify_password

class CRUDInstructor(CRUDBase[Instructor, InstructorCreate, InstructorUpdate]):
    """Öğretim elemanı CRUD işlemleri sınıfı"""
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[Instructor]:
        """İsme göre öğretim elemanı getir"""
        return db.query(Instructor).filter(Instructor.name == name).first()
    
    def get_by_role(self, db: Session, *, role: str) -> List[Instructor]:
        """Role göre öğretim elemanlarını getir"""
        return db.query(Instructor).filter(Instructor.role == role).all()
    
    def get_available_instructors(
        self,
        db: Session,
        *,
        timeslot_id: int
    ) -> List[Instructor]:
        """Belirli bir zaman diliminde müsait öğretim elemanlarını getir"""
        from app.models.schedule import Schedule
        busy_instructors = (
            db.query(Instructor)
            .join(Instructor.schedules)
            .filter(Schedule.timeslot_id == timeslot_id)
            .all()
        )
        busy_ids = [i.id for i in busy_instructors]
        return (
            db.query(Instructor)
            .filter(Instructor.id.notin_(busy_ids))
            .all()
        )
    
    def get_by_project_count(
        self,
        db: Session,
        *,
        project_type: str,
        min_count: int = 0
    ) -> List[Instructor]:
        """Proje sayısına göre öğretim elemanlarını getir"""
        if project_type == "bitirme":
            return (
                db.query(Instructor)
                .filter(Instructor.bitirme_count >= min_count)
                .all()
            )
        return (
            db.query(Instructor)
            .filter(Instructor.ara_count >= min_count)
            .all()
        )

    async def create(self, db: AsyncSession, *, obj_in: InstructorCreate) -> Instructor:
        """Create a new instructor with proper type handling"""
        create_data = obj_in.model_dump(exclude_unset=True)
        
        # Remove password field and add hashed_password
        if "password" in create_data:
            create_data["hashed_password"] = get_password_hash(create_data.pop("password"))
        
        db_obj = Instructor(**create_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
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
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        return await super().update(db, db_obj=db_obj, obj_in=update_data)
    
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[Instructor]:
        """Get instructor by email"""
        result = await db.execute(select(Instructor).filter(Instructor.email == email))
        return result.scalar_one_or_none()
    
    async def get_by_type(self, db: AsyncSession, *, type_value: Union[str, InstructorType]) -> List[Instructor]:
        """Get instructors by type"""
        if isinstance(type_value, str):
            type_value = Instructor._convert_instructor_type(type_value)
        
        result = await db.execute(select(Instructor).filter(Instructor.type == type_value))
        return result.scalars().all()

    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> Optional[Instructor]:
        """Kullanıcı doğrulama"""
        instructor = await self.get_by_email(db, email=email)
        if not instructor:
            return None
        if not verify_password(password, instructor.hashed_password):
            return None
        return instructor

    def is_active(self, instructor: Instructor) -> bool:
        return instructor.is_active

    async def get_available_advisors(self, db: AsyncSession, *, project_type: str) -> List[Instructor]:
        """Get instructors available for advising new projects"""
        query = select(Instructor).filter(Instructor.is_active == True)
        
        if project_type == "bitirme":
            query = query.filter(Instructor.type == InstructorType.INSTRUCTOR)
        
        result = await db.execute(query)
        return result.scalars().all()

crud_instructor = CRUDInstructor(Instructor) 