from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.services.auth import AuthService
from app.services.project import ProjectService
from app.schemas.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectWithRelations
)
from app.models.user import User, UserRole

router = APIRouter()
project_service = ProjectService()

@router.get("/", response_model=List[Project])
async def read_projects(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """
    Projeleri listele
    """
    try:
        # Basitleştirilmiş geçici çözüm
        from sqlalchemy import select
        from app.models.project import Project
        
        result = await db.execute(select(Project).offset(skip).limit(limit))
        return result.scalars().all()
    except Exception as e:
        print(f"Projects error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Projects error: {str(e)}"
        )

@router.post("/", response_model=Project)
async def create_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_in: ProjectCreate,
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """
    Yeni proje oluştur
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    return await project_service.create_with_instructors(db, obj_in=project_in)

@router.get("/{project_id}", response_model=ProjectWithRelations)
async def read_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """
    Proje detaylarını getir
    """
    project = await project_service.get_with_relations(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proje bulunamadı"
        )
    
    if current_user.role != UserRole.ADMIN:
        instructor_id = current_user.instructor_profile.id
        if (project.responsible_id != instructor_id and 
            instructor_id not in [a.id for a in project.assistants]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu projeye erişim yetkiniz yok"
            )
    return project

@router.put("/{project_id}", response_model=Project)
async def update_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """
    Proje bilgilerini güncelle
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    
    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proje bulunamadı"
        )
    project = await project_service.update(db, db_obj=project, obj_in=project_in)
    return project

@router.delete("/{project_id}", response_model=Project)
async def delete_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: int,
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """
    Projeyi sil
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    
    project = await project_service.get(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proje bulunamadı"
        )
    project = await project_service.remove(db, id=project_id)
    return project

@router.post("/{project_id}/makeup")
async def mark_project_as_makeup(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: int,
    remaining_students: int,
    current_user: User = Depends(AuthService.get_current_user)
) -> Any:
    """
    Projeyi bütünleme olarak işaretle
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    
    project = await project_service.mark_as_makeup(db, project_id, remaining_students)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proje bulunamadı"
        )
    return project 