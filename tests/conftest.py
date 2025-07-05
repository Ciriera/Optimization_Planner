"""
Test fixtures
"""
import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole
from app.schemas.user import UserCreate
from tests.utils import create_random_user

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Test database engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=True  # Show SQL logs
)

# Test session factory
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Event loop fixture."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Test database session fixture."""
    
    # Clean database and recreate tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create new session for test
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Test client fixture."""
    
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Disable response validation to avoid serialization issues
    app.router.default_response_class.validate_response = False
    
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    
    # Clean up dependency override after test
    app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> User:
    """Admin user fixture."""
    user_in = UserCreate(
        email="admin@example.com",
        username="admin",
        password="admin123",
        full_name="Test Admin",
        role=UserRole.ADMIN,
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
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture(scope="function")
async def instructor_user(db_session: AsyncSession) -> User:
    """Instructor user fixture."""
    return await create_random_user(db_session, role=UserRole.INSTRUCTOR)

@pytest_asyncio.fixture(scope="function")
async def admin_token(admin_user: User) -> str:
    """Admin token fixture."""
    return create_access_token(
        subject=admin_user.email, 
        data={"role": admin_user.role.value}
    )

@pytest_asyncio.fixture(scope="function")
async def instructor_token(instructor_user: User) -> str:
    """Instructor token fixture."""
    return create_access_token(
        subject=instructor_user.email,
        data={"role": instructor_user.role.value}
    ) 