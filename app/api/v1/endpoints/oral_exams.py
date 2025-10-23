"""
API endpoints for oral exam planning
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.services.oral_exam_service import OralExamService
from app.models.user import User

router = APIRouter()

@router.get("/")
async def get_oral_exam_status() -> Dict[str, Any]:
    """
    Public oral exam status endpoint for testing
    """
    return {
        "status": "success",
        "message": "Oral exam service is working",
        "scheduled_exams": 0,
        "pending_exams": 0
    }


@router.post("/plan-oral-exams")
async def plan_oral_exams(
    projects: List[Dict[str, Any]],
    instructors: List[Dict[str, Any]],
    classrooms: List[Dict[str, Any]],
    timeslots: List[Dict[str, Any]],
    constraints: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Plan oral examinations for projects.
    """
    try:
        service = OralExamService(db)
        result = service.plan_oral_exams(projects, instructors, classrooms, timeslots, constraints)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Oral exam planning failed: {str(e)}"
        )


@router.post("/optimize-schedule")
async def optimize_schedule(
    schedule: List[Dict[str, Any]],
    optimization_goals: List[str],
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Optimize oral exam schedule based on specified goals.
    """
    try:
        service = OralExamService(db)
        result = service.optimize_schedule(schedule, optimization_goals)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schedule optimization failed: {str(e)}"
        )


@router.get("/exam-statistics")
async def get_exam_statistics(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Get oral exam planning statistics.
    """
    try:
        return {
            "status": "success",
            "statistics": {
                "total_exams_planned": 0,
                "average_scheduling_rate": 0.0,
                "common_conflicts": [],
                "resource_utilization": 0.0
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get exam statistics: {str(e)}"
        )
