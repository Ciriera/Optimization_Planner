from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Schedule])
def read_schedules(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve schedules.
    """
    schedules = crud.schedule.get_multi(db, skip=skip, limit=limit)
    return schedules


@router.post("/", response_model=schemas.Schedule)
def create_schedule(
    *,
    db: Session = Depends(deps.get_db),
    schedule_in: schemas.ScheduleCreate,
    instructor_ids: List[int] = Body(...),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new schedule with instructors.
    """
    # Check if project already has a schedule
    existing_schedule = crud.schedule.get_by_project(db, project_id=schedule_in.project_id)
    if existing_schedule:
        raise HTTPException(
            status_code=400,
            detail="This project already has a schedule.",
        )
    
    # Check if classroom and timeslot are available
    conflicts = crud.schedule.get_by_classroom_and_timeslot(
        db, classroom_id=schedule_in.classroom_id, timeslot_id=schedule_in.timeslot_id
    )
    if conflicts:
        raise HTTPException(
            status_code=400,
            detail="This classroom and timeslot combination is already occupied.",
        )
    
    # Create schedule with instructors
    schedule = crud.schedule.create_with_instructors(
        db, obj_in=schedule_in, instructor_ids=instructor_ids
    )
    return schedule


@router.put("/{id}", response_model=schemas.Schedule)
def update_schedule(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    schedule_in: schemas.ScheduleUpdate,
    instructor_ids: List[int] = Body(None),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a schedule.
    """
    schedule = crud.schedule.get(db, id=id)
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail="The schedule with this ID does not exist in the system",
        )
    
    # Update basic schedule info
    schedule = crud.schedule.update(db, db_obj=schedule, obj_in=schedule_in)
    
    # Update instructors if provided
    if instructor_ids is not None:
        from app.models.instructor import Instructor
        instructors = db.query(Instructor).filter(Instructor.id.in_(instructor_ids)).all()
        schedule.instructors = instructors
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
    
    return schedule


@router.get("/{id}", response_model=schemas.Schedule)
def read_schedule(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get schedule by ID.
    """
    schedule = crud.schedule.get(db, id=id)
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail="The schedule with this ID does not exist in the system",
        )
    return schedule


@router.delete("/{id}", response_model=schemas.Schedule)
def delete_schedule(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a schedule.
    """
    schedule = crud.schedule.get(db, id=id)
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail="The schedule with this ID does not exist in the system",
        )
    schedule = crud.schedule.remove(db, id=id)
    return schedule


@router.get("/project/{project_id}", response_model=schemas.Schedule)
def read_schedule_by_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get schedule by project ID.
    """
    schedule = crud.schedule.get_by_project(db, project_id=project_id)
    if not schedule:
        raise HTTPException(
            status_code=404,
            detail="No schedule found for this project",
        )
    return schedule


@router.get("/instructor/{instructor_id}", response_model=List[schemas.Schedule])
def read_schedules_by_instructor(
    *,
    db: Session = Depends(deps.get_db),
    instructor_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all schedules for a specific instructor.
    """
    schedules = crud.schedule.get_by_instructor(db, instructor_id=instructor_id)
    return schedules 