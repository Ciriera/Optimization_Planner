"""
API endpoints for calendar integration
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.services.calendar_service import CalendarService
from app.models.user import User

router = APIRouter()

@router.get("/")
async def get_calendar_status() -> Dict[str, Any]:
    """
    Public calendar status endpoint for testing
    """
    return {
        "status": "success",
        "message": "Calendar service is working",
        "synced_events": 0,
        "pending_sync": 0
    }


@router.post("/create-event")
async def create_calendar_event(
    event_data: Dict[str, Any],
    calendar_type: str = "google",
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Create a calendar event.
    """
    try:
        service = CalendarService()
        result = service.create_calendar_event(event_data, calendar_type)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calendar event creation failed: {str(e)}"
        )


@router.post("/create-schedule-events")
async def create_schedule_events(
    schedule_data: List[Dict[str, Any]],
    calendar_type: str = "google",
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Create multiple calendar events for a complete schedule.
    """
    try:
        service = CalendarService()
        result = service.create_schedule_events(schedule_data, calendar_type)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch calendar event creation failed: {str(e)}"
        )


@router.post("/sync-calendar")
async def sync_with_external_calendar(
    events: List[Dict[str, Any]],
    calendar_type: str = "google",
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Sync events with external calendar system.
    """
    try:
        service = CalendarService()
        result = service.sync_with_external_calendar(events, calendar_type)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calendar synchronization failed: {str(e)}"
        )


@router.post("/export-ical")
async def export_to_ical(
    events: List[Dict[str, Any]],
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Export events to iCal format.
    """
    try:
        service = CalendarService()
        ical_content = service.export_to_ical(events)
        
        return {
            "status": "success",
            "ical_content": ical_content,
            "content_type": "text/calendar"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"iCal export failed: {str(e)}"
        )


@router.get("/calendar-settings")
async def get_calendar_settings() -> Dict[str, Any]:
    """
    Get calendar integration settings and capabilities.
    """
    try:
        service = CalendarService()
        settings = service.get_calendar_settings()
        
        return {
            "status": "success",
            "settings": settings
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get calendar settings: {str(e)}"
        )
