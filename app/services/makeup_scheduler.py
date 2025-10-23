"""
Makeup (Bütünleme) Scheduling Service
Handles separate scheduling for final and makeup sessions
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)


class MakeupScheduler:
    """Service for handling makeup session scheduling"""
    
    def __init__(self):
        self.makeup_session_prefix = "MAKEUP_"
    
    async def identify_makeup_projects(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Bütünleme için kalan projeleri belirler.
        
        Args:
            db: Veritabanı oturumu
            
        Returns:
            Bütünleme projeleri analizi
        """
        from app.models.project import Project
        
        # Tüm projeleri getir
        result = await db.execute(select(Project))
        all_projects = result.scalars().all()
        
        # Final ve bütünleme projelerini ayır
        final_projects = [p for p in all_projects if not p.is_makeup]
        makeup_projects = [p for p in all_projects if p.is_makeup]
        
        # Proje türlerine göre kategorize et
        bitirme_final = [p for p in final_projects if p.type == "bitirme"]
        ara_final = [p for p in final_projects if p.type == "ara"]
        bitirme_makeup = [p for p in makeup_projects if p.type == "bitirme"]
        ara_makeup = [p for p in makeup_projects if p.type == "ara"]
        
        return {
            "total_projects": len(all_projects),
            "final_projects": {
                "total": len(final_projects),
                "bitirme": len(bitirme_final),
                "ara": len(ara_final),
                "projects": final_projects
            },
            "makeup_projects": {
                "total": len(makeup_projects),
                "bitirme": len(bitirme_makeup),
                "ara": len(ara_makeup),
                "projects": makeup_projects
            },
            "makeup_percentage": (len(makeup_projects) / len(all_projects)) * 100 if all_projects else 0
        }
    
    async def create_makeup_session(self, db: AsyncSession, 
                                  session_name: str,
                                  algorithm_type: str = "greedy") -> Dict[str, Any]:
        """
        Bütünleme oturumu oluşturur.
        
        Args:
            db: Veritabanı oturumu
            session_name: Oturum adı
            algorithm_type: Kullanılacak algoritma
            
        Returns:
            Bütünleme oturumu sonucu
        """
        try:
            # Bütünleme projelerini belirle
            makeup_analysis = await self.identify_makeup_projects(db)
            makeup_projects = makeup_analysis["makeup_projects"]["projects"]
            
            if not makeup_projects:
                return {
                    "success": False,
                    "message": "No makeup projects found",
                    "session_data": None
                }
            
            # Bütünleme algoritması için optimize edilmiş parametreler
            makeup_params = self._get_makeup_algorithm_params(algorithm_type, len(makeup_projects))
            
            # Algoritma servisini çağır
            from app.services.algorithm import AlgorithmService
            
            # Bütünleme için veri hazırla
            makeup_data = await self._prepare_makeup_data(db, makeup_projects)
            
            # Algoritma çalıştır
            result, algorithm_run = await AlgorithmService.run_algorithm(
                algorithm_type, makeup_data, makeup_params
            )
            
            # Bütünleme oturumu bilgileri
            session_info = {
                "session_name": session_name,
                "session_type": "makeup",
                "algorithm_used": algorithm_type,
                "project_count": len(makeup_projects),
                "algorithm_run_id": algorithm_run.id,
                "created_at": algorithm_run.started_at,
                "completed_at": algorithm_run.completed_at,
                "execution_time": algorithm_run.execution_time,
                "status": algorithm_run.status
            }
            
            return {
                "success": True,
                "message": f"Makeup session '{session_name}' created successfully",
                "session_data": session_info,
                "algorithm_result": result,
                "makeup_analysis": makeup_analysis
            }
            
        except Exception as e:
            logger.error(f"Error creating makeup session: {str(e)}")
            return {
                "success": False,
                "message": f"Error creating makeup session: {str(e)}",
                "session_data": None
            }
    
    def _get_makeup_algorithm_params(self, algorithm_type: str, project_count: int) -> Dict[str, Any]:
        """Bütünleme algoritması için optimize edilmiş parametreler"""
        
        # Bütünleme için daha hızlı ve basit parametreler
        base_params = {
            "max_execution_time": 60,  # 1 dakika (bütünleme daha az proje)
            "project_count": project_count
        }
        
        if algorithm_type == "greedy":
            return {
                **base_params,
                "optimization_level": "fast",
                "quality_threshold": 0.7  # Bütünleme için daha düşük kalite threshold
            }
        elif algorithm_type == "genetic_algorithm":
            return {
                **base_params,
                "population_size": min(50, project_count * 2),  # Daha küçük popülasyon
                "generations": min(20, project_count),  # Daha az generation
                "mutation_rate": 0.15
            }
        elif algorithm_type == "simulated_annealing":
            return {
                **base_params,
                "initial_temperature": 100,
                "cooling_rate": 0.95,
                "max_iterations": min(1000, project_count * 50)
            }
        elif algorithm_type == "cp_sat":
            return {
                **base_params,
                "timeout_seconds": 30,  # Daha kısa timeout
                "optimization_level": "fast"
            }
        else:
            return base_params
    
    async def _prepare_makeup_data(self, db: AsyncSession, 
                                 makeup_projects: List[Any]) -> Dict[str, Any]:
        """Bütünleme için veri hazırlar"""
        from app.models.instructor import Instructor
        from app.models.classroom import Classroom
        from app.models.timeslot import TimeSlot
        
        # Sadece bütünleme projelerini dahil et
        projects_data = []
        for project in makeup_projects:
            projects_data.append({
                "id": project.id,
                "title": project.title,
                "type": project.type,
                "is_makeup": True,
                "responsible_id": project.responsible_id,
                "advisor_id": project.advisor_id,
                "co_advisor_id": project.co_advisor_id
            })
        
        # Instructor'ları getir
        result = await db.execute(select(Instructor))
        instructors = result.scalars().all()
        instructors_data = [
            {
                "id": inst.id,
                "name": inst.name,
                "type": inst.type,
                "total_load": inst.total_load or 0
            }
            for inst in instructors
        ]
        
        # Classroom'ları getir
        result = await db.execute(select(Classroom))
        classrooms = result.scalars().all()
        classrooms_data = [
            {
                "id": cls.id,
                "name": cls.name,
                "capacity": cls.capacity
            }
            for cls in classrooms
        ]
        
        # TimeSlot'ları getir
        result = await db.execute(select(TimeSlot))
        timeslots = result.scalars().all()
        timeslots_data = [
            {
                "id": ts.id,
                "start_time": ts.start_time,
                "end_time": ts.end_time,
                "is_morning": ts.is_morning
            }
            for ts in timeslots
        ]
        
        return {
            "projects": projects_data,
            "instructors": instructors_data,
            "classrooms": classrooms_data,
            "timeslots": timeslots_data,
            "session_type": "makeup"
        }
    
    async def compare_final_vs_makeup(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Final ve bütünleme oturumlarını karşılaştırır.
        
        Args:
            db: Veritabanı oturumu
            
        Returns:
            Karşılaştırma sonucu
        """
        # Final ve bütünleme analizi
        makeup_analysis = await self.identify_makeup_projects(db)
        
        # Algoritma run'larını getir
        from app.models.algorithm import AlgorithmRun
        
        # Son final run
        result = await db.execute(
            select(AlgorithmRun)
            .where(AlgorithmRun.status == "completed")
            .order_by(AlgorithmRun.completed_at.desc())
            .limit(1)
        )
        latest_final_run = result.scalar_one_or_none()
        
        # Son bütünleme run
        # Bu kısım daha spesifik olabilir, örneğin session_type field'ı eklenebilir
        result = await db.execute(
            select(AlgorithmRun)
            .where(AlgorithmRun.status == "completed")
            .order_by(AlgorithmRun.completed_at.desc())
            .limit(2)
        )
        all_runs = result.scalars().all()
        
        # Basit karşılaştırma (gerçek implementasyonda session_type field'ı olmalı)
        comparison = {
            "project_distribution": makeup_analysis,
            "latest_runs": {
                "final": {
                    "run_id": latest_final_run.id if latest_final_run else None,
                    "status": latest_final_run.status if latest_final_run else None,
                    "execution_time": latest_final_run.execution_time if latest_final_run else None
                },
                "makeup": {
                    "run_id": all_runs[1].id if len(all_runs) > 1 else None,
                    "status": all_runs[1].status if len(all_runs) > 1 else None,
                    "execution_time": all_runs[1].execution_time if len(all_runs) > 1 else None
                }
            },
            "recommendations": self._generate_scheduling_recommendations(makeup_analysis)
        }
        
        return comparison
    
    def _generate_scheduling_recommendations(self, makeup_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scheduling önerileri üretir"""
        recommendations = []
        
        makeup_count = makeup_analysis["makeup_projects"]["total"]
        makeup_percentage = makeup_analysis["makeup_percentage"]
        
        if makeup_percentage > 30:
            recommendations.append({
                "type": "warning",
                "message": f"High makeup percentage ({makeup_percentage:.1f}%). Consider reviewing project requirements.",
                "priority": "high"
            })
        elif makeup_percentage > 15:
            recommendations.append({
                "type": "info",
                "message": f"Moderate makeup percentage ({makeup_percentage:.1f}%). Standard makeup session recommended.",
                "priority": "medium"
            })
        else:
            recommendations.append({
                "type": "success",
                "message": f"Low makeup percentage ({makeup_percentage:.1f}%). Quick makeup session sufficient.",
                "priority": "low"
            })
        
        if makeup_count > 20:
            recommendations.append({
                "type": "algorithm",
                "message": f"Large makeup session ({makeup_count} projects). Use efficient algorithm like CP-SAT or Greedy.",
                "algorithm_suggestion": "cp_sat",
                "priority": "medium"
            })
        elif makeup_count > 10:
            recommendations.append({
                "type": "algorithm",
                "message": f"Medium makeup session ({makeup_count} projects). Genetic Algorithm or Simulated Annealing recommended.",
                "algorithm_suggestion": "genetic_algorithm",
                "priority": "medium"
            })
        else:
            recommendations.append({
                "type": "algorithm",
                "message": f"Small makeup session ({makeup_count} projects). Greedy algorithm sufficient.",
                "algorithm_suggestion": "greedy",
                "priority": "low"
            })
        
        return recommendations
    
    async def get_makeup_session_history(self, db: AsyncSession) -> Dict[str, Any]:
        """Bütünleme oturumu geçmişini getirir"""
        from app.models.algorithm import AlgorithmRun
        
        # Son 10 run'u getir
        result = await db.execute(
            select(AlgorithmRun)
            .order_by(AlgorithmRun.completed_at.desc().nullslast())
            .limit(10)
        )
        runs = result.scalars().all()
        
        # Basit analiz (gerçek implementasyonda session_type field'ı olmalı)
        makeup_runs = []
        final_runs = []
        
        for run in runs:
            # Bu kısım session_type field'ı ile geliştirilebilir
            # Şimdilik basit bir yaklaşım
            if "makeup" in run.algorithm_type.lower() or run.execution_time and run.execution_time < 120:  # 2 dakikadan kısa
                makeup_runs.append({
                    "id": run.id,
                    "algorithm_type": run.algorithm_type,
                    "status": run.status,
                    "execution_time": run.execution_time,
                    "started_at": run.started_at,
                    "completed_at": run.completed_at
                })
            else:
                final_runs.append({
                    "id": run.id,
                    "algorithm_type": run.algorithm_type,
                    "status": run.status,
                    "execution_time": run.execution_time,
                    "started_at": run.started_at,
                    "completed_at": run.completed_at
                })
        
        return {
            "total_runs": len(runs),
            "final_runs": final_runs,
            "makeup_runs": makeup_runs,
            "latest_makeup": makeup_runs[0] if makeup_runs else None,
            "latest_final": final_runs[0] if final_runs else None
        }
