from pydantic import BaseModel
from typing import Optional, List

# Shared properties
class ClassroomBase(BaseModel):
    name: str
    capacity: Optional[int] = 30
    location: Optional[str] = None

# Properties to receive on classroom creation
class ClassroomCreate(ClassroomBase):
    pass

# Properties to receive on classroom update
class ClassroomUpdate(ClassroomBase):
    name: Optional[str] = None
    capacity: Optional[int] = None

# Properties shared by models stored in DB
class ClassroomInDBBase(ClassroomBase):
    id: int

    class Config:
        orm_mode = True

# Properties to return to client
class Classroom(ClassroomInDBBase):
    pass

# Properties stored in DB
class ClassroomInDB(ClassroomInDBBase):
    pass 