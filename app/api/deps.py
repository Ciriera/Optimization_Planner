from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import crud_user
from app import schemas
from app.core import security
from app.core.config import settings
from app.db.base import async_session
from app.models.user import User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token"
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Veritabanı oturumu bağımlılığı.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    """
    Mevcut kullanıcıyı getir.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = await crud_user.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Aktif kullanıcıyı getir.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Aktif süper kullanıcıyı getir.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user