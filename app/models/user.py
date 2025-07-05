from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLAEnum
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base

class UserRole(str, enum.Enum):
    """Kullanıcı rolleri"""
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    ASSISTANT = "assistant"

class User(Base):
    """Kullanıcı modeli."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(SQLAEnum(UserRole), nullable=False, default=UserRole.INSTRUCTOR)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    language = Column(String(2), default="tr")  # 'tr' veya 'en'
    
    # İlişkiler
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email}, {self.role}>" 