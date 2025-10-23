import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.instructor import Instructor
from app.models.schedule import Schedule
from app.models.classroom import Classroom
from app.models.timeslot import TimeSlot
from app.models.user import User, UserRole
from app.core.security import get_password_hash

pytestmark = pytest.mark.asyncio

async def test_generate_pdf_report(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """PDF raporu oluşturma testi"""
    # Test verileri oluştur
    await create_test_data(db_session)

    response = await client.post(
        "/api/v1/reports/pdf",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "report_type": "schedule",
            "filters": {
                "date_range": ["2024-01-01", "2024-12-31"],
                "project_types": ["final", "interim"]
            }
        }
    )
    assert response.status_code == 202  # Accepted
    data = response.json()
    assert "task_id" in data

async def test_generate_excel_report(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Excel raporu oluşturma testi"""
    # Test verileri oluştur
    await create_test_data(db_session)

    response = await client.post(
        "/api/v1/reports/excel",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "report_type": "workload",
            "filters": {
                "department": "Test Department",
                "semester": "2024-spring"
            }
        }
    )
    assert response.status_code == 202  # Accepted
    data = response.json()
    assert "task_id" in data

async def test_generate_workload_stats(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """İş yükü istatistikleri raporu testi"""
    # Test verileri oluştur
    await create_test_data(db_session)

    response = await client.get(
        "/api/v1/reports/workload-stats",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={
            "department": "Test Department",
            "semester": "2024-spring"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "instructor_stats" in data
    assert "department_summary" in data

async def test_get_task_status(client: AsyncClient, admin_token: str):
    """Rapor oluşturma görevi durumu kontrolü testi"""
    # Önce bir rapor oluşturma görevi başlat
    report_response = await client.post(
        "/api/v1/reports/pdf",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "report_type": "schedule",
            "filters": {
                "date_range": ["2024-01-01", "2024-12-31"]
            }
        }
    )
    task_id = report_response.json()["task_id"]

    # Görev durumunu kontrol et
    response = await client.get(
        f"/api/v1/reports/task-status/{task_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "progress" in data
    assert data["status"] in ["pending", "processing", "completed", "failed"]

async def test_normal_user_access(client: AsyncClient, normal_user_token: str):
    """Normal kullanıcı rapor erişimi testi"""
    response = await client.post(
        "/api/v1/reports/pdf",
        headers={"Authorization": f"Bearer {normal_user_token}"},
        json={
            "report_type": "schedule",
            "filters": {
                "date_range": ["2024-01-01", "2024-12-31"]
            }
        }
    )
    assert response.status_code == 403  # Forbidden

async def create_test_data(db_session: AsyncSession):
    """Test verileri oluşturma yardımcı fonksiyonu"""
    # Kullanıcı oluştur
    user = User(
        email="instructor@example.com",
        username="instructor",
        hashed_password=get_password_hash("test123"),
        full_name="Test Instructor",
        role=UserRole.INSTRUCTOR,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Öğretim elemanı oluştur
    instructor = Instructor(
        type="professor",
        department="Test Department",
        user_id=user.id
    )
    db_session.add(instructor)
    await db_session.commit()
    await db_session.refresh(instructor)

    # Proje oluştur
    project = Project(
        title="Test Project",
        type="final",
        responsible_id=instructor.id,
        is_active=True
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Sınıf oluştur
    classroom = Classroom(
        name="Test Classroom",
        capacity=30,
        is_active=True
    )
    db_session.add(classroom)
    await db_session.commit()
    await db_session.refresh(classroom)

    # Zaman dilimi oluştur
    timeslot = TimeSlot(
        start_time="09:00",
        end_time="10:00",
        is_morning=True
    )
    db_session.add(timeslot)
    await db_session.commit()
    await db_session.refresh(timeslot)

    # Planlama oluştur
    schedule = Schedule(
        project_id=project.id,
        classroom_id=classroom.id,
        timeslot_id=timeslot.id,
        is_makeup=False
    )
    db_session.add(schedule)
    await db_session.commit() 