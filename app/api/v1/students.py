from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import student
from app.schemas.student import (
    Student,
    StudentCreate,
    StudentUpdate,
)

router = APIRouter()

@router.get("/", response_model=List[Student])
def read_students(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve students.
    """
    students = student.get_multi(db, skip=skip, limit=limit)
    return students

@router.post("/", response_model=Student)
def create_student(
    *,
    db: Session = Depends(deps.get_db),
    student_in: StudentCreate,
    current_user: dict = Depends(deps.get_current_instructor)
) -> Any:
    """
    Create new student.
    """
    student_exists = student.get_by_email(db, email=student_in.email)
    if student_exists:
        raise HTTPException(
            status_code=400,
            detail="A student with this email already exists."
        )
    student_number_exists = student.get_by_student_number(
        db, student_number=student_in.student_number
    )
    if student_number_exists:
        raise HTTPException(
            status_code=400,
            detail="A student with this student number already exists."
        )
    student_obj = student.create(db, obj_in=student_in)
    return student_obj

@router.put("/me", response_model=Student)
def update_student_me(
    *,
    db: Session = Depends(deps.get_db),
    student_in: StudentUpdate,
    current_user: dict = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update own student information.
    """
    if not hasattr(current_user, "student_number"):
        raise HTTPException(
            status_code=400,
            detail="Not a student account"
        )
    student_obj = student.update(
        db, db_obj=current_user, obj_in=student_in
    )
    return student_obj

@router.get("/me", response_model=Student)
def read_student_me(
    current_user: dict = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get current student.
    """
    if not hasattr(current_user, "student_number"):
        raise HTTPException(
            status_code=400,
            detail="Not a student account"
        )
    return current_user

@router.get("/{student_id}", response_model=Student)
def read_student(
    student_id: int,
    current_user: dict = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get student by ID.
    """
    student_obj = student.get(db, id=student_id)
    if not student_obj:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )
    return student_obj

@router.put("/{student_id}", response_model=Student)
def update_student(
    *,
    db: Session = Depends(deps.get_db),
    student_id: int,
    student_in: StudentUpdate,
    current_user: dict = Depends(deps.get_current_instructor)
) -> Any:
    """
    Update a student.
    """
    student_obj = student.get(db, id=student_id)
    if not student_obj:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )
    student_obj = student.update(
        db, db_obj=student_obj, obj_in=student_in
    )
    return student_obj

@router.delete("/{student_id}", response_model=Student)
def delete_student(
    *,
    db: Session = Depends(deps.get_db),
    student_id: int,
    current_user: dict = Depends(deps.get_current_instructor)
) -> Any:
    """
    Delete a student.
    """
    student_obj = student.get(db, id=student_id)
    if not student_obj:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )
    student_obj = student.remove(db, id=student_id)
    return student_obj 