from datetime import timedelta
from typing import Any
import traceback
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.core import security
from app.core.config import settings
from app.services.auth import AuthService
from app.crud.user import crud_user
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    """Login isteği modeli"""
    email: str
    password: str

@router.post("/login/access-token", response_model=dict)
async def login_access_token(
    request: Request,
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    try:
        print(f"Login attempt for user: {form_data.username}")
        
        # User'ı doğrudan CRUD ile sorgulayalım
        user = await crud_user.get_by_email(db, email=form_data.username)
        if not user:
            print(f"User not found: {form_data.username}")
            raise HTTPException(
                status_code=400, detail="Incorrect email or password"
            )
        
        # Şifreyi doğrulama
        if not security.verify_password(form_data.password, user.hashed_password):
            print(f"Invalid password for user: {form_data.username}")
            raise HTTPException(
                status_code=400, detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=400, detail="Inactive user"
            )
        
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        token = security.create_access_token(
            {"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        print(f"Login successful for user: {form_data.username}")
        
        return {
            "access_token": token,
            "token_type": "bearer"
        }
    except HTTPException as e:
        # HTTP istisnaları doğrudan yeniden fırlatılabilir
        raise
    except Exception as e:
        error_detail = f"Login error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        # Güvenlik nedeniyle dış kullanıcılara ayrıntılı hata mesajı göstermemeliyiz
        raise HTTPException(
            status_code=500, detail=f"Login error: {str(e)}"
        )

@router.post("/login/json", response_model=dict)
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
                status_code=400, detail="Incorrect email or password"
            )
        
        # Şifreyi doğrulama
        if not security.verify_password(login_data.password, user.hashed_password):
            print(f"Invalid password for user: {login_data.email}")
            raise HTTPException(
                status_code=400, detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=400, detail="Inactive user"
            )
        
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        token = security.create_access_token(
            {"sub": str(user.id)}, expires_delta=access_token_expires
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
        error_detail = f"Login error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        # Güvenlik nedeniyle dış kullanıcılara ayrıntılı hata mesajı göstermemeliyiz
        raise HTTPException(
            status_code=500, detail=f"Login error: {str(e)}"
        )

@router.post("/login/test-token", response_model=dict)
async def test_token(current_user: dict = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    return current_user 