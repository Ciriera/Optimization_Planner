from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    from app.schemas.project import Project
    from app.schemas.classroom import Classroom
    from app.schemas.timeslot import TimeSlot
    from app.schemas.instructor import Instructor

# Shared properties
class ScheduleBase(BaseModel):
    project_id: int
    classroom_id: int
    timeslot_id: int

# Properties to receive on schedule creation
class ScheduleCreate(ScheduleBase):
    pass

# Properties to receive on schedule update
class ScheduleUpdate(BaseModel):
    project_id: Optional[int] = None
    classroom_id: Optional[int] = None
    timeslot_id: Optional[int] = None

# Properties shared by models stored in DB
class ScheduleInDBBase(ScheduleBase):
    id: int

    class Config:
        from_attributes = True

# Properties to return to client
class Schedule(ScheduleInDBBase):
    pass

# Properties stored in DB
class ScheduleInDB(ScheduleInDBBase):
    pass

# Detailed schedule with nested objects
class ScheduleDetail(ScheduleInDBBase):
    # Import referenced models as forwards refs
    project: Optional["Project"] = None
    classroom: Optional["Classroom"] = None
    timeslot: Optional["TimeSlot"] = None
    instructors: Optional[List["Instructor"]] = None 