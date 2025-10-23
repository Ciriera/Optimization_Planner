"""
Test utility functions
"""
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.project import Project, ProjectType, ProjectStatus
from app.models.classroom import Classroom
from app.models.timeslot import TimeSlot
from app.models.instructor import Instructor, InstructorType

def random_lower_string(length: int = 32) -> str:
    """Generate a random lowercase string."""
    return "".join(random.choices(string.ascii_lowercase, k=length))

def random_email() -> str:
    """Generate a random email."""
    return f"{random_lower_string(10)}@{random_lower_string(6)}.com"

async def create_random_user(
    db: AsyncSession, 
    role: UserRole = UserRole.INSTRUCTOR,
    is_active: bool = True
) -> User:
    """Create a random user."""
    email = random_email()
    password = random_lower_string()
    full_name = random_lower_string()
    username = random_lower_string(8)
    
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=role,
        is_active=is_active
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def create_random_instructor(
    db: AsyncSession,
    type_value: str = None,
    department: str = None,
    bitirme_count: int = 2,
    ara_count: int = 3,
    total_load: int = 5,
    **kwargs  # Added to capture any extra parameters
) -> Instructor:
    """Create a random instructor."""
    # Debug: print any extra kwargs
    if kwargs:
        print(f"DEBUG: Extra kwargs passed to create_random_instructor: {kwargs}")
        
    user = await create_random_user(db, role=UserRole.INSTRUCTOR)
    
    if type_value is None:
        # Randomly select instructor type
        type_value = random.choice([InstructorType.INSTRUCTOR.value, InstructorType.ASSISTANT.value])
    
    if department is None:
        department = f"Department {random_lower_string(5)}"
    
    # Only include the valid parameters for the Instructor model
    instructor_data = {
        "name": user.full_name,
        "user_id": user.id,
        "type": type_value,
        "department": department,
        "bitirme_count": bitirme_count,
        "ara_count": ara_count,
        "total_load": total_load
    }
    
    print(f"DEBUG: Creating Instructor with data: {instructor_data}")
    
    instructor = Instructor(**instructor_data)
    db.add(instructor)
    await db.commit()
    await db.refresh(instructor)
    return instructor

async def create_random_project(
    db: AsyncSession,
    responsible_id: int,
    project_type: str = ProjectType.INTERIM,
    is_makeup: bool = False,
    status: str = ProjectStatus.ACTIVE
) -> Project:
    """Create a random project."""
    title = f"Project {random_lower_string(8)}"
    
    project = Project(
        title=title,
        type=project_type,
        responsible_id=responsible_id,
        is_makeup=is_makeup
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

async def create_random_classroom(
    db: AsyncSession,
    capacity: int = 30,
    is_active: bool = True
) -> Classroom:
    """Create a random classroom."""
    name = f"D{random.randint(100, 999)}"
    
    classroom = Classroom(
        name=name,
        capacity=capacity,
        is_active=is_active
    )
    db.add(classroom)
    await db.commit()
    await db.refresh(classroom)
    return classroom

async def create_random_timeslot(
    db: AsyncSession,
    is_morning: bool = True,
    is_active: bool = True
) -> TimeSlot:
    """Create a random timeslot."""
    if is_morning:
        base_hour = random.randint(9, 11)
    else:
        base_hour = random.randint(13, 16)
    
    start_time = datetime.now().replace(hour=base_hour, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(minutes=30)
    
    timeslot = TimeSlot(
        start_time=start_time,
        end_time=end_time,
        is_morning=is_morning,
        is_active=is_active
    )
    db.add(timeslot)
    await db.commit()
    await db.refresh(timeslot)
    return timeslot 