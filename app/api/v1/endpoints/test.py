from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.services.auth import AuthService
from app.models.user import User
from app.models.instructor import Instructor
from app.models.project import Project
from app.models.classroom import Classroom
from app.models.timeslot import TimeSlot
from app.models.schedule import Schedule
from app.models.algorithm import AlgorithmRun
from app.models.audit_log import AuditLog

router = APIRouter()

@router.get("/")
async def test_endpoint():
    """
    Basit bir test endpoint'i.
    """
    return {
        "status": "success",
        "message": "Test endpoint is working!",
    }

@router.get("/db")
async def test_db(db: AsyncSession = Depends(get_db)):
    """
    Veritabanı bağlantısını test et.
    """
    try:
        # Kullanıcı sayısı
        user_result = await db.execute(select(User))
        users = user_result.scalars().all()
        
        # Öğretim üyesi sayısı
        instructor_result = await db.execute(select(Instructor))
        instructors = instructor_result.scalars().all()
        
        # Proje sayısı
        project_result = await db.execute(select(Project))
        projects = project_result.scalars().all()
        
        # Sınıf sayısı
        classroom_result = await db.execute(select(Classroom))
        classrooms = classroom_result.scalars().all()
        
        # Zaman dilimi sayısı
        timeslot_result = await db.execute(select(TimeSlot))
        timeslots = timeslot_result.scalars().all()
        
        # Program sayısı
        schedule_result = await db.execute(select(Schedule))
        schedules = schedule_result.scalars().all()
        
        # Algoritma çalıştırma sayısı
        algorithm_result = await db.execute(select(AlgorithmRun))
        algorithms = algorithm_result.scalars().all()
        
        # Denetim kaydı sayısı
        audit_result = await db.execute(select(AuditLog))
        audit_logs = audit_result.scalars().all()
        
        return {
            "status": "success",
            "message": "Database connection is working!",
            "data": {
                "users": len(users),
                "instructors": len(instructors),
                "projects": len(projects),
                "classrooms": len(classrooms),
                "timeslots": len(timeslots),
                "schedules": len(schedules),
                "algorithms": len(algorithms),
                "audit_logs": len(audit_logs)
            }
        }
    except Exception as e:
        print(f"Database test error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database test error: {str(e)}"
        )
