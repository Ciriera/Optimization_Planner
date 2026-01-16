from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.api import deps
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

@router.get("/", response_model=List[dict])
async def read_projects(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Projeleri listele - assistant_instructors ile birlikte
    """
    try:
        from sqlalchemy import select, text
        from app.models.project import Project
        from app.models.instructor import Instructor
        from app.models.project import project_assistants
        
        # Direkt SQL query kullan (gerçek kolon adlarıyla) + assistant_instructors
        query = """
        SELECT p.id, p.title, p.description, p.type, p.status, p.student_capacity, 
               p.responsible_instructor_id, p.advisor_id, p.co_advisor_id, p.is_makeup, p.is_active,
               COALESCE(
                   json_agg(
                       json_build_object(
                           'id', ai.id,
                           'name', ai.name,
                           'type', ai.type
                       )
                   ) FILTER (WHERE ai.id IS NOT NULL),
                   '[]'::json
               ) as assistant_instructors
        FROM projects p
        LEFT JOIN project_assistants pa ON p.id = pa.project_id
        LEFT JOIN instructors ai ON pa.instructor_id = ai.id
        GROUP BY p.id, p.title, p.description, p.type, p.status, p.student_capacity, 
                 p.responsible_instructor_id, p.advisor_id, p.co_advisor_id, p.is_makeup, p.is_active
        ORDER BY p.id
        LIMIT :limit OFFSET :skip
        """
        result = await db.execute(text(query), {"limit": limit, "skip": skip})
        
        projects = []
        for row in result.fetchall():
            project = {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "type": row[3],
                "status": row[4],
                "student_capacity": row[5],
                "responsible_instructor_id": row[6],  # Frontend uyumluluğu için
                "responsible_id": row[6],  # Backend uyumluluğu için (alias)
                "advisor_id": row[7],
                "co_advisor_id": row[8],
                "is_makeup": row[9],
                "is_active": row[10],
                "assistant_instructors": row[11] if row[11] else []  # Assistant instructors listesi
            }
            projects.append(project)
        
        return projects
    except Exception as e:
        return []

@router.get("/public", response_model=List[dict])
async def read_projects_public(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Public projects endpoint for frontend dashboard - assistant_instructors ile birlikte
    """
    try:
        from sqlalchemy import text
        
        # Direkt SQL query kullan (gerçek kolon adlarıyla) + assistant_instructors
        query = """
        SELECT p.id, p.title, p.description, p.type, p.status, p.student_capacity, 
               p.responsible_instructor_id, p.advisor_id, p.co_advisor_id, p.is_makeup, p.is_active,
               COALESCE(
                   json_agg(
                       json_build_object(
                           'id', ai.id,
                           'name', ai.name,
                           'type', ai.type
                       )
                   ) FILTER (WHERE ai.id IS NOT NULL),
                   '[]'::json
               ) as assistant_instructors
        FROM projects p
        LEFT JOIN project_assistants pa ON p.id = pa.project_id
        LEFT JOIN instructors ai ON pa.instructor_id = ai.id
        GROUP BY p.id, p.title, p.description, p.type, p.status, p.student_capacity, 
                 p.responsible_instructor_id, p.advisor_id, p.co_advisor_id, p.is_makeup, p.is_active
        ORDER BY p.id
        """
        result = await db.execute(text(query))
        
        projects = []
        for row in result.fetchall():
            project = {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "type": row[3],
                "status": row[4],
                "student_capacity": row[5],
                "responsible_instructor_id": row[6],  # Frontend uyumluluğu için
                "responsible_id": row[6],  # Backend uyumluluğu için (alias)
                "advisor_id": row[7],
                "co_advisor_id": row[8],
                "is_makeup": bool(row[9]) if row[9] is not None else False,
                "is_active": bool(row[10]) if row[10] is not None else True,
                "assistant_instructors": row[11] if row[11] else []  # Assistant instructors listesi
            }
            projects.append(project)
        
        return projects
    except Exception as e:
        return []

@router.post("/", response_model=Project)
async def create_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_in: ProjectCreate,
    current_user: User = Depends(deps.get_current_user)
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
    current_user: User = Depends(deps.get_current_user)
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

@router.put("/{project_id}")
async def update_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(deps.get_current_user)
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
    # Update işlemini yap
    updated_project = await project_service.update(db, db_obj=project, obj_in=project_in)
    
    # Basit response döndür (async relationship sorunlarını önlemek için)
    return {
        "status": "success", 
        "message": "Proje güncellendi", 
        "project_id": updated_project.id,
        "responsible_id": updated_project.responsible_id
    }

@router.delete("/{project_id}", response_model=Project)
async def delete_project(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: int,
    current_user: User = Depends(deps.get_current_user)
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


@router.delete("/bulk/delete-all", status_code=status.HTTP_200_OK)
async def delete_all_projects(
    *,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Tüm projeleri ve ilişkili schedule'ları sil
    """
    try:
        from sqlalchemy import text
        
        # Get total projects count
        count_query = "SELECT COUNT(*) FROM projects"
        count_result = await db.execute(text(count_query))
        total_projects = count_result.scalar() or 0
        
        if total_projects == 0:
            return {
                "message": "Silinecek proje bulunamadı",
                "deleted_projects_count": 0,
                "deleted_schedules_count": 0
            }
        
        # Get schedules count
        schedules_count_query = "SELECT COUNT(*) FROM schedules"
        schedules_result = await db.execute(text(schedules_count_query))
        total_schedules = schedules_result.scalar() or 0
        
        # Delete all schedules first (foreign key constraint)
        await db.execute(text("DELETE FROM schedules"))
        
        # Delete all project assistants
        await db.execute(text("DELETE FROM project_assistants"))
        
        # Delete all projects
        await db.execute(text("DELETE FROM projects"))
        
        await db.commit()
        
        return {
            "message": "Tüm projeler ve schedule'lar başarıyla silindi",
            "deleted_projects_count": total_projects,
            "deleted_schedules_count": total_schedules
        }
        
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"ERROR in delete_all_projects: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Toplu silme işlemi sırasında hata oluştu: {str(e)}"
        )

@router.post("/{project_id}/makeup")
async def mark_project_as_makeup(
    *,
    db: AsyncSession = Depends(get_db),
    project_id: int,
    remaining_students: int,
    current_user: User = Depends(deps.get_current_user)
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


@router.get("/jury-structure/analysis")
async def analyze_jury_structure(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Jüri yapısını analiz eder (3 kişilik jüri yapısı kontrolü).
    """
    try:
        from app.services.jury_structure_service import JuryStructureService
        
        jury_service = JuryStructureService()
        analysis = await jury_service.analyze_jury_structure(db)
        
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing jury structure: {str(e)}"
        )


@router.post("/jury-structure/fix")
async def fix_jury_structure(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Jüri yapısını düzeltir (3 kişilik jüri yapısını sağlar).
    """
    try:
        from app.services.jury_structure_service import JuryStructureService
        
        jury_service = JuryStructureService()
        result = await jury_service.fix_jury_structure(db)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fixing jury structure: {str(e)}"
        )


@router.post("/jury-structure/cleanup-conflicts")
async def cleanup_jury_conflicts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Sorumlu hocanın aynı projede jüri/assistant olarak yer almasını engelleyen
    otomatik temizlik işlemi. Tüm projeleri tarar ve temizler.
    """
    try:
        result = await project_service.cleanup_jury_conflicts(db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up jury conflicts: {str(e)}"
        )

@router.post("/reconcile-instructors")
async def reconcile_instructors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Instructor tablosunda olmayan referansları temizler; istenirse en az yüklü
    hocaya yeniden atar. Ayrıca geçersiz assistant linklerini kaldırır.
    """
    try:
        result = await project_service.reconcile_instructor_references(db, reassign_missing=True)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reconciling instructors: {str(e)}"
        )

@router.get("/jury-structure/summary")
async def get_jury_structure_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Jüri yapısı özetini getirir.
    """
    try:
        from app.services.jury_structure_service import JuryStructureService
        
        jury_service = JuryStructureService()
        summary = await jury_service.get_jury_structure_summary(db)
        
        if not summary.get("success", True):  # success field yoksa True kabul et
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=summary["message"]
            )
        
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting jury structure summary: {str(e)}"
        ) 