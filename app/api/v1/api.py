from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    instructors,
    projects,
    classrooms,
    timeslots,
    schedules,
    algorithms,
    audit_logs,
    reports,
    debug
)

# Sağlık kontrolü endpointini doğrudan ekle
from app.api.v1.endpoints.health import router as health_router

api_router = APIRouter()

# Health check endpoint
api_router.include_router(health_router, prefix="/health", tags=["health"])

# Auth endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Instructor endpoints
api_router.include_router(instructors.router, prefix="/instructors", tags=["instructors"])

# Project endpoints
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])

# Classroom endpoints
api_router.include_router(classrooms.router, prefix="/classrooms", tags=["classrooms"])

# Timeslot endpoints
api_router.include_router(timeslots.router, prefix="/timeslots", tags=["timeslots"])

# Schedule endpoints
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])

# Algorithm endpoints
api_router.include_router(algorithms.router, prefix="/algorithms", tags=["algorithms"])

# Audit log endpoints
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])

# Report endpoints
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

# Debug endpoints (only in development)
api_router.include_router(debug.router, prefix="/debug", tags=["debug"]) 