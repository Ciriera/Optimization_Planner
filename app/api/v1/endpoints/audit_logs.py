from typing import List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.schemas.audit_log import AuditLog, AuditLogFilter
from app.core.config import settings
from app.crud.audit_log import crud_audit_log

router = APIRouter()


@router.get("/", response_model=List[schemas.AuditLog])
async def read_audit_logs(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve audit logs.
    Only superusers can access this endpoint.
    """
    filters = AuditLogFilter(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date,
        offset=skip,
        limit=limit
    )
    
    audit_logs = await crud_audit_log.get_audit_logs(db=db, filters=filters)
    return audit_logs


@router.get("/count", response_model=int)
async def count_audit_logs(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Any:
    """
    Count audit logs with filters.
    Only superusers can access this endpoint.
    """
    filters = AuditLogFilter(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date
    )
    
    count = await crud_audit_log.get_audit_logs_count(db=db, filters=filters)
    return count


@router.get("/{audit_log_id}", response_model=schemas.AuditLog)
async def read_audit_log(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    audit_log_id: int,
) -> Any:
    """
    Get a specific audit log by ID.
    Only superusers can access this endpoint.
    """
    audit_log = await crud_audit_log.get_audit_log(db=db, audit_log_id=audit_log_id)
    if not audit_log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return audit_log 