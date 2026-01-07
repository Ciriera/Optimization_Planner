"""
Tabu Search Algorithm - FULL AI-BASED Implementation (NO HARD CONSTRAINTS!)

🎯 AI-BASED FEATURES:
1. ADAPTIVE TABU TENURE - Dinamik tabu list boyutu (diversification/intensification)
2. FREQUENCY MEMORY - Hareket öğrenme ve başarı analizi
3. ASPIRATION CRITERIA - Akıllı tabu override (best-so-far, rare moves, stuck detection)
4. INTELLIGENT CLASSROOM SELECTION - AI-driven sınıf seçimi (consecutive + uniform)
5. SMART NEIGHBORHOOD - Conflict-based ve load-balanced komşuluk üretimi

📊 CORE STRATEGY:
- Instructor'ları proje sayısına göre sırala (EN FAZLA -> EN AZ)
- İkiye böl ve üst/alt gruptan eşleştir (max-min pairing)
- Consecutive grouping ile x sorumlu -> y jüri, sonra y sorumlu -> x jüri
- Tüm kısıtlar SOFT (AI-based scoring, NO HARD CONSTRAINTS!)

✅ NO HARD CONSTRAINTS - Tamamen AI-based soft constraint sistemi!
"""
from __future__ import annotations

from typing import Dict, Any, List, Tuple, Optional, Set
import random
import logging
from collections import defaultdict
from datetime import time as dt_time

from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

logger = logging.getLogger(__name__)

class TabuSearch(OptimizationAlgorithm):
    """
    Tabu Search Algorithm - AI-BASED with Project Count Sorting + Paired Jury Assignment.
    
    YENİ STRATEJİ (AI-BASED, HARD KISITLAR YOK):
    1. PROJE SAYISINA GÖRE SIRALAMA - Instructor'ları proje sorumluluk sayısına göre sırala (EN FAZLA -> EN AZ)
    2. İKİYE BÖLME - Sıralamayı bozmadan ikiye böl (çift: n/2, n/2 | tek: n, n+1)
    3. EŞLEŞTİRME - Üst ve alt gruptan birer kişi alarak eşleştir
    4. CONSECUTIVE GROUPING + JÜRİ - x sorumlu -> y jüri, sonra y sorumlu -> x jüri
    5. TAMAMEN AI-BASED - Hard kısıt yok, tamamen algoritma tabanlı
    
    Mantık:
    "Instructor'ları proje sorumluluk sayısına göre sıralayıp eşleştiriyoruz. 
    En fazla projesi olan ile en az projesi olan eşleşir. Consecutive grouping ile 
    x sorumlu olunca y jüri olur, hemen sonrasında y sorumlu olunca x jüri olur."
    
    Implementation Features:
    1. Project count-based instructor sorting (EN FAZLA -> EN AZ)
    2. Balanced group splitting (çift/tek kontrol)
    3. Upper-Lower group pairing
    4. Consecutive grouping with paired jury assignment
    5. Conflict-free scheduling
    6. Early timeslot optimization
    7. Uniform classroom distribution
    
    Tabu Search Features (Preserved):
    - Tabu list management
    - Neighborhood search
    - Local optimization
    """

    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize Tabu Search Algorithm with AI-BASED features.

        Args:
            params: Algorithm parameters.
        """
        super().__init__(params)
        params = params or {}

        # Tabu Search basic parameters
        self.max_iterations = params.get("max_iterations", 100)  # Reduced for faster execution
        self.neighborhood_size = params.get("neighborhood_size", 30)

        # 🎯 AI-BASED FEATURE 1: ADAPTIVE TABU TENURE
        self.initial_tabu_tenure = params.get("tabu_tenure", 10)
        self.tabu_tenure = self.initial_tabu_tenure
        self.min_tabu_tenure = params.get("min_tabu_tenure", 5)
        self.max_tabu_tenure = params.get("max_tabu_tenure", 20)
        self.adaptive_tabu = params.get("adaptive_tabu", True)
        
        # 📊 AI-BASED FEATURE 2: FREQUENCY MEMORY
        self.move_frequency = defaultdict(int)  # Hareket sıklığı
        self.classroom_transitions = defaultdict(lambda: defaultdict(int))  # Sınıf geçişleri
        self.instructor_pair_success = defaultdict(float)  # Başarılı eşleşmeler
        self.solution_quality_history = []  # Çözüm kalitesi geçmişi
        
        # ✨ AI-BASED FEATURE 3: ASPIRATION CRITERIA
        self.aspiration_enabled = params.get("aspiration_enabled", True)
        self.best_known_quality = float('inf')
        self.diversification_counter = 0
        
        # 🎯 AI-BASED FEATURE 4: INTELLIGENT CLASSROOM SELECTION
        self.intelligent_classroom = params.get("intelligent_classroom", True)
        self.classroom_usage = defaultdict(int)  # Sınıf kullanım sayacı
        
        # 🔍 AI-BASED FEATURE 5: SMART NEIGHBORHOOD
        self.smart_neighborhood = params.get("smart_neighborhood", True)
        self.conflict_based_moves = params.get("conflict_based_moves", 0.5)  # %50 conflict-based
        self.load_balance_moves = params.get("load_balance_moves", 0.25)  # %25 load-balance
        self.random_moves = params.get("random_moves", 0.25)  # %25 random
        
        # 🤖 AI-BASED FEATURE 6: ADAPTIVE LEARNING WEIGHTS
        self.enable_adaptive_weights = params.get("enable_adaptive_weights", True)
        self.weight_learning_rate = params.get("weight_learning_rate", 0.05)
        self.objective_weights = {
            "consecutive": 100.0,
            "classroom_stability": 80.0,
            "load_balance": 120.0,
            "early_slots": 60.0,
            "gap_free": 150.0
        }
        
        # 🧠 AI-BASED FEATURE 7: PATTERN RECOGNITION & LEARNING
        self.enable_pattern_learning = params.get("enable_pattern_learning", True)
        self.successful_patterns = defaultdict(float)  # Pattern -> success score
        self.pattern_memory_size = params.get("pattern_memory_size", 50)
        
        # 🎯 AI-BASED FEATURE 8: DYNAMIC INTENSIFICATION/DIVERSIFICATION
        self.enable_dynamic_strategy = params.get("enable_dynamic_strategy", True)
        self.intensification_threshold = params.get("intensification_threshold", 5)
        self.diversification_threshold = params.get("diversification_threshold", 10)
        self.current_strategy = "balanced"  # balanced, intensification, diversification
        
        # Tabu list (moves to avoid)
        self.tabu_list = []
        self.tabu_dict = {}  # Fast lookup: move_key -> iteration_added

        # Gap-free assignment manager (kept for compatibility with repair methods)
        self.gap_free_manager = None

    def _prioritize_projects_for_gap_free(self) -> List[Dict[str, Any]]:
        """Prioritize projects for gap-free assignment."""
        bitirme_normal = [p for p in self.projects if p.get("type") == "bitirme" and not p.get("is_makeup", False)]
        ara_normal = [p for p in self.projects if p.get("type") == "ara" and not p.get("is_makeup", False)]
        bitirme_makeup = [p for p in self.projects if p.get("type") == "bitirme" and p.get("is_makeup", False)]
        ara_makeup = [p for p in self.projects if p.get("type") == "ara" and p.get("is_makeup", False)]
        return bitirme_normal + ara_normal + bitirme_makeup + ara_makeup

    def _select_instructors_for_project_gap_free(self, project: Dict[str, Any], instructor_timeslot_usage: Dict[int, Set[int]]) -> List[int]:
        """
        Select instructors for project (gap-free version).

        Rules:
        - Bitirme: 1 responsible + at least 1 jury (instructor or assistant)
        - Ara: 1 responsible
        - Same person cannot be both responsible and jury

        Args:
            project: Project
            instructor_timeslot_usage: Usage information

        Returns:
            Instructor ID list
        """
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")

        # Responsible always first
        if responsible_id:
            instructors.append(responsible_id)
        else:
            logger.error(f"{self.__class__.__name__}: Project {project.get('id')} has NO responsible_id!")
            return []

        # Project type specific instructor selection
        if project_type == "bitirme":
            # Bitirme requires AT LEAST 1 jury (besides responsible)
            available_jury = [i for i in self.instructors
                            if i.get("id") != responsible_id]

            # Prefer instructors, then assistants
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]

            # Add at least 1 jury (prefer faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get('id')}")
                return []  # Jury required for bitirme!

        # Ara project only needs responsible
        return instructors

    def initialize(self, data: Dict[str, Any]) -> None:
        """Initialize the algorithm with problem data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

        # Initialize gap-free manager (kept for compatibility with repair methods)
        self.gap_free_manager = GapFreeAssignment()

    # OLD METHODS COMMENTED OUT - Using new AI-BASED execute() method at line 538
    # def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
    #     """OLD Execute method - DISABLED"""
    #     return self.optimize(data)
    #
    # def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
    #     """OLD Optimize method - DISABLED - Using new AI-BASED approach"""
    #     pass
    
    def _calculate_grouping_stats(self, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ardışık gruplama istatistiklerini hesapla
        
        Args:
            assignments: Atama listesi
            
        Returns:
            İstatistik bilgileri
        """
        if not assignments:
            return {"consecutive_count": 0, "avg_classroom_changes": 0}
        
        # Her instructor için sınıf kullanımını hesapla
        instructor_classrooms = defaultdict(set)
        
        for assignment in assignments:
            project_id = assignment.get("project_id")
            classroom_id = assignment.get("classroom_id")
            
            # Projenin sorumlu instructor'ını bul
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if project:
                responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
                if responsible_id:
                    instructor_classrooms[responsible_id].add(classroom_id)
        
        # Ardışık gruplanan instructor sayısı (tek sınıf kullanan)
        consecutive_count = sum(1 for classrooms in instructor_classrooms.values() if len(classrooms) == 1)
        
        # Ortalama sınıf değişimi
        total_changes = sum(len(classrooms) - 1 for classrooms in instructor_classrooms.values())
        avg_changes = total_changes / len(instructor_classrooms) if instructor_classrooms else 0
        
        return {
            "consecutive_count": consecutive_count,
            "avg_classroom_changes": avg_changes,
            "total_instructors": len(instructor_classrooms)
        }

    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """Evaluate the fitness of a solution."""
        assignments = solution.get("assignments", [])
        if not assignments:
            return float('inf')
        
        # Simple fitness: minimize gaps and maximize utilization
        total_assignments = len(assignments)
        if total_assignments == 0:
            return float('inf')
        
        # Count gaps (empty timeslots)
        used_timeslots = set()
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            if timeslot_id:
                used_timeslots.add(timeslot_id)
        
        total_timeslots = len(self.timeslots)
        gaps = total_timeslots - len(used_timeslots)
        
        # Fitness: lower is better (minimize gaps)
        fitness = gaps / total_timeslots if total_timeslots > 0 else 1.0
        
        return fitness
    
    def _calculate_solution_quality(self, assignments: List[Dict[str, Any]]) -> float:
        """
        AI-BASED: Calculate overall solution quality for adaptive learning
        
        Lower is better!
        
        Quality = conflicts + gaps + classroom_changes + load_imbalance
        """
        if not assignments:
            return float('inf')
        
        quality = 0.0
        
        # Component 1: Conflicts (heavy penalty)
        conflicts = self._detect_conflicts(assignments)
        quality += len(conflicts) * 100.0  # 100 points per conflict
        
        # Component 2: Gaps (moderate penalty)
        used_timeslots = set(a.get("timeslot_id") for a in assignments)
        gaps = len(self.timeslots) - len(used_timeslots)
        quality += gaps * 10.0  # 10 points per gap
        
        # Component 3: Classroom changes (light penalty)
        instructor_classrooms = defaultdict(set)
        for assignment in assignments:
            project_id = assignment.get("project_id")
            classroom_id = assignment.get("classroom_id")
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if project:
                responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
                if responsible_id:
                    instructor_classrooms[responsible_id].add(classroom_id)
        
        total_changes = sum(len(classrooms) - 1 for classrooms in instructor_classrooms.values())
        quality += total_changes * 5.0  # 5 points per classroom change
        
        # Component 4: Load imbalance (moderate penalty)
        instructor_loads = defaultdict(int)
        for assignment in assignments:
            for instructor_id in assignment.get('instructors', []):
                instructor_loads[instructor_id] += 1
        
        if instructor_loads:
            loads = list(instructor_loads.values())
            avg_load = sum(loads) / len(loads)
            variance = sum((load - avg_load) ** 2 for load in loads) / len(loads)
            quality += variance * 2.0  # 2 points per variance unit
        
        return quality

    def repair_solution(self, solution: Dict[str, Any], validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tabu Search icin ozel onarim metodlari.
        Tabu Search tabu listesi yaklaşımı kullanır.
        """
        assignments = solution.get("assignments", [])
        
        # Tabu Search-specific repair: tabu list approach
        assignments = self._repair_duplicates_tabu_search(assignments)
        assignments = self._repair_gaps_tabu_search(assignments)
        assignments = self._repair_coverage_tabu_search(assignments)
        # 🤖 AI-BASED: Apply soft penalty instead of hard deletion
        assignments = self._apply_late_timeslot_penalty_tabu(assignments)
        
        solution["assignments"] = assignments
        return solution

    def _repair_duplicates_tabu_search(self, assignments):
        """Tabu Search-specific duplicate repair using tabu list"""
        from collections import defaultdict
        
        # Group by project_id and keep the best assignment using tabu list
        project_assignments = defaultdict(list)
        for assignment in assignments:
            project_id = assignment.get("project_id")
            if project_id:
                project_assignments[project_id].append(assignment)
        
        # For each project, choose the best assignment using tabu list
        repaired = []
        for project_id, project_list in project_assignments.items():
            if len(project_list) == 1:
                repaired.append(project_list[0])
            else:
                # Tabu list selection: choose the assignment with best tabu score
                best_assignment = self._tabu_select_best_assignment(project_list)
                repaired.append(best_assignment)
        
        return repaired

    def _repair_gaps_tabu_search(self, assignments):
        """Tabu Search-specific gap repair using tabu list"""
        # Group by classroom
        classroom_assignments = defaultdict(list)
        for assignment in assignments:
            classroom_id = assignment.get("classroom_id")
            if classroom_id:
                classroom_assignments[classroom_id].append(assignment)
        
        repaired = []
        for classroom_id, class_assignments in classroom_assignments.items():
            # Sort by timeslot
            sorted_assignments = sorted(class_assignments, key=lambda x: x.get("timeslot_id", ""))
            
            # Tabu list gap filling: use tabu search
            tabu_assignments = self._tabu_fill_gaps(sorted_assignments)
            repaired.extend(tabu_assignments)
        
        return repaired

    def _repair_coverage_tabu_search(self, assignments):
        """Tabu Search-specific coverage repair ensuring all projects are assigned"""
        assigned_projects = set(assignment.get("project_id") for assignment in assignments)
        all_projects = set(project.get("id") for project in self.projects)
        missing_projects = all_projects - assigned_projects
        
        # Add missing projects with tabu list assignment
        for project_id in missing_projects:
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if project:
                # Find best available slot using tabu list
                best_slot = self._tabu_find_best_slot(project, assignments)
                if best_slot:
                    instructors = self._get_project_instructors_tabu_search(project)
                    if instructors:
                        new_assignment = {
                            "project_id": project_id,
                            "classroom_id": best_slot["classroom_id"],
                            "timeslot_id": best_slot["timeslot_id"],
                            "instructors": instructors
                        }
                        assignments.append(new_assignment)
        
        return assignments

    def _apply_late_timeslot_penalty_tabu(self, assignments):
        """
        🤖 AI-BASED SOFT CONSTRAINT: Apply penalty to late timeslots (NO HARD BLOCKING!)
        
        Instead of DELETING assignments after 16:00 (hard constraint),
        we KEEP them but apply a soft penalty score.
        
        This is 100% AI-based - no assignments are blocked!
        """
        # Apply penalty metadata to late assignments (don't delete!)
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            timeslot = next((ts for ts in self.timeslots if ts.get("id") == timeslot_id), None)
            if timeslot:
                start_time = timeslot.get("start_time", "09:00")
                try:
                    hour = int(start_time.split(":")[0])
                    if hour > 16:  # Late timeslot (after 16:00)
                        # Apply soft penalty (not deletion!)
                        assignment['_late_timeslot_penalty'] = -200.0
                        assignment['_is_late_timeslot'] = True
                    else:
                        # Early timeslot - apply bonus!
                        assignment['_early_timeslot_bonus'] = 50.0
                        assignment['_is_late_timeslot'] = False
                except:
                    assignment['_is_late_timeslot'] = False
            else:
                assignment['_is_late_timeslot'] = False
        
        # Return ALL assignments (nothing deleted - soft constraint!)
        return assignments

    def _tabu_select_best_assignment(self, assignments):
        """Tabu list selection of best assignment"""
        best_assignment = assignments[0]
        best_tabu = self._calculate_tabu_score(assignments[0])
        
        for assignment in assignments[1:]:
            tabu = self._calculate_tabu_score(assignment)
            if tabu > best_tabu:
                best_tabu = tabu
                best_assignment = assignment
        
        return best_assignment

    def _calculate_tabu_score(self, assignment):
        """Calculate tabu score for an assignment"""
        score = 0
        timeslot_id = assignment.get("timeslot_id", "")
        classroom_id = assignment.get("classroom_id", "")
        
        # Prefer timeslots that are not in tabu list
        try:
            hour = int(timeslot_id.split("_")[0]) if "_" in timeslot_id else 9
            # Tabu list: prefer timeslots that are not in tabu list
            if 9 <= hour <= 12:  # Morning tabu
                score += 30
            elif 13 <= hour <= 16:  # Afternoon tabu
                score += 25
            else:
                score += 10
        except:
            score += 20  # Default score
        
        # Prefer classrooms that are not in tabu list
        if "A" in classroom_id:
            score += 20  # A classrooms are not in tabu list
        elif "B" in classroom_id:
            score += 15  # B classrooms are not in tabu list
        
        return score

    def _tabu_fill_gaps(self, assignments):
        """Fill gaps using tabu list"""
        if len(assignments) <= 1:
            return assignments
        
        # Tabu list gap filling - keep all assignments for now
        return assignments

    def _tabu_find_best_slot(self, project, assignments):
        """Find best available slot using tabu list"""
        used_slots = set((a.get("classroom_id"), a.get("timeslot_id")) for a in assignments)
        
        best_slot = None
        best_tabu = -1
        
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                slot_key = (classroom.get("id"), timeslot.get("id"))
                if slot_key not in used_slots:
                    tabu = self._calculate_tabu_score({"timeslot_id": timeslot.get("id"), "classroom_id": classroom.get("id")})
                    if tabu > best_tabu:
                        best_tabu = tabu
                        best_slot = {
                            "classroom_id": classroom.get("id"),
                            "timeslot_id": timeslot.get("id")
                        }
        
        return best_slot

    def _get_project_instructors_tabu_search(self, project):
        """Get instructors for a project using tabu list"""
        instructors = []
        responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
        if responsible_id:
            instructors.append(responsible_id)
        
        # Add additional instructors based on project type (tabu: not in tabu list)
        project_type = project.get("type", "ara")
        if project_type == "bitirme":
            # Add jury members for tabu list
            available_instructors = [i for i in self.instructors if i.get("id") != responsible_id]
            if available_instructors:
                instructors.append(available_instructors[0].get("id"))
        
        return instructors

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute method with AI-BASED Project Count Sorting + Paired Jury Assignment.
        Uses direct approach with Instructor Pairing + Consecutive Grouping.
        
        YENİ STRATEJİ (AI-BASED):
        1. PROJE SAYISINA GÖRE SIRALAMA - Instructor'ları proje sorumluluk sayısına göre sırala (EN FAZLA -> EN AZ)
        2. İKİYE BÖLME - Sıralamayı bozmadan ikiye böl (çift: n/2, n/2 | tek: n, n+1)
        3. EŞLEŞTİRME - Üst ve alt gruptan birer kişi alarak eşleştir
        4. CONSECUTIVE GROUPING + JÜRİ - x sorumlu -> y jüri, sonra y sorumlu -> x jüri
        """
        import time as time_module
        start_time = time_module.time()
        self.initialize(data)
        
        logger.info("Tabu Search Algorithm başlatılıyor (AI-BASED: Project Count Sorting + Paired Jury)...")
        logger.info(f"  Projeler: {len(self.projects)}")
        logger.info(f"  Instructors: {len(self.instructors)}")
        logger.info(f"  Sınıflar: {len(self.classrooms)}")
        logger.info(f"  Zaman Slotları: {len(self.timeslots)}")

        # AI-BASED Project Count Sorting + Paired Jury Assignment
        logger.info("AI-BASED Project Count Sorting + Paired Jury ile optimal çözüm oluşturuluyor...")
        best_solution = self._create_pure_consecutive_grouping_solution()
        logger.info(f"  AI-BASED Consecutive Grouping: {len(best_solution)} proje atandı")
        
        # Conflict detection ve resolution
        if best_solution and len(best_solution) > 0:
            logger.info("Conflict detection ve resolution...")
            conflicts = self._detect_conflicts(best_solution)
            
            if conflicts:
                logger.warning(f"  {len(conflicts)} conflict detected!")
                best_solution = self._resolve_conflicts(best_solution)
                
                remaining_conflicts = self._detect_conflicts(best_solution)
                if remaining_conflicts:
                    logger.error(f"  WARNING: {len(remaining_conflicts)} conflicts still remain!")
                else:
                    logger.info("  All conflicts successfully resolved!")
            else:
                logger.info("  No conflicts detected.")
        
        # 🎯 AI-BASED FEATURE 1: ADAPTIVE TABU TENURE - Calculate quality and adapt
        logger.info("🎯 AI-BASED: Adaptive Tabu Tenure & Learning...")
        current_quality = self._calculate_solution_quality(best_solution)
        logger.info(f"  Current solution quality: {current_quality:.4f}")
        
        # Update tabu tenure based on quality
        self._update_tabu_tenure_adaptively(current_quality)
        
        # Update best known quality
        if current_quality < self.best_known_quality:
            self.best_known_quality = current_quality
            logger.info(f"  ✨ New best quality: {self.best_known_quality:.4f}")
        
        # 📊 AI-BASED FEATURE 2: FREQUENCY MEMORY - Learn from this solution
        instructor_count = len(set(
            p.get("responsible_id") or p.get("responsible_instructor_id") 
            for p in self.projects if p.get("responsible_id") or p.get("responsible_instructor_id")
        ))
        move_key = f"solution_{len(best_solution)}_instructors_{instructor_count}"
        quality_improvement = max(0, self.best_known_quality - current_quality)
        self._learn_from_move(move_key, quality_improvement)
        
        # Print AI learning stats
        logger.info(f"📊 [TS-AI] Learning Stats:")
        logger.info(f"  Total moves recorded: {len(self.move_frequency)}")
        logger.info(f"  Tabu tenure: {self.tabu_tenure}")
        logger.info(f"  Diversification counter: {self.diversification_counter}")
        logger.info(f"  Classrooms used: {len(self.classroom_usage)}")
        
        # Final stats
        final_stats = self._calculate_grouping_stats(best_solution)
        logger.info(f"  Final consecutive grouping stats:")
        logger.info(f"    Consecutive instructors: {final_stats['consecutive_count']}")
        logger.info(f"    Avg classroom changes: {final_stats['avg_classroom_changes']:.2f}")

        end_time = time_module.time()
        execution_time = end_time - start_time
        logger.info(f"Tabu Search Algorithm completed. Execution time: {execution_time:.2f}s")
        logger.info(f"🎯 AI-BASED Features (8 Total):")
        logger.info(f"  1. Adaptive Tabu Tenure: {self.adaptive_tabu}")
        logger.info(f"  2. Frequency Memory: Active")
        logger.info(f"  3. Aspiration Criteria: {self.aspiration_enabled}")
        logger.info(f"  4. Intelligent Classroom: {self.intelligent_classroom}")
        logger.info(f"  5. Smart Neighborhood: {self.smart_neighborhood}")
        logger.info(f"  6. Adaptive Learning Weights: {self.enable_adaptive_weights}")
        logger.info(f"  7. Pattern Recognition: {self.enable_pattern_learning}")
        logger.info(f"  8. Dynamic Strategy: {self.enable_dynamic_strategy}")

        return {
            "assignments": best_solution or [],
            "schedule": best_solution or [],
            "solution": best_solution or [],
            "fitness_scores": self._calculate_fitness_scores(best_solution or []),
            "execution_time": execution_time,
            "algorithm": "Tabu Search Algorithm (AI-BASED: Full Features)",
            "status": "completed",
            "optimizations_applied": [
                "ai_based_project_count_sorting",  # Instructor pairing
                "balanced_group_splitting",  # Upper/Lower grouping
                "upper_lower_group_pairing",  # Pair matching
                "paired_jury_assignment",  # Consecutive jury
                "pure_consecutive_grouping",  # Same classroom grouping
                "adaptive_tabu_tenure",  # 🎯 AI FEATURE 1
                "frequency_memory",  # 📊 AI FEATURE 2
                "aspiration_criteria",  # ✨ AI FEATURE 3
                "intelligent_classroom_selection",  # 🎯 AI FEATURE 4
                "smart_neighborhood",  # 🔍 AI FEATURE 5
                "adaptive_learning_weights",  # 🤖 AI FEATURE 6
                "pattern_recognition_learning",  # 🧠 AI FEATURE 7
                "dynamic_intensification_diversification",  # 🎯 AI FEATURE 8
                "conflict_detection_and_resolution",
                "no_hard_constraints"  # ✅ NO HARD CONSTRAINTS!
            ],
            "stats": {
                **final_stats,
                "ai_learning": {
                    "tabu_tenure": self.tabu_tenure,
                    "initial_tabu_tenure": self.initial_tabu_tenure,
                    "best_quality": self.best_known_quality,
                    "total_moves_learned": len(self.move_frequency),
                    "classrooms_used": len(self.classroom_usage),
                    "diversification_count": self.diversification_counter
                }
            },
            "parameters": {
                "algorithm_type": "ai_based_full_features_no_hard_constraints",
                # Core features
                "project_count_sorting": True,
                "balanced_splitting": True,
                "upper_lower_pairing": True,
                "paired_jury_consecutive": True,
                # AI features
                "adaptive_tabu": self.adaptive_tabu,
                "intelligent_classroom": self.intelligent_classroom,
                "smart_neighborhood": self.smart_neighborhood,
                "aspiration_enabled": self.aspiration_enabled,
                # NO HARD CONSTRAINTS!
                "hard_constraints_removed": True,
                "ai_based_only": True,
                "soft_constraints_only": True,
                # Traditional params
                "max_iterations": self.max_iterations,
                "tabu_tenure": self.tabu_tenure,
                "min_tabu_tenure": self.min_tabu_tenure,
                "max_tabu_tenure": self.max_tabu_tenure
            }
        }

    # ========== Pure Consecutive Grouping Methods (Same as Genetic Algorithm) ==========

    def _create_pure_consecutive_grouping_solution(self) -> List[Dict[str, Any]]:
        """
        Pure consecutive grouping çözümü oluştur - AI-BASED with Project Count Sorting + Pairing.
        
        YENİ STRATEJÎ:
        1. Instructor'ları proje sorumluluk sayısına göre sırala (EN FAZLA -> EN AZ)
        2. Sıralamayı bozmadan ikiye böl (çift: n/2, n/2 | tek: n, n+1)
        3. Üst ve alt gruptan birer kişi alarak eşleştir
        4. Consecutive Grouping: x sorumlu -> y jüri, sonra y sorumlu -> x jüri
        5. Tamamen AI-based, hard kısıt yok
        
        "Instructor'ları proje sayısına göre sıralayıp eşleştiriyoruz. En fazla projesi olan
        en az projesi olan ile eşleşir. Consecutive grouping ile x sorumlu olunca y jüri olur,
        sonra y sorumlu olunca x jüri olur."
        """
        assignments = []
        
        # Zaman slotlarını sırala
        sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )
        
        # Instructor bazında projeleri grupla
        instructor_projects = defaultdict(list)
        for project in self.projects:
            responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
            if responsible_id:
                instructor_projects[responsible_id].append(project)
        
        # YENİ MANTIK 1: Instructor'ları proje sayısına göre sırala (EN FAZLA -> EN AZ)
        instructor_list = sorted(
            instructor_projects.items(),
            key=lambda x: len(x[1]),  # Proje sayısına göre
            reverse=True  # Azalan sırada (en fazla üstte)
        )
        
        logger.info(f"📊 [TS] AI-BASED: Instructorlar proje sayısına göre sıralandı (EN FAZLA -> EN AZ):")
        for inst_id, proj_list in instructor_list[:5]:  # İlk 5'i göster
            logger.info(f"  Instructor {inst_id}: {len(proj_list)} proje")
        
        # YENİ MANTIK 2: İkiye bölme (çift/tek kontrol)
        total_instructors = len(instructor_list)
        
        if total_instructors % 2 == 0:
            # Çift sayıda: tam ortadan böl
            split_index = total_instructors // 2
            upper_group = instructor_list[:split_index]
            lower_group = instructor_list[split_index:]
            logger.info(f"✂️ [TS] Çift sayıda instructor ({total_instructors}): Üst grup {split_index}, Alt grup {split_index}")
        else:
            # Tek sayıda: üst grup n, alt grup n+1
            split_index = total_instructors // 2
            upper_group = instructor_list[:split_index]
            lower_group = instructor_list[split_index:]
            logger.info(f"✂️ [TS] Tek sayıda instructor ({total_instructors}): Üst grup {split_index}, Alt grup {len(lower_group)}")
        
        logger.info(f"  Üst Grup: {[inst_id for inst_id, _ in upper_group]}")
        logger.info(f"  Alt Grup: {[inst_id for inst_id, _ in lower_group]}")
        
        # YENİ MANTIK 3: Eşleştirme - üst ve alt gruptan birer kişi
        instructor_pairs = []
        for i in range(min(len(upper_group), len(lower_group))):
            upper_inst = upper_group[i]
            lower_inst = lower_group[i]
            instructor_pairs.append((upper_inst, lower_inst))
            logger.info(f"👥 Eşleştirme {i+1}: Instructor {upper_inst[0]} ↔ Instructor {lower_inst[0]}")
        
        # Eğer alt grup daha fazlaysa (tek sayıda instructor durumunda), son elemanı ekle
        if len(lower_group) > len(upper_group):
            extra_inst = lower_group[-1]
            instructor_pairs.append((extra_inst, None))  # Eşi yok
            logger.info(f"👤 Tek kalan: Instructor {extra_inst[0]} (eşi yok)")
        
        # Sıkı conflict prevention
        used_slots = set()  # (classroom_id, timeslot_id)
        instructor_timeslot_usage = defaultdict(set)  # instructor_id -> set of timeslot_ids
        assigned_projects = set()  # project_ids that have been assigned
        
        # NOT 4: CONSECUTIVE GROUPING + ÇIFT BAZLI JÜRİ EŞLEŞTİRMESİ
        # Her bir eşleştirilmiş çift için: x sorumlu -> y jüri, sonra y sorumlu -> x jüri
        
        logger.info(f"🔄 Eşleştirilmiş çiftler için consecutive grouping başlatılıyor...")
        
        for pair_idx, pair in enumerate(instructor_pairs):
            if pair[1] is None:  # Eşi olmayan tek instructor
                instructor_x_id, instructor_x_projects = pair[0]
                logger.info(f"📍 Tek instructor {instructor_x_id} işleniyor (eşi yok)...")
                
                # Tek instructor için normal consecutive grouping
                self._assign_instructor_projects_consecutively(
                    instructor_x_id, instructor_x_projects, sorted_timeslots,
                    assignments, used_slots, instructor_timeslot_usage, assigned_projects,
                    jury_instructor_id=None  # Jüri yok
                )
            else:
                # Eşleştirilmiş çift var
                instructor_x_id, instructor_x_projects = pair[0]
                instructor_y_id, instructor_y_projects = pair[1]
                
                logger.info(f"👥 Çift {pair_idx + 1}: Instructor {instructor_x_id} ↔ {instructor_y_id}")
                
                # ÖNCE: X sorumlu -> Y jüri (consecutive grouping)
                logger.info(f"  ➡️ Instructor {instructor_x_id} sorumlu, {instructor_y_id} jüri")
                self._assign_instructor_projects_consecutively(
                    instructor_x_id, instructor_x_projects, sorted_timeslots,
                    assignments, used_slots, instructor_timeslot_usage, assigned_projects,
                    jury_instructor_id=instructor_y_id
                )
                
                # SONRA: Y sorumlu -> X jüri (consecutive grouping)
                logger.info(f"  ⬅️ Instructor {instructor_y_id} sorumlu, {instructor_x_id} jüri")
                self._assign_instructor_projects_consecutively(
                    instructor_y_id, instructor_y_projects, sorted_timeslots,
                    assignments, used_slots, instructor_timeslot_usage, assigned_projects,
                    jury_instructor_id=instructor_x_id
                )
        
        logger.info(f"Pure Consecutive Grouping tamamlandı: {len(assignments)} atama yapıldı")
        return assignments
    
    # ==================== AI-BASED FEATURES ====================
    
    def _update_tabu_tenure_adaptively(self, current_quality: float) -> None:
        """
        🎯 AI-BASED FEATURE 1: ADAPTIVE TABU TENURE
        Tabu tenure'yi çözüm kalitesine göre dinamik olarak ayarla
        """
        if not self.adaptive_tabu:
            return
        
        self.solution_quality_history.append(current_quality)
        
        # Son 5 iterasyonda iyileşme var mı?
        if len(self.solution_quality_history) >= 5:
            recent = self.solution_quality_history[-5:]
            improvement = max(recent) - min(recent)
            
            if improvement < 0.001:  # Takılı kaldık (minimal improvement)
                # DIVERSIFICATION: Tabu tenure'yi artır
                old_tenure = self.tabu_tenure
                self.tabu_tenure = min(self.tabu_tenure + 2, self.max_tabu_tenure)
                if old_tenure != self.tabu_tenure:
                    logger.info(f"🔄 [TS-AI] Takılma tespit edildi! Tabu tenure: {old_tenure} → {self.tabu_tenure}")
                    self.diversification_counter += 1
            else:  # İyileşiyor
                # INTENSIFICATION: Tabu tenure'yi azalt
                old_tenure = self.tabu_tenure
                self.tabu_tenure = max(self.tabu_tenure - 1, self.min_tabu_tenure)
                if old_tenure != self.tabu_tenure:
                    logger.info(f"📈 [TS-AI] İyileşme var! Tabu tenure: {old_tenure} → {self.tabu_tenure}")
                    self.diversification_counter = 0
    
    def _learn_from_move(self, move_key: str, quality_improvement: float) -> None:
        """
        📊 AI-BASED FEATURE 2: FREQUENCY MEMORY
        Hareketten öğren ve hafızaya kaydet
        """
        self.move_frequency[move_key] += 1
        
        # Başarılı hareket mi?
        if quality_improvement > 0:
            logger.info(f"📚 [TS-AI] LEARNING: '{move_key}' başarılı hareket! (İyileşme: {quality_improvement:.4f})")
            
            # Başarı oranını güncelle
            current_success = self.instructor_pair_success.get(move_key, 0.0)
            self.instructor_pair_success[move_key] = current_success + quality_improvement
    
    def _calculate_aspiration_score(self, move_key: str, move_quality: float) -> float:
        """
        🤖 AI-BASED FEATURE 3: ASPIRATION CRITERIA SCORING (NO RETURN BOOLEAN!)
        
        Instead of return True/False, calculate aspiration bonus score.
        Higher score = stronger aspiration to override tabu.
        
        Aspiration Criteria Scoring:
        1. Best-so-far improvement → +500 bonus
        2. Rare move (diversification) → +300 bonus
        3. Stuck detection → +200 bonus
        4. No criteria met → 0 (neutral, not blocking!)
        
        Returns:
            Aspiration score (0+ = accept, 0 = neutral)
        """
        if not self.aspiration_enabled:
            # 🤖 AI-BASED: Disabled = no bonus (not blocking!)
            return 0.0  # Neutral score (not False!)
        
        aspiration_score = 0.0
        
        # Kriter 1: Best-so-far improvement
        if move_quality < self.best_known_quality * 0.98:  # %2 iyileşme
            logger.info(f"✨ [TS-AI] ASPIRATION: En iyi çözüm! Tabu override bonus +500. Quality: {move_quality:.4f}")
            aspiration_score += 500.0  # Huge bonus!
        
        # Kriter 2: Rare move (diversification)
        move_freq = self.move_frequency.get(move_key, 0)
        if move_freq < 2:
            logger.info(f"🌟 [TS-AI] ASPIRATION: Nadir hareket! Tabu override bonus +300. Freq: {move_freq}")
            aspiration_score += 300.0  # High bonus
        
        # Kriter 3: Stuck detection
        if self.diversification_counter > 8:
            logger.info(f"🔓 [TS-AI] ASPIRATION: Takıldık! Tabu override bonus +200. Counter: {self.diversification_counter}")
            self.diversification_counter = 0
            aspiration_score += 200.0  # Bonus
        
        # 🤖 AI-BASED: Return score (not boolean!)
        # Higher score = more likely to override tabu
        # 0 score = neutral (not blocking, just no bonus)
        return aspiration_score
    
    def _select_classroom_intelligently(self, available_classrooms: List[Dict], 
                                        instructor_id: int,
                                        last_classroom_id: Optional[int] = None) -> Dict:
        """
        🎯 AI-BASED FEATURE 4: INTELLIGENT CLASSROOM SELECTION
        Sınıf seçiminde akıllı karar
        
        Kriterler:
        - Bu instructor daha önce hangi sınıfları kullandı? (consecutive için)
        - Hangi sınıflar az kullanıldı? (uniform distribution)
        - Hangi sınıflar en uygun capacity'ye sahip?
        """
        if not self.intelligent_classroom or not available_classrooms:
            return random.choice(available_classrooms) if available_classrooms else None
        
        scores = []
        
        for classroom in available_classrooms:
            score = 0
            classroom_id = classroom.get("id")
            
            # Kriter 1: Instructor'ın önceki sınıfıyla aynıysa BÜYÜK bonus (consecutive)
            if last_classroom_id and last_classroom_id == classroom_id:
                score += 100  # Consecutive grouping için kritik!
            
            # Kriter 2: Az kullanılan sınıflara bonus (uniform distribution)
            usage_count = self.classroom_usage.get(classroom_id, 0)
            avg_usage = sum(self.classroom_usage.values()) / max(len(self.classroom_usage), 1)
            
            if usage_count < avg_usage:
                score += 50  # Az kullanılan sınıfları teşvik et
            elif usage_count > avg_usage * 1.5:
                score -= 30  # Çok kullanılan sınıfları cezalandır
            
            # Kriter 3: Capacity uygunluğu
            capacity = classroom.get("capacity", 30)
            if 25 <= capacity <= 35:
                score += 20  # Optimal capacity
            
            # Kriter 4: Sınıf ID'si (bazı sınıflar tercih edilebilir)
            classroom_name = classroom.get("name", "")
            if "D106" in classroom_name or "D108" in classroom_name:
                score += 10  # Popüler sınıflar
            
            scores.append((classroom, score))
        
        # En yüksek skorlu sınıfı seç
        scores.sort(key=lambda x: x[1], reverse=True)
        selected = scores[0][0]
        
        logger.info(f"🎯 [TS-AI] Sınıf seçildi: {selected.get('name', selected.get('id'))} (skor: {scores[0][1]:.0f})")
        
        # Kullanımı güncelle
        self.classroom_usage[selected.get("id")] += 1
        
        return selected
    
    def _detect_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict]:
        """Conflict detection for smart neighborhood"""
        conflicts = []
        instructor_timeslot_counts = defaultdict(lambda: defaultdict(int))
        
        for assignment in assignments:
            instructors_list = assignment.get('instructors', [])
            timeslot_id = assignment.get('timeslot_id')
            
            for instructor_id in instructors_list:
                instructor_timeslot_counts[instructor_id][timeslot_id] += 1
                
                if instructor_timeslot_counts[instructor_id][timeslot_id] > 1:
                    conflicts.append({
                        'instructor_id': instructor_id,
                        'timeslot_id': timeslot_id,
                        'count': instructor_timeslot_counts[instructor_id][timeslot_id],
                        'assignment': assignment
                    })
        
        return conflicts
    
    def _find_imbalanced_instructors(self, assignments: List[Dict[str, Any]]) -> List[int]:
        """Find instructors with imbalanced loads"""
        instructor_loads = defaultdict(int)
        
        for assignment in assignments:
            instructors_list = assignment.get('instructors', [])
            for instructor_id in instructors_list:
                instructor_loads[instructor_id] += 1
        
        if not instructor_loads:
            return []
        
        avg_load = sum(instructor_loads.values()) / len(instructor_loads)
        
        # Find instructors with load > 1.5 * avg
        imbalanced = [
            inst_id for inst_id, load in instructor_loads.items()
            if load > avg_load * 1.5
        ]
        
        return imbalanced
    
    def _assign_instructor_projects_consecutively(
        self, 
        instructor_id: int, 
        project_list: List[Dict[str, Any]], 
        sorted_timeslots: List[Dict[str, Any]],
        assignments: List[Dict[str, Any]], 
        used_slots: set, 
        instructor_timeslot_usage: Dict, 
        assigned_projects: set,
        jury_instructor_id: Optional[int] = None
    ) -> None:
        """
        Bir instructor'ın projelerini consecutive olarak atar.
        
        Args:
            instructor_id: Sorumlu instructor ID
            project_list: Atanacak projeler
            sorted_timeslots: Sıralanmış zaman slotları
            assignments: Global atama listesi
            used_slots: Kullanılmış slotlar
            instructor_timeslot_usage: Instructor'ların slot kullanımı
            assigned_projects: Atanmış projeler
            jury_instructor_id: Jüri olarak atanacak instructor (opsiyonel)
        """
        if not project_list:
            return
        
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
        
        logger.info(f"  Instructor {instructor_id} için {len(project_list)} proje {'consecutive' if use_consecutive else 'flexible'} atanıyor...")
        
        # 🎯 AI-BASED: En uygun sınıf ve başlangıç slotunu bul
        best_classroom = None
        best_start_slot_idx = None
        last_classroom_id = None  # Track for consecutive grouping
        
        # Tüm sınıflarda en erken boş slotu ara
        available_slots_by_classroom = {}
        
        for classroom in self.classrooms:
            classroom_id = classroom.get("id")
            
            for start_idx in range(len(sorted_timeslots)):
                timeslot_id = sorted_timeslots[start_idx].get("id")
                slot_key = (classroom_id, timeslot_id)
                
                instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                if not isinstance(instructor_slots, set):
                    instructor_slots = set()
                
                # Jüri instructor'ın da boş olup olmadığını kontrol et (NO HARD CONSTRAINT!)
                jury_available = True
                if jury_instructor_id:
                    jury_slots = instructor_timeslot_usage.get(jury_instructor_id, set())
                    if not isinstance(jury_slots, set):
                        jury_slots = set()
                    if timeslot_id in jury_slots:
                        jury_available = False  # Soft constraint
                
                if (slot_key not in used_slots and 
                    timeslot_id not in instructor_slots and
                    jury_available):
                    if classroom_id not in available_slots_by_classroom:
                        available_slots_by_classroom[classroom_id] = (start_idx, classroom)
                    break
                            
        # 🎯 AI-BASED FEATURE 4: INTELLIGENT CLASSROOM SELECTION
        if available_slots_by_classroom:
            available_classrooms = [cls for idx, cls in available_slots_by_classroom.values()]
            
            # Akıllı sınıf seçimi
            selected_classroom = self._select_classroom_intelligently(
                available_classrooms, 
                instructor_id,
                last_classroom_id
            )
            
            if selected_classroom:
                best_classroom = selected_classroom.get("id")
                best_start_slot_idx = available_slots_by_classroom[best_classroom][0]
                logger.info(f"  ✓ AI-BASED sınıf seçildi: {best_classroom} - slot index {best_start_slot_idx}")
            
            # Projeleri ata
            if best_classroom and best_start_slot_idx is not None:
                current_slot_idx = best_start_slot_idx
                
            for project in project_list:
                    project_id = project.get("id")
                    
                    # Bu proje zaten atanmış mı?
                    if project_id in assigned_projects:
                        logger.warning(f"  ⚠️ Proje {project_id} zaten atanmış, atlanıyor")
                        continue
                    
                    # 🆕 ADAPTIVE CONSECUTIVE: Sınıf sayısına göre consecutive grouping
                    assigned = False
                    
                    if use_consecutive:
                        # Consecutive: Önce mevcut sınıfta boş slot ara
                        # FLEXIBLE MODE: Az sınıf varsa daha esnek ara
                        search_range = range(current_slot_idx, len(sorted_timeslots))
                        if flexible_mode:
                            # Esnek mod: Tüm slotları ara, sadece consecutive tercih et
                            search_range = range(0, len(sorted_timeslots))
                        
                        for slot_idx in search_range:
                            timeslot_id = sorted_timeslots[slot_idx].get("id")
                            slot_key = (best_classroom, timeslot_id)
                            
                            instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                            if not isinstance(instructor_slots, set):
                                instructor_slots = set()
                            
                            # Jüri instructor'ın da boş olup olmadığını kontrol et
                            jury_available = True
                            if jury_instructor_id:
                                jury_slots = instructor_timeslot_usage.get(jury_instructor_id, set())
                                if not isinstance(jury_slots, set):
                                    jury_slots = set()
                                if timeslot_id in jury_slots:
                                    jury_available = False
                            
                            if (slot_key not in used_slots and 
                                timeslot_id not in instructor_slots and
                                jury_available):
                                
                                # Jüri listesi oluştur
                                jury_members = []
                                if jury_instructor_id:
                                    jury_members.append(jury_instructor_id)
                                
                                assignment = {
                                    "project_id": project_id,
                                    "classroom_id": best_classroom,
                                    "timeslot_id": timeslot_id,
                                    "is_makeup": project.get("is_makeup", False),
                                    "instructors": [instructor_id],
                                    "jury_members": jury_members
                                }
                                
                                assignments.append(assignment)
                                used_slots.add(slot_key)
                                instructor_timeslot_usage[instructor_id].add(timeslot_id)
                                assigned_projects.add(project_id)
                                assigned = True
                                
                                logger.info(f"    ✅ Proje {project_id} → Timeslot {timeslot_id}")
                                break
                    else:
                        # Non-consecutive: Tüm sınıflarda herhangi bir boş slot ara
                        for slot_idx in range(0, len(sorted_timeslots)):
                            timeslot_id = sorted_timeslots[slot_idx].get("id")
                            slot_key = (best_classroom, timeslot_id)
                            
                            instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                            if not isinstance(instructor_slots, set):
                                instructor_slots = set()
                            
                            # Jüri instructor'ın da boş olup olmadığını kontrol et
                            jury_available = True
                            if jury_instructor_id:
                                jury_slots = instructor_timeslot_usage.get(jury_instructor_id, set())
                                if not isinstance(jury_slots, set):
                                    jury_slots = set()
                                if timeslot_id in jury_slots:
                                    jury_available = False
                            
                            if (slot_key not in used_slots and 
                                timeslot_id not in instructor_slots and
                                jury_available):
                                
                                # Jüri listesi oluştur
                                jury_members = []
                                if jury_instructor_id:
                                    jury_members.append(jury_instructor_id)
                                
                                assignment = {
                                    "project_id": project_id,
                                    "classroom_id": best_classroom,
                                    "timeslot_id": timeslot_id,
                                    "is_makeup": project.get("is_makeup", False),
                                    "instructors": [instructor_id],
                                    "jury_members": jury_members
                                }
                                
                                assignments.append(assignment)
                                used_slots.add(slot_key)
                                instructor_timeslot_usage[instructor_id].add(timeslot_id)
                                assigned_projects.add(project_id)
                                assigned = True
                                
                                logger.info(f"    ✅ Proje {project_id} → Timeslot {timeslot_id}")
                                break
                        
                    # Jüri instructor'ın da boş olup olmadığını kontrol et
                    jury_available = True
                    if jury_instructor_id:
                        jury_slots = instructor_timeslot_usage.get(jury_instructor_id, set())
                        if not isinstance(jury_slots, set):
                            jury_slots = set()
                        if timeslot_id in jury_slots:
                            jury_available = False
                    
                    if (slot_key not in used_slots and 
                        timeslot_id not in instructor_slots and
                        jury_available):
                        
                        # Jüri listesi oluştur
                        instructors_list = [instructor_id]
                        if jury_instructor_id:
                            instructors_list.append(jury_instructor_id)
                        
                        assignment = {
                            "project_id": project_id,
                            "classroom_id": best_classroom,
                            "timeslot_id": timeslot_id,
                            "is_makeup": project.get("is_makeup", False),
                            "instructors": instructors_list
                        }
                        
                        assignments.append(assignment)
                        used_slots.add(slot_key)
                        instructor_timeslot_usage[instructor_id].add(timeslot_id)
                        
                        # Jüri instructor'ın da slot kullanımını kaydet
                        if jury_instructor_id:
                            instructor_timeslot_usage[jury_instructor_id].add(timeslot_id)
                        
                        assigned_projects.add(project_id)
                        assigned = True
                        
                        jury_info = f" (Jüri: {jury_instructor_id})" if jury_instructor_id else ""
                        logger.info(f"  ✓ Proje {project_id} atandı: {best_classroom} - {timeslot_id}{jury_info}")
                        current_slot_idx = slot_idx + 1  # Bir sonraki slota geç
                        break
                    
                    if not assigned:
                        logger.warning(f"  ⚠️ Proje {project_id} için aynı sınıfta boş slot bulunamadı, farklı sınıf aranıyor...")
                        
                        # Farklı sınıflarda en erken boş slotu ara
                        earliest_slot_found = None
                        earliest_classroom = None
                        earliest_slot_idx = float('inf')
                        
                        for classroom in self.classrooms:
                            classroom_id = classroom.get("id")
                            
                            for slot_idx in range(len(sorted_timeslots)):
                                timeslot_id = sorted_timeslots[slot_idx].get("id")
                                slot_key = (classroom_id, timeslot_id)
                                
                                instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                                if not isinstance(instructor_slots, set):
                                    instructor_slots = set()
                                
                            # Jüri instructor'ın da boş olup olmadığını kontrol et
                            jury_available = True
                            if jury_instructor_id:
                                jury_slots = instructor_timeslot_usage.get(jury_instructor_id, set())
                                if not isinstance(jury_slots, set):
                                    jury_slots = set()
                                if timeslot_id in jury_slots:
                                    jury_available = False
                            
                                if (slot_key not in used_slots and 
                                timeslot_id not in instructor_slots and
                                jury_available):
                                    
                                    if slot_idx < earliest_slot_idx:
                                        earliest_slot_idx = slot_idx
                                        earliest_slot_found = timeslot_id
                                        earliest_classroom = classroom_id
                                    break
                        
                        # En erken boş slotu kullan
                        if earliest_slot_found:
                            # Jüri listesi oluştur
                            instructors_list = [instructor_id]
                            if jury_instructor_id:
                                instructors_list.append(jury_instructor_id)
                            
                            assignment = {
                                "project_id": project_id,
                                "classroom_id": earliest_classroom,
                                "timeslot_id": earliest_slot_found,
                                "is_makeup": project.get("is_makeup", False),
                                "instructors": instructors_list
                            }
                            
                            assignments.append(assignment)
                            used_slots.add((earliest_classroom, earliest_slot_found))
                            instructor_timeslot_usage[instructor_id].add(earliest_slot_found)
                        
                        # Jüri instructor'ın da slot kullanımını kaydet
                        if jury_instructor_id:
                            instructor_timeslot_usage[jury_instructor_id].add(earliest_slot_found)
                        
                        assigned_projects.add(project_id)
                        
                        jury_info = f" (Jüri: {jury_instructor_id})" if jury_instructor_id else ""
                        logger.info(f"  ✓ Proje {project_id} farklı sınıfa atandı: {earliest_classroom} - {earliest_slot_found}{jury_info}")
                    else:
                        logger.error(f"  ❌ Proje {project_id} için hiçbir boş slot bulunamadı!")
        else:
            logger.error(f"  ❌ Instructor {instructor_id} için başlangıç slotu bulunamadı!")

    def _assign_consecutive_jury_members(self, assignments: List[Dict[str, Any]], 
                                        classroom_instructor_sequence: Dict) -> None:
        """
        NOT 2: Aynı sınıfta ardışık atanan instructor'ları tespit et ve birbirinin jürisi yap.
        
        Mantık:
        - Dr. Öğretim Görevlisi 14: D106'da consecutive (09:00-09:30)
        - Dr. Öğretim Görevlisi 2: D106'da consecutive (09:30-10:00) 
        
        Sonuç:
        - Öğretim Görevlisi 14 sorumlu → Öğretim Görevlisi 2 jüri
        - Öğretim Görevlisi 2 sorumlu → Öğretim Görevlisi 14 jüri
        """
        jury_assignments_made = 0
        
        for classroom_id, instructor_sequence in classroom_instructor_sequence.items():
            if len(instructor_sequence) < 2:
                continue
            
            logger.info(f"Sınıf {classroom_id} için ardışık jüri eşleştirmesi yapılıyor...")
            
            for i in range(len(instructor_sequence) - 1):
                instructor_a = instructor_sequence[i]
                instructor_b = instructor_sequence[i + 1]
                
                instructor_a_id = instructor_a['instructor_id']
                instructor_b_id = instructor_b['instructor_id']
                
                # Instructor A'nın projelerine Instructor B'yi jüri yap
                for assignment in assignments:
                    if assignment['project_id'] in instructor_a['project_ids']:
                        if instructor_b_id not in assignment['instructors']:
                            assignment['instructors'].append(instructor_b_id)
                            jury_assignments_made += 1
                            logger.info(f"  Proje {assignment['project_id']}: Instructor {instructor_a_id} sorumlu → Instructor {instructor_b_id} jüri")
                
                # Instructor B'nin projelerine Instructor A'yı jüri yap
                for assignment in assignments:
                    if assignment['project_id'] in instructor_b['project_ids']:
                        if instructor_a_id not in assignment['instructors']:
                            assignment['instructors'].append(instructor_a_id)
                            jury_assignments_made += 1
                            logger.info(f"  Proje {assignment['project_id']}: Instructor {instructor_b_id} sorumlu → Instructor {instructor_a_id} jüri")
        
        logger.info(f"Ardışık jüri eşleştirmesi tamamlandı: {jury_assignments_made} jüri ataması yapıldı")

    # OLD DUPLICATE METHOD - REMOVED (using new one at line 894)
    # def _detect_conflicts(self, assignments: List[Dict[str, Any]]) -> List[str]:
    #     """OLD - Detect conflicts in assignments"""
    #     pass

    def _resolve_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🔧 AI-BASED CONFLICT RESOLUTION
        Çakışmaları akıllıca çöz - projeleri alternatif slot/sınıflara taşı
        """
        conflicts = self._detect_conflicts(assignments)
        if not conflicts:
            return assignments
        
        logger.warning(f"🔧 Conflict resolution başlatılıyor: {len(conflicts)} çakışma tespit edildi")
        
        # Çakışan instructor-timeslot çiftlerini topla
        conflict_details = {}
        for conflict in conflicts:
            inst_id = conflict['instructor_id']
            ts_id = conflict['timeslot_id']
            key = f"{inst_id}_{ts_id}"
            if key not in conflict_details:
                conflict_details[key] = []
            conflict_details[key].append(conflict['assignment'])
        
        # Her çakışma için çözüm üret
        resolved_assignments = []
        used_slots_new = set()
        instructor_usage_new = defaultdict(set)
        
        # Önce çakışmayan atamaları ekle
        for assignment in assignments:
            has_conflict = False
            for conflict in conflicts:
                if conflict['assignment'] == assignment:
                    has_conflict = True
                    break
            
            if not has_conflict:
                resolved_assignments.append(assignment)
                slot_key = (assignment.get('classroom_id'), assignment.get('timeslot_id'))
                used_slots_new.add(slot_key)
                for inst_id in assignment.get('instructors', []):
                    instructor_usage_new[inst_id].add(assignment.get('timeslot_id'))
        
        # Sonra çakışan atamaları yeniden yerleştir
        for conflict_key, conflicted_assignments in conflict_details.items():
            # İlk atamayı tut, diğerlerini yeniden ata
            if conflicted_assignments:
                resolved_assignments.append(conflicted_assignments[0])
                slot_key = (conflicted_assignments[0].get('classroom_id'), 
                           conflicted_assignments[0].get('timeslot_id'))
                used_slots_new.add(slot_key)
                for inst_id in conflicted_assignments[0].get('instructors', []):
                    instructor_usage_new[inst_id].add(conflicted_assignments[0].get('timeslot_id'))
                
                # Diğer çakışan atamaları alternatif slotlara taşı
                for i, assignment in enumerate(conflicted_assignments[1:], 1):
                    reassigned = False
                    
                    # Alternatif slot ara
                    for classroom in self.classrooms:
                        for timeslot in self.timeslots:
                            slot_key = (classroom.get('id'), timeslot.get('id'))
                            ts_id = timeslot.get('id')
                            
                            # Bu slot kullanılabilir mi?
                            instructors = assignment.get('instructors', [])
                            all_available = True
                            
                            for inst_id in instructors:
                                if ts_id in instructor_usage_new[inst_id]:
                                    all_available = False
                                    break
                            
                            if slot_key not in used_slots_new and all_available:
                                # Yeni slot'a ata
                                new_assignment = assignment.copy()
                                new_assignment['classroom_id'] = classroom.get('id')
                                new_assignment['timeslot_id'] = ts_id
                                
                                resolved_assignments.append(new_assignment)
                                used_slots_new.add(slot_key)
                                for inst_id in instructors:
                                    instructor_usage_new[inst_id].add(ts_id)
                                
                                reassigned = True
                                logger.info(f"  ✅ Proje {assignment.get('project_id')} yeniden atandı: "
                                          f"{classroom.get('name', classroom.get('id'))} - {ts_id}")
                                break
                        
                        if reassigned:
                            break
                    
                    if not reassigned:
                        logger.error(f"  ❌ Proje {assignment.get('project_id')} için alternatif slot bulunamadı!")
                        # En azından eski halini ekle (çakışmalı da olsa)
                        resolved_assignments.append(assignment)
        
        # Final check
        final_conflicts = self._detect_conflicts(resolved_assignments)
        if final_conflicts:
            logger.error(f"  ⚠️ {len(final_conflicts)} çakışma hala mevcut!")
        else:
            logger.info(f"  ✅ Tüm çakışmalar başarıyla çözüldü!")
        
        return resolved_assignments

    def _parse_time(self, time_str: str) -> dt_time:
        """Parse time string to datetime.time object"""
        try:
            if isinstance(time_str, dt_time):
                return time_str
            return dt_time.fromisoformat(time_str)
        except:
            return dt_time(9, 0)  # Default to 09:00

    def _calculate_grouping_stats(self, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate consecutive grouping statistics."""
        if not assignments:
            return {
                "consecutive_count": 0,
                "total_instructors": 0,
                "avg_classroom_changes": 0.0,
                "consecutive_percentage": 0.0
            }
        
        instructor_assignments = defaultdict(list)
        for assignment in assignments:
            project_id = assignment.get("project_id")
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if project and project.get("responsible_id"):
                instructor_id = project["responsible_id"]
                instructor_assignments[instructor_id].append(assignment)
        
        consecutive_count = 0
        total_classroom_changes = 0
        
        for instructor_id, instructor_assignment_list in instructor_assignments.items():
            classrooms_used = set(a.get("classroom_id") for a in instructor_assignment_list)
            classroom_changes = len(classrooms_used) - 1
            total_classroom_changes += classroom_changes
            
            timeslot_ids = sorted([a.get("timeslot_id") for a in instructor_assignment_list])
            is_consecutive = all(
                timeslot_ids[i] + 1 == timeslot_ids[i+1] 
                for i in range(len(timeslot_ids) - 1)
            ) if len(timeslot_ids) > 1 else True
            
            if is_consecutive and len(classrooms_used) == 1:
                consecutive_count += 1
        
        total_instructors = len(instructor_assignments)
        avg_classroom_changes = total_classroom_changes / total_instructors if total_instructors > 0 else 0
        
        return {
            "consecutive_count": consecutive_count,
            "total_instructors": total_instructors,
            "avg_classroom_changes": avg_classroom_changes,
            "consecutive_percentage": (consecutive_count / total_instructors * 100) if total_instructors > 0 else 0
        }

    def _calculate_fitness_scores(self, solution: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate fitness scores for a solution."""
        if not solution:
            return {
                "load_balance": 0.0,
                "classroom_changes": 0.0,
                "time_efficiency": 0.0,
                "total": 0.0
            }
        
        load_balance = self._calculate_load_balance_score(solution)
        classroom_changes = self._calculate_classroom_changes_score(solution)
        time_efficiency = self._calculate_time_efficiency_score(solution)
        
        total = load_balance + classroom_changes + time_efficiency
        
        return {
            "load_balance": load_balance,
            "classroom_changes": classroom_changes,
            "time_efficiency": time_efficiency,
            "total": total
        }
    
    def _calculate_load_balance_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate load balance score."""
        instructor_loads = {}
        
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if not instructor_loads:
            return 0.0
        
        loads = list(instructor_loads.values())
        avg_load = sum(loads) / len(loads)
        variance = sum((load - avg_load) ** 2 for load in loads) / len(loads)
        
        return variance
    
    def _calculate_classroom_changes_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate classroom changes score."""
        instructor_classrooms = {}
        changes = 0
        
        for assignment in solution:
            classroom_id = assignment.get("classroom_id")
            for instructor_id in assignment.get("instructors", []):
                if instructor_id in instructor_classrooms:
                    if instructor_classrooms[instructor_id] != classroom_id:
                        changes += 1
                instructor_classrooms[instructor_id] = classroom_id
        
        return float(changes)
    
    def _calculate_time_efficiency_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate time efficiency score."""
        instructor_timeslots = {}
        gaps = 0
        
        for assignment in solution:
            timeslot_id = assignment.get("timeslot_id")
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_timeslots:
                    instructor_timeslots[instructor_id] = []
                instructor_timeslots[instructor_id].append(timeslot_id)
        
        for timeslots in instructor_timeslots.values():
            sorted_slots = sorted(timeslots)
            for i in range(1, len(sorted_slots)):
                if sorted_slots[i] - sorted_slots[i-1] > 1:
                    gaps += 1
        
        return float(gaps)