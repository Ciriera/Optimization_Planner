@echo off
echo Starting services...

REM Start Celery worker in a new window
start cmd /k "title Celery Worker && celery -A app.core.celery worker --loglevel=info"

REM Start Celery beat in a new window
start cmd /k "title Celery Beat && celery -A app.core.celery beat --loglevel=info"

REM Start FastAPI application
echo Starting FastAPI application...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 