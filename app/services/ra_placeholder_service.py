"""
Research Assistant (RA) Placeholder Service
Handles RA assignments as placeholders with manual naming capability
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import logging

logger = logging.getLogger(__name__)


class RAPlaceholderService:
    """Service for managing Research Assistant placeholders"""
    
    def __init__(self):
        self.ra_type_identifier = "assistant"  # Instructor type for RA
        self.placeholder_prefix = "RA_"
    
    async def create_ra_placeholders(self, db: AsyncSession, 
                                   required_ra_count: int) -> List[Dict[str, Any]]:
        """
        Belirtilen sayıda RA placeholder oluşturur.
        
        Args:
            db: Veritabanı oturumu
            required_ra_count: Gerekli RA sayısı
            
        Returns:
            Oluşturulan placeholder'lar
        """
        placeholders = []
        
        for i in range(required_ra_count):
            placeholder = {
                "id": f"{self.placeholder_prefix}{i+1}",
                "name": f"Research Assistant {i+1}",
                "type": self.ra_type_identifier,
                "is_placeholder": True,
                "is_active": True,
                "assigned_projects": [],
                "total_load": 0
            }
            placeholders.append(placeholder)
        
        return placeholders
    
    async def assign_ra_placeholders_to_projects(self, db: AsyncSession, 
                                               projects: List[Dict[str, Any]],
                                               available_placeholders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        RA placeholder'larını projelere atar.
        
        Args:
            db: Veritabanı oturumu
            projects: Atanacak projeler
            available_placeholders: Mevcut placeholder'lar
            
        Returns:
            Atama sonucu
        """
        assignments = []
        used_placeholders = set()
        
        for project in projects:
            project_id = project.get("id")
            project_type = project.get("type", "ara")
            
            # Proje türüne göre gerekli RA sayısını belirle
            if project_type == "bitirme":
                required_ra = max(0, 3 - 2)  # 3 kişi - 2 hoca = 1 RA
            else:  # ara
                required_ra = max(0, 3 - 1)  # 3 kişi - 1 hoca = 2 RA
            
            # Bu proje için RA placeholder'ları ata
            project_ra_assignments = []
            for i in range(required_ra):
                # Kullanılmayan placeholder bul
                for placeholder in available_placeholders:
                    if placeholder["id"] not in used_placeholders:
                        project_ra_assignments.append(placeholder["id"])
                        used_placeholders.add(placeholder["id"])
                        break
            
            if project_ra_assignments:
                assignments.append({
                    "project_id": project_id,
                    "ra_placeholders": project_ra_assignments,
                    "assigned_count": len(project_ra_assignments)
                })
        
        return {
            "assignments": assignments,
            "total_assigned": len(used_placeholders),
            "unassigned_placeholders": [
                p for p in available_placeholders 
                if p["id"] not in used_placeholders
            ]
        }
    
    async def update_ra_placeholder_name(self, db: AsyncSession, 
                                       placeholder_id: str, 
                                       new_name: str) -> Dict[str, Any]:
        """
        RA placeholder'ının ismini günceller.
        
        Args:
            db: Veritabanı oturumu
            placeholder_id: Placeholder ID
            new_name: Yeni isim
            
        Returns:
            Güncelleme sonucu
        """
        try:
            # Instructor tablosunda placeholder'ı bul ve güncelle
            from app.models.instructor import Instructor
            
            result = await db.execute(
                select(Instructor).where(Instructor.name.like(f"{self.placeholder_prefix}%"))
            )
            instructors = result.scalars().all()
            
            # Placeholder'ı bul
            target_instructor = None
            for instructor in instructors:
                if instructor.name.startswith(self.placeholder_prefix):
                    # Placeholder ID ile eşleşen instructor'ı bul
                    if placeholder_id in instructor.name or instructor.id == int(placeholder_id.replace(self.placeholder_prefix, "")):
                        target_instructor = instructor
                        break
            
            if not target_instructor:
                return {
                    "success": False,
                    "message": f"Placeholder {placeholder_id} not found"
                }
            
            # İsmi güncelle
            target_instructor.name = new_name
            await db.commit()
            
            return {
                "success": True,
                "message": f"Placeholder {placeholder_id} renamed to {new_name}",
                "updated_instructor": {
                    "id": target_instructor.id,
                    "name": target_instructor.name,
                    "type": target_instructor.type
                }
            }
            
        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "message": f"Error updating placeholder: {str(e)}"
            }
    
    async def get_ra_placeholders_status(self, db: AsyncSession) -> Dict[str, Any]:
        """
        RA placeholder'larının durumunu getirir.
        
        Args:
            db: Veritabanı oturumu
            
        Returns:
            Placeholder durum raporu
        """
        from app.models.instructor import Instructor
        
        # Tüm RA'ları getir
        result = await db.execute(
            select(Instructor).where(Instructor.type == self.ra_type_identifier)
        )
        ra_instructors = result.scalars().all()
        
        placeholders = []
        named_ras = []
        
        for ra in ra_instructors:
            if ra.name.startswith(self.placeholder_prefix) or "Research Assistant" in ra.name:
                # Placeholder
                placeholders.append({
                    "id": ra.id,
                    "name": ra.name,
                    "type": ra.type,
                    "is_placeholder": True,
                    "total_load": ra.total_load or 0
                })
            else:
                # Named RA
                named_ras.append({
                    "id": ra.id,
                    "name": ra.name,
                    "type": ra.type,
                    "is_placeholder": False,
                    "total_load": ra.total_load or 0
                })
        
        return {
            "total_ra_count": len(ra_instructors),
            "placeholder_count": len(placeholders),
            "named_ra_count": len(named_ras),
            "placeholders": placeholders,
            "named_ras": named_ras,
            "placeholder_utilization": len(named_ras) / len(ra_instructors) if ra_instructors else 0
        }
    
    async def convert_placeholder_to_named_ra(self, db: AsyncSession, 
                                            placeholder_id: str, 
                                            ra_name: str,
                                            ra_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Placeholder'ı gerçek RA'ya dönüştürür.
        
        Args:
            db: Veritabanı oturumu
            placeholder_id: Placeholder ID
            ra_name: RA ismi
            ra_details: Ek RA detayları
            
        Returns:
            Dönüştürme sonucu
        """
        try:
            from app.models.instructor import Instructor
            
            # Placeholder'ı bul
            result = await db.execute(
                select(Instructor).where(Instructor.id == int(placeholder_id.replace(self.placeholder_prefix, "")))
            )
            placeholder = result.scalar_one_or_none()
            
            if not placeholder:
                return {
                    "success": False,
                    "message": f"Placeholder {placeholder_id} not found"
                }
            
            # Placeholder'ı gerçek RA'ya dönüştür
            placeholder.name = ra_name
            placeholder.type = self.ra_type_identifier
            
            if ra_details:
                if "department" in ra_details:
                    placeholder.department = ra_details["department"]
                if "user_id" in ra_details:
                    placeholder.user_id = ra_details["user_id"]
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"Placeholder {placeholder_id} converted to named RA: {ra_name}",
                "converted_ra": {
                    "id": placeholder.id,
                    "name": placeholder.name,
                    "type": placeholder.type,
                    "department": placeholder.department
                }
            }
            
        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "message": f"Error converting placeholder: {str(e)}"
            }
    
    async def cleanup_unused_placeholders(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Kullanılmayan placeholder'ları temizler.
        
        Args:
            db: Veritabanı oturumu
            
        Returns:
            Temizleme sonucu
        """
        try:
            from app.models.instructor import Instructor
            
            # Kullanılmayan placeholder'ları bul
            result = await db.execute(
                select(Instructor).where(
                    Instructor.type == self.ra_type_identifier,
                    Instructor.total_load == 0,
                    Instructor.name.like(f"{self.placeholder_prefix}%")
                )
            )
            unused_placeholders = result.scalars().all()
            
            # Placeholder'ları sil
            deleted_count = 0
            for placeholder in unused_placeholders:
                await db.delete(placeholder)
                deleted_count += 1
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"Cleaned up {deleted_count} unused placeholders",
                "deleted_count": deleted_count
            }
            
        except Exception as e:
            await db.rollback()
            return {
                "success": False,
                "message": f"Error cleaning up placeholders: {str(e)}"
            }
