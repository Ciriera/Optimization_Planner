from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Schedule(Base):
    """Planlama modeli."""
    
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    timeslot_id = Column(Integer, ForeignKey("timeslots.id"), nullable=False)
    is_makeup = Column(Boolean, default=False)  # True: bütünleme, False: final
    
    # İlişkiler
    project = relationship("Project", back_populates="schedules")
    classroom = relationship("Classroom", back_populates="schedules")
    timeslot = relationship("TimeSlot", back_populates="schedules")
    
    def __repr__(self):
        return f"<Schedule {self.project_id} at {self.classroom_id}>" 