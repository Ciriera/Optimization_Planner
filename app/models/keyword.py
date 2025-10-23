from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Keyword(Base):
    __tablename__ = "keyword"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    
    # Relationships
    projects = relationship("Project", secondary="project_keyword", back_populates="keywords")
    instructors = relationship("Instructor", secondary="instructor_keyword", back_populates="expertise_keywords")
    interested_students = relationship("Student", secondary="student_keyword", back_populates="preferred_keywords") 