"""
User Recommendations API Endpoints
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models import User
from app.services.user_recommendation_service import UserRecommendationService

router = APIRouter()

@router.post("/personalized-algorithm", response_model=dict)
async def get_personalized_algorithm_recommendation(
    *,
    problem_data: Dict[str, Any],
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Kullanıcıya özelleştirilmiş algoritma önerisi getirir."""
    service = UserRecommendationService()
    result = await service.get_personalized_algorithm_recommendation(
        current_user.id, problem_data, db
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.get("/performance-insights", response_model=dict)
async def get_user_performance_insights(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Kullanıcının performans içgörülerini getirir."""
    service = UserRecommendationService()
    result = await service.get_user_performance_insights(current_user.id, db)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.post("/smart-defaults", response_model=dict)
async def get_smart_defaults(
    *,
    problem_data: Dict[str, Any],
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Kullanıcı için akıllı varsayılan değerler önerir."""
    service = UserRecommendationService()
    result = await service.get_smart_defaults(current_user.id, problem_data)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result
