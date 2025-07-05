from typing import Dict, Any, List
import time
from celery import Task
from app.core.celery import celery_app
from app.core.cache import set_cache, get_cache
from app.algorithms.factory import AlgorithmFactory
from app.crud.project import project as project_crud
from app.crud.instructor import instructor as instructor_crud
from app.crud.student import student as student_crud
from app.db.session import SessionLocal

class OptimizationTask(Task):
    """Custom task class for optimization tasks"""
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        # Store error in cache
        error_info = {
            "status": "failed",
            "error": str(exc),
            "traceback": str(einfo)
        }
        set_cache(f"optimization_result:{task_id}", error_info)
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        # Store result in cache
        result_info = {
            "status": "completed",
            "result": retval
        }
        set_cache(f"optimization_result:{task_id}", result_info)
        super().on_success(retval, task_id, args, kwargs)

@celery_app.task(base=OptimizationTask, bind=True)
def optimize_assignments(
    self,
    algorithm_type: str,
    algorithm_params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Run project assignment optimization
    
    Args:
        algorithm_type: Type of optimization algorithm to use
        algorithm_params: Algorithm-specific parameters
        
    Returns:
        Optimization results including assignments and metrics
    """
    db = SessionLocal()
    try:
        # Get available resources
        projects = project_crud.get_available_projects(db)
        instructors = instructor_crud.get_available_advisors(db, project_type="graduation")
        students = student_crud.get_available_students(db)
        
        # Create and run optimization algorithm
        algorithm = AlgorithmFactory.get_algorithm(
            algorithm_type=algorithm_type,
            projects=projects,
            instructors=instructors,
            students=students,
            **(algorithm_params or {})
        )
        
        # Store initial status
        set_cache(
            f"optimization_progress:{self.request.id}",
            {"status": "running", "progress": 0}
        )
        
        # Run optimization
        start_time = time.time()
        solution = algorithm.optimize()
        execution_time = time.time() - start_time
        
        # Prepare result
        result = {
            "solution": solution,
            "fitness_score": algorithm.get_fitness_score(),
            "execution_time": execution_time,
            "iterations": getattr(algorithm, "generations", 0)
        }
        
        # Apply assignments to database
        for project_id, assignment in solution["project_assignments"].items():
            project_crud.assign_students(
                db,
                project_id=int(project_id),
                student_ids=assignment["students"]
            )
        
        return result
        
    finally:
        db.close()

@celery_app.task
def send_email_notifications(
    assignments: Dict[str, Any],
    recipient_emails: List[str]
) -> None:
    """
    Send email notifications about project assignments
    
    Args:
        assignments: Project assignment results
        recipient_emails: List of email addresses to notify
    """
    # TODO: Implement email notification logic
    pass 