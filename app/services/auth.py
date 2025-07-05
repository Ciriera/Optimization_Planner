from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from app.core.config import settings
from app.db.base import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate
from app.core import security

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token")

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Şifre doğrulama"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Şifre hash'leme"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        subject: Union[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        JWT erişim tokenı oluşturur.
        
        Args:
            subject: Token konusu (genellikle kullanıcı ID)
            expires_delta: Token süresi
            
        Returns:
            str: JWT token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Kullanıcı kimlik doğrulama"""
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
        """Yeni kullanıcı oluşturma"""
        db_user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            role=user_in.role,
            hashed_password=AuthService.get_password_hash(user_in.password)
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def get_current_user(
        db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
    ) -> User:
        """
        JWT tokendan aktif kullanıcıyı getirir.
        
        Args:
            db: Veritabanı oturumu
            token: JWT token
            
        Returns:
            models.User: Aktif kullanıcı
            
        Raises:
            HTTPException: Geçersiz token, geçersiz yetki veya kullanıcı bulunamazsa
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            
            # Extract email from token
            email: str = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Could not validate credentials",
                )
            
            # Get user by email
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            user = result.scalars().first()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
                
            # Add role to token data for easier access
            if hasattr(user, "role"):
                payload["role"] = user.role
                
            return user
            
        except (JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )

    @staticmethod
    async def get_current_active_user(
        current_user: User = Depends(get_current_user),
    ) -> User:
        """
        Aktif kullanıcıyı getirir ve aktif olup olmadığını kontrol eder.
        
        Args:
            current_user: Aktif kullanıcı
            
        Returns:
            models.User: Aktif kullanıcı
            
        Raises:
            HTTPException: Kullanıcı aktif değilse
        """
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user

    @staticmethod
    async def get_current_active_superuser(
        current_user: User = Depends(get_current_user),
    ) -> User:
        """
        Aktif admin kullanıcısını getirir.
        
        Args:
            current_user: Aktif kullanıcı
            
        Returns:
            models.User: Aktif admin kullanıcısı
            
        Raises:
            HTTPException: Kullanıcı admin değilse
        """
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return current_user

    @staticmethod
    async def get_user(db: AsyncSession, id: int) -> Optional[User]:
        """
        ID'ye göre kullanıcı getirir.
        
        Args:
            db: Veritabanı oturumu
            id: Kullanıcı ID
            
        Returns:
            Optional[models.User]: Kullanıcı nesnesi veya None
        """
        stmt = select(User).where(User.id == id)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        Email'e göre kullanıcı getirir.
        
        Args:
            db: Veritabanı oturumu
            email: Kullanıcı email
            
        Returns:
            Optional[models.User]: Kullanıcı nesnesi veya None
        """
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_users(
        db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """
        Tüm kullanıcıları getirir.
        
        Args:
            db: Veritabanı oturumu
            skip: Atlanacak kayıt sayısı
            limit: Maksimum kayıt sayısı
            
        Returns:
            List[models.User]: Kullanıcı listesi
        """
        stmt = select(User).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def update_user(
        db: AsyncSession, db_obj: User, obj_in: Union[UserCreate, Dict[str, Any]]
    ) -> User:
        """
        Kullanıcıyı günceller.
        
        Args:
            db: Veritabanı oturumu
            db_obj: Güncellenecek kullanıcı
            obj_in: Güncelleme bilgileri
            
        Returns:
            models.User: Güncellenen kullanıcı
        """
        update_data = obj_in.dict(exclude_unset=True) if isinstance(obj_in, UserCreate) else obj_in
        
        if "password" in update_data and update_data["password"]:
            hashed_password = AuthService.get_password_hash(update_data["password"])
            update_data["hashed_password"] = hashed_password
            del update_data["password"]
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def update_user_role(
        db: AsyncSession, db_obj: User, role: UserRole
    ) -> User:
        """
        Kullanıcı rolünü günceller.
        
        Args:
            db: Veritabanı oturumu
            db_obj: Güncellenecek kullanıcı
            role: Yeni rol
            
        Returns:
            models.User: Güncellenen kullanıcı
        """
        db_obj.role = role
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def update_user_language(
        db: AsyncSession, db_obj: User, language: str
    ) -> User:
        """
        Kullanıcının dil tercihini günceller.
        
        Args:
            db: Veritabanı oturumu
            db_obj: Güncellenecek kullanıcı
            language: Yeni dil tercihi (ör. "tr", "en")
            
        Returns:
            models.User: Güncellenen kullanıcı
        """
        db_obj.language = language
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def authenticate(db: AsyncSession, *, email: str, password: str) -> Optional[User]:
        """
        Kullanıcıyı doğrular.
        
        Args:
            db: Veritabanı oturumu
            email: Kullanıcı email
            password: Kullanıcı şifresi
            
        Returns:
            Optional[models.User]: Doğrulanan kullanıcı veya None
        """
        user = await AuthService.get_user_by_email(db, email=email)
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user