from fastapi import APIRouter

from app.api.v1.endpoints import auth, instructors, projects, classrooms, timeslots, schedules, algorithms, audit_logs, reports, debug

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(instructors.router, prefix="/instructors", tags=["instructors"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(classrooms.router, prefix="/classrooms", tags=["classrooms"])
api_router.include_router(timeslots.router, prefix="/timeslots", tags=["timeslots"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
api_router.include_router(algorithms.router, prefix="/algorithms", tags=["algorithms"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit_logs"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(debug.router, prefix="/debug", tags=["debug"]) 