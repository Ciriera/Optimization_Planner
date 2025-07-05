from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.instructor import Instructor
from app.schemas.instructor import InstructorCreate, InstructorUpdate, Instructor as InstructorSchema

router = APIRouter()

def check_admin_access(current_user: User):
    """Admin yetkisi kontrolü"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action"
        )

@router.post("/", response_model=InstructorSchema)
def create_instructor(
    current_user: Annotated[User, Depends(get_current_user)],
    instructor: InstructorCreate,
    db: Session = Depends(get_db)
):
    """Yeni öğretim elemanı oluştur"""
    check_admin_access(current_user)
    
    # Kullanıcının varlığını kontrol et
    user = db.query(User).filter(User.id == instructor.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Öğretim elemanının zaten var olup olmadığını kontrol et
    db_instructor = db.query(Instructor).filter(
        Instructor.user_id == instructor.user_id
    ).first()
    if db_instructor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instructor already exists for this user"
        )
    
    db_instructor = Instructor(**instructor.model_dump())
    db.add(db_instructor)
    db.commit()
    db.refresh(db_instructor)
    return db_instructor

@router.get("/", response_model=List[InstructorSchema])
def read_instructors(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Tüm öğretim elemanlarını listele"""
    instructors = db.query(Instructor).offset(skip).limit(limit).all()
    return instructors

@router.get("/{instructor_id}", response_model=InstructorSchema)
def read_instructor(
    instructor_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Belirli bir öğretim elemanını getir"""
    instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if instructor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found"
        )
    return instructor

@router.put("/{instructor_id}", response_model=InstructorSchema)
def update_instructor(
    instructor_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    instructor: InstructorUpdate,
    db: Session = Depends(get_db)
):
    """Öğretim elemanı bilgilerini güncelle"""
    check_admin_access(current_user)
    
    db_instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if db_instructor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found"
        )
    
    for field, value in instructor.model_dump(exclude_unset=True).items():
        setattr(db_instructor, field, value)
    
    db.commit()
    db.refresh(db_instructor)
    return db_instructor

@router.delete("/{instructor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instructor(
    instructor_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Öğretim elemanını sil"""
    check_admin_access(current_user)
    
    instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if instructor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instructor not found"
        )
    
    db.delete(instructor)
    db.commit()
    return None 