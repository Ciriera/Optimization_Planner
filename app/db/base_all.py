"""
Bu dosya tüm modelleri tek bir yerden import ediyor.
Bu sayede döngüsel bağımlılık sorunları çözülüyor.
"""
# Import base
from app.db.base_class import Base  # noqa

# Import all models
from app.models.audit_log import AuditLog  # noqa
from app.models.instructor import Instructor  # noqa
from app.models.project import Project  # noqa
from app.models.classroom import Classroom  # noqa
from app.models.timeslot import TimeSlot  # noqa
from app.models.schedule import Schedule  # noqa
from app.models.algorithm import AlgorithmRun  # noqa
from app.models.user import User  # noqa 