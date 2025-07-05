from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import datetime
from contextlib import asynccontextmanager

# Import all models to ensure they are loaded
from app.db.base_all import Base  # noqa

from app.api.v1.api import api_router
from app.core.config import settings
from app.api.middleware import setup_middleware
from app.core.celery import celery_app
from app.core.cache import init_redis_pool
from app.i18n import init_i18n


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize services on application startup and cleanup on shutdown.
    """
    # Initialize Redis connection
    redis_connected = await init_redis_pool()
    if redis_connected:
        print("✅ Redis bağlantısı başarıyla kuruldu.")
        print(f"   Host: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    else:
        print("⚠️ Redis bağlantısı kurulamadı, bellek içi önbellek kullanılıyor.")
        print("   Not: Bu durum performansı etkileyebilir ve yalnızca geliştirme ortamı için önerilir.")
    
    # Initialize i18n (internationalization)
    init_i18n()
    print("🌐 Çoklu dil desteği başlatıldı.")
    
    # Execute startup code
    yield
    
    # Execute shutdown code (resource cleanup)
    print("🔄 Uygulama kapatılıyor, kaynaklar temizleniyor...")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="University Project Assignment System API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    validate_responses=False,  # Disable response validation to avoid serialization issues
)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup middleware
setup_middleware(app)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Create reports directory
reports_dir = settings.REPORT_DIR
os.makedirs(reports_dir, exist_ok=True)


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
        "error": None,
        "message": "Welcome to Project Assignment API"
    }


@app.get("/test")
async def test_endpoint():
    """
    Test endpoint.
    """
    return {
        "success": True,
        "message": "Test endpoint is working!",
        "timestamp": str(datetime.datetime.now())
    }

@app.get("/test/db")
async def test_db():
    """
    Test database connection.
    """
    from sqlalchemy import text
    from app.db.base import async_session
    
    try:
        async with async_session() as db:
            # Basit bir SQL sorgusu çalıştır
            result = await db.execute(text("SELECT 1 AS test"))
            test_value = result.scalar_one()
            
            return {
                "success": True,
                "message": "Database connection is working!",
                "data": {
                    "test_value": test_value
                }
            }
    except Exception as e:
        return {
            "success": False,
            "message": "Database connection failed!",
            "error": str(e)
        }

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """
    Health check endpoint.
    """
    try:
        celery_status = celery_app.control.ping() is not None
    except:
        celery_status = False
        
    return {
        "status": "ok",
        "timestamp": datetime.datetime.now().isoformat(),
        "services": {
            "api": True,
            "celery": celery_status
        }
    }

@app.get("/test/i18n")
def test_i18n():
    """
    Test i18n (internationalization) functionality.
    """
    from app.i18n import translate
    
    return {
        "success": True,
        "data": {
            "tr": {
                "welcome": translate("common.welcome", locale="tr"),
                "login": translate("common.login", locale="tr"),
                "algorithms_title": translate("algorithms.title", locale="tr")
            },
            "en": {
                "welcome": translate("common.welcome", locale="en"),
                "login": translate("common.login", locale="en"),
                "algorithms_title": translate("algorithms.title", locale="en")
            }
        },
        "error": None
    }

@app.get("/test/algorithms")
def test_algorithms():
    """
    Test algorithms functionality.
    """
    from app.algorithms.factory import get_algorithm_types
    
    return {
        "success": True,
        "data": {
            "available_algorithms": get_algorithm_types()
        },
        "error": None
    }