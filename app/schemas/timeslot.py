from typing import Optional, List, TYPE_CHECKING, Any, ForwardRef
from datetime import time

from pydantic import BaseModel, field_validator

if TYPE_CHECKING:
    from app.schemas.schedule import Schedule

# ForwardRef tanımı
ScheduleRef = ForwardRef("Schedule")

class TimeSlotBase(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_morning: Optional[bool] = None
    is_active: Optional[bool] = True
    
    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time(cls, v):
        if v is None:
            return v
        try:
            # Geçersiz saatleri kontrol et ve güvenli varsayılanlar kullan
            if hasattr(v, 'hour') and hasattr(v, 'minute'):
                hour = v.hour
                minute = v.minute
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    print(f"Warning: Invalid time hour={hour}, minute={minute}, using default")
                    return time(9, 0) if 'start_time' in cls.__annotations__ else time(9, 30)
            return v
        except (ValueError, AttributeError, TypeError):
            print(f"Warning: Error validating time {v}, using default")
            return time(9, 0) if 'start_time' in cls.__annotations__ else time(9, 30)

class TimeSlotCreate(TimeSlotBase):
    start_time: time
    end_time: time

class TimeSlotUpdate(TimeSlotBase):
    pass

class TimeSlotInDBBase(TimeSlotBase):
    id: int

    class Config:
        from_attributes = True

class TimeSlot(TimeSlotInDBBase):
    pass

class TimeSlotInDB(TimeSlotInDBBase):
    pass

class TimeSlotWithRelations(TimeSlotInDBBase):
    schedules: List[Any] = []  # ScheduleRef yerine Any kullanıyoruz

    class Config:
        from_attributes = True

def update_forward_refs():
    from app.schemas.schedule import Schedule
    TimeSlotWithRelations.model_rebuild() 