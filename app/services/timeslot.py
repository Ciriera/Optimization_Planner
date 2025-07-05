from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.timeslot import TimeSlot
from app.schemas.timeslot import TimeSlotCreate, TimeSlotUpdate
from app.services.base import BaseService

class TimeSlotService(BaseService[TimeSlot, TimeSlotCreate, TimeSlotUpdate]):
    def __init__(self):
        super().__init__(TimeSlot) 