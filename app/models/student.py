from sqlalchemy import Column, Integer, String, Boolean, Float, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.base_class import Base

# İlişki tablosu tanımı
project_student = Table(
    "project_student",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("student_id", Integer, ForeignKey("student.id"), primary_key=True)
)

# Student ve anahtar kelimeler arasındaki ilişki tablosu
student_keyword = Table(
    "student_keyword",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("student.id"), primary_key=True),
    Column("keyword_id", Integer, ForeignKey("keyword.id"), primary_key=True),
    extend_existing=True
)

class Student(Base):
    __tablename__ = "student"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    student_number = Column(String(20), unique=True, index=True, nullable=False)
    department = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String(255), nullable=False)
    gpa = Column(Float)
    interests = Column(Text, nullable=True)

    # Relationships
    projects = relationship("Project", secondary="project_student", back_populates="students")
    preferred_keywords = relationship("Keyword", secondary=student_keyword, back_populates="interested_students")
    
    def __repr__(self):
        return f"<Student {self.full_name}, {self.student_number}>" 