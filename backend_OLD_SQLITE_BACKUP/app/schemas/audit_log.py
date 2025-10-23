from typing import Optional
from datetime import datetime
from pydantic import BaseModel

# Shared properties
class AuditLogBase(BaseModel):
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

# Properties to receive on AuditLog creation
class AuditLogCreate(AuditLogBase):
    user_id: Optional[int] = None

# Properties to receive on AuditLog update
class AuditLogUpdate(AuditLogBase):
    pass

# Properties shared by models stored in DB
class AuditLogInDBBase(AuditLogBase):
    id: int
    user_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

# Properties to return to client
class AuditLog(AuditLogInDBBase):
    pass

# Properties stored in DB
class AuditLogInDB(AuditLogInDBBase):
    pass 