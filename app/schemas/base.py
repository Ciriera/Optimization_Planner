from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BaseUserSchema(BaseSchema):
    email: EmailStr
    full_name: str
    is_active: bool = True

class TokenSchema(BaseSchema):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseSchema):
    sub: Optional[str] = None

class Msg(BaseSchema):
    msg: str 