from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.AuditLog])
def read_audit_logs(
    db: Session = Depends(deps.get_db),
    skip: int = 0, 
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve audit logs.
    """
    logs = crud.audit_log.get_multi(db, skip=skip, limit=limit)
    return logs


@router.get("/{id}", response_model=schemas.AuditLog)
def read_audit_log(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get audit log by ID.
    """
    log = crud.audit_log.get(db, id=id)
    if not log:
        raise HTTPException(
            status_code=404,
            detail="Audit log not found",
        )
    return log 