"""
Dynamic Configuration Service
Handles runtime configuration changes and validation
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.config import DynamicConfig
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class DynamicConfigService:
    """Service for managing dynamic system configuration."""
    
    def __init__(self):
        self.default_config = {
            "min_class_count": settings.MIN_CLASS_COUNT,
            "max_class_count": settings.MAX_CLASS_COUNT,
            "min_instructors_bitirme": settings.MIN_INSTRUCTORS_BITIRME,
            "min_instructors_ara": settings.MIN_INSTRUCTORS_ARA,
            "use_real_ortools": settings.USE_REAL_ORTOOLS,
            "ortools_timeout": settings.ORTOOLS_TIMEOUT
        }
    
    async def get_current_config(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Mevcut dinamik konfigürasyonu getirir.
        """
        try:
            # Try to get from database first
            result = await db.execute(
                select(DynamicConfig).order_by(DynamicConfig.updated_at.desc())
            )
            config = result.scalar_one_or_none()
            
            if config:
                return {
                    "config": config.config_data,
                    "updated_at": config.updated_at.isoformat(),
                    "updated_by": config.updated_by
                }
            else:
                # Return default config if no database config exists
                return {
                    "config": self.default_config,
                    "updated_at": None,
                    "updated_by": None
                }
        except Exception as e:
            logger.error(f"Error getting current config: {e}")
            return {
                "config": self.default_config,
                "updated_at": None,
                "updated_by": None
            }
    
    async def update_config(self, db: AsyncSession, config_updates: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        Dinamik konfigürasyonu günceller.
        """
        try:
            # Validate updates
            validation_result = await self._validate_config_updates(config_updates)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "message": f"Validation failed: {validation_result['errors']}"
                }
            
            # Get current config or create new one
            result = await db.execute(
                select(DynamicConfig).order_by(DynamicConfig.updated_at.desc())
            )
            config = result.scalar_one_or_none()
            
            if config:
                # Update existing config
                current_config = config.config_data
                current_config.update(config_updates)
                config.config_data = current_config
                config.updated_by = user_id
            else:
                # Create new config
                new_config = self.default_config.copy()
                new_config.update(config_updates)
                config = DynamicConfig(
                    config_data=new_config,
                    updated_by=user_id
                )
                db.add(config)
            
            await db.commit()
            await db.refresh(config)
            
            return {
                "success": True,
                "message": "Configuration updated successfully",
                "config": config.config_data,
                "updated_at": config.updated_at.isoformat()
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating config: {e}")
            return {
                "success": False,
                "message": f"Error updating configuration: {str(e)}"
            }
    
    async def reset_to_defaults(self, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """
        Konfigürasyonu default değerlere sıfırlar.
        """
        try:
            # Get current config or create new one
            result = await db.execute(
                select(DynamicConfig).order_by(DynamicConfig.updated_at.desc())
            )
            config = result.scalar_one_or_none()
            
            if config:
                # Update existing config to defaults
                config.config_data = self.default_config.copy()
                config.updated_by = user_id
            else:
                # Create new config with defaults
                config = DynamicConfig(
                    config_data=self.default_config.copy(),
                    updated_by=user_id
                )
                db.add(config)
            
            await db.commit()
            await db.refresh(config)
            
            return {
                "success": True,
                "message": "Configuration reset to defaults successfully",
                "config": config.config_data,
                "updated_at": config.updated_at.isoformat()
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error resetting config: {e}")
            return {
                "success": False,
                "message": f"Error resetting configuration: {str(e)}"
            }
    
    async def validate_class_count_range(self, db: AsyncSession, min_count: int, max_count: int) -> Dict[str, Any]:
        """
        Sınıf sayısı aralığını validate eder.
        Proje açıklamasına göre: Min sınıf sayısı: 5, Max sınıf sayısı: 7
        """
        errors = []
        warnings = []
        
        # Proje açıklamasına göre temel kısıtlamalar
        if min_count < 5:
            errors.append("Minimum class count must be at least 5 (as per project specification)")
        
        if max_count > 7:
            errors.append("Maximum class count cannot exceed 7 (as per project specification)")
        
        if min_count > max_count:
            errors.append("Minimum class count cannot be greater than maximum class count")
        
        # Proje açıklamasına göre ideal aralık kontrolü
        if min_count < 5:
            warnings.append("Minimum class count below recommended 5 (project specification)")
        
        if max_count > 7:
            warnings.append("Maximum class count above recommended 7 (project specification)")
        
        # Pratik kısıtlamalar
        if min_count > 10:
            errors.append("Minimum class count should not exceed 10 for practical purposes")
        
        if max_count < 3:
            errors.append("Maximum class count should be at least 3 for meaningful optimization")
        
        # Mevcut sistem durumunu kontrol et
        try:
            from app.services.project import ProjectService
            project_service = ProjectService()
            projects = await project_service.get_multi(db)
            project_count = len(projects)
            
            # Proje sayısına göre öneriler
            if project_count > 0:
                if project_count <= 10 and min_count > 5:
                    warnings.append(f"With {project_count} projects, minimum class count of {min_count} might be excessive")
                elif project_count > 20 and max_count < 7:
                    warnings.append(f"With {project_count} projects, maximum class count of {max_count} might be insufficient")
        except Exception as e:
            logger.warning(f"Could not check project count for validation: {e}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "message": "Class count range is valid" if len(errors) == 0 else "Class count range has validation errors",
            "project_specification_compliant": min_count >= 5 and max_count <= 7
        }
    
    async def get_config_recommendations(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Mevcut duruma göre konfigürasyon önerileri üretir.
        """
        try:
            # Get current system state
            from app.services.instructor import InstructorService
            from app.services.project import ProjectService
            
            instructor_service = InstructorService()
            project_service = ProjectService()
            
            # Get counts
            instructors = await instructor_service.get_multi(db)
            projects = await project_service.get_multi(db)
            
            instructor_count = len(instructors)
            project_count = len(projects)
            
            recommendations = []
            
            # Class count recommendations
            if project_count > 0:
                if project_count <= 10:
                    recommendations.append({
                        "setting": "min_class_count",
                        "current": settings.MIN_CLASS_COUNT,
                        "recommended": 3,
                        "reason": "Small project count, lower minimum class count is sufficient"
                    })
                    recommendations.append({
                        "setting": "max_class_count",
                        "current": settings.MAX_CLASS_COUNT,
                        "recommended": 5,
                        "reason": "Small project count, lower maximum class count is appropriate"
                    })
                elif project_count <= 20:
                    recommendations.append({
                        "setting": "min_class_count",
                        "current": settings.MIN_CLASS_COUNT,
                        "recommended": 5,
                        "reason": "Medium project count, moderate minimum class count is appropriate"
                    })
                    recommendations.append({
                        "setting": "max_class_count",
                        "current": settings.MAX_CLASS_COUNT,
                        "recommended": 7,
                        "reason": "Medium project count, moderate maximum class count is appropriate"
                    })
                else:
                    recommendations.append({
                        "setting": "min_class_count",
                        "current": settings.MIN_CLASS_COUNT,
                        "recommended": 7,
                        "reason": "Large project count, higher minimum class count is needed"
                    })
                    recommendations.append({
                        "setting": "max_class_count",
                        "current": settings.MAX_CLASS_COUNT,
                        "recommended": 10,
                        "reason": "Large project count, higher maximum class count is needed"
                    })
            
            # Instructor requirements recommendations
            if instructor_count > 0:
                if instructor_count >= 10:
                    recommendations.append({
                        "setting": "min_instructors_bitirme",
                        "current": settings.MIN_INSTRUCTORS_BITIRME,
                        "recommended": 2,
                        "reason": "Sufficient instructors available for bitirme projects"
                    })
                    recommendations.append({
                        "setting": "min_instructors_ara",
                        "current": settings.MIN_INSTRUCTORS_ARA,
                        "recommended": 1,
                        "reason": "Sufficient instructors available for ara projects"
                    })
                else:
                    recommendations.append({
                        "setting": "min_instructors_bitirme",
                        "current": settings.MIN_INSTRUCTORS_BITIRME,
                        "recommended": 1,
                        "reason": "Limited instructors, reduce minimum requirement for bitirme projects"
                    })
                    recommendations.append({
                        "setting": "min_instructors_ara",
                        "current": settings.MIN_INSTRUCTORS_ARA,
                        "recommended": 1,
                        "reason": "Limited instructors, maintain minimum requirement for ara projects"
                    })
            
            return {
                "recommendations": recommendations,
                "system_state": {
                    "instructor_count": instructor_count,
                    "project_count": project_count
                },
                "message": f"Generated {len(recommendations)} configuration recommendations"
            }
            
        except Exception as e:
            logger.error(f"Error getting config recommendations: {e}")
            return {
                "recommendations": [],
                "system_state": {},
                "message": f"Error generating recommendations: {str(e)}"
            }
    
    async def _validate_config_updates(self, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Konfigürasyon güncellemelerini validate eder.
        """
        errors = []
        
        # Validate min_class_count
        if "min_class_count" in config_updates:
            min_count = config_updates["min_class_count"]
            if not isinstance(min_count, int) or min_count < 1:
                errors.append("Minimum class count must be a positive integer")
        
        # Validate max_class_count
        if "max_class_count" in config_updates:
            max_count = config_updates["max_class_count"]
            if not isinstance(max_count, int) or max_count < 1:
                errors.append("Maximum class count must be a positive integer")
        
        # Validate class count range
        if "min_class_count" in config_updates and "max_class_count" in config_updates:
            min_count = config_updates["min_class_count"]
            max_count = config_updates["max_class_count"]
            if min_count > max_count:
                errors.append("Minimum class count cannot be greater than maximum class count")
        
        # Validate instructor requirements
        if "min_instructors_bitirme" in config_updates:
            min_bitirme = config_updates["min_instructors_bitirme"]
            if not isinstance(min_bitirme, int) or min_bitirme < 1:
                errors.append("Minimum instructors for bitirme projects must be a positive integer")
        
        if "min_instructors_ara" in config_updates:
            min_ara = config_updates["min_instructors_ara"]
            if not isinstance(min_ara, int) or min_ara < 1:
                errors.append("Minimum instructors for ara projects must be a positive integer")
        
        # Validate OR-Tools settings
        if "use_real_ortools" in config_updates:
            use_ortools = config_updates["use_real_ortools"]
            if not isinstance(use_ortools, bool):
                errors.append("use_real_ortools must be a boolean value")
        
        if "ortools_timeout" in config_updates:
            timeout = config_updates["ortools_timeout"]
            if not isinstance(timeout, int) or timeout < 1:
                errors.append("OR-Tools timeout must be a positive integer")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }