from pydantic import BaseModel
from typing import Optional, List, TYPE_CHECKING, Any, ForwardRef
from datetime import time

if TYPE_CHECKING:
    from app.schemas.project import ProjectWithRelations
    from app.schemas.classroom import ClassroomWithRelations
    from app.schemas.timeslot import TimeSlotWithRelations

# ForwardRef tanımları
ProjectRef = ForwardRef("ProjectWithRelations")
ClassroomRef = ForwardRef("ClassroomWithRelations")
TimeSlotRef = ForwardRef("TimeSlotWithRelations")

class ClassroomBase(BaseModel):
    name: str
    capacity: Optional[int] = 30
    location: Optional[str] = None

class ClassroomCreate(ClassroomBase):
    pass

class ClassroomUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    location: Optional[str] = None

class Classroom(ClassroomBase):
    id: int

    class Config:
        from_attributes = True

class TimeSlotBase(BaseModel):
    start_time: time
    end_time: time

class TimeSlotCreate(TimeSlotBase):
    pass

class TimeSlot(TimeSlotBase):
    id: int

    class Config:
        from_attributes = True

class ScheduleBase(BaseModel):
    project_id: Optional[int] = None
    classroom_id: Optional[int] = None
    timeslot_id: Optional[int] = None
    is_makeup: Optional[bool] = False

class ScheduleCreate(ScheduleBase):
    project_id: int
    classroom_id: int
    timeslot_id: int

class ScheduleUpdate(ScheduleBase):
    instructors: Optional[List[Any]] = None  # Jüri üyeleri (instructor ID'leri veya dict formatında)
    responsible_instructor_id: Optional[int] = None  # Proje sorumlusu (Project'in responsible_id'si)

class ScheduleInDBBase(ScheduleBase):
    id: int

    class Config:
        from_attributes = True

class Schedule(ScheduleInDBBase):
    pass

class ScheduleInDB(ScheduleInDBBase):
    pass

class ScheduleWithRelations(ScheduleInDBBase):
    project: Optional[Any] = None  # ProjectRef yerine Any kullanıyoruz, sonra update edeceğiz
    classroom: Optional[Any] = None  # ClassroomRef yerine Any kullanıyoruz
    timeslot: Optional[Any] = None  # TimeSlotRef yerine Any kullanıyoruz

    class Config:
        from_attributes = True

# Modeli daha sonra güncellemek için işlevi tanımlayalım
def update_forward_refs():
    from app.schemas.project import ProjectWithRelations
    from app.schemas.classroom import ClassroomWithRelations
    from app.schemas.timeslot import TimeSlotWithRelations
    
    ScheduleWithRelations.model_rebuild()
    # Bu fonksiyon __init__.py'de çağrılacak 