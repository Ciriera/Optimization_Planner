from sqlalchemy import Column, Integer, Time, Boolean
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class TimeSlot(Base):
    """Zaman dilimi modeli."""
    
    __tablename__ = "timeslots"
    
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_morning = Column(Boolean, default=None)
    is_active = Column(Boolean, default=True)
    
    # İlişkiler
    schedules = relationship("Schedule", back_populates="timeslot")

    def __repr__(self):
        return f"<TimeSlot {self.start_time}-{self.end_time}>" 