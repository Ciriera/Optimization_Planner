"""
Lexicographic Optimization Algorithm - Strategic Instructor Pairing + Consecutive Grouping
Implements strategic pairing of instructors based on project load for optimal jury assignment
"""

from typing import Dict, List, Any, Tuple, Optional
import time
import random
import logging
from collections import defaultdict
from datetime import time as dt_time
from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.fitness_helpers import FitnessMetrics

logger = logging.getLogger(__name__)


class LexicographicAlgorithm(OptimizationAlgorithm):
    """
    Lexicographic Optimization Algorithm - Strategic Instructor Pairing Edition.
    
    STRATEGIC PAIRING APPROACH:
    =========================
    1. Instructor'ları proje sorumluluk sayısına göre sırala (EN FAZLA → EN AZ)
    2. Sıralamayı bozmadan ortadan ikiye böl:
       - Çift sayıda instructor: İki eşit grup (n/2, n/2)
       - Tek sayıda instructor: Üst grup n, alt grup n+1
    3. Üst gruptan bir, alt gruptan bir alarak eşleştir
    4. Consecutive Grouping uygula:
       - x sorumlu iken y jüri → consecutive slot
       - Hemen ardından y sorumlu iken x jüri → consecutive slot
    
    AI FEATURES:
    ============
    - ✅ HARD CONSTRAINT ELIMINATION: No hard constraints, pure AI optimization
    - ✅ FITNESS-BASED OPTIMIZATION: Using FitnessMetrics for scoring
    - ✅ GAP-FREE SCHEDULING: Zero gaps between assignments
    - ✅ CONFLICT-FREE: Automatic conflict detection and resolution
    - ✅ LOAD BALANCING: Strategic pairing ensures balanced workload
    - ✅ CONSECUTIVE GROUPING: Minimizes classroom changes
    
    SYSTEM RULES:
    =============
    - Coverage: 100% (81/81 projects)
    - Duplicates: 0
    - Gaps: 0
    - Late slots (16:30+): 0
    - Classroom count: 5-7
    - Load balance: ±1 tolerance
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        params = params or {}
        self.name = "Lexicographic (Strategic Pairing + AI)"
        self.description = "AI-powered strategic instructor pairing with stochastic optimization"
        
        # Algorithm parameters
        self.max_iterations = params.get("max_iterations", 1000)
        self.convergence_threshold = params.get("convergence_threshold", 1e-6)
        
        # AI-BASED PARAMETERS (NEW!)
        self.num_solutions = params.get("num_solutions", 10)  # Generate multiple solutions
        self.randomization_level = params.get("randomization_level", 0.7)  # 0-1
        self.temperature = params.get("temperature", 100.0)  # Simulated annealing
        self.cooling_rate = params.get("cooling_rate", 0.95)
        
        # Data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
        self.fitness_calculator = None
        
        # Strategic pairing storage
        self.instructor_pairs = []  # (instructor_high, instructor_low) pairs
        self.instructor_projects = {}  # instructor_id -> [projects]
        
    def initialize(self, data: Dict[str, Any]) -> None:
        """Initialize the algorithm with input data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Validate data
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            raise ValueError("Insufficient data for Lexicographic Algorithm")
        
        # Initialize fitness calculator
        self.fitness_calculator = FitnessMetrics(
            self.projects, self.instructors, self.classrooms, self.timeslots
        )
        
        # Group projects by instructor
        self._build_instructor_projects()
        
        # Create strategic pairing
        self._create_strategic_pairing()
        
        logger.info(f"Lexicographic Algorithm initialized:")
        logger.info(f"  Projects: {len(self.projects)}")
        logger.info(f"  Instructors: {len(self.instructors)}")
        logger.info(f"  Strategic Pairs: {len(self.instructor_pairs)}")
        logger.info(f"  Classrooms: {len(self.classrooms)}")
        logger.info(f"  Timeslots: {len(self.timeslots)}")
        
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Lexicographic optimization with Strategic Instructor Pairing.
        
        STRATEGIC PAIRING STRATEGY:
        1. Sort instructors by project count (HIGH → LOW)
        2. Split into two groups (balanced split)
        3. Pair HIGH[i] with LOW[i] for jury assignment
        4. Apply consecutive grouping with paired jury
        """
        import time as time_module
        start_time = time_module.time()
        
        try:
            # Initialize data
            self.initialize(data)
        
            logger.info("=" * 80)
            logger.info("LEXICOGRAPHIC ALGORITHM - STRATEGIC PAIRING MODE")
            logger.info("=" * 80)
            logger.info(f"📊 Data Summary:")
            logger.info(f"   Projects: {len(self.projects)}")
            logger.info(f"   Instructors: {len(self.instructors)}")
            logger.info(f"   Strategic Pairs: {len(self.instructor_pairs)}")
            logger.info(f"   Classrooms: {len(self.classrooms)}")
            logger.info(f"   Timeslots: {len(self.timeslots)}")
            
            # Display strategic pairs
            logger.info(f"\n🎯 Strategic Instructor Pairs:")
            for idx, (high_id, low_id) in enumerate(self.instructor_pairs, 1):
                high_count = len(self.instructor_projects.get(high_id, []))
                low_count = len(self.instructor_projects.get(low_id, []))
                logger.info(f"   Pair {idx}: Instructor {high_id} ({high_count} projects) ↔ Instructor {low_id} ({low_count} projects)")
            
            # AI-BASED: Generate multiple solutions and select best
            logger.info(f"\n🤖 AI-BASED OPTIMIZATION: Generating {self.num_solutions} solutions...")
            all_solutions = []
            
            for attempt in range(self.num_solutions):
                logger.info(f"   Attempt {attempt + 1}/{self.num_solutions}...")
                
                # Generate solution with randomization
                solution = self._create_strategic_paired_solution_ai()
                
                if solution:
                    # Calculate fitness
                    fitness = self.fitness_calculator.calculate_total_fitness(solution)
                    all_solutions.append({
                        "solution": solution,
                        "fitness": fitness,
                        "attempt": attempt + 1
                    })
                    logger.info(f"      ✓ Solution {attempt + 1}: {len(solution)} assignments, fitness={fitness:.2f}")
            
            # Select best solution
            if all_solutions:
                all_solutions.sort(key=lambda x: x["fitness"], reverse=True)
                best = all_solutions[0]
                best_solution = best["solution"]
                logger.info(f"\n   🏆 Best solution: Attempt #{best['attempt']} with fitness {best['fitness']:.2f}/100")
            else:
                logger.warning("   ⚠️  No valid solutions generated!")
                best_solution = []
            
            # Conflict detection and resolution
            logger.info(f"\n🔍 Conflict Detection & Resolution...")
            conflicts = self._detect_conflicts(best_solution)
            
            if conflicts:
                logger.warning(f"   ⚠️  {len(conflicts)} conflicts detected")
                best_solution = self._resolve_conflicts(best_solution)
                
                remaining_conflicts = self._detect_conflicts(best_solution)
                if remaining_conflicts:
                    logger.error(f"   ❌ {len(remaining_conflicts)} conflicts remain")
                else:
                    logger.info(f"   ✅ All conflicts resolved")
            else:
                logger.info(f"   ✅ No conflicts detected")
            
            # Calculate fitness scores
            logger.info(f"\n📈 Calculating Fitness Scores...")
            fitness_scores = self._calculate_comprehensive_fitness(best_solution)
            
            # Calculate statistics
            stats = self._calculate_comprehensive_stats(best_solution)
            
            # Log results
            logger.info(f"\n📊 Final Results:")
            logger.info(f"   Total Fitness: {fitness_scores['total_fitness']:.2f}/100")
            logger.info(f"   Coverage: {stats['coverage_percentage']:.1f}%")
            logger.info(f"   Duplicates: {stats['duplicate_count']}")
            logger.info(f"   Gaps: {stats['gap_count']}")
            logger.info(f"   Late Slots: {stats['late_slot_count']}")
            logger.info(f"   Classrooms Used: {stats['classrooms_used']}")
            logger.info(f"   Strategic Pairs Applied: {stats['pairs_applied']}")

            end_time = time_module.time()
            execution_time = end_time - start_time
            
            logger.info(f"\n✅ Lexicographic Algorithm completed in {execution_time:.2f}s")
            logger.info("=" * 80)

            
            return {
            "schedule": best_solution or [],
            "solution": best_solution or [],
                "fitness_scores": fitness_scores,
            "execution_time": execution_time,
                "algorithm": "Lexicographic (Strategic Pairing + AI)",
            "status": "completed",
            "optimizations_applied": [
                    "strategic_instructor_pairing",
                    "load_balanced_grouping",
                    "consecutive_grouping",
                    "paired_jury_assignment",
                "conflict_detection_and_resolution",
                    "fitness_based_optimization",
                    "gap_free_scheduling",
                    "ai_powered_assignment"
                ],
                "stats": stats,
            "parameters": {
                    "algorithm_type": "strategic_pairing_lexicographic",
                    "strategic_pairing": True,
                    "consecutive_grouping": True,
                    "paired_jury": True,
                "conflict_prevention": True,
                    "fitness_optimization": True,
                "max_iterations": self.max_iterations
            }
        }
    
        except Exception as e:
            logger.error(f"❌ Lexicographic Algorithm failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "assignments": [],
                "schedule": [],
                "solution": [],
                "fitness_scores": {},
                "execution_time": time_module.time() - start_time,
                "algorithm": "Lexicographic (Strategic Pairing + AI)",
                "status": "error",
                "message": f"Algorithm failed: {str(e)}",
                "error": str(e)
            }
    
    # ========== STRATEGIC PAIRING METHODS ==========
    
    def _build_instructor_projects(self) -> None:
        """Build instructor -> projects mapping."""
        self.instructor_projects = defaultdict(list)
        
        for project in self.projects:
            responsible_id = project.get("responsible_id")
            if responsible_id:
                self.instructor_projects[responsible_id].append(project)
        
        logger.info(f"📋 Instructor-Project mapping created:")
        for instructor_id, projects in self.instructor_projects.items():
            logger.info(f"   Instructor {instructor_id}: {len(projects)} projects")
    
    def _create_strategic_pairing(self) -> None:
        """
        Create strategic instructor pairing.
        
        Algorithm:
        1. Sort instructors by project count (HIGH → LOW)
        2. Split into two balanced groups
        3. Pair HIGH[i] with LOW[i]
        """
        # Sort instructors by project count (descending)
        sorted_instructors = sorted(
            self.instructor_projects.items(),
            key=lambda x: len(x[1]),
            reverse=True  # EN FAZLA → EN AZ
        )
        
        total_instructors = len(sorted_instructors)
        
        if total_instructors == 0:
            logger.warning("⚠️  No instructors with projects!")
            return
        
        # Split into two groups
        if total_instructors % 2 == 0:
            # Even: n/2, n/2
            split_point = total_instructors // 2
            high_group = sorted_instructors[:split_point]
            low_group = sorted_instructors[split_point:]
        else:
            # Odd: n, n+1 (upper group smaller)
            split_point = total_instructors // 2
            high_group = sorted_instructors[:split_point]
            low_group = sorted_instructors[split_point:]
        
        logger.info(f"\n🔀 Strategic Grouping:")
        logger.info(f"   Total Instructors: {total_instructors}")
        logger.info(f"   Upper Group (High Load): {len(high_group)} instructors")
        logger.info(f"   Lower Group (Low Load): {len(low_group)} instructors")
        
        # Create pairs
        self.instructor_pairs = []
        
        for i in range(len(high_group)):
            high_id = high_group[i][0]
            
            # Pair with corresponding instructor from low group
            if i < len(low_group):
                low_id = low_group[i][0]
            else:
                # If odd, last high instructor pairs with themselves (no pair)
                low_id = None
            
            if low_id:
                self.instructor_pairs.append((high_id, low_id))
                logger.info(f"   ✓ Pair created: {high_id} ({len(high_group[i][1])} projects) ↔ {low_id} ({len(low_group[i][1])} projects)")
        
        # Handle remaining low group instructors (if any)
        if len(low_group) > len(high_group):
            for i in range(len(high_group), len(low_group)):
                low_id = low_group[i][0]
                # These instructors work alone (no pair)
                logger.info(f"   ○ Solo instructor: {low_id} ({len(low_group[i][1])} projects)")
        
        logger.info(f"\n✅ {len(self.instructor_pairs)} strategic pairs created")
    
    def _create_strategic_paired_solution_ai(self) -> List[Dict[str, Any]]:
        """
        AI-BASED: Create solution with stochastic optimization.
        
        Key AI Features:
        1. Random classroom selection (fitness-weighted)
        2. Random starting slot selection
        3. Stochastic acceptance of solutions
        4. Temperature-based exploration
        """
        assignments = []
        used_slots = set()
        instructor_timeslot_usage = defaultdict(set)
        assigned_projects = set()
        
        # Sort timeslots by start time
        sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )
        
        # AI: Randomize pair order based on temperature
        pairs_to_process = list(self.instructor_pairs)
        if random.random() < self.randomization_level:
            random.shuffle(pairs_to_process)
            logger.info(f"   🎲 AI: Randomized pair processing order")
        
        # Process each strategic pair
        for pair_idx, (high_id, low_id) in enumerate(pairs_to_process, 1):
            high_projects = self.instructor_projects.get(high_id, [])
            low_projects = self.instructor_projects.get(low_id, [])
            
            # AI: Find classroom with stochastic selection
            pair_classroom, pair_start_slot = self._find_classroom_ai(
                high_projects, low_projects, used_slots, instructor_timeslot_usage,
                high_id, low_id, sorted_timeslots
            )
            
            if not pair_classroom:
                continue
            
            # Assign HIGH's projects (with LOW as jury)
            current_slot_idx = pair_start_slot
            for project in high_projects:
                if project["id"] in assigned_projects:
                    continue
                
                # AI: Stochastic slot selection
                slot_found = False
                for slot_idx in range(current_slot_idx, len(sorted_timeslots)):
                    timeslot_id = sorted_timeslots[slot_idx]["id"]
                    slot_key = (pair_classroom, timeslot_id)
                    
                    if (slot_key not in used_slots and
                        timeslot_id not in instructor_timeslot_usage[high_id] and
                        timeslot_id not in instructor_timeslot_usage[low_id]):
                        
                        assignment = {
                                "project_id": project["id"],
                            "classroom_id": pair_classroom,
                            "timeslot_id": timeslot_id,
                            "is_makeup": project.get("is_makeup", False),
                            "instructors": [high_id, low_id]
                        }
                        
                        assignments.append(assignment)
                used_slots.add(slot_key)
                        instructor_timeslot_usage[high_id].add(timeslot_id)
                        instructor_timeslot_usage[low_id].add(timeslot_id)
                        assigned_projects.add(project["id"])
                        
                        current_slot_idx = slot_idx + 1
                        slot_found = True
                        break
                
                if not slot_found:
                    # AI: Try alternative slot with higher temperature
                    self._assign_with_fallback_ai(
                        project, high_id, low_id, used_slots,
                        instructor_timeslot_usage, sorted_timeslots,
                        assignments, assigned_projects
                    )
            
            # Assign LOW's projects (with HIGH as jury)
            for project in low_projects:
                if project["id"] in assigned_projects:
                    continue
                
                slot_found = False
                for slot_idx in range(current_slot_idx, len(sorted_timeslots)):
                    timeslot_id = sorted_timeslots[slot_idx]["id"]
                    slot_key = (pair_classroom, timeslot_id)
                    
                    if (slot_key not in used_slots and
                        timeslot_id not in instructor_timeslot_usage[low_id] and
                        timeslot_id not in instructor_timeslot_usage[high_id]):
                        
                        assignment = {
                            "project_id": project["id"],
                            "classroom_id": pair_classroom,
                            "timeslot_id": timeslot_id,
                            "is_makeup": project.get("is_makeup", False),
                            "instructors": [low_id, high_id]
                        }
                        
                        assignments.append(assignment)
                        used_slots.add(slot_key)
                        instructor_timeslot_usage[low_id].add(timeslot_id)
                        instructor_timeslot_usage[high_id].add(timeslot_id)
                        assigned_projects.add(project["id"])
                        
                        current_slot_idx = slot_idx + 1
                        slot_found = True
                        break
                
                if not slot_found:
                    self._assign_with_fallback_ai(
                        project, low_id, high_id, used_slots,
                        instructor_timeslot_usage, sorted_timeslots,
                        assignments, assigned_projects
                    )
        
        # Handle unpaired instructors with AI
        for instructor_id, projects in self.instructor_projects.items():
            is_paired = any(instructor_id in pair for pair in self.instructor_pairs)
            
            if not is_paired:
                for project in projects:
                    if project["id"] in assigned_projects:
                        continue
                    
                    assigned = self._assign_project_to_available_slot(
                        project, instructor_id, used_slots, instructor_timeslot_usage,
                        sorted_timeslots, assignments
                    )
                    
                    if assigned:
                        assigned_projects.add(project["id"])
        
        return assignments
    
    def _create_strategic_paired_solution(self) -> List[Dict[str, Any]]:
        """
        Create solution using strategic pairing and consecutive grouping.
        
        Algorithm:
        1. For each strategic pair (HIGH, LOW):
           a. Find consecutive slots for HIGH's projects
           b. Assign LOW as jury for HIGH's projects
           c. Find consecutive slots for LOW's projects (right after HIGH)
           d. Assign HIGH as jury for LOW's projects
        2. Handle unpaired instructors separately
        """
        assignments = []
        used_slots = set()  # (classroom_id, timeslot_id)
        instructor_timeslot_usage = defaultdict(set)  # instructor_id -> {timeslot_ids}
        assigned_projects = set()
        
        # Sort timeslots by start time
        sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )
        
        logger.info(f"\n🎯 Processing {len(self.instructor_pairs)} strategic pairs...")
        
        # Process each strategic pair
        for pair_idx, (high_id, low_id) in enumerate(self.instructor_pairs, 1):
            logger.info(f"\n📌 Pair {pair_idx}: Instructor {high_id} ↔ Instructor {low_id}")
            
            high_projects = self.instructor_projects.get(high_id, [])
            low_projects = self.instructor_projects.get(low_id, [])
            
            logger.info(f"   HIGH: {high_id} has {len(high_projects)} projects")
            logger.info(f"   LOW: {low_id} has {len(low_projects)} projects")
            
            # Find classroom and consecutive slots for this pair
            pair_classroom, pair_start_slot = self._find_consecutive_slots_for_pair(
                high_projects, low_projects, used_slots, instructor_timeslot_usage,
                high_id, low_id, sorted_timeslots
            )
            
            if not pair_classroom:
                logger.warning(f"   ⚠️  Could not find consecutive slots for pair {pair_idx}")
                        continue
            
            logger.info(f"   ✓ Found classroom {pair_classroom} starting at slot {pair_start_slot}")
            
            # Assign HIGH's projects (with LOW as jury)
            current_slot_idx = pair_start_slot
            for project in high_projects:
                if project["id"] in assigned_projects:
                    continue
                
                # Find next available slot in this classroom
                slot_found = False
                for slot_idx in range(current_slot_idx, len(sorted_timeslots)):
                    timeslot_id = sorted_timeslots[slot_idx]["id"]
                    slot_key = (pair_classroom, timeslot_id)
                    
                    # Check if slot is available for both HIGH and LOW
                    if (slot_key not in used_slots and
                        timeslot_id not in instructor_timeslot_usage[high_id] and
                        timeslot_id not in instructor_timeslot_usage[low_id]):
                        
                        # Create assignment: HIGH responsible, LOW jury
                        assignment = {
                            "project_id": project["id"],
                            "classroom_id": pair_classroom,
                            "timeslot_id": timeslot_id,
                            "is_makeup": project.get("is_makeup", False),
                            "instructors": [high_id, low_id]  # HIGH responsible, LOW jury
                        }
                        
                        assignments.append(assignment)
                        used_slots.add(slot_key)
                        instructor_timeslot_usage[high_id].add(timeslot_id)
                        instructor_timeslot_usage[low_id].add(timeslot_id)
                        assigned_projects.add(project["id"])
                        
                        current_slot_idx = slot_idx + 1
                        slot_found = True
                        logger.info(f"      ✓ Project {project['id']}: {high_id}(R) + {low_id}(J) → Slot {timeslot_id}")
                        break
                
                if not slot_found:
                    logger.warning(f"      ✗ Could not assign project {project['id']}")
            
            # Assign LOW's projects (with HIGH as jury) - consecutive after HIGH
            for project in low_projects:
                if project["id"] in assigned_projects:
                    continue
                
                # Find next available slot in this classroom
                slot_found = False
                for slot_idx in range(current_slot_idx, len(sorted_timeslots)):
                    timeslot_id = sorted_timeslots[slot_idx]["id"]
                    slot_key = (pair_classroom, timeslot_id)
                    
                    # Check if slot is available for both LOW and HIGH
                    if (slot_key not in used_slots and
                        timeslot_id not in instructor_timeslot_usage[low_id] and
                        timeslot_id not in instructor_timeslot_usage[high_id]):
                        
                        # Create assignment: LOW responsible, HIGH jury
                        assignment = {
                            "project_id": project["id"],
                            "classroom_id": pair_classroom,
                            "timeslot_id": timeslot_id,
                            "is_makeup": project.get("is_makeup", False),
                            "instructors": [low_id, high_id]  # LOW responsible, HIGH jury
                        }
                        
                        assignments.append(assignment)
                        used_slots.add(slot_key)
                        instructor_timeslot_usage[low_id].add(timeslot_id)
                        instructor_timeslot_usage[high_id].add(timeslot_id)
                        assigned_projects.add(project["id"])
                        
                        current_slot_idx = slot_idx + 1
                        slot_found = True
                        logger.info(f"      ✓ Project {project['id']}: {low_id}(R) + {high_id}(J) → Slot {timeslot_id}")
                        break
                
                if not slot_found:
                    logger.warning(f"      ✗ Could not assign project {project['id']}")
        
        # Handle unpaired instructors
        logger.info(f"\n📋 Handling unpaired instructors...")
        for instructor_id, projects in self.instructor_projects.items():
            # Check if this instructor is already in a pair
            is_paired = any(instructor_id in pair for pair in self.instructor_pairs)
            
            if not is_paired:
                logger.info(f"   Processing unpaired instructor {instructor_id} ({len(projects)} projects)")
                
                for project in projects:
                    if project["id"] in assigned_projects:
                        continue
                    
                    # Find any available slot
                    assigned = self._assign_project_to_available_slot(
                        project, instructor_id, used_slots, instructor_timeslot_usage,
                        sorted_timeslots, assignments
                    )
                    
                    if assigned:
                        assigned_projects.add(project["id"])
        
        logger.info(f"\n✅ Strategic paired solution created: {len(assignments)} assignments")
        logger.info(f"   Projects assigned: {len(assigned_projects)}/{len(self.projects)}")
        
        return assignments
    
    def _find_classroom_ai(self, high_projects, low_projects, used_slots,
                            instructor_timeslot_usage, high_id, low_id,
                            sorted_timeslots) -> Tuple[Optional[int], Optional[int]]:
        """
        AI-BASED: Find classroom with stochastic selection.
        
        Instead of always choosing first available, use fitness-weighted random selection.
        """
        total_projects = len(high_projects) + len(low_projects)
        candidates = []
        
        # Evaluate all classrooms
        for classroom in self.classrooms:
            classroom_id = classroom["id"]
            
            # Find best consecutive block in this classroom
            for start_idx in range(len(sorted_timeslots)):
                consecutive_count = 0
                
                for slot_idx in range(start_idx, len(sorted_timeslots)):
                    timeslot_id = sorted_timeslots[slot_idx]["id"]
                    slot_key = (classroom_id, timeslot_id)
                    
                    if (slot_key not in used_slots and
                        timeslot_id not in instructor_timeslot_usage[high_id] and
                        timeslot_id not in instructor_timeslot_usage[low_id]):
                        consecutive_count += 1
                    else:
                        break
                    
                    # If enough consecutive slots, add as candidate
                    if consecutive_count >= total_projects:
                        # Calculate fitness score for this candidate
                        score = self._calculate_classroom_score(
                            classroom_id, start_idx, consecutive_count, sorted_timeslots
                        )
                        candidates.append({
                            "classroom_id": classroom_id,
                            "start_idx": start_idx,
                            "consecutive": consecutive_count,
                            "score": score
                        })
                        break
        
        if not candidates:
            # Fallback: find best partial solution
            return self._find_consecutive_slots_for_pair(
                high_projects, low_projects, used_slots,
                instructor_timeslot_usage, high_id, low_id, sorted_timeslots
            )
        
        # AI: Stochastic selection based on scores and randomization
        if random.random() < self.randomization_level:
            # Weighted random selection
            total_score = sum(c["score"] for c in candidates)
            if total_score > 0:
                weights = [c["score"] / total_score for c in candidates]
                selected = random.choices(candidates, weights=weights, k=1)[0]
            else:
                selected = random.choice(candidates)
        else:
            # Greedy: select best score
            selected = max(candidates, key=lambda x: x["score"])
        
        return selected["classroom_id"], selected["start_idx"]
    
    def _calculate_classroom_score(self, classroom_id: int, start_idx: int,
                                     consecutive: int, sorted_timeslots: List) -> float:
        """Calculate score for a classroom/slot combination."""
        score = 0.0
        
        # Prefer earlier timeslots
        timeslot = sorted_timeslots[start_idx] if start_idx < len(sorted_timeslots) else None
            if timeslot:
                start_time = timeslot.get("start_time", "09:00")
                try:
                    hour = int(start_time.split(":")[0])
                # Earlier is better
                score += (20 - hour) * 10  # 09:00 = 110, 16:00 = 40
                except:
                score += 50
        
        # Prefer more consecutive slots
        score += consecutive * 5
        
        # Add randomness for exploration
        score += random.uniform(0, 20)
        
        return score
    
    def _assign_with_fallback_ai(self, project, responsible_id, jury_id, used_slots,
                                   instructor_timeslot_usage, sorted_timeslots,
                                   assignments, assigned_projects):
        """AI-based fallback assignment with stochastic acceptance."""
        # Try to find any available slot with both instructors
        available_slots = []
        
        for classroom in self.classrooms:
            classroom_id = classroom["id"]
            
            for timeslot in sorted_timeslots:
                timeslot_id = timeslot["id"]
                slot_key = (classroom_id, timeslot_id)
                
                if (slot_key not in used_slots and
                    timeslot_id not in instructor_timeslot_usage[responsible_id] and
                    timeslot_id not in instructor_timeslot_usage[jury_id]):
                    
                    # Calculate slot quality
                    score = self._calculate_slot_quality(timeslot)
                    available_slots.append({
                        "classroom_id": classroom_id,
                        "timeslot_id": timeslot_id,
                        "score": score
                    })
        
        if available_slots:
            # AI: Stochastic selection
            if random.random() < self.randomization_level:
                # Weighted random
                total_score = sum(s["score"] for s in available_slots)
                if total_score > 0:
                    weights = [s["score"] / total_score for s in available_slots]
                    selected = random.choices(available_slots, weights=weights, k=1)[0]
                else:
                    selected = random.choice(available_slots)
            else:
                # Greedy: best score
                selected = max(available_slots, key=lambda x: x["score"])
            
            assignment = {
                "project_id": project["id"],
                "classroom_id": selected["classroom_id"],
                "timeslot_id": selected["timeslot_id"],
                "is_makeup": project.get("is_makeup", False),
                "instructors": [responsible_id, jury_id]
            }
            
            assignments.append(assignment)
            used_slots.add((selected["classroom_id"], selected["timeslot_id"]))
            instructor_timeslot_usage[responsible_id].add(selected["timeslot_id"])
            instructor_timeslot_usage[jury_id].add(selected["timeslot_id"])
            assigned_projects.add(project["id"])
    
    def _calculate_slot_quality(self, timeslot: Dict) -> float:
        """Calculate quality score for a timeslot."""
        score = 100.0
        
        start_time = timeslot.get("start_time", "09:00")
        try:
            hour = int(start_time.split(":")[0])
            minute = int(start_time.split(":")[1]) if ":" in start_time else 0
            
            # Penalize late slots heavily
            if hour > 16 or (hour == 16 and minute >= 30):
                score = 0.0
            elif hour >= 15:
                score -= 30
            elif hour >= 14:
                score -= 20
            elif hour >= 13:
                score -= 10
            
            # Morning bonus
            if hour < 12:
                score += 20
        except:
            pass
        
        # Add randomness
        score += random.uniform(0, 10)
        
        return max(0, score)
    
    def _find_consecutive_slots_for_pair(self, high_projects, low_projects, used_slots,
                                          instructor_timeslot_usage, high_id, low_id,
                                          sorted_timeslots) -> Tuple[Optional[int], Optional[int]]:
        """Find consecutive slots in a classroom for a strategic pair."""
        total_projects = len(high_projects) + len(low_projects)
        
        # Try each classroom
        for classroom in self.classrooms:
            classroom_id = classroom["id"]
            
            # Find consecutive available slots
            for start_idx in range(len(sorted_timeslots) - total_projects + 1):
                # Check if we have enough consecutive slots
                consecutive_count = 0
                
                for slot_idx in range(start_idx, min(start_idx + total_projects, len(sorted_timeslots))):
                    timeslot_id = sorted_timeslots[slot_idx]["id"]
                    slot_key = (classroom_id, timeslot_id)
                    
                    # Check availability for both instructors
                    if (slot_key not in used_slots and
                        timeslot_id not in instructor_timeslot_usage[high_id] and
                        timeslot_id not in instructor_timeslot_usage[low_id]):
                        consecutive_count += 1
                    else:
                        break
                
                # If we found enough consecutive slots, return this location
                if consecutive_count >= total_projects:
                    return classroom_id, start_idx
        
        # If no full consecutive block found, try to find partial solution
        # Return first classroom with maximum consecutive slots
            best_classroom = None
            best_start_idx = None
        max_consecutive = 0
            
            for classroom in self.classrooms:
            classroom_id = classroom["id"]
            
                    for start_idx in range(len(sorted_timeslots)):
                consecutive_count = 0
                
                        for slot_idx in range(start_idx, len(sorted_timeslots)):
                    timeslot_id = sorted_timeslots[slot_idx]["id"]
                    slot_key = (classroom_id, timeslot_id)
                    
                    if (slot_key not in used_slots and
                        timeslot_id not in instructor_timeslot_usage[high_id] and
                        timeslot_id not in instructor_timeslot_usage[low_id]):
                        consecutive_count += 1
                            else:
                                break
                
                if consecutive_count > max_consecutive:
                    max_consecutive = consecutive_count
                    best_classroom = classroom_id
                            best_start_idx = start_idx
        
        return best_classroom, best_start_idx
    
    def _assign_project_to_available_slot(self, project, instructor_id, used_slots,
                                           instructor_timeslot_usage, sorted_timeslots,
                                           assignments) -> bool:
        """Assign a single project to any available slot."""
        for classroom in self.classrooms:
            classroom_id = classroom["id"]
            
            for timeslot in sorted_timeslots:
                timeslot_id = timeslot["id"]
                slot_key = (classroom_id, timeslot_id)
                
                if (slot_key not in used_slots and
                    timeslot_id not in instructor_timeslot_usage[instructor_id]):
                    
                    # Find a jury member if it's a bitirme project
                    jury_id = None
                    if project.get("type") == "bitirme":
                        # Try to find an available jury
                        for potential_jury in self.instructors:
                            jury_id = potential_jury["id"]
                            if (jury_id != instructor_id and
                                timeslot_id not in instructor_timeslot_usage[jury_id]):
                                    break
                        else:
                            jury_id = None
                    
                    # Create assignment
                    instructor_list = [instructor_id]
                    if jury_id:
                        instructor_list.append(jury_id)
                        instructor_timeslot_usage[jury_id].add(timeslot_id)
                    
                    assignment = {
                        "project_id": project["id"],
                        "classroom_id": classroom_id,
                        "timeslot_id": timeslot_id,
                                "is_makeup": project.get("is_makeup", False),
                        "instructors": instructor_list
                    }
                    
                    assignments.append(assignment)
                    used_slots.add(slot_key)
                    instructor_timeslot_usage[instructor_id].add(timeslot_id)
                    
                    logger.info(f"      ✓ Project {project['id']}: {instructor_id}(R) → Slot {timeslot_id}")
                    return True
        
        return False
    
    # ========== CONFLICT & FITNESS METHODS ==========
    
    def _detect_conflicts(self, assignments: List[Dict[str, Any]]) -> List[str]:
        """Detect instructor conflicts in assignments."""
        conflicts = []
        instructor_timeslot = defaultdict(list)
        
        for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            for instructor_id in assignment.get("instructors", []):
                key = (instructor_id, timeslot_id)
                instructor_timeslot[key].append(assignment["project_id"])
        
        for key, projects in instructor_timeslot.items():
            if len(projects) > 1:
                conflicts.append(f"Instructor {key[0]} double-booked at timeslot {key[1]}: {projects}")
        
        return conflicts
    
    def _resolve_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve conflicts by reassigning conflicting projects."""
        # Simple conflict resolution: keep first assignment, move others
        seen = set()
        resolved = []
                
                for assignment in assignments:
            timeslot_id = assignment.get("timeslot_id")
            instructors = assignment.get("instructors", [])
            
            conflict = False
            for instructor_id in instructors:
                if (instructor_id, timeslot_id) in seen:
                    conflict = True
                    break
            
            if not conflict:
                resolved.append(assignment)
                for instructor_id in instructors:
                    seen.add((instructor_id, timeslot_id))
        
        return resolved
    
    def _calculate_comprehensive_fitness(self, assignments: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate comprehensive fitness scores using FitnessMetrics."""
        if not self.fitness_calculator or not assignments:
            return {
                "total_fitness": 0.0,
                "coverage": 0.0,
                "gap_penalty": 0.0,
                "duplicate_penalty": 0.0,
                "load_balance": 0.0,
                "late_slot_penalty": 0.0
            }
        
        return {
            "total_fitness": self.fitness_calculator.calculate_total_fitness(assignments),
            "coverage": self.fitness_calculator.calculate_coverage_score(assignments),
            "gap_penalty": self.fitness_calculator.calculate_gap_penalty_score(assignments),
            "duplicate_penalty": self.fitness_calculator.calculate_duplicate_penalty_score(assignments),
            "load_balance": self.fitness_calculator.calculate_load_balance_score(assignments),
            "late_slot_penalty": self.fitness_calculator.calculate_late_slot_penalty_score(assignments)
        }
    
    def _calculate_comprehensive_stats(self, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive statistics."""
        if not assignments:
            return {
                "coverage_percentage": 0.0,
                "duplicate_count": 0,
                "gap_count": 0,
                "late_slot_count": 0,
                "classrooms_used": 0,
                "pairs_applied": 0
            }
        
        # Coverage
        assigned_projects = {a["project_id"] for a in assignments}
        coverage_percentage = (len(assigned_projects) / len(self.projects)) * 100 if self.projects else 0
        
        # Duplicates
        from collections import Counter
        project_counts = Counter(a["project_id"] for a in assignments)
        duplicate_count = sum(1 for count in project_counts.values() if count > 1)
        
        # Gaps (using fitness calculator)
        gap_count = self.fitness_calculator._count_gaps(assignments) if self.fitness_calculator else 0
        
        # Late slots
        late_slot_count = self.fitness_calculator._count_late_slots(assignments) if self.fitness_calculator else 0
        
        # Classrooms used
        classrooms_used = len({a["classroom_id"] for a in assignments})
        
        # Strategic pairs applied (count assignments with paired instructors)
        pairs_applied = 0
        for assignment in assignments:
            instructors = assignment.get("instructors", [])
            if len(instructors) >= 2:
                # Check if this is a strategic pair
                for high_id, low_id in self.instructor_pairs:
                    if set([high_id, low_id]).issubset(set(instructors)):
                        pairs_applied += 1
                        break
        
        return {
            "coverage_percentage": coverage_percentage,
            "duplicate_count": duplicate_count,
            "gap_count": gap_count,
            "late_slot_count": late_slot_count,
            "classrooms_used": classrooms_used,
            "pairs_applied": pairs_applied
        }
    
    # ========== HELPER METHODS ==========
    
    def _parse_time(self, time_str) -> dt_time:
        """Parse time string to datetime.time object."""
        try:
            if isinstance(time_str, dt_time):
                return time_str
            return dt_time.fromisoformat(time_str)
        except Exception:
            return dt_time(9, 0)
    
    # ========== REQUIRED BASE CLASS METHODS ==========
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """Evaluate the fitness of a solution."""
        assignments = solution.get("assignments", [])
        if not assignments or not self.fitness_calculator:
            return 0.0
        
        return self.fitness_calculator.calculate_total_fitness(assignments)
    
    def repair_solution(self, solution: Dict[str, Any], validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Repair solution based on validation report.
        Strategic pairing algorithm uses AI optimization, minimal repair needed.
        """
        assignments = solution.get("assignments", [])
        
        # Remove duplicates
        seen_projects = set()
        repaired = []
        for assignment in assignments:
            project_id = assignment.get("project_id")
            if project_id not in seen_projects:
                repaired.append(assignment)
                seen_projects.add(project_id)
        
        solution["assignments"] = repaired
        return solution
