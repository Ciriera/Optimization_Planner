"""
Import endpoints for Excel file import functionality.
"""

import logging
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import io

from app.db.base import get_db
from app.api import deps
from app.models.user import User
from app.services.import_service import ImportService

logger = logging.getLogger(__name__)

router = APIRouter()
import_service = ImportService()


@router.post("/validate")
async def validate_excel_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Validate Excel file and return parsed data with validation results.
    """
    try:
        # Check file extension
        if not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Only .xlsx and .xls files are supported.",
            )
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty.",
            )
        
        # Parse Excel file
        parsed_data = import_service.parse_excel_file(file_content)
        
        if not parsed_data.get("success"):
            return {
                "success": False,
                "error": parsed_data.get("error"),
                "rows": [],
                "total_rows": 0,
                "valid_rows": 0,
                "invalid_rows": 0,
            }
        
        # Validate against database
        validated_data = await import_service.validate_import_data(parsed_data, db)
        
        return {
            "success": True,
            "rows": validated_data.get("rows", []),
            "total_rows": validated_data.get("total_rows", 0),
            "valid_rows": validated_data.get("valid_rows", 0),
            "invalid_rows": validated_data.get("invalid_rows", 0),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating Excel file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating file: {str(e)}",
        )


@router.post("/execute")
async def execute_import(
    file: UploadFile = File(...),
    dry_run: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Execute import: parse Excel file and save to database.
    """
    try:
        # Check file extension
        if not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Only .xlsx and .xls files are supported.",
            )
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty.",
            )
        
        # Parse Excel file
        parsed_data = import_service.parse_excel_file(file_content)
        
        if not parsed_data.get("success"):
            return {
                "success": False,
                "error": parsed_data.get("error"),
                "statistics": {},
            }
        
        # Validate against database
        validated_data = await import_service.validate_import_data(parsed_data, db)
        
        # Execute import
        import_result = await import_service.execute_import(
            validated_data, db, dry_run=dry_run
        )
        
        return {
            "success": import_result.get("success", False),
            "error": import_result.get("error"),
            "statistics": import_result.get("statistics", {}),
            "errors": import_result.get("errors"),
            "dry_run": dry_run,
            "timestamp": datetime.now().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing import: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing import: {str(e)}",
        )


@router.get("/template")
async def download_template(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Download Excel template file for import.
    """
    try:
        template_bytes = import_service.generate_template()
        
        return StreamingResponse(
            io.BytesIO(template_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=import_template.xlsx",
            },
        )
    except Exception as e:
        logger.error(f"Error generating template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating template: {str(e)}",
        )


@router.get("/logs")
async def get_import_logs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get import history/logs.
    Note: This is a placeholder. In a full implementation, you would have an ImportLog model.
    """
    # TODO: Implement import logs table and model
    return {
        "success": True,
        "logs": [],
        "total": 0,
        "limit": limit,
        "offset": skip,
    }

