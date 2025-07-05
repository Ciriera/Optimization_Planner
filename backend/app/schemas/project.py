from typing import Optional, List
from pydantic import BaseModel
from app.models.project import ProjectType, ProjectStatus

# Shared properties
class ProjectBase(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None  # "ara" veya "bitirme"
    is_makeup: Optional[bool] = False
    status: Optional[str] = None
    responsible_instructor_id: Optional[int] = None

# Properties to receive on project creation
class ProjectCreate(ProjectBase):
    title: str
    type: str
    responsible_instructor_id: int

# Properties to receive on project update
class ProjectUpdate(ProjectBase):
    pass

# Properties shared by models stored in DB
class ProjectInDBBase(ProjectBase):
    id: int

    class Config:
        from_attributes = True

# Properties to return to client
class Project(ProjectInDBBase):
    pass

# Properties stored in DB
class ProjectInDB(ProjectInDBBase):
    pass 