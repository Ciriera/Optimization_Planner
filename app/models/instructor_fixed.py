from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Table, Enum as SQLAEnum
from sqlalchemy.orm import relationship
from typing import Dict, Any
from app.db.base_class import Base
import enum

class InstructorType(str, enum.Enum):
    INSTRUCTOR = "instructor"  # Öğretim üyesi (hoca)
    ASSISTANT = "assistant"    # Araştırma görevlisi

# Instructor ve anahtar kelimeler arasındaki ilişki tablosu
instructor_keyword = Table(
    "instructor_keyword",
    Base.metadata,
    Column("instructor_id", Integer, ForeignKey("instructors.id"), primary_key=True),
    Column("keyword_id", Integer, ForeignKey("keyword.id"), primary_key=True),
    extend_existing=True
)

# Proje ve asistanlar arasındaki ilişki tablosu
project_assistants = Table(
    "project_assistants",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("instructor_id", Integer, ForeignKey("instructors.id"), primary_key=True),
    extend_existing=True
)

class Instructor(Base):
    """Öğretim üyesi veya araştırma görevlisi modeli."""
    __tablename__ = "instructors"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    type = Column(String(10), nullable=False)
    department = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String(255), nullable=False)
    research_interests = Column(Text, nullable=True)
    max_project_count = Column(Integer, default=5)
    bitirme_count = Column(Integer, default=0)
    ara_count = Column(Integer, default=0)
    total_load = Column(Integer, default=0)
    
    # İlişkiler
    responsible_projects = relationship("Project", foreign_keys="Project.responsible_id", back_populates="responsible")
    advised_projects = relationship("Project", foreign_keys="Project.advisor_id", back_populates="advisor")
    co_advised_projects = relationship("Project", foreign_keys="Project.co_advisor_id", back_populates="co_advisor")
    expertise_keywords = relationship("Keyword", secondary=instructor_keyword, back_populates="instructors")
    assistant_projects = relationship("Project", secondary=project_assistants, back_populates="assistants")
    
    def __repr__(self):
        return f"<Instructor {self.full_name}, {self.type}>"
    
    def to_dict(self):
        """Convert instructor to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "type": self.type,
            "department": self.department,
            "is_active": self.is_active,
            "research_interests": self.research_interests,
            "max_project_count": self.max_project_count,
            "bitirme_count": self.bitirme_count,
            "ara_count": self.ara_count,
            "total_load": self.total_load
        }
        
    @staticmethod
    def _convert_instructor_type(type_str: str) -> InstructorType:
        """Convert string type to InstructorType enum"""
        # Map legacy values to enum values
        type_mapping = {
            "professor": InstructorType.INSTRUCTOR,
            "research_assistant": InstructorType.ASSISTANT,
            "hoca": InstructorType.INSTRUCTOR,
            "aras_gor": InstructorType.ASSISTANT,
        }
        
        if type_str in type_mapping:
            return type_mapping[type_str]
        
        # Try direct conversion if it's already an enum value
        try:
            return InstructorType(type_str)
        except ValueError:
            # Default to INSTRUCTOR if unknown
            return InstructorType.INSTRUCTOR 