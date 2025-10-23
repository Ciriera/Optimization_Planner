import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classroom import Classroom
from app.models.timeslot import TimeSlot
from app.models.schedule import Schedule
from app.models.project import Project
from app.models.instructor import Instructor
from app.models.user import User, UserRole
from app.core.security import get_password_hash

pytestmark = pytest.mark.asyncio

async def test_create_classroom(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Sınıf oluşturma testi"""
    response = await client.post(
        "/api/v1/classrooms/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Test Classroom",
            "capacity": 30,
            "is_active": True
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Classroom"
    assert data["capacity"] == 30
    assert data["is_active"]

async def test_create_timeslot(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Zaman dilimi oluşturma testi"""
    start_time = datetime.now().replace(microsecond=0)
    end_time = start_time + timedelta(hours=1)

    response = await client.post(
        "/api/v1/timeslots/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "is_morning": True
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["start_time"] == start_time.isoformat()
    assert data["end_time"] == end_time.isoformat()
    assert data["is_morning"]

async def test_schedule_assignment(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Proje atama testi"""
    # Gerekli nesneleri oluştur
    classroom = Classroom(name="Test Classroom", capacity=30, is_active=True)
    db_session.add(classroom)

    start_time = datetime.now().replace(microsecond=0)
    end_time = start_time + timedelta(hours=1)
    timeslot = TimeSlot(
        start_time=start_time,
        end_time=end_time,
        is_morning=True
    )
    db_session.add(timeslot)

    user = User(
        email="instructor@example.com",
        username="instructor",
        hashed_password=get_password_hash("instructor123"),
        full_name="Test Instructor",
        role=UserRole.INSTRUCTOR,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    instructor = Instructor(
        type="professor",
        department="Test Department",
        user_id=user.id
    )
    db_session.add(instructor)

    project = Project(
        title="Test Project",
        type="final",
        responsible_id=instructor.id,
        is_active=True
    )
    db_session.add(project)
    await db_session.commit()

    response = await client.post(
        "/api/v1/schedules/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "project_id": project.id,
            "classroom_id": classroom.id,
            "timeslot_id": timeslot.id,
            "is_makeup": False
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == project.id
    assert data["classroom_id"] == classroom.id
    assert data["timeslot_id"] == timeslot.id
    assert not data["is_makeup"]

async def test_schedule_conflict(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Çakışma kontrolü testi"""
    # İlk atamayı yap
    classroom = Classroom(name="Test Classroom", capacity=30, is_active=True)
    db_session.add(classroom)

    start_time = datetime.now().replace(microsecond=0)
    end_time = start_time + timedelta(hours=1)
    timeslot = TimeSlot(
        start_time=start_time,
        end_time=end_time,
        is_morning=True
    )
    db_session.add(timeslot)

    project1 = Project(
        title="Test Project 1",
        type="final",
        responsible_id=1,
        is_active=True
    )
    db_session.add(project1)

    project2 = Project(
        title="Test Project 2",
        type="final",
        responsible_id=1,
        is_active=True
    )
    db_session.add(project2)
    await db_session.commit()

    # İlk atama
    schedule1 = Schedule(
        project_id=project1.id,
        classroom_id=classroom.id,
        timeslot_id=timeslot.id,
        is_makeup=False
    )
    db_session.add(schedule1)
    await db_session.commit()

    # Çakışan atama denemesi
    response = await client.post(
        "/api/v1/schedules/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "project_id": project2.id,
            "classroom_id": classroom.id,
            "timeslot_id": timeslot.id,
            "is_makeup": False
        }
    )
    assert response.status_code == 409  # Conflict

async def test_list_available_slots(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Müsait zaman dilimlerini listeleme testi"""
    # Birkaç zaman dilimi oluştur
    start_time = datetime.now().replace(microsecond=0)
    timeslots = []
    for i in range(3):
        slot_start = start_time + timedelta(hours=i)
        slot_end = slot_start + timedelta(minutes=30)
        timeslot = TimeSlot(
            start_time=slot_start,
            end_time=slot_end,
            is_morning=(i < 2)
        )
        timeslots.append(timeslot)
        db_session.add(timeslot)
    await db_session.commit()

    response = await client.get(
        "/api/v1/schedules/available-slots",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3 