import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, HttpUrl, PostgresDsn, field_validator, ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = ConfigDict(
        extra='ignore',
        case_sensitive=True,
        env_file=".env"
    )
    
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
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",  # React frontend
        "http://localhost:5173",  # Vite dev server
    ]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # PostgreSQL Configuration
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "optimization_planner")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    # Redis ayarları
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
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
    
    # Optimization settings
    USE_REAL_ORTOOLS: bool = os.getenv("USE_REAL_ORTOOLS", "false").lower() == "true"
    ORTOOLS_TIMEOUT: int = int(os.getenv("ORTOOLS_TIMEOUT", "30"))
    
    # Constraint settings
    MIN_CLASS_COUNT: int = int(os.getenv("MIN_CLASS_COUNT", "5"))
    MAX_CLASS_COUNT: int = int(os.getenv("MAX_CLASS_COUNT", "7"))
    MIN_INSTRUCTORS_BITIRME: int = int(os.getenv("MIN_INSTRUCTORS_BITIRME", "2"))
    MIN_INSTRUCTORS_ARA: int = int(os.getenv("MIN_INSTRUCTORS_ARA", "1"))
    
    # Parallel processing settings
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))

settings = Settings() 