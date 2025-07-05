from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.db.base import get_db
from app.services.classroom import ClassroomService
from app.services.auth import AuthService
from app.models.user import User, UserRole

router = APIRouter()
classroom_service = ClassroomService()

def check_admin_access(current_user: User = Depends(AuthService.get_current_user)) -> None:
    """Admin yetkisi kontrolü"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )

@router.get("/active", response_model=List[schemas.Classroom])
async def get_active_classrooms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
) -> Any:
    """
    Aktif sınıfları getir
    """
    # Get all classrooms
    classrooms = await classroom_service.get_multi(db)
    
    # Filter active ones
    active_classrooms = [c for c in classrooms if c.is_active]
    
    return active_classrooms

@router.get("/", response_model=List[schemas.Classroom])
async def read_classrooms(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(AuthService.get_current_user),
) -> Any:
    """
    Sınıfları listele
    """
    classrooms = await classroom_service.get_multi(db, skip=skip, limit=limit)
    return classrooms

@router.post("/", response_model=schemas.Classroom, status_code=status.HTTP_201_CREATED)
async def create_classroom(
    *,
    db: AsyncSession = Depends(get_db),
    classroom_in: schemas.ClassroomCreate,
    current_user: User = Depends(check_admin_access),
) -> Any:
    """
    Yeni sınıf oluştur
    """
    classroom = await classroom_service.create(db, obj_in=classroom_in)
    return classroom

@router.get("/{classroom_id}", response_model=schemas.Classroom)
async def read_classroom(
    *,
    db: AsyncSession = Depends(get_db),
    classroom_id: int,
    current_user: User = Depends(AuthService.get_current_user),
) -> Any:
    """
    Sınıf detayını getir
    """
    classroom = await classroom_service.get(db, id=classroom_id)
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sınıf bulunamadı"
        )
    return classroom

@router.put("/{classroom_id}", response_model=schemas.Classroom)
async def update_classroom(
    *,
    db: AsyncSession = Depends(get_db),
    classroom_id: int,
    classroom_in: schemas.ClassroomUpdate,
    current_user: User = Depends(check_admin_access),
) -> Any:
    """
    Sınıf bilgilerini güncelle
    """
    classroom = await classroom_service.get(db, id=classroom_id)
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sınıf bulunamadı"
        )
    classroom = await classroom_service.update(db, db_obj=classroom, obj_in=classroom_in)
    return classroom

@router.delete("/{classroom_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def delete_classroom(
    *,
    db: AsyncSession = Depends(get_db),
    classroom_id: int,
    current_user: User = Depends(check_admin_access),
) -> Any:
    """
    Sınıfı sil
    """
    classroom = await classroom_service.get(db, id=classroom_id)
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sınıf bulunamadı"
        )
    await classroom_service.remove(db, id=classroom_id)
    return None

@router.get("/{classroom_id}/schedule", response_model=List[Dict[str, Any]])
async def get_classroom_schedule(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
) -> Any:
    """
    Sınıfın planlamasını getir
    """
    # Check if classroom exists
    classroom = await classroom_service.get(db, id=classroom_id)
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sınıf bulunamadı"
        )
    
    # Return empty list for now
    return []

@router.get("/{classroom_id}/availability", response_model=Dict[str, Any])
async def get_classroom_availability(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
) -> Any:
    """
    Sınıfın müsaitlik durumunu getir
    """
    # Check if classroom exists
    classroom = await classroom_service.get(db, id=classroom_id)
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sınıf bulunamadı"
        )
    
    # Return simple availability info
    return {
        "classroom_id": classroom_id,
        "available_slots": []
    }