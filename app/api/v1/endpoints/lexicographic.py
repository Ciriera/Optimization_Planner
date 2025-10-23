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
                    "supervisor_id": p.responsible_instructor_id,
                    "type": p.type.value if hasattr(p.type, 'value') else str(p.type),
                    "is_makeup": p.is_makeup
                }
                for p in projects
            ],
            "instructors": [
                {
                    "id": i.id,
                    "name": i.name,
                    "project_count": len([p for p in projects if p.responsible_instructor_id == i.id]),
                    "availability": [True] * len(timeslots)  # Varsayılan olarak tüm zaman dilimlerinde müsait
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
            ]
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
            # Supervisor ve jury bilgilerini al
            supervisor_id = assignment.get("supervisor_id")
            jury_id = assignment.get("jury_id")
            time_slot_id = assignment.get("time_slot_id")
            
            if supervisor_id and jury_id and time_slot_id:
                # Projeyi bul (supervisor'a göre)
                project_result = await db.execute(
                    select(Project).where(Project.responsible_instructor_id == supervisor_id).limit(1)
                )
                project = project_result.scalar_one_or_none()
                
                if project:
                    # Algoritmanın atadığı sınıfı kullan veya rastgele bir sınıf seç
                    classroom_id = assignment.get("classroom_id")
                    
                    # Eğer sınıf ID'si yoksa veya geçersizse rastgele bir sınıf seç
                    if not classroom_id or not any(c.id == classroom_id for c in classrooms):
                        # Sınıf dağılımını optimize etmek için en az kullanılan sınıfı seç
                        classroom_usage = {}
                        for c in classrooms:
                            classroom_usage[c.id] = 0
                        
                        # Mevcut atamaları say
                        for a in assignments:
                            if a.get("classroom_id") in classroom_usage:
                                classroom_usage[a.get("classroom_id")] += 1
                        
                        # En az kullanılan sınıfları bul
                        min_usage = min(classroom_usage.values()) if classroom_usage else 0
                        least_used_classrooms = [c for c in classrooms if classroom_usage.get(c.id, 0) == min_usage]
                        
                        # Rastgele bir sınıf seç (çeşitlilik için)
                        import random
                        classroom = random.choice(least_used_classrooms) if least_used_classrooms else (classrooms[0] if classrooms else None)
                    else:
                        # Algoritmanın atadığı sınıfı bul
                        classroom = next((c for c in classrooms if c.id == classroom_id), classrooms[0] if classrooms else None)
                    
                    if classroom:
                        # Schedule oluştur
                        new_schedule = Schedule(
                            project_id=project.id,
                            classroom_id=classroom.id,
                            timeslot_id=time_slot_id,
                            is_makeup=False
                        )
                        db.add(new_schedule)
                        saved_count += 1
        
        await db.commit()
        
        logger.info(f"✅ {saved_count} schedule kaydedildi")
        
        # AI metriklerini hesapla
        ai_metrics = lexicographic.get_ai_enhanced_metrics()
        
        # Sonuçları döndür
        return {
            "id": 1,
            "task_id": f"lexicographic_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "success",
            "message": f"🤖 Lexicographic optimization başarıyla tamamlandı! {len(assignments)} atama yapıldı, {saved_count} schedule kaydedildi.",
            "algorithm_type": "lexicographic",
            "result": {
                "assignments": assignments,
                "ai_metrics": ai_metrics,
                "stats": {
                    "total_assignments": len(assignments),
                    "saved_assignments": saved_count,
                    "workload_distribution": ai_metrics.get("workload_distribution", 0),
                    "pairing_efficiency": ai_metrics.get("pairing_efficiency", 0),
                    "schedule_optimization": ai_metrics.get("schedule_optimization", 0)
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
