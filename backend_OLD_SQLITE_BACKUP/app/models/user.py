from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base_class import Base

class UserRole(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    RESEARCH_ASSISTANT = "research_assistant"

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.INSTRUCTOR)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    department = relationship("Department", back_populates="users")
    projects = relationship("Project", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")
