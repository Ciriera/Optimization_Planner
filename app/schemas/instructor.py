from typing import List, Optional, TYPE_CHECKING, Any, ForwardRef, Dict
from enum import Enum
from pydantic import EmailStr, BaseModel, ConfigDict, model_validator
import json

if TYPE_CHECKING:
    from app.schemas.project import Project

# ForwardRef tanımı
ProjectRef = ForwardRef("Project")

class InstructorType(str, Enum):
    INSTRUCTOR = "instructor"
    ASSISTANT = "assistant"

class InstructorBase(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None  # Changed from role to type
    department: Optional[str] = None  # Added department
    bitirme_count: Optional[int] = 0
    ara_count: Optional[int] = 0
    total_load: Optional[int] = 0
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    @model_validator(mode='before')
    @classmethod
    def validate_type_field(cls, data):
        """Validate and convert type field"""
        if isinstance(data, dict) and "type" in data and data["type"] is not None:
            # Handle string conversion to enum
            if data["type"] not in ["instructor", "assistant"]:
                # Map legacy values if needed
                type_mapping = {
                    "professor": "instructor",
                    "research_assistant": "assistant",
                    "hoca": "instructor",
                    "aras_gor": "assistant",
                }
                if data["type"] in type_mapping:
                    data["type"] = type_mapping[data["type"]]
                else:
                    data["type"] = "instructor"
        # Handle role field for backwards compatibility
        elif isinstance(data, dict) and "role" in data and data["role"] is not None:
            # Map role to type
            role_mapping = {
                "professor": "instructor",
                "research_assistant": "assistant",
                "hoca": "instructor",
                "aras_gor": "assistant",
                "instructor": "instructor",
                "assistant": "assistant",
            }
            if data["role"] in role_mapping:
                data["type"] = role_mapping[data["role"]]
            else:
                data["type"] = "instructor"
        return data

class InstructorCreate(InstructorBase):
    name: str
    type: str
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class InstructorUpdate(InstructorBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class InstructorInDBBase(InstructorBase):
    id: int
    user_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class Instructor(InstructorInDBBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class InstructorInDB(InstructorInDBBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

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