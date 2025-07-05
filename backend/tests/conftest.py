import asyncio
import pytest
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole

# Test veritabanı URL'si
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Test veritabanı motoru
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Test oturum fabrikası
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Event loop fixture."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Test veritabanı oturumu fixture'ı."""
    # Veritabanı tablolarını oluştur
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[TestClient, None]:
    """Test istemcisi fixture'ı."""
    async def override_get_db():
        try:
            yield db_session
        finally:
            await db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    async with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
async def admin_token(client: TestClient, db_session: AsyncSession) -> str:
    """Admin kullanıcı token fixture'ı."""
    # Admin kullanıcı oluştur
    admin_user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("admin123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=True
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    # Token al
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "admin123"}
    )
    return response.json()["access_token"]

@pytest.fixture(scope="function")
async def normal_user_token(client: TestClient, db_session: AsyncSession) -> str:
    """Normal kullanıcı token fixture'ı."""
    # Normal kullanıcı oluştur
    user = User(
        email="user@example.com",
        username="user",
        hashed_password=get_password_hash("user123"),
        full_name="Normal User",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Token al
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "user@example.com", "password": "user123"}
    )
    return response.json()["access_token"]

@pytest.fixture(scope="function")
async def superuser_token_headers(admin_token: str) -> dict:
    """Admin kullanıcı token header'ları fixture'ı."""
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture(scope="function")
async def normal_user_token_headers(normal_user_token: str) -> dict:
    """Normal kullanıcı token header'ları fixture'ı."""
    return {"Authorization": f"Bearer {normal_user_token}"} 