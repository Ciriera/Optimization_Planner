from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.db.base import get_db
from app.services.timeslot import TimeSlotService

router = APIRouter()
timeslot_service = TimeSlotService()

@router.get("/", response_model=List[schemas.TimeSlot])
async def read_timeslots(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Zaman dilimlerini listele
    """
    timeslots = await timeslot_service.get_multi(db, skip=skip, limit=limit)
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