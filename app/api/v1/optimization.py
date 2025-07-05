from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.core.cache import get_cache
from app.schemas.algorithm import (
    OptimizationRequest,
    OptimizationResponse,
    OptimizationResult
)
from app.tasks import optimize_assignments

router = APIRouter()

@router.post("/optimize", response_model=OptimizationResponse)
def start_optimization(
    *,
    optimization_in: OptimizationRequest,
    current_user: dict = Depends(deps.get_current_instructor)
) -> Any:
    """
    Start project assignment optimization task.
    """
    # Start Celery task
    task = optimize_assignments.delay(
        algorithm_type=optimization_in.algorithm_type,
        algorithm_params=optimization_in.parameters.dict() if optimization_in.parameters else None
    )
    
    return {
        "task_id": task.id,
        "status": "pending"
    }

@router.get("/results/{task_id}", response_model=OptimizationResult)
def get_optimization_results(
    task_id: str,
    current_user: dict = Depends(deps.get_current_instructor)
) -> Any:
    """
    Get optimization task results.
    """
    # Check cache for results
    result = get_cache(f"optimization_result:{task_id}")
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Task result not found"
        )
    
    if result.get("status") == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Task failed: {result.get('error')}"
        )
    
    if result.get("status") != "completed":
        raise HTTPException(
            status_code=102,
            detail="Task still processing"
        )
    
    return result.get("result") 