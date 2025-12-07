"""
Notification API endpoints for sending instructor exam planner notifications.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models import User, NotificationStatus
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService


class CustomEmailRequest(BaseModel):
    """Request model for custom email notification"""
    email: EmailStr
    recipient_name: str = "TEST_ADMIN"

router = APIRouter()


@router.get("/preview/global")
async def preview_global_planner(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get global planner preview for notification page.
    Returns the current planner data structure.
    """
    service = NotificationService()
    result = await service.get_global_planner_preview(db)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get planner preview"))
    
    return result


@router.get("/preview/instructor/{instructor_id}")
async def preview_instructor_notification(
    *,
    instructor_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get personalized preview for a specific instructor.
    Shows what email content will be sent to this instructor.
    """
    service = NotificationService()
    result = await service.get_instructor_preview(instructor_id, db)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get instructor preview"))
    
    return result


@router.post("/send/all")
async def send_notifications_to_all(
    *,
    dry_run: bool = Query(False, description="If true, don't actually send emails"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send notification emails to all instructors with email addresses.
    Requires admin privileges.
    """
    # Check if user is admin
    if not (current_user.is_superuser or current_user.role.value == "admin"):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    service = NotificationService()
    result = await service.send_notifications_to_all(db, dry_run=dry_run)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to send notifications"))
    
    return result


@router.post("/send/test")
async def send_test_email(
    *,
    admin_email: str = Query("cavuldak-eren@hotmail.com", description="Admin email for test"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send a test email to verify email configuration.
    """
    email_service = EmailService()
    result = email_service.send_test_email(admin_email)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to send test email"))
    
    return {
        "success": True,
        "message": f"Test email sent to {admin_email}",
    }


@router.post("/send/custom-email")
async def send_notification_to_custom_email(
    *,
    request: CustomEmailRequest = Body(...),
    dry_run: bool = Query(False, description="If true, don't actually send email"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send notification email to a custom email address (e.g., TEST_ADMIN).
    Includes the full planner calendar.
    """
    service = NotificationService()
    result = await service.send_notification_to_custom_email(
        email=request.email,
        recipient_name=request.recipient_name,
        db=db,
        dry_run=dry_run,
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to send notification"))
    
    return result


@router.post("/send/{instructor_id}")
async def send_notification_to_instructor(
    *,
    instructor_id: int,
    dry_run: bool = Query(False, description="If true, don't actually send email"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Send notification email to a specific instructor.
    """
    service = NotificationService()
    result = await service.send_notification_to_instructor(instructor_id, db, dry_run=dry_run)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to send notification"))
    
    return result


@router.get("/logs")
async def get_notification_logs(
    *,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Filter by status: pending, success, error, failed"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get notification logs with pagination and optional status filtering.
    """
    service = NotificationService()
    
    # Convert status string to enum if provided
    status_enum = None
    if status:
        try:
            status_enum = NotificationStatus(status.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    result = await service.get_notification_logs(db, limit=limit, offset=offset, status=status_enum)
    
    # If table doesn't exist yet (migration not run), return empty logs instead of error
    if not result.get("success") and "does not exist" in str(result.get("error", "")):
        return {
            "success": True,
            "logs": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
        }
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to get logs"))
    
    return result


@router.post("/migrate")
async def run_notification_migration(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Run notification migration manually.
    Adds email column to instructors and creates notification_logs table.
    Requires admin privileges.
    """
    # Check if user is admin
    if not (current_user.is_superuser or current_user.role.value == "admin"):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    try:
        from sqlalchemy import text
        
        # Add email column to instructors table
        await db.execute(text("ALTER TABLE instructors ADD COLUMN IF NOT EXISTS email VARCHAR(200)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_instructors_email ON instructors(email)"))
        
        # Create notificationstatus enum type
        await db.execute(text("""
            DO $$ BEGIN
                CREATE TYPE notificationstatus AS ENUM ('pending', 'success', 'error', 'failed');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
        # Create notification_logs table
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS notification_logs (
                id SERIAL PRIMARY KEY,
                instructor_id INTEGER NOT NULL,
                instructor_email VARCHAR(200) NOT NULL,
                instructor_name VARCHAR(200),
                planner_timestamp TIMESTAMP,
                subject VARCHAR(500),
                status notificationstatus NOT NULL,
                error_message TEXT,
                sent_at TIMESTAMP,
                attempt_count INTEGER,
                meta_data JSONB,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                CONSTRAINT fk_notification_logs_instructor_id FOREIGN KEY (instructor_id) REFERENCES instructors(id)
            )
        """))
        
        # Create indexes
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_id ON notification_logs(id)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_instructor_id ON notification_logs(instructor_id)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_instructor_email ON notification_logs(instructor_email)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_status ON notification_logs(status)"))
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Migration completed successfully!",
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Migration failed: {str(e)}")

