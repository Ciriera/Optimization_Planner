"""
Configuration models
"""

from sqlalchemy import Column, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base_class import Base


class DynamicConfig(Base):
    """Dynamic system configuration storage."""
    
    __tablename__ = "dynamic_config"
    
    id = Column(Integer, primary_key=True, index=True)
    config_data = Column(JSON, nullable=False, default=dict)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
