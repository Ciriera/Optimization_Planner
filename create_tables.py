import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.base import Base
from app.core.config import settings

async def create_tables():
    # SQLite için async engine oluştur
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True
    )
    
    async with engine.begin() as conn:
        # Tüm tabloları oluştur
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(create_tables()) 