from typing import List, Optional
from sqlalchemy.orm import Session

from fastapi.encoders import jsonable_encoder
from app.crud.base import CRUDBase
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate

class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    """Project CRUD operations"""
    def get_by_responsible(self, db: Session, *, responsible_id: int) -> List[Project]:
        """Get projects by responsible instructor"""
        return db.query(self.model).filter(Project.responsible_id == responsible_id).all()
    
    def get_by_assistant(self, db: Session, *, assistant_id: int) -> List[Project]:
        """Get projects by assistant"""
        return db.query(self.model).filter(Project.assistants.contains([assistant_id])).all()
    
    def get_by_type(self, db: Session, *, project_type: str) -> List[Project]:
        """Get projects by type (final/interim)"""
        return db.query(self.model).filter(Project.type == project_type).all()
    
    def get_by_status(self, db: Session, *, status: str) -> List[Project]:
        """Get projects by status"""
        return db.query(self.model).filter(Project.status == status).all()
    
    def get_unassigned(self, db: Session) -> List[Project]:
        """Get projects without schedule assignment"""
        return db.query(self.model).filter(Project.schedule == None).all()
    
    def get_by_instructor(self, db: Session, *, instructor_id: int) -> List[Project]:
        """Get all projects where instructor is either responsible or assistant"""
        return (
            db.query(self.model)
            .filter(
                (Project.responsible_id == instructor_id) |
                (Project.assistants.contains([instructor_id]))
            )
            .all()
        )

    def create_with_instructors(
        self, db: Session, *, obj_in: ProjectCreate, assistant_instructor_ids: List[int]
    ) -> Project:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        if assistant_instructor_ids:
            for instructor_id in assistant_instructor_ids:
                instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
                if instructor:
                    db_obj.assistant_instructors.append(instructor)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

crud_project = CRUDProject(Project) 