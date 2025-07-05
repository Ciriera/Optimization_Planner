from datetime import timedelta, datetime
from typing import Any
import traceback
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.utils import (
    generate_password_reset_token,
    send_reset_password_email,
    verify_password_reset_token,
)
from app.core.cache import set_cache, get_cache, delete_cache
from pydantic import BaseModel
from app.crud.user import crud_user
from app.schemas.base import TokenSchema as Token
from app.schemas.user import User as UserSchema
from app.schemas.base import Msg

router = APIRouter()

class LoginRequest(BaseModel):
    """Login isteği modeli"""
    email: str
    password: str

@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 uyumlu token alma endpoint'i.
    """
    try:
        print(f"Login attempt for user: {form_data.username}")
        
        # User'ı doğrudan CRUD ile sorgulayalım
        user = await crud_user.get_by_email(db, email=form_data.username)
        if not user:
            print(f"User not found: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Şifreyi doğrulama
        if not verify_password(form_data.password, user.hashed_password):
            print(f"Invalid password for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Token oluştur
        token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
        
        print(f"Login successful for user: {form_data.username}")
        
        return {
            "access_token": token,
            "token_type": "bearer",
        }
    except HTTPException as e:
        # HTTP istisnaları doğrudan yeniden fırlatılabilir
        raise
    except Exception as e:
        error_detail = f"Login error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        # Güvenlik nedeniyle dış kullanıcılara ayrıntılı hata mesajı göstermemeliyiz
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}"
        )

@router.post("/login/json", response_model=Token)
async def login_json(
    login_data: LoginRequest,
    db: AsyncSession = Depends(deps.get_db)
) -> Any:
    """
    JSON body ile login, test amacıyla
    """
    try:
        print(f"JSON Login attempt for user: {login_data.email}")
        
        # User'ı doğrudan CRUD ile sorgulayalım
        user = await crud_user.get_by_email(db, email=login_data.email)
        if not user:
            print(f"User not found: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Şifreyi doğrulama
        if not verify_password(login_data.password, user.hashed_password):
            print(f"Invalid password for user: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
        
        print(f"Login successful for user: {login_data.email}")
        
        return {
            "access_token": token,
            "token_type": "bearer"
        }
    except HTTPException as e:
        # HTTP istisnaları doğrudan yeniden fırlatılabilir
        raise
    except Exception as e:
        error_detail = f"Login error: {str(e)}"
        print(error_detail)
        print(traceback.format_exc())
        # Güvenlik nedeniyle dış kullanıcılara ayrıntılı hata mesajı göstermemeliyiz
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )

@router.post("/login/test-token", response_model=UserSchema)
async def test_token(current_user: User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token.
    """
    return current_user

@router.post("/password-recovery/{email}", response_model=Msg)
async def recover_password(email: str, db: AsyncSession = Depends(deps.get_db)) -> Any:
    """
    Password recovery.
    """
    user = await crud_user.get_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    send_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    return {"msg": "Password recovery email sent"}

@router.post("/reset-password/", response_model=Msg)
async def reset_password(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Reset password.
    """
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = await crud_user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    await db.commit()
    return {"msg": "Password updated successfully"}

@router.get("/test-redis")
async def test_redis_cache():
    """
    Redis önbellek bağlantısını test et.
    """
    test_key = "test_redis_key"
    test_value = {"message": "Redis bağlantısı çalışıyor!", "timestamp": str(datetime.now())}
    
    # Önbelleğe veri kaydet
    set_cache(test_key, test_value)
    
    # Önbellekten veri oku
    cached_value = get_cache(test_key)
    
    # Önbellekten veriyi sil
    delete_cache(test_key)
    
    return {
        "success": True,
        "data": {
            "test_value": test_value,
            "cached_value": cached_value,
            "cache_match": test_value == cached_value
        },
        "message": "Redis önbellek testi tamamlandı"
    }

@router.get("/test")
async def test_auth_endpoint():
    """
    Basit bir test endpoint'i.
    """
    return {
        "status": "success",
        "message": "Auth endpoint is working!",
        "timestamp": str(datetime.now())
    } 