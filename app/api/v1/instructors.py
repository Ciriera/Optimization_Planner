from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import instructor
from app.schemas.instructor import (
    Instructor,
    InstructorCreate,
    InstructorUpdate,
)

router = APIRouter()

@router.get("/", response_model=List[Instructor])
def read_instructors(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve instructors.
    """
    instructors = instructor.get_multi(db, skip=skip, limit=limit)
    return instructors

@router.post("/", response_model=Instructor)
def create_instructor(
    *,
    db: Session = Depends(deps.get_db),
    instructor_in: InstructorCreate,
    current_user: dict = Depends(deps.get_current_instructor)
) -> Any:
    """
    Create new instructor.
    """
    instructor_exists = instructor.get_by_email(db, email=instructor_in.email)
    if instructor_exists:
        raise HTTPException(
            status_code=400,
            detail="An instructor with this email already exists."
        )
    instructor_obj = instructor.create(db, obj_in=instructor_in)
    return instructor_obj

@router.put("/me", response_model=Instructor)
def update_instructor_me(
    *,
    db: Session = Depends(deps.get_db),
    instructor_in: InstructorUpdate,
    current_user: dict = Depends(deps.get_current_instructor)
) -> Any:
    """
    Update own instructor information.
    """
    instructor_obj = instructor.update(
        db, db_obj=current_user, obj_in=instructor_in
    )
    return instructor_obj

@router.get("/me", response_model=Instructor)
def read_instructor_me(
    current_user: dict = Depends(deps.get_current_instructor)
) -> Any:
    """
    Get current instructor.
    """
    return current_user

@router.get("/{instructor_id}", response_model=Instructor)
def read_instructor(
    instructor_id: int,
    current_user: dict = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get instructor by ID.
    """
    instructor_obj = instructor.get(db, id=instructor_id)
    if not instructor_obj:
        raise HTTPException(
            status_code=404,
            detail="Instructor not found"
        )
    return instructor_obj

@router.put("/{instructor_id}", response_model=Instructor)
def update_instructor(
    *,
    db: Session = Depends(deps.get_db),
    instructor_id: int,
    instructor_in: InstructorUpdate,
    current_user: dict = Depends(deps.get_current_instructor)
) -> Any:
    """
    Update an instructor.
    """
    instructor_obj = instructor.get(db, id=instructor_id)
    if not instructor_obj:
        raise HTTPException(
            status_code=404,
            detail="Instructor not found"
        )
    instructor_obj = instructor.update(
        db, db_obj=instructor_obj, obj_in=instructor_in
    )
    return instructor_obj

@router.delete("/{instructor_id}", response_model=Instructor)
def delete_instructor(
    *,
    db: Session = Depends(deps.get_db),
    instructor_id: int,
    current_user: dict = Depends(deps.get_current_instructor)
) -> Any:
    """
    Delete an instructor.
    """
    instructor_obj = instructor.get(db, id=instructor_id)
    if not instructor_obj:
        raise HTTPException(
            status_code=404,
            detail="Instructor not found"
        )
    instructor_obj = instructor.remove(db, id=instructor_id)
    return instructor_obj 