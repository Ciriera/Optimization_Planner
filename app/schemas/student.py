from typing import List, Optional
from pydantic import EmailStr, conint, confloat
from app.schemas.base import BaseUserSchema

class StudentBase(BaseUserSchema):
    student_number: str
    department: str
    gpa: Optional[confloat(ge=0.0, le=4.0)] = None
    interests: Optional[str] = None

class StudentCreate(StudentBase):
    password: str

class StudentUpdate(StudentBase):
    password: Optional[str] = None

class StudentInDBBase(StudentBase):
    id: int
    preferred_keywords: List[str] = []

class Student(StudentInDBBase):
    pass

class StudentInDB(StudentInDBBase):
    hashed_password: str 