from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session

# Async session uyumluluğu için yeni isim
SessionLocal = async_session

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Veritabanı oturumu için dependency.
    FastAPI endpoint'lerinde kullanılır.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

@asynccontextmanager
async def get_db_context():
    """
    Veritabanı oturumu için async context manager.
    `async with` ile kullanılır.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close() 