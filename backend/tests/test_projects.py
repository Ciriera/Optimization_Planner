import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.instructor import Instructor
from app.models.user import User, UserRole
from app.core.security import get_password_hash

pytestmark = pytest.mark.asyncio

async def test_create_project(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Proje oluşturma testi"""
    # Önce bir öğretim elemanı oluştur
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
    await db_session.commit()
    await db_session.refresh(instructor)

    response = await client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Test Project",
            "type": "final",
            "responsible_id": instructor.id,
            "is_active": True
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Project"
    assert data["type"] == "final"

async def test_get_project(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Proje getirme testi"""
    # Önce bir proje oluştur
    project = Project(
        title="Test Project",
        type="final",
        responsible_id=1,
        is_active=True
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    response = await client.get(
        f"/api/v1/projects/{project.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Project"
    assert data["type"] == "final"

async def test_update_project(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Proje güncelleme testi"""
    # Önce bir proje oluştur
    project = Project(
        title="Test Project",
        type="final",
        responsible_id=1,
        is_active=True
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    response = await client.put(
        f"/api/v1/projects/{project.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Updated Project",
            "type": "interim",
            "is_active": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Project"
    assert data["type"] == "interim"
    assert not data["is_active"]

async def test_delete_project(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Proje silme testi"""
    # Önce bir proje oluştur
    project = Project(
        title="Test Project",
        type="final",
        responsible_id=1,
        is_active=True
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    response = await client.delete(
        f"/api/v1/projects/{project.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204

    # Silinen projeyi kontrol et
    result = await db_session.get(Project, project.id)
    assert result is None

async def test_list_projects(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Projeleri listeleme testi"""
    # Birkaç proje oluştur
    projects = [
        Project(
            title=f"Test Project {i}",
            type="final",
            responsible_id=1,
            is_active=True
        )
        for i in range(3)
    ]
    for project in projects:
        db_session.add(project)
    await db_session.commit()

    response = await client.get(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3

async def test_project_validation(client: AsyncClient, admin_token: str):
    """Proje doğrulama testi"""
    # Geçersiz proje tipi
    response = await client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Test Project",
            "type": "invalid_type",  # Geçersiz tip
            "responsible_id": 1,
            "is_active": True
        }
    )
    assert response.status_code == 422

    # Boş başlık
    response = await client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "",  # Boş başlık
            "type": "final",
            "responsible_id": 1,
            "is_active": True
        }
    )
    assert response.status_code == 422 