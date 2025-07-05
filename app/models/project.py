from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum

class ProjectType(str, enum.Enum):
    ARA = "ara"
    BITIRME = "bitirme"

class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    MAKEUP = "makeup"

# Proje asistanları için ara tablo
project_assistants = Table(
    "project_assistants",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("instructor_id", Integer, ForeignKey("instructors.id"), primary_key=True),
    extend_existing=True
)

# Proje anahtar kelimeleri için ara tablo
project_keyword = Table(
    "project_keyword",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("keyword_id", Integer, ForeignKey("keyword.id"), primary_key=True),
    extend_existing=True
)

class Project(Base):
    """Proje modeli."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=True)
    type = Column(String(50), nullable=False)  # "ara" veya "bitirme"
    status = Column(String, default=ProjectStatus.ACTIVE.value)
    student_capacity = Column(Integer, default=1)
    responsible_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    advisor_id = Column(Integer, ForeignKey("instructors.id"), nullable=True)
    co_advisor_id = Column(Integer, ForeignKey("instructors.id"), nullable=True)
    is_makeup = Column(Boolean, default=False)  # True: bütünleme, False: final
    is_active = Column(Boolean, default=True)
    
    # İlişkiler
    responsible = relationship("Instructor", foreign_keys=[responsible_id], back_populates="responsible_projects")
    advisor = relationship("Instructor", foreign_keys=[advisor_id], back_populates="advised_projects")
    co_advisor = relationship("Instructor", foreign_keys=[co_advisor_id], back_populates="co_advised_projects")
    assistants = relationship("Instructor", secondary=project_assistants, back_populates="assistant_projects")
    schedules = relationship("Schedule", back_populates="project")
    students = relationship("Student", secondary="project_student", back_populates="projects")
    keywords = relationship("Keyword", secondary=project_keyword, back_populates="projects")
    
    def __repr__(self):
        return f"<Project {self.title}>"