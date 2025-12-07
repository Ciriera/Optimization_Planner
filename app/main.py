from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket
import os
import datetime
import logging
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
    
    # Filter out /api/v1/process requests from ALL uvicorn logs
    class ProcessEndpointFilter(logging.Filter):
        """Filter to suppress ALL logs for /api/v1/process endpoint"""
        def filter(self, record):
            # Filter out any log containing /api/v1/process in any attribute
            message_str = ""
            if hasattr(record, 'message'):
                message_str = str(record.message)
            if hasattr(record, 'msg'):
                message_str += str(record.msg)
            if hasattr(record, 'getMessage'):
                message_str += record.getMessage()
            
            # Check all string attributes
            for attr in ['message', 'msg', 'args', 'pathname', 'filename', 'funcName']:
                if hasattr(record, attr):
                    attr_value = str(getattr(record, attr))
                    if '/api/v1/process' in attr_value:
                        return False
            
            if '/api/v1/process' in message_str:
                return False
            
            return True
    
    # Apply filter to ALL uvicorn loggers
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.addFilter(ProcessEndpointFilter())
    
    # Also apply to root uvicorn logger
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.addFilter(ProcessEndpointFilter())
    
    print("Uvicorn log filter applied for /api/v1/process endpoint.")
    
    # Auto-create notification_logs table if it doesn't exist
    try:
        from sqlalchemy import text
        from app.core.database import async_engine
        
        async with async_engine.begin() as conn:
            print("Checking notification_logs table...")
            
            # Check if table exists and update columns if needed
            try:
                # Check if status column uses enum type
                result = await conn.execute(text("""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'notification_logs' AND column_name = 'status'
                """))
                column_info = result.fetchone()
                
                if column_info and column_info[0] == 'USER-DEFINED':
                    # Column exists and uses enum type, convert to VARCHAR
                    print("Converting status column from enum to VARCHAR...")
                    await conn.execute(text("""
                        ALTER TABLE notification_logs 
                        ALTER COLUMN status TYPE VARCHAR(20) 
                        USING status::text
                    """))
                    print("✓ Status column converted to VARCHAR")
                
                # Check if instructor_id is NOT NULL and make it nullable
                result = await conn.execute(text("""
                    SELECT is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'notification_logs' AND column_name = 'instructor_id'
                """))
                instructor_id_info = result.fetchone()
                
                if instructor_id_info and instructor_id_info[0] == 'NO':
                    # Column exists and is NOT NULL, make it nullable
                    print("Making instructor_id column nullable for custom emails...")
                    await conn.execute(text("""
                        ALTER TABLE notification_logs 
                        ALTER COLUMN instructor_id DROP NOT NULL
                    """))
                    print("✓ instructor_id column is now nullable")
            except Exception as e:
                # Table might not exist yet, or column might not exist
                pass
            
            # Create table (safe - won't fail if exists)
            # Note: Using VARCHAR instead of enum type to avoid case sensitivity issues
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS notification_logs (
                    id SERIAL PRIMARY KEY,
                    instructor_id INTEGER,  -- Nullable for custom emails
                    instructor_email VARCHAR(200) NOT NULL,
                    instructor_name VARCHAR(200),
                    planner_timestamp TIMESTAMP,
                    subject VARCHAR(500),
                    status VARCHAR(20) NOT NULL,
                    error_message TEXT,
                    sent_at TIMESTAMP,
                    attempt_count INTEGER DEFAULT 0,
                    meta_data JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    CONSTRAINT fk_notification_logs_instructor_id FOREIGN KEY (instructor_id) REFERENCES instructors(id)
                )
            """))
            
            # Create indexes (safe - won't fail if exists)
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_id ON notification_logs(id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_instructor_id ON notification_logs(instructor_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_instructor_email ON notification_logs(instructor_email)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_status ON notification_logs(status)"))
            
            # Add email column to instructors if it doesn't exist
            await conn.execute(text("ALTER TABLE instructors ADD COLUMN IF NOT EXISTS email VARCHAR(200)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_instructors_email ON instructors(email)"))
            
            print("✓ notification_logs table ready!")
    except Exception as e:
        print(f"⚠ Warning: Could not auto-create notification_logs table: {str(e)}")
        print("   You can manually run migration at /api/v1/notification/migrate")
    
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

# CORS settings (add first to handle preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Block all requests to non-existent /api/v1/process endpoint
from fastapi import Request
from fastapi.responses import JSONResponse

@app.api_route("/api/v1/process", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
async def block_process_endpoint(request: Request):
    """
    Block all requests to /api/v1/process endpoint - This endpoint does not exist.
    This handler should rarely be reached as ProcessEndpointBlockerMiddleware catches it first.
    Returns 204 No Content to minimize browser retries.
    """
    # Return 204 No Content (instead of 404) to tell browser: "Nothing here, stop asking"
    from starlette.responses import Response
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",  # Cache for 24 hours
            "Cache-Control": "public, max-age=86400",  # Browser cache
        },
        background=None  # Prevent any background tasks
    )

# Setup middleware (after CORS and endpoint definition)
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