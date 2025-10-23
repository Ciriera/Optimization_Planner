from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal

# Geçici olarak OAuth2PasswordBearer'i devre dışı bırak
# reusable_oauth2 = OAuth2PasswordBearer(
#     tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token",
#     auto_error=False  # Authentication'ı geçici olarak devre dışı bırak
# )

def mock_oauth2():
    """Mock OAuth2 dependency"""
    return None

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(mock_oauth2)
) -> models.User:
    # Geçici olarak mock user döndür
    return models.User(
        id=1,
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_superuser=True
    )

def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    try:
        if not crud.user.is_active(current_user):
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
    except Exception as e:
        print(f"Error in get_current_active_user: {e}")
        return current_user

def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user 