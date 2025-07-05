from typing import Dict, Any, Optional, List
from celery import shared_task
import json
import os
from datetime import datetime

from app.db.session import SessionLocal
from app.services.report import ReportService
from app.core.cache import redis_client
from app.core.config import settings


@shared_task(name="generate_assignment_report_pdf")
def generate_assignment_report_pdf(
    project_type: str = "ALL",
    is_makeup: bool = False,
    algorithm_result_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a PDF report for project assignments.
    
    Args:
        project_type: Type of projects to include in the report
        is_makeup: Whether to include makeup exams
        algorithm_result_id: Optional ID of a cached algorithm result to use
        task_id: Optional task ID for caching the report
        
    Returns:
        Report metadata including the file path
    """
    # Create database session
    db = SessionLocal()
    
    try:
        # Create report service
        report_service = ReportService(db)
        
        # Get algorithm result if provided
        algorithm_result = None
        if algorithm_result_id and redis_client:
            cached_result = redis_client.get(f"algorithm_result:{algorithm_result_id}")
            if cached_result:
                algorithm_result = json.loads(cached_result)
        
        # Generate the report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"assignment_report_{project_type}_{timestamp}.pdf"
        file_path = os.path.join(settings.REPORT_DIR, filename)
        
        # Ensure directory exists
        os.makedirs(settings.REPORT_DIR, exist_ok=True)
        
        # Generate the PDF report
        report_service.generate_assignment_pdf(
            file_path=file_path,
            project_type=project_type,
            is_makeup=is_makeup,
            algorithm_result=algorithm_result
        )
        
        # Prepare report metadata
        report_metadata = {
            "report_type": "assignment_pdf",
            "project_type": project_type,
            "is_makeup": is_makeup,
            "file_name": filename,
            "file_path": file_path,
            "file_url": f"/api/v1/reports/download/{filename}",
            "generated_at": datetime.now().isoformat()
        }
        
        # Cache the report metadata if task_id is provided
        if task_id and redis_client:
            redis_client.set(
                f"report:{task_id}",
                json.dumps(report_metadata),
                ex=86400  # 24 hours expiration
            )
        
        return report_metadata
    finally:
        db.close()


@shared_task(name="generate_assignment_report_excel")
def generate_assignment_report_excel(
    project_type: str = "ALL",
    is_makeup: bool = False,
    algorithm_result_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an Excel report for project assignments.
    
    Args:
        project_type: Type of projects to include in the report
        is_makeup: Whether to include makeup exams
        algorithm_result_id: Optional ID of a cached algorithm result to use
        task_id: Optional task ID for caching the report
        
    Returns:
        Report metadata including the file path
    """
    # Create database session
    db = SessionLocal()
    
    try:
        # Create report service
        report_service = ReportService(db)
        
        # Get algorithm result if provided
        algorithm_result = None
        if algorithm_result_id and redis_client:
            cached_result = redis_client.get(f"algorithm_result:{algorithm_result_id}")
            if cached_result:
                algorithm_result = json.loads(cached_result)
        
        # Generate the report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"assignment_report_{project_type}_{timestamp}.xlsx"
        file_path = os.path.join(settings.REPORT_DIR, filename)
        
        # Ensure directory exists
        os.makedirs(settings.REPORT_DIR, exist_ok=True)
        
        # Generate the Excel report
        report_service.generate_assignment_excel(
            file_path=file_path,
            project_type=project_type,
            is_makeup=is_makeup,
            algorithm_result=algorithm_result
        )
        
        # Prepare report metadata
        report_metadata = {
            "report_type": "assignment_excel",
            "project_type": project_type,
            "is_makeup": is_makeup,
            "file_name": filename,
            "file_path": file_path,
            "file_url": f"/api/v1/reports/download/{filename}",
            "generated_at": datetime.now().isoformat()
        }
        
        # Cache the report metadata if task_id is provided
        if task_id and redis_client:
            redis_client.set(
                f"report:{task_id}",
                json.dumps(report_metadata),
                ex=86400  # 24 hours expiration
            )
        
        return report_metadata
    finally:
        db.close()


@shared_task(name="generate_workload_report")
def generate_workload_report(
    project_type: str = "ALL",
    is_makeup: bool = False,
    algorithm_result_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a workload statistics report.
    
    Args:
        project_type: Type of projects to include in the report
        is_makeup: Whether to include makeup exams
        algorithm_result_id: Optional ID of a cached algorithm result to use
        task_id: Optional task ID for caching the report
        
    Returns:
        Workload statistics
    """
    # Create database session
    db = SessionLocal()
    
    try:
        # Create report service
        report_service = ReportService(db)
        
        # Get algorithm result if provided
        algorithm_result = None
        if algorithm_result_id and redis_client:
            cached_result = redis_client.get(f"algorithm_result:{algorithm_result_id}")
            if cached_result:
                algorithm_result = json.loads(cached_result)
        
        # Generate workload statistics
        workload_stats = report_service.generate_workload_statistics(
            project_type=project_type,
            is_makeup=is_makeup,
            algorithm_result=algorithm_result
        )
        
        # Cache the workload stats if task_id is provided
        if task_id and redis_client:
            redis_client.set(
                f"workload_stats:{task_id}",
                json.dumps(workload_stats),
                ex=86400  # 24 hours expiration
            )
        
        return workload_stats
    finally:
        db.close()


@shared_task(name="get_report")
def get_report(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get cached report metadata.
    
    Args:
        task_id: Task ID for retrieving cached report metadata
        
    Returns:
        The cached report metadata or None if not found
    """
    if redis_client:
        cached_report = redis_client.get(f"report:{task_id}")
        if cached_report:
            return json.loads(cached_report)
    return None


@shared_task(name="get_workload_stats")
def get_workload_stats(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get cached workload statistics.
    
    Args:
        task_id: Task ID for retrieving cached workload statistics
        
    Returns:
        The cached workload statistics or None if not found
    """
    if redis_client:
        cached_stats = redis_client.get(f"workload_stats:{task_id}")
        if cached_stats:
            return json.loads(cached_stats)
    return None 