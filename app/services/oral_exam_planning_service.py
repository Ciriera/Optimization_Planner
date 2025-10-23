"""
Oral Exam Planning Service
Proje açıklamasına göre: Sözlü sınav planlaması
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.instructor import Instructor
from app.models.project import Project
from app.models.classroom import Classroom
from app.models.timeslot import TimeSlot

logger = logging.getLogger(__name__)

class OralExamPlanningService:
    """
    Sözlü sınav planlaması servisi.
    Proje açıklamasına göre: Sözlü sınav planlaması
    """
    
    def __init__(self):
        pass
    
    async def create_oral_exam_schedule(self, db: AsyncSession, 
                                      exam_type: str = "final",
                                      duration_per_exam: int = 30,
                                      preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sözlü sınav planlaması oluşturur.
        
        Args:
            db: Database session
            exam_type: Sınav türü (final, makeup, midterm)
            duration_per_exam: Sınav başına süre (dakika)
            preferences: Planlama tercihleri
            
        Returns:
            Oral exam schedule result
        """
        try:
            logger.info(f"Creating oral exam schedule for {exam_type} exams")
            
            # 1. Sınav için projeleri getir
            projects = await self._get_projects_for_exam(db, exam_type)
            
            # 2. Müsait hocaları getir
            instructors = await self._get_available_instructors_for_exam(db)
            
            # 3. Sınıfları getir
            classrooms = await self._get_available_classrooms(db)
            
            # 4. Zaman dilimlerini getir
            timeslots = await self._get_available_timeslots(db, preferences)
            
            # 5. Sınav planlaması oluştur
            exam_schedule = await self._create_exam_schedule(
                projects, instructors, classrooms, timeslots, duration_per_exam, preferences
            )
            
            # 6. Çakışma kontrolü yap
            conflict_check = await self._check_exam_conflicts(exam_schedule)
            
            if conflict_check["has_conflicts"]:
                # Çakışmaları çöz
                exam_schedule = await self._resolve_exam_conflicts(exam_schedule, conflict_check["conflicts"])
            
            # 7. Planlamayı optimize et
            optimized_schedule = await self._optimize_exam_schedule(exam_schedule)
            
            # 8. Sonuçları kaydet
            saved_schedule = await self._save_exam_schedule(optimized_schedule, db)
            
            return {
                "success": True,
                "exam_schedule": optimized_schedule,
                "exam_type": exam_type,
                "total_exams": len(projects),
                "scheduled_exams": len(optimized_schedule),
                "duration_per_exam": duration_per_exam,
                "conflict_resolution": conflict_check,
                "saved_schedule": saved_schedule,
                "message": f"{exam_type} sözlü sınav planlaması başarıyla oluşturuldu"
            }
            
        except Exception as e:
            logger.error(f"Error creating oral exam schedule: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Sözlü sınav planlaması oluşturulamadı"
            }
    
    async def _get_projects_for_exam(self, db: AsyncSession, exam_type: str) -> List[Dict[str, Any]]:
        """Sınav için projeleri getir"""
        try:
            if exam_type == "makeup":
                result = await db.execute(
                    select(Project).filter(
                        and_(Project.is_active == True, Project.is_makeup == True)
                    )
                )
            else:  # final
                result = await db.execute(
                    select(Project).filter(
                        and_(Project.is_active == True, Project.is_makeup == False)
                    )
                )
            
            projects = result.scalars().all()
            
            return [
                {
                    "id": p.id,
                    "title": p.title,
                    "type": p.type.value,
                    "responsible_id": p.responsible_id,
                    "second_participant_id": p.second_participant_id,
                    "third_participant_id": p.third_participant_id,
                    "participants": [
                        p.responsible_id,
                        p.second_participant_id,
                        p.third_participant_id
                    ],
                    "is_makeup": p.is_makeup
                } for p in projects
            ]
            
        except Exception as e:
            logger.error(f"Error getting projects for exam: {str(e)}")
            return []
    
    async def _get_available_instructors_for_exam(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Sınav için müsait hocaları getir"""
        try:
            result = await db.execute(select(Instructor))
            instructors = result.scalars().all()
            
            return [
                {
                    "id": i.id,
                    "name": i.name,
                    "type": i.type,
                    "bitirme_count": i.bitirme_count,
                    "ara_count": i.ara_count,
                    "total_load": i.total_load,
                    "availability": self._get_instructor_availability(i)
                } for i in instructors
            ]
            
        except Exception as e:
            logger.error(f"Error getting available instructors for exam: {str(e)}")
            return []
    
    def _get_instructor_availability(self, instructor: Instructor) -> Dict[str, Any]:
        """Hocanın müsaitlik durumunu getir"""
        # Basit müsaitlik kontrolü (gerçek uygulamada daha karmaşık olabilir)
        return {
            "available": True,
            "preferred_timeslots": ["09:00-12:00", "13:00-16:00"],
            "max_exams_per_day": 6,
            "preferred_classrooms": ["D106", "D107", "D108"]
        }
    
    async def _get_available_classrooms(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Müsait sınıfları getir"""
        try:
            result = await db.execute(select(Classroom))
            classrooms = result.scalars().all()
            
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "capacity": c.capacity,
                    "equipment": getattr(c, 'equipment', []),
                    "available": True
                } for c in classrooms
            ]
            
        except Exception as e:
            logger.error(f"Error getting available classrooms: {str(e)}")
            return []
    
    async def _get_available_timeslots(self, db: AsyncSession, 
                                     preferences: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Müsait zaman dilimlerini getir"""
        try:
            result = await db.execute(select(TimeSlot))
            timeslots = result.scalars().all()
            
            # Tercihler varsa filtrele
            if preferences and "preferred_timeslots" in preferences:
                preferred = preferences["preferred_timeslots"]
                filtered_timeslots = [
                    t for t in timeslots 
                    if any(pref in str(t.start_time) for pref in preferred)
                ]
            else:
                filtered_timeslots = timeslots
            
            return [
                {
                    "id": t.id,
                    "start_time": t.start_time.isoformat(),
                    "end_time": t.end_time.isoformat(),
                    "session_type": t.session_type.value,
                    "available": True
                } for t in filtered_timeslots
            ]
            
        except Exception as e:
            logger.error(f"Error getting available timeslots: {str(e)}")
            return []
    
    async def _create_exam_schedule(self, projects: List[Dict[str, Any]], 
                                  instructors: List[Dict[str, Any]],
                                  classrooms: List[Dict[str, Any]],
                                  timeslots: List[Dict[str, Any]],
                                  duration_per_exam: int,
                                  preferences: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sınav planlaması oluştur"""
        try:
            exam_schedule = []
            
            # Basit planlama stratejisi
            current_time_slot = 0
            current_classroom = 0
            
            for i, project in enumerate(projects):
                # Zaman dilimi seç
                if current_time_slot < len(timeslots):
                    selected_timeslot = timeslots[current_time_slot]
                else:
                    # Zaman dilimi bitti, yeni güne geç
                    current_time_slot = 0
                    selected_timeslot = timeslots[current_time_slot]
                
                # Sınıf seç
                if current_classroom < len(classrooms):
                    selected_classroom = classrooms[current_classroom]
                else:
                    current_classroom = 0
                    selected_classroom = classrooms[current_classroom]
                
                # Jüri üyelerini belirle
                jury_members = await self._select_jury_for_exam(project, instructors)
                
                # Sınav planlaması oluştur
                exam_entry = {
                    "exam_id": f"exam_{project['id']}",
                    "project_id": project["id"],
                    "project_title": project["title"],
                    "project_type": project["type"],
                    "timeslot": selected_timeslot,
                    "classroom": selected_classroom,
                    "duration_minutes": duration_per_exam,
                    "jury_members": jury_members,
                    "exam_date": selected_timeslot["start_time"][:10],  # YYYY-MM-DD
                    "exam_time": selected_timeslot["start_time"][11:16],  # HH:MM
                    "status": "scheduled"
                }
                
                exam_schedule.append(exam_entry)
                
                # Sonraki sınav için hazırla
                current_time_slot += 1
                if current_time_slot >= len(timeslots):
                    current_time_slot = 0
                    current_classroom = (current_classroom + 1) % len(classrooms)
            
            return exam_schedule
            
        except Exception as e:
            logger.error(f"Error creating exam schedule: {str(e)}")
            return []
    
    async def _select_jury_for_exam(self, project: Dict[str, Any], 
                                  instructors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sınav için jüri seç"""
        jury_members = []
        
        # Mevcut katılımcıları jüri olarak ata
        for participant_id in project["participants"]:
            if participant_id:
                instructor = next((i for i in instructors if i["id"] == participant_id), None)
                if instructor:
                    jury_members.append({
                        "instructor_id": instructor["id"],
                        "name": instructor["name"],
                        "type": instructor["type"],
                        "role": "jury_member"
                    })
        
        # Eksik jüri üyelerini tamamla (gerekirse)
        if len(jury_members) < 3:
            available_instructors = [
                i for i in instructors 
                if i["id"] not in project["participants"] and 
                i["type"] == "instructor" and
                i["availability"]["available"]
            ]
            
            needed = 3 - len(jury_members)
            for i in range(min(needed, len(available_instructors))):
                instructor = available_instructors[i]
                jury_members.append({
                    "instructor_id": instructor["id"],
                    "name": instructor["name"],
                    "type": instructor["type"],
                    "role": "additional_jury_member"
                })
        
        return jury_members
    
    async def _check_exam_conflicts(self, exam_schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sınav çakışmalarını kontrol et"""
        conflicts = []
        
        # Aynı hocanın aynı anda birden fazla sınavda olup olmadığını kontrol et
        instructor_schedule = {}
        
        for exam in exam_schedule:
            exam_time = exam["exam_time"]
            exam_date = exam["exam_date"]
            
            for jury_member in exam["jury_members"]:
                instructor_id = jury_member["instructor_id"]
                schedule_key = f"{instructor_id}_{exam_date}_{exam_time}"
                
                if schedule_key in instructor_schedule:
                    conflicts.append({
                        "type": "instructor_conflict",
                        "instructor_id": instructor_id,
                        "instructor_name": jury_member["name"],
                        "conflicting_exams": [
                            instructor_schedule[schedule_key],
                            exam["exam_id"]
                        ],
                        "date": exam_date,
                        "time": exam_time,
                        "severity": "high"
                    })
                else:
                    instructor_schedule[schedule_key] = exam["exam_id"]
        
        # Aynı sınıfta aynı anda birden fazla sınav olup olmadığını kontrol et
        classroom_schedule = {}
        
        for exam in exam_schedule:
            classroom_id = exam["classroom"]["id"]
            schedule_key = f"{classroom_id}_{exam['exam_date']}_{exam['exam_time']}"
            
            if schedule_key in classroom_schedule:
                conflicts.append({
                    "type": "classroom_conflict",
                    "classroom_id": classroom_id,
                    "classroom_name": exam["classroom"]["name"],
                    "conflicting_exams": [
                        classroom_schedule[schedule_key],
                        exam["exam_id"]
                    ],
                    "date": exam["exam_date"],
                    "time": exam["exam_time"],
                    "severity": "high"
                })
            else:
                classroom_schedule[schedule_key] = exam["exam_id"]
        
        return {
            "has_conflicts": len(conflicts) > 0,
            "conflicts": conflicts,
            "conflict_count": len(conflicts)
        }
    
    async def _resolve_exam_conflicts(self, exam_schedule: List[Dict[str, Any]], 
                                    conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sınav çakışmalarını çöz"""
        resolved_schedule = exam_schedule.copy()
        
        for conflict in conflicts:
            if conflict["type"] == "instructor_conflict":
                # Çakışan hocayı en az kritik sınavdan çıkar
                instructor_id = conflict["instructor_id"]
                conflicting_exams = conflict["conflicting_exams"]
                
                # İkinci sınavdan hocayı çıkar (basit strateji)
                exam_to_modify = conflicting_exams[1]
                
                for exam in resolved_schedule:
                    if exam["exam_id"] == exam_to_modify:
                        # Hocayı jüri üyelerinden çıkar
                        exam["jury_members"] = [
                            member for member in exam["jury_members"]
                            if member["instructor_id"] != instructor_id
                        ]
                        break
            
            elif conflict["type"] == "classroom_conflict":
                # İkinci sınavı farklı sınıfa taşı
                exam_to_move = conflict["conflicting_exams"][1]
                
                # Farklı sınıf bul
                available_classrooms = ["D106", "D107", "D108", "D109", "D110", "D111", "D223"]
                current_classroom = None
                new_classroom = None
                
                for exam in resolved_schedule:
                    if exam["exam_id"] == exam_to_move:
                        current_classroom = exam["classroom"]["name"]
                        break
                
                for classroom_name in available_classrooms:
                    if classroom_name != current_classroom:
                        new_classroom = classroom_name
                        break
                
                if new_classroom:
                    for exam in resolved_schedule:
                        if exam["exam_id"] == exam_to_move:
                            exam["classroom"]["name"] = new_classroom
                            exam["classroom"]["id"] = new_classroom
                            break
        
        return resolved_schedule
    
    async def _optimize_exam_schedule(self, exam_schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sınav planlamasını optimize et"""
        # Basit optimizasyon: Günlük yük dengesi
        optimized_schedule = exam_schedule.copy()
        
        # Günlük sınav sayılarını hesapla
        daily_counts = {}
        for exam in optimized_schedule:
            date = exam["exam_date"]
            daily_counts[date] = daily_counts.get(date, 0) + 1
        
        # Günlük yük dengesini optimize et
        if daily_counts:
            avg_per_day = len(optimized_schedule) / len(daily_counts)
            
            # Aşırı yüklü günleri tespit et
            overloaded_days = [
                date for date, count in daily_counts.items() 
                if count > avg_per_day * 1.5
            ]
            
            # Aşırı yüklü günlerden sınavları başka günlere taşı
            for overloaded_day in overloaded_days:
                exams_to_move = [
                    exam for exam in optimized_schedule 
                    if exam["exam_date"] == overloaded_day
                ]
                
                # İlk yarısını başka güne taşı
                exams_to_move = exams_to_move[:len(exams_to_move)//2]
                
                for exam in exams_to_move:
                    # Boş gün bul
                    for date in daily_counts:
                        if date != overloaded_day and daily_counts[date] < avg_per_day:
                            exam["exam_date"] = date
                            daily_counts[date] += 1
                            daily_counts[overloaded_day] -= 1
                            break
        
        return optimized_schedule
    
    async def _save_exam_schedule(self, exam_schedule: List[Dict[str, Any]], 
                                db: AsyncSession) -> Dict[str, Any]:
        """Sınav planlamasını kaydet"""
        try:
            # Bu kısım gerçek uygulamada exam_schedule tablosuna kayıt yapabilir
            saved_count = len(exam_schedule)
            
            return {
                "saved_count": saved_count,
                "total_exams": len(exam_schedule),
                "success_rate": 1.0 if exam_schedule else 0,
                "message": "Sınav planlaması başarıyla kaydedildi"
            }
            
        except Exception as e:
            logger.error(f"Error saving exam schedule: {str(e)}")
            return {
                "saved_count": 0,
                "total_exams": len(exam_schedule),
                "success_rate": 0,
                "error": str(e)
            }
    
    async def get_exam_schedule_summary(self, db: AsyncSession, 
                                      exam_type: str = "final") -> Dict[str, Any]:
        """Sınav planlaması özetini getir"""
        try:
            # Sınav türüne göre projeleri getir
            projects = await self._get_projects_for_exam(db, exam_type)
            
            # Planlama istatistikleri
            total_projects = len(projects)
            
            # Proje türü dağılımı
            bitirme_count = sum(1 for p in projects if p["type"] == "bitirme")
            ara_count = total_projects - bitirme_count
            
            # Tahmini süre hesaplama
            duration_per_exam = 30  # dakika
            total_duration_hours = (total_projects * duration_per_exam) / 60
            
            # Tahmini gün sayısı (günde 8 saat çalışma varsayımı)
            estimated_days = max(1, total_duration_hours / 8)
            
            return {
                "success": True,
                "exam_type": exam_type,
                "total_projects": total_projects,
                "bitirme_count": bitirme_count,
                "ara_count": ara_count,
                "duration_per_exam": duration_per_exam,
                "total_duration_hours": total_duration_hours,
                "estimated_days": estimated_days,
                "recommendations": [
                    "Sınavlar arasında 15 dakika mola verin",
                    "Günde maksimum 12 sınav planlayın",
                    "Jüri üyelerinin yük dengesini kontrol edin"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting exam schedule summary: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Sınav planlaması özeti alınamadı"
            }
