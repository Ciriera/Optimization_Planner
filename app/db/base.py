from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base_class import Base  # noqa

# SQLAlchemy async engine
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        "sqlite+aiosqlite:///./test.db",
        echo=True,
        future=True,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        future=True
    )

# Async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Veritabanı bağlantısı için dependency
async def get_db():
    async with async_session() as db:
        try:
            yield db
        finally:
            await db.close()

# Import all models here
from app.models.audit_log import AuditLog  # noqa
from app.models.instructor import Instructor  # noqa
from app.models.project import Project  # noqa
from app.models.classroom import Classroom  # noqa
from app.models.timeslot import TimeSlot  # noqa
from app.models.schedule import Schedule  # noqa
from app.models.algorithm import AlgorithmRun  # noqa
from app.models.user import User  # noqa 