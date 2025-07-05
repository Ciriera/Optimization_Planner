from typing import Dict, Any, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
import json

from app import crud, models, schemas
from app.crud.audit_log import create_audit_log
from app.schemas.audit_log import AuditLogCreate
from app.models.user import User


async def log_activity(
    db: AsyncSession,
    user_id: Optional[int],
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    request: Optional[Request] = None,
    details: Optional[Dict[str, Any]] = None,
) -> models.AuditLog:
    """
    Kullanıcı aktivitesini loglar.
    
    Args:
        db: Veritabanı oturumu
        user_id: Kullanıcı ID
        action: İşlem türü (create, update, delete, login, etc.)
        resource_type: Kaynak türü (instructor, project, schedule, etc.)
        resource_id: Kaynak ID
        request: İstek nesnesi
        details: Ek detaylar
        
    Returns:
        Oluşturulan audit log kaydı
    """
    # İstek bilgilerini al
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
    
    # Audit log oluştur
    audit_log = models.AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )
    
    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)
    
    return audit_log


async def log_login(db: AsyncSession, user_id: int, request: Request, success: bool) -> models.AuditLog:
    """
    Kullanıcı girişini loglar.
    
    Args:
        db: Veritabanı oturumu
        user_id: Kullanıcı ID
        request: İstek nesnesi
        success: Giriş başarılı mı?
        
    Returns:
        Oluşturulan audit log kaydı
    """
    return await log_activity(
        db=db,
        user_id=user_id,
        action="login",
        resource_type="user",
        resource_id=user_id,
        request=request,
        details={"success": success}
    )


async def log_logout(db: AsyncSession, user_id: int, request: Request) -> models.AuditLog:
    """
    Kullanıcı çıkışını loglar.
    
    Args:
        db: Veritabanı oturumu
        user_id: Kullanıcı ID
        request: İstek nesnesi
        
    Returns:
        Oluşturulan audit log kaydı
    """
    return await log_activity(
        db=db,
        user_id=user_id,
        action="logout",
        resource_type="user",
        resource_id=user_id,
        request=request
    )


async def log_create(
    db: AsyncSession,
    user_id: int,
    resource_type: str,
    resource_id: int,
    request: Optional[Request] = None,
    data: Optional[Dict[str, Any]] = None
) -> models.AuditLog:
    """
    Kaynak oluşturma işlemini loglar.
    
    Args:
        db: Veritabanı oturumu
        user_id: Kullanıcı ID
        resource_type: Kaynak türü
        resource_id: Kaynak ID
        request: İstek nesnesi
        data: Oluşturulan veri
        
    Returns:
        Oluşturulan audit log kaydı
    """
    return await log_activity(
        db=db,
        user_id=user_id,
        action="create",
        resource_type=resource_type,
        resource_id=resource_id,
        request=request,
        details={"data": data} if data else None
    )


async def log_update(
    db: AsyncSession,
    user_id: int,
    resource_type: str,
    resource_id: int,
    request: Optional[Request] = None,
    old_data: Optional[Dict[str, Any]] = None,
    new_data: Optional[Dict[str, Any]] = None
) -> models.AuditLog:
    """
    Kaynak güncelleme işlemini loglar.
    
    Args:
        db: Veritabanı oturumu
        user_id: Kullanıcı ID
        resource_type: Kaynak türü
        resource_id: Kaynak ID
        request: İstek nesnesi
        old_data: Eski veri
        new_data: Yeni veri
        
    Returns:
        Oluşturulan audit log kaydı
    """
    return await log_activity(
        db=db,
        user_id=user_id,
        action="update",
        resource_type=resource_type,
        resource_id=resource_id,
        request=request,
        details={
            "old_data": old_data,
            "new_data": new_data
        } if old_data and new_data else None
    )


async def log_delete(
    db: AsyncSession,
    user_id: int,
    resource_type: str,
    resource_id: int,
    request: Optional[Request] = None,
    data: Optional[Dict[str, Any]] = None
) -> models.AuditLog:
    """
    Kaynak silme işlemini loglar.
    
    Args:
        db: Veritabanı oturumu
        user_id: Kullanıcı ID
        resource_type: Kaynak türü
        resource_id: Kaynak ID
        request: İstek nesnesi
        data: Silinen veri
        
    Returns:
        Oluşturulan audit log kaydı
    """
    return await log_activity(
        db=db,
        user_id=user_id,
        action="delete",
        resource_type=resource_type,
        resource_id=resource_id,
        request=request,
        details={"data": data} if data else None
    )


class AuditService:
    """
    Service for audit logging functionality.
    """
    
    @staticmethod
    async def log_action(
        db: AsyncSession,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        details: Optional[str] = None,
        user: Optional[User] = None,
        request: Optional[Request] = None
    ) -> models.AuditLog:
        """
        Log an action performed by a user.
        
        Args:
            db: Database session
            action: The action performed (e.g., "login", "create_project", "update_assignment")
            entity_type: The type of entity affected (e.g., "user", "project", "assignment")
            entity_id: The ID of the entity affected
            details: Additional details about the action
            user: The user who performed the action
            request: The FastAPI request object
        """
        # Get the user ID if a user is provided
        user_id = user.id if user else None
        
        # Get the client IP address and user agent
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        # Create the audit log entry
        audit_log = models.AuditLog(
            user_id=user_id,
            action=action,
            resource_type=entity_type,
            resource_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"details": details} if details else None
        )
        
        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)
        
        return audit_log
    
    @staticmethod
    async def log_login(
        db: AsyncSession, 
        user: User, 
        success: bool,
        request: Optional[Request] = None
    ) -> models.AuditLog:
        """Log a user login attempt"""
        return await AuditService.log_action(
            db=db,
            action="login",
            entity_type="user",
            entity_id=user.id,
            details=json.dumps({"success": success}),
            user=user,
            request=request
        )
    
    @staticmethod
    async def log_create(
        db: AsyncSession,
        entity_type: str,
        entity_id: int,
        data: Dict[str, Any],
        user: Optional[User] = None,
        request: Optional[Request] = None
    ) -> models.AuditLog:
        """Log a creation action"""
        return await AuditService.log_action(
            db=db,
            action="create",
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps({"data": data}),
            user=user,
            request=request
        )
    
    @staticmethod
    async def log_update(
        db: AsyncSession,
        entity_type: str,
        entity_id: int,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        user: Optional[User] = None,
        request: Optional[Request] = None
    ) -> models.AuditLog:
        """Log an update action"""
        return await AuditService.log_action(
            db=db,
            action="update",
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps({
                "old_data": old_data,
                "new_data": new_data
            }),
            user=user,
            request=request
        )
    
    @staticmethod
    async def log_delete(
        db: AsyncSession,
        entity_type: str,
        entity_id: int,
        data: Dict[str, Any],
        user: Optional[User] = None,
        request: Optional[Request] = None
    ) -> models.AuditLog:
        """Log a deletion action"""
        return await AuditService.log_action(
            db=db,
            action="delete",
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps({"data": data}),
            user=user,
            request=request
        )


# Create a singleton instance
audit_service = AuditService() 