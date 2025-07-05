from typing import List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate, AuditLogUpdate

class CRUDAuditLog(CRUDBase[AuditLog, AuditLogCreate, AuditLogUpdate]):
    async def get_by_user_id(
        self, db: AsyncSession, *, user_id: int
    ) -> List[AuditLog]:
        result = await db.execute(
            select(AuditLog).where(AuditLog.user_id == user_id)
        )
        return result.scalars().all()

    async def get_by_date_range(
        self,
        db: AsyncSession,
        *,
        start_date: datetime,
        end_date: datetime
    ) -> List[AuditLog]:
        result = await db.execute(
            select(AuditLog).where(
                AuditLog.created_at >= start_date,
                AuditLog.created_at <= end_date
            )
        )
        return result.scalars().all()

crud_audit_log = CRUDAuditLog(AuditLog)

async def create_audit_log(
    db: AsyncSession,
    *,
    user_id: Optional[int] = None,
    action: str,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditLog:
    audit_log_in = AuditLogCreate(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    return await crud_audit_log.create(db, obj_in=audit_log_in) 