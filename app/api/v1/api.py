from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    instructors,
    projects,
    classrooms,
    timeslots,
    schedules,
    algorithms,
    audit_logs,
    reports,
    config,
    debug,
    recommendations,
    jury,
    oral_exams,
    accessibility,
    calendar,
    websocket,
    final_makeup,
    user_recommendations,
    conflict_resolution,
    lexicographic
)
from app.api.v1.endpoints import project_jury

# Sağlık kontrolü endpointini doğrudan ekle
from app.api.v1.endpoints.health import router as health_router

api_router = APIRouter()

# Health check endpoint
api_router.include_router(health_router, prefix="/health", tags=["health"])

# Auth endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# User endpoints
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Instructor endpoints
api_router.include_router(instructors.router, prefix="/instructors", tags=["instructors"])

# Project endpoints
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])

# Project jury endpoints
api_router.include_router(project_jury.router, prefix="/projects", tags=["project-jury"])

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

# Config endpoints
api_router.include_router(config.router, prefix="/config", tags=["config"])

# Debug endpoints (only in development)
api_router.include_router(debug.router, prefix="/debug", tags=["debug"])

# Recommendation endpoints
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])

# Jury matching endpoints
api_router.include_router(jury.router, prefix="/jury", tags=["jury"])

# Oral exam endpoints
api_router.include_router(oral_exams.router, prefix="/oral-exams", tags=["oral-exams"])

# Accessibility endpoints
api_router.include_router(accessibility.router, prefix="/accessibility", tags=["accessibility"])

# Calendar endpoints
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])

# WebSocket endpoints for real-time progress tracking
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Final/Makeup session endpoints
api_router.include_router(final_makeup.router, prefix="/final-makeup", tags=["final-makeup"])

# User recommendation endpoints
api_router.include_router(user_recommendations.router, prefix="/user-recommendations", tags=["user-recommendations"])

# Conflict resolution endpoints
api_router.include_router(conflict_resolution.router, prefix="/conflict-resolution", tags=["conflict-resolution"])

# Lexicographic algorithm endpoints
api_router.include_router(lexicographic.router, prefix="/lexicographic", tags=["lexicographic"]) 