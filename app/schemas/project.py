from typing import List, Optional, TYPE_CHECKING, Any, ForwardRef
from datetime import datetime
from pydantic import conint, BaseModel
from app.schemas.base import BaseSchema
from app.models.project import ProjectType, ProjectStatus
from enum import Enum

if TYPE_CHECKING:
    from app.schemas.instructor import InstructorWithRelations
    from app.schemas.schedule import ScheduleWithRelations

# ForwardRef tanımları
InstructorRef = ForwardRef("InstructorWithRelations")
ScheduleRef = ForwardRef("ScheduleWithRelations")

class ProjectType(str, Enum):
    ARA = "ara"
    BITIRME = "bitirme"

class ProjectStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ProjectBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[ProjectType] = None
    status: ProjectStatus = ProjectStatus.PENDING
    student_capacity: conint(ge=1, le=4) = 1
    is_makeup: Optional[bool] = False

class ProjectCreate(ProjectBase):
    title: str
    type: ProjectType
    responsible_id: int
    advisor_id: int
    co_advisor_id: Optional[int] = None
    keywords: List[str] = []
    is_active: Optional[bool] = True

class ProjectUpdate(ProjectBase):
    responsible_id: Optional[int] = None
    advisor_id: Optional[int] = None
    co_advisor_id: Optional[int] = None
    keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ProjectInDBBase(ProjectBase):
    id: int
    responsible_id: int
    advisor_id: int
    co_advisor_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    keywords: List[str] = []

    class Config:
        from_attributes = True

class Project(ProjectInDBBase):
    students: List[int] = []

class ProjectInDB(ProjectInDBBase):
    pass

class ProjectAssignment(BaseSchema):
    project_id: int
    advisor_id: int
    student_ids: List[int]
    score: float

class ProjectWithRelations(ProjectInDBBase):
    responsible: Optional[Any] = None  # InstructorRef yerine Any kullanıyoruz
    schedules: List[Any] = []  # ScheduleRef yerine Any kullanıyoruz

    class Config:
        from_attributes = True

# Forward referans güncellemesi için fonksiyon
def update_forward_refs():
    from app.schemas.instructor import InstructorWithRelations
    from app.schemas.schedule import ScheduleWithRelations
    
    ProjectWithRelations.model_rebuild() 