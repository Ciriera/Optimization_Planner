from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.TimeSlot])
def read_timeslots(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve timeslots.
    """
    timeslots = crud.timeslot.get_multi(db, skip=skip, limit=limit)
    return timeslots


@router.post("/", response_model=schemas.TimeSlot)
def create_timeslot(
    *,
    db: Session = Depends(deps.get_db),
    timeslot_in: schemas.TimeSlotCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new timeslot.
    """
    timeslot = crud.timeslot.get_by_time(
        db, start_time=timeslot_in.start_time, end_time=timeslot_in.end_time
    )
    if timeslot:
        raise HTTPException(
            status_code=400,
            detail="A timeslot with this start and end time already exists.",
        )
    timeslot = crud.timeslot.create(db, obj_in=timeslot_in)
    return timeslot


@router.put("/{id}", response_model=schemas.TimeSlot)
def update_timeslot(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    timeslot_in: schemas.TimeSlotUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a timeslot.
    """
    timeslot = crud.timeslot.get(db, id=id)
    if not timeslot:
        raise HTTPException(
            status_code=404,
            detail="The timeslot with this ID does not exist in the system",
        )
    timeslot = crud.timeslot.update(db, db_obj=timeslot, obj_in=timeslot_in)
    return timeslot


@router.get("/{id}", response_model=schemas.TimeSlot)
def read_timeslot(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get timeslot by ID.
    """
    timeslot = crud.timeslot.get(db, id=id)
    if not timeslot:
        raise HTTPException(
            status_code=404,
            detail="The timeslot with this ID does not exist in the system",
        )
    return timeslot


@router.delete("/{id}", response_model=schemas.TimeSlot)
def delete_timeslot(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a timeslot.
    """
    timeslot = crud.timeslot.get(db, id=id)
    if not timeslot:
        raise HTTPException(
            status_code=404,
            detail="The timeslot with this ID does not exist in the system",
        )
    timeslot = crud.timeslot.remove(db, id=id)
    return timeslot


@router.get("/period/{period}", response_model=List[schemas.TimeSlot])
def read_timeslots_by_period(
    *,
    db: Session = Depends(deps.get_db),
    period: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get timeslots by period (morning/afternoon).
    """
    timeslots = crud.timeslot.get_by_period(db, period=period)
    return timeslots 