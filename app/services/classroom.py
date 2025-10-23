from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classroom import Classroom
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate
from app.services.base import BaseService

class ClassroomService(BaseService[Classroom, ClassroomCreate, ClassroomUpdate]):
    def __init__(self):
        super().__init__(Classroom) 