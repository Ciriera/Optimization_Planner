"""
Final and Makeup Session API Endpoints
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models import User
from app.services.final_makeup_service import FinalMakeupService

router = APIRouter()

@router.post("/separate", response_model=dict)
async def separate_final_makeup_projects(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Projeleri final ve bütünleme olarak ayırır."""
    service = FinalMakeupService()
    result = await service.separate_final_makeup_projects(db)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.post("/create-makeup", response_model=dict)
async def create_makeup_session(
    *,
    session_name: str,
    remaining_projects: List[int],
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Bütünleme oturumu oluşturur."""
    service = FinalMakeupService()
    result = await service.create_makeup_session(db, session_name, remaining_projects)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.post("/create-final", response_model=dict)
async def create_final_session(
    *,
    session_name: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Final oturumu oluşturur."""
    service = FinalMakeupService()
    result = await service.create_final_session(db, session_name)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.get("/compare", response_model=dict)
async def compare_final_vs_makeup(
    *,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Final ve bütünleme oturumlarını karşılaştırır."""
    service = FinalMakeupService()
    result = await service.compare_final_vs_makeup(db)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result
