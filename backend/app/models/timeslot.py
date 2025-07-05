from sqlalchemy import Column, Integer, String, Time
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class TimeSlot(Base):
    __tablename__ = "timeslots"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(Time, index=True)
    end_time = Column(Time, index=True)
    period = Column(String, index=True)  # "morning" veya "afternoon"
    
    # İlişkiler
    schedules = relationship("Schedule", back_populates="timeslot")

    class Config:
        orm_mode = True 