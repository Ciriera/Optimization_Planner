from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.get("/", response_model=List[schemas.Instructor])
def read_instructors(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Tüm öğretim üyelerini getir.
    """
    instructors = crud.instructor.get_multi(db, skip=skip, limit=limit)
    return instructors

@router.post("/", response_model=schemas.Instructor)
def create_instructor(
    *,
    db: Session = Depends(deps.get_db),
    instructor_in: schemas.InstructorCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Yeni öğretim üyesi oluştur.
    """
    instructor = crud.instructor.create(db=db, obj_in=instructor_in)
    return instructor

@router.put("/{instructor_id}", response_model=schemas.Instructor)
def update_instructor(
    *,
    db: Session = Depends(deps.get_db),
    instructor_id: int,
    instructor_in: schemas.InstructorUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Öğretim üyesi bilgilerini güncelle.
    """
    instructor = crud.instructor.get(db=db, id=instructor_id)
    if not instructor:
        raise HTTPException(
            status_code=404,
            detail="Instructor not found",
        )
    instructor = crud.instructor.update(db=db, db_obj=instructor, obj_in=instructor_in)
    return instructor

@router.get("/{instructor_id}", response_model=schemas.Instructor)
def read_instructor(
    *,
    db: Session = Depends(deps.get_db),
    instructor_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Öğretim üyesi bilgilerini getir.
    """
    instructor = crud.instructor.get(db=db, id=instructor_id)
    if not instructor:
        raise HTTPException(
            status_code=404,
            detail="Instructor not found",
        )
    return instructor

@router.delete("/{instructor_id}", response_model=schemas.Instructor)
def delete_instructor(
    *,
    db: Session = Depends(deps.get_db),
    instructor_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Öğretim üyesini sil.
    """
    instructor = crud.instructor.get(db=db, id=instructor_id)
    if not instructor:
        raise HTTPException(
            status_code=404,
            detail="Instructor not found",
        )
    instructor = crud.instructor.remove(db=db, id=instructor_id)
    return instructor 