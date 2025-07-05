from typing import List, Optional
from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder
from app.crud.base import CRUDBase
from app.models.instructor import Instructor
from app.schemas.instructor import InstructorCreate, InstructorUpdate

class CRUDInstructor(CRUDBase[Instructor, InstructorCreate, InstructorUpdate]):
    """Instructor CRUD operations"""
    def get_by_email(self, db: Session, *, email: str) -> Optional[Instructor]:
        """Get instructor by email"""
        return db.query(self.model).filter(Instructor.email == email).first()
    
    def get_by_role(self, db: Session, *, role: str) -> List[Instructor]:
        """Get instructors by role"""
        return db.query(self.model).filter(Instructor.role == role).all()
    
    def get_by_department(self, db: Session, *, department_id: int) -> List[Instructor]:
        """Get instructors by department"""
        return db.query(self.model).filter(Instructor.department_id == department_id).all()
    
    def get_available(self, db: Session) -> List[Instructor]:
        """Get available instructors"""
        return db.query(self.model).filter(Instructor.is_available == True).all()
    
    def get_by_project_count(self, db: Session, *, min_count: int = None, max_count: int = None) -> List[Instructor]:
        """Get instructors by project count range"""
        query = db.query(self.model)
        if min_count is not None:
            query = query.filter(Instructor.project_count >= min_count)
        if max_count is not None:
            query = query.filter(Instructor.project_count <= max_count)
        return query.all()

    def create_with_projects(
        self, db: Session, *, obj_in: InstructorCreate, project_ids: List[int]
    ) -> Instructor:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        if project_ids:
            for project_id in project_ids:
                project = db.query(Project).filter(Project.id == project_id).first()
                if project:
                    db_obj.projects.append(project)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

crud_instructor = CRUDInstructor(Instructor) 