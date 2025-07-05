from typing import Any, List
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import project
from app.models.project import ProjectType, ProjectStatus
from app.schemas.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectAssignment
)

router = APIRouter()

@router.get("/", response_model=List[Project])
def read_projects(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve projects.
    """
    projects = project.get_multi(db, skip=skip, limit=limit)
    return projects

@router.post("/", response_model=Project)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: ProjectCreate,
    current_user: dict = Depends(deps.get_current_instructor)
) -> Any:
    """
    Create new project.
    """
    project_obj = project.create_with_advisor(
        db=db, obj_in=project_in, advisor_id=current_user.id
    )
    return project_obj

@router.get("/type/{project_type}", response_model=List[Project])
def read_projects_by_type(
    project_type: ProjectType,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve projects by type.
    """
    projects = project.get_multi_by_type(
        db=db, project_type=project_type, skip=skip, limit=limit
    )
    return projects

@router.get("/status/{status}", response_model=List[Project])
def read_projects_by_status(
    status: ProjectStatus,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve projects by status.
    """
    projects = project.get_multi_by_status(
        db=db, status=status, skip=skip, limit=limit
    )
    return projects

@router.get("/advisor/{advisor_id}", response_model=List[Project])
def read_projects_by_advisor(
    advisor_id: int,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve projects by advisor.
    """
    projects = project.get_multi_by_advisor(
        db=db, advisor_id=advisor_id, skip=skip, limit=limit
    )
    return projects

@router.get("/available", response_model=List[Project])
def read_available_projects(
    db: Session = Depends(deps.get_db),
    project_type: ProjectType = None,
    current_user: dict = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve available projects.
    """
    projects = project.get_available_projects(
        db=db, project_type=project_type
    )
    return projects

@router.get("/{project_id}", response_model=Project)
def read_project(
    project_id: int,
    current_user: dict = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get project by ID.
    """
    project_obj = project.get(db=db, id=project_id)
    if not project_obj:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    return project_obj

@router.put("/{project_id}", response_model=Project)
def update_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    project_in: ProjectUpdate,
    current_user: dict = Depends(deps.get_current_instructor)
) -> Any:
    """
    Update a project.
    """
    project_obj = project.get(db=db, id=project_id)
    if not project_obj:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    if project_obj.advisor_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    project_obj = project.update(
        db=db, db_obj=project_obj, obj_in=project_in
    )
    return project_obj

@router.delete("/{project_id}", response_model=Project)
def delete_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: dict = Depends(deps.get_current_instructor)
) -> Any:
    """
    Delete a project.
    """
    project_obj = project.get(db=db, id=project_id)
    if not project_obj:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    if project_obj.advisor_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    project_obj = project.remove(db=db, id=project_id)
    return project_obj

@router.post("/{project_id}/assign", response_model=Project)
def assign_students_to_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    assignment: ProjectAssignment,
    current_user: dict = Depends(deps.get_current_instructor)
) -> Any:
    """
    Assign students to a project.
    """
    project_obj = project.get(db=db, id=project_id)
    if not project_obj:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    if project_obj.advisor_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    if project_obj.status != ProjectStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="Project is not available for assignment"
        )
    if len(assignment.student_ids) > project_obj.student_capacity:
        raise HTTPException(
            status_code=400,
            detail=f"Project capacity is {project_obj.student_capacity}"
        )
    project_obj = project.assign_students(
        db=db,
        project_id=project_id,
        student_ids=assignment.student_ids
    )
    return project_obj 