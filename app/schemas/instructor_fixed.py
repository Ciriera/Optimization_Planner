from typing import List, Optional, TYPE_CHECKING, Any, ForwardRef, Dict
from enum import Enum
from pydantic import BaseModel, ConfigDict, model_validator
import json

if TYPE_CHECKING:
    from app.schemas.project import Project

# ForwardRef tanımı
ProjectRef = ForwardRef("Project")

class InstructorType(str, Enum):
    HOCA = "hoca"
    ARAS_GOR = "aras_gor"

class InstructorBase(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    bitirme_count: Optional[int] = 0
    ara_count: Optional[int] = 0
    total_load: Optional[int] = 0
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    @model_validator(mode='before')
    @classmethod
    def validate_role_field(cls, data):
        """Validate and convert role field"""
        if isinstance(data, dict) and "role" in data and data["role"] is not None:
            # Handle string conversion to enum
            if data["role"] not in ["hoca", "aras_gor"]:
                # Map legacy values if needed
                role_mapping = {
                    "professor": "hoca",
                    "research_assistant": "aras_gor",
                    "instructor": "hoca",
                    "assistant": "aras_gor",
                }
                if data["role"] in role_mapping:
                    data["role"] = role_mapping[data["role"]]
                else:
                    data["role"] = "hoca"
        return data

class InstructorCreate(InstructorBase):
    name: str
    role: str

class InstructorUpdate(InstructorBase):
    pass

class InstructorInDBBase(InstructorBase):
    id: int

class Instructor(InstructorInDBBase):
    pass

class InstructorInDB(InstructorInDBBase):
    pass

class TimeSlotInfo(BaseModel):
    id: int
    start_time: str
    end_time: str
    is_morning: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)

class InstructorAvailability(BaseModel):
    instructor_id: int
    date: str
    busy_slots: List[TimeSlotInfo] = []
    available_slots: List[TimeSlotInfo] = []
    
    model_config = ConfigDict(from_attributes=True)

class InstructorWithRelations(InstructorInDBBase):
    projects: List[Dict[str, Any]] = []
    
    model_config = ConfigDict(from_attributes=True)

# InstructorWithProjects için alias tanımlama - endpoints/instructors.py için
InstructorWithProjects = InstructorWithRelations

def update_forward_refs():
    from app.schemas.project import Project
    InstructorWithRelations.model_rebuild() 