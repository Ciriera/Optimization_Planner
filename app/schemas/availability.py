from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class TimeSlotInfo(BaseModel):
    id: int
    start_time: str
    end_time: str
    is_morning: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    def model_dump(self, **kwargs):
        return {
            "id": self.id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "is_morning": self.is_morning
        }

class InstructorAvailability(BaseModel):
    instructor_id: int
    date: str
    busy_slots: List[TimeSlotInfo] = Field(default_factory=list)
    available_slots: List[TimeSlotInfo] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)
    
    def model_dump(self, **kwargs):
        return {
            "instructor_id": self.instructor_id,
            "date": self.date,
            "busy_slots": [slot.model_dump() for slot in self.busy_slots],
            "available_slots": [slot.model_dump() for slot in self.available_slots]
        }
