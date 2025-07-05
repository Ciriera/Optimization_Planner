from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.services.algorithm import run_algorithm, get_algorithm_result, recommend_best_algorithm

router = APIRouter()


@router.get("/list", response_model=List[str])
def list_algorithms(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    List all available algorithms.
    """
    return [
        "simplex",
        "genetic",
        "simulated_annealing",
        "deep_search",
        "ant_colony",
        "nsga2",
        "greedy_local_search",
        "tabu_search",
        "particle_swarm",
        "harmony_search",
        "firefly",
        "grey_wolf",
        "cp_sat"
    ]


@router.post("/execute", response_model=schemas.AlgorithmRun)
async def execute_algorithm(
    *,
    db: Session = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    algorithm_in: schemas.AlgorithmExecuteRequest,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Execute an algorithm with given parameters.
    """
    # Validate algorithm exists
    available_algorithms = list_algorithms(current_user)
    if algorithm_in.algorithm not in available_algorithms:
        raise HTTPException(
            status_code=400,
            detail=f"Algorithm '{algorithm_in.algorithm}' not found. Available algorithms: {', '.join(available_algorithms)}",
        )
    
    # Create a record for the algorithm run
    algorithm_run = crud.algorithm.create(
        db, 
        obj_in=schemas.AlgorithmCreate(
            algorithm=algorithm_in.algorithm,
            params=algorithm_in.params,
            status="pending"
        )
    )
    
    # Run algorithm in background
    background_tasks.add_task(
        run_algorithm,
        db=db,
        algorithm_run_id=algorithm_run.id,
        algorithm_name=algorithm_in.algorithm,
        params=algorithm_in.params
    )
    
    return algorithm_run


@router.get("/results/{algorithm_run_id}", response_model=schemas.AlgorithmRun)
def get_algorithm_results(
    *,
    db: Session = Depends(deps.get_db),
    algorithm_run_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get results of an algorithm run.
    """
    algorithm_run = crud.algorithm.get(db, id=algorithm_run_id)
    if not algorithm_run:
        raise HTTPException(
            status_code=404,
            detail="Algorithm run not found",
        )
    
    # If algorithm is still running, get updated status
    if algorithm_run.status == "pending":
        algorithm_run = get_algorithm_result(db, algorithm_run_id)
    
    return algorithm_run


@router.get("/recommend-best", response_model=schemas.AlgorithmRecommendation)
def get_best_algorithm_recommendation(
    *,
    db: Session = Depends(deps.get_db),
    project_type: str = None,
    optimize_for: str = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get recommendation for the best algorithm based on the current data.
    """
    recommendation = recommend_best_algorithm(db, project_type=project_type, optimize_for=optimize_for)
    return recommendation 