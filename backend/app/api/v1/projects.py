from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus
from app.models.instructor import Instructor
from app.schemas.project import ProjectCreate, ProjectUpdate, Project as ProjectSchema

router = APIRouter()

def check_admin_access(current_user: User):
    """Admin yetkisi kontrolü"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action"
        )

@router.post("/", response_model=ProjectSchema)
def create_project(
    current_user: Annotated[User, Depends(get_current_user)],
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Yeni proje oluştur"""
    check_admin_access(current_user)
    
    # Sorumlu hocanın varlığını kontrol et
    responsible_instructor = db.query(Instructor).filter(
        Instructor.id == project.responsible_instructor_id
    ).first()
    if not responsible_instructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Responsible instructor not found"
        )
    
    # Yardımcı hocaların varlığını kontrol et
    assistant_instructors = []
    for instructor_id in project.assistant_instructor_ids:
        instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
        if not instructor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assistant instructor with id {instructor_id} not found"
            )
        assistant_instructors.append(instructor)
    
    # Projeyi oluştur
    db_project = Project(
        title=project.title,
        type=project.type,
        status=project.status,
        responsible_instructor_id=project.responsible_instructor_id,
        remaining_student_count=project.remaining_student_count
    )
    
    # Yardımcı hocaları ekle
    db_project.assistant_instructors = assistant_instructors
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/", response_model=List[ProjectSchema])
def read_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: ProjectStatus | None = None
):
    """Projeleri listele"""
    query = db.query(Project)
    
    if status:
        query = query.filter(Project.status == status)
    
    projects = query.offset(skip).limit(limit).all()
    return projects

@router.get("/{project_id}", response_model=ProjectSchema)
def read_project(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Belirli bir projeyi getir"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project

@router.put("/{project_id}", response_model=ProjectSchema)
def update_project(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    project: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Proje bilgilerini güncelle"""
    check_admin_access(current_user)
    
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Temel alanları güncelle
    update_data = project.model_dump(exclude_unset=True)
    
    # Yardımcı hocaları güncelle
    if "assistant_instructor_ids" in update_data:
        assistant_instructors = []
        for instructor_id in update_data["assistant_instructor_ids"]:
            instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
            if not instructor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assistant instructor with id {instructor_id} not found"
                )
            assistant_instructors.append(instructor)
        db_project.assistant_instructors = assistant_instructors
        del update_data["assistant_instructor_ids"]
    
    # Diğer alanları güncelle
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Projeyi sil"""
    check_admin_access(current_user)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db.delete(project)
    db.commit()
    return None 