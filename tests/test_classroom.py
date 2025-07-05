"""
Classroom tests
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import crud_classroom
from app.models.classroom import Classroom
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate
from tests.utils import create_random_classroom

pytestmark = pytest.mark.asyncio

async def test_create_classroom(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Test classroom creation"""
    classroom_data = {
        "name": "D101",
        "capacity": 30,
        "location": "D Block",
        "is_active": True
    }
    response = await client.post(
        "/api/v1/classrooms/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=classroom_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == classroom_data["name"]
    assert data["capacity"] == classroom_data["capacity"]
    assert data["location"] == classroom_data["location"]
    assert data["is_active"] == classroom_data["is_active"]

async def test_read_classrooms(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Test getting all classrooms"""
    # Create test classrooms
    for _ in range(3):
        await create_random_classroom(db_session)

    response = await client.get(
        "/api/v1/classrooms/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3

async def test_read_classroom(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Test getting a single classroom"""
    classroom = await create_random_classroom(db_session)
    response = await client.get(
        f"/api/v1/classrooms/{classroom.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == classroom.id
    assert data["name"] == classroom.name
    assert data["capacity"] == classroom.capacity

async def test_update_classroom(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Test updating a classroom"""
    classroom = await create_random_classroom(db_session)
    update_data = {
        "capacity": 40,
        "is_active": False
    }
    response = await client.put(
        f"/api/v1/classrooms/{classroom.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["capacity"] == update_data["capacity"]
    assert data["is_active"] == update_data["is_active"]
    assert data["id"] == classroom.id

async def test_delete_classroom(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Test deleting a classroom"""
    classroom = await create_random_classroom(db_session)
    response = await client.delete(
        f"/api/v1/classrooms/{classroom.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204

    # Verify deletion
    response = await client.get(
        f"/api/v1/classrooms/{classroom.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404

async def test_get_classroom_schedule(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Test getting classroom schedule"""
    classroom = await create_random_classroom(db_session)
    response = await client.get(
        f"/api/v1/classrooms/{classroom.id}/schedule",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

async def test_get_classroom_availability(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Test getting classroom availability"""
    classroom = await create_random_classroom(db_session)
    response = await client.get(
        f"/api/v1/classrooms/{classroom.id}/availability",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"date": "2024-03-20"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "available_slots" in data

async def test_get_active_classrooms(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Test getting only active classrooms"""
    # Create both active and inactive classrooms
    await create_random_classroom(db_session)  # Active by default
    classroom = await create_random_classroom(db_session)
    classroom.is_active = False
    db_session.add(classroom)
    await db_session.commit()

    response = await client.get(
        "/api/v1/classrooms/active",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all(c["is_active"] for c in data)