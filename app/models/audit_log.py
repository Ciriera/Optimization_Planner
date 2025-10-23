"""
Denetim günlüğü modeli
"""
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

class AuditLog(Base):
    """Denetim günlüğü modeli."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # create, update, delete
    resource_type = Column(String, nullable=False)  # instructor, project, etc.
    resource_id = Column(Integer, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # İlişkiler
    user = relationship("User", back_populates="audit_logs")