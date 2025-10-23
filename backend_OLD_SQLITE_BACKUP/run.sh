#!/bin/bash

# Start Redis server
echo "Starting Redis server..."
redis-server --daemonize yes

# Start Celery worker
echo "Starting Celery worker..."
celery -A app.core.celery worker --loglevel=info &

# Start Celery beat
echo "Starting Celery beat..."
celery -A app.core.celery beat --loglevel=info &

# Start FastAPI application
echo "Starting FastAPI application..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 