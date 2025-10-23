"""
Final and Makeup Session Management Service
Proje açıklamasına göre: Final ve bütünleme ayrımı sistemi
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.project import Project, ProjectStatus
from app.models.schedule import Schedule
from app.models.instructor import Instructor
from app.models.classroom import Classroom
from app.models.timeslot import TimeSlot
from app.services.algorithm import AlgorithmService
from app.models.algorithm import AlgorithmType

logger = logging.getLogger(__name__)

class FinalMakeupService:
    """
    Final ve bütünleme oturumlarını yöneten servis.
    Proje açıklamasına göre: Final & Bütünleme Ayrımı
    """
    
    def __init__(self):
        self.algorithm_service = AlgorithmService()
    
    async def separate_final_makeup_projects(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Projeleri final ve bütünleme olarak ayırır.
        
        Returns:
            Dict containing final and makeup project lists
        """
        try:
            # Tüm aktif projeleri getir
            result = await db.execute(
                select(Project).filter(Project.is_active == True)
            )
            all_projects = result.scalars().all()
            
            final_projects = []
            makeup_projects = []
            
            for project in all_projects:
                if project.is_makeup:
                    makeup_projects.append(project)
                else:
                    final_projects.append(project)
            
            logger.info(f"Final projects: {len(final_projects)}, Makeup projects: {len(makeup_projects)}")
            
            return {
                "success": True,
                "final_projects": [
                    {
                        "id": p.id,
                        "title": p.title,
                        "type": p.type.value,
                        "responsible_id": p.responsible_id,
                        "participants": [
                            p.responsible_id,
                            p.second_participant_id,
                            p.third_participant_id
                        ]
                    } for p in final_projects
                ],
                "makeup_projects": [
                    {
                        "id": p.id,
                        "title": p.title,
                        "type": p.type.value,
                        "responsible_id": p.responsible_id,
                        "participants": [
                            p.responsible_id,
                            p.second_participant_id,
                            p.third_participant_id
                        ]
                    } for p in makeup_projects
                ],
                "summary": {
                    "total_projects": len(all_projects),
                    "final_count": len(final_projects),
                    "makeup_count": len(makeup_projects)
                }
            }
            
        except Exception as e:
            logger.error(f"Error separating final/makeup projects: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "final_projects": [],
                "makeup_projects": []
            }
    
    async def create_makeup_session(self, db: AsyncSession, session_name: str, 
                                  remaining_projects: List[int]) -> Dict[str, Any]:
        """
        Bütünleme oturumu oluşturur.
        
        Args:
            session_name: Oturum adı
            remaining_projects: Kalan proje ID'leri
            
        Returns:
            Session creation result
        """
        try:
            # Kalan projeleri bütünleme olarak işaretle
            marked_projects = []
            for project_id in remaining_projects:
                result = await db.execute(
                    select(Project).filter(Project.id == project_id)
                )
                project = result.scalar_one_or_none()
                
                if project:
                    project.is_makeup = True
                    project.status = ProjectStatus.MAKEUP
                    db.add(project)
                    marked_projects.append(project)
            
            await db.commit()
            
            # Bütünleme oturumu için optimize et
            makeup_data = await self._prepare_makeup_data(db, marked_projects)
            
            # Bütünleme için özel algoritma seç (Greedy + Local Refinement)
            result, algorithm_run = await self.algorithm_service.run_algorithm(
                AlgorithmType.GREEDY,
                makeup_data,
                {
                    "max_iterations": 100,
                    "local_refinement": True,
                    "session_type": "makeup"
                }
            )
            
            return {
                "success": True,
                "session_name": session_name,
                "session_type": "makeup",
                "project_count": len(marked_projects),
                "algorithm_run_id": algorithm_run.id,
                "result": result,
                "message": f"Bütünleme oturumu '{session_name}' başarıyla oluşturuldu"
            }
            
        except Exception as e:
            logger.error(f"Error creating makeup session: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Bütünleme oturumu oluşturulamadı"
            }
    
    async def create_final_session(self, db: AsyncSession, session_name: str) -> Dict[str, Any]:
        """
        Final oturumu oluşturur.
        
        Args:
            session_name: Oturum adı
            
        Returns:
            Session creation result
        """
        try:
            # Final projelerini getir
            result = await db.execute(
                select(Project).filter(
                    and_(Project.is_active == True, Project.is_makeup == False)
                )
            )
            final_projects = result.scalars().all()
            
            if not final_projects:
                return {
                    "success": False,
                    "error": "Final projesi bulunamadı",
                    "message": "Final oturumu için proje bulunamadı"
                }
            
            # Final oturumu için optimize et
            final_data = await self._prepare_final_data(db, final_projects)
            
            # Final için hibrit algoritma seç (CP-SAT + NSGA-II)
            result, algorithm_run = await self.algorithm_service.run_algorithm(
                AlgorithmType.HYBRID_CP_SAT_NSGA,
                final_data,
                {
                    "cp_sat_timeout": 30,
                    "nsga_generations": 100,
                    "session_type": "final"
                }
            )
            
            return {
                "success": True,
                "session_name": session_name,
                "session_type": "final",
                "project_count": len(final_projects),
                "algorithm_run_id": algorithm_run.id,
                "result": result,
                "message": f"Final oturumu '{session_name}' başarıyla oluşturuldu"
            }
            
        except Exception as e:
            logger.error(f"Error creating final session: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Final oturumu oluşturulamadı"
            }
    
    async def _prepare_final_data(self, db: AsyncSession, projects: List[Project]) -> Dict[str, Any]:
        """Final oturumu için veri hazırla"""
        # Instructors
        result = await db.execute(select(Instructor))
        instructors = result.scalars().all()
        
        # Classrooms
        result = await db.execute(select(Classroom))
        classrooms = result.scalars().all()
        
        # Timeslots
        result = await db.execute(select(TimeSlot))
        timeslots = result.scalars().all()
        
        return {
            "projects": [
                {
                    "id": p.id,
                    "title": p.title,
                    "type": p.type.value,
                    "responsible_id": p.responsible_id,
                    "second_participant_id": p.second_participant_id,
                    "third_participant_id": p.third_participant_id,
                    "is_makeup": p.is_makeup
                } for p in projects
            ],
            "instructors": [
                {
                    "id": i.id,
                    "name": i.name,
                    "type": i.type,
                    "bitirme_count": i.bitirme_count,
                    "ara_count": i.ara_count,
                    "total_load": i.total_load
                } for i in instructors
            ],
            "classrooms": [
                {
                    "id": c.id,
                    "name": c.name,
                    "capacity": c.capacity
                } for c in classrooms
            ],
            "timeslots": [
                {
                    "id": t.id,
                    "start_time": str(t.start_time),
                    "end_time": str(t.end_time),
                    "session_type": t.session_type.value
                } for t in timeslots
            ],
            "session_type": "final"
        }
    
    async def _prepare_makeup_data(self, db: AsyncSession, projects: List[Project]) -> Dict[str, Any]:
        """Bütünleme oturumu için veri hazırla"""
        # Instructors
        result = await db.execute(select(Instructor))
        instructors = result.scalars().all()
        
        # Classrooms
        result = await db.execute(select(Classroom))
        classrooms = result.scalars().all()
        
        # Timeslots
        result = await db.execute(select(TimeSlot))
        timeslots = result.scalars().all()
        
        return {
            "projects": [
                {
                    "id": p.id,
                    "title": p.title,
                    "type": p.type.value,
                    "responsible_id": p.responsible_id,
                    "second_participant_id": p.second_participant_id,
                    "third_participant_id": p.third_participant_id,
                    "is_makeup": p.is_makeup
                } for p in projects
            ],
            "instructors": [
                {
                    "id": i.id,
                    "name": i.name,
                    "type": i.type,
                    "bitirme_count": i.bitirme_count,
                    "ara_count": i.ara_count,
                    "total_load": i.total_load
                } for i in instructors
            ],
            "classrooms": [
                {
                    "id": c.id,
                    "name": c.name,
                    "capacity": c.capacity
                } for c in classrooms
            ],
            "timeslots": [
                {
                    "id": t.id,
                    "start_time": str(t.start_time),
                    "end_time": str(t.end_time),
                    "session_type": t.session_type.value
                } for t in timeslots
            ],
            "session_type": "makeup"
        }
    
    async def compare_final_vs_makeup(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Final ve bütünleme oturumlarını karşılaştırır.
        """
        try:
            # Final ve bütünleme projelerini getir
            final_result = await db.execute(
                select(Project).filter(
                    and_(Project.is_active == True, Project.is_makeup == False)
                )
            )
            final_projects = final_result.scalars().all()
            
            makeup_result = await db.execute(
                select(Project).filter(
                    and_(Project.is_active == True, Project.is_makeup == True)
                )
            )
            makeup_projects = makeup_result.scalars().all()
            
            # İstatistikleri hesapla
            final_stats = self._calculate_session_stats(final_projects)
            makeup_stats = self._calculate_session_stats(makeup_projects)
            
            return {
                "success": True,
                "final_session": {
                    "project_count": len(final_projects),
                    "bitirme_count": final_stats["bitirme_count"],
                    "ara_count": final_stats["ara_count"],
                    "instructor_count": final_stats["unique_instructors"],
                    "complexity": final_stats["complexity"]
                },
                "makeup_session": {
                    "project_count": len(makeup_projects),
                    "bitirme_count": makeup_stats["bitirme_count"],
                    "ara_count": makeup_stats["ara_count"],
                    "instructor_count": makeup_stats["unique_instructors"],
                    "complexity": makeup_stats["complexity"]
                },
                "comparison": {
                    "total_projects": len(final_projects) + len(makeup_projects),
                    "final_ratio": len(final_projects) / (len(final_projects) + len(makeup_projects)),
                    "makeup_ratio": len(makeup_projects) / (len(final_projects) + len(makeup_projects)),
                    "recommended_algorithm_final": "CP-SAT + NSGA-II",
                    "recommended_algorithm_makeup": "Greedy + Local Refinement"
                }
            }
            
        except Exception as e:
            logger.error(f"Error comparing final vs makeup: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_session_stats(self, projects: List[Project]) -> Dict[str, Any]:
        """Oturum istatistiklerini hesapla"""
        bitirme_count = sum(1 for p in projects if p.type.value == "bitirme")
        ara_count = len(projects) - bitirme_count
        
        # Unique instructors
        unique_instructors = set()
        for project in projects:
            if project.responsible_id:
                unique_instructors.add(project.responsible_id)
            if project.second_participant_id:
                unique_instructors.add(project.second_participant_id)
            if project.third_participant_id:
                unique_instructors.add(project.third_participant_id)
        
        # Complexity score (0-1)
        complexity = min(1.0, len(projects) / 100.0)
        
        return {
            "bitirme_count": bitirme_count,
            "ara_count": ara_count,
            "unique_instructors": len(unique_instructors),
            "complexity": complexity
        }
    
    async def get_makeup_session_history(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Bütünleme oturumu geçmişini getirir.
        """
        try:
            # Bütünleme projelerini getir
            result = await db.execute(
                select(Project).filter(Project.is_makeup == True)
            )
            makeup_projects = result.scalars().all()
            
            # Tarihe göre grupla
            history = {}
            for project in makeup_projects:
                date_key = project.created_at.strftime("%Y-%m-%d") if project.created_at else "Unknown"
                if date_key not in history:
                    history[date_key] = []
                history[date_key].append({
                    "id": project.id,
                    "title": project.title,
                    "type": project.type.value,
                    "status": project.status.value
                })
            
            return {
                "success": True,
                "history": history,
                "total_sessions": len(history),
                "total_projects": len(makeup_projects)
            }
            
        except Exception as e:
            logger.error(f"Error getting makeup session history: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
