"""
Slot Minimization Service
Optimizes schedule to minimize total session count by maximizing parallel project presentations
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class SlotMinimizer:
    """Service for minimizing total session count"""
    
    def __init__(self):
        self.parallel_weight = 2.0  # Weight for parallel scheduling
        self.min_sessions_weight = 3.0  # Weight for minimizing sessions
    
    def minimize_sessions(self, schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Schedule'ı oturum sayısını minimize edecek şekilde optimize eder.
        
        Args:
            schedule: Mevcut schedule
            
        Returns:
            Optimizasyon sonucu
        """
        # Mevcut schedule analizi
        current_analysis = self._analyze_schedule(schedule)
        
        # Optimize edilmiş schedule oluştur
        optimized_schedule = self._create_optimized_schedule(schedule)
        
        # Optimize edilmiş schedule analizi
        optimized_analysis = self._analyze_schedule(optimized_schedule)
        
        # İyileştirme metrikleri
        improvement = self._calculate_improvement(current_analysis, optimized_analysis)
        
        return {
            "original_schedule": {
                "schedule": schedule,
                "analysis": current_analysis
            },
            "optimized_schedule": {
                "schedule": optimized_schedule,
                "analysis": optimized_analysis
            },
            "improvement": improvement,
            "optimization_suggestions": self._generate_optimization_suggestions(current_analysis, optimized_analysis)
        }
    
    def _analyze_schedule(self, schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Schedule'ı analiz eder"""
        
        # Timeslot kullanımını analiz et
        timeslot_usage = defaultdict(list)
        classroom_usage = defaultdict(list)
        
        for assignment in schedule:
            timeslot_id = assignment.get("timeslot_id")
            classroom_id = assignment.get("classroom_id")
            project_id = assignment.get("project_id")
            
            if timeslot_id:
                timeslot_usage[timeslot_id].append({
                    "project_id": project_id,
                    "classroom_id": classroom_id
                })
            
            if classroom_id:
                classroom_usage[classroom_id].append({
                    "project_id": project_id,
                    "timeslot_id": timeslot_id
                })
        
        # Paralel proje sayısını hesapla
        parallel_projects_per_slot = {
            slot_id: len(projects) 
            for slot_id, projects in timeslot_usage.items()
        }
        
        # İstatistikler
        total_sessions = len(timeslot_usage)
        total_projects = len(schedule)
        max_parallel = max(parallel_projects_per_slot.values()) if parallel_projects_per_slot else 0
        avg_parallel = sum(parallel_projects_per_slot.values()) / len(parallel_projects_per_slot) if parallel_projects_per_slot else 0
        
        # Classroom utilization
        classroom_utilization = {}
        for classroom_id, projects in classroom_usage.items():
            unique_timeslots = len(set(proj["timeslot_id"] for proj in projects))
            classroom_utilization[classroom_id] = {
                "total_assignments": len(projects),
                "unique_timeslots": unique_timeslots,
                "utilization_rate": len(projects) / unique_timeslots if unique_timeslots > 0 else 0
            }
        
        return {
            "total_sessions": total_sessions,
            "total_projects": total_projects,
            "max_parallel_projects": max_parallel,
            "avg_parallel_projects": round(avg_parallel, 2),
            "timeslot_usage": dict(timeslot_usage),
            "parallel_projects_per_slot": parallel_projects_per_slot,
            "classroom_utilization": classroom_utilization,
            "efficiency_score": self._calculate_efficiency_score(total_sessions, total_projects, max_parallel)
        }
    
    def _create_optimized_schedule(self, schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Oturum sayısını minimize edecek şekilde schedule oluşturur"""
        
        # Projeleri grupla (conflict olmayan projeler)
        project_groups = self._group_projects_for_parallel_execution(schedule)
        
        # Her grup için en az timeslot kullanacak şekilde atama yap
        optimized_schedule = []
        used_classrooms = set()
        
        for group in project_groups:
            # Bu grup için en uygun timeslot'u bul
            best_timeslot = self._find_best_timeslot_for_group(group, used_classrooms)
            
            # Grup projelerini bu timeslot'a ata
            for i, project in enumerate(group):
                classroom_id = list(used_classrooms)[i % len(used_classrooms)] if used_classrooms else i + 1
                
                optimized_schedule.append({
                    "project_id": project["project_id"],
                    "classroom_id": classroom_id,
                    "timeslot_id": best_timeslot,
                    "instructors": project.get("instructors", [])
                })
        
        return optimized_schedule
    
    def _group_projects_for_parallel_execution(self, schedule: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Paralel çalıştırılabilecek projeleri gruplar"""
        
        # Instructor conflict'lerini kontrol et
        instructor_conflicts = self._find_instructor_conflicts(schedule)
        
        # Conflict olmayan projeleri grupla
        groups = []
        assigned_projects = set()
        
        for assignment in schedule:
            if assignment.get("project_id") in assigned_projects:
                continue
            
            # Bu proje için conflict olmayan projeleri bul
            compatible_projects = [assignment]
            assigned_projects.add(assignment.get("project_id"))
            
            for other_assignment in schedule:
                other_project_id = other_assignment.get("project_id")
                if other_project_id in assigned_projects:
                    continue
                
                # Conflict kontrolü
                if not self._has_conflict(assignment, other_assignment, instructor_conflicts):
                    compatible_projects.append(other_assignment)
                    assigned_projects.add(other_project_id)
            
            groups.append(compatible_projects)
        
        return groups
    
    def _find_instructor_conflicts(self, schedule: List[Dict[str, Any]]) -> Dict[int, Set[int]]:
        """Instructor conflict'lerini bulur"""
        instructor_schedule = defaultdict(set)
        
        for assignment in schedule:
            timeslot_id = assignment.get("timeslot_id")
            for instructor_id in assignment.get("instructors", []):
                instructor_schedule[instructor_id].add(timeslot_id)
        
        return dict(instructor_schedule)
    
    def _has_conflict(self, assignment1: Dict[str, Any], assignment2: Dict[str, Any], 
                     instructor_conflicts: Dict[int, Set[int]]) -> bool:
        """İki assignment arasında conflict var mı kontrol eder"""
        
        # Aynı instructor'ları kontrol et
        instructors1 = set(assignment1.get("instructors", []))
        instructors2 = set(assignment2.get("instructors", []))
        
        common_instructors = instructors1.intersection(instructors2)
        
        if common_instructors:
            return True  # Aynı instructor iki projede olamaz
        
        return False
    
    def _find_best_timeslot_for_group(self, group: List[Dict[str, Any]], 
                                    used_classrooms: Set[int]) -> int:
        """Grup için en uygun timeslot'u bulur"""
        
        # Basit implementasyon - gerçek implementasyonda daha sofistike olabilir
        # Mevcut timeslot'ları kullan
        used_timeslots = set()
        for project in group:
            if "timeslot_id" in project:
                used_timeslots.add(project["timeslot_id"])
        
        # En az kullanılan timeslot'u seç
        if used_timeslots:
            return min(used_timeslots)
        else:
            return 1  # Default timeslot
    
    def _calculate_efficiency_score(self, total_sessions: int, total_projects: int, 
                                  max_parallel: int) -> float:
        """Schedule efficiency skorunu hesaplar"""
        
        if total_sessions == 0 or total_projects == 0:
            return 0.0
        
        # İdeal durum: tüm projeler tek timeslot'ta
        ideal_sessions = 1
        ideal_parallel = total_projects
        
        # Efficiency hesapla
        session_efficiency = ideal_sessions / total_sessions
        parallel_efficiency = max_parallel / ideal_parallel if ideal_parallel > 0 else 0
        
        # Kombine efficiency
        efficiency = (session_efficiency * 0.6 + parallel_efficiency * 0.4)
        
        return round(efficiency, 3)
    
    def _calculate_improvement(self, original: Dict[str, Any], optimized: Dict[str, Any]) -> Dict[str, Any]:
        """İyileştirme metriklerini hesaplar"""
        
        session_reduction = original["total_sessions"] - optimized["total_sessions"]
        session_reduction_percent = (session_reduction / original["total_sessions"]) * 100 if original["total_sessions"] > 0 else 0
        
        parallel_increase = optimized["max_parallel_projects"] - original["max_parallel_projects"]
        efficiency_improvement = optimized["efficiency_score"] - original["efficiency_score"]
        
        return {
            "session_reduction": session_reduction,
            "session_reduction_percent": round(session_reduction_percent, 2),
            "parallel_increase": parallel_increase,
            "efficiency_improvement": round(efficiency_improvement, 3),
            "overall_improvement": "positive" if efficiency_improvement > 0 else "negative" if efficiency_improvement < 0 else "neutral"
        }
    
    def _generate_optimization_suggestions(self, original: Dict[str, Any], 
                                         optimized: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimizasyon önerileri üretir"""
        
        suggestions = []
        
        # Session reduction suggestions
        if optimized["total_sessions"] < original["total_sessions"]:
            suggestions.append({
                "type": "success",
                "category": "session_reduction",
                "message": f"Reduced sessions from {original['total_sessions']} to {optimized['total_sessions']}",
                "impact": "high"
            })
        
        # Parallel execution suggestions
        if optimized["max_parallel_projects"] > original["max_parallel_projects"]:
            suggestions.append({
                "type": "info",
                "category": "parallel_execution",
                "message": f"Increased parallel execution from {original['max_parallel_projects']} to {optimized['max_parallel_projects']} projects",
                "impact": "medium"
            })
        
        # Efficiency suggestions
        if optimized["efficiency_score"] > original["efficiency_score"]:
            suggestions.append({
                "type": "success",
                "category": "efficiency",
                "message": f"Improved efficiency score from {original['efficiency_score']} to {optimized['efficiency_score']}",
                "impact": "high"
            })
        
        # Classroom utilization suggestions
        for classroom_id, utilization in optimized["classroom_utilization"].items():
            if utilization["utilization_rate"] > 0.8:
                suggestions.append({
                    "type": "warning",
                    "category": "classroom_utilization",
                    "message": f"Classroom {classroom_id} has high utilization ({utilization['utilization_rate']:.1%})",
                    "impact": "medium"
                })
        
        return suggestions
    
    def calculate_slot_minimization_fitness(self, schedule: List[Dict[str, Any]]) -> float:
        """Slot minimization fitness skorunu hesaplar"""
        
        analysis = self._analyze_schedule(schedule)
        
        # Fitness components
        session_efficiency = 1.0 / max(1, analysis["total_sessions"])  # Fewer sessions = higher fitness
        parallel_efficiency = analysis["max_parallel_projects"] / max(1, analysis["total_projects"])  # More parallel = higher fitness
        overall_efficiency = analysis["efficiency_score"]
        
        # Weighted combination
        fitness = (
            session_efficiency * 0.4 +
            parallel_efficiency * 0.3 +
            overall_efficiency * 0.3
        )
        
        return round(fitness, 3)
    
    def suggest_slot_optimization_improvements(self, schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Slot optimization için iyileştirme önerileri"""
        
        analysis = self._analyze_schedule(schedule)
        suggestions = []
        
        # Low parallel execution
        if analysis["max_parallel_projects"] < 3:
            suggestions.append({
                "type": "optimization",
                "category": "parallel_execution",
                "message": f"Low parallel execution ({analysis['max_parallel_projects']} projects). Consider grouping compatible projects.",
                "priority": "high"
            })
        
        # High session count
        if analysis["total_sessions"] > analysis["total_projects"] * 0.5:
            suggestions.append({
                "type": "optimization",
                "category": "session_count",
                "message": f"High session count ({analysis['total_sessions']}). Consider consolidating timeslots.",
                "priority": "medium"
            })
        
        # Low efficiency
        if analysis["efficiency_score"] < 0.6:
            suggestions.append({
                "type": "optimization",
                "category": "efficiency",
                "message": f"Low efficiency score ({analysis['efficiency_score']}). Schedule needs optimization.",
                "priority": "high"
            })
        
        return suggestions
