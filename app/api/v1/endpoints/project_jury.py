from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from sqlalchemy.orm import selectinload

from app import models
from app.api import deps
from app.db.base import get_db
from app.models.project import project_assistants
from app.i18n import translate as _

router = APIRouter()

@router.post("/{project_id}/jury", response_model=Dict[str, Any])
async def assign_jury_to_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: int,
    jury_in: Dict[str, Any],
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Projeye jüri üyelerini ata
    """
    try:
        # Projeyi kontrol et
        stmt = select(models.Project).where(models.Project.id == project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_("project.not_found", locale=current_user.language)
            )
        
        # Jüri üyelerini kontrol et
        jury_member_ids = jury_in.get("jury_member_ids", [])
        if not isinstance(jury_member_ids, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="jury_member_ids must be a list"
            )
        
        # Instructor'ları kontrol et
        if jury_member_ids:
            stmt = select(models.Instructor).where(models.Instructor.id.in_(jury_member_ids))
            result = await db.execute(stmt)
            instructors = result.scalars().all()
            
            if len(instructors) != len(jury_member_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Some jury members not found"
                )
        
        # Mevcut jüri üyelerini sil
        await db.execute(delete(project_assistants).where(project_assistants.c.project_id == project_id))
        
        # Yeni jüri üyelerini ekle
        if jury_member_ids:
            jury_assignments = [
                {"project_id": project_id, "instructor_id": instructor_id}
                for instructor_id in jury_member_ids
            ]
            await db.execute(insert(project_assistants), jury_assignments)
        
        await db.commit()
        
        # Güncellenmiş projeyi döndür
        stmt = select(models.Project).options(
            selectinload(models.Project.assistants)
        ).where(models.Project.id == project_id)
        result = await db.execute(stmt)
        updated_project = result.scalar_one_or_none()
        
        return {
            "project_id": project_id,
            "jury_members": [
                {
                    "id": instructor.id,
                    "name": instructor.name,
                    "type": instructor.type
                }
                for instructor in updated_project.assistants
            ],
            "message": "Jury members assigned successfully"
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning jury: {str(e)}"
        )

@router.get("/{project_id}/jury", response_model=Dict[str, Any])
async def get_project_jury(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: int,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Projenin jüri üyelerini getir
    """
    try:
        # Projeyi jüri üyeleri ile birlikte getir
        stmt = select(models.Project).options(
            selectinload(models.Project.assistants),
            selectinload(models.Project.responsible)
        ).where(models.Project.id == project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_("project.not_found", locale=current_user.language)
            )
        
        # Sorumlu öğretim üyesi
        responsible = {
            "id": project.responsible.id,
            "name": project.responsible.name,
            "type": project.responsible.type,
            "role": "responsible"
        } if project.responsible else None
        
        # Jüri üyeleri (assistant instructors)
        jury_members = [
            {
                "id": instructor.id,
                "name": instructor.name,
                "type": instructor.type,
                "role": "jury_member"
            }
            for instructor in project.assistants
        ]
        
        return {
            "project_id": project_id,
            "project_title": project.title,
            "responsible_instructor": responsible,
            "jury_members": jury_members,
            "total_jury_count": len(jury_members) + (1 if responsible else 0)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching jury: {str(e)}"
        )

@router.delete("/{project_id}/jury/{instructor_id}", response_model=Dict[str, Any])
async def remove_jury_member(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: int,
    instructor_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Projeden jüri üyesini kaldır
    """
    try:
        # Projeyi kontrol et
        stmt = select(models.Project).where(models.Project.id == project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_("project.not_found", locale=current_user.language)
            )
        
        # Jüri üyesini kaldır
        await db.execute(
            delete(project_assistants).where(
                project_assistants.c.project_id == project_id,
                project_assistants.c.instructor_id == instructor_id
            )
        )
        
        await db.commit()
        
        return {
            "project_id": project_id,
            "instructor_id": instructor_id,
            "message": "Jury member removed successfully"
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing jury member: {str(e)}"
        )

@router.post("/batch-assign-jury", response_model=Dict[str, Any])
async def batch_assign_jury(
    *,
    db: AsyncSession = Depends(get_db),
    assignments: Dict[str, Any],
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Birden fazla projeye toplu jüri ataması yap
    """
    try:
        project_assignments = assignments.get("project_assignments", [])
        
        if not isinstance(project_assignments, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="project_assignments must be a list"
            )
        
        results = []
        
        for assignment in project_assignments:
            project_id = assignment.get("project_id")
            jury_member_ids = assignment.get("jury_member_ids", [])
            
            if not project_id:
                continue
            
            # Projeyi kontrol et
            stmt = select(models.Project).where(models.Project.id == project_id)
            result = await db.execute(stmt)
            project = result.scalar_one_or_none()
            
            if not project:
                results.append({
                    "project_id": project_id,
                    "status": "error",
                    "message": "Project not found"
                })
                continue
            
            # Mevcut jüri üyelerini sil
            await db.execute(delete(project_assistants).where(project_assistants.c.project_id == project_id))
            
            # Yeni jüri üyelerini ekle
            if jury_member_ids:
                jury_assignments = [
                    {"project_id": project_id, "instructor_id": instructor_id}
                    for instructor_id in jury_member_ids
                ]
                await db.execute(insert(project_assistants), jury_assignments)
            
            results.append({
                "project_id": project_id,
                "status": "success",
                "jury_count": len(jury_member_ids)
            })
        
        await db.commit()
        
        return {
            "total_processed": len(project_assignments),
            "results": results,
            "message": "Batch jury assignment completed"
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in batch assignment: {str(e)}"
        )
