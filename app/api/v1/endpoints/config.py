"""
Configuration management endpoints
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.api import deps
from app.core.config import settings
from app.db.base import get_db

router = APIRouter()


class ConfigResponse(BaseModel):
    """Configuration response model."""
    use_real_ortools: bool
    ortools_timeout: int
    min_class_count: int
    max_class_count: int
    min_instructors_bitirme: int
    min_instructors_ara: int


class ConfigUpdate(BaseModel):
    """Configuration update model."""
    use_real_ortools: bool = None
    ortools_timeout: int = None
    min_class_count: int = None
    max_class_count: int = None
    min_instructors_bitirme: int = None
    min_instructors_ara: int = None


@router.get("/", response_model=ConfigResponse)
async def get_configuration(
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Get current system configuration.
    """
    return ConfigResponse(
        use_real_ortools=settings.USE_REAL_ORTOOLS,
        ortools_timeout=settings.ORTOOLS_TIMEOUT,
        min_class_count=settings.MIN_CLASS_COUNT,
        max_class_count=settings.MAX_CLASS_COUNT,
        min_instructors_bitirme=settings.MIN_INSTRUCTORS_BITIRME,
        min_instructors_ara=settings.MIN_INSTRUCTORS_ARA,
    )


@router.put("/", response_model=ConfigResponse)
async def update_configuration(
    *,
    config_update: ConfigUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update system configuration.
    Note: Changes require application restart to take effect.
    """
    # Validate constraints with project specification compliance
    from app.services.dynamic_config_service import DynamicConfigService
    config_service = DynamicConfigService()
    
    # Proje açıklamasına göre sınıf sayısı kısıtlamaları
    if config_update.min_class_count is not None and config_update.min_class_count < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum class count must be at least 5 (as per project specification)"
        )
    
    if config_update.max_class_count is not None and config_update.max_class_count > 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum class count cannot exceed 7 (as per project specification)"
        )
    
    if (config_update.min_class_count is not None and 
        config_update.max_class_count is not None and 
        config_update.min_class_count > config_update.max_class_count):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum class count cannot be greater than maximum class count"
        )
    
    # Advanced validation using DynamicConfigService
    if (config_update.min_class_count is not None or 
        config_update.max_class_count is not None):
        min_count = config_update.min_class_count or settings.MIN_CLASS_COUNT
        max_count = config_update.max_class_count or settings.MAX_CLASS_COUNT
        
        validation_result = await config_service.validate_class_count_range(
            db, min_count, max_count
        )
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Class count validation failed: {'; '.join(validation_result['errors'])}"
            )
    
    if (config_update.min_instructors_bitirme is not None and 
        config_update.min_instructors_bitirme < 1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum instructors for bitirme projects must be at least 1"
        )
    
    if (config_update.min_instructors_ara is not None and 
        config_update.min_instructors_ara < 1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum instructors for ara projects must be at least 1"
        )
    
    if config_update.ortools_timeout is not None and config_update.ortools_timeout < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OR-Tools timeout must be at least 1 second"
        )
    
    # Update settings (runtime only - requires restart for persistence)
    if config_update.use_real_ortools is not None:
        settings.USE_REAL_ORTOOLS = config_update.use_real_ortools
    
    if config_update.ortools_timeout is not None:
        settings.ORTOOLS_TIMEOUT = config_update.ortools_timeout
    
    if config_update.min_class_count is not None:
        settings.MIN_CLASS_COUNT = config_update.min_class_count
    
    if config_update.max_class_count is not None:
        settings.MAX_CLASS_COUNT = config_update.max_class_count
    
    if config_update.min_instructors_bitirme is not None:
        settings.MIN_INSTRUCTORS_BITIRME = config_update.min_instructors_bitirme
    
    if config_update.min_instructors_ara is not None:
        settings.MIN_INSTRUCTORS_ARA = config_update.min_instructors_ara
    
    return ConfigResponse(
        use_real_ortools=settings.USE_REAL_ORTOOLS,
        ortools_timeout=settings.ORTOOLS_TIMEOUT,
        min_class_count=settings.MIN_CLASS_COUNT,
        max_class_count=settings.MAX_CLASS_COUNT,
        min_instructors_bitirme=settings.MIN_INSTRUCTORS_BITIRME,
        min_instructors_ara=settings.MIN_INSTRUCTORS_ARA,
    )


@router.get("/ortools-status", response_model=Dict[str, Any])
async def get_ortools_status(
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Check OR-Tools availability and status.
    """
    try:
        import ortools
        ortools_available = True
        ortools_version = ortools.__version__
    except ImportError:
        ortools_available = False
        ortools_version = None
    
    return {
        "ortools_available": ortools_available,
        "ortools_version": ortools_version,
        "use_real_ortools": settings.USE_REAL_ORTOOLS,
        "ortools_timeout": settings.ORTOOLS_TIMEOUT,
        "status": "available" if ortools_available else "not_installed",
        "message": "OR-Tools is available and configured" if ortools_available else "OR-Tools is not installed. Install with: pip install ortools"
    }


@router.get("/constraints", response_model=Dict[str, Any])
async def get_constraints_info(
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get information about current constraint settings.
    """
    from app.services.rules import RulesService
    
    rules_service = RulesService()
    constraints = rules_service.get_configurable_constraints()
    
    return {
        "constraints": constraints,
        "description": {
            "min_class_count": "Minimum number of classes to be scheduled",
            "max_class_count": "Maximum number of classes to be scheduled",
            "min_instructors_bitirme": "Minimum instructors required for bitirme projects",
            "min_instructors_ara": "Minimum instructors required for ara projects"
        },
        "current_values": {
            "min_class_count": settings.MIN_CLASS_COUNT,
            "max_class_count": settings.MAX_CLASS_COUNT,
            "min_instructors_bitirme": settings.MIN_INSTRUCTORS_BITIRME,
            "min_instructors_ara": settings.MIN_INSTRUCTORS_ARA
        }
    }


@router.get("/dynamic")
async def get_dynamic_config(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Mevcut dinamik sistem konfigürasyonunu getirir.
    """
    try:
        from app.services.dynamic_config_service import DynamicConfigService
        
        config_service = DynamicConfigService()
        config = await config_service.get_current_config(db)
        
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting dynamic config: {str(e)}"
        )


@router.put("/dynamic")
async def update_dynamic_config(
    config_updates: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Dinamik sistem konfigürasyonunu günceller.
    """
    try:
        from app.services.dynamic_config_service import DynamicConfigService
        
        config_service = DynamicConfigService()
        result = await config_service.update_config(db, config_updates, current_user.id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating dynamic config: {str(e)}"
        )


@router.post("/dynamic/reset")
async def reset_dynamic_config(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Dinamik konfigürasyonu default değerlere sıfırlar.
    """
    try:
        from app.services.dynamic_config_service import DynamicConfigService
        
        config_service = DynamicConfigService()
        result = await config_service.reset_to_defaults(db, current_user.id)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting dynamic config: {str(e)}"
        )


@router.post("/dynamic/validate-class-count")
async def validate_class_count_range(
    min_count: int,
    max_count: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Sınıf sayısı aralığını validate eder.
    """
    try:
        from app.services.dynamic_config_service import DynamicConfigService
        
        config_service = DynamicConfigService()
        result = await config_service.validate_class_count_range(db, min_count, max_count)
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating class count range: {str(e)}"
        )


@router.get("/dynamic/recommendations")
async def get_config_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Mevcut duruma göre konfigürasyon önerileri üretir.
    """
    try:
        from app.services.dynamic_config_service import DynamicConfigService
        
        config_service = DynamicConfigService()
        recommendations = await config_service.get_config_recommendations(db)
        
        return recommendations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting config recommendations: {str(e)}"
        )
