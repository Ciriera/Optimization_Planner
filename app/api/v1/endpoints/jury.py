"""
API endpoints for jury matching system
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.services.jury_matching_service import JuryMatchingService
from app.models.user import User

router = APIRouter()

@router.get("/")
async def get_jury_status() -> Dict[str, Any]:
    """
    Public jury status endpoint for testing
    """
    return {
        "status": "success",
        "message": "Jury matching service is working",
        "matched_juries": 0,
        "pending_matches": 0
    }


@router.post("/match-jury")
async def match_jury(
    projects: List[Dict[str, Any]],
    instructors: List[Dict[str, Any]],
    constraints: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Match juries to projects based on expertise and constraints.
    """
    try:
        service = JuryMatchingService(db)
        result = service.match_jury(projects, instructors, constraints)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Jury matching failed: {str(e)}"
        )


@router.get("/jury-statistics")
async def get_jury_statistics(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Get jury matching statistics and performance metrics.
    """
    try:
        # This would typically fetch from database
        return {
            "status": "success",
            "statistics": {
                "total_matches": 0,
                "average_matching_score": 0.0,
                "most_used_instructors": [],
                "matching_trends": {}
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get jury statistics: {str(e)}"
        )
