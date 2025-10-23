"""
API endpoints for recommendation system
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.services.recommendation_service import RecommendationService
from app.models.user import User

router = APIRouter()

@router.get("/")
async def get_recommendations_public() -> Dict[str, Any]:
    """
    Public recommendations endpoint for testing
    """
    return {
        "status": "success",
        "message": "Recommendations service is working",
        "recommendations": [
            {"algorithm": "greedy", "confidence": 0.8, "reason": "Fast and reliable"},
            {"algorithm": "genetic_algorithm", "confidence": 0.7, "reason": "Good for complex problems"}
        ]
    }


@router.post("/recommend-algorithm")
async def recommend_algorithm(
    problem_data: Dict[str, Any],
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Get algorithm recommendation for a specific problem.
    """
    try:
        service = RecommendationService(db)
        recommendation = service.recommend_algorithm(current_user.id, problem_data)
        
        return {
            "status": "success",
            "recommendation": recommendation,
            "user_id": current_user.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {str(e)}"
        )


@router.get("/user-preferences/{user_id}")
async def get_user_preferences(
    user_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Get user's algorithm preferences based on history.
    """
    try:
        service = RecommendationService(db)
        preferences = service.get_user_preferences(user_id)
        
        return {
            "status": "success",
            "preferences": preferences,
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}"
        )


@router.get("/algorithm-performance")
async def get_algorithm_performance(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Get algorithm performance statistics.
    """
    try:
        service = RecommendationService(db)
        history = service._get_user_history(current_user.id)
        
        return {
            "status": "success",
            "performance_data": history,
            "user_id": current_user.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance data: {str(e)}"
        )
