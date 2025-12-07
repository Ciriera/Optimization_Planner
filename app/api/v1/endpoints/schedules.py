from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app import models, schemas
from app.api import deps
from app.db.base import get_db
from app.services.schedule import ScheduleService
from app.services.report import ReportService
from app.i18n import translate as _

router = APIRouter()
schedule_service = ScheduleService()
report_service = ReportService()

@router.get("/", response_model=List[Dict[str, Any]])
async def read_schedules(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    is_makeup: bool = Query(None, description="Bütünleme mi?"),
    # Temporarily remove auth requirement for testing
    # current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Planları listele
    """
    try:
        schedules = await schedule_service.get_filtered(
            db, skip=skip, limit=limit, is_makeup=is_makeup
        )
        return schedules
    except Exception as e:
        # Log the error and return empty list for dashboard compatibility
        print(f"Error fetching schedules: {e}")
        return []

@router.get("/public", response_model=List[Dict[str, Any]])
async def read_schedules_public(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Public schedules endpoint for frontend dashboard
    """
    try:
        schedules = await schedule_service.get_filtered(db, skip=0, limit=1000)
        return schedules
    except Exception as e:
        print(f"Error fetching public schedules: {e}")
        return []

@router.post("/", response_model=schemas.Schedule)
async def create_schedule(
    *,
    db: AsyncSession = Depends(get_db),
    schedule_in: schemas.ScheduleCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Yeni bir planlama oluştur.
    """
    # Classroom kontrolü
    stmt = select(models.Classroom).where(models.Classroom.id == schedule_in.classroom_id)
    result = await db.execute(stmt)
    classroom = result.scalars().first()
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("schedule.classroom_not_found", locale=current_user.language)
        )
    
    # Timeslot kontrolü
    stmt = select(models.TimeSlot).where(models.TimeSlot.id == schedule_in.timeslot_id)
    result = await db.execute(stmt)
    timeslot = result.scalars().first()
    if not timeslot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("schedule.timeslot_not_found", locale=current_user.language)
        )
    
    # Project kontrolü
    stmt = select(models.Project).where(models.Project.id == schedule_in.project_id)
    result = await db.execute(stmt)
    project = result.scalars().first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("schedule.project_not_found", locale=current_user.language)
        )
    
    # Çakışma kontrolü
    exists = await schedule_service.check_conflict(
        db, classroom_id=schedule_in.classroom_id, timeslot_id=schedule_in.timeslot_id
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_("schedule.conflict", locale=current_user.language)
        )
    
    schedule = await schedule_service.create(db, obj_in=schedule_in)
    return schedule

@router.get("/{schedule_id}", response_model=schemas.ScheduleWithRelations)
async def read_schedule(
    *,
    db: AsyncSession = Depends(get_db),
    schedule_id: int,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Planlama detayını getir
    """
    schedule = await schedule_service.get(db, id=schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("schedule.not_found", locale=current_user.language)
        )
    return schedule

@router.put("/{schedule_id}", response_model=schemas.Schedule)
async def update_schedule(
    *,
    db: AsyncSession = Depends(get_db),
    schedule_id: int,
    schedule_in: schemas.ScheduleUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Planlama kaydını güncelle
    """
    schedule = await schedule_service.get(db, id=schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("schedule.not_found", locale=current_user.language)
        )
    
    # Çakışma kontrolü (eğer sınıf veya zaman dilimi değiştiyse)
    if (schedule_in.classroom_id != schedule.classroom_id or 
            schedule_in.timeslot_id != schedule.timeslot_id):
        exists = await schedule_service.check_conflict(
            db, classroom_id=schedule_in.classroom_id, 
            timeslot_id=schedule_in.timeslot_id, exclude_id=schedule_id
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_("schedule.conflict", locale=current_user.language)
            )
    
    schedule = await schedule_service.update(db, db_obj=schedule, obj_in=schedule_in)
    return schedule

@router.delete("/{schedule_id}", response_model=schemas.Schedule)
async def delete_schedule(
    *,
    db: AsyncSession = Depends(get_db),
    schedule_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Planlama kaydını sil
    """
    schedule = await schedule_service.get(db, id=schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("schedule.not_found", locale=current_user.language)
        )
    schedule = await schedule_service.remove(db, id=schedule_id)
    return schedule

@router.get("/reports/pdf", response_class=Response)
async def generate_pdf_report(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    PDF formatında atama planı raporu oluştur
    """
    try:
        pdf_data = await report_service.generate_schedule_pdf(db)
        
        # PDF dosyası için response
        headers = {
            'Content-Disposition': f'attachment; filename="schedule_report_{datetime.now().strftime("%Y%m%d")}.pdf"'
        }
        return Response(content=pdf_data, media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("reports.error", locale=current_user.language)
        )

@router.get("/reports/excel", response_class=Response)
async def generate_excel_report(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Excel formatında atama planı raporu oluştur
    """
    try:
        excel_data = await report_service.generate_schedule_excel(db)
        
        # Excel dosyası için response
        headers = {
            'Content-Disposition': f'attachment; filename="schedule_report_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        }
        return Response(content=excel_data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("reports.error", locale=current_user.language)
        ) 