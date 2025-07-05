from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class Classroom(Base):
    """Sınıf modeli."""
    
    __tablename__ = "classrooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    capacity = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    location = Column(String(100), nullable=True)
    
    # İlişkiler
    schedules = relationship("Schedule", back_populates="classroom")
    
    def __repr__(self):
        return f"<Classroom {self.name}>" 