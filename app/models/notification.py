"""
Notification log model for tracking email notifications sent to instructors.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum as SQLAEnum, TypeDecorator
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base_class import Base


class NotificationStatus(str, enum.Enum):
    """Notification status enum"""
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"
    FAILED = "failed"


class EnumValueType(TypeDecorator):
    """Custom type that stores enum values (not names) as strings"""
    impl = String
    cache_ok = True
    
    def __init__(self, enum_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_class = enum_class
    
    def process_bind_param(self, value, dialect):
        """Convert enum to its value (string) when saving to DB"""
        if value is None:
            return None
        if isinstance(value, enum.Enum):
            return value.value
        if isinstance(value, str):
            # If it's already a string, check if it's a valid enum value
            try:
                enum_member = self.enum_class(value)
                return enum_member.value
            except ValueError:
                return value
        return str(value)
    
    def process_result_value(self, value, dialect):
        """Convert string back to enum when reading from DB"""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value
        try:
            return self.enum_class(value)
        except ValueError:
            return value


class NotificationLog(Base):
    """Email notification log model."""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=True, index=True)  # Nullable for custom emails
    instructor_email = Column(String(200), nullable=False, index=True)
    instructor_name = Column(String(200), nullable=True)
    
    # Planner reference (optional - can be null if planner is deleted)
    planner_timestamp = Column(DateTime, nullable=True)  # When planner was generated
    
    # Email details
    subject = Column(String(500), nullable=True)
    status = Column(EnumValueType(NotificationStatus, length=20), nullable=False, default=NotificationStatus.PENDING, index=True)
    error_message = Column(Text, nullable=True)
    
    # Tracking
    sent_at = Column(DateTime, nullable=True)
    attempt_count = Column(Integer, default=0)
    
    # Additional metadata
    meta_data = Column(JSON, nullable=True)  # Store assignment count, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    instructor = relationship("Instructor", foreign_keys=[instructor_id])
    
    def __repr__(self):
        return f"<NotificationLog {self.id} - {self.instructor_email} - {self.status}>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "instructor_id": self.instructor_id,
            "instructor_email": self.instructor_email,
            "instructor_name": self.instructor_name,
            "planner_timestamp": self.planner_timestamp.isoformat() if self.planner_timestamp else None,
            "subject": self.subject,
            "status": self.status.value if isinstance(self.status, enum.Enum) else self.status,
            "error_message": self.error_message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "attempt_count": self.attempt_count,
            "metadata": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

