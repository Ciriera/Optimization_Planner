"""
Test configuration and fixtures.
"""
import pytest
import asyncio
import os
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base_class import Base
from app.db.base import get_db
from app.main import app


# Test database - PostgreSQL
SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:Fer.153624987@localhost:5432/ceng_project_test")
SQLALCHEMY_ASYNC_DATABASE_URL = os.getenv("TEST_ASYNC_DATABASE_URL", "postgresql+asyncpg://postgres:Fer.153624987@localhost:5432/ceng_project_test")

# Sync engine for metadata operations (PostgreSQL)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # PostgreSQL için connection check
    echo=False
)

# Async engine for actual testing (PostgreSQL)
async_engine = create_async_engine(
    SQLALCHEMY_ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncTestingSessionLocal = AsyncSession(async_engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def db() -> Generator:
    """Create test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
async def async_db() -> AsyncGenerator:
    """Create async test database session."""
    Base.metadata.create_all(bind=engine)
    async with AsyncSession(async_engine) as session:
        try:
            yield session
        finally:
            Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """Create test client."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with app.test_client() as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "title": "Test Project",
        "description": "Test project description",
        "project_type": "ara",
        "status": "active",
        "student_name": "Test Student",
        "student_number": "12345678",
        "supervisor_id": 1,
        "keywords": ["test", "optimization"]
    }


@pytest.fixture
def sample_instructor_data():
    """Sample instructor data for testing."""
    return {
        "name": "Test Instructor",
        "email": "test@example.com",
        "instructor_type": "instructor",
        "max_projects": 5,
        "keywords": ["optimization", "algorithms"]
    }


@pytest.fixture
def sample_classroom_data():
    """Sample classroom data for testing."""
    return {
        "name": "D106",
        "capacity": 30,
        "location": "Test Building",
        "is_active": True
    }


@pytest.fixture
def sample_timeslot_data():
    """Sample timeslot data for testing."""
    return {
        "start_time": "09:00",
        "end_time": "10:00",
        "is_morning": True,
        "is_active": True
    }


@pytest.fixture
def test_data():
    """Comprehensive test data for algorithm testing."""
    return {
        'projects': [
            {'id': 1, 'title': 'Bitirme Projesi 1', 'type': 'bitirme', 'responsible_id': 1, 'advisor_id': 1, 'co_advisor_id': 2},
            {'id': 2, 'title': 'Ara Proje 1', 'type': 'ara', 'responsible_id': 2, 'advisor_id': 2, 'co_advisor_id': 3},
            {'id': 3, 'title': 'Bitirme Projesi 2', 'type': 'bitirme', 'responsible_id': 3, 'advisor_id': 3, 'co_advisor_id': 1}
        ],
        'instructors': [
            {'id': 1, 'name': 'Prof. Dr. Ahmet Yılmaz', 'type': 'professor', 'department': 'Bilgisayar Mühendisliği'},
            {'id': 2, 'name': 'Doç. Dr. Mehmet Kaya', 'type': 'professor', 'department': 'Bilgisayar Mühendisliği'},
            {'id': 3, 'name': 'Dr. Ayşe Demir', 'type': 'assistant_professor', 'department': 'Bilgisayar Mühendisliği'},
            {'id': 4, 'name': 'Arş. Gör. Ali Veli', 'type': 'research_assistant', 'department': 'Bilgisayar Mühendisliği'}
        ],
        'classrooms': [
            {'id': 1, 'name': 'D106', 'capacity': 20, 'location': 'B Blok'},
            {'id': 2, 'name': 'D107', 'capacity': 20, 'location': 'B Blok'},
            {'id': 3, 'name': 'D108', 'capacity': 20, 'location': 'B Blok'},
            {'id': 4, 'name': 'D109', 'capacity': 20, 'location': 'B Blok'},
            {'id': 5, 'name': 'D110', 'capacity': 20, 'location': 'B Blok'}
        ],
        'timeslots': [
            {'id': 1, 'start_time': '09:00', 'end_time': '09:30', 'session_type': 'morning', 'is_morning': True},
            {'id': 2, 'start_time': '09:30', 'end_time': '10:00', 'session_type': 'morning', 'is_morning': True},
            {'id': 3, 'start_time': '10:00', 'end_time': '10:30', 'session_type': 'morning', 'is_morning': True},
            {'id': 4, 'start_time': '10:30', 'end_time': '11:00', 'session_type': 'morning', 'is_morning': True},
            {'id': 5, 'start_time': '11:00', 'end_time': '11:30', 'session_type': 'morning', 'is_morning': True},
            {'id': 6, 'start_time': '13:00', 'end_time': '13:30', 'session_type': 'afternoon', 'is_morning': False},
            {'id': 7, 'start_time': '13:30', 'end_time': '14:00', 'session_type': 'afternoon', 'is_morning': False},
            {'id': 8, 'start_time': '14:00', 'end_time': '14:30', 'session_type': 'afternoon', 'is_morning': False}
        ]
    }