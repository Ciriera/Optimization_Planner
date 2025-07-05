from typing import Optional, List, TYPE_CHECKING, Any, ForwardRef
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.schemas.schedule import Schedule

# ForwardRef tanımı
ScheduleRef = ForwardRef("Schedule")

class ClassroomBase(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = True
    location: Optional[str] = None

class ClassroomCreate(ClassroomBase):
    name: str
    capacity: int

class ClassroomUpdate(ClassroomBase):
    pass

class ClassroomInDBBase(ClassroomBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class Classroom(ClassroomInDBBase):
    pass

class ClassroomInDB(ClassroomInDBBase):
    pass

class ClassroomWithRelations(ClassroomInDBBase):
    schedules: List[Any] = Field(default_factory=list)  # ScheduleRef yerine Any kullanıyoruz

    model_config = ConfigDict(from_attributes=True)

def update_forward_refs():
    from app.schemas.schedule import Schedule
    ClassroomWithRelations.model_rebuild() 