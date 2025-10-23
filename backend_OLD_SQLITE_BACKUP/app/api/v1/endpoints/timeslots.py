from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import time, datetime, timedelta

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/public", response_model=List[schemas.TimeSlot])
def read_timeslots_public(
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve timeslots (public, no authentication required).
    """
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        timeslots = crud.timeslot.get_multi(db, skip=skip, limit=limit)
        return timeslots
    finally:
        db.close()

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


@router.post("/seed-standard")
def seed_standard_timeslots(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Sabah ve öğle için standart 30 dakikalık zaman dilimlerini oluşturur.
    Idempotent: Var olan aralıkları atlar.
    """
    def generate(start_h: int, start_m: int, count: int, period: str):
        created = 0
        cur = datetime(2000, 1, 1, start_h, start_m)
        for _ in range(count):
            st = (cur).time()
            et = (cur + timedelta(minutes=30)).time()
            existing = crud.timeslot.get_by_time(db, start_time=st, end_time=et)
            if not existing:
                crud.timeslot.create(db, obj_in=schemas.TimeSlotCreate(start_time=st, end_time=et, period=period))
                created += 1
            cur += timedelta(minutes=30)
        return created

    created = 0
    # Sabah 09:00 - 12:00 (09:00-09:30, ..., 11:30-12:00) -> 6 slot
    created += generate(9, 0, 6, "morning")
    # Öğle 13:00 - 17:00 (13:00-13:30, ..., 16:30-17:00) -> 8 slot
    created += generate(13, 0, 8, "afternoon")

    total = db.query(models.TimeSlot).count()
    return {"status": "success", "created": created, "total": total}