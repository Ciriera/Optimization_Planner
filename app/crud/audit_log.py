from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate, AuditLogUpdate, AuditLogFilter


class CRUDAuditLog(CRUDBase[AuditLog, AuditLogCreate, AuditLogUpdate]):
    """
    Audit log için CRUD işlemleri.
    """
    
    async def get_by_user_id(
        self, db: AsyncSession, *, user_id: int
    ) -> List[AuditLog]:
        """Kullanıcı ID'sine göre denetim günlüklerini getirir."""
        result = await db.execute(
            select(AuditLog).where(AuditLog.user_id == user_id)
        )
        return result.scalars().all()
    
    async def get_by_action(
        self, db: AsyncSession, *, action: str
    ) -> List[AuditLog]:
        """İşlem türüne göre denetim günlüklerini getirir."""
        query = select(self.model).where(self.model.action == action)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_date_range(
        self,
        db: AsyncSession,
        *,
        start_date: str,
        end_date: str
    ) -> List[AuditLog]:
        """Tarih aralığına göre denetim günlüklerini getirir."""
        try:
            # Convert string dates to datetime objects if they are strings
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
                
            print(f"Querying logs between {start_date} and {end_date}")
            
            # Get all logs first to debug
            debug_result = await db.execute(select(AuditLog))
            all_logs = debug_result.scalars().all()
            print(f"Total logs in database: {len(all_logs)}")
            for log in all_logs:
                print(f"Log ID: {log.id}, Created At: {log.created_at}")
            
            # Query with between operator
            result = await db.execute(
                select(AuditLog).where(
                    AuditLog.created_at.between(start_date, end_date)
                )
            )
            logs = result.scalars().all()
            print(f"Found {len(logs)} logs in date range")
            return logs
        except Exception as e:
            print(f"Error in get_by_date_range: {str(e)}")
            return []
    
    async def get_by_user(
        self, db: AsyncSession, *, user_id: int
    ) -> List[AuditLog]:
        """Kullanıcı ID'sine göre denetim günlüklerini getirir."""
        result = await db.execute(
            select(AuditLog).where(AuditLog.user_id == user_id)
        )
        return result.scalars().all()
    
    async def get_by_resource_type(
        self, db: AsyncSession, *, resource_type: str
    ) -> List[AuditLog]:
        """Kaynak türüne göre denetim günlüklerini getirir."""
        result = await db.execute(
            select(AuditLog).where(AuditLog.resource_type == resource_type)
        )
        return result.scalars().all()
    
    async def get_by_resource(
        self, db: AsyncSession, *, resource_type: str, resource_id: Optional[int] = None, 
        skip: int = 0, limit: int = 100
    ) -> List[AuditLog]:
        """
        Belirli bir kaynak türüne göre audit logları getirir.
        """
        filters = [self.model.resource_type == resource_type]
        if resource_id:
            filters.append(self.model.resource_id == resource_id)
            
        result = await db.execute(
            select(self.model)
            .filter(and_(*filters))
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def search(
        self, db: AsyncSession, *,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Çeşitli kriterlere göre audit logları arar.
        """
        filters = []
        
        if user_id:
            filters.append(self.model.user_id == user_id)
        
        if action:
            filters.append(self.model.action == action)
        
        if resource_type:
            filters.append(self.model.resource_type == resource_type)
        
        if resource_id:
            filters.append(self.model.resource_id == resource_id)
        
        if start_date:
            filters.append(self.model.created_at >= start_date)
        
        if end_date:
            filters.append(self.model.created_at <= end_date)
        
        result = await db.execute(
            select(self.model)
            .filter(and_(*filters))
            .order_by(desc(self.model.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: AuditLogCreate) -> AuditLog:
        """
        AuditLog kaydı oluştur.
        """
        from fastapi.encoders import jsonable_encoder
        
        # Objeyi dict'e çevir
        obj_data = jsonable_encoder(obj_in)
        
        # created_at değeri string ise çıkar, model varsayılanı kullansın
        if "created_at" in obj_data and isinstance(obj_data["created_at"], str):
            del obj_data["created_at"]
            
        # Modeli oluştur ve kaydet
        db_obj = AuditLog(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_user_logs(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Kullanıcının denetim günlüğü kayıtlarını getir"""
        result = await db.execute(
            select(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_resource_logs(
        self,
        db: AsyncSession,
        *,
        resource: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Belirli bir kaynağın denetim günlüğü kayıtlarını getir"""
        result = await db.execute(
            select(AuditLog)
            .filter(AuditLog.resource == resource)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_action_logs(
        self,
        db: AsyncSession,
        *,
        action: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Belirli bir işlemin denetim günlüğü kayıtlarını getir"""
        result = await db.execute(
            select(AuditLog)
            .filter(AuditLog.action == action)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_logs_by_date_range(
        self,
        db: AsyncSession,
        *,
        start_date: str,
        end_date: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Tarih aralığına göre denetim günlüğü kayıtlarını getir"""
        try:
            # Convert string dates to datetime objects if they are strings
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)

            result = await db.execute(
                select(AuditLog)
                .filter(AuditLog.created_at.between(start_date, end_date))
                .order_by(AuditLog.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            print(f"Error in get_logs_by_date_range: {str(e)}")
            return []


crud_audit_log = CRUDAuditLog(AuditLog)


async def create_audit_log(db: AsyncSession, obj_in: AuditLogCreate) -> AuditLog:
    """
    Create a new audit log entry.
    """
    db_obj = AuditLog(
        user_id=obj_in.user_id,
        action=obj_in.action,
        entity_type=obj_in.entity_type,
        entity_id=obj_in.entity_id,
        details=obj_in.details,
        ip_address=obj_in.ip_address
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_audit_logs(
    db: AsyncSession,
    filters: AuditLogFilter
) -> List[AuditLog]:
    """
    Get audit logs with filters.
    """
    query = select(AuditLog)
    
    if filters.user_id is not None:
        query = query.filter(AuditLog.user_id == filters.user_id)
    
    if filters.action:
        query = query.filter(AuditLog.action == filters.action)
    
    if filters.entity_type:
        query = query.filter(AuditLog.entity_type == filters.entity_type)
    
    if filters.entity_id is not None:
        query = query.filter(AuditLog.entity_id == filters.entity_id)
    
    if filters.start_date:
        query = query.filter(AuditLog.created_at >= filters.start_date)
    
    if filters.end_date:
        query = query.filter(AuditLog.created_at <= filters.end_date)
    
    # Order by timestamp descending (newest first)
    query = query.order_by(AuditLog.created_at.desc())
    
    # Apply pagination
    query = query.offset(filters.offset).limit(filters.limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_audit_logs_count(
    db: AsyncSession,
    filters: AuditLogFilter
) -> int:
    """
    Count audit logs with filters.
    """
    query = select(AuditLog)
    
    if filters.user_id is not None:
        query = query.filter(AuditLog.user_id == filters.user_id)
    
    if filters.action:
        query = query.filter(AuditLog.action == filters.action)
    
    if filters.entity_type:
        query = query.filter(AuditLog.entity_type == filters.entity_type)
    
    if filters.entity_id is not None:
        query = query.filter(AuditLog.entity_id == filters.entity_id)
    
    if filters.start_date:
        query = query.filter(AuditLog.created_at >= filters.start_date)
    
    if filters.end_date:
        query = query.filter(AuditLog.created_at <= filters.end_date)
    
    # Count the results
    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    return result.scalar_one()


async def get_audit_log(db: AsyncSession, audit_log_id: int) -> Optional[AuditLog]:
    """
    Get a specific audit log by ID.
    """
    result = await db.execute(select(AuditLog).filter(AuditLog.id == audit_log_id))
    return result.scalar_one_or_none() 