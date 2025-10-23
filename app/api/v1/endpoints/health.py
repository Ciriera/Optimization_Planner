"""
Sağlık kontrolü endpointleri.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.core.cache import redis_pool

router = APIRouter()

@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Sistemin sağlık durumunu kontrol eder.
    """
    # Veritabanı bağlantısını kontrol et
    try:
        result = await db.execute(text("SELECT 1"))
        db_status = result.scalar() == 1
    except Exception:
        db_status = False
    
    # Redis bağlantısını kontrol et
    redis_status = False
    if redis_pool:
        try:
            redis_status = await redis_pool.ping()
        except Exception:
            redis_status = False
    
    return {
        "status": "healthy" if db_status and redis_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "redis": "connected" if redis_status else "disconnected",
        "version": "1.0.0"
    } 