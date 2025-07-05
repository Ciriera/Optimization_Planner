import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, HttpUrl, PostgresDsn, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Proje Atama Sistemi"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    SERVER_NAME: str = os.getenv("SERVER_NAME", "localhost")
    SERVER_HOST: AnyHttpUrl = os.getenv("SERVER_HOST", "http://localhost:8000")
    
    # JWT algoritması
    ALGORITHM: str = "HS256"
    
    # Debug modu
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    
    # CORS ayarları
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",  # React frontend
        "http://localhost:5173",  # Vite dev server
    ]
    
    # Veritabanı ayarları
    TESTING: bool = os.getenv("TESTING", "False") == "True"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./app.db" if not TESTING else "sqlite+aiosqlite:///./test.db"
    )
    
    # Redis ayarları
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6380/0")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6380"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # Email ayarları
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48  # Şifre sıfırlama tokeni geçerlilik süresi (saat)
    
    # Celery ayarları
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    
    # Report ayarları
    REPORT_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "reports")
    
    # i18n ayarları
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "tr")
    SUPPORTED_LANGUAGES: List[str] = ["tr", "en"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 