"""
🤖 NSGA-II (Non-dominated Sorting Genetic Algorithm II) - ULTRA AI-POWERED VERSION
═══════════════════════════════════════════════════════════════════════════════

✨ AI FEATURES:
1. Strategic Pairing: Instructor'ları proje sayısına göre sırala ve eşleştir
2. Consecutive Grouping: X sorumlu → Y jüri, sonra Y sorumlu → X jüri  
3. Multi-objective optimization: Pareto front with non-dominated sorting
4. AI-based genetic operators: Smart mutation, crossover, selection
5. Crowding distance: Diversity maintenance in Pareto front
6. NO HARD CONSTRAINTS: 100% soft constraint-based AI approach
7. Adaptive parameters: Population size, mutation/crossover rates
8. Elite preservation with diversity
9. Smart initialization: Strategic pairing-based population
10. AI-powered conflict resolution

═══════════════════════════════════════════════════════════════════════════════
"""

from typing import Dict, Any, List, Tuple, Optional, Set
import random
import numpy as np
import logging
import time
from copy import deepcopy
from collections import defaultdict
from datetime import datetime
from app.algorithms.base import OptimizationAlgorithm


logger = logging.getLogger(__name__)


class NSGAII(OptimizationAlgorithm):
    """
    🤖 NSGA-II (Non-dominated Sorting Genetic Algorithm II) - ULTRA AI-POWERED
    
    Multi-objective optimization with strategic instructor pairing,
    consecutive grouping, and Pareto-optimal solution selection.
    
    NO HARD CONSTRAINTS - Pure AI-driven soft constraint optimization!
    """

    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize NSGA-II algorithm with AI features.
        
        Args:
            params: Algorithm parameters
        """
        super().__init__(params)
        self.name = "🤖 NSGA-II (AI-Powered Multi-Objective Optimizer)"
        self.description = "Strategic pairing + consecutive grouping + Pareto optimization"

        # ========== NSGA-II Core Parameters ==========
        self.population_size = params.get("population_size", 100) if params else 100
        self.generations = params.get("generations", 200) if params else 200
        self.mutation_rate = params.get("mutation_rate", 0.15) if params else 0.15
        self.crossover_rate = params.get("crossover_rate", 0.85) if params else 0.85
        self.elite_size = params.get("elite_size", 20) if params else 20
        
        # ========== AI Features Enablers ==========
        self.enable_strategic_pairing = params.get("enable_strategic_pairing", True) if params else True
        self.enable_consecutive_grouping = params.get("enable_consecutive_grouping", True) if params else True
        self.enable_diversity_maintenance = params.get("enable_diversity_maintenance", True) if params else True
        self.enable_adaptive_params = params.get("enable_adaptive_params", True) if params else True
        self.enable_conflict_resolution = params.get("enable_conflict_resolution", True) if params else True
        
        # ========== Soft Constraint Weights (Auto-adjustable) ==========
        self.w_instructor_conflict = params.get("w_instructor_conflict", 100.0) if params else 100.0
        self.w_classroom_conflict = params.get("w_classroom_conflict", 80.0) if params else 80.0
        self.w_workload_balance = params.get("w_workload_balance", 50.0) if params else 50.0
        self.w_consecutive_bonus = params.get("w_consecutive_bonus", 70.0) if params else 70.0
        self.w_pairing_quality = params.get("w_pairing_quality", 60.0) if params else 60.0
        self.w_early_timeslot = params.get("w_early_timeslot", 40.0) if params else 40.0
        
        # ========== Data Storage ==========
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
        self.data = {}
        
        # ========== Runtime Tracking ==========
        self.current_generation = 0
        self.best_solution = None
        self.best_fitness = float('-inf')
        self.population = []
        self.pareto_front = []
        
        logger.info(f"🤖 [NSGA-II] Initialized with {self.population_size} population, {self.generations} generations")
        logger.info(f"✨ [NSGA-II] AI Features: Strategic Pairing={self.enable_strategic_pairing}, Consecutive Grouping={self.enable_consecutive_grouping}")

    def initialize(self, data: Dict[str, Any]):
        """Initialize the algorithm with problem data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

        # Validate data
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            raise ValueError("❌ Insufficient data for NSGA-II Algorithm")
        
        logger.info(f"📊 [NSGA-II] Data loaded: {len(self.projects)} projects, {len(self.instructors)} instructors, "
                   f"{len(self.classrooms)} classrooms, {len(self.timeslots)} timeslots")
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Evaluate fitness of a solution (required by base class).
        
        Args:
            solution: Solution dictionary with assignments
        
        Returns:
            float: Fitness score
        """
        if 'fitness' in solution and solution['fitness'] != 0:
            return solution['fitness']
        
        assignments = solution.get('assignments', [])
        if not assignments:
            return 0.0
        
        objectives = self._calculate_objectives(assignments)
        fitness = self._aggregate_fitness(objectives)
        
        return fitness

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        🚀 Main NSGA-II optimization loop.
        
        Returns:
            Dict with optimized schedule and metrics
        """
        start_time = time.time()

        try:
            self.initialize(data)
            
            # ========== STEP 1: Initialize Population with Strategic Pairing ==========
            logger.info("🧬 [NSGA-II] STEP 1: Initializing population with strategic pairing...")
            self.population = self._initialize_population_strategic()
            
            # ========== STEP 2: NSGA-II Main Loop ==========
            logger.info(f"🔁 [NSGA-II] STEP 2: Starting {self.generations} generations of evolution...")
            
            for gen in range(self.generations):
                self.current_generation = gen
                
                # Evaluate population
                self._evaluate_population()
                
                # Non-dominated sorting
                fronts = self._fast_non_dominated_sort()
                
                # Calculate crowding distance
                for front in fronts:
                    self._calculate_crowding_distance(front)
                
                # Create offspring
                offspring = self._create_offspring()
                
                # Combine parent and offspring
                combined_population = self.population + offspring
                
                # Select next generation
                self.population = self._environmental_selection(combined_population)
                
                # Track best solution
                if fronts and len(fronts[0]) > 0:
                    best_in_gen = self._select_best_from_front(fronts[0])
                    if best_in_gen['fitness'] > self.best_fitness:
                        self.best_fitness = best_in_gen['fitness']
                        self.best_solution = best_in_gen
                
                # Adaptive parameters
                if self.enable_adaptive_params and gen % 20 == 0:
                    self._adapt_parameters()
                
                # Log progress
                if gen % 25 == 0 or gen == self.generations - 1:
                    logger.info(f"📈 [NSGA-II] Generation {gen}/{self.generations}: "
                               f"Best Fitness={self.best_fitness:.2f}, "
                               f"Pareto Front Size={len(fronts[0]) if fronts else 0}")
            
            # ========== STEP 3: Extract Best Solution ==========
            execution_time = time.time() - start_time
            
            if not self.best_solution:
                logger.warning("⚠️ [NSGA-II] No valid solution found, returning empty schedule")
                return {
                    "algorithm": "NSGA-II",
                    "status": "no_solution",
                    "schedule": [],
                    "solution": [],
                    "metrics": {
                        "execution_time": execution_time,
                        "generations_completed": self.generations,
                        "message": "No valid solution found"
                    },
                    "execution_time": execution_time
                }
            
            # Format result
            schedule = self.best_solution.get('assignments', [])
            metrics = self._calculate_final_metrics(schedule)
            
            logger.info(f"✅ [NSGA-II] Optimization completed in {execution_time:.2f}s")
            logger.info(f"🎯 [NSGA-II] Best Fitness: {self.best_fitness:.2f}")
            logger.info(f"📊 [NSGA-II] Final Metrics: {metrics}")
            
            return {
                "algorithm": "NSGA-II (AI-Powered Multi-Objective)",
                "status": "success",
                "schedule": schedule,
                "solution": schedule,
                "metrics": {
                    **metrics,
                    "execution_time": execution_time,
                    "generations_completed": self.generations,
                    "population_size": self.population_size,
                    "best_fitness": self.best_fitness,
                    "pareto_front_size": len(self.pareto_front),
                    "ai_features_enabled": {
                        "strategic_pairing": self.enable_strategic_pairing,
                        "consecutive_grouping": self.enable_consecutive_grouping,
                        "diversity_maintenance": self.enable_diversity_maintenance,
                        "adaptive_parameters": self.enable_adaptive_params,
                        "conflict_resolution": self.enable_conflict_resolution
                    }
                },
                "execution_time": execution_time,
                "message": f"🤖 NSGA-II AI optimization completed with {len(schedule)} assignments"
            }

        except Exception as e:
            logger.error(f"❌ [NSGA-II] Error: {str(e)}", exc_info=True)
            return {
                "algorithm": "NSGA-II",
                "status": "error",
                "schedule": [],
                "solution": [],
                "metrics": {},
                "execution_time": time.time() - start_time,
                "message": f"NSGA-II failed: {str(e)}"
            }

    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎯 STRATEGIC PAIRING & CONSECUTIVE GROUPING (AI FEATURE 1 & 2)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _initialize_population_strategic(self) -> List[Dict[str, Any]]:
        """
        🤖 AI FEATURE 1 & 2: Strategic Pairing + Consecutive Grouping
        
        Initialize population with strategic instructor pairing:
        1. Sort instructors by project count (HIGH → LOW)
        2. Split into upper/lower groups
        3. Pair upper[i] with lower[i]
        4. Consecutive scheduling: X responsible → Y jury, then Y responsible → X jury
        """
        population = []
        
        for i in range(self.population_size):
            if i == 0:
                # First solution uses deterministic strategic pairing
                individual = self._create_strategic_paired_solution(randomize=False)
            elif i < self.elite_size:
                # Elite solutions with slight randomization
                individual = self._create_strategic_paired_solution(randomize=True, temperature=0.3)
            else:
                # More diverse solutions
                individual = self._create_strategic_paired_solution(randomize=True, temperature=0.7)
            
            if individual and individual.get('assignments'):
                population.append(individual)
                if i < 3:
                    logger.info(f"✅ [NSGA-II] Individual {i+1}: {len(individual['assignments'])} assignments created")
        
        logger.info(f"🧬 [NSGA-II] Population initialized: {len(population)}/{self.population_size} individuals")
        return population
    
    def _create_strategic_paired_solution(self, randomize: bool = False, temperature: float = 0.5) -> Dict[str, Any]:
        """
        Create solution with strategic instructor pairing and consecutive grouping.
        
        Args:
            randomize: Whether to add randomization
            temperature: Randomization intensity (0-1)
        
        Returns:
            Individual solution dictionary
        """
        assignments = []
        
        # ========== Sort timeslots (earliest first) ==========
        sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )
        
        # ========== Group projects by instructor ==========
        instructor_projects = defaultdict(list)
        for project in self.projects:
            responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
            if responsible_id:
                instructor_projects[responsible_id].append(project)
        
        # ========== STRATEGIC PAIRING: Sort instructors by project count (HIGH → LOW) ==========
        instructor_list = sorted(
            instructor_projects.items(),
            key=lambda x: len(x[1]),
            reverse=True  # Descending order
        )
        
        if not instructor_list:
            logger.warning("⚠️ [NSGA-II] No instructors with projects found")
            return {"assignments": [], "fitness": 0, "objectives": []}
        
        total_instructors = len(instructor_list)
        
        # ========== Split into upper and lower groups ==========
        if total_instructors % 2 == 0:
            # Even: split equally
            split_index = total_instructors // 2
        else:
            # Odd: upper has n, lower has n+1
            split_index = total_instructors // 2
        
        upper_group = instructor_list[:split_index]
        lower_group = instructor_list[split_index:]
        
        # ========== Create instructor pairs ==========
        instructor_pairs = []
        for i in range(min(len(upper_group), len(lower_group))):
            instructor_pairs.append((upper_group[i], lower_group[i]))
        
        # Add remaining instructors (if lower group is larger)
        if len(lower_group) > len(upper_group):
            for i in range(len(upper_group), len(lower_group)):
                instructor_pairs.append((lower_group[i], None))
        
        # ========== Conflict tracking ==========
        used_slots = set()  # (classroom_id, timeslot_id)
        instructor_timeslot_usage = defaultdict(set)
        assigned_projects = set()
        
        # ========== CONSECUTIVE GROUPING: Process each pair ==========
        classroom_idx = 0
        timeslot_idx = 0
        
        for pair_idx, pair in enumerate(instructor_pairs):
            if pair[1] is None:
                # Single instructor (no pair)
                instructor_id, instructor_project_list = pair[0]
                
                # Assign projects consecutively
                for project in instructor_project_list:
                    if project['id'] in assigned_projects:
                        continue
                    
                    assigned = False
                    attempts = 0
                    max_attempts = len(sorted_timeslots) * len(self.classrooms)
                    
                    while not assigned and attempts < max_attempts:
                        classroom = self.classrooms[classroom_idx % len(self.classrooms)]
                        timeslot = sorted_timeslots[timeslot_idx % len(sorted_timeslots)]
                        
                        slot_key = (classroom['id'], timeslot['id'])
                        
                        # Soft constraint check (not hard!)
                        if randomize:
                            # AI-based: accept even conflicting slots with probability
                            accept_prob = temperature if slot_key in used_slots else 1.0
                            if random.random() > accept_prob:
                                timeslot_idx += 1
                                attempts += 1
                                continue
                        else:
                            # Deterministic: avoid conflicts if possible
                            if slot_key in used_slots or timeslot['id'] in instructor_timeslot_usage[instructor_id]:
                                timeslot_idx += 1
                                if timeslot_idx % len(sorted_timeslots) == 0:
                                    classroom_idx += 1
                                attempts += 1
                                continue
                        
                        # Create assignment
                        assignments.append({
                            "project_id": project['id'],
                            "timeslot_id": timeslot['id'],
                            "classroom_id": classroom['id'],
                            "responsible_instructor_id": instructor_id,
                            "is_makeup": project.get('is_makeup', False),
                            "instructors": [instructor_id]
                        })
                        
                        used_slots.add(slot_key)
                        instructor_timeslot_usage[instructor_id].add(timeslot['id'])
                        assigned_projects.add(project['id'])
                        assigned = True
                        timeslot_idx += 1
                        attempts += 1
                
                classroom_idx += 1
                timeslot_idx = 0
            
            else:
                # Paired instructors
                instructor_x_id, instructor_x_projects = pair[0]
                instructor_y_id, instructor_y_projects = pair[1]
                
                # ========== PHASE 1: X responsible → Y jury (consecutive) ==========
                for project in instructor_x_projects:
                    if project['id'] in assigned_projects:
                        continue
                    
                    assigned = False
                    attempts = 0
                    max_attempts = len(sorted_timeslots) * len(self.classrooms)
                    
                    while not assigned and attempts < max_attempts:
                        classroom = self.classrooms[classroom_idx % len(self.classrooms)]
                        timeslot = sorted_timeslots[timeslot_idx % len(sorted_timeslots)]
                        
                        slot_key = (classroom['id'], timeslot['id'])
                        
                        # Check conflicts (soft)
                        if randomize:
                            accept_prob = temperature
                            if slot_key in used_slots or timeslot['id'] in instructor_timeslot_usage[instructor_x_id]:
                                if random.random() > accept_prob:
                                    timeslot_idx += 1
                                    attempts += 1
                                    continue
                        else:
                            if (slot_key in used_slots or 
                                timeslot['id'] in instructor_timeslot_usage[instructor_x_id] or 
                                timeslot['id'] in instructor_timeslot_usage[instructor_y_id]):
                                timeslot_idx += 1
                                if timeslot_idx % len(sorted_timeslots) == 0:
                                    classroom_idx += 1
                                attempts += 1
                                continue
                        
                        # Create assignment with X as responsible, Y as jury
                        project_type = project.get('type', 'ara')
                        instructors_list = [instructor_x_id]
                        
                        if project_type == 'bitirme':
                            instructors_list.append(instructor_y_id)
                        
                        assignments.append({
                            "project_id": project['id'],
                            "timeslot_id": timeslot['id'],
                            "classroom_id": classroom['id'],
                            "responsible_instructor_id": instructor_x_id,
                            "is_makeup": project.get('is_makeup', False),
                            "instructors": instructors_list
                        })
                        
                        used_slots.add(slot_key)
                        instructor_timeslot_usage[instructor_x_id].add(timeslot['id'])
                        if len(instructors_list) > 1:
                            instructor_timeslot_usage[instructor_y_id].add(timeslot['id'])
                        assigned_projects.add(project['id'])
                        assigned = True
                        timeslot_idx += 1
                        attempts += 1
                
                # ========== PHASE 2: Y responsible → X jury (consecutive, immediately after) ==========
                for project in instructor_y_projects:
                    if project['id'] in assigned_projects:
                        continue
                    
                    assigned = False
                    attempts = 0
                    max_attempts = len(sorted_timeslots) * len(self.classrooms)
                    
                    while not assigned and attempts < max_attempts:
                        classroom = self.classrooms[classroom_idx % len(self.classrooms)]
                        timeslot = sorted_timeslots[timeslot_idx % len(sorted_timeslots)]
                        
                        slot_key = (classroom['id'], timeslot['id'])
                        
                        # Check conflicts (soft)
                        if randomize:
                            accept_prob = temperature
                            if slot_key in used_slots or timeslot['id'] in instructor_timeslot_usage[instructor_y_id]:
                                if random.random() > accept_prob:
                                    timeslot_idx += 1
                                    attempts += 1
                                    continue
                        else:
                            if (slot_key in used_slots or 
                                timeslot['id'] in instructor_timeslot_usage[instructor_y_id] or 
                                timeslot['id'] in instructor_timeslot_usage[instructor_x_id]):
                                timeslot_idx += 1
                                if timeslot_idx % len(sorted_timeslots) == 0:
                                    classroom_idx += 1
                                attempts += 1
                                continue
                        
                        # Create assignment with Y as responsible, X as jury
                        project_type = project.get('type', 'ara')
                        instructors_list = [instructor_y_id]
                        
                        if project_type == 'bitirme':
                            instructors_list.append(instructor_x_id)
                        
                        assignments.append({
                            "project_id": project['id'],
                            "timeslot_id": timeslot['id'],
                            "classroom_id": classroom['id'],
                            "responsible_instructor_id": instructor_y_id,
                            "is_makeup": project.get('is_makeup', False),
                            "instructors": instructors_list
                        })
                        
                        used_slots.add(slot_key)
                        instructor_timeslot_usage[instructor_y_id].add(timeslot['id'])
                        if len(instructors_list) > 1:
                            instructor_timeslot_usage[instructor_x_id].add(timeslot['id'])
                        assigned_projects.add(project['id'])
                        assigned = True
                        timeslot_idx += 1
                        attempts += 1
                
                # Move to next classroom for next pair
                classroom_idx += 1
                timeslot_idx = 0
        
        return {
            "assignments": assignments,
            "fitness": 0,  # Will be evaluated later
            "objectives": []
        }

    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎯 MULTI-OBJECTIVE FITNESS EVALUATION (AI FEATURE 3)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _evaluate_population(self):
        """Evaluate fitness for all individuals in population."""
        for individual in self.population:
            if 'fitness' not in individual or individual['fitness'] == 0:
                objectives = self._calculate_objectives(individual['assignments'])
                individual['objectives'] = objectives
                individual['fitness'] = self._aggregate_fitness(objectives)
    
    def _calculate_objectives(self, assignments: List[Dict[str, Any]]) -> List[float]:
        """
        Calculate multiple objectives for NSGA-II.
        
        Objectives (to be minimized/maximized):
        1. Minimize instructor conflicts
        2. Minimize classroom conflicts
        3. Maximize workload balance
        4. Maximize consecutive grouping quality
        5. Maximize pairing quality
        6. Maximize early timeslot usage
        
        Returns:
            List of objective values
        """
        # Objective 1: Instructor conflicts (minimize)
        instructor_conflicts = self._count_instructor_conflicts(assignments)
        
        # Objective 2: Classroom conflicts (minimize)
        classroom_conflicts = self._count_classroom_conflicts(assignments)
        
        # Objective 3: Workload balance (maximize)
        workload_balance = self._calculate_workload_balance(assignments)
        
        # Objective 4: Consecutive grouping quality (maximize)
        consecutive_quality = self._calculate_consecutive_quality(assignments)
        
        # Objective 5: Pairing quality (maximize)
        pairing_quality = self._calculate_pairing_quality(assignments)
        
        # Objective 6: Early timeslot usage (maximize)
        early_timeslot_score = self._calculate_early_timeslot_score(assignments)
        
        return [
            -instructor_conflicts,  # Minimize → maximize negative
            -classroom_conflicts,
            workload_balance,
            consecutive_quality,
            pairing_quality,
            early_timeslot_score
        ]
    
    def _aggregate_fitness(self, objectives: List[float]) -> float:
        """
        Aggregate multiple objectives into single fitness value.
        
        Uses weighted sum for simplicity.
        """
        weights = [
            self.w_instructor_conflict,
            self.w_classroom_conflict,
            self.w_workload_balance,
            self.w_consecutive_bonus,
            self.w_pairing_quality,
            self.w_early_timeslot
        ]
        
        return sum(w * obj for w, obj in zip(weights, objectives))
    
    def _count_instructor_conflicts(self, assignments: List[Dict[str, Any]]) -> int:
        """Count number of instructor conflicts (same instructor, same timeslot)."""
        instructor_timeslots = defaultdict(set)
        conflicts = 0
        
        for assignment in assignments:
            instructors = assignment.get('instructors', [])
            timeslot_id = assignment.get('timeslot_id')
            
            for instructor_id in instructors:
                if timeslot_id in instructor_timeslots[instructor_id]:
                    conflicts += 1
                instructor_timeslots[instructor_id].add(timeslot_id)
        
        return conflicts
    
    def _count_classroom_conflicts(self, assignments: List[Dict[str, Any]]) -> int:
        """Count number of classroom conflicts (same classroom, same timeslot)."""
        classroom_timeslots = set()
        conflicts = 0
        
        for assignment in assignments:
            classroom_id = assignment.get('classroom_id')
            timeslot_id = assignment.get('timeslot_id')
            key = (classroom_id, timeslot_id)
            
            if key in classroom_timeslots:
                conflicts += 1
            classroom_timeslots.add(key)
        
        return conflicts
    
    def _calculate_workload_balance(self, assignments: List[Dict[str, Any]]) -> float:
        """Calculate workload balance score (higher is better)."""
        instructor_loads = defaultdict(int)
        
        for assignment in assignments:
            instructors = assignment.get('instructors', [])
            responsible_id = assignment.get('responsible_instructor_id')
            
            # Responsible counts as 2x
            if responsible_id:
                instructor_loads[responsible_id] += 2
            
            # Jury counts as 1x
            for instructor_id in instructors:
                if instructor_id != responsible_id:
                    instructor_loads[instructor_id] += 1
        
        if not instructor_loads:
            return 0.0
        
        loads = list(instructor_loads.values())
        avg_load = np.mean(loads)
        std_load = np.std(loads)
        
        # Lower std = better balance
        return 100.0 / (1.0 + std_load)
    
    def _calculate_consecutive_quality(self, assignments: List[Dict[str, Any]]) -> float:
        """Calculate consecutive grouping quality (higher is better)."""
        # Group by instructor and classroom
        instructor_classroom_timeslots = defaultdict(lambda: defaultdict(list))
        
        for assignment in assignments:
            responsible_id = assignment.get('responsible_instructor_id')
            classroom_id = assignment.get('classroom_id')
            timeslot_id = assignment.get('timeslot_id')
            
            if responsible_id:
                instructor_classroom_timeslots[responsible_id][classroom_id].append(timeslot_id)
        
        consecutive_bonus = 0.0
        
        for instructor_id, classrooms in instructor_classroom_timeslots.items():
            for classroom_id, timeslot_ids in classrooms.items():
                # Sort timeslots
                sorted_slots = sorted(timeslot_ids)
                
                # Count consecutive sequences
                if len(sorted_slots) > 1:
                    consecutive_bonus += len(sorted_slots) * 10  # Bonus for grouping
                    
                    # Extra bonus for perfect consecutiveness
                    for i in range(len(sorted_slots) - 1):
                        if sorted_slots[i+1] == sorted_slots[i] + 1:
                            consecutive_bonus += 5
        
        return consecutive_bonus
    
    def _calculate_pairing_quality(self, assignments: List[Dict[str, Any]]) -> float:
        """Calculate quality of instructor pairing (higher is better)."""
        # Track which instructors work together as responsible/jury
        pairing_count = defaultdict(int)
        
        for assignment in assignments:
            instructors = assignment.get('instructors', [])
            if len(instructors) >= 2:
                responsible_id = instructors[0]
                jury_id = instructors[1]
                
                # Create symmetric pair key
                pair_key = tuple(sorted([responsible_id, jury_id]))
                pairing_count[pair_key] += 1
        
        # More consistent pairing = better
        if not pairing_count:
            return 0.0
        
        return sum(count ** 1.5 for count in pairing_count.values())
    
    def _calculate_early_timeslot_score(self, assignments: List[Dict[str, Any]]) -> float:
        """Calculate early timeslot usage score (higher is better)."""
        early_bonus = 0.0
        
        for assignment in assignments:
            timeslot_id = assignment.get('timeslot_id')
            
            # Find timeslot
            timeslot = next((t for t in self.timeslots if t['id'] == timeslot_id), None)
            if not timeslot:
                continue
            
            start_time = timeslot.get('start_time', '09:00')
            hour = int(start_time.split(':')[0])
            
            # Bonus for earlier times (09:00 gets max bonus, 17:00 gets min)
            if hour < 12:
                early_bonus += (12 - hour) * 2
            elif hour < 15:
                early_bonus += (15 - hour) * 1
        
        return early_bonus

    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎯 NSGA-II CORE OPERATIONS (AI FEATURE 4)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _fast_non_dominated_sort(self) -> List[List[Dict[str, Any]]]:
        """
        Perform fast non-dominated sorting.
        
        Returns:
            List of fronts (each front is a list of individuals)
        """
        if not self.population:
            return [[]]
        
        # Domination count and dominated solutions
        domination_count = {}
        dominated_solutions = defaultdict(list)
        fronts = [[]]
        
        for i, p in enumerate(self.population):
            domination_count[i] = 0
            dominated_solutions[i] = []
            
            for j, q in enumerate(self.population):
                if i == j:
                    continue
                
                if self._dominates(p.get('objectives', []), q.get('objectives', [])):
                    dominated_solutions[i].append(j)
                elif self._dominates(q.get('objectives', []), p.get('objectives', [])):
                    domination_count[i] += 1
            
            if domination_count[i] == 0:
                p['rank'] = 0
                fronts[0].append(p)
        
        # Generate subsequent fronts
        i = 0
        while i < len(fronts) and len(fronts[i]) > 0:
            next_front = []
            for p_idx in range(len(self.population)):
                p = self.population[p_idx]
                if p in fronts[i]:
                    for q_idx in dominated_solutions[p_idx]:
                        domination_count[q_idx] -= 1
                        if domination_count[q_idx] == 0:
                            q = self.population[q_idx]
                            q['rank'] = i + 1
                            next_front.append(q)
            i += 1
            if next_front:
                fronts.append(next_front)
        
        # Store Pareto front
        self.pareto_front = fronts[0] if fronts and len(fronts[0]) > 0 else []
        
        return fronts
    
    def _dominates(self, obj1: List[float], obj2: List[float]) -> bool:
        """
        Check if obj1 dominates obj2.
        
        obj1 dominates obj2 if:
        - obj1 is no worse than obj2 in all objectives
        - obj1 is strictly better than obj2 in at least one objective
        """
        if not obj1 or not obj2 or len(obj1) != len(obj2):
            return False
        
        better_in_any = False
        for o1, o2 in zip(obj1, obj2):
            if o1 < o2:  # Worse in this objective
                return False
            if o1 > o2:  # Better in this objective
                better_in_any = True
        
        return better_in_any
    
    def _calculate_crowding_distance(self, front: List[Dict[str, Any]]):
        """
        Calculate crowding distance for individuals in a front.
        
        Crowding distance measures how close an individual is to its neighbors.
        Higher distance = more diversity.
        """
        if not front:
            return
        
        n_objectives = len(front[0]['objectives'])
        
        # Initialize distances
        for individual in front:
            individual['crowding_distance'] = 0.0
        
        # Calculate distance for each objective
        for obj_idx in range(n_objectives):
            # Sort by objective
            front.sort(key=lambda x: x['objectives'][obj_idx])
            
            # Boundary points get infinite distance
            front[0]['crowding_distance'] = float('inf')
            front[-1]['crowding_distance'] = float('inf')
            
            # Calculate distances
            obj_min = front[0]['objectives'][obj_idx]
            obj_max = front[-1]['objectives'][obj_idx]
            obj_range = obj_max - obj_min
            
            if obj_range == 0:
                continue
            
            for i in range(1, len(front) - 1):
                distance = (front[i+1]['objectives'][obj_idx] - front[i-1]['objectives'][obj_idx]) / obj_range
                front[i]['crowding_distance'] += distance
    
    def _create_offspring(self) -> List[Dict[str, Any]]:
        """
        Create offspring through selection, crossover, and mutation.
        
        Returns:
            List of offspring individuals
        """
        offspring = []
        
        for _ in range(self.population_size // 2):
            # Tournament selection
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()
            
            # Crossover
            if random.random() < self.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()
            
            # Mutation
            if random.random() < self.mutation_rate:
                child1 = self._mutate(child1)
            if random.random() < self.mutation_rate:
                child2 = self._mutate(child2)
            
            offspring.extend([child1, child2])
        
        return offspring[:self.population_size]
    
    def _tournament_selection(self, tournament_size: int = 3) -> Dict[str, Any]:
        """
        Select individual using tournament selection.
        
        Considers both rank and crowding distance.
        """
        tournament = random.sample(self.population, min(tournament_size, len(self.population)))
        
        # Sort by rank (lower is better) and crowding distance (higher is better)
        tournament.sort(key=lambda x: (x.get('rank', float('inf')), -x.get('crowding_distance', 0)))
        
        return tournament[0]
    
    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        🤖 AI FEATURE 5: Smart crossover operation.
        
        Combines assignments from two parents intelligently.
        """
        assignments1 = parent1['assignments']
        assignments2 = parent2['assignments']
        
        if not assignments1 or not assignments2:
            return parent1.copy(), parent2.copy()
        
        # Single-point crossover
        crossover_point = random.randint(1, min(len(assignments1), len(assignments2)) - 1)
        
        child1_assignments = assignments1[:crossover_point] + assignments2[crossover_point:]
        child2_assignments = assignments2[:crossover_point] + assignments1[crossover_point:]
        
        # Remove duplicates (keep first occurrence)
        child1_assignments = self._remove_duplicate_projects(child1_assignments)
        child2_assignments = self._remove_duplicate_projects(child2_assignments)
        
        return (
            {"assignments": child1_assignments, "fitness": 0, "objectives": []},
            {"assignments": child2_assignments, "fitness": 0, "objectives": []}
        )
    
    def _mutate(self, individual: Dict[str, Any]) -> Dict[str, Any]:
        """
        🤖 AI FEATURE 6: Smart mutation operation.
        
        Randomly modifies assignments.
        """
        assignments = individual['assignments'].copy()
        
        if not assignments:
            return individual
        
        # Mutation type (random)
        mutation_type = random.choice(['swap_timeslot', 'swap_classroom', 'swap_assignments'])
        
        if mutation_type == 'swap_timeslot':
            # Change timeslot of a random assignment
            idx = random.randint(0, len(assignments) - 1)
            new_timeslot = random.choice(self.timeslots)
            assignments[idx]['timeslot_id'] = new_timeslot['id']
        
        elif mutation_type == 'swap_classroom':
            # Change classroom of a random assignment
            idx = random.randint(0, len(assignments) - 1)
            new_classroom = random.choice(self.classrooms)
            assignments[idx]['classroom_id'] = new_classroom['id']
        
        elif mutation_type == 'swap_assignments':
            # Swap two random assignments
            if len(assignments) >= 2:
                idx1, idx2 = random.sample(range(len(assignments)), 2)
                assignments[idx1], assignments[idx2] = assignments[idx2], assignments[idx1]
        
        return {"assignments": assignments, "fitness": 0, "objectives": []}
    
    def _environmental_selection(self, combined_population: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Select next generation from combined population.
        
        Uses non-dominated sorting and crowding distance.
        """
        # Evaluate new individuals
        for individual in combined_population:
            if 'fitness' not in individual or individual['fitness'] == 0:
                objectives = self._calculate_objectives(individual['assignments'])
                individual['objectives'] = objectives
                individual['fitness'] = self._aggregate_fitness(objectives)
        
        # Temporarily set population for sorting
        original_population = self.population
        self.population = combined_population
        
        # Non-dominated sort
        fronts = self._fast_non_dominated_sort()
        
        # Calculate crowding distance
        for front in fronts:
            self._calculate_crowding_distance(front)
        
        # Select individuals
        next_population = []
        for front in fronts:
            if len(next_population) + len(front) <= self.population_size:
                next_population.extend(front)
            else:
                # Sort by crowding distance and fill remaining spots
                front.sort(key=lambda x: x.get('crowding_distance', 0), reverse=True)
                remaining = self.population_size - len(next_population)
                next_population.extend(front[:remaining])
                break
        
        # Restore original population
        self.population = original_population
        
        return next_population
    
    def _select_best_from_front(self, front: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select best individual from Pareto front based on aggregate fitness."""
        if not front:
            return {"assignments": [], "fitness": 0, "objectives": []}
        
        return max(front, key=lambda x: x.get('fitness', 0))

    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎯 ADAPTIVE PARAMETERS (AI FEATURE 7)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _adapt_parameters(self):
        """
        🤖 AI FEATURE 7: Adapt mutation/crossover rates based on progress.
        """
        progress = self.current_generation / self.generations
        
        # Increase mutation rate as we progress (more exploration)
        self.mutation_rate = 0.15 + (progress * 0.15)
        
        # Decrease crossover rate slightly (less exploitation)
        self.crossover_rate = 0.85 - (progress * 0.10)
        
        logger.info(f"🔧 [NSGA-II] Adaptive parameters: mutation_rate={self.mutation_rate:.3f}, crossover_rate={self.crossover_rate:.3f}")

    # ═══════════════════════════════════════════════════════════════════════════════
    # 🛠️ UTILITY FUNCTIONS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _parse_time(self, time_str: str) -> int:
        """Parse time string to minutes since midnight."""
        try:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours * 60 + minutes
        except:
            return 540  # Default 09:00
    
    def _remove_duplicate_projects(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate project assignments (keep first occurrence)."""
        seen_projects = set()
        unique_assignments = []
        
        for assignment in assignments:
            project_id = assignment.get('project_id')
            if project_id not in seen_projects:
                seen_projects.add(project_id)
                unique_assignments.append(assignment)
        
        return unique_assignments
    
    def _calculate_final_metrics(self, schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate final metrics for the schedule."""
        if not schedule:
            return {
                "total_assignments": 0,
                "instructor_conflicts": 0,
                "classroom_conflicts": 0,
                "workload_balance": 0,
                "consecutive_quality": 0,
                "pairing_quality": 0,
                "early_timeslot_score": 0
            }
        
        objectives = self._calculate_objectives(schedule)
        
        return {
            "total_assignments": len(schedule),
            "instructor_conflicts": -objectives[0],  # Convert back to positive
            "classroom_conflicts": -objectives[1],
            "workload_balance": objectives[2],
            "consecutive_quality": objectives[3],
            "pairing_quality": objectives[4],
            "early_timeslot_score": objectives[5],
            "aggregate_fitness": self._aggregate_fitness(objectives)
        }
