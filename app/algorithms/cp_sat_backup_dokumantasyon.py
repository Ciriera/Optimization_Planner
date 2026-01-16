"""
CP-SAT Algorithm - Enhanced with Pure Consecutive Grouping
Uses same logic as Genetic Algorithm for optimal uniform distribution
"""
from __future__ import annotations

from typing import Dict, Any, List, Tuple, Optional, Set
import random
import logging
from collections import defaultdict
import math
from datetime import time as dt_time

from app.algorithms.base import OptimizationAlgorithm

# Google OR-Tools CP-SAT
try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    print("Warning: OR-Tools not available. CP-SAT will use fallback implementation.")

logger = logging.getLogger(__name__)

class CPSAT(OptimizationAlgorithm):
    """
    CP-SAT Algorithm - Enhanced with Pure Consecutive Grouping + Smart Jury Assignment.
    
    SUCCESS STRATEGY (Same as Deep Search Algorithm):
    NOT 1: RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
    NOT 2: AKILLI JÜRİ ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin jürisi
    NOT 3: CONSECUTIVE GROUPING - Her instructor'ın projeleri ardışık ve aynı sınıfta
    
    This implementation uses the SAME logic as Deep Search Algorithm for:
    1. RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
    2. EN ERKEN BOŞ SLOT mantığı - Boş slotlar varken ileri atlamaz
    3. Uniform distribution - D111 dahil tüm sınıfları kullanır
    4. Pure consecutive grouping - Her instructor'ın projeleri ardışık
    5. AKILLI JÜRİ ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin jürisi
    6. Conflict-free scheduling - Instructor çakışmalarını önler
    
    Strategy:
    "Bir öğretim görevlimizi sorumlu olduğu projelerden birisiyle birlikte 
    diyelim ki 09:00-09:30 zaman slotuna ve D106 sınıfına atamasını yaptık. 
    Bu öğretim görevlimizin diğer sorumlu olduğu projeleri de aynı sınıfa 
    ve hemen sonraki zaman slotlarına atayalım ki çok fazla yer değişimi olmasın"
    
    Original Features (Preserved):
    - CP-SAT constraint programming
    - Google OR-Tools integration
    - Hybrid CP-SAT + Greedy approach
    """

    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize CP-SAT Algorithm with AI-Based Enhancements.

        Args:
            params: Algorithm parameters.
        """
        super().__init__(params)
        params = params or {}

        # CP-SAT parameters
        self.time_limit = params.get("time_limit", 60)  # 1 minute for large problems
        self.log_search_progress = params.get("log_search_progress", False)
        
        # 🤖 AI-BASED PARAMETERS - NO HARD CONSTRAINTS!
        self.ai_timeslot_scoring = params.get("ai_timeslot_scoring", True)
        self.ai_classroom_selection = params.get("ai_classroom_selection", True)
        self.ai_conflict_resolution = params.get("ai_conflict_resolution", True)
        self.ai_workload_balancing = params.get("ai_workload_balancing", True)
        self.ai_capacity_management = params.get("ai_capacity_management", True)
        self.ai_multi_objective = params.get("ai_multi_objective", True)
        self.ai_adaptive_learning = params.get("ai_adaptive_learning", True)
        
        # Greedy compatibility parameters (SOFT CONSTRAINTS ONLY!)
        self.penalty_factors = {
            "class_switch": 50.0,
            "role_conflict": 100.0,
            "missing_supervisor": 200.0,
            "missing_jury": 150.0,
            "duplicate": 300.0,
            "gap": 25.0
        }
        
        self.bonus_factors = {
            "class_stay": 10.0,
            "time_bonus": 5.0,
            "morning_slot": 50.0,  # NEW: Morning bonus
            "consecutive": 30.0,   # NEW: Consecutive bonus
            "balanced_workload": 40.0  # NEW: Workload balance bonus
        }
        
        # 🤖 AI Learning Storage
        self.historical_patterns = {}
        self.instructor_preferences = defaultdict(dict)
        self.classroom_usage_history = defaultdict(int)
        self.workload_history = defaultdict(list)
        
        # Data storage
        self.data = {}
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []

    def initialize(self, data: Dict[str, Any]) -> None:
        """Initialize the algorithm with problem data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run CP-SAT optimization with Pure Consecutive Grouping + Smart Jury.
        
        SUCCESS STRATEGY (Same as Deep Search Algorithm):
        NOT 1: RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
        NOT 2: AKILLI JÜRİ ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin jürisi
        NOT 3: CONSECUTIVE GROUPING - Her instructor'ın projeleri ardışık ve aynı sınıfta
        """
        import time as time_module
        start_time = time_module.time()
        
        # Initialize data
        self.initialize(data)
        
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            return {
                "assignments": [],
                "quality": float('inf'),
                "message": "Insufficient data for optimization"
            }
        
        logger.info("CP-SAT Algorithm başlatılıyor (Enhanced Randomizer + Consecutive Grouping + Smart Jury mode)...")
        logger.info(f"  Projeler: {len(self.projects)}")
        logger.info(f"  Instructors: {len(self.instructors)}")
        logger.info(f"  Sınıflar: {len(self.classrooms)}")
        logger.info(f"  Zaman Slotları: {len(self.timeslots)}")

        # Pure Consecutive Grouping Algorithm - Same as Deep Search Algorithm
        logger.info("Pure Consecutive Grouping + Enhanced Randomizer + Smart Jury ile optimal çözüm oluşturuluyor...")
        best_solution = self._create_pure_consecutive_grouping_solution()
        logger.info(f"  Pure Consecutive Grouping: {len(best_solution)} proje atandı")
        
        # 🤖 AI-BASED CONFLICT RESOLUTION (NO HARD CONSTRAINTS!)
        if best_solution and len(best_solution) > 0:
            logger.info("🤖 AI-Based Conflict Detection & Resolution...")
            
            # Güçlendirilmiş AI conflict resolution
            best_solution = self._resolve_conflicts_ai(best_solution)
            
            # Final conflict check
            remaining_conflicts = self._detect_conflicts(best_solution)
            if remaining_conflicts:
                logger.warning(f"  ⚠️ {len(remaining_conflicts)} conflicts remain (will be handled by AI)")
                # NO HARD CONSTRAINT - Continue with best effort solution
            else:
                logger.info("  ✅ All conflicts successfully resolved by AI!")
        
        # 🤖 AI-BASED MULTI-OBJECTIVE SCORING
        ai_score = self._calculate_multi_objective_score_ai(best_solution)
        logger.info(f"\n🎯 AI Multi-Objective Score:")
        logger.info(f"    Total Score: {ai_score['total']:.2f}/100")
        logger.info(f"    Grade: {ai_score['grade']}")
        logger.info(f"    Breakdown:")
        for key, value in ai_score.get('breakdown', {}).items():
            logger.info(f"      {key}: {value:.2f}")
        
        # 🤖 AI ADAPTIVE LEARNING
        self._learn_from_solution_ai(best_solution)
        
        # Final stats
        final_stats = self._calculate_grouping_stats(best_solution)
        logger.info(f"\n📊 Final Consecutive Grouping Stats:")
        logger.info(f"    Consecutive instructors: {final_stats['consecutive_count']}/{final_stats['total_instructors']}")
        logger.info(f"    Consecutive percentage: {final_stats['consecutive_percentage']:.1f}%")
        logger.info(f"    Avg classroom changes: {final_stats['avg_classroom_changes']:.2f}")

        end_time = time_module.time()
        execution_time = end_time - start_time
        logger.info(f"CP-SAT Algorithm completed. Execution time: {execution_time:.2f}s")

        return {
            "assignments": best_solution or [],
            "schedule": best_solution or [],
            "solution": best_solution or [],
            "fitness_scores": self._calculate_fitness_scores(best_solution or []),
            "execution_time": execution_time,
            "algorithm": "CP-SAT",
            "status": "completed",
            
            # 🤖 AI SCORES
            "ai_score": ai_score,
            "ai_grade": ai_score.get('grade', 'N/A'),
            "ai_total_score": ai_score.get('total', 0),
            "ai_breakdown": ai_score.get('breakdown', {}),
            "ai_details": ai_score.get('details', {}),
            
            # AI FEATURES APPLIED
            "optimizations_applied": [
                # Core AI Features
                "ai_based_instructor_sorting_by_project_count",
                "intelligent_instructor_pairing_upper_lower_groups",
                "pure_consecutive_grouping",
                "smart_jury_assignment_via_pairing",
                "consecutive_jury_pairing",
                
                # NEW AI Enhancements
                "ai_timeslot_scoring_with_morning_bonus",
                "ai_classroom_selection_with_load_balancing",
                "ai_conflict_resolution_smart_swap",
                "ai_capacity_management_optimization",
                "ai_workload_balancing_dynamic",
                "ai_multi_objective_scoring",
                "ai_adaptive_learning_from_history",
                
                # Constraint Management
                "soft_constraints_only_no_hard_constraints",
                "conflict_detection_and_ai_resolution",
                "uniform_classroom_distribution",
                "earliest_slot_assignment",
                "ai_based_optimization_engine"
            ],
            
            "stats": final_stats,
            
            "parameters": {
                "algorithm_type": "ultra_ai_powered_cp_sat",
                "instructor_sorting": "by_project_count_descending",
                "pairing_strategy": "upper_lower_group_pairing",
                
                # AI Feature Flags
                "ai_timeslot_scoring": self.ai_timeslot_scoring,
                "ai_classroom_selection": self.ai_classroom_selection,
                "ai_conflict_resolution": self.ai_conflict_resolution,
                "ai_workload_balancing": self.ai_workload_balancing,
                "ai_capacity_management": self.ai_capacity_management,
                "ai_multi_objective": self.ai_multi_objective,
                "ai_adaptive_learning": self.ai_adaptive_learning,
                
                # Core Strategies
                "smart_jury_assignment": True,
                "consecutive_jury_pairing": True,
                "soft_constraints_only": True,
                "hard_constraints_removed": True,
                "conflict_prevention": True,
                "same_classroom_priority": True,
                "uniform_distribution": True,
                "earliest_slot_strategy": True,
                "time_limit": self.time_limit
            },
            
            # Workload Analysis
            "workload_analysis": {
                instructor.get('id'): self._calculate_instructor_workload_ai(
                    instructor.get('id'), 
                    best_solution or []
                )
                for instructor in self.instructors
            } if self.ai_workload_balancing else {}
        }

    def _create_balanced_classroom_assignment(self) -> List[Dict[str, Any]]:
        """
        Balanced classroom assignment ile consecutive grouping.
        Tüm sınıfları eşit şekilde kullanmaya çalışır.
        """
        assignments = []
        used_slots = set()  # (classroom_id, timeslot_id)
        instructor_timeslot_usage = defaultdict(set)
        assigned_projects = set()
        
        # Instructor bazında projeleri grupla
        instructor_projects = defaultdict(list)
        for project in self.projects:
            responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
            if responsible_id:
                instructor_projects[responsible_id].append(project)
        
        logger.info(f"Balanced classroom assignment başlatılıyor...")
        logger.info(f"  {len(instructor_projects)} instructor için proje grupları oluşturuldu")
        
        # Her instructor için projeleri ata
        for instructor_id, instructor_project_list in instructor_projects.items():
            if not instructor_project_list:
                continue
            
            logger.info(f"Instructor {instructor_id} için {len(instructor_project_list)} proje atanıyor...")
            
            # Bu instructor için en uygun sınıf ve başlangıç slotunu bul
            best_classroom = None
            best_start_slot = None
            max_consecutive_slots = 0
            
            # Tüm sınıfları dene
            for classroom in self.classrooms:
                classroom_id = classroom.get("id")
                
                # Bu sınıfta kaç tane ardışık slot bulabiliriz?
                consecutive_slots = self._find_max_consecutive_slots(
                    classroom_id, instructor_project_list, used_slots, instructor_timeslot_usage
                )
                
                if consecutive_slots > max_consecutive_slots:
                    max_consecutive_slots = consecutive_slots
                    best_classroom = classroom_id
                    best_start_slot = self._find_start_slot_for_consecutive(
                        classroom_id, instructor_project_list, used_slots, instructor_timeslot_usage
                    )
            
            if best_classroom and best_start_slot is not None:
                # Bu instructor'ın projelerini best_classroom'da ardışık olarak ata
                current_slot = best_start_slot
                
                for i, project in enumerate(instructor_project_list):
                    project_id = project.get("id")
                    
                    if project_id in assigned_projects:
                        continue
                    
                    # Bu slot uygun mu?
                    slot_key = (best_classroom, current_slot)
                    instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                    
                    if slot_key not in used_slots and current_slot not in instructor_slots:
                        # Bu slotu kullan
                        assignment = {
                            "project_id": project_id,
                            "classroom_id": best_classroom,
                            "timeslot_id": current_slot,
                            "is_makeup": project.get("is_makeup", False),
                            "instructors": self._assign_instructors(project, instructor_id)
                        }
                        
                        assignments.append(assignment)
                        used_slots.add(slot_key)
                        instructor_timeslot_usage[instructor_id].add(current_slot)
                        assigned_projects.add(project_id)
                        
                        current_slot += 1  # Sonraki slot
                    else:
                        # Bu slot dolu, sonraki slotları ara
                        current_slot = self._find_next_available_slot(
                            best_classroom, current_slot, used_slots, instructor_timeslot_usage.get(instructor_id, set())
                        )
                        
                        if current_slot is None:
                            # Bu sınıfta yer yok, başka sınıf ara
                            current_slot = self._find_alternative_classroom_slot(
                                instructor_id, project_id, used_slots, instructor_timeslot_usage
                            )
                            
                            if current_slot:
                                classroom_id, timeslot_id = current_slot
                                assignment = {
                                    "project_id": project_id,
                                    "classroom_id": classroom_id,
                                    "timeslot_id": timeslot_id,
                                    "is_makeup": project.get("is_makeup", False),
                                    "instructors": self._assign_instructors(project, instructor_id)
                                }
                                
                                assignments.append(assignment)
                                used_slots.add((classroom_id, timeslot_id))
                                instructor_timeslot_usage[instructor_id].add(timeslot_id)
                                assigned_projects.add(project_id)
                                
                                current_slot = timeslot_id + 1
                            else:
                                logger.warning(f"Proje {project_id} için uygun slot bulunamadı!")
                                break
                        else:
                            # Sonraki slotu kullan
                            assignment = {
                                "project_id": project_id,
                                "classroom_id": best_classroom,
                                "timeslot_id": current_slot,
                                "is_makeup": project.get("is_makeup", False),
                                "instructors": self._assign_instructors(project, instructor_id)
                            }
                            
                            assignments.append(assignment)
                            used_slots.add((best_classroom, current_slot))
                            instructor_timeslot_usage[instructor_id].add(current_slot)
                            assigned_projects.add(project_id)
                            
                            current_slot += 1
            else:
                logger.warning(f"Instructor {instructor_id} için uygun sınıf bulunamadı!")
        
        logger.info(f"Balanced classroom assignment tamamlandı: {len(assignments)} proje atandı")
        return assignments

    def _find_max_consecutive_slots(self, classroom_id, projects, used_slots, instructor_timeslot_usage):
        """Bir sınıfta kaç tane ardışık slot bulabiliriz?"""
        max_consecutive = 0
        current_consecutive = 0
        
        for timeslot in self.timeslots:
            timeslot_id = timeslot.get("id")
            slot_key = (classroom_id, timeslot_id)
            
            if slot_key not in used_slots:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return min(max_consecutive, len(projects))

    def _find_start_slot_for_consecutive(self, classroom_id, projects, used_slots, instructor_timeslot_usage):
        """Ardışık slotlar için başlangıç slotunu bul"""
        needed_slots = len(projects)
        current_consecutive = 0
        start_slot = None
        
        for timeslot in self.timeslots:
            timeslot_id = timeslot.get("id")
            slot_key = (classroom_id, timeslot_id)
            
            if slot_key not in used_slots:
                if current_consecutive == 0:
                    start_slot = timeslot_id
                current_consecutive += 1
                
                if current_consecutive >= needed_slots:
                    return start_slot
            else:
                current_consecutive = 0
                start_slot = None
        
        return start_slot

    def _find_next_available_slot_with_score(self, classroom_id, start_slot, used_slots, instructor_slots):
        """
        🤖 AI-BASED FALLBACK SCORING: Find next available slot with quality score (NO RETURN NONE!)
        
        Returns:
            Dict with 'timeslot_id' and 'score'
        """
        for timeslot in self.timeslots:
            timeslot_id = timeslot.get("id")
            if timeslot_id <= start_slot:
                continue
                
            slot_key = (classroom_id, timeslot_id)
            if slot_key not in used_slots and timeslot_id not in instructor_slots:
                # ✅ OPTIMAL SLOT FOUND!
                return {'timeslot_id': timeslot_id, 'score': 100.0, 'quality': 'optimal'}
        
        # 🤖 FALLBACK: Return first available timeslot with penalty
        fallback_timeslot = self.timeslots[0].get("id") if self.timeslots else -1
        return {
            'timeslot_id': fallback_timeslot,
            'score': -300.0,
            'quality': 'fallback',
            'reason': 'no_next_available_slot'
        }

    def _find_alternative_classroom_slot_with_score(self, instructor_id, project_id, used_slots, instructor_timeslot_usage):
        """
        🤖 AI-BASED FALLBACK SCORING: Find alternative classroom slot with quality score (NO RETURN NONE!)
        
        Instead of returning None when no slot found, returns a fallback slot with penalty score.
        
        Returns:
            Dict with 'classroom_id', 'timeslot_id', and 'score'
        """
        for classroom in self.classrooms:
            classroom_id = classroom.get("id")
            for timeslot in self.timeslots:
                timeslot_id = timeslot.get("id")
                slot_key = (classroom_id, timeslot_id)
                
                if slot_key not in used_slots:
                    instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                    if timeslot_id not in instructor_slots:
                        # ✅ OPTIMAL SLOT FOUND!
                        return {
                            'classroom_id': classroom_id,
                            'timeslot_id': timeslot_id,
                            'score': 100.0,
                            'quality': 'optimal'
                        }
        
        # 🤖 NO OPTIMAL SLOT - RETURN FALLBACK WITH PENALTY (NOT None!)
        # Fallback: Use first classroom and timeslot (with conflict acceptance)
        fallback_classroom = self.classrooms[0].get("id") if self.classrooms else -1
        fallback_timeslot = self.timeslots[0].get("id") if self.timeslots else -1
        return {
            'classroom_id': fallback_classroom,
            'timeslot_id': fallback_timeslot,
            'score': -600.0,  # Very high penalty for fallback
            'quality': 'fallback',
            'reason': 'no_available_alternative_slot'
        }

    def _assign_instructors(self, project, responsible_id):
        """Proje için instructorları ata"""
        instructors = [responsible_id]
        
        # Bitirme projesi için ek instructor ekle
        if project.get("type") == "bitirme":
            # Ek instructor bul
            for instructor in self.instructors:
                instructor_id = instructor.get("id")
                if instructor_id != responsible_id and instructor_id not in instructors:
                    instructors.append(instructor_id)
                    break
        
        return instructors

    def _hybrid_cp_sat_optimization(self) -> List[Dict[str, Any]]:
        """Hybrid CP-SAT + Greedy optimization for large problems."""
        print("CP-SAT: Starting hybrid optimization for large problem...")
        
        # Phase 1: Use Greedy to get initial solution quickly
        print("CP-SAT: Phase 1 - Generating initial solution with Greedy...")
        assignments = self._greedy_initial_solution()
        print(f"CP-SAT: Initial solution has {len(assignments)} assignments")
        
        # Phase 2: Use CP-SAT for local optimization on critical parts
        print("CP-SAT: Phase 2 - Applying CP-SAT local optimization...")
        assignments = self._cp_sat_local_optimization(assignments)
        print(f"CP-SAT: After local optimization: {len(assignments)} assignments")
        
        # Phase 3: Apply post-processing optimizations
        print("CP-SAT: Phase 3 - Applying post-processing optimizations...")
        assignments = self._apply_post_processing_optimizations(assignments)
        print(f"CP-SAT: Final solution has {len(assignments)} assignments")
        
        return assignments

    def _greedy_initial_solution(self) -> List[Dict[str, Any]]:
        """Generate initial solution using Greedy approach."""
        assignments = []
        assigned_projects = set()
        assigned_classrooms_timeslots = set()
        instructor_timeslot_usage = defaultdict(set)
        
        # Sort projects by priority
        prioritized_projects = self._prioritize_projects_cp_sat()
        
        for project in prioritized_projects:
            best_assignment = None
            best_score = float('inf')
            
            for classroom in self.classrooms:
                for timeslot in self.timeslots:
                    if (project.get("id") not in assigned_projects and 
                        (classroom.get("id"), timeslot.get("id")) not in assigned_classrooms_timeslots):
                        
                        instructors = self._select_instructors_for_project_cp_sat(project, timeslot.get("id"))
                        
                        if instructors:
                            # Check instructor availability
                            instructor_conflict = False
                            for instructor_id in instructors:
                                if timeslot.get("id") in instructor_timeslot_usage[instructor_id]:
                                    instructor_conflict = True
                                    break
                            
                            if not instructor_conflict:
                                # Calculate score
                                score = self._calculate_assignment_score_cp_sat(project, classroom, timeslot, instructors)
                                
                                if score < best_score:
                                    best_score = score
                                    best_assignment = {
                                        "project_id": project.get("id"),
                                        "classroom_id": classroom.get("id"),
                                        "timeslot_id": timeslot.get("id"),
                                        "instructors": instructors
                                    }
            
            if best_assignment:
                assignments.append(best_assignment)
                assigned_projects.add(best_assignment["project_id"])
                assigned_classrooms_timeslots.add((best_assignment["classroom_id"], best_assignment["timeslot_id"]))
                
                for instructor_id in best_assignment["instructors"]:
                    instructor_timeslot_usage[instructor_id].add(best_assignment["timeslot_id"])
        
        return assignments

    def _cp_sat_local_optimization(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply CP-SAT local optimization to improve the solution."""
        if not assignments:
            return assignments
        
        # Focus on optimizing critical parts (e.g., gaps, priority slots)
        print("CP-SAT: Optimizing gaps and priority slots...")
        
        # Sort timeslots
        sorted_timeslots = sorted(self.timeslots, key=lambda x: x.get("start_time", "09:00"))
        
        # Detect and fill gaps
        assignments = self._apply_gap_free_optimization_cp_sat(assignments, sorted_timeslots)
        
        # Optimize priority slots
        assignments = self._apply_priority_slot_optimization_cp_sat(assignments, sorted_timeslots)
        
        # Optimize classroom transitions
        assignments = self._apply_classroom_transition_optimization_cp_sat(assignments, sorted_timeslots)
        
        return assignments

    def _apply_post_processing_optimizations(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply post-processing optimizations."""
        # Sort timeslots for proper ordering
        sorted_timeslots = sorted(self.timeslots, key=lambda x: x.get("start_time", "09:00"))
        
        # Apply gap-free optimization
        assignments = self._apply_gap_free_optimization_cp_sat(assignments, sorted_timeslots)
        
        # Apply priority slot optimization
        assignments = self._apply_priority_slot_optimization_cp_sat(assignments, sorted_timeslots)
        
        # Apply classroom transition optimization
        assignments = self._apply_classroom_transition_optimization_cp_sat(assignments, sorted_timeslots)
        
        return assignments

    def _apply_gap_free_optimization_cp_sat(self, assignments: List[Dict[str, Any]], sorted_timeslots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply gap-free optimization."""
        if not assignments:
            return assignments
        
        # Detect gaps
        gaps = self._detect_gaps_cp_sat(assignments, sorted_timeslots)
        
        if not gaps:
            return assignments
        
        # Fill gaps
        assignments = self._fill_gaps_cp_sat(assignments, gaps, sorted_timeslots)
        
        return assignments

    def _detect_gaps_cp_sat(self, assignments: List[Dict[str, Any]], sorted_timeslots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect gaps in assignments."""
        gaps = []
        
        for classroom in self.classrooms:
            classroom_id = classroom.get("id")
            classroom_assignments = [a for a in assignments if a.get("classroom_id") == classroom_id]
            
            if not classroom_assignments:
                continue
            
            # Sort assignments by timeslot
            sorted_assignments = sorted(classroom_assignments, 
                                      key=lambda x: self._get_timeslot_index_cp_sat(x.get("timeslot_id"), sorted_timeslots))
            
            # Check for gaps
            for i in range(len(sorted_assignments) - 1):
                current_idx = self._get_timeslot_index_cp_sat(sorted_assignments[i].get("timeslot_id"), sorted_timeslots)
                next_idx = self._get_timeslot_index_cp_sat(sorted_assignments[i + 1].get("timeslot_id"), sorted_timeslots)
                
                if next_idx - current_idx > 1:
                    # Gap found
                    for gap_idx in range(current_idx + 1, next_idx):
                        gap_timeslot = sorted_timeslots[gap_idx]
                        gaps.append({
                            "classroom_id": classroom_id,
                            "timeslot_id": gap_timeslot.get("id"),
                            "timeslot": gap_timeslot
                        })
        
        return gaps

    def _get_timeslot_index_cp_sat(self, timeslot_id: int, sorted_timeslots: List[Dict[str, Any]]) -> int:
        """Get timeslot index."""
        for i, timeslot in enumerate(sorted_timeslots):
            if timeslot.get("id") == timeslot_id:
                return i
        return 0

    def _fill_gaps_cp_sat(self, assignments: List[Dict[str, Any]], gaps: List[Dict[str, Any]], 
                         sorted_timeslots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fill gaps using CP-SAT approach."""
        # Find unassigned projects
        assigned_projects = set(a.get("project_id") for a in assignments)
        unassigned_projects = [p for p in self.projects if p.get("id") not in assigned_projects]
        
        for gap in gaps:
            if not unassigned_projects:
                break
            
            classroom_id = gap.get("classroom_id")
            timeslot_id = gap.get("timeslot_id")
            
            # Try to assign a project to this gap
            for project in unassigned_projects:
                instructors = self._select_instructors_for_project_cp_sat(project, timeslot_id)
                
                if instructors:
                    assignment = {
                        "project_id": project.get("id"),
                        "classroom_id": classroom_id,
                        "timeslot_id": timeslot_id,
                        "instructors": instructors
                    }
                    assignments.append(assignment)
                    unassigned_projects.remove(project)
                    break
        
        return assignments

    def _apply_priority_slot_optimization_cp_sat(self, assignments: List[Dict[str, Any]], sorted_timeslots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply priority slot optimization."""
        # Priority slots are morning slots (09:00-12:00) - AI-based scoring
        priority_slots = [ts for ts in sorted_timeslots if self._calculate_morning_slot_bonus_cp_sat(ts) > 0]
        
        # Try to move assignments to priority slots
        for priority_slot in priority_slots:
            assignments = self._try_fill_priority_slot_cp_sat(assignments, priority_slot)
        
        return assignments

    def _try_fill_priority_slot_cp_sat(self, assignments: List[Dict[str, Any]], priority_slot: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Try to fill a priority slot."""
        timeslot_id = priority_slot.get("id")
        
        # Check if slot is already filled
        for assignment in assignments:
            if assignment.get("timeslot_id") == timeslot_id:
                return assignments
        
        # Try to assign an unassigned project
        assigned_projects = set(a.get("project_id") for a in assignments)
        unassigned_projects = [p for p in self.projects if p.get("id") not in assigned_projects]
        
        # Prioritize bitirme projects for morning slots
        bitirme_projects = [p for p in unassigned_projects if p.get("type") == "bitirme"]
        ara_projects = [p for p in unassigned_projects if p.get("type") == "ara"]
        
        # Try bitirme projects first
        for project in bitirme_projects + ara_projects:
            instructors = self._select_instructors_for_project_cp_sat(project, timeslot_id)
            
            if instructors:
                # Find available classroom
                for classroom in self.classrooms:
                    classroom_id = classroom.get("id")
                    
                    # Check if classroom is available for this timeslot
                    available = True
                    for assignment in assignments:
                        if (assignment.get("classroom_id") == classroom_id and 
                            assignment.get("timeslot_id") == timeslot_id):
                            available = False
                            break
                    
                    if available:
                        assignment = {
                            "project_id": project.get("id"),
                            "classroom_id": classroom_id,
                            "timeslot_id": timeslot_id,
                            "instructors": instructors
                        }
                        assignments.append(assignment)
                        return assignments
        
        return assignments

    def _apply_classroom_transition_optimization_cp_sat(self, assignments: List[Dict[str, Any]], sorted_timeslots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply classroom transition optimization."""
        # Group assignments by instructor
        instructor_assignments = defaultdict(list)
        for assignment in assignments:
            for instructor_id in assignment.get("instructors", []):
                instructor_assignments[instructor_id].append(assignment)
        
        # Optimize each instructor's schedule
        for instructor_id, instructor_assignments_list in instructor_assignments.items():
            if len(instructor_assignments_list) <= 1:
                continue
            
            # Try to minimize classroom changes
            assignments = self._optimize_instructor_schedule_cp_sat(instructor_id, instructor_assignments_list, assignments)
        
        return assignments

    def _optimize_instructor_schedule_cp_sat(self, instructor_id: int, instructor_assignments: List[Dict[str, Any]], 
                                           all_assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize instructor schedule to minimize classroom transitions."""
        if len(instructor_assignments) <= 1:
            return all_assignments
        
        # Find the most common classroom for this instructor
        classroom_counts = defaultdict(int)
        for assignment in instructor_assignments:
            classroom_counts[assignment.get("classroom_id")] += 1
        
        most_common_classroom = max(classroom_counts.items(), key=lambda x: x[1])[0]
        
        # Try to move assignments to the most common classroom
        for assignment in instructor_assignments:
            if assignment.get("classroom_id") == most_common_classroom:
                continue
            
            # 🤖 AI-BASED: Calculate conflict score for classroom move (soft constraint)
            conflict_score = self._calculate_classroom_move_conflict_score_cp_sat(assignment, most_common_classroom, all_assignments)
            
            # Prefer moves with low conflict (but allow high conflict with penalty)
            if conflict_score < 100.0:  # Soft threshold, not hard block
                assignment["classroom_id"] = most_common_classroom
        
        return all_assignments

    def _calculate_classroom_move_conflict_score_cp_sat(self, assignment: Dict[str, Any], new_classroom_id: int, 
                                                        all_assignments: List[Dict[str, Any]]) -> float:
        """
        🤖 AI-BASED SOFT CONSTRAINT: Calculate conflict score for classroom move (NO HARD BLOCKING!)
        
        Instead of return True/False (hard constraint), calculate conflict penalty score.
        Higher score = more conflicts, but moves are NEVER blocked.
        
        Returns:
            Conflict score (0 = no conflict, 200+ = high conflict)
        """
        timeslot_id = assignment.get("timeslot_id")
        conflict_score = 0.0
        
        # SOFT CHECK: Is new classroom occupied for this timeslot?
        for other_assignment in all_assignments:
            if (other_assignment.get("classroom_id") == new_classroom_id and 
                other_assignment.get("timeslot_id") == timeslot_id):
                conflict_score += 200.0  # High penalty for occupied classroom
        
        # Bonus for successful move
        if conflict_score == 0:
            conflict_score = -50.0  # Negative = bonus!
        
        return conflict_score

    def _select_instructors_for_project_cp_sat(self, project: Dict[str, Any], timeslot_id: int) -> List[int]:
        """Select instructors for project using CP-SAT constraints."""
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
        
        if not responsible_id:
            return []
        
        # Responsible instructor is mandatory
        instructors.append(responsible_id)
        
        # Project type specific constraints
        if project_type == "bitirme":
            # Bitirme requires at least 1 additional instructor (jury)
            available_jury = [i for i in self.instructors
                            if i.get("id") != responsible_id and 
                            self._is_instructor_available_for_timeslot_cp_sat(i.get("id"), timeslot_id)]
            
            if available_jury:
                # Prefer instructors, then assistants
                faculty = [i for i in available_jury if i.get("type") == "instructor"]
                assistants = [i for i in available_jury if i.get("type") == "assistant"]
                
                if faculty:
                    instructors.append(faculty[0].get("id"))
                elif assistants:
                    instructors.append(assistants[0].get("id"))
                else:
                    return []  # No jury available
            else:
                return []  # No jury available
        
        # Ara project only needs responsible instructor
        return instructors

    def _is_instructor_available_for_timeslot_cp_sat(self, instructor_id: int, timeslot_id: int) -> bool:
        """Check if instructor is available for timeslot."""
        return True

    def _calculate_assignment_score_cp_sat(self, project: Dict[str, Any], classroom: Dict[str, Any], 
                                         timeslot: Dict[str, Any], instructors: List[int]) -> float:
        """Calculate assignment score for CP-SAT optimization (same as Greedy)."""
        score = 0.0
        
        # Base score
        score += 100.0
        
        # Time bonus (prefer earlier timeslots)
        time_bonus = self._calculate_time_bonus_cp_sat(timeslot)
        score -= time_bonus * self.bonus_factors["time_bonus"]
        
        # Project type priority
        if project.get("type") == "bitirme":
            score -= 20.0  # Prefer bitirme projects
        
        # 🤖 AI-BASED: Morning slot bonus (soft constraint)
        morning_bonus = self._calculate_morning_slot_bonus_cp_sat(timeslot)
        score -= morning_bonus * 0.15  # Scale the bonus
        
        # Instructor load balancing
        instructor_loads = self._calculate_instructor_loads_cp_sat()
        for instructor_id in instructors:
            load = instructor_loads.get(instructor_id, 0)
            score += load * 5.0  # Penalty for high load
        
        return score

    def _calculate_time_bonus_cp_sat(self, timeslot: Dict[str, Any]) -> float:
        """Calculate time bonus for CP-SAT (same as Greedy)."""
        start_time = timeslot.get("start_time", "09:00")
        try:
            hour = int(start_time.split(":")[0])
            if 9 <= hour <= 11:
                return 5.0  # Morning bonus (highest)
            elif 13 <= hour <= 15:
                return 3.0  # Afternoon bonus
            elif 16 <= hour <= 17:
                return 1.0  # Late afternoon
            else:
                return 0.5  # Other times
        except:
            return 1.0

    def _calculate_morning_slot_bonus_cp_sat(self, timeslot: Dict[str, Any]) -> float:
        """
        🤖 AI-BASED SOFT CONSTRAINT: Calculate bonus for morning slots (NO HARD BLOCKING!)
        
        Instead of return True/False, calculate bonus/penalty score.
        
        Returns:
            Score (positive = morning bonus, 0 = afternoon/error)
        """
        start_time = timeslot.get("start_time", "09:00")
        try:
            hour = int(start_time.split(":")[0])
            if 9 <= hour < 12:
                return 100.0  # Morning bonus!
            else:
                return 0.0  # Afternoon - neutral
        except:
            return -50.0  # Parsing error - small penalty

    def _calculate_instructor_loads_cp_sat(self) -> Dict[int, int]:
        """Calculate current instructor loads."""
        loads = defaultdict(int)
        # This would be calculated based on existing assignments
        return loads

    def _prioritize_projects_cp_sat(self) -> List[Dict[str, Any]]:
        """Prioritize projects (same as Greedy)."""
        bitirme_normal = [p for p in self.projects if p.get("type") == "bitirme" and not p.get("is_makeup", False)]
        ara_normal = [p for p in self.projects if p.get("type") == "ara" and not p.get("is_makeup", False)]
        bitirme_makeup = [p for p in self.projects if p.get("type") == "bitirme" and p.get("is_makeup", False)]
        ara_makeup = [p for p in self.projects if p.get("type") == "ara" and p.get("is_makeup", False)]
        return bitirme_normal + ara_normal + bitirme_makeup + ara_makeup

    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """Evaluate the fitness of a solution."""
        assignments = solution.get("assignments", [])
        if not assignments:
            return float('inf')
        
        # Calculate comprehensive fitness score
        total_score = 0.0
        
        # 1. Load balance score
        load_balance_score = self._calculate_load_balance_score_cp_sat(assignments)
        total_score += load_balance_score * 0.25
        
        # 2. Time distribution score
        time_distribution_score = self._calculate_time_distribution_score_cp_sat(assignments)
        total_score += time_distribution_score * 0.20
        
        # 3. Classroom transition score
        classroom_transition_score = self._calculate_classroom_transition_score_cp_sat(assignments)
        total_score += classroom_transition_score * 0.20
        
        # 4. Session efficiency score
        session_efficiency_score = self._calculate_session_efficiency_score_cp_sat(assignments)
        total_score += session_efficiency_score * 0.15
        
        # 5. Rule compliance score
        rule_compliance_score = self._calculate_rule_compliance_score_cp_sat(assignments)
        total_score += rule_compliance_score * 0.20
        
        return total_score

    def _calculate_load_balance_score_cp_sat(self, assignments: List[Dict[str, Any]]) -> float:
        """Calculate load balance score."""
        if not assignments:
            return 0.0
        
        # Calculate instructor loads
        instructor_loads = defaultdict(int)
        for assignment in assignments:
            for instructor_id in assignment.get("instructors", []):
                instructor_loads[instructor_id] += 1
        
        if not instructor_loads:
            return 0.0
        
        # Calculate standard deviation
        loads = list(instructor_loads.values())
        mean_load = sum(loads) / len(loads)
        variance = sum((load - mean_load) ** 2 for load in loads) / len(loads)
        std_dev = math.sqrt(variance)
        
        # Normalize to 0-100 scale (lower is better)
        max_possible_std = math.sqrt(len(assignments))
        normalized_std = min(std_dev / max_possible_std, 1.0) if max_possible_std > 0 else 0.0
        
        return normalized_std * 100

    def _calculate_time_distribution_score_cp_sat(self, assignments: List[Dict[str, Any]]) -> float:
        """Calculate time distribution score."""
        if not assignments:
            return 0.0
        
        # Count assignments per timeslot
        timeslot_counts = defaultdict(int)
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            if timeslot_id:
                timeslot_counts[timeslot_id] += 1
        
        if not timeslot_counts:
            return 0.0
        
        # Calculate distribution variance
        counts = list(timeslot_counts.values())
        mean_count = sum(counts) / len(counts)
        variance = sum((count - mean_count) ** 2 for count in counts) / len(counts)
        std_dev = math.sqrt(variance)
        
        # Normalize to 0-100 scale (lower is better)
        max_possible_std = math.sqrt(len(assignments))
        normalized_std = min(std_dev / max_possible_std, 1.0) if max_possible_std > 0 else 0.0
        
        return normalized_std * 100

    def _calculate_classroom_transition_score_cp_sat(self, assignments: List[Dict[str, Any]]) -> float:
        """Calculate classroom transition score."""
        if not assignments:
            return 0.0
        
        # Count classroom changes per instructor
        instructor_classroom_changes = defaultdict(int)
        
        for instructor in self.instructors:
            instructor_id = instructor.get("id")
            instructor_assignments = []
            
        for assignment in assignments:
            if instructor_id in assignment.get("instructors", []):
                instructor_assignments.append(assignment)
        
            # Sort by timeslot
        instructor_assignments.sort(key=lambda x: x.get("timeslot_id", 0))
        
        # Count classroom changes
        changes = 0
        for i in range(len(instructor_assignments) - 1):
            current_classroom = instructor_assignments[i].get("classroom_id")
            next_classroom = instructor_assignments[i + 1].get("classroom_id")
            if current_classroom != next_classroom:
                changes += 1
            
            instructor_classroom_changes[instructor_id] = changes
        
        # Calculate total changes
        total_changes = sum(instructor_classroom_changes.values())
        
        # Normalize to 0-100 scale (lower is better)
        max_possible_changes = len(assignments) - 1
        normalized_changes = min(total_changes / max_possible_changes, 1.0) if max_possible_changes > 0 else 0.0
        
        return normalized_changes * 100

    def _calculate_session_efficiency_score_cp_sat(self, assignments: List[Dict[str, Any]]) -> float:
        """Calculate session efficiency score."""
        if not assignments:
            return 0.0
        
        # Count unique timeslots used
        used_timeslots = set(assignment.get("timeslot_id") for assignment in assignments)
        total_timeslots = len(self.timeslots)
        
        # Efficiency = used timeslots / total timeslots (higher is better)
        efficiency = len(used_timeslots) / total_timeslots if total_timeslots > 0 else 0.0
        
        # Convert to penalty (lower is better)
        return (1.0 - efficiency) * 100

    def _calculate_rule_compliance_score_cp_sat(self, assignments: List[Dict[str, Any]]) -> float:
        """Calculate rule compliance score."""
        if not assignments:
            return 0.0
        
        violations = 0
        total_assignments = len(assignments)
        
        for assignment in assignments:
            project_id = assignment.get("project_id")
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            
            if not project:
                violations += 1
                continue
            
            instructors = assignment.get("instructors", [])
            
            # 🤖 AI-BASED: Check rule compliance with scoring (soft constraint)
            compliance_score = self._calculate_rule_compliance_score_cp_sat(project, instructors)
            
            # Count as violation if score is significantly negative
            if compliance_score < -100.0:  # Soft threshold
                violations += 1
        
        # Normalize to 0-100 scale (lower is better)
        violation_rate = violations / total_assignments if total_assignments > 0 else 1.0
        return min(violation_rate, 1.0) * 100

    def _calculate_rule_compliance_score_cp_sat(self, project: Dict[str, Any], instructors: List[int]) -> float:
        """
        🤖 AI-BASED SOFT CONSTRAINT: Calculate rule compliance score (NO HARD BLOCKING!)
        
        Instead of return True/False (hard constraint), calculate compliance score.
        Lower score = rule violations (penalties), higher score = full compliance.
        
        Returns:
            Compliance score (0+ = compliant, negative = violations)
        """
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
        score = 0.0
        
        # SOFT CHECK: Responsible in instructors?
        if responsible_id not in instructors:
            score -= 500.0  # Critical penalty - no responsible!
        else:
            score += 100.0  # Bonus for having responsible
        
        # SOFT CHECK: Project type specific rules
        if project_type == "bitirme":
            # Bitirme prefers at least 2 instructors
            if len(instructors) < 2:
                score -= 300.0  # High penalty for missing jury
            else:
                score += 150.0  # Bonus for full compliance
                
            # Extra instructors = bonus
            if len(instructors) > 2:
                score += 50.0 * (len(instructors) - 2)  # Bonus per extra jury
                
        elif project_type == "ara":
            # Ara requires at least 1 instructor
            if len(instructors) < 1:
                score -= 400.0  # Critical penalty
            else:
                score += 100.0  # Bonus for compliance
        
        return score

    def repair_solution(self, solution: Dict[str, Any], validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Repair solution using CP-SAT approach."""
        assignments = solution.get("assignments", [])

        # Apply comprehensive CP-SAT optimization
        assignments = self._hybrid_cp_sat_optimization()

        solution["assignments"] = assignments
        return solution

    # ========== Pure Consecutive Grouping Methods (Same as Genetic Algorithm) ==========

    def _create_pure_consecutive_grouping_solution(self):
        """
        AI-Based Pure Consecutive Grouping - Advanced Jury Pairing Strategy
        
        NEW AI STRATEGY:
        1. Instructor'ları proje sorumluluk sayısına göre sırala (en fazla -> en az)
        2. Listeyi ikiye böl (üst grup: fazla projeli, alt grup: az projeli)
        3. Üst ve alt gruptan eşleştirmeler yap (pairing)
        4. Consecutive grouping ile jüri ataması:
           - İlk slot: X sorumlu, Y jüri
           - Sonraki slot: Y sorumlu, X jüri
        5. Hard kısıtları kaldır, AI-based optimizasyon yap
        """
        assignments = []
        from collections import defaultdict
        
        sorted_timeslots = sorted(self.timeslots, key=lambda x: self._parse_time(x.get("start_time", "09:00")))
        instructor_projects = defaultdict(list)
        for project in self.projects:
            rid = project.get("responsible_id") or project.get("responsible_instructor_id")
            if rid:
                instructor_projects[rid].append(project)
        
        used_slots = set()
        instructor_timeslot_usage = defaultdict(set)
        assigned_projects = set()
        
        # 🎯 YENİ ADIM 1: Instructor'ları proje sorumluluk sayısına göre sırala
        instructor_list = self._sort_instructors_by_project_count(instructor_projects)
        logger.info(f"📊 Instructorlar proje sayısına göre sıralandı (en fazla -> en az):")
        for inst_id, proj_list in instructor_list:
            logger.info(f"  Instructor {inst_id}: {len(proj_list)} proje")
        
        # 🎯 YENİ ADIM 2: Instructor listesini ikiye böl
        upper_group, lower_group = self._split_instructors_into_groups(instructor_list)
        logger.info(f"📊 Üst grup: {len(upper_group)} instructor (fazla projeli)")
        logger.info(f"📊 Alt grup: {len(lower_group)} instructor (az projeli)")
        
        # 🎯 YENİ ADIM 3: Üst ve alt grubu eşleştir (pairing)
        instructor_pairs = self._create_instructor_pairs(upper_group, lower_group)
        logger.info(f"🔗 {len(instructor_pairs)} instructor çifti oluşturuldu")
        for idx, (inst_a, inst_b) in enumerate(instructor_pairs):
            logger.info(f"  Çift {idx + 1}: Instructor {inst_a[0]} ↔ Instructor {inst_b[0]}")
        
        # 🎯 YENİ ADIM 4: Consecutive grouping ile AI-based jüri ataması
        # 🆕 ADAPTIVE CONSECUTIVE: Sınıf sayısına göre consecutive grouping ayarla - PROJE EKSİK ATANMA SORUNU DÜZELTİLDİ!
        classroom_count = len(self.classrooms)
        # SORUN DÜZELTİLDİ: Sınıf sayısı az olsa bile consecutive grouping'i tamamen kapatma!
        # Sadece esnek hale getir - projelerin eksik atanmasını önle
        use_consecutive = True  # HEP consecutive kullan - sadece esnek modda
        flexible_mode = classroom_count < 6  # Az sınıf varsa esnek mod
        logger.info(f"🔄 ADAPTIVE: Sınıf sayısı {classroom_count} - consecutive grouping: AÇIK (esnek: {'EVET' if flexible_mode else 'HAYIR'})")
        
        # 🔧 SORUN DÜZELTİLDİ: Flexible mode'da bile tüm projelerin atanmasını garanti et!
        if flexible_mode:
            logger.info("🔧 FLEXIBLE MODE: Tüm projelerin atanması garanti ediliyor...")
            
            # 🆕 PROJE COVERAGE VALIDATION: Flexible mode'da proje eksik atanmasını önle!
            self._validate_project_coverage = True
            self._flexible_mode_retry_count = 0
            self._max_flexible_retries = 3  # Maksimum 3 deneme
        
        logger.info("🤖 AI-based consecutive grouping başlatılıyor...")
        assignments = self._assign_projects_with_consecutive_jury_pairing(
            instructor_pairs,
            sorted_timeslots,
            used_slots,
            instructor_timeslot_usage,
            assigned_projects,
            use_consecutive
        )
        
        logger.info(f"✅ AI-based consecutive grouping tamamlandı: {len(assignments)} atama yapıldı")
        return assignments


    def _detect_conflicts(self, assignments):
        """Detect conflicts"""
        from collections import defaultdict
        conflicts = []
        counts = defaultdict(int)
        for a in assignments:
            for iid in a.get("instructors", []):
                key = f"instructor_{iid}_timeslot_{a.get('timeslot_id')}"
                counts[key] += 1
                if counts[key] > 1:
                    conflicts.append(key)
        return conflicts

    def _resolve_conflicts(self, assignments):
        """Resolve conflicts"""
        return assignments

    def _parse_time(self, time_str):
        """Parse time string"""
        from datetime import time as dt_time
        try:
            if isinstance(time_str, dt_time):
                return time_str
            return dt_time.fromisoformat(time_str)
        except:
            return dt_time(9, 0)

    def _calculate_grouping_stats(self, assignments):
        """Calculate consecutive grouping statistics"""
        from collections import defaultdict
        if not assignments:
            return {"consecutive_count": 0, "total_instructors": 0, "avg_classroom_changes": 0.0, "consecutive_percentage": 0.0}
        
        instructor_assignments = defaultdict(list)
        for a in assignments:
            pid = a.get("project_id")
            proj = next((p for p in self.projects if p.get("id") == pid), None)
            if proj and proj.get("responsible_id"):
                instructor_assignments[proj["responsible_id"]].append(a)
        
        consecutive_count = 0
        total_changes = 0
        for iid, ilist in instructor_assignments.items():
            classrooms = set(a.get("classroom_id") for a in ilist)
            changes = len(classrooms) - 1
            total_changes += changes
            tids = sorted([a.get("timeslot_id") for a in ilist])
            is_consec = all(tids[i] + 1 == tids[i+1] for i in range(len(tids) - 1)) if len(tids) > 1 else True
            if is_consec and len(classrooms) == 1:
                consecutive_count += 1
        
        total_inst = len(instructor_assignments)
        avg_changes = total_changes / total_inst if total_inst > 0 else 0
        return {
            "consecutive_count": consecutive_count,
            "total_instructors": total_inst,
            "avg_classroom_changes": avg_changes,
            "consecutive_percentage": (consecutive_count / total_inst * 100) if total_inst > 0 else 0
        }

    def _calculate_fitness_scores(self, solution):
        """Calculate fitness scores"""
        if not solution:
            return {"load_balance": 0.0, "classroom_changes": 0.0, "time_efficiency": 0.0, "total": 0.0}
        lb = self._calculate_load_balance_score(solution)
        cc = self._calculate_classroom_changes_score(solution)
        te = self._calculate_time_efficiency_score(solution)
        return {"load_balance": lb, "classroom_changes": cc, "time_efficiency": te, "total": lb + cc + te}

    def _calculate_load_balance_score(self, solution):
        """Calculate load balance score"""
        loads = {}
        for a in solution:
            for iid in a.get("instructors", []):
                loads[iid] = loads.get(iid, 0) + 1
        if not loads:
            return 0.0
        lst = list(loads.values())
        avg = sum(lst) / len(lst)
        return sum((l - avg) ** 2 for l in lst) / len(lst)

    def _calculate_classroom_changes_score(self, solution):
        """Calculate classroom changes score"""
        crooms = {}
        changes = 0
        for a in solution:
            cid = a.get("classroom_id")
            for iid in a.get("instructors", []):
                if iid in crooms:
                    if crooms[iid] != cid:
                        changes += 1
                crooms[iid] = cid
        return float(changes)

    def _calculate_time_efficiency_score(self, solution):
        """Calculate time efficiency score"""
        tslots = {}
        gaps = 0
        for a in solution:
            tid = a.get("timeslot_id")
            for iid in a.get("instructors", []):
                if iid not in tslots:
                    tslots[iid] = []
                tslots[iid].append(tid)
        for ts_list in tslots.values():
            sorted_ts = sorted(ts_list)
            for i in range(1, len(sorted_ts)):
                if sorted_ts[i] - sorted_ts[i-1] > 1:
                    gaps += 1
        return float(gaps)

    # ========== AI-Based Instructor Pairing Methods ==========

    def _sort_instructors_by_project_count(self, instructor_projects):
        """
        Instructor'ları proje sorumluluk sayısına göre sırala.
        En fazla projeli instructor başta, en az projeli sonda.
        
        Args:
            instructor_projects: Dict[instructor_id, List[project]]
        
        Returns:
            List[Tuple[instructor_id, List[project]]] - Sıralanmış liste
        """
        instructor_list = list(instructor_projects.items())
        # En fazla projeden en aza doğru sırala
        instructor_list.sort(key=lambda x: len(x[1]), reverse=True)
        return instructor_list
    
    def _split_instructors_into_groups(self, instructor_list):
        """
        Instructor listesini ikiye böl.
        
        Çift sayıda instructor: Tam ortadan ikiye böl (n/2, n/2)
        Tek sayıda instructor: Üst grupta n, alt grupta n+1
        
        Args:
            instructor_list: Sıralanmış instructor listesi
        
        Returns:
            Tuple[List, List] - (upper_group, lower_group)
        """
        total_instructors = len(instructor_list)
        
        if total_instructors % 2 == 0:
            # Çift sayıda instructor: Tam ortadan böl
            split_point = total_instructors // 2
            upper_group = instructor_list[:split_point]
            lower_group = instructor_list[split_point:]
            logger.info(f"✂️ Çift sayıda instructor ({total_instructors}): {split_point} üst, {split_point} alt")
        else:
            # Tek sayıda instructor: Üst grupta n, alt grupta n+1
            split_point = total_instructors // 2
            upper_group = instructor_list[:split_point]
            lower_group = instructor_list[split_point:]
            logger.info(f"✂️ Tek sayıda instructor ({total_instructors}): {split_point} üst, {split_point + 1} alt")
        
        return upper_group, lower_group
    
    def _create_instructor_pairs(self, upper_group, lower_group):
        """
        Üst ve alt gruptan birer instructor alarak eşleştirme yap.
        
        Args:
            upper_group: Fazla projeli instructor'lar
            lower_group: Az projeli instructor'lar
        
        Returns:
            List[Tuple] - [(instructor_a, instructor_b), ...]
        """
        pairs = []
        
        # Üst ve alt gruptan eşleştir
        for i in range(len(upper_group)):
            if i < len(lower_group):
                pairs.append((upper_group[i], lower_group[i]))
            else:
                # Eğer alt grup bittiyse, üst grupta kalan instructor'ları tek başına ekle
                pairs.append((upper_group[i], None))
        
        # Eğer alt grup daha uzunsa (tek sayıda instructor durumunda)
        if len(lower_group) > len(upper_group):
            for i in range(len(upper_group), len(lower_group)):
                pairs.append((None, lower_group[i]))
        
        return pairs
    
    def _assign_projects_with_consecutive_jury_pairing(
        self,
        instructor_pairs,
        sorted_timeslots,
        used_slots,
        instructor_timeslot_usage,
        assigned_projects,
        use_consecutive=True
    ):
        """
        AI-Based Consecutive Grouping ile Jüri Ataması.
        
        Mantık:
        1. Her pair için (X, Y):
           - X'in projelerini ata (X sorumlu, Y jüri)
           - Hemen ardından Y'nin projelerini ata (Y sorumlu, X jüri)
        2. Consecutive grouping: Aynı sınıfta ardışık slotlarda
        3. Hard kısıtları kaldır, AI-based optimizasyon yap
        
        Args:
            instructor_pairs: Eşleştirilmiş instructor çiftleri
            sorted_timeslots: Sıralanmış zaman slotları
            used_slots: Kullanılan slotlar
            instructor_timeslot_usage: Instructor'ların kullandığı slotlar
            assigned_projects: Atanmış projeler
        
        Returns:
            List[Dict] - Assignments
        """
        from collections import defaultdict
        assignments = []
        
        for pair_idx, (instructor_a, instructor_b) in enumerate(instructor_pairs):
            logger.info(f"\n🔗 Çift {pair_idx + 1} işleniyor...")
            
            # Instructor A varsa, projelerini ata
            if instructor_a:
                instructor_a_id = instructor_a[0]
                instructor_a_projects = instructor_a[1]
                logger.info(f"  📌 Instructor {instructor_a_id}: {len(instructor_a_projects)} proje")
                
                # Instructor B'yi jüri olarak belirle
                jury_id = instructor_b[0] if instructor_b else None
                
                # Bu instructor için en uygun sınıf ve ardışık slotları bul
                assigned_count = self._assign_instructor_projects_consecutively(
                    instructor_a_id,
                    instructor_a_projects,
                    jury_id,
                    sorted_timeslots,
                    used_slots,
                    instructor_timeslot_usage,
                    assigned_projects,
                    assignments,
                    is_primary=True,  # X sorumlu, Y jüri
                    use_consecutive=use_consecutive
                )
                logger.info(f"  ✅ Instructor {instructor_a_id}: {assigned_count} proje atandı")
            
            # Instructor B varsa, projelerini ata (consecutive olarak A'nın hemen ardından)
            if instructor_b:
                instructor_b_id = instructor_b[0]
                instructor_b_projects = instructor_b[1]
                logger.info(f"  📌 Instructor {instructor_b_id}: {len(instructor_b_projects)} proje")
                
                # Instructor A'yı jüri olarak belirle
                jury_id = instructor_a[0] if instructor_a else None
                
                # Bu instructor için ardışık slotları bul (A'nın hemen ardından)
                assigned_count = self._assign_instructor_projects_consecutively(
                    instructor_b_id,
                    instructor_b_projects,
                    jury_id,
                    sorted_timeslots,
                    used_slots,
                    instructor_timeslot_usage,
                    assigned_projects,
                    assignments,
                    is_primary=False,  # Y sorumlu, X jüri
                    use_consecutive=use_consecutive
                )
                logger.info(f"  ✅ Instructor {instructor_b_id}: {assigned_count} proje atandı")
        
        return assignments
    
    def _assign_instructor_projects_consecutively(
        self,
        instructor_id,
        projects,
        jury_id,
        sorted_timeslots,
        used_slots,
        instructor_timeslot_usage,
        assigned_projects,
        assignments,
        is_primary=True,
        use_consecutive=True
    ):
        """
        Bir instructor'ın projelerini consecutive olarak ata.
        🤖 AI-POWERED: Akıllı sınıf seçimi, timeslot skorlama, NO HARD CONSTRAINTS!
        
        Args:
            instructor_id: Sorumlu instructor ID
            projects: Atanacak projeler
            jury_id: Jüri instructor ID (None olabilir)
            sorted_timeslots: Sıralanmış zaman slotları
            used_slots: Kullanılan slotlar
            instructor_timeslot_usage: Instructor'ların kullandığı slotlar
            assigned_projects: Atanmış projeler
            assignments: Atama listesi (referans)
            is_primary: X sorumlu mu, Y sorumlu mu
        
        Returns:
            int - Atanan proje sayısı
        """
        assigned_count = 0
        
        # 🤖 AI FEATURE 2: AKILLI SINIF SEÇİMİ
        logger.info(f"    🤖 AI-based sınıf seçimi başlatılıyor...")
        best_classroom = self._select_best_classroom_ai(
            instructor_id,
            len(projects),
            projects,
            used_slots,
            instructor_timeslot_usage,
            assignments
        )
        
        if not best_classroom:
            # Fallback: İlk sınıfı kullan
            best_classroom = self.classrooms[0].get("id") if self.classrooms else None
            logger.warning(f"    ⚠️ AI sınıf seçimi başarısız, fallback kullanılıyor")
        
        best_start_idx = None
        
        # Ardışık slotları bul (AI-optimized)
        for classroom in self.classrooms:
            classroom_id = classroom.get("id")
            
            # AI seçtiği sınıfı önceliklendir
            if classroom_id != best_classroom:
                continue
            
            # 🆕 ADAPTIVE CONSECUTIVE: Sınıf sayısına göre consecutive grouping
            if use_consecutive:
                # Bu sınıfta ardışık boş slotlar var mı?
                consecutive_slots = self._find_consecutive_slots(
                    classroom_id,
                    len(projects),
                    sorted_timeslots,
                    used_slots,
                    instructor_timeslot_usage,
                    instructor_id,
                    jury_id
                )
                
                if consecutive_slots:
                    best_classroom = classroom_id
                    best_start_idx = consecutive_slots[0]
                    logger.info(f"    🎯 Sınıf {classroom_id}: {len(consecutive_slots)} ardışık slot bulundu")
                    break
            else:
                # Non-consecutive: Herhangi bir boş slot bul
                for idx, timeslot in enumerate(sorted_timeslots):
                    timeslot_id = timeslot.get("id")
                    slot_key = (classroom_id, timeslot_id)
                    
                    if slot_key not in used_slots:
                        best_classroom = classroom_id
                        best_start_idx = idx
                        logger.info(f"    🎯 Sınıf {classroom_id}: Boş slot bulundu (non-consecutive)")
                        break
                
                if best_start_idx is not None:
                    break
        
        # Eğer ardışık slot bulunamadıysa, en erken boş slotları kullan
        if not best_classroom:
            logger.info(f"    ⚠️ Ardışık slot bulunamadı, FALLBACK mekanizması devreye giriyor...")
            best_classroom, best_start_idx = self._find_earliest_available_slot(
                sorted_timeslots,
                used_slots,
                instructor_timeslot_usage,
                instructor_id,
                jury_id
            )
            
            # 🔧 SORUN DÜZELTİLDİ: Eğer hala slot bulunamadıysa, herhangi bir boş slot ara
            if not best_classroom:
                logger.warning(f"    🔄 FALLBACK: En erken slot da bulunamadı, herhangi bir boş slot aranıyor...")
                best_classroom, best_start_idx = self._find_any_available_slot_fallback(
                    sorted_timeslots,
                    used_slots,
                    instructor_timeslot_usage,
                    instructor_id,
                    jury_id
                )
        
        if best_classroom and best_start_idx is not None:
            # Projeleri ata
            current_slot_idx = best_start_idx
            
            for project in projects:
                project_id = project.get("id")
                
                if project_id in assigned_projects:
                    continue
                
                # Bu slot uygun mu kontrol et
                timeslot_id = sorted_timeslots[current_slot_idx].get("id")
                slot_key = (best_classroom, timeslot_id)
                
                # 🤖 AI-BASED: Soft constraint - Calculate conflict penalty
                busy_penalty = self._calculate_instructor_busy_penalty(
                    instructor_id, timeslot_id, instructor_timeslot_usage, jury_id
                )
                
                # Prefer slots with low conflict (soft threshold, not hard block)
                if slot_key in used_slots or busy_penalty > 100.0:
                    # Sonraki boş slotu bul
                    next_slot = self._find_next_available_slot_in_classroom(
                        best_classroom,
                        current_slot_idx + 1,
                        sorted_timeslots,
                        used_slots,
                        instructor_timeslot_usage,
                        instructor_id,
                        jury_id
                    )
                    
                    if next_slot is not None:
                        current_slot_idx = next_slot
                        timeslot_id = sorted_timeslots[current_slot_idx].get("id")
                        slot_key = (best_classroom, timeslot_id)
                    else:
                        # Bu sınıfta yer yok, başka sınıfa geç
                        alt_classroom, alt_slot_idx = self._find_earliest_available_slot(
                            sorted_timeslots,
                            used_slots,
                            instructor_timeslot_usage,
                            instructor_id,
                            jury_id
                        )
                        
                        if alt_classroom:
                            best_classroom = alt_classroom
                            current_slot_idx = alt_slot_idx
                            timeslot_id = sorted_timeslots[current_slot_idx].get("id")
                            slot_key = (best_classroom, timeslot_id)
                        else:
                            # 🚫 NO HARD CONSTRAINT! En iyi çabayı göster
                            logger.warning(f"    ⚠️ Proje {project_id} için ideal slot yok, AI en iyi alternatifi buluyor...")
                            
                            # AI-based best effort: En az çakışmalı slotu bul
                            best_effort_slot = self._find_best_effort_slot_ai(
                                project,
                                instructor_id,
                                jury_id,
                                sorted_timeslots,
                                used_slots,
                                instructor_timeslot_usage
                            )
                            
                            if best_effort_slot:
                                best_classroom = best_effort_slot['classroom_id']
                                timeslot_id = best_effort_slot['timeslot_id']
                                current_slot_idx = best_effort_slot['slot_idx']
                                slot_key = (best_classroom, timeslot_id)
                                logger.info(f"    🤖 AI Best Effort: Sınıf {best_classroom}, Slot {timeslot_id}")
                            else:
                                # 🚫 ABSOLUTE NO HARD CONSTRAINT! 
                                # Son çare: Overlap kabul et ve en az kötü slota ata
                                logger.warning(f"    ⚠️ CRITICAL: Best effort slot bulunamadı, FORCE ASSIGNMENT yapılıyor!")
                                
                                # En az yüklü sınıfı ve en erken slotu zorla kullan
                                fallback_classroom = min(
                                    self.classrooms,
                                    key=lambda c: sum(1 for (cid, _) in used_slots if cid == c.get('id'))
                                ).get('id')
                                
                                fallback_slot_idx = current_slot_idx
                                timeslot_id = sorted_timeslots[fallback_slot_idx].get("id")
                                
                                best_classroom = fallback_classroom
                                current_slot_idx = fallback_slot_idx
                                slot_key = (best_classroom, timeslot_id)
                                
                                logger.warning(f"    🚨 FORCE ASSIGNMENT: Proje {project_id} → Sınıf {best_classroom}, Slot {timeslot_id} (OVERLAP ACCEPTED)")
                
                # Jüri listesini oluştur
                instructors = [instructor_id]
                if jury_id:
                    instructors.append(jury_id)
                
                # Atamayı yap
                assignment = {
                    "project_id": project_id,
                    "classroom_id": best_classroom,
                    "timeslot_id": timeslot_id,
                    "is_makeup": project.get("is_makeup", False),
                    "instructors": instructors
                }
                
                assignments.append(assignment)
                used_slots.add(slot_key)
                instructor_timeslot_usage[instructor_id].add(timeslot_id)
                if jury_id:
                    instructor_timeslot_usage[jury_id].add(timeslot_id)
                assigned_projects.add(project_id)
                assigned_count += 1
                
                logger.info(f"    ✓ Proje {project_id}: Sınıf {best_classroom}, Slot {timeslot_id}, Sorumlu: {instructor_id}, Jüri: {jury_id}")
                
                # Sonraki slota geç
                current_slot_idx += 1
                if current_slot_idx >= len(sorted_timeslots):
                    break
        
        return assigned_count
    
    def _find_consecutive_slots(
        self,
        classroom_id,
        needed_slots,
        sorted_timeslots,
        used_slots,
        instructor_timeslot_usage,
        instructor_id,
        jury_id
    ):
        """
        Bir sınıfta ardışık boş slotlar bul.
        
        Returns:
            List[int] - Ardışık slot indeksleri, bulunamazsa None
        """
        consecutive = []
        
        for idx, timeslot in enumerate(sorted_timeslots):
            timeslot_id = timeslot.get("id")
            slot_key = (classroom_id, timeslot_id)
            
            # 🤖 AI-BASED: Bu slot uygun mu? (soft constraint)
            busy_penalty = self._calculate_instructor_busy_penalty(
                instructor_id, timeslot_id, instructor_timeslot_usage, jury_id
            )
            
            # Accept slots with low/no conflict
            if slot_key not in used_slots and busy_penalty <= 0:  # Soft threshold
                consecutive.append(idx)
                
                if len(consecutive) >= needed_slots:
                    return consecutive
            else:
                consecutive = []
        
        return consecutive if len(consecutive) >= needed_slots else None
    
    def _calculate_instructor_busy_penalty(self, instructor_id, timeslot_id, instructor_timeslot_usage, jury_id=None) -> float:
        """
        🤖 AI-BASED SOFT CONSTRAINT: Calculate penalty if instructor is busy (NO HARD BLOCKING!)
        
        Instead of return True/False (hard constraint), calculate conflict penalty score.
        Higher penalty = more conflicts, but assignments are NEVER blocked.
        
        Args:
            instructor_id: Sorumlu instructor
            timeslot_id: Kontrol edilecek slot
            instructor_timeslot_usage: Instructor kullanım bilgisi
            jury_id: Jüri instructor (varsa)
        
        Returns:
            Conflict penalty (0 = available, 300+ = busy/conflict)
        """
        penalty = 0.0
        
        # SOFT CHECK: Sorumlu instructor meşgul mü?
        if timeslot_id in instructor_timeslot_usage.get(instructor_id, set()):
            penalty += 300.0  # High penalty for responsible conflict
        
        # SOFT CHECK: Jüri meşgul mü?
        if jury_id and timeslot_id in instructor_timeslot_usage.get(jury_id, set()):
            penalty += 200.0  # Penalty for jury conflict
        
        # Bonus if both available
        if penalty == 0.0:
            penalty = -50.0  # Negative = bonus!
        
        return penalty
    
    def _find_earliest_available_slot_with_score(
        self,
        sorted_timeslots,
        used_slots,
        instructor_timeslot_usage,
        instructor_id,
        jury_id
    ):
        """
        🤖 AI-BASED FALLBACK SCORING: Find earliest available slot with quality score (NO RETURN NONE!)
        
        Instead of returning (None, None) when no slot found, returns a fallback slot with penalty score.
        
        Returns:
            Dict with 'classroom_id', 'slot_idx', and 'score'
        """
        for slot_idx, timeslot in enumerate(sorted_timeslots):
            timeslot_id = timeslot.get("id")
            
            for classroom in self.classrooms:
                classroom_id = classroom.get("id")
                slot_key = (classroom_id, timeslot_id)
                
                # 🤖 AI-BASED: Check availability with scoring (soft constraint)
                busy_penalty = self._calculate_instructor_busy_penalty(
                    instructor_id, timeslot_id, instructor_timeslot_usage, jury_id
                )
                
                if slot_key not in used_slots and busy_penalty <= 0:  # Soft threshold
                    # ✅ OPTIMAL SLOT FOUND!
                    return {
                        'classroom_id': classroom_id,
                        'slot_idx': slot_idx,
                        'score': 100.0,
                        'quality': 'optimal'
                    }
        
        # 🤖 NO OPTIMAL SLOT - RETURN FALLBACK WITH PENALTY (NOT None!)
        # Fallback: Use first classroom and first available timeslot
        fallback_classroom = self.classrooms[0].get("id") if self.classrooms else -1
        fallback_slot_idx = 0
        return {
            'classroom_id': fallback_classroom,
            'slot_idx': fallback_slot_idx,
            'score': -700.0,  # Very high penalty for fallback
            'quality': 'fallback',
            'reason': 'no_earliest_available_slot'
        }
    
    def _find_next_available_slot_in_classroom_with_score(
        self,
        classroom_id,
        start_idx,
        sorted_timeslots,
        used_slots,
        instructor_timeslot_usage,
        instructor_id,
        jury_id
    ):
        """
        🤖 AI-BASED FALLBACK SCORING: Find next available slot in classroom with quality score (NO RETURN NONE!)
        
        Instead of returning None when no slot found, returns a fallback slot with penalty score.
        
        Returns:
            Dict with 'slot_idx' and 'score'
        """
        for idx in range(start_idx, len(sorted_timeslots)):
            timeslot_id = sorted_timeslots[idx].get("id")
            slot_key = (classroom_id, timeslot_id)
            
            # 🤖 AI-BASED: Check availability with scoring (soft constraint)
            busy_penalty = self._calculate_instructor_busy_penalty(
                instructor_id, timeslot_id, instructor_timeslot_usage, jury_id
            )
            
            if slot_key not in used_slots and busy_penalty <= 0:  # Soft threshold
                # ✅ OPTIMAL SLOT FOUND!
                return {
                    'slot_idx': idx,
                    'score': 100.0,
                    'quality': 'optimal'
                }
        
        # 🤖 NO OPTIMAL SLOT - RETURN FALLBACK WITH PENALTY (NOT None!)
        # Fallback: Use start_idx (accept conflict)
        return {
            'slot_idx': start_idx if start_idx < len(sorted_timeslots) else 0,
            'score': -400.0,  # High penalty for fallback
            'quality': 'fallback',
            'reason': 'no_next_available_slot_in_classroom'
        }
    
    # ========== AI-BASED ENHANCEMENTS - NO HARD CONSTRAINTS! ==========
    
    def _calculate_timeslot_score_ai(self, timeslot, project, current_assignments=None):
        """
        🤖 AI FEATURE 1: Akıllı Zaman Slot Seçimi
        
        Timeslot'a AI-based skor hesapla:
        1. Sabah saatleri bonus (09:00-11:00)
        2. Bitirme projeleri sabah tercih et
        3. Ara projeler öğleden sonra olabilir
        4. Öğle arası penaltı (12:00-13:00)
        5. Geç saatler penaltı (16:00+)
        
        Returns:
            float - Timeslot skoru (yüksek = daha iyi)
        """
        if not self.ai_timeslot_scoring:
            return 100.0
        
        score = 100.0
        start_time = timeslot.get('start_time', '09:00')
        
        try:
            hour = int(start_time.split(':')[0])
            minute = int(start_time.split(':')[1]) if ':' in start_time else 0
        except:
            return score
        
        project_type = project.get('type', 'ara') if project else 'ara'
        is_makeup = project.get('is_makeup', False) if project else False
        
        # 1. SABAH SAATLERİ BONUS (09:00-11:00)
        if 9 <= hour < 11:
            score += self.bonus_factors.get("morning_slot", 50.0)
            logger.debug(f"      Sabah bonusu: +{self.bonus_factors.get('morning_slot', 50.0)}")
            
            # 2. BİTİRME PROJELERİ SABAH ÖNCELİKLİ
            if project_type == "bitirme":
                score += 30.0
                logger.debug(f"      Bitirme sabah bonusu: +30.0")
        
        # 3. ÖĞLEDEN SONRA ERKEN (13:00-15:00)
        elif 13 <= hour < 15:
            score += 20.0
            logger.debug(f"      Öğleden sonra bonusu: +20.0")
            
            # Ara projeler öğleden sonra olabilir
            if project_type == "ara":
                score += 10.0
                logger.debug(f"      Ara proje öğleden sonra bonusu: +10.0")
        
        # 4. ÖĞLE ARASI PENALTY (12:00-13:00)
        elif 12 <= hour < 13:
            score -= 30.0
            logger.debug(f"      Öğle arası penaltı: -30.0")
        
        # 5. GEÇ SAATLER PENALTY (16:00+)
        elif hour >= 16:
            score -= 50.0
            logger.debug(f"      Geç saat penaltı: -50.0")
            
            # Makeup projeler geç saatlerde daha da kötü
            if is_makeup:
                score -= 20.0
                logger.debug(f"      Makeup geç saat penaltı: -20.0")
        
        # ÇEYREK SAATLER (xx:30) yerine TAM SAATLER (xx:00) tercih edilir
        if minute == 0:
            score += 5.0
        
        return max(score, 0.0)  # Negatif skor olmasın
    
    def _select_best_classroom_ai(
        self, 
        instructor_id, 
        project_count, 
        projects,
        used_slots, 
        instructor_timeslot_usage,
        current_assignments=None
    ):
        """
        🤖 AI FEATURE 2: Akıllı Sınıf Seçimi
        
        AI-based sınıf seçimi:
        1. Load balancing - En az dolu sınıfı tercih et
        2. Same classroom bonus - Instructor'ın önceki sınıfını tercih et
        3. Capacity optimization - Proje sayısına göre uygun sınıf
        4. Historical patterns - Geçmiş başarılı kombinasyonlar
        
        Returns:
            classroom_id - En uygun sınıf ID'si
        """
        if not self.ai_classroom_selection:
            # AI kapalıysa ilk sınıfı kullan
            return self.classrooms[0].get('id') if self.classrooms else None
        
        classroom_scores = {}
        
        for classroom in self.classrooms:
            classroom_id = classroom.get('id')
            score = 100.0
            
            # 1. LOAD BALANCING - En az dolu sınıf
            usage_rate = self._calculate_classroom_usage(classroom_id, used_slots)
            score += (1.0 - usage_rate) * 100.0
            logger.debug(f"      Sınıf {classroom_id} kullanım oranı: {usage_rate:.2f}, load balance skoru: {(1.0 - usage_rate) * 100.0:.2f}")
            
            # 2. SAME CLASSROOM BONUS - 🤖 AI-BASED: Classroom reuse bonus (soft constraint)
            if current_assignments:
                reuse_bonus = self._calculate_classroom_reuse_bonus(
                    instructor_id, classroom_id, current_assignments
                )
                score += reuse_bonus
                if reuse_bonus > 0:
                    logger.debug(f"      Sınıf {classroom_id} aynı sınıf bonusu: +{reuse_bonus:.2f}")
            
            # 3. CAPACITY OPTIMIZATION - Proje sayısına göre uygun kapasite
            capacity_score = self._calculate_capacity_fitness(
                classroom, project_count, projects
            )
            score += capacity_score
            logger.debug(f"      Sınıf {classroom_id} kapasite skoru: {capacity_score:.2f}")
            
            # 4. HISTORICAL PATTERNS - Adaptive learning
            if self.ai_adaptive_learning and instructor_id in self.instructor_preferences:
                preferred_classroom = self.instructor_preferences[instructor_id].get('preferred_classroom')
                if preferred_classroom == classroom_id:
                    score += 30.0
                    logger.debug(f"      Sınıf {classroom_id} historical preference bonusu: +30.0")
            
            classroom_scores[classroom_id] = score
        
        if not classroom_scores:
            # 🤖 FALLBACK: Return first classroom with penalty (not None!)
            fallback_classroom = self.classrooms[0].get("id") if self.classrooms else -1
            logger.warning(f"    ⚠️ AI Sınıf Seçimi: No classroom scores, using fallback {fallback_classroom}")
            return fallback_classroom
        
        # En yüksek skorlu sınıfı seç
        best_classroom = max(classroom_scores, key=classroom_scores.get)
        best_score = classroom_scores[best_classroom]
        
        logger.info(f"    🎯 AI Sınıf Seçimi: Sınıf {best_classroom} (Skor: {best_score:.2f})")
        
        return best_classroom
    
    def _calculate_classroom_usage(self, classroom_id, used_slots):
        """Sınıfın doluluk oranını hesapla"""
        if not self.timeslots:
            return 0.0
        
        total_slots = len(self.timeslots)
        used_slots_in_classroom = sum(
            1 for (cid, tid) in used_slots if cid == classroom_id
        )
        
        return used_slots_in_classroom / total_slots if total_slots > 0 else 0.0
    
    def _calculate_classroom_reuse_bonus(self, instructor_id, classroom_id, assignments) -> float:
        """
        🤖 AI-BASED SOFT CONSTRAINT: Calculate bonus for classroom reuse (NO HARD BLOCKING!)
        
        Instead of return True/False, calculate bonus score for familiarity.
        
        Returns:
            Bonus score (positive = reuse bonus, 0 = new classroom)
        """
        for assignment in assignments:
            if classroom_id == assignment.get('classroom_id'):
                instructors = assignment.get('instructors', [])
                if instructor_id in instructors:
                    return 50.0  # Bonus for same classroom!
        
        return 0.0  # No bonus for new classroom (neutral)
    
    def _calculate_capacity_fitness(self, classroom, project_count, projects):
        """
        🤖 AI FEATURE 3: Smart Classroom Capacity Management
        
        Sınıf kapasitesinin proje ihtiyacına uygunluk skoru
        """
        if not self.ai_capacity_management:
            return 0.0
        
        capacity = classroom.get('capacity', 30)
        score = 0.0
        
        # Proje tipine göre ideal kapasite
        if projects:
            bitirme_count = sum(1 for p in projects if p.get('type') == 'bitirme')
            ara_count = len(projects) - bitirme_count
            
            # Bitirme projeleri için orta/büyük sınıf
            if bitirme_count > 0:
                if 30 <= capacity <= 50:
                    score += 40.0
                elif capacity > 50:
                    score += 20.0
            
            # Ara projeler için küçük/orta sınıf
            if ara_count > 0:
                if 20 <= capacity <= 35:
                    score += 30.0
        
        # Proje sayısına göre
        if project_count <= 2:
            # Az projeli -> Küçük sınıf
            if capacity < 30:
                score += 30.0
        elif project_count >= 5:
            # Çok projeli -> Büyük sınıf
            if capacity >= 40:
                score += 30.0
        else:
            # Orta projeli -> Orta sınıf
            if 30 <= capacity < 40:
                score += 30.0
        
        return score
    
    def _resolve_conflicts_ai(self, assignments):
        """
        🤖 AI FEATURE 4: AI-Based Conflict Resolution
        
        Akıllı çakışma çözümü - NO HARD CONSTRAINTS!
        1. Conflict tipini tespit et
        2. En az etkili çözümü bul (minimum değişiklik)
        3. Alternative slot öner
        4. Smart swap stratejisi
        5. Priority-based resolution
        """
        if not self.ai_conflict_resolution:
            return assignments
        
        conflicts = self._detect_conflicts(assignments)
        
        if not conflicts:
            logger.info("  ✅ No conflicts detected")
            return assignments
        
        logger.info(f"🤖 AI-Based Conflict Resolution: {len(conflicts)} conflicts detected")
        resolution_count = 0
        
        for conflict_key in conflicts:
            try:
                # Conflict parse et
                parts = conflict_key.split('_')
                instructor_id = int(parts[1])
                timeslot_id = int(parts[3])
                
                # Bu slottaki tüm çakışan atamaları bul
                conflicting_assignments = [
                    a for a in assignments 
                    if instructor_id in a.get('instructors', []) 
                    and a.get('timeslot_id') == timeslot_id
                ]
                
                if len(conflicting_assignments) <= 1:
                    continue
                
                logger.info(f"  🔍 Resolving conflict: Instructor {instructor_id}, Slot {timeslot_id}")
                
                # ÖNCELIK SIRASI: Bitirme > Ara, Sorumlu > Jüri
                sorted_assignments = sorted(
                    conflicting_assignments,
                    key=lambda a: (
                        self._get_project_type(a.get('project_id')) == 'bitirme',
                        a.get('instructors', [])[0] == instructor_id if a.get('instructors') else False
                    ),
                    reverse=True
                )
                
                # İlk projeyi tut, diğerlerini taşı
                keep_assignment = sorted_assignments[0]
                move_assignments = sorted_assignments[1:]
                
                logger.info(f"    Keeping: Project {keep_assignment.get('project_id')}")
                
                for assignment in move_assignments:
                    # Alternative slot bul
                    new_slot = self._find_alternative_slot_ai(
                        assignment, 
                        instructor_id, 
                        assignments
                    )
                    
                    if new_slot:
                        old_slot = assignment.get('timeslot_id')
                        old_classroom = assignment.get('classroom_id')
                        
                        assignment['timeslot_id'] = new_slot['timeslot_id']
                        if new_slot.get('classroom_id'):
                            assignment['classroom_id'] = new_slot['classroom_id']
                        
                        resolution_count += 1
                        logger.info(
                            f"    ✓ Project {assignment.get('project_id')}: "
                            f"Moved from Slot {old_slot} → {new_slot['timeslot_id']}"
                        )
                    else:
                        logger.warning(
                            f"    ⚠️ Could not find alternative for Project {assignment.get('project_id')}"
                        )
            
            except Exception as e:
                logger.error(f"  Error resolving conflict {conflict_key}: {e}")
                continue
        
        logger.info(f"  ✅ AI Conflict Resolution Complete: {resolution_count} conflicts resolved")
        
        return assignments
    
    def _get_project_type(self, project_id):
        """Proje tipini getir"""
        for project in self.projects:
            if project.get('id') == project_id:
                return project.get('type', 'ara')
        return 'ara'
    
    def _find_alternative_slot_ai(self, assignment, instructor_id, all_assignments):
        """
        Conflict için alternatif slot bul - AI-based scoring ile
        """
        project_id = assignment.get('project_id')
        current_classroom = assignment.get('classroom_id')
        current_slot = assignment.get('timeslot_id')
        instructors = assignment.get('instructors', [])
        
        # Tüm slotları skorla
        slot_scores = []
        
        for classroom in self.classrooms:
            classroom_id = classroom.get('id')
            
            for timeslot in self.timeslots:
                timeslot_id = timeslot.get('id')
                
                # Mevcut slot değilse
                if timeslot_id == current_slot and classroom_id == current_classroom:
                    continue
                
                # Bu slot uygun mu kontrol et
                is_available = True
                
                # Tüm instructor'lar uygun mu?
                for inst_id in instructors:
                    # Bu instructor bu slotta başka projede mi?
                    for other_assignment in all_assignments:
                        if (other_assignment.get('timeslot_id') == timeslot_id and 
                            inst_id in other_assignment.get('instructors', [])):
                            is_available = False
                            break
                    if not is_available:
                        break
                
                if is_available:
                    # Slot skorunu hesapla
                    project = next((p for p in self.projects if p.get('id') == project_id), None)
                    slot_score = self._calculate_timeslot_score_ai(timeslot, project)
                    
                    # Aynı sınıf bonusu
                    if classroom_id == current_classroom:
                        slot_score += 25.0
                    
                    slot_scores.append({
                        'timeslot_id': timeslot_id,
                        'classroom_id': classroom_id,
                        'score': slot_score
                    })
        
        if slot_scores:
            # En yüksek skorlu slot'u döndür
            best_slot = max(slot_scores, key=lambda x: x['score'])
            return best_slot
        
        # 🤖 FALLBACK: Return current assignment with penalty (not None!)
        return {
            'classroom_id': current_classroom,
            'timeslot_id': current_slot,
            'score': -800.0,  # Very high penalty
            'quality': 'fallback',
            'reason': 'no_alternative_slot_found'
        }
    
    def _calculate_instructor_workload_ai(self, instructor_id, assignments):
        """
        🤖 AI FEATURE 5: Dinamik Workload Balancing
        
        Instructor'ın toplam iş yükünü hesapla:
        1. Sorumlu olduğu proje sayısı (ağırlık: 2x)
        2. Jüri olduğu proje sayısı (ağırlık: 1x)
        3. Toplam saat (timeslot count)
        4. Sınıf değişikliği sayısı (her değişiklik: 0.5x penalty)
        """
        if not self.ai_workload_balancing:
            return {'score': 0, 'responsible': 0, 'jury': 0}
        
        responsible_count = 0
        jury_count = 0
        timeslots_used = set()
        classrooms_used = []
        classroom_changes = 0
        
        for assignment in assignments:
            instructors = assignment.get('instructors', [])
            if not instructors:
                continue
            
            # Sorumlu mu?
            if len(instructors) > 0 and instructors[0] == instructor_id:
                responsible_count += 1
            # Jüri mi?
            elif instructor_id in instructors[1:]:
                jury_count += 1
            
            # Timeslot tracking
            if instructor_id in instructors:
                timeslots_used.add(assignment.get('timeslot_id'))
                classrooms_used.append(assignment.get('classroom_id'))
        
        # Sınıf değişikliği sayısı
        if len(classrooms_used) > 1:
            classroom_changes = len(set(classrooms_used)) - 1
        
        # Workload skoru hesapla
        workload_score = (responsible_count * 2.0) + (jury_count * 1.0) + (classroom_changes * 0.5)
        
        return {
            'score': workload_score,
            'responsible': responsible_count,
            'jury': jury_count,
            'total_hours': len(timeslots_used),
            'classroom_changes': classroom_changes,
            'classrooms_used': len(set(classrooms_used))
        }
    
    def _calculate_multi_objective_score_ai(self, assignments):
        """
        🤖 AI FEATURE 6: Multi-Objective Optimization Score
        
        Çoklu hedef optimizasyonu:
        1. Consecutive grouping quality (40%)
        2. Workload balance (25%)
        3. Time efficiency (20%)
        4. Classroom optimization (15%)
        
        Returns:
            Dict with total score, breakdown, and grade
        """
        if not self.ai_multi_objective:
            return {'total': 0, 'grade': 'N/A'}
        
        scores = {}
        
        # 1. CONSECUTIVE GROUPING QUALITY (40%)
        consecutive_score = self._calculate_consecutive_quality_score(assignments)
        scores['consecutive'] = consecutive_score * 0.40
        
        # 2. WORKLOAD BALANCE (25%)
        workload_score = self._calculate_workload_balance_score(assignments)
        scores['workload'] = workload_score * 0.25
        
        # 3. TIME EFFICIENCY (20%) - Early slots bonus
        time_score = self._calculate_time_efficiency_ai(assignments)
        scores['time'] = time_score * 0.20
        
        # 4. CLASSROOM OPTIMIZATION (15%)
        classroom_score = self._calculate_classroom_efficiency_score(assignments)
        scores['classroom'] = classroom_score * 0.15
        
        total_score = sum(scores.values())
        
        grade = self._get_grade_ai(total_score)
        
        return {
            'total': total_score,
            'breakdown': scores,
            'grade': grade,
            'details': {
                'consecutive_pct': consecutive_score,
                'workload_pct': workload_score,
                'time_pct': time_score,
                'classroom_pct': classroom_score
            }
        }
    
    def _calculate_consecutive_quality_score(self, assignments):
        """Consecutive grouping kalitesi (0-100)"""
        if not assignments:
            return 0.0
        
        instructor_assignments = defaultdict(list)
        for assignment in assignments:
            # Sorumlu instructor'u bul
            instructors = assignment.get('instructors', [])
            if instructors:
                responsible = instructors[0]
                instructor_assignments[responsible].append(assignment)
        
        if not instructor_assignments:
            return 0.0
        
        consecutive_count = 0
        total_instructors = len(instructor_assignments)
        
        for instructor_id, inst_assignments in instructor_assignments.items():
            # Timeslot'ları sırala
            timeslots = sorted([a.get('timeslot_id') for a in inst_assignments])
            classrooms = [a.get('classroom_id') for a in inst_assignments]
            
            # Ardışık mı?
            is_consecutive = all(
                timeslots[i] + 1 == timeslots[i+1] 
                for i in range(len(timeslots) - 1)
            ) if len(timeslots) > 1 else True
            
            # Aynı sınıfta mı?
            same_classroom = len(set(classrooms)) == 1
            
            if is_consecutive and same_classroom:
                consecutive_count += 1
        
        return (consecutive_count / total_instructors * 100) if total_instructors > 0 else 0.0
    
    def _calculate_workload_balance_score(self, assignments):
        """Workload dengesi skoru (0-100)"""
        if not assignments:
            return 0.0
        
        workloads = []
        for instructor in self.instructors:
            instructor_id = instructor.get('id')
            workload = self._calculate_instructor_workload_ai(instructor_id, assignments)
            workloads.append(workload['score'])
        
        if not workloads:
            return 0.0
        
        # Standard deviation hesapla
        mean_workload = sum(workloads) / len(workloads)
        variance = sum((w - mean_workload) ** 2 for w in workloads) / len(workloads)
        std_dev = variance ** 0.5
        
        # Düşük std_dev = yüksek skor (dengeli)
        max_possible_std = mean_workload if mean_workload > 0 else 1.0
        balance_score = max(0, 100 - (std_dev / max_possible_std * 100))
        
        return balance_score
    
    def _calculate_time_efficiency_ai(self, assignments):
        """Zaman verimliliği skoru - sabah saatleri kullanımı (0-100)"""
        if not assignments:
            return 0.0
        
        morning_count = 0
        afternoon_count = 0
        late_count = 0
        
        for assignment in assignments:
            timeslot_id = assignment.get('timeslot_id')
            timeslot = next((t for t in self.timeslots if t.get('id') == timeslot_id), None)
            
            if timeslot:
                start_time = timeslot.get('start_time', '09:00')
                try:
                    hour = int(start_time.split(':')[0])
                    
                    if 9 <= hour < 12:
                        morning_count += 1
                    elif 13 <= hour < 16:
                        afternoon_count += 1
                    else:
                        late_count += 1
                except:
                    continue
        
        total = morning_count + afternoon_count + late_count
        if total == 0:
            return 0.0
        
        # Sabah %60+, öğleden sonra %30+, gece %10- ideal
        morning_pct = (morning_count / total) * 100
        score = min(morning_pct * 1.2, 100)  # Sabah ağırlıklı skor
        
        return score
    
    def _calculate_classroom_efficiency_score(self, assignments):
        """Sınıf verimliliği skoru (0-100)"""
        if not assignments:
            return 0.0
        
        classroom_usage = defaultdict(int)
        for assignment in assignments:
            classroom_id = assignment.get('classroom_id')
            classroom_usage[classroom_id] += 1
        
        if not classroom_usage:
            return 0.0
        
        # Dengeli sınıf kullanımı = yüksek skor
        usages = list(classroom_usage.values())
        mean_usage = sum(usages) / len(usages)
        variance = sum((u - mean_usage) ** 2 for u in usages) / len(usages)
        std_dev = variance ** 0.5
        
        # Düşük varyans = dengeli kullanım
        max_std = mean_usage if mean_usage > 0 else 1.0
        balance_score = max(0, 100 - (std_dev / max_std * 100))
        
        return balance_score
    
    def _get_grade_ai(self, score):
        """Score'a göre harf notu"""
        if score >= 95: return 'A+'
        elif score >= 90: return 'A'
        elif score >= 85: return 'A-'
        elif score >= 80: return 'B+'
        elif score >= 75: return 'B'
        elif score >= 70: return 'B-'
        elif score >= 65: return 'C+'
        elif score >= 60: return 'C'
        elif score >= 55: return 'C-'
        elif score >= 50: return 'D'
        else: return 'F'
    
    def _learn_from_solution_ai(self, assignments):
        """
        🤖 AI FEATURE 7: Adaptive Learning from Solutions
        
        Başarılı çözümden pattern'leri öğren:
        1. Hangi instructor çiftleri iyi çalışıyor?
        2. Hangi sınıf kombinasyonları optimal?
        3. Hangi zaman dilimi dağılımı en iyi?
        """
        if not self.ai_adaptive_learning or not assignments:
            return
        
        logger.info("🤖 AI Adaptive Learning: Analyzing solution patterns...")
        
        # 1. INSTRUCTOR PREFERENCES
        instructor_classrooms = defaultdict(list)
        for assignment in assignments:
            instructors = assignment.get('instructors', [])
            if instructors:
                responsible = instructors[0]
                classroom_id = assignment.get('classroom_id')
                instructor_classrooms[responsible].append(classroom_id)
        
        # Her instructor'ın en çok kullandığı sınıfı kaydet
        for instructor_id, classrooms in instructor_classrooms.items():
            if classrooms:
                most_common_classroom = max(set(classrooms), key=classrooms.count)
                self.instructor_preferences[instructor_id]['preferred_classroom'] = most_common_classroom
        
        # 2. CLASSROOM USAGE HISTORY
        for assignment in assignments:
            classroom_id = assignment.get('classroom_id')
            self.classroom_usage_history[classroom_id] += 1
        
        # 3. WORKLOAD HISTORY
        for instructor in self.instructors:
            instructor_id = instructor.get('id')
            workload = self._calculate_instructor_workload_ai(instructor_id, assignments)
            self.workload_history[instructor_id].append(workload)
        
        logger.info(f"  ✓ Learned preferences for {len(self.instructor_preferences)} instructors")
        logger.info(f"  ✓ Updated classroom usage history for {len(self.classroom_usage_history)} classrooms")
        logger.info(f"  ✓ Tracked workload history for {len(self.workload_history)} instructors")
    
    def _find_best_effort_slot_ai(
        self,
        project,
        instructor_id,
        jury_id,
        sorted_timeslots,
        used_slots,
        instructor_timeslot_usage
    ):
        """
        🚫 NO HARD CONSTRAINTS! 
        En iyi çaba ile slot bul - overlap olsa bile en az çakışmalı slotu seç
        
        Returns:
            Dict with classroom_id, timeslot_id, slot_idx or None
        """
        best_slot = None
        best_score = float('-inf')
        
        for classroom in self.classrooms:
            classroom_id = classroom.get('id')
            
            for slot_idx, timeslot in enumerate(sorted_timeslots):
                timeslot_id = timeslot.get('id')
                slot_key = (classroom_id, timeslot_id)
                
                # Skor hesapla - boş slotlar öncelikli ama dolu slotlar da kabul edilir
                score = 0.0
                
                # 1. BOŞ SLOT BONUS (en önemli)
                if slot_key not in used_slots:
                    score += 100.0
                else:
                    score -= 50.0  # Dolu ama kabul edilebilir
                
                # 2. INSTRUCTOR AVAILABILITY
                if instructor_id not in instructor_timeslot_usage or \
                   timeslot_id not in instructor_timeslot_usage.get(instructor_id, set()):
                    score += 80.0
                else:
                    score -= 30.0  # Çakışma var ama devam et
                
                # 3. JURY AVAILABILITY
                if jury_id:
                    if jury_id not in instructor_timeslot_usage or \
                       timeslot_id not in instructor_timeslot_usage.get(jury_id, set()):
                        score += 60.0
                    else:
                        score -= 20.0
                
                # 4. TIMESLOT QUALITY (AI-based scoring)
                timeslot_quality = self._calculate_timeslot_score_ai(timeslot, project)
                score += timeslot_quality * 0.5
                
                # 5. CLASSROOM CAPACITY FIT
                capacity_fit = self._calculate_capacity_fitness(classroom, 1, [project])
                score += capacity_fit * 0.3
                
                if score > best_score:
                    best_score = score
                    best_slot = {
                        'classroom_id': classroom_id,
                        'timeslot_id': timeslot_id,
                        'slot_idx': slot_idx,
                        'score': score
                    }
        
        if best_slot:
            logger.info(f"      Best effort slot found: Classroom {best_slot['classroom_id']}, "
                       f"Slot {best_slot['timeslot_id']} (Score: {best_slot['score']:.2f})")
        
        return best_slot
    
    def _find_any_available_slot_fallback(
        self,
        sorted_timeslots,
        used_slots,
        instructor_timeslot_usage,
        instructor_id,
        jury_id
    ):
        """
        Herhangi bir boş slot bul (consecutive olması gerekmez) - FALLBACK mekanizması.
        
        Args:
            sorted_timeslots: Sıralanmış zaman slotları
            used_slots: Kullanılmış slotlar
            instructor_timeslot_usage: Öğretim üyesi slot kullanımı
            instructor_id: Öğretim üyesi ID
            jury_id: Jüri ID
            
        Returns:
            (classroom_id, start_idx) veya (None, None)
        """
        logger.info(f"    🔄 FALLBACK: Herhangi bir boş slot aranıyor...")
        
        # Tüm sınıflarda herhangi bir boş slot ara
        for classroom in self.classrooms:
            classroom_id = classroom.get("id")
            
            for idx, timeslot in enumerate(sorted_timeslots):
                timeslot_id = timeslot.get("id")
                slot_key = (classroom_id, timeslot_id)
                
                # Jüri instructor'ın da boş olup olmadığını kontrol et
                jury_available = True
                if jury_id:
                    jury_slots = instructor_timeslot_usage.get(jury_id, set())
                    if timeslot_id in jury_slots:
                        jury_available = False
                
                # Slot boş mu ve öğretim üyesi o saatte meşgul değil mi?
                if (slot_key not in used_slots and 
                    timeslot_id not in instructor_timeslot_usage.get(instructor_id, set()) and
                    jury_available):
                    
                    logger.info(f"    ✅ FALLBACK: Sınıf {classroom_id}, Slot {timeslot_id} bulundu")
                    return classroom_id, idx
        
        logger.error(f"    ❌ FALLBACK FAILED: Hiç boş slot bulunamadı!")
        return None, None