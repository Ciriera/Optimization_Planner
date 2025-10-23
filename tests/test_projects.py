"""
Project tests
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from pydantic import ValidationError

from app.crud import crud_project
from app.models.project import Project
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectStatus
from tests.utils import create_random_instructor, create_random_project

pytestmark = pytest.mark.asyncio

@pytest.mark.project
class TestProject:
    """Project CRUD operation tests"""

    async def test_create_project(self, db_session: AsyncSession):
        """Test project creation"""
        instructor = await create_random_instructor(db_session)
        project_in = ProjectCreate(
            title="Test Project",
            type="bitirme",
            responsible_id=instructor.id,
            advisor_id=instructor.id
        )
        project = await crud_project.create(db_session, obj_in=project_in)
        assert project.title == "Test Project"
        assert project.type == "bitirme"
        assert project.responsible_id == instructor.id
        assert project.advisor_id == instructor.id

    async def test_get_project(self, db_session: AsyncSession):
        """Test getting a project"""
        instructor = await create_random_instructor(db_session)
        project = await create_random_project(db_session, responsible_id=instructor.id)
        stored_project = await crud_project.get(db_session, id=project.id)
        assert stored_project
        assert project.id == stored_project.id
        assert project.type == stored_project.type
        assert project.responsible_id == stored_project.responsible_id

    async def test_get_projects_by_instructor(self, db_session: AsyncSession):
        """Test getting projects by instructor"""
        instructor1 = await create_random_instructor(db_session)
        instructor2 = await create_random_instructor(db_session)
        
        project1 = await create_random_project(db_session, responsible_id=instructor1.id)
        project2 = await create_random_project(db_session, responsible_id=instructor1.id)
        project3 = await create_random_project(db_session, responsible_id=instructor2.id)
        
        instructor1_projects = await crud_project.get_by_instructor(
            db_session,
            instructor_id=instructor1.id
        )
        assert len(instructor1_projects) == 2
        assert all(p.responsible_id == instructor1.id for p in instructor1_projects)

    async def test_get_projects_by_type(self, db_session: AsyncSession):
        """Test getting projects by type"""
        instructor = await create_random_instructor(db_session)
        project1 = await create_random_project(
            db_session,
            responsible_id=instructor.id,
            type="bitirme"
        )
        project2 = await create_random_project(
            db_session,
            responsible_id=instructor.id,
            type="ara"
        )
        
        bitirme_projects = await crud_project.get_by_type(db_session, type="bitirme")
        ara_projects = await crud_project.get_by_type(db_session, type="ara")
        
        assert any(p.id == project1.id for p in bitirme_projects)
        assert any(p.id == project2.id for p in ara_projects)

    async def test_update_project(self, db_session: AsyncSession):
        """Test updating a project"""
        instructor = await create_random_instructor(db_session)
        project = await create_random_project(db_session, responsible_id=instructor.id)
        
        project_update = ProjectUpdate(
            title="Updated Project",
            is_active=False
        )
        updated_project = await crud_project.update(
            db_session,
            db_obj=project,
            obj_in=project_update
        )
        assert updated_project.title == "Updated Project"
        assert updated_project.is_active is False
        assert updated_project.responsible_id == instructor.id  # Should not change

    async def test_delete_project(self, db_session: AsyncSession):
        """Test deleting a project"""
        instructor = await create_random_instructor(db_session)
        project = await create_random_project(db_session, responsible_id=instructor.id)
        
        await crud_project.remove(db_session, id=project.id)
        deleted_project = await crud_project.get(db_session, id=project.id)
        assert deleted_project is None

    async def test_get_multi_project(self, db_session: AsyncSession):
        """Çoklu proje getirme testleri"""
        instructor = await create_random_instructor(db_session)
        project1 = await create_random_project(db_session, responsible_id=instructor.id)
        project2 = await create_random_project(db_session, responsible_id=instructor.id, type="ara")
        projects = await crud_project.get_multi(db_session, skip=0, limit=100)
        assert len(projects) >= 2
        assert any(p.id == project1.id for p in projects)
        assert any(p.id == project2.id for p in projects)

    async def test_get_makeup_projects(self, db_session: AsyncSession):
        """Bütünleme projelerini getirme testleri"""
        instructor = await create_random_instructor(db_session)
        project1 = await create_random_project(db_session, responsible_id=instructor.id, is_makeup=True)
        project2 = await create_random_project(db_session, responsible_id=instructor.id, is_makeup=False)
        
        makeup_projects = await crud_project.get_makeup_projects(db_session)
        assert any(p.id == project1.id for p in makeup_projects)
        assert all(p.is_makeup for p in makeup_projects)

    async def test_invalid_project_type(self, db_session: AsyncSession):
        """Geçersiz proje tipi testleri"""
        instructor = await create_random_instructor(db_session)
        with pytest.raises(ValidationError):
            project_in = ProjectCreate(
                title="Invalid Project",
                type="invalid_type",
                responsible_id=instructor.id,
                advisor_id=instructor.id,
                is_makeup=False,
                status=ProjectStatus.ACTIVE
            )
            # Validation hatası oluşacak, create'e kadar gitmeyecek 