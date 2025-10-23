"""
Reports API Endpoints
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models import User
from app.services.report_generator_service import ReportGeneratorService
from app.services.score_generator_service import ScoreGeneratorService
from app.services.chart_generator_service import ChartGeneratorService
from app.services.performance_metrics import compute, compute_many

router = APIRouter()

@router.post("/generate-score", response_model=dict)
async def generate_score_report(
    *,
    algorithm_run_id: Optional[int] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Score.json dosyası oluşturur."""
    service = ScoreGeneratorService()
    result = await service.generate_comprehensive_score_report(algorithm_run_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.post("/generate-report", response_model=dict)
async def generate_comprehensive_report(
    *,
    algorithm_run_id: Optional[int] = None,
    format_types: List[str] = ["pdf", "excel"],
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Kapsamlı rapor oluşturur (PDF ve Excel)."""
    service = ReportGeneratorService()
    result = await service.generate_comprehensive_report(algorithm_run_id, format_types)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.post("/generate-load-chart", response_model=dict)
async def generate_load_distribution_chart(
    *,
    algorithm_run_id: Optional[int] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Yük dağılımı grafiği oluşturur."""
    service = ChartGeneratorService()
    result = await service.generate_load_distribution_chart(algorithm_run_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.post("/generate-dashboard", response_model=dict)
async def generate_comprehensive_dashboard(
    *,
    algorithm_run_id: Optional[int] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Kapsamlı dashboard oluşturur."""
    service = ChartGeneratorService()
    result = await service.generate_comprehensive_dashboard(algorithm_run_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.get("/latest-score", response_model=dict)
async def get_latest_score(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """En son score.json dosyasını getirir."""
    service = ScoreGeneratorService()
    result = await service.get_latest_score()
    
    if result is None:
        raise HTTPException(status_code=404, detail="Score dosyası bulunamadı")
    
    return {"success": True, "score_data": result}


@router.post("/metrics/compute", response_model=dict)
async def compute_performance_metrics(
    *,
    plan: dict,
    db: AsyncSession = Depends(deps.get_db),
    # Temporarily remove auth for testing
    # current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Tek bir plan için performans metriklerini hesapla."""
    return {"success": True, "metrics": compute(plan)}


@router.post("/metrics/compare", response_model=dict)
async def compare_performance_metrics(
    *,
    payload: dict,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Birden fazla algoritmanın plan çıktısını metriklerle karşılaştır."""
    by_algo = payload.get("byAlgorithm", {}) or {}
    weights = payload.get("weights")
    params = payload.get("params")
    return {"success": True, "results": compute_many(by_algo, weights=weights, params=params)}