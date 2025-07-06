"""
Kullanıcı CRUD işlemleri
"""
from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """Kullanıcı CRUD işlemleri sınıfı"""
    
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """
        Get a user by email.
        """
        # Sadece temel kullanıcı bilgilerini seçelim, ilişkileri yüklemeyelim
        stmt = select(User.id, User.email, User.full_name, User.role, 
                      User.hashed_password, User.is_active, User.is_superuser).\
               where(User.email == email)
        result = await db.execute(stmt)
        user_data = result.first()
        
        if not user_data:
            return None
            
        # Verileri kullanarak User nesnesi oluştur
        user = User(
            id=user_data.id,
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            hashed_password=user_data.hashed_password,
            is_active=user_data.is_active,
            is_superuser=user_data.is_superuser
        )
        return user
    
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        Create a new user.
        """
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            role=obj_in.role,
            is_superuser=obj_in.is_superuser,
            is_active=obj_in.is_active,
            language=obj_in.language,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, db: AsyncSession, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        Update a user.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return await super().update(db, db_obj=db_obj, obj_in=update_data)
    
    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user.
        """
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    async def is_active(self, user: User) -> bool:
        """
        Check if a user is active.
        """
        return user.is_active
    
    async def is_superuser(self, user: User) -> bool:
        """
        Check if a user is a superuser.
        """
        return user.is_superuser
    
    def is_admin(self, user: User) -> bool:
        """Kullanıcı admin mi kontrolü"""
        return user.role == UserRole.ADMIN
    
    async def get_by_role(
        self,
        db: AsyncSession,
        *,
        role: UserRole,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Role göre kullanıcıları getir"""
        result = await db.execute(
            select(User)
            .filter(User.role == role)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

crud_user = CRUDUser(User) 