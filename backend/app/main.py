from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

from app.api.v1.api import api_router
from app.core.config import settings
from app.api.deps import get_db
from app.core.celery import celery_app
from app.core.cache import init_redis_pool

# Logging
logging.basicConfig(level=logging.DEBUG if settings.DEBUG else settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="University Project Assignment System API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Create reports directory
reports_dir = settings.REPORT_DIR
os.makedirs(reports_dir, exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """
    Initialize services on application startup.
    """
    # Redis bağlantı havuzunu başlat
    try:
        await init_redis_pool()
        logger.info("Redis bağlantı havuzu başarıyla başlatıldı.")
    except Exception as e:
        logger.warning(f"Redis bağlantı havuzu başlatılamadı, bazı özellikler sınırlı çalışabilir: {e}")


@app.get("/")
def root():
    """
    Root endpoint.
    """
    return {
        "success": True,
        "data": {
            "name": settings.PROJECT_NAME,
            "version": "1.0.0",
            "description": "University Project Assignment System API",
            "docs_url": "/docs",
            "redoc_url": "/redoc"
        },
        "error": None
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """
    # Servislerin durumunu kontrol et
    try:
        celery_status = celery_app.control.ping() is not None
    except Exception:
        celery_status = False
        
    # Database kontrolü
    db_status = "ok"
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.sql import text
        
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            if not result.scalar() == 1:
                db_status = "error"
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "database": db_status,
            "celery": celery_status
        },
        "error": None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 