"""
Test yardımcı fonksiyonları
"""
import random
import string
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Union, Any
import jwt

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.instructor import Instructor, InstructorType
from app.models.project import Project
from app.models.classroom import Classroom
from app.models.timeslot import TimeSlot
from app.models.user import User, UserRole
from app.crud import crud_instructor, crud_project, crud_classroom, crud_timeslot
from app.schemas.instructor import InstructorCreate
from app.schemas.project import ProjectCreate
from app.schemas.classroom import ClassroomCreate
from app.schemas.timeslot import TimeSlotCreate
from app.schemas.user import UserCreate

fake = Faker()

def random_lower_string(length: int = 32) -> str:
    """Rastgele küçük harfli string üretir"""
    return "".join(random.choices(string.ascii_lowercase, k=length))

def random_email() -> str:
    """Rastgele email üretir"""
    return f"{random_lower_string(8)}@{random_lower_string(6)}.com"

async def create_random_user(db: AsyncSession) -> User:
    """Test için rastgele kullanıcı oluşturur"""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(
        email=email,
        username=email.split("@")[0],
        password=password,
        full_name=fake.name(),
        role=UserRole.INSTRUCTOR,
        is_active=True
    )
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=user_in.is_active
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def create_random_instructor(db: AsyncSession) -> Instructor:
    """Test için rastgele öğretim elemanı oluşturur"""
    user = await create_random_user(db)
    
    # Randomly choose between instructor and assistant types
    instructor_type = random.choice([InstructorType.INSTRUCTOR.value, InstructorType.ASSISTANT.value])
    
    # Only include valid fields for the Instructor model
    instructor = Instructor(
        name=user.full_name,
        user_id=user.id,
        type=instructor_type,
        department="Computer Engineering",
        bitirme_count=0,
        ara_count=0,
        total_load=0
    )
    
    db.add(instructor)
    await db.commit()
    await db.refresh(instructor)
    return instructor

async def create_random_project(
    db: AsyncSession,
    *,
    responsible_id: Optional[int] = None,
    advisor_id: Optional[int] = None,
    type: str = None,
    is_makeup: bool = False
) -> Project:
    """Test için rastgele proje oluşturur"""
    if not responsible_id:
        instructor = await create_random_instructor(db)
        responsible_id = instructor.id
    
    # advisor_id belirtilmemişse responsible_id değerini kullan
    if advisor_id is None:
        advisor_id = responsible_id
    
    if not type:
        type = random.choice(["ara", "bitirme"])
    elif type == "final":
        type = "bitirme"
    elif type == "interim":
        type = "ara"
    
    project_in = ProjectCreate(
        title=fake.sentence(),
        type=type,
        responsible_id=responsible_id,
        advisor_id=advisor_id,
        is_makeup=is_makeup
    )
    project = await crud_project.create(db, obj_in=project_in)
    return project

async def create_random_classroom(db: AsyncSession) -> Classroom:
    """Test için rastgele sınıf oluşturur"""
    classroom_in = ClassroomCreate(
        name=f"D{random.randint(100, 999)}",
        capacity=random.randint(20, 40)
    )
    classroom = await crud_classroom.create(db, obj_in=classroom_in)
    return classroom

async def create_random_timeslot(db: AsyncSession) -> TimeSlot:
    """Test için rastgele zaman dilimi oluşturur"""
    # Saat ve dakika değerlerini ayrı ayrı oluştur
    hour = random.randint(9, 16)  # 9:00 - 16:00 arası
    minute = random.choice([0, 30])  # Yarım saatlik dilimler
    
    # time nesneleri oluştur
    start_time = time(hour=hour, minute=minute)
    end_time = time(hour=hour + 1 if minute == 0 else hour, minute=0 if minute == 30 else 30)
    
    timeslot_in = TimeSlotCreate(
        start_time=start_time,
        end_time=end_time,
        is_morning=hour < 12
    )
    timeslot = await crud_timeslot.create(db, obj_in=timeslot_in)
    return timeslot

def get_token_headers(token: str) -> Dict[str, str]:
    """Token başlığı oluşturur"""
    return {"Authorization": f"Bearer {token}"}

def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    data: Dict[str, Any] = None
) -> str:
    """Test için access token üretir"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    if data:
        to_encode.update(data)
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt 