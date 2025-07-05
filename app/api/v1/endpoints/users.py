from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.db.base import get_db
from app.i18n import translate as _
from app.services.auth import AuthService

router = APIRouter()
auth_service = AuthService()

@router.post("/", response_model=schemas.User)
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Yeni kullanıcı oluşturma (admin yetkisi gereklidir)
    """
    user = await auth_service.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail=_("user.email_exists", locale=current_user.language),
        )
    
    user = await auth_service.create_user(db, user_in=user_in)
    return user


@router.get("/", response_model=List[schemas.User])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Kullanıcıları listele (admin yetkisi gereklidir)
    """
    users = await auth_service.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/me", response_model=schemas.User)
async def read_user_me(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Aktif kullanıcıyı getir
    """
    return current_user


@router.put("/me", response_model=schemas.User)
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Aktif kullanıcıyı güncelle
    """
    user = await auth_service.update_user(db, db_obj=current_user, obj_in=user_in)
    return user


@router.get("/{user_id}", response_model=schemas.User)
async def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Belirli bir kullanıcıyı getir
    """
    user = await auth_service.get_user(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=_("user.not_found", locale=current_user.language),
        )
    
    if user.id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=400,
            detail=_("user.not_enough_permissions", locale=current_user.language),
        )
    
    return user


@router.put("/{user_id}", response_model=schemas.User)
async def update_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Belirli bir kullanıcıyı güncelle (admin yetkisi gereklidir)
    """
    user = await auth_service.get_user(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=_("user.not_found", locale=current_user.language),
        )
    
    user = await auth_service.update_user(db, db_obj=user, obj_in=user_in)
    return user


@router.patch("/{user_id}/role", response_model=schemas.User)
async def update_user_role(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    role_update: schemas.UserRoleUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Belirli bir kullanıcının rolünü güncelle (admin yetkisi gereklidir)
    """
    user = await auth_service.get_user(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=_("user.not_found", locale=current_user.language),
        )
    
    user = await auth_service.update_user_role(db, db_obj=user, role=role_update.role)
    return user


@router.patch("/me/language", response_model=schemas.User)
async def update_user_language(
    *,
    db: AsyncSession = Depends(get_db),
    language_update: schemas.UserLanguageUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Aktif kullanıcının dil tercihini güncelle
    """
    # Desteklenen dilleri kontrol et
    if language_update.language not in settings.SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=_("user.unsupported_language", locale=current_user.language),
        )
    
    user = await auth_service.update_user_language(
        db, db_obj=current_user, language=language_update.language
    )
    return user 