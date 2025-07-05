from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.db.base import get_db
from app.services.algorithm import AlgorithmService
from app.models.algorithm import AlgorithmType
from app.core.celery import celery_app
from app.i18n import translate as _

router = APIRouter()

@router.get("/list", response_model=List[Dict[str, Any]])
async def list_available_algorithms(
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Any:
    """
    Kullanılabilir algoritmaları listeler
    """
    return AlgorithmService.list_algorithms()

@router.post("/execute", response_model=schemas.AlgorithmRunResponse)
async def execute_algorithm(
    *,
    algorithm_in: schemas.AlgorithmRunCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Belirtilen algoritmayı çalıştırır
    """
    # Algoritmanın geçerli olduğunu kontrol et
    try:
        algorithm_type = AlgorithmType(algorithm_in.algorithm_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_("algorithms.invalid_algorithm", locale=current_user.language)
        )
    
    try:
        # Algoritmayı çalıştır
        result, algorithm_run = await AlgorithmService.run_algorithm(
            algorithm_type=algorithm_type,
            data=algorithm_in.data or {},
            params=algorithm_in.parameters or {}
        )
        
        # Sonucu döndür
        return {
            "id": algorithm_run.id,
            "algorithm_type": algorithm_type,
            "status": algorithm_run.status,
            "task_id": str(algorithm_run.id),
            "message": _("algorithms.completed", locale=current_user.language)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("algorithms.execution_error", locale=current_user.language, error=str(e))
        )

@router.get("/status/{run_id}", response_model=Dict[str, Any])
async def get_algorithm_status(
    run_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Algoritma çalıştırma durumunu kontrol eder
    """
    try:
        result = await AlgorithmService.get_run_result(run_id)
        return {
            "status": result["status"],
            "execution_time": result["execution_time"],
            "started_at": result["started_at"],
            "completed_at": result["completed_at"],
            "error": result["error"]
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("algorithms.run_not_found", locale=current_user.language)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("algorithms.status_error", locale=current_user.language, error=str(e))
        )

@router.post("/recommend-best", response_model=Dict[str, Any])
async def recommend_best_algorithm(
    *,
    data: Dict[str, Any],
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    En iyi algoritmayı öner
    """
    try:
        recommendation = AlgorithmService.recommend_algorithm(data)
        return recommendation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("algorithms.recommendation_error", locale=current_user.language, error=str(e))
        )

@router.get("/results/{run_id}", response_model=Dict[str, Any])
async def get_algorithm_results(
    *,
    run_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Algoritma çalıştırma sonuçlarını getirir
    """
    try:
        result = await AlgorithmService.get_run_result(run_id)
        if result["status"] != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_("algorithms.not_completed", locale=current_user.language, status=result["status"])
            )
        return result
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("algorithms.run_not_found", locale=current_user.language)
        )

@router.get("/compare", response_model=Dict[str, Any])
async def compare_algorithms(
    *,
    data: Dict[str, Any],
    algorithm_types: List[str],
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Belirtilen algoritmaları karşılaştırır
    """
    # Bu endpoint'i ileride implementasyonlar tamamlandıkça geliştirebilirsiniz
    return {
        "message": _("algorithms.comparison_not_implemented", locale=current_user.language),
        "status": "NOT_IMPLEMENTED"
    } 