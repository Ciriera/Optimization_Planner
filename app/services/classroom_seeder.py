"""
Default classroom seeding service
Creates standard classroom names as specified in project requirements
"""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.classroom import Classroom
from app.services.base import BaseService
from app.schemas.classroom import ClassroomCreate


class ClassroomSeeder:
    """Service for seeding default classrooms."""
    
    # Proje açıklamasından: D106, D107, D108, D109, D110, D111, D223 + Yeni: D224, D225, D226
    DEFAULT_CLASSROOMS = [
        {"name": "D106", "capacity": 25, "location": "Bilgisayar Mühendisliği Binası"},
        {"name": "D107", "capacity": 25, "location": "Bilgisayar Mühendisliği Binası"},
        {"name": "D108", "capacity": 25, "location": "Bilgisayar Mühendisliği Binası"},
        {"name": "D109", "capacity": 25, "location": "Bilgisayar Mühendisliği Binası"},
        {"name": "D110", "capacity": 25, "location": "Bilgisayar Mühendisliği Binası"},
        {"name": "D111", "capacity": 25, "location": "Bilgisayar Mühendisliği Binası"},
        {"name": "D223", "capacity": 30, "location": "Bilgisayar Mühendisliği Binası"},
        {"name": "D224", "capacity": 25, "location": "Bilgisayar Mühendisliği Binası"},
        {"name": "D225", "capacity": 25, "location": "Bilgisayar Mühendisliği Binası"},
        {"name": "D226", "capacity": 25, "location": "Bilgisayar Mühendisliği Binası"},
    ]
    
    async def seed_default_classrooms(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Default classroom'ları oluşturur.
        
        Args:
            db: Veritabanı oturumu
            
        Returns:
            Seeding sonucu
        """
        created_count = 0
        existing_count = 0
        errors = []
        
        for classroom_data in self.DEFAULT_CLASSROOMS:
            try:
                # Mevcut classroom'ı kontrol et
                result = await db.execute(
                    select(Classroom).where(Classroom.name == classroom_data["name"])
                )
                existing_classroom = result.scalar_one_or_none()
                
                if existing_classroom:
                    existing_count += 1
                    continue
                
                # Yeni classroom oluştur
                classroom = Classroom(
                    name=classroom_data["name"],
                    capacity=classroom_data["capacity"],
                    location=classroom_data["location"],
                    is_active=True
                )
                
                db.add(classroom)
                created_count += 1
                
            except Exception as e:
                errors.append(f"Error creating classroom {classroom_data['name']}: {str(e)}")
        
        if created_count > 0:
            await db.commit()
        
        return {
            "created": created_count,
            "existing": existing_count,
            "total_requested": len(self.DEFAULT_CLASSROOMS),
            "errors": errors,
            "success": len(errors) == 0
        }
    
    async def get_default_classroom_names(self) -> List[str]:
        """
        Default classroom isimlerini döndürür.
        
        Returns:
            Classroom isimleri listesi
        """
        return [classroom["name"] for classroom in self.DEFAULT_CLASSROOMS]
    
    async def validate_classroom_names(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Mevcut classroom isimlerini default'larla karşılaştırır.
        
        Args:
            db: Veritabanı oturumu
            
        Returns:
            Validation sonucu
        """
        # Mevcut classroom'ları getir
        result = await db.execute(select(Classroom))
        existing_classrooms = result.scalars().all()
        
        existing_names = {classroom.name for classroom in existing_classrooms}
        default_names = set(self.get_default_classroom_names())
        
        missing_names = default_names - existing_names
        extra_names = existing_names - default_names
        
        return {
            "existing_classrooms": list(existing_names),
            "default_classrooms": list(default_names),
            "missing_classrooms": list(missing_names),
            "extra_classrooms": list(extra_names),
            "is_compliant": len(missing_names) == 0
        }
