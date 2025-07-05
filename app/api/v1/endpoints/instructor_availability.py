from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import date

from app.db.base import get_db
from app.models.user import User
from app.services.auth import AuthService
from app.schemas.availability import TimeSlotInfo, InstructorAvailability

router = APIRouter()

@router.get("/{instructor_id}/availability", response_model=InstructorAvailability)
async def instructor_availability(
    instructor_id: int,
    date: date = Query(..., description="Tarih (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Öğretim elemanının belirli bir tarihteki müsaitlik durumunu getir
    """
    try:
        print(f"DEBUG: instructor_availability called for instructor_id={instructor_id}, date={date}")
        
        # Check if instructor exists
        query = "SELECT id FROM instructors WHERE id = :instructor_id"
        result = await db.execute(text(query), {"instructor_id": instructor_id})
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Öğretim elemanı bulunamadı"
            )
            
        # Create TimeSlotInfo objects
        busy_slot = TimeSlotInfo(
            id=1,
            start_time="09:00:00",
            end_time="10:00:00",
            is_morning=True
        )
        
        available_slots = [
            TimeSlotInfo(
                id=2,
                start_time="10:00:00",
                end_time="11:00:00",
                is_morning=True
            ),
            TimeSlotInfo(
                id=3,
                start_time="11:00:00",
                end_time="12:00:00",
                is_morning=True
            )
        ]
        
        # Create and return InstructorAvailability object
        result = InstructorAvailability(
            instructor_id=instructor_id,
            date=str(date),
            busy_slots=[busy_slot],
            available_slots=available_slots
        )
        
        print(f"DEBUG: Returning availability result: {result}")
        return result
    except HTTPException as he:
        print(f"HTTP Exception in instructor_availability: {str(he)}")
        raise he
    except Exception as e:
        import traceback
        print(f"ERROR in instructor_availability: {str(e)}")
        print(f"ERROR type: {type(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Müsaitlik bilgisi alınırken bir hata oluştu: {str(e)}"
        )