from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.db.base import get_db
from app.services.report import ReportService

router = APIRouter()
report_service = ReportService()

@router.get("/load-distribution", response_model=Dict[str, Any])
async def get_load_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Öğretim elemanlarının yük dağılımını getirir
    """
    return await report_service.get_load_distribution(db)

@router.get("/export/pdf")
async def export_schedule_pdf(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Planlama bilgilerini PDF olarak dışa aktarır
    """
    content = await report_service.generate_schedule_pdf(db)
    headers = {"Content-Disposition": "attachment; filename=schedule_report.pdf"}
    return Response(content, media_type="application/pdf", headers=headers)

@router.get("/export/excel")
async def export_schedule_excel(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Planlama bilgilerini Excel olarak dışa aktarır
    """
    content = await report_service.generate_schedule_excel(db)
    headers = {"Content-Disposition": "attachment; filename=schedule_report.xlsx"}
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers) 