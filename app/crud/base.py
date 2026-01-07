from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base_class import Base
import enum

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD işlemleri için temel sınıf.
        
        **Parametreler**
        
        * `model`: SQLAlchemy model sınıfı
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """ID ile kayıt getir."""
        result = await db.execute(select(self.model).filter(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Birden fazla kayıt getir."""
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """Yeni kayıt oluştur."""
        # Convert enum objects to their .value for PostgreSQL native enum
        # jsonable_encoder converts enum to .name, but PostgreSQL needs .value
        if hasattr(obj_in, 'model_dump'):
            # Pydantic v2
            obj_in_data = obj_in.model_dump()
        else:
            # Pydantic v1
            obj_in_data = obj_in.dict()
        
        # Fix: Convert enum objects to their .value (string) for PostgreSQL native enum
        for key, value in obj_in_data.items():
            if isinstance(value, enum.Enum):
                obj_in_data[key] = value.value
            elif key == 'algorithm_type' and isinstance(value, str):
                # Convert string to enum value (lowercase) for PostgreSQL
                from app.models.algorithm import AlgorithmType
                # Always convert to lowercase first (enum values are lowercase)
                value_lower = value.lower()
                try:
                    # First, try to match by value (lowercase string)
                    enum_obj = AlgorithmType(value_lower)
                    obj_in_data[key] = enum_obj.value
                except ValueError:
                    # If not found by value, try to match by enum name (uppercase)
                    # Example: "HUNGARIAN" -> find AlgorithmType.HUNGARIAN -> use .value which is "hungarian"
                    found = False
                    for enum_member in AlgorithmType:
                        if enum_member.name.upper() == value.upper():
                            obj_in_data[key] = enum_member.value  # Always use lowercase .value
                            found = True
                            break
                    if not found:
                        # If still not found, try direct lowercase assignment
                        # This handles cases where the value might already be correct
                        obj_in_data[key] = value_lower
        
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Kayıt güncelle."""
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> ModelType:
        """Kayıt sil."""
        obj = await db.get(self.model, id)
        await db.delete(obj)
        await db.commit()
        return obj 