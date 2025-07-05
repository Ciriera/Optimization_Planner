from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship

from app.db.base_class import Base

# Ara tablo: schedule_instructor (bir planlamada hangi hocalar var)
schedule_instructor = Table(
    "schedule_instructor",
    Base.metadata,
    Column("schedule_id", Integer, ForeignKey("schedules.id")),
    Column("instructor_id", Integer, ForeignKey("instructors.id")),
)

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), unique=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"))
    timeslot_id = Column(Integer, ForeignKey("timeslots.id"))
    
    # İlişkiler
    project = relationship("Project", back_populates="schedule")
    classroom = relationship("Classroom", back_populates="schedules")
    timeslot = relationship("TimeSlot", back_populates="schedules")
    instructors = relationship(
        "Instructor",
        secondary=schedule_instructor,
        back_populates="schedules"
    )
    
    class Config:
        orm_mode = True 