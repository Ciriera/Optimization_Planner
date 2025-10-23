from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, time

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.schedule import Schedule
from app.models.project import Project
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, Schedule as ScheduleSchema

router = APIRouter()

def check_admin_access(current_user: User):
    """Admin yetkisi kontrolü"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action"
        )

def check_schedule_conflict(db: Session, classroom: str, date: datetime, 
                          start_time: time, end_time: time, exclude_id: int = None):
    """Zaman çakışması kontrolü"""
    query = db.query(Schedule).filter(
        Schedule.classroom == classroom,
        Schedule.date == date,
        Schedule.start_time < end_time,
        Schedule.end_time > start_time
    )
    
    if exclude_id:
        query = query.filter(Schedule.id != exclude_id)
    
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schedule conflict detected"
        )

@router.post("/", response_model=ScheduleSchema)
def create_schedule(
    current_user: Annotated[User, Depends(get_current_user)],
    schedule: ScheduleCreate,
    db: Session = Depends(get_db)
):
    """Yeni zaman planlaması oluştur"""
    check_admin_access(current_user)
    
    # Projenin varlığını kontrol et
    project = db.query(Project).filter(Project.id == schedule.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Projenin zaten planlanıp planlanmadığını kontrol et
    existing_schedule = db.query(Schedule).filter(
        Schedule.project_id == schedule.project_id
    ).first()
    if existing_schedule:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project already scheduled"
        )
    
    # Zaman çakışması kontrolü
    check_schedule_conflict(
        db, schedule.classroom, schedule.date, 
        schedule.start_time, schedule.end_time
    )
    
    db_schedule = Schedule(**schedule.model_dump())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@router.get("/", response_model=List[ScheduleSchema])
def read_schedules(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    date: datetime | None = None
):
    """Zaman planlamalarını listele"""
    query = db.query(Schedule)
    
    if date:
        query = query.filter(Schedule.date == date)
    
    schedules = query.offset(skip).limit(limit).all()
    return schedules

@router.get("/{schedule_id}", response_model=ScheduleSchema)
def read_schedule(
    schedule_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Belirli bir zaman planlamasını getir"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    return schedule

@router.put("/{schedule_id}", response_model=ScheduleSchema)
def update_schedule(
    schedule_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    schedule: ScheduleUpdate,
    db: Session = Depends(get_db)
):
    """Zaman planlaması bilgilerini güncelle"""
    check_admin_access(current_user)
    
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if db_schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    update_data = schedule.model_dump(exclude_unset=True)
    
    # Eğer zaman veya sınıf güncellemesi varsa çakışma kontrolü yap
    if any(field in update_data for field in ["classroom", "date", "start_time", "end_time"]):
        check_schedule_conflict(
            db,
            update_data.get("classroom", db_schedule.classroom),
            update_data.get("date", db_schedule.date),
            update_data.get("start_time", db_schedule.start_time),
            update_data.get("end_time", db_schedule.end_time),
            exclude_id=schedule_id
        )
    
    for field, value in update_data.items():
        setattr(db_schedule, field, value)
    
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Zaman planlamasını sil"""
    check_admin_access(current_user)
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    db.delete(schedule)
    db.commit()
    return None 