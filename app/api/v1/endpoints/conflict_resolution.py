"""
🔧 CONFLICT RESOLUTION API ENDPOINTS
Görsellerde tespit edilen çakışmaları çözmek için API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any, Optional
import logging

from app.db.session import get_db
from app.services.conflict_resolution_service import ConflictResolutionService
from app.services.algorithm import AlgorithmService
from app.schemas.conflict_resolution import ConflictResolutionRequest, ConflictResolutionResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/detect-conflicts", response_model=Dict[str, Any])
async def detect_conflicts(
    db: AsyncSession = Depends(get_db)
):
    """
    Mevcut çizelgedeki tüm çakışmaları tespit eder
    
    Tespit edilen çakışmalar:
    - Dr. Öğretim Üyesi 3: 14:30-15:00'da 2 farklı görev
    - Dr. Öğretim Üyesi 21: 15:00-15:30'da 2 jüri görevi
    - Dr. Öğretim Üyesi 11: 16:00-16:30'da 2 farklı görev
    """
    try:
        logger.info("🔍 CONFLICT DETECTION API CALLED")
        
        # Mevcut çizelgeyi al
        algorithm_service = AlgorithmService()
        data = await algorithm_service._get_real_data(db)
        
        # Mevcut atamaları al
        from app.services.schedule import ScheduleService
        schedule_service = ScheduleService()
        schedules = await schedule_service.get_filtered(db, limit=1000)
        
        # Schedule formatını assignment formatına çevir
        assignments = []
        for schedule in schedules:
            if schedule.get('project_id'):
                assignment = {
                    'project_id': schedule.get('project_id'),
                    'timeslot_id': schedule.get('timeslot_id'),
                    'classroom_id': schedule.get('classroom_id'),
                    'responsible_instructor_id': schedule.get('responsible_instructor_id'),
                    'instructors': schedule.get('instructors', []),
                    'is_makeup': schedule.get('is_makeup', False)
                }
                assignments.append(assignment)
        
        # Çakışmaları tespit et
        conflict_service = ConflictResolutionService()
        conflicts = conflict_service.detect_all_conflicts(
            assignments=assignments,
            projects=data.get('projects', []),
            instructors=data.get('instructors', []),
            classrooms=data.get('classrooms', []),
            timeslots=data.get('timeslots', [])
        )
        
        # Rapor oluştur
        report = conflict_service.generate_conflict_report(conflicts)
        
        logger.info(f"🔍 CONFLICT DETECTION COMPLETED: {len(conflicts)} conflicts found")
        
        return {
            "success": True,
            "conflicts_detected": len(conflicts),
            "conflict_report": report,
            "message": f"{len(conflicts)} çakışma tespit edildi"
        }
        
    except Exception as e:
        logger.error(f"Error in conflict detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Çakışma tespit edilirken hata oluştu: {str(e)}"
        )

@router.post("/resolve-conflicts", response_model=Dict[str, Any])
async def resolve_conflicts(
    request: ConflictResolutionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Tespit edilen çakışmaları otomatik olarak çözer
    """
    try:
        logger.info("🔧 CONFLICT RESOLUTION API CALLED")
        
        # Mevcut çizelgeyi al
        algorithm_service = AlgorithmService()
        data = await algorithm_service._get_real_data(db)
        
        # Mevcut atamaları al
        from app.services.schedule import ScheduleService
        schedule_service = ScheduleService()
        schedules = await schedule_service.get_filtered(db, limit=1000)
        
        # Schedule formatını assignment formatına çevir
        assignments = []
        for schedule in schedules:
            if schedule.get('project_id'):
                assignment = {
                    'project_id': schedule.get('project_id'),
                    'timeslot_id': schedule.get('timeslot_id'),
                    'classroom_id': schedule.get('classroom_id'),
                    'responsible_instructor_id': schedule.get('responsible_instructor_id'),
                    'instructors': schedule.get('instructors', []),
                    'is_makeup': schedule.get('is_makeup', False)
                }
                assignments.append(assignment)
        
        # Çakışmaları tespit et
        conflict_service = ConflictResolutionService()
        conflicts = conflict_service.detect_all_conflicts(
            assignments=assignments,
            projects=data.get('projects', []),
            instructors=data.get('instructors', []),
            classrooms=data.get('classrooms', []),
            timeslots=data.get('timeslots', [])
        )
        
        if not conflicts:
            return {
                "success": True,
                "message": "Hiç çakışma bulunamadı",
                "conflicts_resolved": 0,
                "resolution_log": []
            }
        
        # Çakışmaları çöz
        resolved_assignments, resolution_log = conflict_service.resolve_conflicts(
            assignments=assignments,
            conflicts=conflicts,
            projects=data.get('projects', []),
            instructors=data.get('instructors', []),
            classrooms=data.get('classrooms', []),
            timeslots=data.get('timeslots', [])
        )
        
        # Çözüm sonrası kalan çakışmaları kontrol et
        remaining_conflicts = conflict_service.detect_all_conflicts(
            assignments=resolved_assignments,
            projects=data.get('projects', []),
            instructors=data.get('instructors', []),
            classrooms=data.get('classrooms', []),
            timeslots=data.get('timeslots', [])
        )
        
        # Başarılı çözüm sayısını hesapla
        successful_resolutions = len([r for r in resolution_log if r.get('success', False)])
        
        logger.info(f"🔧 CONFLICT RESOLUTION COMPLETED: {successful_resolutions}/{len(conflicts)} resolved")
        
        return {
            "success": True,
            "conflicts_detected": len(conflicts),
            "conflicts_resolved": successful_resolutions,
            "remaining_conflicts": len(remaining_conflicts),
            "resolution_log": resolution_log,
            "resolved_assignments": resolved_assignments,
            "message": f"{successful_resolutions}/{len(conflicts)} çakışma çözüldü"
        }
        
    except Exception as e:
        logger.error(f"Error in conflict resolution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Çakışma çözülürken hata oluştu: {str(e)}"
        )

@router.post("/fix-specific-conflicts", response_model=Dict[str, Any])
async def fix_specific_conflicts(
    instructor_ids: List[int],
    timeslot_ids: List[int],
    db: AsyncSession = Depends(get_db)
):
    """
    Belirli instructor ve zaman dilimi çakışmalarını düzeltir
    
    Örnek kullanım:
    - instructor_ids: [3, 21, 11] (çakışan instructor'lar)
    - timeslot_ids: [14, 15, 16] (çakışan zaman dilimleri)
    """
    try:
        logger.info(f"🔧 SPECIFIC CONFLICT RESOLUTION API CALLED: instructors={instructor_ids}, timeslots={timeslot_ids}")
        
        # Mevcut çizelgeyi al
        algorithm_service = AlgorithmService()
        data = await algorithm_service._get_real_data(db)
        
        # Mevcut atamaları al
        from app.services.schedule import ScheduleService
        schedule_service = ScheduleService()
        schedules = await schedule_service.get_filtered(db, limit=1000)
        
        # Schedule formatını assignment formatına çevir
        assignments = []
        for schedule in schedules:
            if schedule.get('project_id'):
                assignment = {
                    'project_id': schedule.get('project_id'),
                    'timeslot_id': schedule.get('timeslot_id'),
                    'classroom_id': schedule.get('classroom_id'),
                    'responsible_instructor_id': schedule.get('responsible_instructor_id'),
                    'instructors': schedule.get('instructors', []),
                    'is_makeup': schedule.get('is_makeup', False)
                }
                assignments.append(assignment)
        
        # Belirli çakışmaları filtrele
        conflict_service = ConflictResolutionService()
        all_conflicts = conflict_service.detect_all_conflicts(
            assignments=assignments,
            projects=data.get('projects', []),
            instructors=data.get('instructors', []),
            classrooms=data.get('classrooms', []),
            timeslots=data.get('timeslots', [])
        )
        
        # Belirtilen instructor ve zaman dilimi çakışmalarını filtrele
        specific_conflicts = []
        for conflict in all_conflicts:
            conflict_instructor = conflict.get('instructor_id')
            conflict_timeslot = conflict.get('timeslot_id')
            
            if (conflict_instructor in instructor_ids and 
                conflict_timeslot in timeslot_ids):
                specific_conflicts.append(conflict)
        
        if not specific_conflicts:
            return {
                "success": True,
                "message": "Belirtilen kriterlere uygun çakışma bulunamadı",
                "conflicts_resolved": 0,
                "resolution_log": []
            }
        
        # Sadece belirli çakışmaları çöz
        resolved_assignments, resolution_log = conflict_service.resolve_conflicts(
            assignments=assignments,
            conflicts=specific_conflicts,
            projects=data.get('projects', []),
            instructors=data.get('instructors', []),
            classrooms=data.get('classrooms', []),
            timeslots=data.get('timeslots', [])
        )
        
        # Başarılı çözüm sayısını hesapla
        successful_resolutions = len([r for r in resolution_log if r.get('success', False)])
        
        logger.info(f"🔧 SPECIFIC CONFLICT RESOLUTION COMPLETED: {successful_resolutions}/{len(specific_conflicts)} resolved")
        
        return {
            "success": True,
            "target_instructors": instructor_ids,
            "target_timeslots": timeslot_ids,
            "conflicts_detected": len(specific_conflicts),
            "conflicts_resolved": successful_resolutions,
            "resolution_log": resolution_log,
            "resolved_assignments": resolved_assignments,
            "message": f"Belirtilen kriterlere göre {successful_resolutions}/{len(specific_conflicts)} çakışma çözüldü"
        }
        
    except Exception as e:
        logger.error(f"Error in specific conflict resolution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Belirli çakışmalar çözülürken hata oluştu: {str(e)}"
        )

@router.get("/conflict-statistics", response_model=Dict[str, Any])
async def get_conflict_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Çakışma istatistiklerini getirir
    """
    try:
        logger.info("📊 CONFLICT STATISTICS API CALLED")
        
        # Mevcut çizelgeyi al
        algorithm_service = AlgorithmService()
        data = await algorithm_service._get_real_data(db)
        
        # Mevcut atamaları al
        from app.services.schedule import ScheduleService
        schedule_service = ScheduleService()
        schedules = await schedule_service.get_filtered(db, limit=1000)
        
        # Schedule formatını assignment formatına çevir
        assignments = []
        for schedule in schedules:
            if schedule.get('project_id'):
                assignment = {
                    'project_id': schedule.get('project_id'),
                    'timeslot_id': schedule.get('timeslot_id'),
                    'classroom_id': schedule.get('classroom_id'),
                    'responsible_instructor_id': schedule.get('responsible_instructor_id'),
                    'instructors': schedule.get('instructors', []),
                    'is_makeup': schedule.get('is_makeup', False)
                }
                assignments.append(assignment)
        
        # Çakışmaları tespit et
        conflict_service = ConflictResolutionService()
        conflicts = conflict_service.detect_all_conflicts(
            assignments=assignments,
            projects=data.get('projects', []),
            instructors=data.get('instructors', []),
            classrooms=data.get('classrooms', []),
            timeslots=data.get('timeslots', [])
        )
        
        # İstatistikleri hesapla
        stats = {
            "total_assignments": len(assignments),
            "total_conflicts": len(conflicts),
            "conflict_rate": len(conflicts) / len(assignments) if assignments else 0,
            "conflict_types": conflict_service._categorize_conflicts(conflicts),
            "severity_breakdown": conflict_service._get_severity_breakdown(conflicts),
            "most_problematic_instructors": conflict_service._get_most_problematic_instructors(conflicts),
            "most_problematic_timeslots": conflict_service._get_most_problematic_timeslots(conflicts),
            "most_problematic_classrooms": conflict_service._get_most_problematic_classrooms(conflicts)
        }
        
        logger.info(f"📊 CONFLICT STATISTICS COMPLETED: {len(conflicts)} conflicts analyzed")
        
        return {
            "success": True,
            "statistics": stats,
            "message": f"{len(conflicts)} çakışma analiz edildi"
        }
        
    except Exception as e:
        logger.error(f"Error in conflict statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Çakışma istatistikleri alınırken hata oluştu: {str(e)}"
        )
