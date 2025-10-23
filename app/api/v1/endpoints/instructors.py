from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import date

from app import schemas
from app.db.base import get_db
from app.models.user import User, UserRole
from app.api import deps
from app.schemas.availability import TimeSlotInfo, InstructorAvailability
from app.schemas.instructor import InstructorCreate, InstructorUpdate

router = APIRouter()

def check_admin_access(current_user: User = Depends(deps.get_current_user)) -> None:
    """Admin yetkisi kontrolü"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )

@router.get("/", response_model=List[Dict[str, Any]])
async def list_instructors(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Eğitmenleri listele
    """
    try:
        result = await db.execute(text("SELECT * FROM instructors"))
        instructors = result.fetchall()
        
        # Convert to list of dicts
        instructor_list = []
        for instructor in instructors:
            instructor_dict = dict(instructor._mapping)
            instructor_list.append(instructor_dict)
        
        return instructor_list
    except Exception as e:
        return []

@router.get("/public", response_model=List[Dict[str, Any]])
async def list_instructors_public(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Public instructors endpoint for frontend dashboard
    """
    try:
        result = await db.execute(text("SELECT * FROM instructors"))
        instructors = result.fetchall()
        
        # Convert to list of dicts
        instructor_list = []
        for instructor in instructors:
            instructor_dict = dict(instructor._mapping)
            instructor_list.append(instructor_dict)
        
        return instructor_list
    except Exception as e:
        return []

@router.get("/{instructor_id}/projects", response_model=List[Dict[str, Any]])
async def get_instructor_projects(
    instructor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Öğretim elemanının projelerini getir
    """
    try:
        # Check if instructor exists
        print(f"DEBUG: Looking for instructor with ID {instructor_id}")
        query = "SELECT id FROM instructors WHERE id = :instructor_id"
        result = await db.execute(text(query), {"instructor_id": instructor_id})
        instructor_exists = result.scalar_one_or_none()
        print(f"DEBUG: Instructor exists: {instructor_exists is not None}")
        
        if not instructor_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Öğretim elemanı bulunamadı"
            )
    
        # Get projects using direct SQL
        query = """
        SELECT p.id, p.title, p.type, p.status, p.is_active 
        FROM projects p 
        WHERE p.responsible_id = :instructor_id
        """
        result = await db.execute(text(query), {"instructor_id": instructor_id})
        
        projects = []
        for row in result.fetchall():
            projects.append({
                "id": row[0],
                "title": row[1],
                "type": row[2],
                "status": row[3],
                "is_active": row[4] if row[4] is not None else True
            })
        
        print(f"DEBUG: Found {len(projects)} projects for instructor {instructor_id}")
        return projects
    except Exception as e:
        import traceback
        print(f"ERROR in get_instructor_projects: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Projeler alınırken bir hata oluştu: {str(e)}"
        )

@router.get("/{instructor_id}/schedule", response_model=List[Dict[str, Any]])
async def get_instructor_schedule(
    instructor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Öğretim elemanının planlamasını getir
    """
    try:
        # Check if instructor exists
        query = "SELECT id FROM instructors WHERE id = :instructor_id"
        result = await db.execute(text(query), {"instructor_id": instructor_id})
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Öğretim elemanı bulunamadı"
            )
    
        # Return empty list for now
        return []
    except Exception as e:
        import traceback
        print(f"ERROR in get_instructor_schedule: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Planlama bilgisi alınırken bir hata oluştu: {str(e)}"
        )

@router.get("/{instructor_id}/availability", response_model=InstructorAvailability)
async def instructor_availability(
    instructor_id: int,
    date: date = Query(..., description="Tarih (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Öğretim elemanının belirli bir tarihteki müsaitlik durumunu getir
    """
    try:
        print(f"DEBUG: instructor_availability called for instructor_id={instructor_id}, date={date}")
        
        # Check if instructor exists
        query = "SELECT id FROM instructors WHERE id = :instructor_id"
        result = await db.execute(text(query), {"instructor_id": instructor_id})
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Öğretim elemanı bulunamadı"
            )
        
        # Create TimeSlotInfo objects
        busy_slot = TimeSlotInfo(
            id=1,
            start_time="09:00:00",
            end_time="10:00:00",
            is_morning=True
        )
        
        available_slots = [
            TimeSlotInfo(
                id=2,
                start_time="10:00:00",
                end_time="11:00:00",
                is_morning=True
            ),
            TimeSlotInfo(
                id=3,
                start_time="11:00:00",
                end_time="12:00:00",
                is_morning=True
            )
        ]
        
        # Create and return InstructorAvailability object
        result = InstructorAvailability(
            instructor_id=instructor_id,
            date=str(date),
            busy_slots=[busy_slot],
            available_slots=available_slots
        )
        
        print(f"DEBUG: Returning availability result: {result}")
        return result
    except HTTPException as he:
        print(f"HTTP Exception in instructor_availability: {str(he)}")
        raise he
    except Exception as e:
        import traceback
        print(f"ERROR in instructor_availability: {str(e)}")
        print(f"ERROR type: {type(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Müsaitlik bilgisi alınırken bir hata oluştu: {str(e)}"
        )

@router.get("/", response_model=List[Dict[str, Any]])
async def read_instructors(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Öğretim elemanlarını listele
    """
    try:
        # Use the simplest possible approach - direct SQL query
        
        # Execute a simple SQL query to get all instructors
        query = "SELECT id, name, type, department, bitirme_count, ara_count, total_load, user_id FROM instructors LIMIT :limit OFFSET :skip"
        result = await db.execute(text(query), {"limit": limit, "skip": skip})
        
        # Convert to list of dictionaries
        instructors = []
        for row in result.fetchall():
            instructor = {
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "department": row[3],
                "bitirme_count": row[4] or 0,
                "ara_count": row[5] or 0,
                "total_load": row[6] or 0,
                "user_id": row[7]
            }
            instructors.append(instructor)
        
        print(f"DEBUG: Returning {len(instructors)} instructors")
        return instructors
    except Exception as e:
        import traceback
        print(f"ERROR in read_instructors: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Öğretim elemanları listelenirken bir hata oluştu: {str(e)}"
        )

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
async def create_instructor(
    *,
    db: AsyncSession = Depends(get_db),
    instructor_in: InstructorCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Öğretim elemanı oluştur
    """
    try:
        print(f"DEBUG: Creating instructor with data: {instructor_in.model_dump()}")
        
        # Create instructor using direct SQL for maximum reliability
        query = """
        INSERT INTO instructors (name, type, department, bitirme_count, ara_count, total_load, user_id)
        VALUES (:name, :type, :department, :bitirme_count, :ara_count, :total_load, :user_id)
        RETURNING id, name, type, department, bitirme_count, ara_count, total_load, user_id
        """
        
        # Prepare parameters
        params = {
            "name": instructor_in.name if hasattr(instructor_in, "name") and instructor_in.name else "New Instructor",
            "type": instructor_in.type if hasattr(instructor_in, "type") and instructor_in.type else "instructor",
            "department": instructor_in.department if hasattr(instructor_in, "department") and instructor_in.department else None,
            "bitirme_count": instructor_in.bitirme_count if hasattr(instructor_in, "bitirme_count") and instructor_in.bitirme_count is not None else 0,
            "ara_count": instructor_in.ara_count if hasattr(instructor_in, "ara_count") and instructor_in.ara_count is not None else 0,
            "total_load": instructor_in.total_load if hasattr(instructor_in, "total_load") and instructor_in.total_load is not None else 0,
            "user_id": instructor_in.user_id if hasattr(instructor_in, "user_id") and instructor_in.user_id is not None else None
        }
        
        print(f"DEBUG: SQL parameters: {params}")
        
        result = await db.execute(text(query), params)
        row = result.fetchone()
        await db.commit()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Öğretim elemanı oluşturulamadı"
            )
        
        # Return a dictionary directly
        instructor_dict = {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "department": row[3],
            "bitirme_count": row[4] or 0,
            "ara_count": row[5] or 0,
            "total_load": row[6] or 0,
            "user_id": row[7]
        }
        
        print(f"DEBUG: Created instructor: {instructor_dict}")
        return instructor_dict
        
    except Exception as e:
        import traceback
        print(f"ERROR in create_instructor: {str(e)}")
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Öğretim elemanı oluşturulurken bir hata oluştu: {str(e)}"
        )

@router.get("/{instructor_id}", response_model=Dict[str, Any])
async def read_instructor(
    instructor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Belirli bir öğretim elemanını getir
    """
    try:
        # Use direct SQL query for reliability
        query = """
        SELECT id, name, type, department, bitirme_count, ara_count, total_load, user_id 
        FROM instructors 
        WHERE id = :instructor_id
        """
        result = await db.execute(text(query), {"instructor_id": instructor_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Öğretim elemanı bulunamadı"
            )
        
        # Return a dictionary directly
        instructor_dict = {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "department": row[3],
            "bitirme_count": row[4] or 0,
            "ara_count": row[5] or 0,
            "total_load": row[6] or 0,
            "user_id": row[7]
        }
        
        print(f"DEBUG: Retrieved instructor: {instructor_dict}")
        return instructor_dict
        
    except Exception as e:
        import traceback
        print(f"ERROR in read_instructor: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Öğretim elemanı alınırken bir hata oluştu: {str(e)}"
        )

@router.put("/{instructor_id}", response_model=Dict[str, Any])
async def update_instructor(
    *,
    db: AsyncSession = Depends(get_db),
    instructor_id: int,
    instructor_in: InstructorUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Öğretim elemanı bilgilerini güncelle
    """
    try:
        # Check if instructor exists
        query = "SELECT id FROM instructors WHERE id = :instructor_id"
        result = await db.execute(text(query), {"instructor_id": instructor_id})
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Öğretim elemanı bulunamadı"
            )
        
        # Extract update data
        update_data = instructor_in.model_dump(exclude_unset=True)
        print(f"DEBUG: Update data: {update_data}")
        
        if not update_data:
            # If no update data, just return the current instructor
            query = """
            SELECT id, name, type, department, bitirme_count, ara_count, total_load, user_id 
            FROM instructors 
            WHERE id = :instructor_id
            """
            result = await db.execute(text(query), {"instructor_id": instructor_id})
            row = result.fetchone()
            
            instructor_dict = {
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "department": row[3],
                "bitirme_count": row[4] or 0,
                "ara_count": row[5] or 0,
                "total_load": row[6] or 0,
                "user_id": row[7]
            }
            return instructor_dict
        
        # Build SQL update statement
        set_clauses = []
        params = {"instructor_id": instructor_id}
        
        # Handle field mappings
        field_mapping = {
            "name": "name",
            "type": "type",
            "department": "department",
            "bitirme_count": "bitirme_count",
            "ara_count": "ara_count",
            "total_load": "total_load",
            "user_id": "user_id",
            # Handle legacy field names
            "final_project_count": "bitirme_count",
            "interim_project_count": "ara_count",
            "role": "type"
        }
        
        for schema_field, model_field in field_mapping.items():
            if schema_field in update_data:
                value = update_data[schema_field]
                
                # Handle type conversion for role field
                if schema_field == "role" and value:
                    role_to_type = {
                        "professor": "instructor",
                        "research_assistant": "assistant",
                        "hoca": "instructor",
                        "aras_gor": "assistant",
                        "instructor": "instructor",
                        "assistant": "assistant",
                    }
                    value = role_to_type.get(value, "instructor")
                
                set_clauses.append(f"{model_field} = :{model_field}")
                params[model_field] = value
        
        if not set_clauses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        # Execute update
        query = f"""
        UPDATE instructors 
        SET {", ".join(set_clauses)}
        WHERE id = :instructor_id
        RETURNING id, name, type, department, bitirme_count, ara_count, total_load, user_id
        """
        
        print(f"DEBUG: Update SQL: {query}")
        print(f"DEBUG: Update params: {params}")
        
        result = await db.execute(text(query), params)
        row = result.fetchone()
        await db.commit()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Öğretim elemanı güncellenemedi"
            )
        
        # Return updated instructor as dictionary
        instructor_dict = {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "department": row[3],
            "bitirme_count": row[4] or 0,
            "ara_count": row[5] or 0,
            "total_load": row[6] or 0,
            "user_id": row[7]
        }
        
        print(f"DEBUG: Updated instructor: {instructor_dict}")
        return instructor_dict
        
    except Exception as e:
        import traceback
        print(f"ERROR in update_instructor: {str(e)}")
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Öğretim elemanı güncellenirken bir hata oluştu: {str(e)}"
        )

@router.delete("/{instructor_id}", status_code=status.HTTP_200_OK, response_model=Dict[str, Any])
async def delete_instructor(
    *,
    db: AsyncSession = Depends(get_db),
    instructor_id: int,
    # Temporarily disable auth for testing
    # current_user: User = Depends(check_admin_access)
) -> Any:
    """
    Öğretim elemanını ve sorumlu olduğu projeleri sil
    """
    try:
        # Check if instructor exists
        query = "SELECT id, name FROM instructors WHERE id = :instructor_id"
        result = await db.execute(text(query), {"instructor_id": instructor_id})
        instructor_row = result.fetchone()
        
        if not instructor_row:
            # If the instructor doesn't exist, return 404
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Öğretim elemanı bulunamadı"
            )
        
        instructor_name = instructor_row[1]
        
        # Get projects that this instructor is responsible for
        projects_query = """
        SELECT id, title, type 
        FROM projects 
        WHERE responsible_instructor_id = :instructor_id
        """
        projects_result = await db.execute(text(projects_query), {"instructor_id": instructor_id})
        responsible_projects = projects_result.fetchall()
        
        # Get projects where this instructor is a jury member
        jury_projects_query = """
        SELECT DISTINCT p.id, p.title, p.type 
        FROM projects p
        JOIN project_assistants pa ON p.id = pa.project_id
        WHERE pa.instructor_id = :instructor_id
        """
        jury_result = await db.execute(text(jury_projects_query), {"instructor_id": instructor_id})
        jury_projects = jury_result.fetchall()
        
        deleted_projects_count = 0
        removed_jury_count = 0
        
        # Delete projects where instructor is responsible
        if responsible_projects:
            # First delete schedules for these projects
            for project in responsible_projects:
                project_id = project[0]
                delete_schedules_query = "DELETE FROM schedules WHERE project_id = :project_id"
                await db.execute(text(delete_schedules_query), {"project_id": project_id})
            
            # Then delete the projects
            delete_projects_query = "DELETE FROM projects WHERE responsible_instructor_id = :instructor_id"
            await db.execute(text(delete_projects_query), {"instructor_id": instructor_id})
            deleted_projects_count = len(responsible_projects)
        
        # Remove instructor from jury memberships
        if jury_projects:
            remove_jury_query = "DELETE FROM project_assistants WHERE instructor_id = :instructor_id"
            await db.execute(text(remove_jury_query), {"instructor_id": instructor_id})
            removed_jury_count = len(jury_projects)
        
        # Delete instructor
        delete_instructor_query = "DELETE FROM instructors WHERE id = :instructor_id"
        await db.execute(text(delete_instructor_query), {"instructor_id": instructor_id})
        
        await db.commit()
        
        return {
            "message": "Öğretim elemanı ve ilgili projeler başarıyla silindi",
            "instructor_name": instructor_name,
            "deleted_projects_count": deleted_projects_count,
            "removed_jury_count": removed_jury_count,
            "deleted_projects": [
                {"id": p[0], "title": p[1], "type": p[2]} 
                for p in responsible_projects
            ],
            "removed_jury_projects": [
                {"id": p[0], "title": p[1], "type": p[2]} 
                for p in jury_projects
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import traceback
        print(f"ERROR in delete_instructor: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Öğretim elemanı silinirken bir hata oluştu: {str(e)}"
        )

@router.get("/load-distribution/stats", response_model=Dict[str, Any])
async def get_load_distribution_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Öğretim elemanlarının yük dağılımı istatistiklerini getir
    """
    try:
        # Get load stats using direct SQL
        query = """
        SELECT 
            MIN(total_load) as min_load,
            MAX(total_load) as max_load,
            AVG(total_load) as avg_load,
            SQRT(AVG(POWER(total_load - (SELECT AVG(total_load) FROM instructors), 2))) as std_dev
        FROM instructors
        """
        result = await db.execute(text(query))
        row = result.fetchone()
        
        if not row:
            return {
                "min_load": 0,
                "max_load": 0,
                "avg_load": 0,
                "std_dev": 0
            }
        
        return {
            "min_load": row[0] or 0,
            "max_load": row[1] or 0,
            "avg_load": float(row[2] or 0),
            "std_dev": float(row[3] or 0)
        }
    except Exception as e:
        import traceback
        print(f"ERROR in get_load_distribution_stats: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Yük dağılımı istatistikleri alınırken bir hata oluştu: {str(e)}"
        )


@router.post("/ra-placeholders/create")
async def create_ra_placeholders(
    required_count: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Belirtilen sayıda RA placeholder oluşturur.
    """
    try:
        from app.services.ra_placeholder_service import RAPlaceholderService
        
        ra_service = RAPlaceholderService()
        placeholders = await ra_service.create_ra_placeholders(db, required_count)
        
        return {
            "message": f"Created {len(placeholders)} RA placeholders",
            "placeholders": placeholders
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating RA placeholders: {str(e)}"
        )


@router.get("/ra-placeholders/status")
async def get_ra_placeholders_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    RA placeholder'larının durumunu getirir.
    """
    try:
        from app.services.ra_placeholder_service import RAPlaceholderService
        
        ra_service = RAPlaceholderService()
        status = await ra_service.get_ra_placeholders_status(db)
        
        return status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting RA placeholders status: {str(e)}"
        )


@router.put("/ra-placeholders/{placeholder_id}/rename")
async def rename_ra_placeholder(
    placeholder_id: str,
    new_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    RA placeholder'ının ismini günceller.
    """
    try:
        from app.services.ra_placeholder_service import RAPlaceholderService
        
        ra_service = RAPlaceholderService()
        result = await ra_service.update_ra_placeholder_name(db, placeholder_id, new_name)
        
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
            detail=f"Error renaming RA placeholder: {str(e)}"
        )


@router.post("/ra-placeholders/{placeholder_id}/convert")
async def convert_placeholder_to_named_ra(
    placeholder_id: str,
    ra_name: str,
    ra_details: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Placeholder'ı gerçek RA'ya dönüştürür.
    """
    try:
        from app.services.ra_placeholder_service import RAPlaceholderService
        
        ra_service = RAPlaceholderService()
        result = await ra_service.convert_placeholder_to_named_ra(
            db, placeholder_id, ra_name, ra_details
        )
        
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
            detail=f"Error converting placeholder: {str(e)}"
        )


@router.delete("/ra-placeholders/cleanup")
async def cleanup_unused_placeholders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Kullanılmayan placeholder'ları temizler.
    """
    try:
        from app.services.ra_placeholder_service import RAPlaceholderService
        
        ra_service = RAPlaceholderService()
        result = await ra_service.cleanup_unused_placeholders(db)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up placeholders: {str(e)}"
        )


@router.post("/ra-placeholders/assign")
async def assign_ra_placeholders_to_projects(
    projects: List[Dict[str, Any]],
    available_placeholders: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    RA placeholder'larını projelere atar.
    """
    try:
        from app.services.ra_placeholder_service import RAPlaceholderService
        
        ra_service = RAPlaceholderService()
        result = await ra_service.assign_ra_placeholders_to_projects(
            db, projects, available_placeholders
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning RA placeholders: {str(e)}"
        )