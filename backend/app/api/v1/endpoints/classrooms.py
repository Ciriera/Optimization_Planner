from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Classroom])
def read_classrooms(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve classrooms.
    """
    classrooms = crud.classroom.get_multi(db, skip=skip, limit=limit)
    return classrooms


@router.post("/", response_model=schemas.Classroom)
def create_classroom(
    *,
    db: Session = Depends(deps.get_db),
    classroom_in: schemas.ClassroomCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new classroom.
    """
    classroom = crud.classroom.get_by_name(db, name=classroom_in.name)
    if classroom:
        raise HTTPException(
            status_code=400,
            detail="The classroom with this name already exists in the system.",
        )
    classroom = crud.classroom.create(db, obj_in=classroom_in)
    return classroom


@router.put("/{id}", response_model=schemas.Classroom)
def update_classroom(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    classroom_in: schemas.ClassroomUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a classroom.
    """
    classroom = crud.classroom.get(db, id=id)
    if not classroom:
        raise HTTPException(
            status_code=404,
            detail="The classroom with this ID does not exist in the system",
        )
    classroom = crud.classroom.update(db, db_obj=classroom, obj_in=classroom_in)
    return classroom


@router.get("/{id}", response_model=schemas.Classroom)
def read_classroom(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get classroom by ID.
    """
    classroom = crud.classroom.get(db, id=id)
    if not classroom:
        raise HTTPException(
            status_code=404,
            detail="The classroom with this ID does not exist in the system",
        )
    return classroom


@router.delete("/{id}", response_model=schemas.Classroom)
def delete_classroom(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a classroom.
    """
    classroom = crud.classroom.get(db, id=id)
    if not classroom:
        raise HTTPException(
            status_code=404,
            detail="The classroom with this ID does not exist in the system",
        )
    classroom = crud.classroom.remove(db, id=id)
    return classroom 