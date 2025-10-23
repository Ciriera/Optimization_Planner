from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole

# Ortak özellikler
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    role: Optional[UserRole] = None
    language: Optional[str] = "tr"
    username: Optional[str] = None
    is_superuser: Optional[bool] = False

# Veritabanından okunan kullanıcı
class User(UserBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True
        populate_by_name = True

# Yeni kullanıcı oluşturmak için
class UserCreate(UserBase):
    email: EmailStr
    password: str
    full_name: str
    username: str

# Kullanıcı güncellemek için
class UserUpdate(UserBase):
    password: Optional[str] = None

# Kullanıcı yetkisini değiştirmek için
class UserRoleUpdate(BaseModel):
    role: UserRole

# Kullanıcı dilini değiştirmek için
class UserLanguageUpdate(BaseModel):
    language: str

# Token şeması
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None 