from typing import Optional, List, TYPE_CHECKING, Any, ForwardRef
from datetime import time

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.schemas.schedule import Schedule

# ForwardRef tanımı
ScheduleRef = ForwardRef("Schedule")

class TimeSlotBase(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_morning: Optional[bool] = None
    is_active: Optional[bool] = True

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