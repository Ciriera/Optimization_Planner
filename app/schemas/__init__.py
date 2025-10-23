"""
Schema definitions.
"""
# Import schemas in correct order to avoid circular imports
from .base import BaseSchema
from .user import User, UserCreate, UserUpdate, UserRoleUpdate, UserLanguageUpdate
from .token import Token, TokenPayload
from .classroom import Classroom, ClassroomCreate, ClassroomUpdate
from .timeslot import TimeSlot, TimeSlotCreate, TimeSlotUpdate
from .instructor import Instructor, InstructorCreate, InstructorUpdate
from .project import Project, ProjectCreate, ProjectUpdate
from .schedule import Schedule, ScheduleCreate, ScheduleUpdate
from .audit_log import AuditLog, AuditLogCreate
from .algorithm import (
    AlgorithmRun,
    AlgorithmRunCreate,
    AlgorithmRunUpdate,
    AlgorithmRunWithResults,
    AlgorithmRunResponse,
)
from .msg import Msg

# Import with relations after basic schemas are imported
from .classroom import ClassroomWithRelations, update_forward_refs as update_classroom_refs
from .timeslot import TimeSlotWithRelations, update_forward_refs as update_timeslot_refs
from .instructor import InstructorWithRelations, update_forward_refs as update_instructor_refs
from .project import ProjectWithRelations, update_forward_refs as update_project_refs
from .schedule import ScheduleWithRelations, update_forward_refs as update_schedule_refs

# Update all forward references to resolve circular dependencies
def update_all_forward_refs():
    """Update all forward references to resolve circular dependencies"""
    update_classroom_refs()
    update_timeslot_refs()
    update_instructor_refs()
    update_project_refs()
    update_schedule_refs()

# Automatically update forward references when the module is loaded
update_all_forward_refs() 