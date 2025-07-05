from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Table, Boolean
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base

class ProjectType(str, enum.Enum):
    FINAL = "final"
    INTERIM = "interim"

class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    MAKEUP = "makeup"
    COMPLETED = "completed"

# Ara tablo: project_instructor
project_instructor = Table(
    "project_instructor",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id")),
    Column("instructor_id", Integer, ForeignKey("instructors.id")),
)

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    type = Column(Enum(ProjectType), index=True)  # "final" veya "interim"
    is_makeup = Column(Boolean, default=False)  # final veya bütünleme
    status = Column(Enum(ProjectStatus), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # İlişkiler
    responsible_instructor_id = Column(Integer, ForeignKey("instructors.id"))
    responsible_instructor = relationship("Instructor", back_populates="projects")
    
    assistant_instructors = relationship(
        "Instructor",
        secondary=project_instructor,
        back_populates="assisted_projects"
    )
    
    schedule = relationship("Schedule", back_populates="project", uselist=False)
    owner = relationship("User", back_populates="projects")