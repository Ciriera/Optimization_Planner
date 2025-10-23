from pydantic import BaseModel
from typing import Optional, List
from datetime import time

# Shared properties
class TimeSlotBase(BaseModel):
    start_time: time
    end_time: time
    period: Optional[str] = None  # "morning" veya "afternoon"

# Properties to receive on timeslot creation
class TimeSlotCreate(TimeSlotBase):
    pass

# Properties to receive on timeslot update
class TimeSlotUpdate(TimeSlotBase):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    period: Optional[str] = None

# Properties shared by models stored in DB
class TimeSlotInDBBase(TimeSlotBase):
    id: int

    class Config:
        orm_mode = True

# Properties to return to client
class TimeSlot(TimeSlotInDBBase):
    pass

# Properties stored in DB
class TimeSlotInDB(TimeSlotInDBBase):
    pass 