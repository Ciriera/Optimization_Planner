from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket
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
from app.core.error_handling import (
    optimization_planner_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler
)
from app.monitoring.logger import structured_logger, metrics_collector


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize services on application startup and cleanup on shutdown.
    """
    # Initialize Redis connection
    redis_connected = await init_redis_pool()
    if redis_connected:
        print("Redis baglantisi basariyla kuruldu.")
        print(f"   Host: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    else:
        print("Redis baglantisi kurulamadi, bellek ici onbellek kullaniliyor.")
        print("   Not: Bu durum performansi etkileyebilir ve yalnizca gelistirme ortami icin onerilir.")

    # Initialize i18n (internationalization)
    init_i18n()
    print("Coklu dil destegi baslatildi.")
    
    # Initialize structured logging
    print("Structured logging initialized.")
    
    # Execute startup code
    yield
    
    # Execute shutdown code (resource cleanup)
    print("Uygulama kapatiliyor, kaynaklar temizleniyor...")


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

# Add exception handlers
from app.core.error_handling import (
    OptimizationPlannerException,
    ValidationException,
    BusinessLogicException,
    AlgorithmException,
    DatabaseException,
    AuthorizationException,
    ResourceNotFoundException,
    RateLimitException
)
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

app.add_exception_handler(OptimizationPlannerException, optimization_planner_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
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
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "services": {
            "api": True,
            "celery": celery_status,
            "redis": settings.REDIS_HOST is not None
        }
    }


@app.get("/metrics")
def get_metrics():
    """
    Get application metrics.
    """
    return {
        "success": True,
        "data": metrics_collector.get_metrics_summary(),
        "error": None
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

@app.get("/favicon.ico")
def favicon():
    """
    Favicon endpoint.
    """
    from fastapi.responses import FileResponse
    import os
    
    favicon_path = os.path.join(os.path.dirname(__file__), "..", "static", "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/x-icon")
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/logo192.png")
def logo():
    """
    Logo endpoint.
    """
    from fastapi.responses import FileResponse
    import os
    
    logo_path = os.path.join(os.path.dirname(__file__), "..", "static", "logo192.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/png")
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Logo not found")

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket endpoint for real-time algorithm progress tracking.
    """
    from app.api.v1.endpoints.websocket import manager
    from fastapi.websockets import WebSocketDisconnect
    import logging
    
    logger = logging.getLogger(__name__)
    
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            
            try:
                import json
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Client ping, respond with pong
                    await manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": message.get("timestamp")}),
                        user_id
                    )
                elif message_type == "get_progress":
                    # Client requests current progress
                    current_progress = manager.algorithm_progress.get(user_id, {})
                    await manager.send_algorithm_progress(user_id, current_progress)
                elif message_type == "subscribe_algorithm":
                    # Client subscribes to algorithm progress
                    algorithm_id = message.get("algorithm_id")
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscription_confirmed",
                            "algorithm_id": algorithm_id
                        }),
                        user_id
                    )
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from user {user_id}")
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Invalid JSON format"}),
                    user_id
                )
            except Exception as e:
                logger.error(f"Error processing message from user {user_id}: {e}")
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Internal server error"}),
                    user_id
                )
                
    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from WebSocket")
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)