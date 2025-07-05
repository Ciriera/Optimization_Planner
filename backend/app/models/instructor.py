from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base

class InstructorType(str, enum.Enum):
    HOCA = "hoca"
    ARAS_GOR = "aras_gor"

class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    role = Column(String, index=True)  # "hoca" veya "aras_gor"
    bitirme_count = Column(Integer, default=0)
    ara_count = Column(Integer, default=0)
    total_load = Column(Integer, default=0)
    
    # İlişkiler
    projects = relationship("Project", back_populates="responsible_instructor")
    assisted_projects = relationship(
        "Project",
        secondary="project_instructor",
        back_populates="assistant_instructors"
    )
    schedules = relationship(
        "Schedule",
        secondary="schedule_instructor",
        back_populates="instructors"
    ) 