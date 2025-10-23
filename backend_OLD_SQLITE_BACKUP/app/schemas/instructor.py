from typing import Optional, List
from pydantic import BaseModel
from app.models.instructor import InstructorType

# Shared properties
class InstructorBase(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    bitirme_count: Optional[int] = 0
    ara_count: Optional[int] = 0
    total_load: Optional[int] = 0

# Properties to receive on instructor creation
class InstructorCreate(InstructorBase):
    name: str
    role: str

# Properties to receive on instructor update
class InstructorUpdate(InstructorBase):
    pass

# Properties shared by models stored in DB
class InstructorInDBBase(InstructorBase):
    id: int

    class Config:
        from_attributes = True

# Properties to return to client
class Instructor(InstructorInDBBase):
    pass

# Properties stored in DB
class InstructorInDB(InstructorInDBBase):
    pass

class InstructorWithRelations(InstructorInDBBase):
    projects: List["Project"] = []  # type: ignore

    class Config:
        from_attributes = True

from app.schemas.project import Project  # noqa

InstructorWithRelations.model_rebuild() 