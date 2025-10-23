from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.db.base import get_db
from app.services.timeslot import TimeSlotService
from app.services.auth import AuthService
from app.models.user import User, UserRole

router = APIRouter()
timeslot_service = TimeSlotService()

def check_admin_access(current_user: User = Depends(deps.get_current_user)) -> None:
    """Admin yetkisi kontrolü"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )

@router.get("/", response_model=List[schemas.TimeSlot])
async def read_timeslots(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    # Temporarily remove auth requirement for testing
    # current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Zaman dilimlerini listele
    """
    timeslots = await timeslot_service.get_multi(db, skip=skip, limit=limit)
    return timeslots

@router.get("/public", response_model=List[schemas.TimeSlot])
async def read_timeslots_public(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Public timeslots endpoint for frontend dashboard
    """
    timeslots = await timeslot_service.get_multi(db, skip=0, limit=1000)
    return timeslots

@router.post("/", response_model=schemas.TimeSlot)
async def create_timeslot(
    *,
    db: AsyncSession = Depends(get_db),
    timeslot_in: schemas.TimeSlotCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Yeni zaman dilimi oluştur
    """
    timeslot = await timeslot_service.create(db, obj_in=timeslot_in)
    return timeslot

@router.get("/{timeslot_id}", response_model=schemas.TimeSlotWithRelations)
async def read_timeslot(
    *,
    db: AsyncSession = Depends(get_db),
    timeslot_id: int,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Zaman dilimi detayını getir
    """
    timeslot = await timeslot_service.get(db, id=timeslot_id)
    if not timeslot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zaman dilimi bulunamadı"
        )
    return timeslot

@router.put("/{timeslot_id}", response_model=schemas.TimeSlot)
async def update_timeslot(
    *,
    db: AsyncSession = Depends(get_db),
    timeslot_id: int,
    timeslot_in: schemas.TimeSlotUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Zaman dilimi bilgilerini güncelle
    """
    timeslot = await timeslot_service.get(db, id=timeslot_id)
    if not timeslot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zaman dilimi bulunamadı"
        )
    timeslot = await timeslot_service.update(db, db_obj=timeslot, obj_in=timeslot_in)
    return timeslot

@router.delete("/{timeslot_id}", response_model=schemas.TimeSlot)
async def delete_timeslot(
    *,
    db: AsyncSession = Depends(get_db),
    timeslot_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Zaman dilimini sil
    """
    timeslot = await timeslot_service.get(db, id=timeslot_id)
    if not timeslot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zaman dilimi bulunamadı"
        )
    timeslot = await timeslot_service.remove(db, id=timeslot_id)
    return timeslot


@router.post("/fix-structure")
async def fix_timeslot_structure(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_admin_access),
) -> Any:
    """
    Zaman dilimi yapısını düzeltir (12:00-13:00 öğle arası boşluk dahil).
    """
    try:
        from app.services.timeslot_fixer import TimeslotFixer
        
        fixer = TimeslotFixer()
        result = await fixer.fix_timeslot_structure(db)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fixing timeslot structure: {str(e)}"
        )


@router.get("/validate-structure")
async def validate_timeslot_structure(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
) -> Any:
    """
    Zaman dilimi yapısını validate eder.
    """
    try:
        from app.services.timeslot_fixer import TimeslotFixer
        
        fixer = TimeslotFixer()
        validation = await fixer.validate_timeslot_structure(db)
        
        return validation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating timeslot structure: {str(e)}"
        )


@router.get("/schedule-template")
async def get_timeslot_schedule_template(
    current_user: User = Depends(AuthService.get_current_user),
) -> Any:
    """
    Doğru zaman dilimi şablonunu getirir.
    """
    try:
        from app.services.timeslot_fixer import TimeslotFixer
        
        fixer = TimeslotFixer()
        template = await fixer.get_timeslot_schedule_template()
        
        return template
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting schedule template: {str(e)}"
        ) 