from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime
import logging

from app import models, schemas
from app.api import deps
from app.db.base import get_db
from app.models.algorithm import AlgorithmType, AlgorithmRun
from app.algorithms.lexicographic import LexicographicAlgorithm

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/optimize", response_model=Dict[str, Any])
async def optimize_with_lexicographic(
    *,
    algorithm_in: Dict[str, Any] = None,
    db: AsyncSession = Depends(get_db),
    # current_user: models.User = Depends(deps.get_current_user)
):
    """
    🤖 Lexicographic (AI-Powered Strategic Pairing) algoritması ile optimizasyon yap
    
    YENİ STRATEJİ:
    - Instructor'ları proje sayısına göre sıralar (EN FAZLA → EN AZ)
    - High-Low pairing: Üst grup ↔ Alt grup eşleştirmesi
    - Bi-directional jury: X sorumlu → Y jüri, Y sorumlu → X jüri
    - Consecutive grouping: Aynı sınıfta, ardışık slotlarda
    - 100% AI-based: Zero hard constraints!
    """
    try:
        from app.models.project import Project
        from app.models.classroom import Classroom
        from app.models.timeslot import TimeSlot
        from app.models.instructor import Instructor
        from app.models.schedule import Schedule
        
        logger.info("🤖 Lexicographic (Strategic Pairing) başlatılıyor...")
        
        # VERİTABANINDAN GERÇEK VERİLERİ AL
        # Projects
        projects_result = await db.execute(
            select(Project).where(Project.is_active == True)
        )
        projects = projects_result.scalars().all()
        
        # Instructors
        instructors_result = await db.execute(select(Instructor))
        instructors = instructors_result.scalars().all()
        
        # Classrooms
        classrooms_result = await db.execute(select(Classroom))
        classrooms = classrooms_result.scalars().all()
        
        # Timeslots
        timeslots_result = await db.execute(
            select(TimeSlot).where(TimeSlot.is_active == True)
        )
        timeslots = timeslots_result.scalars().all()
        
        logger.info(f"📊 Veri yüklendi:")
        logger.info(f"  - Projeler: {len(projects)}")
        logger.info(f"  - Instructors: {len(instructors)}")
        logger.info(f"  - Sınıflar: {len(classrooms)}")
        logger.info(f"  - Timeslots: {len(timeslots)}")
        
        # Veri kontrolü
        if not projects or not instructors or not classrooms or not timeslots:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Eksik veri: Proje, instructor, sınıf veya timeslot bulunamadı!"
            )
        
        # Verileri algoritma formatına dönüştür
        data = {
            "projects": [
                {
                    "id": p.id,
                    "title": p.title,
                    "responsible_id": p.responsible_instructor_id,
                    "responsible_instructor_id": p.responsible_instructor_id,
                    "type": p.type.value if hasattr(p.type, 'value') else str(p.type),
                    "is_makeup": p.is_makeup
                }
                for p in projects
            ],
            "instructors": [
                {
                    "id": i.id,
                    "name": i.name,
                    "type": i.type,
                    "project_count": len([p for p in projects if p.responsible_instructor_id == i.id])
                }
                for i in instructors
            ],
            "timeslots": [
                {
                    "id": t.id,
                    "start_time": str(t.start_time) if t.start_time else "09:00",
                    "end_time": str(t.end_time) if t.end_time else "09:30"
                }
                for t in timeslots
            ],
            "classrooms": [
                {
                    "id": c.id,
                    "name": c.name,
                    "capacity": c.capacity
                }
                for c in classrooms
            ],
            "classroom_count": algorithm_in.get("classroom_count") if algorithm_in else None
        }
        
        # Lexicographic algoritmasını başlat
        lexicographic = LexicographicAlgorithm()
        
        # Optimizasyonu çalıştır
        logger.info("🚀 Lexicographic optimization başlatılıyor...")
        result = lexicographic.optimize(data)
        
        # Mevcut schedule'ları temizle
        await db.execute(delete(Schedule))
        
        # Yeni schedule'ları veritabanına kaydet
        assignments = result.get("assignments", [])
        saved_count = 0
        
        for assignment in assignments:
            project_id = assignment.get("project_id")
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            instructors = assignment.get("instructors", [])
            
            if project_id and classroom_id and timeslot_id:
                # Projeyi bul
                project_result = await db.execute(
                    select(Project).where(Project.id == project_id)
                )
                project = project_result.scalar_one_or_none()
                
                if project:
                    # Instructors'ı normalize et: Placeholder'ları koru, gerçek ID'leri al
                    normalized_instructors = []
                    for inst in instructors:
                        if isinstance(inst, dict):
                            # Placeholder veya dict formatında instructor
                            if inst.get("is_placeholder", False):
                                # Placeholder'ı özel format olarak sakla
                                normalized_instructors.append({
                                    "id": -1,
                                    "name": inst.get("name", "[Araştırma Görevlisi]"),
                                    "is_placeholder": True
                                })
                            else:
                                # Normal instructor dict
                                normalized_instructors.append(inst.get("id", inst))
                        elif isinstance(inst, int):
                            # Integer ID
                            normalized_instructors.append(inst)
                        else:
                            # String veya diğer formatlar
                            normalized_instructors.append(inst)
                    
                    # Schedule oluştur (instructors JSON alanında sakla)
                    new_schedule = Schedule(
                        project_id=project.id,
                        classroom_id=classroom_id,
                        timeslot_id=timeslot_id,
                        instructors=normalized_instructors,  # JSON alanında sakla
                        is_makeup=assignment.get("is_makeup", False)
                    )
                    db.add(new_schedule)
                    saved_count += 1
        
        await db.commit()
        
        logger.info(f"✅ {saved_count} schedule kaydedildi")
        
        # Sonuçları döndür
        stats = result.get("stats", {})
        return {
            "id": 1,
            "task_id": f"lexicographic_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "success",
            "message": f"🧩 Lexicographic optimization başarıyla tamamlandı! {len(assignments)} atama yapıldı, {saved_count} schedule kaydedildi.",
            "algorithm_type": "lexicographic",
            "result": {
                "assignments": assignments,
                "schedule": result.get("schedule", assignments),
                "stats": {
                    "total_assignments": len(assignments),
                    "saved_assignments": saved_count,
                    "total_projects": stats.get("total_projects", 0),
                    "total_instructors": stats.get("total_instructors", 0),
                    "total_classrooms": stats.get("total_classrooms", 0),
                    "placeholder_count": stats.get("placeholder_count", 0),
                    "uniformity_metric": stats.get("uniformity_metric", 0.0),
                    "execution_time": result.get("execution_time", 0.0),
                    "fitness": result.get("fitness", 0.0)
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lexicographic optimizasyon hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lexicographic optimizasyon hatası: {str(e)}"
        )
