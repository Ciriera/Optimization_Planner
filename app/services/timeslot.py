from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import time

from app.models.timeslot import TimeSlot, SessionType
from app.schemas.timeslot import TimeSlotCreate, TimeSlotUpdate
from app.services.base import BaseService

class TimeSlotService(BaseService[TimeSlot, TimeSlotCreate, TimeSlotUpdate]):
    def __init__(self):
        super().__init__(TimeSlot)
    
    async def validate_timeslot_constraints(self, db: AsyncSession, timeslot_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Proje açıklamasına göre zaman dilimi kısıtlamalarını validate eder.
        Geçerli saatler: 09:00-11:30 (sabah), 13:00-16:30 (öğleden sonra)
        """
        errors = []
        warnings = []
        
        start_time = timeslot_data.get("start_time")
        end_time = timeslot_data.get("end_time")
        session_type = timeslot_data.get("session_type")
        
        if not start_time or not end_time:
            errors.append("Start time and end time are required")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        # Saat diliminin geçerli aralıkta olup olmadığını kontrol et
        if session_type == SessionType.MORNING:
            # Sabah oturumu: 09:00-11:30
            if not (start_time >= time(9, 0) and end_time <= time(11, 30)):
                errors.append("Morning session must be between 09:00-11:30")
            
        elif session_type == SessionType.AFTERNOON:
            # Öğleden sonra oturumu: 13:00-16:30
            if not (start_time >= time(13, 0) and end_time <= time(16, 30)):
                errors.append("Afternoon session must be between 13:00-16:30")
                
        elif session_type == SessionType.BREAK:
            # Öğle arası: 12:00-13:00 (projeler için kullanılamaz)
            warnings.append("Break sessions (12:00-13:00) are not available for project assignments")
        
        # Zaman dilimi çakışması kontrolü
        if not errors:
            conflict_check = await self._check_time_conflict(db, start_time, end_time, timeslot_data.get("id"))
            if conflict_check["has_conflict"]:
                errors.append(f"Time slot conflicts with existing slot: {conflict_check['conflicting_slot']}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "project_specification_compliant": len(errors) == 0 and session_type != SessionType.BREAK
        }
    
    async def _check_time_conflict(self, db: AsyncSession, start_time: time, end_time: time, exclude_id: Optional[int] = None) -> Dict[str, Any]:
        """Zaman dilimi çakışması kontrol eder."""
        query = select(TimeSlot).filter(
            TimeSlot.start_time < end_time,
            TimeSlot.end_time > start_time,
            TimeSlot.is_active == True
        )
        
        if exclude_id:
            query = query.filter(TimeSlot.id != exclude_id)
        
        result = await db.execute(query)
        conflicting_slots = result.scalars().all()
        
        if conflicting_slots:
            return {
                "has_conflict": True,
                "conflicting_slot": f"{conflicting_slots[0].start_time}-{conflicting_slots[0].end_time}"
            }
        
        return {"has_conflict": False}
    
    async def get_project_compatible_timeslots(self, db: AsyncSession) -> List[TimeSlot]:
        """
        Proje ataması için uygun zaman dilimlerini getirir.
        Öğle arası (12:00-13:00) hariç tüm aktif zaman dilimleri.
        """
        result = await db.execute(
            select(TimeSlot).filter(
                TimeSlot.is_active == True,
                TimeSlot.session_type != SessionType.BREAK
            ).order_by(TimeSlot.start_time)
        )
        return result.scalars().all()
    
    async def create_default_project_timeslots(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Proje açıklamasına göre varsayılan zaman dilimlerini oluşturur.
        """
        default_timeslots = [
            # Sabah oturumu: 09:00-11:30
            {"start_time": time(9, 0), "end_time": time(9, 30), "session_type": SessionType.MORNING},
            {"start_time": time(9, 30), "end_time": time(10, 0), "session_type": SessionType.MORNING},
            {"start_time": time(10, 0), "end_time": time(10, 30), "session_type": SessionType.MORNING},
            {"start_time": time(10, 30), "end_time": time(11, 0), "session_type": SessionType.MORNING},
            {"start_time": time(11, 0), "end_time": time(11, 30), "session_type": SessionType.MORNING},
            
            # Öğleden sonra oturumu: 13:00-16:30
            {"start_time": time(13, 0), "end_time": time(13, 30), "session_type": SessionType.AFTERNOON},
            {"start_time": time(13, 30), "end_time": time(14, 0), "session_type": SessionType.AFTERNOON},
            {"start_time": time(14, 0), "end_time": time(14, 30), "session_type": SessionType.AFTERNOON},
            {"start_time": time(14, 30), "end_time": time(15, 0), "session_type": SessionType.AFTERNOON},
            {"start_time": time(15, 0), "end_time": time(15, 30), "session_type": SessionType.AFTERNOON},
            {"start_time": time(15, 30), "end_time": time(16, 0), "session_type": SessionType.AFTERNOON},
            {"start_time": time(16, 0), "end_time": time(16, 30), "session_type": SessionType.AFTERNOON},
        ]
        
        created_slots = []
        errors = []
        
        for slot_data in default_timeslots:
            try:
                # Mevcut zaman dilimi var mı kontrol et
                existing = await self.get_by_time_range(
                    db, slot_data["start_time"], slot_data["end_time"]
                )
                
                if not existing:
                    timeslot = await self.create(db, obj_in=slot_data)
                    created_slots.append(timeslot)
                else:
                    # Mevcut slot'u güncelle
                    if existing.session_type != slot_data["session_type"]:
                        existing.session_type = slot_data["session_type"]
                        await db.commit()
                        await db.refresh(existing)
                        created_slots.append(existing)
                        
            except Exception as e:
                errors.append(f"Error creating timeslot {slot_data['start_time']}-{slot_data['end_time']}: {str(e)}")
        
        return {
            "success": len(errors) == 0,
            "created_slots": len(created_slots),
            "errors": errors,
            "message": f"Created {len(created_slots)} timeslots successfully" if len(errors) == 0 else f"Created {len(created_slots)} timeslots with {len(errors)} errors"
        }
    
    async def get_by_time_range(self, db: AsyncSession, start_time: time, end_time: time) -> Optional[TimeSlot]:
        """Belirli zaman aralığındaki zaman dilimini getirir."""
        result = await db.execute(
            select(TimeSlot).filter(
                TimeSlot.start_time == start_time,
                TimeSlot.end_time == end_time
            )
        )
        return result.scalar_one_or_none() 