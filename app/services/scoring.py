"""
Scoring service for optimization results
Generates score.json and calculates various metrics
"""

from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.schedule import Schedule
from app.models.project import Project
from app.models.instructor import Instructor
from app.models.classroom import Classroom
from app.models.timeslot import TimeSlot
from app.core.config import settings


class ScoringService:
    """Service for calculating and generating optimization scores."""
    
    def __init__(self):
        # Mevcut dizini kullan
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.scores_dir = os.path.join(current_dir, "scores")
        os.makedirs(self.scores_dir, exist_ok=True)
    
    async def calculate_scores(self, db: AsyncSession, algorithm_run_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive scores for current schedules.
        
        Args:
            db: Database session
            algorithm_run_id: Optional algorithm run ID for tracking
            
        Returns:
            Dict containing all calculated scores
        """
        # Get current schedules with relations
        result = await db.execute(
            select(Schedule)
            .options(
                joinedload(Schedule.project),
                joinedload(Schedule.classroom),
                joinedload(Schedule.timeslot)
            )
        )
        schedules = result.scalars().all()
        
        if not schedules:
            return self._empty_scores()
        
        # Calculate individual metrics according to project specification
        objective_scores = {
            "load_balance": await self._calculate_load_balance_score(db, schedules),
            "classroom_changes": self._calculate_classroom_changes_score(schedules),
            "time_efficiency": self._calculate_time_efficiency_score(schedules),
            "session_minimization": self._calculate_session_minimization_score(schedules),
            "rule_compliance": await self._calculate_rule_compliance_score(db, schedules)
        }
        
        scores = {
            "timestamp": datetime.now().isoformat(),
            "algorithm_run_id": algorithm_run_id,
            "total_schedules": len(schedules),
            "objective_scores": objective_scores,
            "metrics": {
                **objective_scores,
                "gini_coefficient": await self._calculate_gini_coefficient(db, schedules),
                "instructor_preference": self._calculate_instructor_preference_score(schedules),
                "classroom_utilization": self._calculate_classroom_utilization_score(schedules),
                "time_slot_distribution": self._calculate_time_slot_distribution_score(schedules)
            }
        }
        
        # Calculate weighted overall score using project specification formula
        from app.services.objective_weights_service import ObjectiveWeightsService
        weights_service = ObjectiveWeightsService()
        weighted_result = await weights_service.calculate_weighted_score(objective_scores)
        
        if weighted_result["success"]:
            scores["weighted_score"] = weighted_result
            scores["overall_score"] = weighted_result["total_weighted_score"]
        else:
            # Fallback to simple average if weighted calculation fails
            scores["overall_score"] = self._calculate_overall_score(scores["metrics"])
            scores["weighted_score"] = {"success": False, "error": weighted_result.get("message", "Unknown error")}
        
        # Add detailed breakdowns
        scores["breakdowns"] = {
            "by_project_type": self._calculate_scores_by_project_type(schedules),
            "by_instructor": await self._calculate_scores_by_instructor(db, schedules),
            "by_classroom": self._calculate_scores_by_classroom(schedules),
            "by_timeslot": self._calculate_scores_by_timeslot(schedules)
        }
        
        return scores
    
    async def _calculate_load_balance_score(self, db: AsyncSession, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate load balance score."""
        # Get instructor loads
        result = await db.execute(select(Instructor))
        instructors = result.scalars().all()
        
        instructor_loads = {}
        for instructor in instructors:
            instructor_loads[instructor.id] = {
                "name": instructor.name,
                "type": instructor.type,
                "bitirme_count": instructor.bitirme_count or 0,
                "ara_count": instructor.ara_count or 0,
                "total_load": instructor.total_load or 0
            }
        
        # Calculate variance and statistics
        loads = [load["total_load"] for load in instructor_loads.values() if load["total_load"] > 0]
        
        if not loads:
            return {"score": 0.0, "variance": 0.0, "mean": 0.0, "details": {}}
        
        mean_load = sum(loads) / len(loads)
        variance = sum((load - mean_load) ** 2 for load in loads) / len(loads)
        
        # Lower variance = better load balance
        max_variance = mean_load ** 2 if mean_load > 0 else 1
        normalized_variance = variance / max_variance if max_variance > 0 else 0
        score = max(0, 1 - normalized_variance)
        
        return {
            "score": score,
            "variance": variance,
            "mean": mean_load,
            "min": min(loads),
            "max": max(loads),
            "details": instructor_loads
        }
    
    def _calculate_classroom_changes_score(self, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate classroom changes score."""
        instructor_classrooms = {}
        changes = 0
        total_assignments = 0
        
        for schedule in schedules:
            # Get instructors for this schedule (simplified - assuming project responsible)
            project = schedule.project
            if project and project.responsible_id:
                instructor_id = project.responsible_id
                classroom_id = schedule.classroom_id
                
                if instructor_id in instructor_classrooms:
                    if instructor_classrooms[instructor_id] != classroom_id:
                        changes += 1
                else:
                    instructor_classrooms[instructor_id] = classroom_id
                
                total_assignments += 1
        
        # Calculate score (lower changes = better)
        max_possible_changes = max(0, total_assignments - 1)
        score = 1 - (changes / max_possible_changes) if max_possible_changes > 0 else 1
        
        return {
            "score": score,
            "changes": changes,
            "total_assignments": total_assignments,
            "max_possible_changes": max_possible_changes
        }
    
    def _calculate_time_efficiency_score(self, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate time efficiency score (minimize gaps)."""
        instructor_timeslots = {}
        gaps = 0
        total_instructors = 0
        
        for schedule in schedules:
            project = schedule.project
            if project and project.responsible_id:
                instructor_id = project.responsible_id
                timeslot_id = schedule.timeslot_id
                
                if instructor_id not in instructor_timeslots:
                    instructor_timeslots[instructor_id] = []
                instructor_timeslots[instructor_id].append(timeslot_id)
        
        # Calculate gaps for each instructor
        for instructor_id, timeslots in instructor_timeslots.items():
            if len(timeslots) > 1:
                sorted_slots = sorted(timeslots)
                for i in range(1, len(sorted_slots)):
                    if sorted_slots[i] - sorted_slots[i-1] > 1:
                        gaps += 1
            total_instructors += 1
        
        # Calculate score (fewer gaps = better)
        max_possible_gaps = max(0, total_instructors * 3)  # Estimate
        score = 1 - (gaps / max_possible_gaps) if max_possible_gaps > 0 else 1
        
        return {
            "score": score,
            "gaps": gaps,
            "total_instructors": total_instructors,
            "max_possible_gaps": max_possible_gaps
        }
    
    async def _calculate_constraint_satisfaction_score(self, db: AsyncSession, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate constraint satisfaction score."""
        violations = []
        
        # Check classroom capacity constraints
        classroom_capacities = {}
        result = await db.execute(select(Classroom))
        classrooms = result.scalars().all()
        for classroom in classrooms:
            classroom_capacities[classroom.id] = classroom.capacity or 20  # Default capacity
        
        # Check for conflicts
        used_slots = {}
        for schedule in schedules:
            slot_key = (schedule.classroom_id, schedule.timeslot_id)
            if slot_key in used_slots:
                violations.append({
                    "type": "conflict",
                    "message": f"Multiple projects in classroom {schedule.classroom_id}, timeslot {schedule.timeslot_id}",
                    "schedule_id": schedule.id
                })
            used_slots[slot_key] = schedule.id
        
        # Check minimum instructor requirements
        for schedule in schedules:
            project = schedule.project
            if project:
                required_instructors = 2 if project.type == "bitirme" else 1
                # Simplified check - assuming project has responsible_id
                actual_instructors = 1 if project.responsible_id else 0
                if actual_instructors < required_instructors:
                    violations.append({
                        "type": "insufficient_instructors",
                        "message": f"Project {project.id} needs {required_instructors} instructors, has {actual_instructors}",
                        "schedule_id": schedule.id
                    })
        
        # Calculate score (fewer violations = better)
        total_violations = len(violations)
        score = max(0, 1 - (total_violations / len(schedules))) if schedules else 1
        
        return {
            "score": score,
            "violations": violations,
            "total_violations": total_violations
        }
    
    async def _calculate_gini_coefficient(self, db: AsyncSession, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate Gini coefficient for load distribution."""
        # Get instructor loads
        result = await db.execute(select(Instructor))
        instructors = result.scalars().all()
        
        loads = [instructor.total_load or 0 for instructor in instructors]
        loads = [load for load in loads if load > 0]  # Remove zero loads
        
        if len(loads) < 2:
            return {"gini": 0.0, "interpretation": "insufficient_data"}
        
        # Sort loads
        loads = sorted(loads)
        n = len(loads)
        
        # Calculate Gini coefficient
        cumsum = 0
        for i, load in enumerate(loads):
            cumsum += (i + 1) * load
        
        total_sum = sum(loads)
        gini = (2 * cumsum) / (n * total_sum) - (n + 1) / n
        
        # Interpretation
        if gini < 0.2:
            interpretation = "very_equal"
        elif gini < 0.3:
            interpretation = "equal"
        elif gini < 0.4:
            interpretation = "moderate_inequality"
        elif gini < 0.5:
            interpretation = "high_inequality"
        else:
            interpretation = "very_high_inequality"
        
        return {
            "gini": gini,
            "interpretation": interpretation,
            "loads": loads
        }
    
    def _calculate_instructor_preference_score(self, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate instructor preference satisfaction score."""
        # Simplified implementation
        satisfied_preferences = 0
        total_preferences = 0
        
        for schedule in schedules:
            project = schedule.project
            if project and project.responsible_id:
                # Check if instructor matches project preferences
                # This is a placeholder - real implementation would check actual preferences
                satisfied_preferences += 1
            total_preferences += 1
        
        score = satisfied_preferences / total_preferences if total_preferences > 0 else 1
        
        return {
            "score": score,
            "satisfied": satisfied_preferences,
            "total": total_preferences
        }
    
    def _calculate_classroom_utilization_score(self, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate classroom utilization score."""
        classroom_usage = {}
        
        for schedule in schedules:
            classroom_id = schedule.classroom_id
            classroom_usage[classroom_id] = classroom_usage.get(classroom_id, 0) + 1
        
        if not classroom_usage:
            return {"score": 0.0, "utilization": {}}
        
        # Calculate utilization variance
        utilizations = list(classroom_usage.values())
        mean_utilization = sum(utilizations) / len(utilizations)
        variance = sum((util - mean_utilization) ** 2 for util in utilizations) / len(utilizations)
        
        # Lower variance = better utilization distribution
        max_variance = mean_utilization ** 2 if mean_utilization > 0 else 1
        normalized_variance = variance / max_variance if max_variance > 0 else 0
        score = max(0, 1 - normalized_variance)
        
        return {
            "score": score,
            "mean_utilization": mean_utilization,
            "variance": variance,
            "utilization": classroom_usage
        }
    
    def _calculate_time_slot_distribution_score(self, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate time slot distribution score."""
        timeslot_usage = {}
        
        for schedule in schedules:
            timeslot_id = schedule.timeslot_id
            timeslot_usage[timeslot_id] = timeslot_usage.get(timeslot_id, 0) + 1
        
        if not timeslot_usage:
            return {"score": 0.0, "distribution": {}}
        
        # Calculate distribution variance
        usages = list(timeslot_usage.values())
        mean_usage = sum(usages) / len(usages)
        variance = sum((usage - mean_usage) ** 2 for usage in usages) / len(usages)
        
        # Lower variance = better distribution
        max_variance = mean_usage ** 2 if mean_usage > 0 else 1
        normalized_variance = variance / max_variance if max_variance > 0 else 0
        score = max(0, 1 - normalized_variance)
        
        return {
            "score": score,
            "mean_usage": mean_usage,
            "variance": variance,
            "distribution": timeslot_usage
        }
    
    def _calculate_overall_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate weighted overall score."""
        weights = {
            "load_balance": 0.25,
            "classroom_changes": 0.20,
            "time_efficiency": 0.20,
            "constraint_satisfaction": 0.20,
            "gini_coefficient": 0.10,
            "instructor_preference": 0.05
        }
        
        overall_score = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if metric in metrics:
                score = metrics[metric].get("score", 0.0)
                overall_score += score * weight
                total_weight += weight
        
        return overall_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_scores_by_project_type(self, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate scores broken down by project type."""
        bitirme_schedules = []
        ara_schedules = []
        
        for schedule in schedules:
            project = schedule.project
            if project:
                if project.type == "bitirme":
                    bitirme_schedules.append(schedule)
                else:
                    ara_schedules.append(schedule)
        
        return {
            "bitirme": {
                "count": len(bitirme_schedules),
                "classroom_changes": self._calculate_classroom_changes_score(bitirme_schedules),
                "time_efficiency": self._calculate_time_efficiency_score(bitirme_schedules)
            },
            "ara": {
                "count": len(ara_schedules),
                "classroom_changes": self._calculate_classroom_changes_score(ara_schedules),
                "time_efficiency": self._calculate_time_efficiency_score(ara_schedules)
            }
        }
    
    async def _calculate_scores_by_instructor(self, db: AsyncSession, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate scores broken down by instructor."""
        result = await db.execute(select(Instructor))
        instructors = result.scalars().all()
        
        instructor_scores = {}
        for instructor in instructors:
            instructor_schedules = [
                s for s in schedules 
                if s.project and s.project.responsible_id == instructor.id
            ]
            
            instructor_scores[instructor.id] = {
                "name": instructor.name,
                "type": instructor.type,
                "schedule_count": len(instructor_schedules),
                "load": instructor.total_load or 0
            }
        
        return instructor_scores
    
    def _calculate_scores_by_classroom(self, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate scores broken down by classroom."""
        classroom_scores = {}
        
        for schedule in schedules:
            classroom_id = schedule.classroom_id
            if classroom_id not in classroom_scores:
                classroom_scores[classroom_id] = {
                    "schedule_count": 0,
                    "projects": []
                }
            
            classroom_scores[classroom_id]["schedule_count"] += 1
            if schedule.project:
                classroom_scores[classroom_id]["projects"].append(schedule.project.id)
        
        return classroom_scores
    
    def _calculate_scores_by_timeslot(self, schedules: List[Schedule]) -> Dict[str, Any]:
        """Calculate scores broken down by timeslot."""
        timeslot_scores = {}
        
        for schedule in schedules:
            timeslot_id = schedule.timeslot_id
            if timeslot_id not in timeslot_scores:
                timeslot_scores[timeslot_id] = {
                    "schedule_count": 0,
                    "projects": []
                }
            
            timeslot_scores[timeslot_id]["schedule_count"] += 1
            if schedule.project:
                timeslot_scores[timeslot_id]["projects"].append(schedule.project.id)
        
        return timeslot_scores
    
    def _empty_scores(self) -> Dict[str, Any]:
        """Return empty scores when no schedules exist."""
        return {
            "timestamp": datetime.now().isoformat(),
            "algorithm_run_id": None,
            "total_schedules": 0,
            "metrics": {
                "load_balance": {"score": 0.0, "variance": 0.0, "mean": 0.0, "details": {}},
                "classroom_changes": {"score": 0.0, "changes": 0, "total_assignments": 0},
                "time_efficiency": {"score": 0.0, "gaps": 0, "total_instructors": 0},
                "constraint_satisfaction": {"score": 0.0, "violations": [], "total_violations": 0},
                "gini_coefficient": {"gini": 0.0, "interpretation": "no_data"},
                "instructor_preference": {"score": 0.0, "satisfied": 0, "total": 0},
                "classroom_utilization": {"score": 0.0, "utilization": {}},
                "time_slot_distribution": {"score": 0.0, "distribution": {}}
            },
            "overall_score": 0.0,
            "breakdowns": {
                "by_project_type": {"bitirme": {"count": 0}, "ara": {"count": 0}},
                "by_instructor": {},
                "by_classroom": {},
                "by_timeslot": {}
            }
        }
    
    async def generate_score_json(self, db: AsyncSession, algorithm_run_id: Optional[int] = None) -> str:
        """
        Generate score.json file with current optimization scores.
        
        Args:
            db: Database session
            algorithm_run_id: Optional algorithm run ID for tracking
            
        Returns:
            Path to generated score.json file
        """
        scores = await self.calculate_scores(db, algorithm_run_id)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"score_{timestamp}.json"
        if algorithm_run_id:
            filename = f"score_run_{algorithm_run_id}_{timestamp}.json"
        
        filepath = os.path.join(self.scores_dir, filename)
        
        # Write scores to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(scores, f, indent=2, ensure_ascii=False)
        
        # Also create/update latest score.json
        latest_filepath = os.path.join(self.scores_dir, "score.json")
        with open(latest_filepath, 'w', encoding='utf-8') as f:
            json.dump(scores, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _calculate_session_minimization_score(self, schedules: List[Schedule]) -> float:
        """
        Oturum minimizasyonu skorunu hesaplar.
        Proje açıklamasına göre: Oturum sayısının minimize edilmesi
        """
        if not schedules:
            return 0.0
        
        # Kullanılan zaman dilimi sayısı
        used_timeslots = set()
        for schedule in schedules:
            if schedule.timeslot_id:
                used_timeslots.add(schedule.timeslot_id)
        
        timeslot_count = len(used_timeslots)
        
        # Minimum oturum sayısına göre normalize et (0-100 arası)
        # İdeal durum: Tüm projeler aynı anda (minimum oturum sayısı)
        min_possible_sessions = 1
        max_possible_sessions = len(schedules)  # Her proje ayrı oturumda
        
        if timeslot_count <= min_possible_sessions:
            return 100.0
        
        # Lineer olarak 0-100 arasında normalize et
        score = max(0.0, 100.0 - ((timeslot_count - min_possible_sessions) / 
                                 (max_possible_sessions - min_possible_sessions)) * 100.0)
        
        return round(score, 2)
    
    async def _calculate_rule_compliance_score(self, db: AsyncSession, schedules: List[Schedule]) -> float:
        """
        Kural uyumu skorunu hesaplar.
        Proje açıklamasına göre: Kurallara uyum (eksik hoca/yanlış yapı olmaması)
        """
        if not schedules:
            return 0.0
        
        total_violations = 0
        total_checks = 0
        
        for schedule in schedules:
            if not schedule.project:
                continue
            
            project = schedule.project
            
            # Proje kurallarına uygunluk kontrolü
            compliance_result = project.is_rule_compliant()
            total_checks += 1
            
            if not compliance_result["compliant"]:
                total_violations += len(compliance_result["errors"])
        
        if total_checks == 0:
            return 0.0
        
        # Violation oranına göre skor hesapla
        violation_rate = total_violations / total_checks
        score = max(0.0, 100.0 - (violation_rate * 100.0))
        
        return round(score, 2)
    
    async def get_latest_scores(self) -> Optional[Dict[str, Any]]:
        """Get the latest scores from score.json."""
        latest_filepath = os.path.join(self.scores_dir, "score.json")
        
        if not os.path.exists(latest_filepath):
            return None
        
        try:
            with open(latest_filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
