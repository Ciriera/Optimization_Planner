from typing import List, Union, Optional
from pydantic import AnyHttpUrl, EmailStr, field_validator
from pydantic_settings import BaseSettings
import secrets
import os
from pathlib import Path

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    PROJECT_NAME: str = "Project Assignment System"
    
    # Debug mode
    DEBUG: bool = True
    
    # Auth settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 saat
    ALGORITHM: str = "HS256"
    
    # CORS ayarları
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # PostgreSQL ayarları
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ceng_project"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ceng_project"

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_url(cls, v: Optional[str], info) -> str:
        if v and v.startswith("postgresql"):
            return v
        postgres_server = info.data.get("POSTGRES_SERVER", "")
        postgres_user = info.data.get("POSTGRES_USER", "")
        postgres_password = info.data.get("POSTGRES_PASSWORD", "")
        postgres_db = info.data.get("POSTGRES_DB", "")
        return f"postgresql://{postgres_user}:{postgres_password}@{postgres_server}/{postgres_db}"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return self.DATABASE_URL
    
    # Redis ayarları
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6380
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # Celery ayarları
    CELERY_BROKER_URL: str = f"redis://localhost:6380/0"
    CELERY_RESULT_BACKEND: str = f"redis://localhost:6380/0"

    # Email ayarları
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_USER: str = "test@example.com"
    SMTP_PASSWORD: str = "password"
    EMAILS_FROM_EMAIL: str = "test@example.com"
    EMAILS_FROM_NAME: str = "Project Assignment System"

    # Admin kullanıcı
    FIRST_SUPERUSER: str = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "adminpassword"

    # Logging
    LOG_LEVEL: str = "INFO"
    
    # File storage
    REPORT_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "reports")
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "uploads")
    
    # Algorithm settings
    DEFAULT_ALGORITHM_ITERATIONS: int = 1000
    DEFAULT_TEMPERATURE: float = 1000.0
    DEFAULT_COOLING_RATE: float = 0.95

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "allow"
    }

# Global settings instance
settings = Settings() 