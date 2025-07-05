from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # Örn: D106, D107
    capacity = Column(Integer, default=30)
    location = Column(String, nullable=True)
    
    # İlişkiler
    schedules = relationship("Schedule", back_populates="classroom")

    class Config:
        orm_mode = True 