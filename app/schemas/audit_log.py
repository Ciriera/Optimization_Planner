"""
Denetim günlüğü şemaları
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# Shared properties
class AuditLogBase(BaseModel):
    """Denetim günlüğü temel şeması"""
    action: str
    resource_type: str
    resource_id: int
    details: Optional[Dict[str, Any]] = None


# Properties to receive on audit log creation
class AuditLogCreate(AuditLogBase):
    """Denetim günlüğü oluşturma şeması"""
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None


# Properties to receive on audit log update
class AuditLogUpdate(AuditLogBase):
    """Denetim günlüğü güncelleme şeması"""
    pass


# Properties shared by models stored in DB
class AuditLogInDBBase(AuditLogBase):
    """Veritabanındaki denetim günlüğü temel şeması"""
    id: int
    user_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Properties to return to client
class AuditLog(AuditLogInDBBase):
    """Denetim günlüğü şeması"""
    pass


# Properties stored in DB
class AuditLogInDB(AuditLogInDBBase):
    """Veritabanındaki denetim günlüğü şeması"""
    pass


# Properties for search
class AuditLogSearch(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class AuditLogFilter(BaseModel):
    """Schema for filtering audit logs"""
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0 