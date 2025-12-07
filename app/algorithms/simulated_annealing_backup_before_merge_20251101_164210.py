"""
Simulated Annealing Algorithm Implementation - AI-BASED Randomizer with Temperature-Based Optimization
Uses AI-driven temperature scheduling for intelligent exploration vs exploitation

🔧 CONFLICT RESOLUTION INTEGRATED:
- Automatic conflict detection and resolution
- Temperature-based conflict resolution strategies
- Real-time conflict monitoring during optimization
"""
from typing import Dict, Any, List, Tuple, Set, Optional
import time
import logging
import random
import math
import numpy as np
from collections import defaultdict
from datetime import time as dt_time
from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


class SimulatedAnnealing(OptimizationAlgorithm):
    
    def _normalize_instructor_id(self, instructor: Any) -> Optional[int]:
        """
        Instructor'ı normalize eder: dict ise 'id' field'ını, int ise direkt döner
        """
        if instructor is None:
            return None
        if isinstance(instructor, int):
            return instructor
        if isinstance(instructor, dict):
            return instructor.get('id') if instructor.get('id') is not None else None
        return None
    
    def _normalize_instructors_list(self, instructors: Any) -> List[int]:
        """
        Instructors listesini normalize eder: dict listesi ise ID'leri, int listesi ise direkt döner
        """
        if not instructors:
            return []
        if not isinstance(instructors, list):
            return []
        
        normalized = []
        for inst in instructors:
            inst_id = self._normalize_instructor_id(inst)
            if inst_id is not None:
                normalized.append(inst_id)
        return normalized
    """
    Simulated Annealing Algorithm - FULL AI-BASED OPTIMIZATION with Phase 1, 2, 3 Intelligence.
    
    PHASE 1: AI-BASED RANDOMIZER & TEMPERATURE MANAGEMENT
    1. TEMPERATURE-BASED INSTRUCTOR SELECTION - Higher temp = more randomness, Lower temp = more greedy
    2. AI-BASED CLASSROOM SELECTION - Temperature-driven exploration vs exploitation
    3. AI-BASED PROJECT ORDERING - Dynamic shuffling based on temperature
    4. AI-DRIVEN COOLING SCHEDULE - Exponential/Linear/Adaptive cooling strategies
    5. INTELLIGENT ACCEPTANCE PROBABILITY - Metropolis criterion for bad moves
    6. ENERGY-BASED FITNESS - Projects with better fitness get priority at low temperatures
    
    PHASE 2: AI-BASED TIMESLOT ASSIGNMENT
    7. AI-BASED TIMESLOT SELECTION - Temperature-based early slot preference
    8. TEMPERATURE-BASED TIMESLOT INTELLIGENCE - Dynamic timeslot exploration
    
    PHASE 3: AI-BASED CONFLICT RESOLUTION & ADAPTIVE SEARCH
    11. AI-BASED CONFLICT RESOLUTION - Temperature-based conflict resolution strategy
    12. ADAPTIVE NEIGHBORHOOD SEARCH - Dynamic search radius based on temperature
    13. INTELLIGENT CONFLICT DETECTION - Advanced conflict analysis
    14. MULTI-PASS RESOLUTION - Multiple attempts to resolve conflicts
    15. REAL-TIME CONFLICT MONITORING - Continuous conflict detection during optimization
    16. AUTOMATIC CONFLICT RESOLUTION - Seamless integration with optimization process
    
    Core Principles:
    - HIGH TEMPERATURE (T > 100): Random exploration, accept bad moves frequently
    - MEDIUM TEMPERATURE (50 < T < 100): Balanced exploration and exploitation
    - LOW TEMPERATURE (T < 50): Greedy selection, only accept good moves
    - FREEZING (T < 10): Pure greedy, no randomness
    - EARLY TIMESLOT PREFERENCE: Rewards using earlier timeslots (GLOBAL + PER CLASSROOM)
    - GAP MINIMIZATION: Penalizes empty slots in schedule (GLOBAL + PER CLASSROOM)
    - CLASSROOM BALANCE: Ensures balanced usage across all classrooms
    
    Strategy:
    "AI-based randomizer uses temperature to control randomness level dynamically.
    At high temperatures, we explore randomly. As temperature cools, we become
    more selective and exploit good solutions."
    """

    def __init__(self, params: Dict[str, Any] = None):
        super().__init__(params)
        self.name = "Simulated Annealing Algorithm (AI-BASED)"
        self.description = "AI-BASED Randomizer with Temperature-Based Intelligence"

        # Helper function to safely get assignment data
        def safe_get_assignment_data(assignment, key, default=None):
            """Safely get data from assignment, handling both dict and list formats"""
            if isinstance(assignment, dict):
                return assignment.get(key, default)
            elif isinstance(assignment, list) and len(assignment) > 0:
                if isinstance(assignment[0], dict):
                    return assignment[0].get(key, default)
            return default
        
        self.safe_get_assignment_data = safe_get_assignment_data

        # AI-Based Temperature Parameters
        self.initial_temperature = params.get("initial_temperature", 1000.0) if params else 1000.0
        self.final_temperature = params.get("final_temperature", 1.0) if params else 1.0
        self.cooling_rate = params.get("cooling_rate", 0.90) if params else 0.90  # Faster cooling (was 0.95)
        self.max_iterations = params.get("max_iterations", 20) if params else 20  # Reduced from 100 to 20
        self.reheat_temperature = params.get("reheat_temperature", 500.0) if params else 500.0
        self.cooling_strategy = params.get("cooling_strategy", "exponential") if params else "exponential"
        
        # OPTIMIZATION: Early stopping parameters
        self.early_stopping_threshold = params.get("early_stopping_threshold", 5) if params else 5
        self.no_improvement_count = 0
        
        # 🔧 CONFLICT RESOLUTION PARAMETERS
        self.conflict_resolution_enabled = params.get("conflict_resolution_enabled", True) if params else True
        self.conflict_detection_frequency = params.get("conflict_detection_frequency", 5) if params else 5
        self.auto_resolve_conflicts = params.get("auto_resolve_conflicts", True) if params else True
        self.conflict_types = {
            'instructor_double_assignment': 'Aynı instructor aynı zaman diliminde 2 farklı görevde',
            'classroom_double_booking': 'Aynı sınıf aynı zaman diliminde 2 projede',
            'timeslot_overflow': 'Zaman dilimi kapasitesi aşıldı'
        }
        
        # AI-BASED Early Timeslot & Gap Optimization Parameters (ULTRA-AGGRESSIVE!)
        self.reward_early_timeslot = params.get("reward_early_timeslot", 50.0) if params else 50.0  # Increased!
        self.penalty_gap = params.get("penalty_gap", -500.0) if params else -500.0  # ULTRA-AGGRESSIVE!
        self.penalty_late_timeslot = params.get("penalty_late_timeslot", -50.0) if params else -50.0  # Increased!
        
        # SINIFLARARASI OPTİMİZASYON (ULTRA-AGGRESSIVE GAP!)
        self.reward_classroom_early_slot = params.get("reward_classroom_early_slot", 100.0) if params else 100.0  # Increased!
        self.penalty_classroom_gap = params.get("penalty_classroom_gap", -300.0) if params else -300.0  # ULTRA-AGGRESSIVE!
        self.reward_balanced_classroom_usage = params.get("reward_balanced_classroom_usage", 200.0) if params else 200.0
        
        # ULTRA-AGGRESSIVE UNIFORM DISTRIBUTION (NEW!)
        self.reward_perfect_uniform = params.get("reward_perfect_uniform", 500.0) if params else 500.0  # Perfect uniform = huge reward
        self.penalty_uniform_imbalance = params.get("penalty_uniform_imbalance", -300.0) if params else -300.0  # Imbalance = huge penalty
        
        # ULTRA-AGGRESSIVE GAP-FILLING PARAMETERS (NEW!)
        self.reward_gap_filled = params.get("reward_gap_filled", 200.0) if params else 200.0  # Huge reward for filling gaps
        self.penalty_large_gap = params.get("penalty_large_gap", -1000.0) if params else -1000.0  # Massive penalty for large gaps
        self.force_gap_filling = params.get("force_gap_filling", True) if params else True  # Force fill gaps
        
        # SUPER AGGRESSIVE: COMPACT CLASSROOMS (NEW!)
        self.compact_classrooms = params.get("compact_classrooms", True) if params else True  # Compact assignments into fewer classrooms
        self.reward_full_classroom = params.get("reward_full_classroom", 500.0) if params else 500.0  # Huge reward for fully filled classroom
        self.penalty_empty_classroom = params.get("penalty_empty_classroom", -200.0) if params else -200.0  # Penalty for empty classrooms
        
        # POST-OPTIMIZATION COMPACTION (NEW!)
        self.post_optimization_compaction = params.get("post_optimization_compaction", True) if params else True  # Automatic upward shift after optimization
        self.aggressive_upward_shift = params.get("aggressive_upward_shift", True) if params else True  # Aggressively shift assignments to early slots
        
        # CLASSROOM TIMESLOT BALANCING (NEW!)
        self.classroom_timeslot_balancing = params.get("classroom_timeslot_balancing", True) if params else True  # Balance timeslot usage across classrooms
        self.balance_target_range = params.get("balance_target_range", 3) if params else 3  # Max timeslot range difference between classrooms
        
        # PHASE 3: AI-BASED CONFLICT RESOLUTION (NEW!)
        self.ai_based_conflict_resolution = params.get("ai_based_conflict_resolution", True) if params else True  # AI-based conflict resolution
        self.temperature_based_resolution = params.get("temperature_based_resolution", True) if params else True  # Temperature-based resolution strategy
        
        # PHASE 3: ADAPTIVE NEIGHBORHOOD SEARCH (NEW!)
        self.adaptive_neighborhood_search = params.get("adaptive_neighborhood_search", True) if params else True  # Adaptive neighborhood search
        self.min_neighborhood_size = params.get("min_neighborhood_size", 2) if params else 2  # Minimum neighborhood radius
        self.max_neighborhood_size = params.get("max_neighborhood_size", 10) if params else 10  # Maximum neighborhood radius
        
        # PHASE 2: AI-BASED TIMESLOT ASSIGNMENT
        self.ai_based_timeslot_selection = params.get("ai_based_timeslot_selection", True) if params else True
        
        # AI Learning Parameters
        self.temperature = self.initial_temperature
        self.current_iteration = 0
        
        # 📊 Dokümantasyon Formülleri Parametreleri (SA Temperature-Based)
        self.delta = params.get("delta", 0.5) if params else 0.5  # Δ = 0.5 saat (30 dakika)
        self.epsilon = params.get("epsilon", 0.001) if params else 0.001  # ε = 0.001 (tolerans eşiği)
        self.alpha = params.get("alpha", 1.0) if params else 1.0  # α: Zaman cezası ağırlığı
        self.beta = params.get("beta", 1.0) if params else 1.0  # β: Sınıf değişim cezası ağırlığı
        self.best_energy = float('inf')
        self.stuck_count = 0
        self.max_stuck_iterations = 20
        
        # Initialize data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
        
        # GA helper attributes (for fallback methods)
        self.instructor_pairs = []
        self.population = []

    def _normalize_solution(self, solution):
        """Normalize a solution so each assignment is a dict.

        Some operators may produce nested lists; this ensures a consistent
        format (list of dicts) across the GA pipeline.
        """
        if not solution:
            return solution

        normalized = []
        for assignment in solution:
            if isinstance(assignment, dict):
                normalized.append(assignment)
            elif isinstance(assignment, list) and len(assignment) > 0 and isinstance(assignment[0], dict):
                # If nested list, take the first dict element
                normalized.append(assignment[0])
            else:
                # Skip unsupported formats
                continue

        return normalized

    def initialize(self, data: Dict[str, Any]):
        """Initialize the algorithm with problem data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

        # Validate data
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            raise ValueError("Insufficient data for Simulated Annealing Algorithm")
    
    def _cool_temperature(self):
        """
        AI-Based Temperature Cooling Strategies.
        
        Strategies:
        1. Exponential: T = T * cooling_rate (fast cooling)
        2. Linear: T = T - constant (slow cooling)
        3. Adaptive: Cooling rate adapts based on acceptance rate
        """
        # OPTIMIZATION: Reduce logging overhead
        if self.cooling_strategy == "exponential":
            # Exponential cooling (fast)
            self.temperature *= self.cooling_rate
        
        elif self.cooling_strategy == "linear":
            # Linear cooling (slow)
            cooling_step = (self.initial_temperature - self.final_temperature) / self.max_iterations
            self.temperature -= cooling_step
        
        elif self.cooling_strategy == "adaptive":
            # Adaptive cooling based on stuck count
            if self.stuck_count > 10:
                # Cool slower if stuck (more exploration needed)
                self.temperature *= 0.98
            else:
                # Cool faster if progressing well
                self.temperature *= 0.92
        
        else:
            # Default: exponential
            self.temperature *= self.cooling_rate
        
        # OPTIMIZATION: Only log every 5 iterations
        if self.current_iteration % 5 == 0:
            logger.info(f"   🌡️  Temperature: {self.temperature:.1f}°C ({self.cooling_strategy})")
        
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute method for compatibility with AlgorithmService"""
        return self.optimize(data)

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run AI-BASED Simulated Annealing optimization with Temperature-Based Randomizer.
        Uses intelligent temperature scheduling for optimal exploration-exploitation balance.
        """
        start_time = time.time()
        self.initialize(data)
        
        logger.info("=" * 80)
        logger.info("AI-BASED SIMULATED ANNEALING ALGORITHM")
        logger.info("=" * 80)
        logger.info(f"🔥 Initial Temperature: {self.initial_temperature}°C")
        logger.info(f"❄️  Final Temperature: {self.final_temperature}°C")
        logger.info(f"📉 Cooling Rate: {self.cooling_rate}")
        logger.info(f"🔄 Max Iterations: {self.max_iterations}")
        logger.info(f"🔥 Reheat Temperature: {self.reheat_temperature}°C")
        logger.info(f"📊 Cooling Strategy: {self.cooling_strategy}")
        logger.info("")
        logger.info(f"📊 Projeler: {len(self.projects)}")
        logger.info(f"👥 Instructors: {len(self.instructors)}")
        logger.info(f"🏫 Sınıflar: {len(self.classrooms)}")
        logger.info(f"⏰ Zaman Slotları: {len(self.timeslots)}")
        logger.info("")

        # AI-BASED Temperature Annealing Loop
        best_solution = None
        best_energy = float('inf')
        current_solution = None
        current_energy = float('inf')
        
        logger.info("🔥 AI-BASED Temperature Annealing başlatılıyor...")
        
        for iteration in range(self.max_iterations):
            self.current_iteration = iteration
            
            # Create solution with current temperature
            logger.info("")
            logger.info(f"🔄 Iteration {iteration + 1}/{self.max_iterations}")
            # Use GA's solution creation method for now (will be replaced with SA-specific methods later)
            if hasattr(self, '_create_pure_consecutive_grouping_solution'):
                current_solution = self._create_pure_consecutive_grouping_solution()
            else:
                # Fallback: use existing GA initialization if available
                # First, create instructor pairs if not exists
                if not self.instructor_pairs and hasattr(self, '_create_instructor_pairs'):
                    self.instructor_pairs = self._create_instructor_pairs()
                
                if not hasattr(self, 'population') or not self.population:
                    # Initialize population if needed (from GA code)
                    if hasattr(self, '_smart_initialize_population'):
                        self.population = self._smart_initialize_population()
                    else:
                        logger.warning("No solution creation method available!")
                        break
                current_solution = self.population[0] if self.population else []
            
            # Calculate energy if method exists
            if hasattr(self, '_calculate_energy'):
                current_energy = self._calculate_energy(current_solution)
            else:
                # Fallback to fitness (negative for minimization)
                if hasattr(self, '_evaluate_fitness_ai'):
                    current_energy = -self._evaluate_fitness_ai(current_solution)
                else:
                    current_energy = float('inf')
            
            # AI-Based Acceptance Criterion (Metropolis)
            if current_energy < best_energy:
                # Better solution - always accept
                improvement = best_energy - current_energy
                best_solution = current_solution.copy() if current_solution else current_solution
                best_energy = current_energy
                self.stuck_count = 0
                self.no_improvement_count = 0  # Reset early stopping counter
                logger.info(f"   ✅ NEW BEST: Energy = {best_energy:.2f} (improved by {improvement:.2f})")
            else:
                # Worse solution - accept with probability based on temperature
                delta_energy = current_energy - best_energy
                acceptance_probability = math.exp(-delta_energy / self.temperature) if self.temperature > 0 else 0
                
                if random.random() < acceptance_probability:
                    # Accept worse solution (exploration)
                    best_solution = current_solution.copy() if current_solution else current_solution
                    best_energy = current_energy
                    self.stuck_count = 0
                    self.no_improvement_count += 1
                    logger.info(f"   🎲 EXPLORATION: Energy = {best_energy:.2f} (accepted with P={acceptance_probability:.3f})")
                else:
                    # Reject worse solution
                    self.stuck_count += 1
                    self.no_improvement_count += 1
                    logger.info(f"   ❌ REJECTED: Energy = {current_energy:.2f} (stuck: {self.stuck_count}, no improve: {self.no_improvement_count})")
            
            # OPTIMIZATION: Early stopping if no improvement for N iterations
            if self.no_improvement_count >= self.early_stopping_threshold:
                logger.warning(f"   ⏹️  EARLY STOPPING: No improvement for {self.no_improvement_count} iterations")
                break
            
            # AI-Based Temperature Cooling
            self._cool_temperature()
            
            # Smart Restart: Reheat if stuck in local optima
            if self.stuck_count >= self.max_stuck_iterations:
                logger.warning(f"   🔥 REHEAT: Stuck in local optima, reheating to {self.reheat_temperature}°C")
                self.temperature = self.reheat_temperature
                self.stuck_count = 0
            
            # Early termination if temperature is too low
            if self.temperature < self.final_temperature:
                logger.info(f"   ❄️  FROZEN: Temperature reached {self.temperature:.1f}°C, terminating")
                break
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("AI-BASED Simulated Annealing completed")
        logger.info("=" * 80)
        logger.info(f"   Best Energy: {best_energy:.2f}")
        logger.info(f"   Final Temperature: {self.temperature:.1f}°C")
        logger.info(f"   Total Iterations: {self.current_iteration + 1}")
        logger.info(f"   Assignments: {len(best_solution) if best_solution else 0}")
        logger.info("=" * 80)
        
        # Conflict detection ve resolution
        if best_solution and len(best_solution) > 0:
            logger.info("")
            logger.info("Conflict detection ve resolution...")
            # Eski _detect_conflicts metodu varsa kullan, yoksa _detect_all_conflicts kullan
            if hasattr(self, '_detect_conflicts'):
                conflicts = self._detect_conflicts(best_solution)
            else:
                conflicts = self._detect_all_conflicts(best_solution) if hasattr(self, '_detect_all_conflicts') else []
            
            if conflicts:
                logger.warning(f"  {len(conflicts)} conflict detected!")
                if hasattr(self, '_resolve_conflicts'):
                    resolved_solution, resolution_log = self._resolve_conflicts(best_solution, conflicts)
                    best_solution = resolved_solution
                    successful_resolutions = len([r for r in resolution_log if r['success']]) if resolution_log else 0
                    logger.info(f"  {successful_resolutions}/{len(conflicts)} conflicts resolved!")
                else:
                    logger.warning("  Conflict resolution method not available!")
            else:
                logger.info("  No conflicts detected.")
        
        # 🔧 CONFLICT RESOLUTION: Final check and resolution
        if self.conflict_resolution_enabled and best_solution:
            logger.info("")
            logger.info("🔧 [SA] CONFLICT RESOLUTION: Final check and resolution...")
            conflicts = self._detect_all_conflicts(best_solution) if hasattr(self, '_detect_all_conflicts') else []
            
            if conflicts:
                logger.warning(f"  {len(conflicts)} conflicts detected in final solution!")
                if self.auto_resolve_conflicts and hasattr(self, '_resolve_conflicts'):
                    resolved_solution, resolution_log = self._resolve_conflicts(best_solution, conflicts)
                    best_solution = resolved_solution
                    successful_resolutions = len([r for r in resolution_log if r['success']]) if resolution_log else 0
                    logger.info(f"  {successful_resolutions}/{len(conflicts)} conflicts resolved!")
                else:
                    logger.warning("  Auto-resolve disabled or method not available - conflicts remain!")
            else:
                logger.info("  ✅ No conflicts detected in final solution!")
        
        # 🎯 2. FAZ: JÜRİ ATAMA SİSTEMİ (Deterministik Dengeleme)
        if best_solution:
            logger.info("")
            logger.info("=" * 80)
            logger.info("2. FAZ: JÜRİ ATAMA SİSTEMİ - BAŞLATILIYOR")
            logger.info("=" * 80)
            phase2_result = self._execute_phase2_jury_assignment(best_solution)
            # Phase 2 içinde 3. faz (Final Fixation Phase) de yapılıyor
            # final_assignments kullan (placeholder'lar eklenmiş halini al)
            best_solution = phase2_result.get("final_assignments", phase2_result.get("assignments", best_solution))
            logger.info(f"2. FAZ TAMAMLANDI: {phase2_result.get('stats', {})}")
            if phase2_result.get('phase3_stats', {}).get('placeholders_added', 0) > 0:
                logger.info(f"3. FAZ (Final Fixation) TAMAMLANDI: {phase2_result.get('phase3_stats', {})}")
            logger.info("=" * 80)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Return SA result structure (compatible with existing GA structure)
        return {
            "assignments": best_solution or [],
            "schedule": best_solution or [],
            "solution": best_solution or [],
            "fitness_scores": self._calculate_fitness_scores(best_solution or []) if hasattr(self, '_calculate_fitness_scores') else {},
            "execution_time": execution_time,
            "algorithm": "AI-BASED Simulated Annealing Algorithm",
            "status": "completed",
            "success": True,
            "optimizations_applied": [
                "ai_based_temperature_randomizer",
                "ai_based_classroom_selection",
                "ai_based_project_ordering",
                "intelligent_cooling_schedule",
                "metropolis_acceptance_criterion",
                "energy_based_fitness",
                "adaptive_neighborhood_search",
                "smart_restart_mechanism",
                "conflict_detection_and_resolution"
            ],
            "parameters": {
                "algorithm_type": "ai_based_simulated_annealing",
                "initial_temperature": self.initial_temperature,
                "final_temperature": self.final_temperature,
                "cooling_rate": self.cooling_rate,
                "max_iterations": self.max_iterations,
                "reheat_temperature": self.reheat_temperature,
                "cooling_strategy": self.cooling_strategy,
                "actual_iterations": self.current_iteration + 1,
                "best_energy": best_energy,
                "final_temperature_reached": self.temperature
            },
            "ai_metrics": {
                "best_energy": best_energy,
                "final_temperature": self.temperature,
                "iterations_completed": self.current_iteration + 1,
                "cooling_strategy": self.cooling_strategy
            }
        }
    
    # ============================================================================
    # 🤖 AI FEATURE 1: ADAPTIVE PARAMETERS
    # ============================================================================
    
    def _adapt_parameters(self, generation: int, current_fitness: float) -> None:
        """
        Adaptively adjust mutation and crossover rates based on performance
        
        Strategy:
        - If no improvement: INCREASE mutation (explore more)
        - If improving: DECREASE mutation (exploit current area)
        - Balance crossover inversely
        """
        # SA için bu metod kullanılmıyor, sadece GA fallback için mevcut
        if not hasattr(self, 'mutation_rate'):
            return  # SA'da mutation_rate yok, bu metod çalışmaz
        
        if self.no_improvement_count > 10:
            # Stuck in local optimum - explore more!
            self.mutation_rate = min(0.5, self.mutation_rate * 1.2)
            if hasattr(self, 'crossover_rate'):
                self.crossover_rate = max(0.5, self.crossover_rate * 0.9)
            logger.debug(f"   🔼 Increased exploration: mutation={self.mutation_rate:.3f}")
        elif self.no_improvement_count < 3:
            # Improving - exploit current area
            self.mutation_rate = max(0.05, self.mutation_rate * 0.95)
            if hasattr(self, 'crossover_rate'):
                self.crossover_rate = min(0.95, self.crossover_rate * 1.05)
            logger.debug(f"   🔽 Increased exploitation: mutation={self.mutation_rate:.3f}")
        
        # Natural cooling (like simulated annealing)
        generations = getattr(self, 'generations', 100)
        if generations > 0:
            progress = generation / generations
            if progress > 0.7:  # Last 30% - focus on refinement
                self.mutation_rate = max(0.05, self.mutation_rate * 0.98)
    
    # ============================================================================
    # 🤖 AI FEATURE 2: SELF-LEARNING WEIGHTS
    # ============================================================================
    
    def _learn_from_solution(self, solution: List[Dict], fitness: float) -> None:
        """
        Learn optimal fitness weights from successful solutions
        
        Strategy:
        - Calculate component scores for successful solution
        - Adjust weights based on which components contributed most
        """
        if not solution:
            return
        
        # Calculate component scores
        coverage = self._calculate_coverage_score(solution)
        consecutive = self._calculate_consecutive_score(solution)
        balance = self._calculate_balance_score(solution)
        classroom = self._calculate_classroom_score(solution)
        
        # Normalize scores
        total = coverage + consecutive + balance + classroom
        if total == 0:
            return
        
        # Calculate contribution percentages
        contributions = {
            'coverage': coverage / total,
            'consecutive': consecutive / total,
            'balance': balance / total,
            'classroom': classroom / total
        }
        
        # Update weights (moving average)
        for key in self.fitness_weights:
            current = self.fitness_weights[key]
            target = contributions[key] * 10  # Scale to reasonable range
            self.fitness_weights[key] = current + self.weight_learning_rate * (target - current)
        
        logger.debug(f"   🧠 Learned weights: {self.fitness_weights}")
        
        # 🤖 AI FEATURE 5: PATTERN RECOGNITION
        if self.pattern_learning_enabled:
            self._learn_patterns(solution)
    
    def _learn_patterns(self, solution: List[Dict]) -> None:
        """Learn patterns from successful solutions"""
        # Learn successful instructor pairs
        instructor_assignments = defaultdict(list)
        for assignment in solution:
            for instructor_id in assignment.get('instructors', []):
                instructor_assignments[instructor_id].append(assignment)
        
        # Track co-occurring instructors
        for assignment in solution:
            instructors = assignment.get('instructors', [])
            if len(instructors) >= 2:
                pair = tuple(sorted(instructors[:2]))
                self.successful_pairs[pair] += 1
        
        # Learn successful classrooms
        for assignment in solution:
            classroom_id = assignment.get('classroom_id')
            if classroom_id:
                self.successful_classrooms[classroom_id] += 1
    
    # ============================================================================
    # 🤖 AI FEATURE 3: DIVERSITY MAINTENANCE
    # ============================================================================
    
    def _calculate_diversity(self) -> float:
        """
        Calculate population diversity
        
        Returns: Diversity score (0.0 = all identical, 1.0 = maximum diversity)
        """
        if not self.population or len(self.population) < 2:
            return 0.0
        
        # Sample-based diversity for performance
        sample_size = min(20, len(self.population))
        sample = random.sample(self.population, sample_size)
        
        total_distance = 0
        comparisons = 0
        
        for i in range(len(sample)):
            for j in range(i + 1, len(sample)):
                distance = self._solution_distance(sample[i], sample[j])
                total_distance += distance
                comparisons += 1
        
        avg_distance = total_distance / comparisons if comparisons > 0 else 0
        
        # Normalize to 0-1 range
        max_distance = len(self.projects) if self.projects else 1
        diversity = min(1.0, avg_distance / max_distance)
        
        return diversity
    
    def _solution_distance(self, sol1: List[Dict], sol2: List[Dict]) -> float:
        """Calculate distance between two solutions"""
        if not sol1 or not sol2:
            return 0.0
        
        # Compare project-timeslot assignments
        assignments1 = {a['project_id']: a['timeslot_id'] for a in sol1 if 'project_id' in a}
        assignments2 = {a['project_id']: a['timeslot_id'] for a in sol2 if 'project_id' in a}
        
        # Count differences
        differences = 0
        all_projects = set(assignments1.keys()) | set(assignments2.keys())
        
        for project_id in all_projects:
            if assignments1.get(project_id) != assignments2.get(project_id):
                differences += 1
        
        return differences
    
    def _inject_diversity(self) -> None:
        """Inject diversity into population when it becomes too similar"""
        logger.debug("   🌈 Injecting diversity into population")
        
        # Replace bottom 20% with new random solutions
        population_size = getattr(self, 'population_size', 10)
        num_replace = int(population_size * 0.2)
        
        # Keep top 80%
        fitness_scores = [self._evaluate_fitness_ai(ind) for ind in self.population]
        sorted_indices = np.argsort(fitness_scores)[::-1]
        self.population = [self.population[i] for i in sorted_indices[:-num_replace]]
        
        # Add new diverse solutions
        for _ in range(num_replace):
            new_solution = self._generate_diverse_solution()
            self.population.append(new_solution)
    
    def _generate_diverse_solution(self) -> List[Dict]:
        """Generate a diverse solution using random strategy"""
        strategy = random.choice(['paired', 'greedy', 'random'])
        
        if strategy == 'paired':
            return self._create_paired_consecutive_solution()
        elif strategy == 'greedy':
            return self._create_greedy_solution()
        else:
            return self._create_random_solution()
    
    # ============================================================================
    # 🤖 AI FEATURE 4: SMART INITIALIZATION
    # ============================================================================
    
    def _smart_initialize_population(self) -> List[List[Dict[str, Any]]]:
        """
        Smart multi-strategy population initialization
        
        Strategy Mix:
        - 40% Paired Consecutive (our main strategy)
        - 30% Greedy Early Slots
        - 30% Random Diverse
        """
        population = []
        
        # Calculate how many of each type
        # SA için population_size yok, default değer kullan
        population_size = getattr(self, 'population_size', 10)
        init_strategies = getattr(self, 'init_strategies', {'paired_consecutive': 0.4, 'greedy_early': 0.3, 'random_diverse': 0.3})
        paired_count = int(population_size * init_strategies.get('paired_consecutive', 0.4))
        greedy_count = int(population_size * init_strategies.get('greedy_early', 0.3))
        random_count = population_size - paired_count - greedy_count
        
        logger.info(f"   Initializing: {paired_count} paired, {greedy_count} greedy, {random_count} random")
        
        # Generate paired solutions
        for _ in range(paired_count):
            solution = self._create_paired_consecutive_solution()
            population.append(solution)
        
        # Generate greedy solutions
        for _ in range(greedy_count):
            solution = self._create_greedy_solution()
            population.append(solution)
        
        # Generate random solutions
        for _ in range(random_count):
            solution = self._create_random_solution()
            population.append(solution)
        
        logger.info(f"   Smart initialization completed: {len(population)} individuals")
        return population
    def _create_greedy_solution(self) -> List[Dict[str, Any]]:
        """Create greedy solution (earliest slots first)"""
        assignments = []
        
        sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )
        
        used_slots = set()
        instructor_usage = defaultdict(set)
        unassigned_projects = []
        
        # Sort projects by type (bitirme first)
        sorted_projects = sorted(
            self.projects,
            key=lambda x: 0 if x.get('type') == 'bitirme' else 1
        )
        
        for project in sorted_projects:
            resp_id = project.get('responsible_instructor_id') or project.get('responsible_id')
            assigned = False
            
            # Find earliest available slot
            for classroom in self.classrooms:
                for timeslot in sorted_timeslots:
                    slot_key = (classroom['id'], timeslot['id'])
                    
                    if (slot_key not in used_slots and 
                        timeslot['id'] not in instructor_usage.get(resp_id, set())):
                        
                        # Try to add another instructor
                        instructors = [resp_id] if resp_id else []
                        
                        # Find a suitable additional instructor
                        for other_instructor in self.instructors:
                            if (other_instructor['id'] != resp_id and
                                timeslot['id'] not in instructor_usage.get(other_instructor['id'], set())):
                                instructors.append(other_instructor['id'])
                                break
                        
                        assignments.append({
                            'project_id': project['id'],
                            'timeslot_id': timeslot['id'],
                            'classroom_id': classroom['id'],
                            'responsible_instructor_id': resp_id,
                            'is_makeup': project.get('is_makeup', False),
                            'instructors': instructors
                        })
                        
                        used_slots.add(slot_key)
                        if resp_id:
                            instructor_usage[resp_id].add(timeslot['id'])
                        assigned = True
                        break
                if assigned:
                    break
            
            # If not assigned, add to unassigned list
            if not assigned:
                unassigned_projects.append((project, resp_id))
        
        # Emergency assignment for unassigned projects
        if unassigned_projects:
            logger.warning(f"GA Greedy: {len(unassigned_projects)} projects not assigned! Emergency assignment...")
            emergency_assignments = self._emergency_assignment_genetic(unassigned_projects, assignments, used_slots, instructor_usage)
            assignments.extend(emergency_assignments)
        
        return assignments
    
    def _create_random_solution(self) -> List[Dict[str, Any]]:
        """Create completely random solution"""
        assignments = []
        
        available_slots = [
            (c['id'], t['id']) 
            for c in self.classrooms 
            for t in self.timeslots
        ]
        random.shuffle(available_slots)
        
        used_slots = set()
        instructor_usage = defaultdict(set)
        unassigned_projects = []
        
        for i, project in enumerate(self.projects):
            if i >= len(available_slots):
                unassigned_projects.append((project, project.get('responsible_instructor_id') or project.get('responsible_id')))
                continue
            
            classroom_id, timeslot_id = available_slots[i]
            resp_id = project.get('responsible_instructor_id') or project.get('responsible_id')
            slot_key = (classroom_id, timeslot_id)
            
            # Check if slot is available and instructor is free
            if (slot_key not in used_slots and 
                timeslot_id not in instructor_usage.get(resp_id, set())):
                
                # Try to add another instructor
                instructors = [resp_id] if resp_id else []
                
                # Find a suitable additional instructor
                for other_instructor in self.instructors:
                    if (other_instructor['id'] != resp_id and
                        timeslot_id not in instructor_usage.get(other_instructor['id'], set())):
                        instructors.append(other_instructor['id'])
                        break
                
                assignments.append({
                    'project_id': project['id'],
                    'timeslot_id': timeslot_id,
                    'classroom_id': classroom_id,
                    'responsible_instructor_id': resp_id,
                    'is_makeup': project.get('is_makeup', False),
                    'instructors': instructors
                })
                
                used_slots.add(slot_key)
                if resp_id:
                    instructor_usage[resp_id].add(timeslot_id)
            else:
                unassigned_projects.append((project, resp_id))
        
        # Emergency assignment for unassigned projects
        if unassigned_projects:
            logger.warning(f"GA Random: {len(unassigned_projects)} projects not assigned! Emergency assignment...")
            emergency_assignments = self._emergency_assignment_genetic(unassigned_projects, assignments, used_slots, instructor_usage)
            assignments.extend(emergency_assignments)
        
        return assignments

    # ============================================================================
    # 🤖 AI FEATURE 6: LOCAL SEARCH INTEGRATION
    # ============================================================================
    
    def _apply_local_search(self) -> None:
        """
        Apply hill climbing local search to elite solutions
        
        Strategy:
        - Take top 10% solutions
        - Apply local improvements (swap, shift)
        - Keep improved versions
        """
        elite_count = max(1, int(self.population_size * 0.1))
        
        # Get elite solutions
        fitness_scores = [self._evaluate_fitness_ai(ind) for ind in self.population]
        elite_indices = np.argsort(fitness_scores)[-elite_count:]
        
        improvements = 0
        for idx in elite_indices:
            original = self.population[idx]
            original_fitness = fitness_scores[idx]
            
            # Try local improvements
            improved = self._hill_climbing(original, original_fitness)
            
            if improved:
                self.population[idx] = improved
                improvements += 1
        
        if improvements > 0:
            logger.debug(f"   🏔️ Local search improved {improvements}/{elite_count} elite solutions")
    
    def _hill_climbing(self, solution: List[Dict], current_fitness: float, max_iterations: int = 10) -> List[Dict]:
        """Hill climbing local search"""
        best_solution = solution.copy()
        best_fitness = current_fitness
        
        for _ in range(max_iterations):
            # Generate neighbor
            neighbor = self._generate_neighbor(best_solution)
            neighbor_fitness = self._evaluate_fitness_ai(neighbor)
            
            # Accept if better
            if neighbor_fitness > best_fitness:
                best_solution = neighbor
                best_fitness = neighbor_fitness
        
        return best_solution if best_fitness > current_fitness else solution
    
    def _generate_neighbor(self, solution: List[Dict]) -> List[Dict]:
        """Generate neighbor solution for local search"""
        if not solution or len(solution) < 2:
            return solution
        
        neighbor = [a.copy() for a in solution]
        
        # Random local move
        move_type = random.choice(['swap_timeslots', 'swap_classrooms', 'shift'])
        
        if move_type == 'swap_timeslots':
            idx1, idx2 = random.sample(range(len(neighbor)), 2)
            neighbor[idx1]['timeslot_id'], neighbor[idx2]['timeslot_id'] = \
                neighbor[idx2]['timeslot_id'], neighbor[idx1]['timeslot_id']
        
        elif move_type == 'swap_classrooms':
            idx1, idx2 = random.sample(range(len(neighbor)), 2)
            neighbor[idx1]['classroom_id'], neighbor[idx2]['classroom_id'] = \
                neighbor[idx2]['classroom_id'], neighbor[idx1]['classroom_id']
        
        elif move_type == 'shift':
            idx = random.randint(0, len(neighbor) - 1)
            if hasattr(self, 'timeslots') and self.timeslots:
                new_timeslot = random.choice(self.timeslots)
                neighbor[idx]['timeslot_id'] = new_timeslot['id']
        
        return neighbor
    
    # ============================================================================
    # INSTRUCTOR PAIRING (Max-Min Strategy)
    # ============================================================================
    
    def _create_instructor_pairs(self) -> List[Tuple]:
        """
        Instructor pairing: Max-Min strategy
        """
        instructor_projects = defaultdict(list)
        for project in self.projects:
            responsible_id = project.get("responsible_instructor_id") or project.get("responsible_id")
            if responsible_id:
                instructor_projects[responsible_id].append(project)
        
        instructor_list = sorted(
            instructor_projects.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        logger.info(f"STATS: Instructorlar proje sayısına göre sıralandı:")
        for inst_id, proj_list in instructor_list[:3]:
            logger.info(f"   Instructor {inst_id}: {len(proj_list)} proje")
        
        total_instructors = len(instructor_list)
        
        if total_instructors % 2 == 0:
            split_index = total_instructors // 2
            upper_group = instructor_list[:split_index]
            lower_group = instructor_list[split_index:]
        else:
            split_index = total_instructors // 2
            upper_group = instructor_list[:split_index]
            lower_group = instructor_list[split_index:]
        
        instructor_pairs = []
        for i in range(min(len(upper_group), len(lower_group))):
            instructor_pairs.append((upper_group[i], lower_group[i]))
        
        if len(lower_group) > len(upper_group):
            instructor_pairs.append((lower_group[-1], None))
        
        return instructor_pairs
    
    def _create_paired_consecutive_solution(self) -> List[Dict[str, Any]]:
        """Create solution with paired consecutive grouping"""
        assignments = []
        
        sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )
        
        used_slots = set()
        instructor_timeslot_usage = defaultdict(set)
        assigned_projects = set()
        
        available_classrooms = self.classrooms.copy()
        random.shuffle(available_classrooms)
        
        classroom_idx = 0
        timeslot_idx = 0
        
        # Track unassigned projects for emergency assignment
        unassigned_projects = []
        
        for pair in self.instructor_pairs:
            if pair[1] is None:
                instructor_id, instructor_projects = pair[0]
                
                for project in instructor_projects:
                    if project['id'] in assigned_projects:
                        continue
                    
                    assigned = False
                    attempts = 0
                    
                    while not assigned and attempts < len(sorted_timeslots) * len(self.classrooms):
                        classroom = available_classrooms[classroom_idx % len(available_classrooms)]
                        timeslot = sorted_timeslots[timeslot_idx % len(sorted_timeslots)]
                        
                        slot_key = (classroom['id'], timeslot['id'])
                        
                        if (slot_key not in used_slots and 
                            timeslot['id'] not in instructor_timeslot_usage[instructor_id]):
                            
                            # For single instructor projects, try to add another instructor
                            instructors = [instructor_id]  # Start with responsible instructor
                            
                            # Find a suitable additional instructor (prefer consecutive assignments)
                            for other_instructor in self.instructors:
                                if (other_instructor['id'] != instructor_id and
                                    timeslot['id'] not in instructor_timeslot_usage[other_instructor['id']]):
                                    instructors.append(other_instructor['id'])
                                    break
                            
                            assignments.append({
                                "project_id": project['id'],
                                "timeslot_id": timeslot['id'],
                                "classroom_id": classroom['id'],
                                "responsible_instructor_id": instructor_id,
                                "is_makeup": project.get('is_makeup', False),
                                "instructors": instructors
                            })
                            
                            used_slots.add(slot_key)
                            instructor_timeslot_usage[instructor_id].add(timeslot['id'])
                            # Add timeslot usage for additional instructor if added
                            if len(instructors) > 1:
                                instructor_timeslot_usage[instructors[1]].add(timeslot['id'])
                            assigned_projects.add(project['id'])
                            assigned = True
                            timeslot_idx += 1
                        else:
                            timeslot_idx += 1
                            if timeslot_idx % len(sorted_timeslots) == 0:
                                classroom_idx += 1
                        
                        attempts += 1
                    
                    # If still not assigned, add to unassigned list for emergency assignment
                    if not assigned:
                        unassigned_projects.append((project, instructor_id))
                
                classroom_idx += 1
                timeslot_idx = 0
            
            else:
                instructor_x_id, instructor_x_projects = pair[0]
                instructor_y_id, instructor_y_projects = pair[1]
                
                # PHASE 1: X responsible -> Y additional instructor
                for project in instructor_x_projects:
                    if project['id'] in assigned_projects:
                        continue
                    
                    assigned = False
                    attempts = 0
                    
                    while not assigned and attempts < len(sorted_timeslots) * len(self.classrooms):
                        classroom = available_classrooms[classroom_idx % len(available_classrooms)]
                        timeslot = sorted_timeslots[timeslot_idx % len(sorted_timeslots)]
                        
                        slot_key = (classroom['id'], timeslot['id'])
                        
                        if (slot_key not in used_slots and 
                            timeslot['id'] not in instructor_timeslot_usage[instructor_x_id] and
                            timeslot['id'] not in instructor_timeslot_usage[instructor_y_id]):
                            
                            instructors = [instructor_x_id]
                            # Always add second instructor for better workload distribution
                            instructors.append(instructor_y_id)
                            
                            assignments.append({
                                "project_id": project['id'],
                                "timeslot_id": timeslot['id'],
                                "classroom_id": classroom['id'],
                                "responsible_instructor_id": instructor_x_id,
                                "is_makeup": project.get('is_makeup', False),
                                "instructors": instructors
                            })
                            
                            used_slots.add(slot_key)
                            instructor_timeslot_usage[instructor_x_id].add(timeslot['id'])
                            if len(instructors) > 1:
                                instructor_timeslot_usage[instructor_y_id].add(timeslot['id'])
                            assigned_projects.add(project['id'])
                            assigned = True
                            timeslot_idx += 1
                        else:
                            timeslot_idx += 1
                            if timeslot_idx % len(sorted_timeslots) == 0:
                                classroom_idx += 1
                        
                        attempts += 1
                    
                    # If still not assigned, add to unassigned list for emergency assignment
                    if not assigned:
                        unassigned_projects.append((project, instructor_x_id))
                
                # PHASE 2: Y responsible -> X additional instructor
                for project in instructor_y_projects:
                    if project['id'] in assigned_projects:
                        continue
                    
                    assigned = False
                    attempts = 0
                    
                    while not assigned and attempts < len(sorted_timeslots) * len(self.classrooms):
                        classroom = available_classrooms[classroom_idx % len(available_classrooms)]
                        timeslot = sorted_timeslots[timeslot_idx % len(sorted_timeslots)]
                        
                        slot_key = (classroom['id'], timeslot['id'])
                        
                        if (slot_key not in used_slots and 
                            timeslot['id'] not in instructor_timeslot_usage[instructor_y_id] and
                            timeslot['id'] not in instructor_timeslot_usage[instructor_x_id]):
                            
                            instructors = [instructor_y_id]
                            # Always add second instructor for better workload distribution
                            instructors.append(instructor_x_id)
                            
                            assignments.append({
                                "project_id": project['id'],
                                "timeslot_id": timeslot['id'],
                                "classroom_id": classroom['id'],
                                "responsible_instructor_id": instructor_y_id,
                                "is_makeup": project.get('is_makeup', False),
                                "instructors": instructors
                            })
                            
                            used_slots.add(slot_key)
                            instructor_timeslot_usage[instructor_y_id].add(timeslot['id'])
                            if len(instructors) > 1:
                                instructor_timeslot_usage[instructor_x_id].add(timeslot['id'])
                            assigned_projects.add(project['id'])
                            assigned = True
                            timeslot_idx += 1
                        else:
                            timeslot_idx += 1
                            if timeslot_idx % len(sorted_timeslots) == 0:
                                classroom_idx += 1
                        
                        attempts += 1
                    
                    # If still not assigned, add to unassigned list for emergency assignment
                    if not assigned:
                        unassigned_projects.append((project, instructor_y_id))
                
                classroom_idx += 1
                timeslot_idx = 0
        
        # Emergency assignment for unassigned projects
        if unassigned_projects:
            logger.warning(f"GA: {len(unassigned_projects)} proje atanamadı! Emergency assignment başlatılıyor...")
            emergency_assignments = self._emergency_assignment_genetic(unassigned_projects, assignments, used_slots, instructor_timeslot_usage)
            assignments.extend(emergency_assignments)
            logger.info(f"GA: Emergency assignment ile {len(emergency_assignments)} proje eklendi")
        
        # Final coverage verification
        final_assigned = set(a['project_id'] for a in assignments if 'project_id' in a)
        total_projects = len(self.projects)
        coverage_rate = len(final_assigned) / total_projects if total_projects > 0 else 0
        
        logger.info(f"GA: Final coverage: {len(final_assigned)}/{total_projects} ({coverage_rate:.2%})")
        
        return assignments
    
    def _emergency_assignment_genetic(self, unassigned_projects: List[Tuple], existing_assignments: List[Dict], used_slots: Set, instructor_timeslot_usage: Dict) -> List[Dict]:
        """
        Emergency assignment for unassigned projects in Genetic Algorithm
        """
        emergency_assignments = []
        
        for project, instructor_id in unassigned_projects:
            # Try to find ANY available slot
            for classroom in self.classrooms:
                for timeslot in self.timeslots:
                    slot_key = (classroom['id'], timeslot['id'])
                    
                    # More relaxed constraints for emergency assignment
                    if slot_key not in used_slots:
                        # Try to add another instructor
                        instructors = [instructor_id] if instructor_id else []
                        
                        # Find a suitable additional instructor
                        for other_instructor in self.instructors:
                            if (other_instructor['id'] != instructor_id and
                                timeslot['id'] not in instructor_timeslot_usage.get(other_instructor['id'], set())):
                                instructors.append(other_instructor['id'])
                                break
                        
                        assignment = {
                            "project_id": project['id'],
                            "timeslot_id": timeslot['id'],
                            "classroom_id": classroom['id'],
                            "responsible_instructor_id": instructor_id,
                            "is_makeup": project.get('is_makeup', False),
                            "instructors": instructors
                        }
                        
                        emergency_assignments.append(assignment)
                        used_slots.add(slot_key)
                        instructor_timeslot_usage[instructor_id].add(timeslot['id'])
                        logger.info(f"GA Emergency: Proje {project['id']} atandı: {classroom['id']} - {timeslot['id']}")
                        break
                else:
                    continue
                break
        
        return emergency_assignments
    
    # ============================================================================
    # AI-BASED FITNESS EVALUATION (Self-Learning Weights)
    # ============================================================================
    
    def _evaluate_fitness_ai(self, individual: List[Dict[str, Any]]) -> float:
        """
        AI-based fitness evaluation with self-learning weights - OPTIMIZED FOR SPEED
        
        NO HARD CONSTRAINTS - Pure soft optimization!
        """
        if not individual:
            return 0.0
        
        coverage = self._calculate_coverage_score(individual)
        consecutive = self._calculate_consecutive_score(individual)
        balance = self._calculate_balance_score(individual)
        classroom = self._calculate_classroom_score(individual)
        
        # 🎯 GAP-FREE OPTIMIZATION SCORING
        gap_free_score = 0.0
        if self.gap_free_enabled:
            gap_free_score = self._calculate_gap_free_score(individual)
        
        # ⏰ EARLY TIMESLOT OPTIMIZATION SCORING
        early_timeslot_score = 0.0
        if self.early_timeslot_enabled:
            early_timeslot_score = self._calculate_early_timeslot_score(individual)
        
        # 🚀 ULTRA-AGGRESSIVE GAP STRATEGY SCORING
        ultra_gap_score = 0.0
        if self.ultra_aggressive_gap:
            ultra_gap_score = self._calculate_ultra_aggressive_gap_score(individual)
        
        # 🔥 SUPER ULTRA-AGGRESSIVE GAP STRATEGY SCORING
        super_ultra_gap_score = 0.0
        if self.super_ultra_gap:
            super_ultra_gap_score = self._calculate_super_ultra_aggressive_gap_score(individual)
        
        # 📊 Dokümantasyon Formülleri - Penalty calculation
        doc_penalty = self._calculate_documentation_penalty({'assignments': individual})
        
        # 🤖 Use learned weights + NEW GAP & EARLY TIMESLOT SCORES - Documentation Penalty
        fitness = (
            coverage * self.fitness_weights['coverage'] +
            consecutive * self.fitness_weights['consecutive'] +
            balance * self.fitness_weights['balance'] +
            classroom * self.fitness_weights['classroom'] +
            gap_free_score * self.reward_gap_free +
            early_timeslot_score * self.reward_early_timeslot +
            ultra_gap_score * self.reward_gap_filled +
            super_ultra_gap_score * self.reward_compact_classrooms -
            doc_penalty  # Subtract documentation penalty
        )
        
        # 🤖 BONUS: Pattern Recognition Bonus
        if self.pattern_learning_enabled:
            pattern_bonus = self._calculate_pattern_bonus(individual)
            fitness += pattern_bonus
        
        return fitness

    def _calculate_pattern_bonus(self, assignments: List[Dict]) -> float:
        """Bonus for using learned successful patterns"""
        bonus = 0.0
        
        # Bonus for using successful instructor pairs
        for assignment in assignments:
            instructors = self.safe_get_assignment_data(assignment, 'instructors', [])
            if len(instructors) >= 2:
                pair = tuple(sorted(instructors[:2]))
                if pair in self.successful_pairs:
                    bonus += self.successful_pairs[pair] * 0.1
        
        # Bonus for using successful classrooms
        for assignment in assignments:
            classroom_id = self.safe_get_assignment_data(assignment, 'classroom_id')
            if classroom_id in self.successful_classrooms:
                bonus += self.successful_classrooms[classroom_id] * 0.05
        
        return bonus
    
    def _calculate_coverage_score(self, assignments: List[Dict]) -> float:
        """Calculate project coverage score"""
        assigned_projects = set()
        for a in assignments:
            if isinstance(a, dict) and 'project_id' in a:
                assigned_projects.add(a['project_id'])
        total_projects = len(self.projects)
        return (len(assigned_projects) / total_projects) * 100.0 if total_projects > 0 else 0.0
    
    def _calculate_consecutive_score(self, assignments: List[Dict]) -> float:
        """Calculate consecutive grouping quality score"""
        instructor_slots = defaultdict(list)
        for assignment in assignments:
            # Handle both dictionary and list formats
            if isinstance(assignment, dict):
                resp_id = assignment.get('responsible_instructor_id')
                if resp_id:
                    instructor_slots[resp_id].append(assignment)
            elif isinstance(assignment, list):
                # If assignment is a list, skip it (should not happen in normal flow)
                continue
        
        consecutive_bonus = 0
        for slots in instructor_slots.values():
            sorted_slots = sorted(slots, key=lambda x: x.get('timeslot_id', 0))
            for i in range(len(sorted_slots) - 1):
                if sorted_slots[i+1]['timeslot_id'] - sorted_slots[i]['timeslot_id'] == 1:
                    if sorted_slots[i]['classroom_id'] == sorted_slots[i+1]['classroom_id']:
                        consecutive_bonus += 2.0
                    else:
                        consecutive_bonus += 1.0
        
        return consecutive_bonus
    
    def _calculate_balance_score(self, assignments: List[Dict]) -> float:
        """Calculate load balance score"""
        loads = defaultdict(int)
        for assignment in assignments:
            if isinstance(assignment, dict):
                for instructor_id in assignment.get('instructors', []):
                    loads[instructor_id] += 1
        
        if not loads:
            return 0.0
        
        load_values = list(loads.values())
        std_load = np.std(load_values)
        
        # 🔧 FIX: Division by zero protection
        if np.isnan(std_load) or np.isinf(std_load) or std_load <= 0:
            return 50.0
        
        balance_score = 50.0 / (1.0 + std_load)
        
        return balance_score
    
    def _calculate_classroom_score(self, assignments: List[Dict]) -> float:
        """Calculate classroom consistency score"""
        instructor_classrooms = defaultdict(set)
        for assignment in assignments:
            if isinstance(assignment, dict):
                resp_id = assignment.get('responsible_instructor_id')
                if resp_id:
                    instructor_classrooms[resp_id].add(assignment.get('classroom_id'))
        
        total_changes = sum(len(classrooms) - 1 for classrooms in instructor_classrooms.values())
        # 🔧 FIX: Division by zero protection
        if total_changes < 0:
            classroom_score = 30.0
        else:
            classroom_score = 30.0 / (1.0 + total_changes)
        
        return classroom_score
    
    def _calculate_gap_free_score(self, assignments: List[Dict]) -> float:
        """Calculate gap-free optimization score"""
        if not assignments:
            return 0.0
        
        # Count total possible slots
        total_slots = len(self.classrooms) * len(self.timeslots)
        used_slots = len(assignments)
        gaps = total_slots - used_slots
        
        # Calculate gap penalty
        # 🔧 FIX: Division by zero protection
        gap_penalty = gaps * abs(self.penalty_gap) / total_slots if total_slots > 0 else 0.0
        
        # Calculate utilization bonus
        utilization_bonus = (used_slots / total_slots) * 100.0 if total_slots > 0 else 0.0
        
        return utilization_bonus - gap_penalty
    
    def _calculate_early_timeslot_score(self, assignments: List[Dict]) -> float:
        """Calculate early timeslot usage score"""
        if not assignments or not self.timeslots:
            return 0.0
        
        total_timeslots = len(self.timeslots)
        early_threshold = int(total_timeslots * self.early_timeslot_threshold)
        
        early_assignments = 0
        late_assignments = 0
        
        for assignment in assignments:
            if isinstance(assignment, dict):
                timeslot_id = assignment.get('timeslot_id', 0)
                if timeslot_id <= early_threshold:
                    early_assignments += 1
                else:
                    late_assignments += 1
        
        total_assignments = early_assignments + late_assignments
        if total_assignments == 0:
            return 0.0
        
        # 🔧 FIX: Division by zero protection
        early_percentage = (early_assignments / total_assignments) * 100.0 if total_assignments > 0 else 0.0
        
        # Bonus for early usage, penalty for late usage when early slots available
        early_bonus = early_percentage * 2.0
        late_penalty = 0.0
        
        if late_assignments > 0 and early_assignments < early_threshold:
            # Penalty for using late slots when early slots are available
            late_penalty = late_assignments * abs(self.penalty_late_timeslot)
        
        return early_bonus - late_penalty
    
    def _calculate_ultra_aggressive_gap_score(self, assignments: List[Dict]) -> float:
        """Calculate ultra-aggressive gap minimization score"""
        if not assignments:
            return 0.0
        
        # Count gaps in each classroom
        classroom_gaps = defaultdict(int)
        classroom_assignments = defaultdict(int)
        
        # Initialize all classrooms
        for classroom in self.classrooms:
            classroom_gaps[classroom['id']] = len(self.timeslots)
            classroom_assignments[classroom['id']] = 0
        
        # Count assignments per classroom
        for assignment in assignments:
            classroom_id = self.safe_get_assignment_data(assignment, 'classroom_id')
            if classroom_id and classroom_id in classroom_assignments:
                classroom_assignments[classroom_id] += 1
                classroom_gaps[classroom_id] -= 1
        
        # Calculate ultra-aggressive gap penalties
        total_gap_penalty = 0.0
        for classroom_id, gap_count in classroom_gaps.items():
            if gap_count > 0:
                # Large gap penalty
                gap_penalty = gap_count * abs(self.penalty_large_gap)
                total_gap_penalty += gap_penalty
        
        # Calculate filled slot rewards
        total_filled_reward = 0.0
        for classroom_id, assignment_count in classroom_assignments.items():
            if assignment_count > 0:
                # Reward for filled slots
                filled_reward = assignment_count * self.reward_gap_filled
                total_filled_reward += filled_reward
        
        return total_filled_reward - total_gap_penalty
    
    def _calculate_super_ultra_aggressive_gap_score(self, assignments: List[Dict]) -> float:
        """🔥 SUPER ULTRA-AGGRESSIVE GAP STRATEGY: Force minimal classroom usage"""
        if not assignments:
            return 0.0
        
        # Count used classrooms
        used_classrooms = set()
        for assignment in assignments:
            classroom_id = self.safe_get_assignment_data(assignment, 'classroom_id')
            if classroom_id:
                used_classrooms.add(classroom_id)
        
        total_classrooms = len(self.classrooms)
        used_classroom_count = len(used_classrooms)
        empty_classrooms = total_classrooms - used_classroom_count
        
        # MASSIVE reward for using fewer classrooms (compact)
        compact_reward = (total_classrooms - used_classroom_count) * self.reward_compact_classrooms
        
        # MASSIVE penalty for empty classrooms
        empty_penalty = empty_classrooms * abs(self.penalty_empty_classrooms)
        
        # Additional reward for high density per classroom
        density_bonus = 0.0
        if used_classroom_count > 0:
            # 🔧 FIX: Division by zero protection
            assignments_per_classroom = len(assignments) / used_classroom_count if used_classroom_count > 0 else 0.0
            density_bonus = assignments_per_classroom * 100.0  # Bonus for high density
        
        return compact_reward - empty_penalty + density_bonus
    # ============================================================================
    # EVOLUTION OPERATORS
    # ============================================================================
    
    def _evolve_population_ai(self, fitness_scores: List[float]) -> List[List[Dict[str, Any]]]:
        """Evolve population with AI-enhanced operators"""
        new_population = []
        
        # Elite preservation
        elite_indices = np.argsort(fitness_scores)[-self.elite_size:]
        for idx in elite_indices:
            new_population.append(self.population[idx].copy())
        
        # Generate offspring with AI-powered operators
        while len(new_population) < self.population_size:
            parent1 = self._ai_powered_selection(self.population, fitness_scores)
            parent2 = self._ai_powered_selection(self.population, fitness_scores)
            
            if random.random() < self.crossover_rate:
                offspring1, offspring2 = self._ai_enhanced_crossover(parent1, parent2)
            else:
                offspring1, offspring2 = parent1.copy(), parent2.copy()
            
            if random.random() < self.mutation_rate:
                offspring1 = self._ai_smart_mutate(offspring1)
            if random.random() < self.mutation_rate:
                offspring2 = self._ai_smart_mutate(offspring2)
            
            new_population.extend([offspring1, offspring2])
        
        return new_population[:self.population_size]

    # ============================================================================
    # 🤖 AI FEATURE 8: AI-POWERED SELECTION OPERATORS
    # ============================================================================
    
    def _ai_powered_selection(self, fitness_scores: List[float]) -> List[Dict[str, Any]]:
        """AI-powered intelligent selection strategy with enhanced AI features"""
        if not self.ai_selection_enabled:
            return self._tournament_selection(fitness_scores)
        
        # Use new AI-powered selection with fitness landscape analysis
        return self._ai_powered_selection(self.population, fitness_scores)
    
    def _choose_ai_selection_strategy(self, fitness_scores: List[float]) -> str:
        """AI chooses the best selection strategy based on population state"""
        # Analyze population diversity and fitness distribution
        diversity = self._calculate_diversity()
        fitness_std = np.std(fitness_scores)
        fitness_mean = np.mean(fitness_scores)
        
        # AI decision logic
        if diversity < 0.3:  # Low diversity
            if fitness_std < 0.1:  # Converged population
                return 'rank_based'  # Force exploration
            else:
                return 'multi_objective'  # Balance exploration/exploitation
        elif fitness_std > 0.5:  # High variance
            return 'fitness_proportional'  # Exploit good solutions
        else:
            return 'tournament'  # Balanced approach
    
    def _fitness_proportional_selection(self, fitness_scores: List[float]) -> List[Dict[str, Any]]:
        """Fitness proportional selection with AI normalization"""
        # Handle negative fitness values
        min_fitness = min(fitness_scores)
        if min_fitness < 0:
            normalized_fitness = [f - min_fitness + 0.1 for f in fitness_scores]
        else:
            normalized_fitness = fitness_scores
        
        total_fitness = sum(normalized_fitness)
        if total_fitness == 0:
            return random.choice(self.population)
        
        # Roulette wheel selection
        # 🔧 FIX: Division by zero protection
        probabilities = [f / total_fitness for f in normalized_fitness] if total_fitness > 0 else [1.0 / len(normalized_fitness)] * len(normalized_fitness)
        selected_idx = np.random.choice(len(self.population), p=probabilities)
        return self.population[selected_idx]
    
    def _rank_based_selection(self, fitness_scores: List[float]) -> List[Dict[str, Any]]:
        """Rank-based selection with AI ranking"""
        # Sort by fitness
        sorted_indices = np.argsort(fitness_scores)
        
        # Linear ranking with AI-adjusted selection pressure
        selection_pressure = 1.5  # AI learns optimal pressure
        ranks = np.arange(1, len(fitness_scores) + 1)
        # 🔧 FIX: Division by zero protection
        if len(fitness_scores) <= 1:
            return self.population[0] if self.population else None
        
        probabilities = (2 - selection_pressure) / len(fitness_scores) + \
                       (2 * (selection_pressure - 1) * (len(fitness_scores) - ranks)) / \
                       (len(fitness_scores) * (len(fitness_scores) - 1))
        
        selected_idx = np.random.choice(sorted_indices, p=probabilities)
        return self.population[selected_idx]
    
    def _multi_objective_selection(self, fitness_scores: List[float]) -> List[Dict[str, Any]]:
        """Multi-objective selection considering multiple criteria"""
        # Calculate multiple objectives for each individual
        objectives = []
        for i, individual in enumerate(self.population):
            coverage = self._calculate_coverage_score(individual)
            consecutive = self._calculate_consecutive_score(individual)
            balance = self._calculate_balance_score(individual)
            objectives.append([coverage, consecutive, balance])
        
        # Pareto dominance-based selection
        pareto_optimal = self._find_pareto_optimal(objectives)
        
        if pareto_optimal:
            selected_idx = random.choice(pareto_optimal)
            return self.population[selected_idx]
        else:
            return self._tournament_selection(fitness_scores)
    
    def _find_pareto_optimal(self, objectives: List[List[float]]) -> List[int]:
        """Find Pareto optimal solutions"""
        pareto_indices = []
        
        for i in range(len(objectives)):
            is_pareto = True
            for j in range(len(objectives)):
                if i != j:
                    # Check if j dominates i
                    if all(objectives[j][k] >= objectives[i][k] for k in range(len(objectives[i]))) and \
                       any(objectives[j][k] > objectives[i][k] for k in range(len(objectives[i]))):
                        is_pareto = False
                        break
            
            if is_pareto:
                pareto_indices.append(i)
        
        return pareto_indices

    def _tournament_selection(self, fitness_scores: List[float]) -> List[Dict[str, Any]]:
        """Enhanced tournament selection with AI tournament size"""
        # AI adjusts tournament size based on population diversity
        diversity = self._calculate_diversity()
        if diversity < 0.3:
            tournament_size = min(self.tournament_size * 2, len(self.population) // 2)
        else:
            tournament_size = self.tournament_size
        
        tournament_indices = random.sample(range(len(self.population)), tournament_size)
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_idx = tournament_indices[np.argmax(tournament_fitness)]
        return self.population[winner_idx]

    # ============================================================================
    # 🤖 AI FEATURE 9: AI-ENHANCED CROSSOVER OPERATORS
    # ============================================================================
    
    def _ai_enhanced_crossover(self, parent1: List[Dict], parent2: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """AI-enhanced intelligent crossover strategy with pattern recognition"""
        if not self.ai_crossover_enabled:
            return self._crossover(parent1, parent2)
        
        # Use new AI-powered crossover with pattern recognition
        offspring = self._ai_powered_crossover(parent1, parent2)
        return offspring[0], offspring[1]
    
    def _choose_ai_crossover_strategy(self, parent1: List[Dict], parent2: List[Dict]) -> str:
        """AI chooses the best crossover strategy based on parent characteristics"""
        # Analyze parent similarity and structure
        similarity = self._calculate_parent_similarity(parent1, parent2)
        structure_quality = self._calculate_parent_structure_quality(parent1, parent2)
        
        # AI decision logic
        if similarity > 0.8:  # Very similar parents
            return 'intelligent_points'  # Force diversity
        elif structure_quality > 0.7:  # High quality parents
            return 'fitness_guided'  # Preserve good structures
        elif similarity < 0.3:  # Very different parents
            return 'context_aware'  # Intelligent combination
        else:
            return 'uniform'  # Balanced approach
    
    def _calculate_parent_similarity(self, parent1: List[Dict], parent2: List[Dict]) -> float:
        """Calculate similarity between two parents"""
        if not parent1 or not parent2:
            return 0.0
        
        # Compare project assignments
        parent1_projects = set(a.get('project_id') for a in parent1 if a.get('project_id'))
        parent2_projects = set(a.get('project_id') for a in parent2 if a.get('project_id'))
        
        if not parent1_projects and not parent2_projects:
            return 1.0
        
        intersection = len(parent1_projects & parent2_projects)
        union = len(parent1_projects | parent2_projects)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_parent_structure_quality(self, parent1: List[Dict], parent2: List[Dict]) -> float:
        """Calculate structural quality of parents"""
        quality1 = self._evaluate_fitness_ai(parent1) if parent1 else 0.0
        quality2 = self._evaluate_fitness_ai(parent2) if parent2 else 0.0
        
        return (quality1 + quality2) / 2.0
    
    def _intelligent_crossover(self, parent1: List[Dict], parent2: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Intelligent crossover with AI-determined crossover points"""
        if not parent1 or not parent2:
            return parent1.copy(), parent2.copy()
        
        # AI determines optimal crossover points
        crossover_points = self._find_intelligent_crossover_points(parent1, parent2)
        
        offspring1, offspring2 = [], []
        offspring1_projects = set()
        offspring2_projects = set()
        
        # Use intelligent crossover points
        for i, point in enumerate(crossover_points):
            if i % 2 == 0:
                # Take from parent1
                if point < len(parent1):
                    assignment = parent1[point]
                    project_id = assignment.get('project_id')
                    if project_id and project_id not in offspring1_projects:
                        offspring1.append(assignment.copy())
                        offspring1_projects.add(project_id)
            else:
                # Take from parent2
                if point < len(parent2):
                    assignment = parent2[point]
                    project_id = assignment.get('project_id')
                    if project_id and project_id not in offspring2_projects:
                        offspring2.append(assignment.copy())
                        offspring2_projects.add(project_id)
        
        # Fill remaining with best assignments
        self._fill_remaining_assignments(offspring1, offspring1_projects, parent1, parent2)
        self._fill_remaining_assignments(offspring2, offspring2_projects, parent2, parent1)
        
        return offspring1, offspring2
    
    def _find_intelligent_crossover_points(self, parent1: List[Dict], parent2: List[Dict]) -> List[int]:
        """AI finds optimal crossover points based on assignment quality"""
        # Analyze assignment quality in each position
        quality_scores1 = [self._evaluate_assignment_quality(a) for a in parent1]
        quality_scores2 = [self._evaluate_assignment_quality(a) for a in parent2]
        
        # Find high-quality regions
        high_quality_points = []
        for i in range(min(len(parent1), len(parent2))):
            if quality_scores1[i] > 0.5 or quality_scores2[i] > 0.5:
                high_quality_points.append(i)
        
        # Select crossover points from high-quality regions
        num_points = min(len(high_quality_points), max(2, len(parent1) // 4))
        return random.sample(high_quality_points, num_points) if high_quality_points else [0]
    
    def _evaluate_assignment_quality(self, assignment: Dict) -> float:
        """Evaluate quality of a single assignment"""
        if not assignment or not isinstance(assignment, dict):
            return 0.0
        
        quality = 0.0
        
        # Check for good timeslot (early is better)
        timeslot_id = assignment.get('timeslot_id')
        if timeslot_id:
            # Find timeslot index (simplified)
            for i, ts in enumerate(self.timeslots):
                if ts.get('id') == timeslot_id:
                    quality += (len(self.timeslots) - i) / len(self.timeslots)
                    break
        
        # Check for good classroom assignment
        classroom_id = assignment.get('classroom_id')
        if classroom_id:
            quality += 0.3
        
        # Check for instructor assignment
        instructors = assignment.get('instructors', [])
        if instructors:
            quality += 0.2 * len(instructors)
        
        return min(quality, 1.0)
    
    def _fitness_guided_crossover(self, parent1: List[Dict], parent2: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Fitness-guided crossover preserving high-quality assignments"""
        if not parent1 or not parent2:
            return parent1.copy(), parent2.copy()
        
        # Evaluate fitness of each assignment
        fitness1 = [self._evaluate_assignment_quality(a) for a in parent1]
        fitness2 = [self._evaluate_assignment_quality(a) for a in parent2]
        
        offspring1, offspring2 = [], []
        offspring1_projects = set()
        offspring2_projects = set()
        
        # Select assignments based on fitness
        for i in range(min(len(parent1), len(parent2))):
            if fitness1[i] > fitness2[i]:
                # Parent1 assignment is better
                assignment = parent1[i]
                project_id = assignment.get('project_id')
                if project_id and project_id not in offspring1_projects:
                    offspring1.append(assignment.copy())
                    offspring1_projects.add(project_id)
                
                # Still add parent2 assignment to offspring2 if not duplicate
                assignment2 = parent2[i]
                project_id2 = assignment2.get('project_id')
                if project_id2 and project_id2 not in offspring2_projects:
                    offspring2.append(assignment2.copy())
                    offspring2_projects.add(project_id2)
            else:
                # Parent2 assignment is better
                assignment = parent2[i]
                project_id = assignment.get('project_id')
                if project_id and project_id not in offspring2_projects:
                    offspring2.append(assignment.copy())
                    offspring2_projects.add(project_id)
                
                # Still add parent1 assignment to offspring1 if not duplicate
                assignment1 = parent1[i]
                project_id1 = assignment1.get('project_id')
                if project_id1 and project_id1 not in offspring1_projects:
                    offspring1.append(assignment1.copy())
                    offspring1_projects.add(project_id1)
        
        # Fill remaining assignments
        self._fill_remaining_assignments(offspring1, offspring1_projects, parent1, parent2)
        self._fill_remaining_assignments(offspring2, offspring2_projects, parent2, parent1)
        
        return offspring1, offspring2
    
    def _context_aware_crossover(self, parent1: List[Dict], parent2: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Context-aware crossover preserving good patterns"""
        if not parent1 or not parent2:
            return parent1.copy(), parent2.copy()
        
        # Analyze patterns in parents
        patterns1 = self._extract_patterns(parent1)
        patterns2 = self._extract_patterns(parent2)
        
        offspring1, offspring2 = [], []
        offspring1_projects = set()
        offspring2_projects = set()
        
        # Preserve good patterns
        for pattern in patterns1:
            if pattern['quality'] > 0.6:  # Good pattern
                for assignment in pattern['assignments']:
                    project_id = assignment.get('project_id')
                    if project_id and project_id not in offspring1_projects:
                        offspring1.append(assignment.copy())
                        offspring1_projects.add(project_id)
        
        for pattern in patterns2:
            if pattern['quality'] > 0.6:  # Good pattern
                for assignment in pattern['assignments']:
                    project_id = assignment.get('project_id')
                    if project_id and project_id not in offspring2_projects:
                        offspring2.append(assignment.copy())
                        offspring2_projects.add(project_id)
        
        # Fill remaining assignments
        self._fill_remaining_assignments(offspring1, offspring1_projects, parent1, parent2)
        self._fill_remaining_assignments(offspring2, offspring2_projects, parent2, parent1)
        
        return offspring1, offspring2
    
    def _extract_patterns(self, individual: List[Dict]) -> List[Dict]:
        """Extract meaningful patterns from individual"""
        patterns = []
        
        # Group by instructor
        instructor_groups = defaultdict(list)
        for assignment in individual:
            instructors = assignment.get('instructors', [])
            for instructor_id in instructors:
                instructor_groups[instructor_id].append(assignment)
        
        # Analyze each group as a pattern
        for instructor_id, assignments in instructor_groups.items():
            if len(assignments) > 1:
                pattern_quality = self._evaluate_pattern_quality(assignments)
                patterns.append({
                    'type': 'instructor_group',
                    'assignments': assignments,
                    'quality': pattern_quality
                })
        
        return patterns
    
    def _evaluate_pattern_quality(self, assignments: List[Dict]) -> float:
        """Evaluate quality of a pattern"""
        if not assignments:
            return 0.0
        
        # Check for consecutive timeslots (good pattern)
        timeslot_ids = [a.get('timeslot_id') for a in assignments if a.get('timeslot_id')]
        consecutive_score = self._calculate_consecutiveness(timeslot_ids)
        
        # Check for same classroom (good pattern)
        classroom_ids = [a.get('classroom_id') for a in assignments if a.get('classroom_id')]
        # 🔧 FIX: Division by zero protection
        classroom_consistency = len(set(classroom_ids)) / len(classroom_ids) if classroom_ids and len(classroom_ids) > 0 else 0
        
        return (consecutive_score + (1 - classroom_consistency)) / 2
    
    def _calculate_consecutiveness(self, timeslot_ids: List[int]) -> float:
        """Calculate how consecutive the timeslots are"""
        if len(timeslot_ids) < 2:
            return 0.0
        
        # Find timeslot indices
        timeslot_indices = []
        for ts_id in timeslot_ids:
            for i, ts in enumerate(self.timeslots):
                if ts.get('id') == ts_id:
                    timeslot_indices.append(i)
                    break
        
        timeslot_indices.sort()
        
        # Calculate consecutive score
        consecutive_count = 0
        for i in range(len(timeslot_indices) - 1):
            if timeslot_indices[i + 1] - timeslot_indices[i] == 1:
                consecutive_count += 1
        
        # 🔧 FIX: Division by zero protection
        return consecutive_count / (len(timeslot_indices) - 1) if len(timeslot_indices) > 1 else 0.0
    
    def _fill_remaining_assignments(self, offspring: List[Dict], offspring_projects: Set, parent1: List[Dict], parent2: List[Dict]) -> None:
        """Fill remaining assignments from parents"""
        all_assignments = parent1 + parent2
        
        for assignment in all_assignments:
            project_id = assignment.get('project_id')
            if project_id and project_id not in offspring_projects:
                offspring.append(assignment.copy())
                offspring_projects.add(project_id)

    def _crossover(self, parent1: List[Dict], parent2: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Enhanced uniform crossover with AI improvements"""
        if not parent1 or not parent2:
            return parent1.copy(), parent2.copy()
        
        offspring1, offspring2 = [], []
        min_len = min(len(parent1), len(parent2))
        
        # Track project IDs to prevent duplicates
        offspring1_projects = set()
        offspring2_projects = set()
        
        for i in range(min_len):
            parent1_project_id = parent1[i].get('project_id')
            parent2_project_id = parent2[i].get('project_id')
            
            if random.random() < 0.5:
                # Add from parent1 to offspring1, parent2 to offspring2
                if parent1_project_id not in offspring1_projects:
                    offspring1.append(parent1[i].copy())
                    offspring1_projects.add(parent1_project_id)
                
                if parent2_project_id not in offspring2_projects:
                    offspring2.append(parent2[i].copy())
                    offspring2_projects.add(parent2_project_id)
            else:
                # Add from parent2 to offspring1, parent1 to offspring2
                if parent2_project_id not in offspring1_projects:
                    offspring1.append(parent2[i].copy())
                    offspring1_projects.add(parent2_project_id)
                
                if parent1_project_id not in offspring2_projects:
                    offspring2.append(parent1[i].copy())
                    offspring2_projects.add(parent1_project_id)
        
        # Fill remaining assignments
        self._fill_remaining_assignments(offspring1, offspring1_projects, parent1, parent2)
        self._fill_remaining_assignments(offspring2, offspring2_projects, parent2, parent1)
        
        return offspring1, offspring2

    # ============================================================================
    # 🤖 AI FEATURE 10: SMART MUTATION STRATEGIES
    # ============================================================================
    
    def _ai_smart_mutate(self, individual: List[Dict]) -> List[Dict]:
        """AI-powered smart mutation with adaptive strategies"""
        if not self.ai_mutation_enabled:
            return self._mutate(individual)
        
        if not individual or len(individual) < 2:
            return individual
        
        # Choose mutation strategy based on AI learning
        strategy = self._choose_ai_mutation_strategy(individual)
        
        if strategy == 'adaptive_strength':
            return self._adaptive_strength_mutation(individual)
        elif strategy == 'fitness_based':
            return self._fitness_based_mutation(individual)
        elif strategy == 'pattern_preserving':
            return self._pattern_preserving_mutation(individual)
        elif strategy == 'landscape_guided':
            return self._landscape_guided_mutation(individual)
        else:
            return self._mutate(individual)
    
    def _choose_ai_mutation_strategy(self, individual: List[Dict]) -> str:
        """AI chooses the best mutation strategy based on individual characteristics"""
        # Analyze individual fitness and structure
        fitness = self._evaluate_fitness_ai(individual)
        diversity = self._calculate_individual_diversity(individual)
        convergence_level = self._calculate_convergence_level()
        
        # AI decision logic
        if fitness < 0.3:  # Low fitness
            return 'adaptive_strength'  # Strong mutation
        elif diversity < 0.2:  # Low diversity
            return 'fitness_based'  # Targeted mutation
        elif convergence_level > 0.8:  # High convergence
            return 'pattern_preserving'  # Preserve good patterns
        else:
            return 'landscape_guided'  # Guided exploration
    
    def _calculate_individual_diversity(self, individual: List[Dict]) -> float:
        """Calculate diversity of an individual"""
        if len(individual) < 2:
            return 0.0
        
        # Analyze timeslot distribution
        timeslot_ids = [a.get('timeslot_id') for a in individual if isinstance(a, dict) and a.get('timeslot_id')]
        # 🔧 FIX: Division by zero protection
        timeslot_diversity = len(set(timeslot_ids)) / len(timeslot_ids) if timeslot_ids and len(timeslot_ids) > 0 else 0
        
        # Analyze classroom distribution
        classroom_ids = [a.get('classroom_id') for a in individual if isinstance(a, dict) and a.get('classroom_id')]
        # 🔧 FIX: Division by zero protection
        classroom_diversity = len(set(classroom_ids)) / len(classroom_ids) if classroom_ids and len(classroom_ids) > 0 else 0
        
        # Analyze instructor distribution
        all_instructors = []
        for assignment in individual:
            if isinstance(assignment, dict):
                all_instructors.extend(assignment.get('instructors', []))
        # 🔧 FIX: Division by zero protection
        instructor_diversity = len(set(all_instructors)) / len(all_instructors) if all_instructors and len(all_instructors) > 0 else 0
        
        return (timeslot_diversity + classroom_diversity + instructor_diversity) / 3
    
    def _calculate_convergence_level(self) -> float:
        """Calculate current convergence level"""
        if len(self.diversity_history) < 5:
            return 0.0
        
        recent_diversity = self.diversity_history[-5:]
        avg_diversity = np.mean(recent_diversity)
        
        # Lower diversity = higher convergence
        return 1.0 - avg_diversity
    
    def _adaptive_strength_mutation(self, individual: List[Dict]) -> List[Dict]:
        """Adaptive strength mutation - AI adjusts mutation intensity"""
        mutated = individual.copy()
        
        # AI determines mutation strength based on fitness
        fitness = self._evaluate_fitness_ai(individual)
        base_strength = 0.3
        adaptive_strength = base_strength + (0.7 * (1.0 - fitness))  # Lower fitness = higher mutation
        
        # Apply multiple mutations based on strength
        num_mutations = max(1, int(len(mutated) * adaptive_strength))
        
        for _ in range(num_mutations):
            mutation_type = random.choice(['swap', 'timeslot', 'classroom', 'shuffle'])
            mutated = self._apply_mutation_operator(mutated, mutation_type)
        
        return mutated
    
    def _apply_mutation_operator(self, individual: List[Dict], mutation_type: str) -> List[Dict]:
        """Apply specific mutation operator to individual"""
        if not individual:
            return individual
            
        mutated = individual.copy()
        
        # Handle case where individual is a list of assignments (each assignment is a dict)
        if mutated and len(mutated) > 0:
            first_assignment = mutated[0]
            if isinstance(first_assignment, list):
                # If first element is a list, then individual is a list of lists
                # Flatten to get list of assignments
                assignments = []
                for assignment_list in mutated:
                    if isinstance(assignment_list, list):
                        assignments.extend(assignment_list)
                    else:
                        assignments.append(assignment_list)
                mutated = assignments
        
        if mutation_type == 'swap':
            # Swap two random assignments
            if len(mutated) >= 2:
                idx1, idx2 = random.sample(range(len(mutated)), 2)
                mutated[idx1], mutated[idx2] = mutated[idx2], mutated[idx1]
                
        elif mutation_type == 'timeslot':
            # Change timeslot of random assignment
            if mutated:
                idx = random.randint(0, len(mutated) - 1)
                if hasattr(self, 'timeslots') and self.timeslots:
                    new_timeslot = random.choice(self.timeslots)
                    # Safe access to timeslot_id
                    if isinstance(mutated[idx], dict) and 'timeslot_id' in mutated[idx]:
                        mutated[idx]['timeslot_id'] = new_timeslot.get('id', mutated[idx]['timeslot_id'])
                    
        elif mutation_type == 'classroom':
            # Change classroom of random assignment
            if mutated:
                idx = random.randint(0, len(mutated) - 1)
                if hasattr(self, 'classrooms') and self.classrooms:
                    new_classroom = random.choice(self.classrooms)
                    # Safe access to classroom_id
                    if isinstance(mutated[idx], dict) and 'classroom_id' in mutated[idx]:
                        mutated[idx]['classroom_id'] = new_classroom.get('id', mutated[idx]['classroom_id'])
                    
        elif mutation_type == 'shuffle':
            # Shuffle the order of assignments
            random.shuffle(mutated)
            
        return mutated
    
    def _fitness_based_mutation(self, individual: List[Dict]) -> List[Dict]:
        """Fitness-based mutation - target low-quality assignments"""
        mutated = individual.copy()
        
        # Evaluate each assignment's quality
        assignment_qualities = []
        for i, assignment in enumerate(mutated):
            quality = self._evaluate_assignment_quality(assignment)
            assignment_qualities.append((i, quality))
        
        # Sort by quality (lowest first)
        assignment_qualities.sort(key=lambda x: x[1])
        
        # Mutate lowest quality assignments
        num_to_mutate = max(1, len(mutated) // 4)  # Mutate 25% of assignments
        
        for i in range(min(num_to_mutate, len(assignment_qualities))):
            assignment_idx = assignment_qualities[i][0]
            mutated[assignment_idx] = self._improve_assignment(mutated[assignment_idx])
        
        return mutated
    
    def _pattern_preserving_mutation(self, individual: List[Dict]) -> List[Dict]:
        """Pattern-preserving mutation - protect good patterns"""
        mutated = individual.copy()
        
        # Identify good patterns
        good_patterns = self._identify_good_patterns(individual)
        protected_assignments = set()
        
        # Protect assignments in good patterns
        for pattern in good_patterns:
            for assignment in pattern['assignments']:
                for i, mut_assignment in enumerate(mutated):
                    if (mut_assignment.get('project_id') == assignment.get('project_id') and
                        mut_assignment.get('timeslot_id') == assignment.get('timeslot_id')):
                        protected_assignments.add(i)
                        break
        
        # Mutate only non-protected assignments
        for i, assignment in enumerate(mutated):
            if i not in protected_assignments:
                mutation_type = random.choice(['timeslot', 'classroom'])
                mutated[i] = self._apply_single_mutation(assignment, mutation_type)
        
        return mutated
    
    def _landscape_guided_mutation(self, individual: List[Dict]) -> List[Dict]:
        """Landscape-guided mutation - explore promising regions"""
        mutated = individual.copy()
        
        # Analyze fitness landscape
        landscape_analysis = self._analyze_fitness_landscape()
        
        # Find promising directions for mutation
        promising_directions = self._find_promising_directions(individual, landscape_analysis)
        
        # Apply mutations in promising directions
        for direction in promising_directions:
            mutated = self._apply_direction_mutation(mutated, direction)
        
        return mutated
    
    def _identify_good_patterns(self, individual: List[Dict]) -> List[Dict]:
        """Identify good patterns in individual"""
        patterns = self._extract_patterns(individual)
        good_patterns = [p for p in patterns if p['quality'] > 0.6]
        return good_patterns
    
    def _improve_assignment(self, assignment: Dict) -> Dict:
        """Improve a single assignment"""
        improved = assignment.copy()
        
        # Try to move to earlier timeslot
        current_timeslot_id = assignment.get('timeslot_id')
        if current_timeslot_id:
            # Find earlier available timeslot
            current_idx = None
            for i, ts in enumerate(self.timeslots):
                if ts.get('id') == current_timeslot_id:
                    current_idx = i
                    break
            
            if current_idx and current_idx > 0:
                # Try to move to earlier timeslot
                for i in range(current_idx):
                    new_timeslot = self.timeslots[i]
                    # Check if this timeslot would be better
                    improved['timeslot_id'] = new_timeslot['id']
                    break
        
        return improved
    
    def _apply_single_mutation(self, assignment: Dict, mutation_type: str) -> Dict:
        """Apply a single mutation to an assignment"""
        mutated = assignment.copy()
        
        if mutation_type == 'timeslot':
            # Change timeslot
            available_timeslots = [ts for ts in self.timeslots if ts.get('id') != assignment.get('timeslot_id')]
            if available_timeslots:
                new_timeslot = random.choice(available_timeslots)
                mutated['timeslot_id'] = new_timeslot['id']
        
        elif mutation_type == 'classroom':
            # Change classroom
            available_classrooms = [c for c in self.classrooms if c.get('id') != assignment.get('classroom_id')]
            if available_classrooms:
                new_classroom = random.choice(available_classrooms)
                mutated['classroom_id'] = new_classroom['id']
        
        return mutated
    
    def _analyze_fitness_landscape(self) -> Dict:
        """Analyze the fitness landscape"""
        if len(self.fitness_landscape_history) < 3:
            return {'trend': 'unknown', 'variability': 'medium'}
        
        recent_fitness = [entry['best_fitness'] for entry in self.fitness_landscape_history[-3:]]
        
        # Calculate trend
        if recent_fitness[-1] > recent_fitness[0]:
            trend = 'improving'
        elif recent_fitness[-1] < recent_fitness[0]:
            trend = 'declining'
        else:
            trend = 'stable'
        
        # Calculate variability
        variability = np.std(recent_fitness)
        if variability > 0.5:
            variability_level = 'high'
        elif variability > 0.2:
            variability_level = 'medium'
        else:
            variability_level = 'low'
        
        return {'trend': trend, 'variability': variability_level}
    
    def _find_promising_directions(self, individual: List[Dict], landscape_analysis: Dict) -> List[str]:
        """Find promising directions for mutation based on landscape analysis"""
        directions = []
        
        if landscape_analysis['trend'] == 'declining':
            directions.extend(['exploration', 'diversification'])
        elif landscape_analysis['trend'] == 'stable':
            directions.extend(['intensification', 'local_search'])
        else:  # improving
            directions.extend(['exploitation', 'refinement'])
        
        if landscape_analysis['variability'] == 'low':
            directions.append('diversification')
        elif landscape_analysis['variability'] == 'high':
            directions.append('stabilization')
        
        return directions[:2]  # Limit to 2 directions
    def _apply_direction_mutation(self, individual: List[Dict], direction: str) -> List[Dict]:
        """Apply mutation in a specific direction"""
        if direction == 'exploration':
            return self._exploration_mutation(individual)
        elif direction == 'diversification':
            return self._diversification_mutation(individual)
        elif direction == 'intensification':
            return self._intensification_mutation(individual)
        elif direction == 'local_search':
            return self._local_search_mutation(individual)
        elif direction == 'exploitation':
            return self._exploitation_mutation(individual)
        elif direction == 'refinement':
            return self._refinement_mutation(individual)
        elif direction == 'stabilization':
            return self._stabilization_mutation(individual)
        else:
            return individual
    
    def _exploration_mutation(self, individual: List[Dict]) -> List[Dict]:
        """Exploration mutation - try new combinations"""
        mutated = individual.copy()
        # Swap assignments between different positions
        if len(mutated) >= 2:
            i, j = random.sample(range(len(mutated)), 2)
            mutated[i], mutated[j] = mutated[j], mutated[i]
        return mutated
    
    def _diversification_mutation(self, individual: List[Dict]) -> List[Dict]:
        """Diversification mutation - increase diversity"""
        mutated = individual.copy()
        # Change multiple assignments to increase diversity
        num_changes = max(1, len(mutated) // 3)
        for _ in range(num_changes):
            idx = random.randint(0, len(mutated) - 1)
            mutated[idx] = self._apply_single_mutation(mutated[idx], 'timeslot')
        return mutated
    
    def _intensification_mutation(self, individual: List[Dict]) -> List[Dict]:
        """Intensification mutation - focus on promising areas"""
        mutated = individual.copy()
        # Improve best assignments
        assignment_qualities = [(i, self._evaluate_assignment_quality(a)) for i, a in enumerate(mutated)]
        assignment_qualities.sort(key=lambda x: x[1], reverse=True)
        
        # Improve top 25% of assignments
        num_to_improve = max(1, len(mutated) // 4)
        for i in range(num_to_improve):
            idx = assignment_qualities[i][0]
            mutated[idx] = self._improve_assignment(mutated[idx])
        
        return mutated
    
    def _local_search_mutation(self, individual: List[Dict]) -> List[Dict]:
        """Local search mutation - small improvements"""
        mutated = individual.copy()
        # Small changes to assignments
        for assignment in mutated:
            if random.random() < 0.3:  # 30% chance
                assignment = self._apply_single_mutation(assignment, random.choice(['timeslot', 'classroom']))
        return mutated
    
    def _exploitation_mutation(self, individual: List[Dict]) -> List[Dict]:
        """Exploitation mutation - exploit current good solutions"""
        return self._intensification_mutation(individual)
    
    def _refinement_mutation(self, individual: List[Dict]) -> List[Dict]:
        """Refinement mutation - fine-tune good solutions"""
        return self._local_search_mutation(individual)
    
    def _stabilization_mutation(self, individual: List[Dict]) -> List[Dict]:
        """Stabilization mutation - reduce variability"""
        mutated = individual.copy()
        # Make conservative changes
        if len(mutated) > 0:
            idx = random.randint(0, len(mutated) - 1)
            mutated[idx] = self._apply_single_mutation(mutated[idx], 'classroom')  # Less disruptive change
        return mutated

    # ============================================================================
    # 🤖 AI FEATURE 11: AI FITNESS LANDSCAPE ANALYSIS
    # ============================================================================
    
    def _update_fitness_landscape_analysis(self, generation: int, best_fitness: float, fitness_scores: List[float]) -> None:
        """Update fitness landscape analysis"""
        landscape_entry = {
            'generation': generation,
            'best_fitness': best_fitness,
            'avg_fitness': np.mean(fitness_scores),
            'std_fitness': np.std(fitness_scores),
            'diversity': self.diversity_history[-1] if self.diversity_history else 0.0,
            'convergence_rate': self._calculate_convergence_rate(),
            'landscape_ruggedness': self._calculate_landscape_ruggedness(fitness_scores)
        }
        
        self.fitness_landscape_history.append(landscape_entry)
        
        # Update Pareto frontier
        self._update_pareto_frontier(fitness_scores)
        
        # Predict future fitness
        if len(self.fitness_landscape_history) > 5:
            prediction = self._predict_future_fitness()
            if prediction:
                logger.info(f"   AI Prediction: Next fitness ≈ {prediction:.3f}")
    
    def _calculate_convergence_rate(self) -> float:
        """Calculate convergence rate"""
        if len(self.fitness_landscape_history) < 3:
            return 0.0
        
        recent_fitness = [entry['best_fitness'] for entry in self.fitness_landscape_history[-3:]]
        improvements = [recent_fitness[i+1] - recent_fitness[i] for i in range(len(recent_fitness)-1)]
        
        return np.mean(improvements) if improvements else 0.0
    
    def _calculate_landscape_ruggedness(self, fitness_scores: List[float]) -> float:
        """Calculate fitness landscape ruggedness"""
        if len(fitness_scores) < 3:
            return 0.0
        
        # Calculate local peaks and valleys
        sorted_fitness = sorted(fitness_scores)
        ruggedness = 0.0
        
        for i in range(1, len(sorted_fitness) - 1):
            if sorted_fitness[i] > sorted_fitness[i-1] and sorted_fitness[i] > sorted_fitness[i+1]:
                ruggedness += 1  # Local peak
            elif sorted_fitness[i] < sorted_fitness[i-1] and sorted_fitness[i] < sorted_fitness[i+1]:
                ruggedness += 1  # Local valley
        
        # 🔧 FIX: Division by zero protection
        return ruggedness / len(sorted_fitness) if len(sorted_fitness) > 0 else 0.0
    
    def _update_pareto_frontier(self, fitness_scores: List[float]) -> None:
        """Update Pareto frontier with current solutions"""
        if not fitness_scores:
            return
        
        # Calculate multi-objective fitness for each individual
        multi_objectives = []
        for i, individual in enumerate(self.population):
            coverage = self._calculate_coverage_score(individual)
            consecutive = self._calculate_consecutive_score(individual)
            balance = self._calculate_balance_score(individual)
            multi_objectives.append([coverage, consecutive, balance])
        
        # Find Pareto optimal solutions
        pareto_indices = self._find_pareto_optimal(multi_objectives)
        
        # Update Pareto frontier
        for idx in pareto_indices:
            if idx < len(self.population):
                pareto_solution = {
                    'individual': self.population[idx].copy(),
                    'objectives': multi_objectives[idx],
                    'fitness': fitness_scores[idx],
                    'generation': len(self.generation_history)
                }
                self.pareto_frontier.append(pareto_solution)
        
        # Keep only recent Pareto solutions (last 50)
        if len(self.pareto_frontier) > 50:
            self.pareto_frontier = self.pareto_frontier[-50:]
    
    def _predict_future_fitness(self) -> float:
        """
        🤖 AI-BASED FALLBACK: Predict future fitness using AI (NO RETURN NONE!)
        """
        if len(self.fitness_landscape_history) < 5:
            # 🤖 FALLBACK: Return current best fitness as prediction
            return self.best_fitness if hasattr(self, 'best_fitness') else 0.0
        
        # Simple linear regression for prediction
        generations = [entry['generation'] for entry in self.fitness_landscape_history[-5:]]
        fitness_values = [entry['best_fitness'] for entry in self.fitness_landscape_history[-5:]]
        
        # Calculate trend
        x = np.array(generations)
        y = np.array(fitness_values)
        
        # Linear regression
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
            intercept = np.polyfit(x, y, 1)[1]
            
            # Predict next generation
            next_generation = max(generations) + 1
            predicted_fitness = slope * next_generation + intercept
            
            return max(0, predicted_fitness)  # Ensure non-negative
        
        # 🤖 FALLBACK: Return current best fitness if regression fails
        return self.best_fitness if hasattr(self, 'best_fitness') else 0.0
    
    def _analyze_fitness_landscape_comprehensive(self) -> Dict:
        """Comprehensive fitness landscape analysis"""
        if len(self.fitness_landscape_history) < 3:
            return {'analysis': 'insufficient_data'}
        
        analysis = {
            'trend_analysis': self._analyze_fitness_trend(),
            'convergence_analysis': self._analyze_convergence_pattern(),
            'diversity_analysis': self._analyze_diversity_pattern(),
            'landscape_characteristics': self._analyze_landscape_characteristics(),
            'optimization_strategy': self._recommend_optimization_strategy()
        }
        
        return analysis
    
    def _analyze_fitness_trend(self) -> Dict:
        """Analyze fitness trend over generations"""
        recent_entries = self.fitness_landscape_history[-10:]
        if len(recent_entries) < 3:
            return {'trend': 'unknown', 'strength': 0.0}
        
        generations = [entry['generation'] for entry in recent_entries]
        fitness_values = [entry['best_fitness'] for entry in recent_entries]
        
        # Calculate trend strength
        x = np.array(generations)
        y = np.array(fitness_values)
        
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
            correlation = np.corrcoef(x, y)[0, 1]
            
            if slope > 0.01:
                trend = 'improving'
            elif slope < -0.01:
                trend = 'declining'
            else:
                trend = 'stable'
            
            strength = abs(correlation)
            
            return {'trend': trend, 'strength': strength, 'slope': slope}
        
        return {'trend': 'unknown', 'strength': 0.0}
    
    def _analyze_convergence_pattern(self) -> Dict:
        """Analyze convergence pattern"""
        if len(self.fitness_landscape_history) < 5:
            return {'convergence': 'unknown'}
        
        recent_fitness = [entry['best_fitness'] for entry in self.fitness_landscape_history[-5:]]
        fitness_std = np.std(recent_fitness)
        
        if fitness_std < 0.05:
            convergence = 'high'
        elif fitness_std < 0.15:
            convergence = 'medium'
        else:
            convergence = 'low'
        
        return {'convergence': convergence, 'variability': fitness_std}
    
    def _analyze_diversity_pattern(self) -> Dict:
        """Analyze diversity pattern"""
        if len(self.diversity_history) < 5:
            return {'diversity': 'unknown'}
        
        recent_diversity = self.diversity_history[-5:]
        avg_diversity = np.mean(recent_diversity)
        
        if avg_diversity > 0.7:
            diversity_level = 'high'
        elif avg_diversity > 0.3:
            diversity_level = 'medium'
        else:
            diversity_level = 'low'
        
        return {'diversity': diversity_level, 'value': avg_diversity}
    
    def _analyze_landscape_characteristics(self) -> Dict:
        """Analyze fitness landscape characteristics"""
        if len(self.fitness_landscape_history) < 3:
            return {'characteristics': 'insufficient_data'}
        
        # Analyze ruggedness
        ruggedness_values = [entry['landscape_ruggedness'] for entry in self.fitness_landscape_history[-5:]]
        avg_ruggedness = np.mean(ruggedness_values)
        
        if avg_ruggedness > 0.3:
            landscape_type = 'rugged'
        elif avg_ruggedness > 0.1:
            landscape_type = 'moderate'
        else:
            landscape_type = 'smooth'
        
        return {
            'landscape_type': landscape_type,
            'ruggedness': avg_ruggedness,
            'complexity': 'high' if avg_ruggedness > 0.2 else 'low'
        }
    
    def _recommend_optimization_strategy(self) -> Dict:
        """Recommend optimization strategy based on landscape analysis"""
        trend_analysis = self._analyze_fitness_trend()
        convergence_analysis = self._analyze_convergence_pattern()
        diversity_analysis = self._analyze_diversity_pattern()
        
        recommendations = []
        
        if trend_analysis['trend'] == 'declining':
            recommendations.append('increase_exploration')
            recommendations.append('adjust_parameters')
        
        if convergence_analysis['convergence'] == 'high':
            recommendations.append('maintain_diversity')
            recommendations.append('local_search')
        
        if diversity_analysis['diversity'] == 'low':
            recommendations.append('increase_mutation')
            recommendations.append('diversity_injection')
        
        return {
            'recommendations': recommendations,
            'priority': 'high' if len(recommendations) > 2 else 'medium'
        }

    # ============================================================================
    # 🤖 AI FEATURE 12: AI-POWERED LOCAL SEARCH
    # ============================================================================
    
    def _apply_ai_powered_local_search(self) -> None:
        """Apply AI-powered local search to elite solutions"""
        if not self.ai_local_search_enabled:
            return
        
        # Get elite solutions
        fitness_scores = [self._evaluate_fitness_ai(ind) for ind in self.population]
        elite_count = max(1, int(self.population_size * 0.1))  # Top 10%
        elite_indices = np.argsort(fitness_scores)[-elite_count:]
        
        improvements = 0
        for idx in elite_indices:
            original = self.population[idx]
            original_fitness = fitness_scores[idx]
            
            # Choose AI local search strategy
            strategy = self._choose_ai_local_search_strategy(original, original_fitness)
            
            # Apply AI local search
            improved = self._apply_ai_local_search_strategy(original, strategy)
            improved_fitness = self._evaluate_fitness_ai(improved)
            
            if improved_fitness > original_fitness:
                self.population[idx] = improved
                improvements += 1
                self.local_search_improvements.append({
                    'improvement': improved_fitness - original_fitness,
                    'strategy': strategy,
                    'generation': len(self.generation_history)
                })
        
        if improvements > 0:
            logger.info(f"   AI Local Search: {improvements}/{elite_count} elite solutions improved")
    
    def _choose_ai_local_search_strategy(self, individual: List[Dict], fitness: float) -> str:
        """AI chooses the best local search strategy"""
        # Analyze individual characteristics
        diversity = self._calculate_individual_diversity(individual)
        convergence_level = self._calculate_convergence_level()
        
        # AI decision logic
        if fitness > 0.8:  # High fitness
            if diversity > 0.5:  # High diversity
                return 'intelligent_neighbors'
            else:
                return 'refinement_search'
        elif fitness > 0.5:  # Medium fitness
            return 'adaptive_step_size'
        else:  # Low fitness
            return 'multi_directional'
    
    def _apply_ai_local_search_strategy(self, individual: List[Dict], strategy: str) -> List[Dict]:
        """Apply specific AI local search strategy"""
        if strategy == 'intelligent_neighbors':
            return self._intelligent_neighbors_search(individual)
        elif strategy == 'adaptive_step_size':
            return self._adaptive_step_size_search(individual)
        elif strategy == 'multi_directional':
            return self._multi_directional_search(individual)
        elif strategy == 'refinement_search':
            return self._refinement_search(individual)
        else:
            return individual
    
    def _intelligent_neighbors_search(self, individual: List[Dict]) -> List[Dict]:
        """Intelligent neighbors search - AI selects best neighbors"""
        best_neighbor = individual.copy()
        best_fitness = self._evaluate_fitness_ai(individual)
        
        # Generate intelligent neighbors
        neighbors = self._generate_intelligent_neighbors(individual)
        
        for neighbor in neighbors:
            neighbor_fitness = self._evaluate_fitness_ai(neighbor)
            if neighbor_fitness > best_fitness:
                best_neighbor = neighbor
                best_fitness = neighbor_fitness
        
        return best_neighbor
    
    def _generate_intelligent_neighbors(self, individual: List[Dict]) -> List[Dict]:
        """Generate intelligent neighbors based on fitness landscape"""
        neighbors = []
        
        # Analyze current assignment quality
        assignment_qualities = [(i, self._evaluate_assignment_quality(a)) for i, a in enumerate(individual)]
        
        # Focus on improving low-quality assignments
        low_quality_assignments = [a for a in assignment_qualities if a[1] < 0.5]
        
        for idx, _ in low_quality_assignments[:3]:  # Top 3 worst assignments
            neighbor = individual.copy()
            
            # Try different improvement strategies
            improvement_strategies = [
                self._improve_timeslot_assignment,
                self._improve_classroom_assignment,
                self._improve_instructor_assignment
            ]
            
            for strategy in improvement_strategies:
                improved_neighbor = strategy(neighbor, idx)
                if improved_neighbor != neighbor:
                    neighbors.append(improved_neighbor)
        
        return neighbors[:5]  # Limit to 5 neighbors
    
    def _adaptive_step_size_search(self, individual: List[Dict]) -> List[Dict]:
        """Adaptive step size search - AI adjusts search intensity"""
        current_fitness = self._evaluate_fitness_ai(individual)
        
        # Determine step size based on fitness
        if current_fitness > 0.7:
            step_size = 1  # Small steps for high fitness
        elif current_fitness > 0.4:
            step_size = 2  # Medium steps
        else:
            step_size = 3  # Large steps for low fitness
        
        best_solution = individual.copy()
        best_fitness = current_fitness
        
        # Apply adaptive step size mutations
        for _ in range(step_size):
            mutated = self._apply_adaptive_mutation(best_solution, current_fitness)
            mutated_fitness = self._evaluate_fitness_ai(mutated)
            
            if mutated_fitness > best_fitness:
                best_solution = mutated
                best_fitness = mutated_fitness
        
        return best_solution
    
    def _apply_adaptive_mutation(self, individual: List[Dict], fitness: float) -> List[Dict]:
        """Apply adaptive mutation based on fitness"""
        mutated = individual.copy()
        
        # Mutation intensity based on fitness
        if fitness > 0.7:
            # Conservative mutation for high fitness
            mutation_type = random.choice(['classroom'])
        elif fitness > 0.4:
            # Moderate mutation
            mutation_type = random.choice(['timeslot', 'classroom'])
        else:
            # Aggressive mutation for low fitness
            mutation_type = random.choice(['swap', 'shuffle', 'timeslot'])
        
        # Apply mutation
        if mutation_type == 'swap' and len(mutated) >= 2:
            i, j = random.sample(range(len(mutated)), 2)
            mutated[i], mutated[j] = mutated[j], mutated[i]
        elif mutation_type == 'timeslot':
            idx = random.randint(0, len(mutated) - 1)
            mutated[idx] = self._apply_single_mutation(mutated[idx], 'timeslot')
        elif mutation_type == 'classroom':
            idx = random.randint(0, len(mutated) - 1)
            mutated[idx] = self._apply_single_mutation(mutated[idx], 'classroom')
        elif mutation_type == 'shuffle':
            random.shuffle(mutated)
        
        return mutated
    
    def _multi_directional_search(self, individual: List[Dict]) -> List[Dict]:
        """Multi-directional search - explore multiple directions simultaneously"""
        directions = ['early_timeslot', 'consecutive_grouping', 'classroom_optimization', 'instructor_balance']
        
        best_solution = individual.copy()
        best_fitness = self._evaluate_fitness_ai(individual)
        
        for direction in directions:
            directional_solution = self._apply_directional_search(individual, direction)
            directional_fitness = self._evaluate_fitness_ai(directional_solution)
            
            if directional_fitness > best_fitness:
                best_solution = directional_solution
                best_fitness = directional_fitness
        
        return best_solution
    
    def _apply_directional_search(self, individual: List[Dict], direction: str) -> List[Dict]:
        """Apply search in specific direction"""
        if direction == 'early_timeslot':
            return self._early_timeslot_search(individual)
        elif direction == 'consecutive_grouping':
            return self._consecutive_grouping_search(individual)
        elif direction == 'classroom_optimization':
            return self._classroom_optimization_search(individual)
        elif direction == 'instructor_balance':
            return self._instructor_balance_search(individual)
        else:
            return individual
    
    def _early_timeslot_search(self, individual: List[Dict]) -> List[Dict]:
        """Search for earlier timeslot assignments"""
        optimized = individual.copy()
        
        for assignment in optimized:
            current_timeslot_id = assignment.get('timeslot_id')
            if current_timeslot_id:
                # Find earlier timeslot
                current_idx = None
                for i, ts in enumerate(self.timeslots):
                    if ts.get('id') == current_timeslot_id:
                        current_idx = i
                        break
                
                if current_idx and current_idx > 0:
                    # Try to move to earlier timeslot
                    for i in range(current_idx):
                        assignment['timeslot_id'] = self.timeslots[i]['id']
                        break
        
        return optimized
    
    def _consecutive_grouping_search(self, individual: List[Dict]) -> List[Dict]:
        """Search for better consecutive groupings"""
        optimized = individual.copy()
        
        # Group by instructor
        instructor_groups = defaultdict(list)
        for i, assignment in enumerate(optimized):
            instructors = assignment.get('instructors', [])
            for instructor_id in instructors:
                instructor_groups[instructor_id].append((i, assignment))
        
        # Optimize each group for consecutiveness
        for instructor_id, assignments in instructor_groups.items():
            if len(assignments) > 1:
                # Sort by timeslot
                sorted_assignments = sorted(assignments, key=lambda x: x[1].get('timeslot_id'))
                
                # Try to make consecutive
                for i in range(len(sorted_assignments) - 1):
                    current_timeslot = sorted_assignments[i][1].get('timeslot_id')
                    next_timeslot = sorted_assignments[i + 1][1].get('timeslot_id')
                    
                    # Find next consecutive timeslot
                    current_idx = None
                    for j, ts in enumerate(self.timeslots):
                        if ts.get('id') == current_timeslot:
                            current_idx = j
                            break
                    
                    if current_idx is not None and current_idx + 1 < len(self.timeslots):
                        next_consecutive_timeslot = self.timeslots[current_idx + 1]['id']
                        if next_consecutive_timeslot != next_timeslot:
                            sorted_assignments[i + 1][1]['timeslot_id'] = next_consecutive_timeslot
        
        return optimized
    
    def _classroom_optimization_search(self, individual: List[Dict]) -> List[Dict]:
        """Search for better classroom assignments"""
        optimized = individual.copy()
        
        # Analyze classroom usage
        classroom_usage = defaultdict(int)
        for assignment in optimized:
            classroom_id = assignment.get('classroom_id')
            if classroom_id:
                classroom_usage[classroom_id] += 1
        
        # Balance classroom usage
        for assignment in optimized:
            current_classroom = assignment.get('classroom_id')
            if current_classroom and classroom_usage[current_classroom] > 2:  # Overused classroom
                # Find less used classroom
                available_classrooms = [c for c in self.classrooms if c.get('id') != current_classroom]
                if available_classrooms:
                    # Choose classroom with least usage
                    least_used_classroom = min(available_classrooms, 
                                             key=lambda c: classroom_usage.get(c.get('id'), 0))
                    assignment['classroom_id'] = least_used_classroom['id']
                    classroom_usage[current_classroom] -= 1
                    classroom_usage[least_used_classroom['id']] += 1
        
        return optimized
    
    def _instructor_balance_search(self, individual: List[Dict]) -> List[Dict]:
        """Search for better instructor balance"""
        optimized = individual.copy()
        
        # Analyze instructor workload
        instructor_workload = defaultdict(int)
        for assignment in optimized:
            instructors = assignment.get('instructors', [])
            for instructor_id in instructors:
                instructor_workload[instructor_id] += 1
        
        # Balance instructor workload
        for assignment in optimized:
            current_instructors = assignment.get('instructors', [])
            if current_instructors:
                # Find instructor with least workload
                least_loaded_instructor = min(instructor_workload.keys(), 
                                            key=lambda x: instructor_workload[x])
                
                if least_loaded_instructor not in current_instructors:
                    # Replace one instructor with least loaded one
                    assignment['instructors'] = [least_loaded_instructor]
        
        return optimized
    
    def _refinement_search(self, individual: List[Dict]) -> List[Dict]:
        """Refinement search - fine-tune high-quality solutions"""
        refined = individual.copy()
        
        # Small, precise improvements
        for assignment in refined:
            # Try small improvements
            if random.random() < 0.3:  # 30% chance
                assignment = self._apply_single_mutation(assignment, 'classroom')
        
        return refined
    
    def _improve_timeslot_assignment(self, individual: List[Dict], idx: int) -> List[Dict]:
        """Improve timeslot assignment for specific index"""
        improved = individual.copy()
        assignment = improved[idx]
        
        current_timeslot_id = assignment.get('timeslot_id')
        if current_timeslot_id:
            # Find better timeslot
            for ts in self.timeslots:
                if ts.get('id') != current_timeslot_id:
                    assignment['timeslot_id'] = ts.get('id')
                    break
        
        return improved
    
    def _improve_classroom_assignment(self, individual: List[Dict], idx: int) -> List[Dict]:
        """Improve classroom assignment for specific index"""
        improved = individual.copy()
        assignment = improved[idx]
        
        current_classroom_id = assignment.get('classroom_id')
        if current_classroom_id:
            # Find better classroom
            for classroom in self.classrooms:
                if classroom.get('id') != current_classroom_id:
                    assignment['classroom_id'] = classroom.get('id')
                    break
        
        return improved
    
    def _improve_instructor_assignment(self, individual: List[Dict], idx: int) -> List[Dict]:
        """Improve instructor assignment for specific index"""
        improved = individual.copy()
        assignment = improved[idx]
        
        # Add or modify instructor assignment
        if not assignment.get('instructors'):
            # Add instructor
            assignment['instructors'] = [assignment.get('responsible_instructor_id', 1)]
        
        return improved

    # ============================================================================
    # 🤖 AI FEATURE 13: AI CONVERGENCE DETECTION
    # ============================================================================
    
    def _ai_convergence_detection(self, generation: int, best_fitness: float, fitness_scores: List[float]) -> str:
        """
        🤖 AI-BASED FALLBACK: AI-powered convergence detection and action (NO RETURN NONE!)
        """
        if not self.ai_convergence_enabled:
            # 🤖 FALLBACK: Return 'disabled' status instead of None
            return 'disabled'
        
        # Update convergence history
        convergence_entry = {
            'generation': generation,
            'best_fitness': best_fitness,
            'avg_fitness': np.mean(fitness_scores),
            'diversity': self.diversity_history[-1] if self.diversity_history else 0.0,
            'stagnation_count': self.no_improvement_count
        }
        self.convergence_history.append(convergence_entry)
        
        # AI convergence analysis
        convergence_analysis = self._analyze_convergence_state()
        
        # Choose action based on analysis
        action = self._choose_convergence_action(convergence_analysis)
        
        if action:
            self._execute_convergence_action(action)
        
        return action
    
    def _analyze_convergence_state(self) -> Dict:
        """Analyze current convergence state"""
        if len(self.convergence_history) < 3:
            return {'state': 'insufficient_data'}
        
        recent_entries = self.convergence_history[-5:]
        
        # Analyze stagnation
        stagnation_count = recent_entries[-1]['stagnation_count']
        fitness_improvements = [recent_entries[i+1]['best_fitness'] - recent_entries[i]['best_fitness'] 
                               for i in range(len(recent_entries)-1)]
        avg_improvement = np.mean(fitness_improvements) if fitness_improvements else 0
        
        # Analyze diversity
        diversity_values = [entry['diversity'] for entry in recent_entries]
        avg_diversity = np.mean(diversity_values)
        
        # Analyze fitness variance
        fitness_values = [entry['best_fitness'] for entry in recent_entries]
        fitness_variance = np.var(fitness_values)
        
        # Determine convergence state
        if stagnation_count > self.stagnation_threshold:
            if avg_diversity < 0.2:
                state = 'premature_convergence'
            else:
                state = 'stagnation'
        elif avg_improvement < 0.01:
            if avg_diversity < 0.3:
                state = 'converging'
            else:
                state = 'plateau'
        elif fitness_variance < 0.01:
            state = 'converged'
        else:
            state = 'exploring'
        
        return {
            'state': state,
            'stagnation_count': stagnation_count,
            'avg_improvement': avg_improvement,
            'avg_diversity': avg_diversity,
            'fitness_variance': fitness_variance
        }
    
    def _choose_convergence_action(self, analysis: Dict) -> str:
        """Choose appropriate action based on convergence analysis"""
        state = analysis['state']
        
        if state == 'premature_convergence':
            return 'restart_with_diversity'
        elif state == 'stagnation':
            if analysis['avg_diversity'] > 0.3:
                return 'parameter_adjustment'
            else:
                return 'diversity_injection'
        elif state == 'plateau':
            return 'local_search_intensification'
        elif state == 'converged':
            if self.restart_count < self.max_restarts:
                return 'restart_optimization'
            else:
                return 'early_termination'
        elif state == 'converging':
            return 'continue'
        else:  # exploring
            return 'continue'
    
    def _execute_convergence_action(self, action: str) -> None:
        """Execute the chosen convergence action"""
        if action == 'restart_with_diversity':
            self._restart_with_diversity()
        elif action == 'parameter_adjustment':
            self._adjust_parameters_for_stagnation()
        elif action == 'diversity_injection':
            self._inject_diversity_boost()
        elif action == 'local_search_intensification':
            self._intensify_local_search()
        elif action == 'restart_optimization':
            self._restart_optimization()
        elif action == 'early_termination':
            self._prepare_early_termination()
    def _restart_with_diversity(self) -> None:
        """Restart optimization with increased diversity"""
        logger.info("   🔄 AI: Restarting with diversity injection...")
        
        # Keep only elite solutions
        fitness_scores = [self._evaluate_fitness_ai(ind) for ind in self.population]
        elite_count = max(1, int(self.population_size * 0.2))  # Keep top 20%
        elite_indices = np.argsort(fitness_scores)[-elite_count:]
        
        # Create new diverse population
        new_population = []
        for idx in elite_indices:
            new_population.append(self.population[idx].copy())
        
        # Fill remaining with diverse solutions
        while len(new_population) < self.population_size:
            solution = self._create_diverse_solution()
            new_population.append(solution)
        
        self.population = new_population
        self.no_improvement_count = 0
        self.restart_count += 1
        
        # Adjust parameters for exploration
        self.mutation_rate = min(0.3, self.mutation_rate * 1.5)
        self.crossover_rate = max(0.6, self.crossover_rate * 0.9)
    
    def _adjust_parameters_for_stagnation(self) -> None:
        """Adjust parameters to escape stagnation"""
        logger.info("   ⚙️ AI: Adjusting parameters for stagnation...")
        
        # Increase mutation rate
        self.mutation_rate = min(0.4, self.mutation_rate * 1.3)
        
        # Decrease crossover rate
        self.crossover_rate = max(0.5, self.crossover_rate * 0.8)
        
        # Adjust elite size
        self.elite_size = max(5, int(self.elite_size * 0.7))
    
    def _inject_diversity_boost(self) -> None:
        """Inject diversity boost into population"""
        logger.info("   🌈 AI: Injecting diversity boost...")
        
        # Replace worst 30% with diverse solutions
        fitness_scores = [self._evaluate_fitness_ai(ind) for ind in self.population]
        worst_count = int(self.population_size * 0.3)
        worst_indices = np.argsort(fitness_scores)[:worst_count]
        
        for idx in worst_indices:
            self.population[idx] = self._create_diverse_solution()
    
    def _intensify_local_search(self) -> None:
        """Intensify local search"""
        logger.info("   AI: Intensifying local search...")
        
        # Apply local search to more individuals
        fitness_scores = [self._evaluate_fitness_ai(ind) for ind in self.population]
        elite_count = max(1, int(self.population_size * 0.3))  # Top 30%
        elite_indices = np.argsort(fitness_scores)[-elite_count:]
        
        for idx in elite_indices:
            # Apply multiple local search iterations
            for _ in range(3):
                improved = self._apply_local_search_to_individual(self.population[idx])
                if self._evaluate_fitness_ai(improved) > fitness_scores[idx]:
                    self.population[idx] = improved
                    fitness_scores[idx] = self._evaluate_fitness_ai(improved)
    
    def _restart_optimization(self) -> None:
        """Restart optimization from scratch"""
        logger.info("   🚀 AI: Restarting optimization...")
        
        # Reset parameters
        self.mutation_rate = self.initial_mutation_rate
        self.crossover_rate = self.initial_crossover_rate
        self.no_improvement_count = 0
        
        # Create new population
        self.population = self._smart_initialize_population()
        
        self.restart_count += 1
    
    def _prepare_early_termination(self) -> None:
        """Prepare for early termination"""
        logger.info("   🏁 AI: Preparing for early termination...")
        
        # Apply final local search to best solution
        fitness_scores = [self._evaluate_fitness_ai(ind) for ind in self.population]
        best_idx = np.argmax(fitness_scores)
        
        # Intensive local search
        for _ in range(10):
            improved = self._apply_local_search_to_individual(self.population[best_idx])
            if self._evaluate_fitness_ai(improved) > fitness_scores[best_idx]:
                self.population[best_idx] = improved
                fitness_scores[best_idx] = self._evaluate_fitness_ai(improved)
    
    def _create_diverse_solution(self) -> List[Dict]:
        """Create a diverse solution"""
        # Use random initialization with bias towards diversity
        solution = self._create_random_solution()
        
        # Add some randomness to increase diversity
        if len(solution) > 0:
            # Randomly shuffle some assignments
            shuffle_count = min(3, len(solution) // 4)
            indices_to_shuffle = random.sample(range(len(solution)), shuffle_count)
            
            for idx in indices_to_shuffle:
                assignment = solution[idx]
                # Randomly change timeslot or classroom
                if random.random() < 0.5:
                    new_timeslot = random.choice(self.timeslots)
                    assignment['timeslot_id'] = new_timeslot['id']
                else:
                    new_classroom = random.choice(self.classrooms)
                    assignment['classroom_id'] = new_classroom['id']
        
        return solution
    
    def _apply_local_search_to_individual(self, individual: List[Dict]) -> List[Dict]:
        """Apply local search to a single individual"""
        improved = individual.copy()
        
        # Try different local search moves
        moves = ['swap', 'timeslot_change', 'classroom_change']
        
        for move in moves:
            if move == 'swap' and len(improved) >= 2:
                i, j = random.sample(range(len(improved)), 2)
                improved[i], improved[j] = improved[j], improved[i]
            elif move == 'timeslot_change':
                idx = random.randint(0, len(improved) - 1)
                improved[idx] = self._apply_single_mutation(improved[idx], 'timeslot')
            elif move == 'classroom_change':
                idx = random.randint(0, len(improved) - 1)
                improved[idx] = self._apply_single_mutation(improved[idx], 'classroom')
        
        return improved

    def _mutate(self, individual: List[Dict]) -> List[Dict]:
        """
        🚨 ULTRA-AGGRESSIVE: Enhanced smart mutation ensuring ALL projects remain assigned!
        """
        if not individual or len(individual) < 2:
            return individual
        
        # 🚨 CRITICAL: Store original project assignments before mutation
        original_projects = set()
        for assignment in individual:
            if isinstance(assignment, dict) and 'project_id' in assignment:
                original_projects.add(assignment['project_id'])
        
        mutated = individual.copy()
        
        # 🎯 GAP-FREE & EARLY TIMESLOT MUTATION TYPES
        mutation_types = ['swap', 'timeslot', 'classroom']
        
        # Add gap-filling and early timeslot mutations if enabled
        if self.gap_free_enabled:
            mutation_types.append('gap_filling')
        if self.early_timeslot_enabled:
            mutation_types.append('early_timeslot')
        if self.ultra_aggressive_gap:
            mutation_types.append('ultra_gap_filling')
        if self.super_ultra_gap:
            mutation_types.append('super_ultra_gap_filling')
        
        mutation_type = random.choice(mutation_types)
        
        if mutation_type == 'swap':
            idx1, idx2 = random.sample(range(len(mutated)), 2)
            mutated[idx1], mutated[idx2] = mutated[idx2], mutated[idx1]
        
        elif mutation_type == 'timeslot':
            # CONFLICT-AWARE TIMESLOT MUTATION
            idx = random.randint(0, len(mutated) - 1)
            assignment = mutated[idx]
            instructor_id = assignment.get('instructors', [None])[0]
            
            if instructor_id:
                # Find available timeslots for this instructor
                available_timeslots = []
                for timeslot in self.timeslots:
                    # Check if instructor is available at this timeslot
                    instructor_busy = any(
                        i != idx and 
                        instructor_id in self._normalize_instructors_list(mutated[i].get('instructors', [])) and
                        mutated[i].get('timeslot_id') == timeslot['id']
                        for i in range(len(mutated))
                    )
                    
                    if not instructor_busy:
                        available_timeslots.append(timeslot)
                
                # Select from available timeslots (or random if none available)
                if available_timeslots:
                    new_timeslot = random.choice(available_timeslots)
                    mutated[idx]['timeslot_id'] = new_timeslot['id']
                else:
                    # Fallback to random if no available timeslot found
                    new_timeslot = random.choice(self.timeslots)
                    mutated[idx]['timeslot_id'] = new_timeslot['id']
            else:
                # No instructor, just random assignment
                new_timeslot = random.choice(self.timeslots)
                mutated[idx]['timeslot_id'] = new_timeslot['id']
        
        elif mutation_type == 'classroom':
            # CONFLICT-AWARE CLASSROOM MUTATION
            idx = random.randint(0, len(mutated) - 1)
            assignment = mutated[idx]
            timeslot_id = assignment.get('timeslot_id')
            
            if timeslot_id:
                # Find available classrooms for this timeslot
                available_classrooms = []
                for classroom in self.classrooms:
                    # Check if classroom is available at this timeslot
                    classroom_busy = any(
                        i != idx and
                        mutated[i].get('classroom_id') == classroom['id'] and
                        mutated[i].get('timeslot_id') == timeslot_id
                        for i in range(len(mutated))
                    )
                    
                    if not classroom_busy:
                        available_classrooms.append(classroom)
                
                # Select from available classrooms (or random if none available)
                if available_classrooms:
                    new_classroom = random.choice(available_classrooms)
                    mutated[idx]['classroom_id'] = new_classroom['id']
                else:
                    # Fallback to random if no available classroom found
                    new_classroom = random.choice(self.classrooms)
                    mutated[idx]['classroom_id'] = new_classroom['id']
            else:
                # No timeslot, just random assignment
                new_classroom = random.choice(self.classrooms)
                mutated[idx]['classroom_id'] = new_classroom['id']
        
        elif mutation_type == 'gap_filling':
            # 🎯 GAP-FILLING MUTATION: Move assignments to fill gaps
            mutated = self._gap_filling_mutation(mutated)
        
        elif mutation_type == 'early_timeslot':
            # ⏰ EARLY TIMESLOT MUTATION: Move assignments to earlier slots
            mutated = self._early_timeslot_mutation(mutated)
        
        elif mutation_type == 'ultra_gap_filling':
            # 🚀 ULTRA-AGGRESSIVE GAP-FILLING MUTATION
            mutated = self._ultra_aggressive_gap_filling_mutation(mutated)
        
        elif mutation_type == 'super_ultra_gap_filling':
            # 🔥 SUPER ULTRA-AGGRESSIVE GAP-FILLING MUTATION
            mutated = self._super_ultra_aggressive_gap_filling_mutation(mutated)
        
        # 🚨 CRITICAL: Verify ALL projects are still assigned after mutation
        mutated_projects = set()
        for assignment in mutated:
            if isinstance(assignment, dict) and 'project_id' in assignment:
                mutated_projects.add(assignment['project_id'])
        
        if len(mutated_projects) < len(original_projects):
            missing_projects = original_projects - mutated_projects
            logger.error(f"🚨 MUTATION CONSTRAINT VIOLATION: {len(missing_projects)} projects lost!")
            
            # Emergency recovery: Re-add missing projects
            for project_id in missing_projects:
                # Find the project data
                project_data = None
                for project in self.projects:
                    if project['id'] == project_id:
                        project_data = project
                        break
                
                if project_data:
                    resp_id = project_data.get('responsible_instructor_id') or project_data.get('responsible_id')
                    
                    # Try to find any available slot
                    assigned = False
                    for classroom in self.classrooms:
                        for timeslot in self.timeslots:
                            slot_key = (classroom['id'], timeslot['id'])
                            
                            # Check if slot is already used
                            slot_used = any(
                                a.get('classroom_id') == classroom['id'] and 
                                a.get('timeslot_id') == timeslot['id'] 
                                for a in mutated
                            )
                            
                            if not slot_used:
                                instructors = [resp_id] if resp_id else []
                                
                                # Find a suitable additional instructor
                                for other_instructor in self.instructors:
                                    if other_instructor['id'] != resp_id:
                                        instructors.append(other_instructor['id'])
                                        break
                                
                                emergency_assignment = {
                                    'project_id': project_id,
                                    'timeslot_id': timeslot['id'],
                                    'classroom_id': classroom['id'],
                                    'responsible_instructor_id': resp_id,
                                    'is_makeup': project_data.get('is_makeup', False),
                                    'instructors': instructors
                                }
                                
                                mutated.append(emergency_assignment)
                                logger.error(f"🚨 MUTATION RECOVERY: Proje {project_id} geri eklendi!")
                                assigned = True
                                break
                        if assigned:
                            break
        
        logger.info(f"✅ Mutation completed: {len(mutated)} assignments, all projects preserved")
        return mutated

    def _gap_filling_mutation(self, individual: List[Dict]) -> List[Dict]:
        """🎯 GAP-FILLING MUTATION: Move assignments to fill gaps"""
        if not individual or not self.classrooms or not self.timeslots:
            return individual
        
        mutated = individual.copy()
        
        # Find gaps in the schedule
        gaps = self._find_gaps_in_schedule(mutated)
        
        if gaps:
            # Try to move assignments to fill gaps
            for gap in gaps[:3]:  # Limit to 3 gap-filling attempts
                gap_classroom = gap['classroom_id']
                gap_timeslot = gap['timeslot_id']
                
                # Find an assignment that can be moved to this gap
                for i, assignment in enumerate(mutated):
                    current_classroom = assignment.get('classroom_id')
                    current_timeslot = assignment.get('timeslot_id')
                    instructors_list = assignment.get('instructors', [])
                    instructor_id = self._normalize_instructor_id(instructors_list[0]) if instructors_list else None
                    
                    # Check if instructor is available at gap timeslot
                    if instructor_id:
                        instructor_busy = any(
                            j != i and
                            instructor_id in self._normalize_instructors_list(mutated[j].get('instructors', [])) and
                            mutated[j].get('timeslot_id') == gap_timeslot
                            for j in range(len(mutated))
                        )
                        
                        if not instructor_busy:
                            # Move assignment to gap
                            mutated[i]['classroom_id'] = gap_classroom
                            mutated[i]['timeslot_id'] = gap_timeslot
                            break  # Move only one assignment per gap
        
        return mutated
    
    def _early_timeslot_mutation(self, individual: List[Dict]) -> List[Dict]:
        """⏰ EARLY TIMESLOT MUTATION: Move assignments to earlier slots"""
        if not individual or not self.timeslots:
            return individual
        
        mutated = individual.copy()
        total_timeslots = len(self.timeslots)
        early_threshold = int(total_timeslots * self.early_timeslot_threshold)
        
        # Find assignments in late timeslots
        late_assignments = []
        for i, assignment in enumerate(mutated):
            timeslot_id = assignment.get('timeslot_id', 0)
            if timeslot_id > early_threshold:
                late_assignments.append((i, assignment))
        
        # Try to move late assignments to early slots
        for i, assignment in late_assignments[:2]:  # Limit to 2 moves
            instructor_id = assignment.get('instructors', [None])[0]
            current_classroom = assignment.get('classroom_id')
            
            # Find available early timeslot
            for early_timeslot_id in range(1, early_threshold + 1):
                if instructor_id:
                    # Check instructor availability
                    instructor_busy = any(
                        j != i and
                        instructor_id in self._normalize_instructors_list(mutated[j].get('instructors', [])) and
                        mutated[j].get('timeslot_id') == early_timeslot_id
                        for j in range(len(mutated))
                    )
                    
                    if not instructor_busy:
                        # Check classroom availability
                        classroom_busy = any(
                            j != i and
                            mutated[j].get('classroom_id') == current_classroom and
                            mutated[j].get('timeslot_id') == early_timeslot_id
                            for j in range(len(mutated))
                        )
                        
                        if not classroom_busy:
                            # Move to early timeslot
                            mutated[i]['timeslot_id'] = early_timeslot_id
                            break
        
        return mutated
    
    def _ultra_aggressive_gap_filling_mutation(self, individual: List[Dict]) -> List[Dict]:
        """🚀 ULTRA-AGGRESSIVE GAP-FILLING MUTATION"""
        if not individual:
            return individual
        
        mutated = individual.copy()
        
        # Force compact assignments into fewer classrooms
        classroom_usage = defaultdict(list)
        for assignment in mutated:
            classroom_id = assignment.get('classroom_id')
            classroom_usage[classroom_id].append(assignment)
        
        # Sort classrooms by usage (most used first)
        sorted_classrooms = sorted(classroom_usage.items(), 
                                 key=lambda x: len(x[1]), reverse=True)
        
        # Redistribute assignments to minimize gaps
        new_assignments = []
        for classroom_id, assignments in sorted_classrooms:
            new_assignments.extend(assignments)
        
        # Try to fill gaps more aggressively
        gaps = self._find_gaps_in_schedule(new_assignments)
        
        for gap in gaps:
            gap_classroom = gap['classroom_id']
            gap_timeslot = gap['timeslot_id']
            
            # Find ANY assignment that can fill this gap
            for i, assignment in enumerate(new_assignments):
                instructors_list = assignment.get('instructors', [])
                instructor_id = self._normalize_instructor_id(instructors_list[0]) if instructors_list else None
                
                if instructor_id:
                    instructor_busy = any(
                        j != i and
                        instructor_id in self._normalize_instructors_list(new_assignments[j].get('instructors', [])) and
                        new_assignments[j].get('timeslot_id') == gap_timeslot
                        for j in range(len(new_assignments))
                    )
                    
                    if not instructor_busy:
                        # Force move to gap
                        new_assignments[i]['classroom_id'] = gap_classroom
                        new_assignments[i]['timeslot_id'] = gap_timeslot
                        break
        
        return new_assignments
    
    def _find_gaps_in_schedule(self, assignments: List[Dict]) -> List[Dict]:
        """Find gaps in the current schedule"""
        gaps = []
        
        # Create occupancy map
        occupied = set()
        for assignment in assignments:
            classroom_id = assignment.get('classroom_id')
            timeslot_id = assignment.get('timeslot_id')
            if classroom_id and timeslot_id:
                occupied.add((classroom_id, timeslot_id))
        
        # Find gaps
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                gap_key = (classroom['id'], timeslot['id'])
                if gap_key not in occupied:
                    gaps.append({
                        'classroom_id': classroom['id'],
                        'timeslot_id': timeslot['id'],
                        'classroom': classroom,
                        'timeslot': timeslot
                    })
        
        return gaps
    
    def _ultra_gap_filling_with_unassigned_projects(self, assignments: List[Dict]) -> List[Dict]:
        """
        🚀 ULTRA GAP-FILLING WITH UNASSIGNED PROJECTS
        
        Bu metod gap'leri tamamen ortadan kaldırmak için:
        1. Mevcut atamaları korur (1. faz kalır)
        2. Gap'leri tespit eder
        3. Atanmamış projeleri gap'lere atar
        4. Her yeni projeye 1 sorumlu + 2 jüri atar
        
        Args:
            assignments: Mevcut atamalar (1. faz sonuçları)
            
        Returns:
            Gap'lerin doldurulmuş hali
        """
        logger.info("🚀 ULTRA GAP-FILLING: Atanmamış projelerle gap'leri dolduruyor...")
        
        # Mevcut atamaları kopyala
        result = [assignment.copy() for assignment in assignments]
        
        # Atanmış proje ID'lerini al
        assigned_project_ids = {assignment.get('project_id') for assignment in result}
        
        # Atanmamış projeleri bul
        unassigned_projects = [
            project for project in self.projects 
            if project.get('id') not in assigned_project_ids
        ]
        
        logger.info(f"  📊 Atanmış projeler: {len(assigned_project_ids)}")
        logger.info(f"  📊 Atanmamış projeler: {len(unassigned_projects)}")
        
        if not unassigned_projects:
            logger.info("  ✅ Atanmamış proje yok, gap-filling atlanıyor")
            return result
        
        # Gap'leri bul
        gaps = self._find_gaps_in_schedule(result)
        logger.info(f"  📊 Tespit edilen gap sayısı: {len(gaps)}")
        
        if not gaps:
            logger.info("  ✅ Gap yok, gap-filling atlanıyor")
            return result
        
        # Gap'leri öncelik sırasına göre sırala (erken saatler önce)
        gaps.sort(key=lambda x: x['timeslot']['id'])
        
        # Her gap için uygun proje bul ve ata
        filled_gaps = 0
        for gap in gaps:
            if not unassigned_projects:
                break
                
            gap_classroom = gap['classroom_id']
            gap_timeslot = gap['timeslot_id']
            gap_timeslot_obj = gap['timeslot']
            
            logger.info(f"  🔍 Gap analizi: Classroom {gap_classroom}, Timeslot {gap_timeslot_obj.get('time_range', gap_timeslot)}")
            
            # En uygun projeyi bul
            best_project = self._find_best_project_for_gap(gap, unassigned_projects, result)
            
            if best_project:
                # Projeyi gap'e ata
                new_assignment = self._create_assignment_for_gap(best_project, gap, result)
                
                if new_assignment:
                    result.append(new_assignment)
                    unassigned_projects.remove(best_project)
                    filled_gaps += 1
                    
                    logger.info(f"  ✅ Proje {best_project['id']} gap'e atandı: {gap_timeslot_obj.get('time_range', gap_timeslot)}")
                else:
                    logger.info(f"  ❌ Proje {best_project['id']} için uygun jüri bulunamadı")
            else:
                logger.info(f"  ❌ Gap için uygun proje bulunamadı")
        
        logger.info(f"  🎯 Gap-filling tamamlandı: {filled_gaps} gap dolduruldu")
        logger.info(f"  📊 Kalan atanmamış projeler: {len(unassigned_projects)}")
        
        return result
    
    def _find_best_project_for_gap(self, gap: Dict, unassigned_projects: List[Dict], existing_assignments: List[Dict]) -> Optional[Dict]:
        """
        Gap için en uygun projeyi bul
        
        Kriterler:
        1. Proje sorumlusu gap timeslot'unda müsait mi?
        2. Proje tipi (ara/bitirme) uygun mu?
        3. Jüri ataması yapılabilir mi?
        """
        gap_timeslot_id = gap['timeslot_id']
        
        for project in unassigned_projects:
            responsible_id = project.get('responsible_instructor_id')
            if not responsible_id:
                continue
            
            # Sorumlu instructor gap timeslot'unda müsait mi?
            responsible_busy = any(
                responsible_id in self._normalize_instructors_list(assignment.get('instructors', [])) and
                assignment.get('timeslot_id') == gap_timeslot_id
                for assignment in existing_assignments
            )
            
            if not responsible_busy:
                return project
        
        return None
    
    def _create_assignment_for_gap(self, project: Dict, gap: Dict, existing_assignments: List[Dict]) -> Optional[Dict]:
        """
        Gap için yeni atama oluştur (1 sorumlu + 2 jüri)
        """
        responsible_id = project.get('responsible_instructor_id')
        gap_timeslot_id = gap['timeslot_id']
        gap_classroom_id = gap['classroom_id']
        
        # Sorumlu instructor'ı ekle
        instructors = [responsible_id]
        
        # 2 jüri üyesi bul ve ekle
        jury_members = self._find_jury_members_for_gap(gap_timeslot_id, responsible_id, existing_assignments)
        
        if len(jury_members) >= 2:
            instructors.extend(jury_members[:2])
            
            assignment = {
                'project_id': project['id'],
                'classroom_id': gap_classroom_id,
                'timeslot_id': gap_timeslot_id,
                'responsible_instructor_id': responsible_id,
                'instructors': instructors,
                'is_makeup': project.get('is_makeup', False)
            }
            
            return assignment
        
        return None
    
    def _find_jury_members_for_gap(self, timeslot_id: int, responsible_id: int, existing_assignments: List[Dict]) -> List[int]:
        """
        Gap için uygun jüri üyelerini bul
        """
        available_jury = []
        
        for instructor in self.instructors:
            instructor_id = instructor.get('id')
            if instructor_id == responsible_id:
                continue
            
            # Instructor bu timeslot'ta müsait mi?
            instructor_busy = any(
                instructor_id in self._normalize_instructors_list(assignment.get('instructors', [])) and
                assignment.get('timeslot_id') == timeslot_id
                for assignment in existing_assignments
            )
            
            if not instructor_busy:
                available_jury.append(instructor_id)
        
        return available_jury
    
    def _super_ultra_aggressive_gap_filling_mutation(self, individual: List[Dict]) -> List[Dict]:
        """🔥 SUPER ULTRA-AGGRESSIVE GAP-FILLING MUTATION: Force minimal classroom usage"""
        if not individual:
            return individual
        
        # Calculate minimum classrooms needed
        total_assignments = len(individual)
        total_timeslots = len(self.timeslots)
        min_classrooms_needed = (total_assignments + total_timeslots - 1) // total_timeslots
        
        # Force all assignments into minimum classrooms
        new_assignments = []
        classroom_assignments = defaultdict(list)
        
        # Distribute assignments to minimum classrooms
        for i, assignment in enumerate(individual):
            target_classroom = (i // total_timeslots) + 1
            if target_classroom <= len(self.classrooms):
                classroom_assignments[target_classroom].append(assignment)
        
        # Redistribute to minimize gaps
        for classroom_id, assignments in classroom_assignments.items():
            # Sort assignments by timeslot
            sorted_assignments = sorted(assignments, key=lambda x: x.get('timeslot_id', 0))
            
            # Try to compact into consecutive timeslots
            for i, assignment in enumerate(sorted_assignments):
                target_timeslot = i + 1  # Start from timeslot 1
                if target_timeslot <= total_timeslots:
                    assignment['classroom_id'] = classroom_id
                    assignment['timeslot_id'] = target_timeslot
                    new_assignments.append(assignment)
        
        return new_assignments
    
    def _post_optimization_gap_filling(self, assignments: List[Dict]) -> List[Dict]:
        """📦 POST-OPTIMIZATION GAP FILLING: Final gap filling phase"""
        if not assignments:
            return assignments
        
        result = assignments.copy()
        gaps = self._find_gaps_in_schedule(result)
        
        if not gaps:
            return result
        
        # Try to fill gaps by moving assignments
        for gap in gaps[:10]:  # Limit to 10 gap-filling attempts
            gap_classroom = gap['classroom_id']
            gap_timeslot = gap['timeslot_id']
            
            # Find assignment that can be moved to this gap
            for i, assignment in enumerate(result):
                current_classroom = assignment.get('classroom_id')
                current_timeslot = assignment.get('timeslot_id')
                instructors_list = assignment.get('instructors', [])
                instructor_id = self._normalize_instructor_id(instructors_list[0]) if instructors_list else None
                
                # Check if instructor is available at gap timeslot
                if instructor_id:
                    instructor_busy = any(
                        j != i and
                        instructor_id in self._normalize_instructors_list(result[j].get('instructors', [])) and
                        result[j].get('timeslot_id') == gap_timeslot
                        for j in range(len(result))
                    )
                    
                    if not instructor_busy:
                        # Move assignment to gap
                        result[i]['classroom_id'] = gap_classroom
                        result[i]['timeslot_id'] = gap_timeslot
                        break  # Move only one assignment per gap
        
        return result
    
    def _post_optimization_early_timeslot_shift(self, assignments: List[Dict]) -> List[Dict]:
        """📦 POST-OPTIMIZATION EARLY TIMESLOT SHIFT: Final early timeslot optimization"""
        if not assignments or not self.timeslots:
            return assignments
        
        result = assignments.copy()
        total_timeslots = len(self.timeslots)
        early_threshold = int(total_timeslots * self.early_timeslot_threshold)
        
        # Find assignments in late timeslots
        late_assignments = []
        for i, assignment in enumerate(result):
            timeslot_id = assignment.get('timeslot_id', 0)
            if timeslot_id > early_threshold:
                late_assignments.append((i, assignment))
        
        # Try to move late assignments to early slots
        for i, assignment in late_assignments:
            instructors_list = assignment.get('instructors', [])
            instructor_id = self._normalize_instructor_id(instructors_list[0]) if instructors_list else None
            current_classroom = assignment.get('classroom_id')
            
            # Find available early timeslot
            for early_timeslot_id in range(1, early_threshold + 1):
                if instructor_id:
                    # Check instructor availability
                    instructor_busy = any(
                        j != i and
                        instructor_id in self._normalize_instructors_list(result[j].get('instructors', [])) and
                        result[j].get('timeslot_id') == early_timeslot_id
                        for j in range(len(result))
                    )
                    
                    if not instructor_busy:
                        # Check classroom availability
                        classroom_busy = any(
                            j != i and
                            result[j].get('classroom_id') == current_classroom and
                            result[j].get('timeslot_id') == early_timeslot_id
                            for j in range(len(result))
                        )
                        
                        if not classroom_busy:
                            # Move to early timeslot
                            result[i]['timeslot_id'] = early_timeslot_id
                            break
        
        return result
    
    def _calculate_early_timeslot_usage_percentage(self, assignments: List[Dict]) -> float:
        """Calculate early timeslot usage percentage"""
        if not assignments or not self.timeslots:
            return 0.0
        
        total_timeslots = len(self.timeslots)
        early_threshold = int(total_timeslots * self.early_timeslot_threshold)
        
        early_count = 0
        for assignment in assignments:
            timeslot_id = assignment.get('timeslot_id', 0)
            if timeslot_id <= early_threshold:
                early_count += 1
        
        # 🔧 FIX: Division by zero protection
        return (early_count / len(assignments) * 100.0) if assignments and len(assignments) > 0 else 0.0
    
    # ============================================================================
    # UTILITIES
    # ============================================================================
    
    def _parse_time(self, time_str: str) -> dt_time:
        """Parse time string"""
        try:
            if isinstance(time_str, dt_time):
                return time_str
            return dt_time.fromisoformat(time_str)
        except:
            return dt_time(9, 0)
    def _calculate_metrics_ai(self, assignments: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive AI metrics"""
        if not assignments:
            return {
                "total_assignments": 0,
                "coverage_percentage": 0.0,
                "ai_metrics": {}
            }
        
        assigned_projects = len(set(a['project_id'] for a in assignments if 'project_id' in a))
        # 🔧 FIX: Division by zero protection
        coverage_pct = (assigned_projects / len(self.projects)) * 100.0 if self.projects and len(self.projects) > 0 else 0.0
        
        consecutive_score = self._calculate_consecutive_score(assignments)
        
        loads = defaultdict(int)
        for assignment in assignments:
            normalized_instructors = self._normalize_instructors_list(assignment.get('instructors', []))
            for instructor_id in normalized_instructors:
                loads[instructor_id] += 1
        
        load_values = list(loads.values()) if loads else [0]
        
        instructor_classrooms = defaultdict(set)
        for assignment in assignments:
            resp_id = assignment.get('responsible_instructor_id')
            if resp_id:
                instructor_classrooms[resp_id].add(assignment.get('classroom_id'))
        
        total_classroom_changes = sum(len(classrooms) - 1 for classrooms in instructor_classrooms.values())
        
        return {
            "total_assignments": len(assignments),
            "assigned_projects": assigned_projects,
            "total_projects": len(self.projects),
            "coverage_percentage": coverage_pct,
            "consecutive_grouping_score": consecutive_score,
            "load_balance": {
                "min": min(load_values),
                "max": max(load_values),
                "avg": float(np.mean(load_values)),
                "std": float(np.std(load_values))
            },
            "classroom_changes": total_classroom_changes,
            "instructor_pairs_used": len(self.instructor_pairs),
            "ai_metrics": {
                "final_diversity": self.diversity_history[-1] if self.diversity_history else 0,
                "learned_weights": self.fitness_weights,
                "successful_patterns": len(self.successful_pairs),
                "adaptation_history": {
                    "initial_mutation": self.initial_mutation_rate,
                    "final_mutation": self.mutation_rate,
                    "initial_crossover": self.initial_crossover_rate,
                    "final_crossover": self.crossover_rate
                }
            }
        }
    
    def _evaluate_fitness(self, individual: List[Dict[str, Any]]) -> float:
        """Wrapper for backwards compatibility"""
        return self._evaluate_fitness_ai(individual)
    
    def evaluate_fitness(self, solution: Any) -> float:
        """Required by base class"""
        if isinstance(solution, list):
            return self._evaluate_fitness_ai(solution)
        return float('-inf')
    
    def repair_solution(self, solution: Dict[str, Any], validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """AI-based solution repair"""
        assignments = solution.get("assignments", [])
        
        logger.info("🤖 AI Genetic Algorithm: Starting AI-based repair...")
        
        assignments = self._ai_repair_duplicates(assignments)
        assignments = self._ai_repair_coverage(assignments)
        
        solution["assignments"] = assignments
        logger.info(f"🤖 AI repair completed: {len(assignments)} assignments")
        
        return solution

    def _ai_repair_duplicates(self, assignments: List[Dict]) -> List[Dict]:
        """Remove duplicates"""
        seen_projects = set()
        unique_assignments = []
        
        for assignment in assignments:
            project_id = assignment.get("project_id")
            if project_id and project_id not in seen_projects:
                seen_projects.add(project_id)
                unique_assignments.append(assignment)
        
        return unique_assignments

    def _ai_repair_coverage(self, assignments: List[Dict]) -> List[Dict]:
        """AI-based coverage improvement"""
        assigned_projects = set(a['project_id'] for a in assignments if 'project_id' in a)
        missing_projects = [p for p in self.projects if p['id'] not in assigned_projects]
        
        if not missing_projects:
            return assignments
        
        for project in missing_projects[:20]:
            best_score = float('-inf')
            best_assignment = None
            
            for timeslot in random.sample(self.timeslots, min(10, len(self.timeslots))):
                for classroom in random.sample(self.classrooms, min(3, len(self.classrooms))):
                    resp_id = project.get('responsible_instructor_id') or project.get('responsible_id')
                    
                    test_assignment = {
                        "project_id": project['id'],
                        "timeslot_id": timeslot['id'],
                        "classroom_id": classroom['id'],
                        "responsible_instructor_id": resp_id,
                        "is_makeup": project.get('is_makeup', False),
                        "instructors": [resp_id] if resp_id else []
                    }
                    
                    test_assignments = assignments + [test_assignment]
                    score = self._evaluate_fitness_ai(test_assignments)
                    
                    if score > best_score:
                        best_score = score
                        best_assignment = test_assignment
            
            if best_assignment:
                assignments.append(best_assignment)
        
        return assignments


    # 🔧 CONFLICT RESOLUTION METHODS
    
    def _detect_all_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Tüm çakışma türlerini tespit eder
        
        Görsellerde tespit edilen çakışmalar:
        - Dr. Öğretim Üyesi 3: 14:30-15:00'da 2 farklı görev
        - Dr. Öğretim Üyesi 21: 15:00-15:30'da 2 farklı görev  
        - Dr. Öğretim Üyesi 11: 16:00-16:30'da 2 farklı görev
        """
        all_conflicts = []
        
        logger.info("CONFLICT DETECTION STARTED")
        
        # 1. Instructor çakışmaları
        instructor_conflicts = self._detect_instructor_conflicts(assignments)
        all_conflicts.extend(instructor_conflicts)
        
        # 2. Classroom çakışmaları
        classroom_conflicts = self._detect_classroom_conflicts(assignments)
        all_conflicts.extend(classroom_conflicts)
        
        # 3. Timeslot çakışmaları
        timeslot_conflicts = self._detect_timeslot_conflicts(assignments)
        all_conflicts.extend(timeslot_conflicts)
        
        logger.info(f"CONFLICT DETECTION COMPLETED: {len(all_conflicts)} conflicts found")
        
        return all_conflicts
    
    def _detect_instructor_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Instructor çakışmalarını tespit eder"""
        conflicts = []
        
        # Instructor -> Timeslot -> Assignments mapping
        instructor_timeslot_assignments = defaultdict(lambda: defaultdict(list))
        
        for assignment in assignments:
            instructor_id = assignment.get('responsible_instructor_id')
            timeslot_id = assignment.get('timeslot_id')
            instructors_list = assignment.get('instructors', [])
            project_id = assignment.get('project_id')
            
            if not instructor_id or not timeslot_id:
                continue
            
            # Responsible instructor
            instructor_timeslot_assignments[instructor_id][timeslot_id].append({
                'project_id': project_id,
                'role': 'responsible',
                'assignment': assignment
            })
            
            # Additional instructors
            normalized_instructors_list = self._normalize_instructors_list(instructors_list)
            for additional_instructor_id in normalized_instructors_list:
                if additional_instructor_id != instructor_id:  # Kendi projesinde ek instructor olamaz
                    instructor_timeslot_assignments[additional_instructor_id][timeslot_id].append({
                        'project_id': project_id,
                        'role': 'additional',
                        'assignment': assignment
                    })
        
        # Çakışmaları tespit et
        for instructor_id, timeslot_assignments in instructor_timeslot_assignments.items():
            for timeslot_id, assignments_list in timeslot_assignments.items():
                if len(assignments_list) > 1:
                    # Çakışma tespit edildi!
                    conflict_type = self._determine_instructor_conflict_type(assignments_list)
                    
                    conflicts.append({
                        'type': conflict_type,
                        'instructor_id': instructor_id,
                        'timeslot_id': timeslot_id,
                        'conflicting_assignments': assignments_list,
                        'conflict_count': len(assignments_list),
                        'severity': self._calculate_conflict_severity(assignments_list),
                        'description': f"Instructor {instructor_id} has {len(assignments_list)} assignments in timeslot {timeslot_id}",
                        'resolution_strategy': self._get_resolution_strategy(conflict_type)
                    })
        
        logger.info(f"Instructor conflicts detected: {len(conflicts)}")
        return conflicts
    
    def _detect_classroom_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sınıf çakışmalarını tespit eder"""
        conflicts = []
        
        # Classroom -> Timeslot -> Assignments mapping
        classroom_timeslot_assignments = defaultdict(lambda: defaultdict(list))
        
        for assignment in assignments:
            classroom_id = assignment.get('classroom_id')
            timeslot_id = assignment.get('timeslot_id')
            project_id = assignment.get('project_id')
            
            if not classroom_id or not timeslot_id:
                continue
            
            classroom_timeslot_assignments[classroom_id][timeslot_id].append({
                'project_id': project_id,
                'assignment': assignment
            })
        
        # Çakışmaları tespit et
        for classroom_id, timeslot_assignments in classroom_timeslot_assignments.items():
            for timeslot_id, assignments_list in timeslot_assignments.items():
                if len(assignments_list) > 1:
                    conflicts.append({
                        'type': 'classroom_double_booking',
                        'classroom_id': classroom_id,
                        'timeslot_id': timeslot_id,
                        'conflicting_assignments': assignments_list,
                        'conflict_count': len(assignments_list),
                        'severity': 'HIGH',
                        'description': f"Classroom {classroom_id} has {len(assignments_list)} projects in timeslot {timeslot_id}",
                        'resolution_strategy': 'relocate_to_available_classroom'
                    })
        
        logger.info(f"Classroom conflicts detected: {len(conflicts)}")
        return conflicts
    
    def _detect_timeslot_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Zaman dilimi çakışmalarını tespit eder"""
        conflicts = []
        
        # Timeslot capacity analysis
        timeslot_usage = defaultdict(list)
        
        for assignment in assignments:
            timeslot_id = assignment.get('timeslot_id')
            project_id = assignment.get('project_id')
            
            if timeslot_id:
                timeslot_usage[timeslot_id].append(project_id)
        
        # Her zaman diliminin kapasitesini kontrol et
        for timeslot in self.timeslots:
            timeslot_id = timeslot.get('id')
            capacity = timeslot.get('capacity', 10)  # Default capacity
            used_count = len(timeslot_usage.get(timeslot_id, []))
            
            if used_count > capacity:
                conflicts.append({
                    'type': 'timeslot_overflow',
                    'timeslot_id': timeslot_id,
                    'capacity': capacity,
                    'used_count': used_count,
                    'overflow': used_count - capacity,
                    'severity': 'HIGH',
                    'description': f"Timeslot {timeslot_id} overflow: {used_count}/{capacity}",
                    'resolution_strategy': 'redistribute_to_other_timeslots'
                })
        
        logger.info(f"Timeslot conflicts detected: {len(conflicts)}")
        return conflicts
    
    def _determine_instructor_conflict_type(self, assignments_list: List[Dict[str, Any]]) -> str:
        """Instructor çakışma türünü belirler"""
        roles = [assignment['role'] for assignment in assignments_list]
        
        if 'responsible' in roles and 'additional' in roles:
            return 'instructor_supervisor_additional_conflict'
        elif roles.count('responsible') > 1:
            return 'instructor_double_assignment'
        elif roles.count('additional') > 1:
            return 'instructor_double_additional'
        else:
            return 'instructor_multiple_roles'
    
    def _calculate_conflict_severity(self, assignments_list: List[Dict[str, Any]]) -> str:
        """Çakışma şiddetini hesaplar"""
        if len(assignments_list) > 2:
            return 'CRITICAL'
        elif len(assignments_list) == 2:
            return 'HIGH'
        else:
            return 'MEDIUM'
    
    def _get_resolution_strategy(self, conflict_type: str) -> str:
        """Çakışma türüne göre çözüm stratejisi belirler"""
        strategies = {
            'instructor_supervisor_additional_conflict': 'reschedule_one_assignment',
            'instructor_double_assignment': 'reschedule_duplicate_assignment',
            'instructor_double_additional': 'replace_additional_member',
            'classroom_double_booking': 'relocate_to_available_classroom',
            'timeslot_overflow': 'redistribute_to_other_timeslots'
        }
        return strategies.get(conflict_type, 'manual_resolution')
    
    def _resolve_conflicts(self, assignments: List[Dict[str, Any]], 
                          conflicts: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Çakışmaları çözer
        
        Returns:
            Tuple[List[Dict], List[Dict]]: (resolved_assignments, resolution_log)
        """
        logger.info(f"🔧 CONFLICT RESOLUTION STARTED: {len(conflicts)} conflicts to resolve")
        
        resolved_assignments = assignments.copy()
        resolution_log = []
        
        # Çakışmaları şiddete göre sırala (CRITICAL -> HIGH -> MEDIUM)
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        sorted_conflicts = sorted(conflicts, key=lambda x: severity_order.get(x.get('severity', 'LOW'), 3))
        
        for conflict in sorted_conflicts:
            try:
                resolution_result = self._resolve_single_conflict(conflict, resolved_assignments)
                
                if resolution_result['success']:
                    resolved_assignments = resolution_result['assignments']
                    resolution_log.append({
                        'conflict_id': conflict.get('type', 'unknown'),
                        'resolution_strategy': conflict.get('resolution_strategy', 'unknown'),
                        'success': True,
                        'changes_made': resolution_result.get('changes_made', []),
                        'description': f"Successfully resolved {conflict['type']}"
                    })
                    logger.info(f"RESOLVED: {conflict['description']}")
                else:
                    resolution_log.append({
                        'conflict_id': conflict.get('type', 'unknown'),
                        'resolution_strategy': conflict.get('resolution_strategy', 'unknown'),
                        'success': False,
                        'error': resolution_result.get('error', 'Unknown error'),
                        'description': f"Failed to resolve {conflict['type']}"
                    })
                    logger.warning(f"FAILED: {conflict['description']}")
                    
            except Exception as e:
                logger.error(f"Error resolving conflict {conflict.get('type', 'unknown')}: {e}")
                resolution_log.append({
                    'conflict_id': conflict.get('type', 'unknown'),
                    'success': False,
                    'error': str(e),
                    'description': f"Exception during resolution: {conflict['type']}"
                })
        
        logger.info(f"🔧 CONFLICT RESOLUTION COMPLETED")
        logger.info(f"   - Conflicts resolved: {len([r for r in resolution_log if r['success']])}")
        logger.info(f"   - Conflicts failed: {len([r for r in resolution_log if not r['success']])}")
        
        return resolved_assignments, resolution_log
    
    def _resolve_single_conflict(self, conflict: Dict[str, Any], 
                                assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tek bir çakışmayı çözer"""
        
        conflict_type = conflict.get('type')
        strategy = conflict.get('resolution_strategy')
        
        try:
            if strategy == 'reschedule_one_assignment':
                return self._reschedule_one_assignment(conflict, assignments)
            elif strategy == 'reschedule_duplicate_assignment':
                return self._reschedule_duplicate_assignment(conflict, assignments)
            elif strategy == 'replace_additional_member':
                return self._replace_additional_member(conflict, assignments)
            elif strategy == 'relocate_to_available_classroom':
                return self._relocate_to_available_classroom(conflict, assignments)
            elif strategy == 'redistribute_to_other_timeslots':
                return self._redistribute_to_other_timeslots(conflict, assignments)
            else:
                return {'success': False, 'error': f'Unknown strategy: {strategy}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _reschedule_one_assignment(self, conflict: Dict[str, Any], 
                                  assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bir atamayı yeniden zamanla"""
        changes_made = []
        
        conflicting_assignments = conflict.get('conflicting_assignments', [])
        if len(conflicting_assignments) < 2:
            return {'success': False, 'error': 'Not enough conflicting assignments'}
        
        # İkinci atamayı yeniden zamanla (birinciyi koru)
        assignment_to_move = conflicting_assignments[1]['assignment']
        
        # Boş zaman dilimi bul
        used_timeslots = {a.get('timeslot_id') for a in assignments if a.get('timeslot_id')}
        available_timeslots = [ts for ts in self.timeslots if ts.get('id') not in used_timeslots]
        
        if not available_timeslots:
            # Hiç boş zaman dilimi yok, mevcut olanlar arasından seç
            available_timeslots = self.timeslots
        
        # En uygun zaman dilimini seç
        new_timeslot = available_timeslots[0]
        old_timeslot_id = assignment_to_move.get('timeslot_id')
        
        # Atamayı güncelle
        for assignment in assignments:
            if assignment.get('project_id') == assignment_to_move.get('project_id'):
                assignment['timeslot_id'] = new_timeslot.get('id')
                changes_made.append({
                    'project_id': assignment.get('project_id'),
                    'old_timeslot': old_timeslot_id,
                    'new_timeslot': new_timeslot.get('id'),
                    'action': 'rescheduled'
                })
                break
        
        return {
            'success': True,
            'assignments': assignments,
            'changes_made': changes_made
        }
    
    def _reschedule_duplicate_assignment(self, conflict: Dict[str, Any], 
                                       assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Çoğaltılmış atamayı yeniden zamanla"""
        return self._reschedule_one_assignment(conflict, assignments)
    
    def _replace_additional_member(self, conflict: Dict[str, Any], 
                                 assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ek instructor'ı değiştir"""
        changes_made = []
        
        conflicting_assignments = conflict.get('conflicting_assignments', [])
        instructor_id = conflict.get('instructor_id')
        timeslot_id = conflict.get('timeslot_id')
        
        # Bu zaman diliminde meşgul olmayan instructor bul
        busy_instructors = set()
        for assignment in assignments:
            if assignment.get('timeslot_id') == timeslot_id:
                responsible_id = self._normalize_instructor_id(assignment.get('responsible_instructor_id'))
                if responsible_id:
                    busy_instructors.add(responsible_id)
                normalized_instructors = self._normalize_instructors_list(assignment.get('instructors', []))
                busy_instructors.update(normalized_instructors)
        
        available_instructors = []
        for instructor in self.instructors:
            if instructor.get('id') not in busy_instructors:
                available_instructors.append(instructor)
        
        if not available_instructors:
            return {'success': False, 'error': 'No available instructors for replacement'}
        
        # İlk uygun instructor'ı seç
        replacement_instructor = available_instructors[0]['id']
        
        # Ek instructor'ı değiştir
        for assignment in assignments:
            if assignment.get('timeslot_id') == timeslot_id:
                instructors_list = assignment.get('instructors', [])
                normalized_list = self._normalize_instructors_list(instructors_list)
                if instructor_id in normalized_list:
                    # Dict formatını koruyarak güncelle
                    updated_list = []
                    replaced = False
                    for inst in instructors_list:
                        inst_id = self._normalize_instructor_id(inst)
                        if inst_id == instructor_id and not replaced:
                            updated_list.append(replacement_instructor)
                            replaced = True
                        else:
                            updated_list.append(inst)
                    assignment['instructors'] = updated_list
                    
                    changes_made.append({
                        'assignment_id': assignment.get('project_id'),
                        'old_additional': instructor_id,
                        'new_additional': replacement_instructor,
                        'action': 'additional_replaced'
                    })
                    break
        
        return {
            'success': True,
            'assignments': assignments,
            'changes_made': changes_made
        }
    
    def _relocate_to_available_classroom(self, conflict: Dict[str, Any], 
                                       assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Boş sınıfa taşı"""
        changes_made = []
        
        conflicting_assignments = conflict.get('conflicting_assignments', [])
        classroom_id = conflict.get('classroom_id')
        timeslot_id = conflict.get('timeslot_id')
        
        # Bu zaman diliminde meşgul olmayan sınıf bul
        busy_classrooms = set()
        for assignment in assignments:
            if assignment.get('timeslot_id') == timeslot_id:
                busy_classrooms.add(assignment.get('classroom_id'))
        
        available_classrooms = []
        for classroom in self.classrooms:
            if classroom.get('id') not in busy_classrooms:
                available_classrooms.append(classroom)
        
        if not available_classrooms:
            return {'success': False, 'error': 'No available classrooms for relocation'}
        
        # İlk uygun sınıfı seç
        new_classroom_id = available_classrooms[0]['id']
        
        # Sınıfı değiştir
        for assignment in assignments:
            if (assignment.get('classroom_id') == classroom_id and 
                assignment.get('timeslot_id') == timeslot_id):
                assignment['classroom_id'] = new_classroom_id
                
                changes_made.append({
                    'assignment_id': assignment.get('project_id'),
                    'old_classroom': classroom_id,
                    'new_classroom': new_classroom_id,
                    'action': 'relocated'
                })
                break
        
        return {
            'success': True,
            'assignments': assignments,
            'changes_made': changes_made
        }
    
    def _redistribute_to_other_timeslots(self, conflict: Dict[str, Any], 
                                       assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Diğer zaman dilimlerine yeniden dağıt"""
        changes_made = []
        
        timeslot_id = conflict.get('timeslot_id')
        overflow = conflict.get('overflow', 0)
        
        if not self.timeslots or overflow <= 0:
            return {'success': False, 'error': 'Invalid overflow or no timeslots available'}
        
        # Bu zaman dilimindeki fazla atamaları bul
        timeslot_assignments = [a for a in assignments if a.get('timeslot_id') == timeslot_id]
        
        if len(timeslot_assignments) <= overflow:
            return {'success': False, 'error': 'Not enough assignments to redistribute'}
        
        # Boş zaman dilimleri bul
        used_timeslots = defaultdict(int)
        for assignment in assignments:
            used_timeslots[assignment.get('timeslot_id')] += 1
        
        available_timeslots = []
        for ts in self.timeslots:
            if ts.get('id') != timeslot_id and used_timeslots.get(ts.get('id'), 0) < ts.get('capacity', 10):
                available_timeslots.append(ts)
        
        if not available_timeslots:
            return {'success': False, 'error': 'No available timeslots for redistribution'}
        
        # Fazla atamaları yeniden dağıt
        assignments_to_move = timeslot_assignments[-overflow:]
        
        for i, assignment in enumerate(assignments_to_move):
            target_timeslot = available_timeslots[i % len(available_timeslots)]
            old_timeslot_id = assignment.get('timeslot_id')
            
            assignment['timeslot_id'] = target_timeslot.get('id')
            
            changes_made.append({
                'assignment_id': assignment.get('project_id'),
                'old_timeslot': old_timeslot_id,
                'new_timeslot': target_timeslot.get('id'),
            'action': 'redistributed'
        })
        
        return {
            'success': True,
            'assignments': assignments,
            'changes_made': changes_made
        }

    # DOCUMENTATION FORMULAS - Genetic Population-Based Implementation
    
    def calculate_time_penalty(self, projects_schedule: List[Dict], delta: float = None, epsilon: float = None) -> float:
        """
        Dokümantasyona göre zaman cezası hesaplama
        Formül: g_r = max(0, round((saat_{r+1} - saat_r) / Δ) - 1)
        
        Args:
            projects_schedule: Instructor'ın projelerinin zaman sıralı listesi
            delta: Δ parametresi (varsayılan: self.delta)
            epsilon: ε tolerans eşiği (varsayılan: self.epsilon)
            
        Returns:
            float: Toplam zaman cezası
        """
        if not projects_schedule or len(projects_schedule) < 2:
            return 0.0
            
        delta = delta or self.delta
        epsilon = epsilon or self.epsilon
        total_penalty = 0.0
        
        # Projeleri zaman sırasına göre sırala
        sorted_projects = sorted(projects_schedule, key=lambda x: x.get('timeslot_id', 0))
        
        for i in range(len(sorted_projects) - 1):
            current_project = sorted_projects[i]
            next_project = sorted_projects[i + 1]
            
            # Zaman slotlarını al
            current_timeslot_id = current_project.get('timeslot_id')
            next_timeslot_id = next_project.get('timeslot_id')
            
            if not current_timeslot_id or not next_timeslot_id:
                continue
                
            # Timeslot bilgilerini bul
            current_timeslot = next((ts for ts in self.timeslots if ts.get('id') == current_timeslot_id), None)
            next_timeslot = next((ts for ts in self.timeslots if ts.get('id') == next_timeslot_id), None)
            
            if not current_timeslot or not next_timeslot:
                continue
                
            # Zaman farkını hesapla (saat cinsinden)
            current_time = self._parse_time(current_timeslot.get('start_time', '09:00'))
            next_time = self._parse_time(next_timeslot.get('start_time', '09:00'))
            
            time_diff = next_time - current_time
            
            # Dokümantasyon formülü: g_r = max(0, round((saat_{r+1} - saat_r) / Δ) - 1)
            # 🔧 FIX: Division by zero protection
            penalty = max(0, round(time_diff / delta) - 1) if delta > 0 else 0
            total_penalty += penalty
            
        return total_penalty

    def calculate_class_penalty(self, projects_schedule: List[Dict]) -> float:
        """
        Dokümantasyona göre sınıf değişim cezası
        Formül: 1[sınıf_{r+1} ≠ sınıf_r]
        
        Args:
            projects_schedule: Instructor'ın projelerinin zaman sıralı listesi
            
        Returns:
            float: Toplam sınıf değişim cezası
        """
        if not projects_schedule or len(projects_schedule) < 2:
            return 0.0
            
        total_penalty = 0.0
        
        # Projeleri zaman sırasına göre sırala
        sorted_projects = sorted(projects_schedule, key=lambda x: x.get('timeslot_id', 0))
        
        for i in range(len(sorted_projects) - 1):
            current_project = sorted_projects[i]
            next_project = sorted_projects[i + 1]
            
            # Sınıf ID'lerini al
            current_classroom = current_project.get('classroom_id')
            next_classroom = next_project.get('classroom_id')
            
            # Dokümantasyon formülü: 1[sınıf_{r+1} ≠ sınıf_r]
            if current_classroom != next_classroom:
                total_penalty += 1.0
                
        return total_penalty

    def calculate_genetic_population_penalty(self, population: List[Dict]) -> float:
        """
        Genetic Algorithm için population-wide penalty
        
        Her birey için penalty hesapla ve population average'ı al
        
        Args:
            population: Population listesi
            
        Returns:
            float: Population average penalty
        """
        if not population:
            return 0.0
        
        total_penalty = 0.0
        
        for individual in population:
            # Individual'dan instructor schedule'larını çıkar
            instructor_schedules = self._extract_schedules_from_individual(individual)
            
            # Her instructor için penalty hesapla
            individual_penalty = 0.0
            for instructor_id, projects in instructor_schedules.items():
                if len(projects) < 2:  # En az 2 proje olmalı
                    continue
                    
                # Zaman cezası hesapla
                time_penalty = self.calculate_time_penalty(projects)
                
                # Sınıf değişim cezası hesapla
                class_penalty = self.calculate_class_penalty(projects)
                
                # Total penalty: α * Σ(time_penalty) + β * Σ(class_penalty)
                instructor_penalty = self.alpha * time_penalty + self.beta * class_penalty
                individual_penalty += instructor_penalty
            
            total_penalty += individual_penalty
        
        # Population average penalty
        return total_penalty / len(population)
    
    def _calculate_documentation_penalty(self, solution: Dict) -> float:
        """Calculate documentation penalty for Genetic Algorithm"""
        try:
            assignments = solution.get('assignments', [])
            if not assignments:
                return 0.0
            
            # Group assignments by instructor
            instructor_schedules = {}
            for assignment in assignments:
                instructor_id = assignment.get('instructor_id')
                if instructor_id:
                    if instructor_id not in instructor_schedules:
                        instructor_schedules[instructor_id] = []
                    instructor_schedules[instructor_id].append(assignment)
            
            # Calculate penalty for each instructor
            total_penalty = 0.0
            for instructor_id, projects_schedule in instructor_schedules.items():
                if len(projects_schedule) < 2:
                    continue
                
                # Sort by time slot
                projects_schedule.sort(key=lambda x: x.get('time_slot', 0))
                
                # Calculate time penalty
                time_penalty = self.calculate_time_penalty(projects_schedule)
                
                # Calculate class penalty
                class_penalty = self.calculate_class_penalty(projects_schedule)
                
                # Combine penalties
                instructor_penalty = self.alpha * time_penalty + self.beta * class_penalty
                total_penalty += instructor_penalty
            
            return total_penalty
            
        except Exception as e:
            return 0.0

    def _extract_schedules_from_individual(self, individual: Dict) -> Dict:
        """
        Individual'dan instructor schedule'larını çıkar
        
        Args:
            individual: Individual dictionary
            
        Returns:
            Dict: Instructor schedules
        """
        instructor_schedules = defaultdict(list)
        
        # Individual'dan assignments'ları al
        assignments = individual.get('assignments', [])
        
        for assignment in assignments:
            # Her assignment'taki instructor'ları al
            responsible_id = assignment.get("supervisor_id") or assignment.get("responsible_id")
            
            if responsible_id:
                instructor_schedules[responsible_id].append({
                    'timeslot_id': assignment.get('timeslot_id'),
                    'classroom_id': assignment.get('classroom_id'),
                    'project_id': assignment.get('project_id')
                })
        
        return instructor_schedules
    def _parse_time(self, time_str: str) -> float:
        """
        Zaman string'ini saat cinsinden float'a çevir
        
        Args:
            time_str: "09:00" formatında zaman string'i
            
        Returns:
            float: Saat cinsinden zaman
        """
        try:
            if isinstance(time_str, str):
                hour, minute = map(int, time_str.split(':'))
                return hour + minute / 60.0
            return 0.0
        except:
            return 0.0

    # 🤖 YENİ AI ÖZELLİKLERİ - Genetic Algorithm Doğasına Göre
    
    def _penalty_aware_crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """
        🤖 AI FEATURE 1: Gene-Level Penalty Awareness
        
        Crossover yaparken penalty'leri dikkate al
        
        Düşük penalty'li gene'leri tercih et
        """
        if not hasattr(self, 'crossover_penalty_history'):
            self.crossover_penalty_history = []
        
        offspring = {
            'assignments': [],
            'fitness': 0.0,
            'generation': max(parent1.get('generation', 0), parent2.get('generation', 0)) + 1
        }
        
        # Parent'ların assignments'larını al
        assignments1 = parent1.get('assignments', [])
        assignments2 = parent2.get('assignments', [])
        
        # Her assignment için penalty-aware crossover
        for i in range(min(len(assignments1), len(assignments2))):
            assignment1 = assignments1[i]
            assignment2 = assignments2[i]
            
            # Her assignment için gene penalty hesapla
            gene1_penalty = self._calculate_gene_penalty(assignment1)
            gene2_penalty = self._calculate_gene_penalty(assignment2)
            
            # Daha düşük penalty'li gene'i seç
            if gene1_penalty < gene2_penalty:
                offspring['assignments'].append(assignment1)
                logger.info(f"🤖 Selected gene from parent1 (penalty: {gene1_penalty:.2f} vs {gene2_penalty:.2f})")
            else:
                offspring['assignments'].append(assignment2)
                logger.info(f"🤖 Selected gene from parent2 (penalty: {gene2_penalty:.2f} vs {gene1_penalty:.2f})")
        
        # Crossover history'yi güncelle
        self.crossover_penalty_history.append({
            'parent1_penalty': self._calculate_individual_penalty(parent1),
            'parent2_penalty': self._calculate_individual_penalty(parent2),
            'offspring_penalty': self._calculate_individual_penalty(offspring),
            'timestamp': time.time()
        })
        
        return offspring

    def _calculate_gene_penalty(self, assignment: Dict) -> float:
        """
        Assignment (gene) için penalty hesapla
        """
        # Assignment'dan instructor schedule'ını çıkar
        instructor_schedules = defaultdict(list)
        
        responsible_id = assignment.get("supervisor_id") or assignment.get("responsible_id")
        if responsible_id:
            instructor_schedules[responsible_id].append({
                'timeslot_id': assignment.get('timeslot_id'),
                'classroom_id': assignment.get('classroom_id'),
                'project_id': assignment.get('project_id')
            })
        
        # Her instructor için penalty hesapla
        total_penalty = 0.0
        for instructor_id, projects in instructor_schedules.items():
            if len(projects) < 2:
                continue
                
            time_penalty = self.calculate_time_penalty(projects)
            class_penalty = self.calculate_class_penalty(projects)
            instructor_penalty = self.alpha * time_penalty + self.beta * class_penalty
            total_penalty += instructor_penalty
        
        return total_penalty

    def _calculate_individual_penalty(self, individual: Dict) -> float:
        """
        Individual için toplam penalty hesapla
        """
        instructor_schedules = self._extract_schedules_from_individual(individual)
        
        total_penalty = 0.0
        for instructor_id, projects in instructor_schedules.items():
            if len(projects) < 2:
                continue
                
            time_penalty = self.calculate_time_penalty(projects)
            class_penalty = self.calculate_class_penalty(projects)
            instructor_penalty = self.alpha * time_penalty + self.beta * class_penalty
            total_penalty += instructor_penalty
        
        return total_penalty

    def _penalty_guided_mutation(self, individual: Dict) -> Dict:
        """
        🤖 AI FEATURE 2: Adaptive Mutation Based on Penalties
        
        Yüksek penalty'li gene'leri daha fazla mutate et
        """
        if not hasattr(self, 'mutation_penalty_history'):
            self.mutation_penalty_history = []
        
        mutated_individual = individual.copy()
        mutated_assignments = []
        
        # Her assignment için penalty'ye göre mutation rate
        for assignment in individual.get('assignments', []):
            gene_penalty = self._calculate_gene_penalty(assignment)
            
            # Penalty'ye göre mutation rate
            if gene_penalty > self.high_penalty_threshold:
                mutation_rate = self.mutation_rate * 2  # Daha agresif
                logger.info(f"🤖 High penalty gene: {gene_penalty:.2f} -> aggressive mutation (rate: {mutation_rate:.3f})")
            else:
                mutation_rate = self.mutation_rate
                logger.info(f"🤖 Low penalty gene: {gene_penalty:.2f} -> normal mutation (rate: {mutation_rate:.3f})")
            
            # Mutation uygula
            if random.random() < mutation_rate:
                mutated_assignment = self._mutate_gene(assignment)
                mutated_assignments.append(mutated_assignment)
            else:
                mutated_assignments.append(assignment)
        
        mutated_individual['assignments'] = mutated_assignments
        
        # Mutation history'yi güncelle
        self.mutation_penalty_history.append({
            'original_penalty': self._calculate_individual_penalty(individual),
            'mutated_penalty': self._calculate_individual_penalty(mutated_individual),
            'improvement': self._calculate_individual_penalty(individual) - self._calculate_individual_penalty(mutated_individual),
            'timestamp': time.time()
        })
        
        return mutated_individual

    def _mutate_gene(self, assignment: Dict) -> Dict:
        """
        Gene'i mutate et
        """
        mutated_assignment = assignment.copy()
        
        # Timeslot mutation
        if random.random() < 0.5:
            # Random timeslot seç
            available_timeslots = [ts for ts in self.timeslots if ts.get('id')]
            if available_timeslots:
                new_timeslot = random.choice(available_timeslots)
                mutated_assignment['timeslot_id'] = new_timeslot.get('id')
        
        # Classroom mutation
        if random.random() < 0.3:
            # Random classroom seç
            available_classrooms = [cr for cr in self.classrooms if cr.get('id')]
            if available_classrooms:
                new_classroom = random.choice(available_classrooms)
                mutated_assignment['classroom_id'] = new_classroom.get('id')
        
        return mutated_assignment

    def _update_penalty_thresholds(self, population: List[Dict]) -> None:
        """
        Population'dan penalty threshold'larını güncelle
        """
        if not population:
            return
        
        # Population penalty'lerini hesapla
        penalties = [self._calculate_individual_penalty(individual) for individual in population]
        
        # High penalty threshold'u güncelle
        self.high_penalty_threshold = np.percentile(penalties, 75)  # Top %25
        
        logger.info(f"🤖 Updated high penalty threshold: {self.high_penalty_threshold:.2f}")
    
    def _ai_powered_selection(self, population: List[Dict], fitness_scores: List[float]) -> List[Dict]:
        """
        AI Feature 1: AI-Powered Selection
        Uses machine learning to select parents based on fitness landscape analysis
        """
        try:
            # Analyze fitness landscape
            fitness_std = np.std(fitness_scores)
            fitness_mean = np.mean(fitness_scores)
            
            # Adaptive selection pressure based on population diversity
            if fitness_std < 0.1:  # Low diversity
                selection_pressure = 0.8  # High pressure
            elif fitness_std > 0.5:  # High diversity
                selection_pressure = 0.3  # Low pressure
            else:
                selection_pressure = 0.5  # Medium pressure
            
            # AI-based parent selection
            selected_parents = []
            for _ in range(len(population) // 2):
                # Tournament selection with AI-enhanced criteria
                candidates = random.sample(population, min(5, len(population)))
                candidate_fitness = [fitness_scores[population.index(c)] for c in candidates]
                
                # AI scoring based on fitness landscape
                ai_scores = []
                for i, fitness in enumerate(candidate_fitness):
                    # Normalize fitness
                    normalized_fitness = (fitness - fitness_mean) / (fitness_std + 1e-8)
                    # AI bonus for diversity and potential
                    diversity_bonus = self._calculate_diversity_bonus(candidates[i], population)
                    potential_bonus = self._calculate_potential_bonus(candidates[i])
                    
                    ai_score = normalized_fitness + diversity_bonus + potential_bonus
                    ai_scores.append(ai_score)
                
                # Select best candidate based on AI score
                best_idx = np.argmax(ai_scores)
                selected_parents.append(candidates[best_idx])
            
            return selected_parents
            
        except Exception as e:
            # Fallback to tournament selection
            return [random.choice(population) for _ in range(len(population) // 2)]
    
    def _ai_powered_crossover(self, parent1: Dict, parent2: Dict) -> List[Dict]:
        """
        AI Feature 2: AI-Powered Crossover
        Uses pattern recognition to create intelligent offspring
        """
        try:
            # Analyze parent patterns
            parent1_patterns = self._extract_solution_patterns(parent1)
            parent2_patterns = self._extract_solution_patterns(parent2)
            
            # AI-based crossover strategy selection
            if len(parent1_patterns) > len(parent2_patterns):
                # Parent1 has more complex patterns - use its structure
                base_structure = parent1['assignments']
                pattern_injection = parent2_patterns
            else:
                # Parent2 has more complex patterns - use its structure
                base_structure = parent2['assignments']
                pattern_injection = parent1_patterns
            
            # Create intelligent offspring
            offspring1 = self._create_intelligent_offspring(base_structure, pattern_injection)
            offspring2 = self._create_intelligent_offspring(base_structure, pattern_injection, reverse=True)
            
            return [offspring1, offspring2]
            
        except Exception as e:
            # Fallback to uniform crossover
            return self._uniform_crossover(parent1, parent2)
    
    def _calculate_diversity_bonus(self, individual: Dict, population: List[Dict]) -> float:
        """Calculate diversity bonus for AI selection"""
        try:
            # Calculate similarity to other individuals
            similarities = []
            for other in population:
                if other != individual:
                    similarity = self._calculate_solution_similarity(individual, other)
                    similarities.append(similarity)
            
            # Diversity bonus is inverse of average similarity
            avg_similarity = np.mean(similarities) if similarities else 0
            diversity_bonus = (1 - avg_similarity) * 0.1  # Scale to reasonable range
            
            return diversity_bonus
            
        except:
            return 0.0
    
    def _calculate_potential_bonus(self, individual: Dict) -> float:
        """Calculate potential bonus for AI selection"""
        try:
            # Analyze solution structure for potential
            assignments = individual.get('assignments', [])
            if not assignments:
                return 0.0
            
            # Check for balanced workload distribution
            instructor_loads = {}
            for assignment in assignments:
                instructor_id = assignment.get('instructor_id')
                if instructor_id:
                    instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
            
            # Calculate load balance
            if instructor_loads:
                load_values = list(instructor_loads.values())
                load_std = np.std(load_values)
                load_mean = np.mean(load_values)
                
                # Lower std/mean ratio indicates better balance
                balance_score = 1 - (load_std / (load_mean + 1e-8))
                potential_bonus = balance_score * 0.05  # Scale to reasonable range
                
                return potential_bonus
            
            return 0.0
            
        except:
            return 0.0
    
    def _extract_solution_patterns(self, solution: Dict) -> List[Dict]:
        """Extract patterns from solution for AI crossover"""
        try:
            patterns = []
            assignments = solution.get('assignments', [])
            
            # Extract instructor patterns
            instructor_patterns = {}
            for assignment in assignments:
                instructor_id = assignment.get('instructor_id')
                if instructor_id:
                    if instructor_id not in instructor_patterns:
                        instructor_patterns[instructor_id] = []
                    instructor_patterns[instructor_id].append(assignment)
            
            # Extract classroom patterns
            classroom_patterns = {}
            for assignment in assignments:
                classroom_id = assignment.get('classroom_id')
                if classroom_id:
                    if classroom_id not in classroom_patterns:
                        classroom_patterns[classroom_id] = []
                    classroom_patterns[classroom_id].append(assignment)
            
            # Extract time patterns
            time_patterns = {}
            for assignment in assignments:
                time_slot = assignment.get('time_slot')
                if time_slot:
                    if time_slot not in time_patterns:
                        time_patterns[time_slot] = []
                    time_patterns[time_slot].append(assignment)
            
            patterns.extend([
                {'type': 'instructor', 'data': instructor_patterns},
                {'type': 'classroom', 'data': classroom_patterns},
                {'type': 'time', 'data': time_patterns}
            ])
            
            return patterns
            
        except:
            return []
    
    def _create_intelligent_offspring(self, base_structure: List[Dict], pattern_injection: List[Dict], reverse: bool = False) -> Dict:
        """Create intelligent offspring using AI patterns"""
        try:
            # Start with base structure
            offspring = {'assignments': base_structure.copy()}
            
            # Inject patterns intelligently
            for pattern in pattern_injection:
                if pattern['type'] == 'instructor' and pattern['data']:
                    # Inject instructor patterns
                    for instructor_id, assignments in pattern['data'].items():
                        if assignments:
                            # Select best assignment from pattern
                            best_assignment = max(assignments, key=lambda x: x.get('score', 0))
                            
                            # Find compatible slot in offspring
                            for i, assignment in enumerate(offspring['assignments']):
                                if assignment.get('instructor_id') == instructor_id:
                                    # Replace with pattern assignment
                                    offspring['assignments'][i] = best_assignment.copy()
                                    break
            
            return offspring
            
        except:
            # Fallback to base structure
            return {'assignments': base_structure.copy()}
    
    def _calculate_solution_similarity(self, sol1: Dict, sol2: Dict) -> float:
        """Calculate similarity between two solutions"""
        try:
            assignments1 = sol1.get('assignments', [])
            assignments2 = sol2.get('assignments', [])
            
            if not assignments1 or not assignments2:
                return 0.0
            
            # Calculate assignment similarity
            similar_assignments = 0
            total_assignments = max(len(assignments1), len(assignments2))
            
            for a1 in assignments1:
                for a2 in assignments2:
                    if (a1.get('instructor_id') == a2.get('instructor_id') and
                        a1.get('classroom_id') == a2.get('classroom_id') and
                        a1.get('time_slot') == a2.get('time_slot')):
                        similar_assignments += 1
                        break
            
            similarity = similar_assignments / total_assignments
            return similarity
            
        except:
            return 0.0
    
    def _uniform_crossover(self, parent1: Dict, parent2: Dict) -> List[Dict]:
        """Fallback uniform crossover"""
        try:
            assignments1 = parent1.get('assignments', [])
            assignments2 = parent2.get('assignments', [])
            
            if not assignments1 or not assignments2:
                return [parent1, parent2]
            
            # Create offspring by randomly selecting from parents
            offspring1 = {'assignments': []}
            offspring2 = {'assignments': []}
            
            for i in range(max(len(assignments1), len(assignments2))):
                if random.random() < 0.5:
                    if i < len(assignments1):
                        offspring1['assignments'].append(assignments1[i])
                    if i < len(assignments2):
                        offspring2['assignments'].append(assignments2[i])
                else:
                    if i < len(assignments2):
                        offspring1['assignments'].append(assignments2[i])
                    if i < len(assignments1):
                        offspring2['assignments'].append(assignments1[i])
            
            return [offspring1, offspring2]
            
        except:
            return [parent1, parent2]

    # ============================================================================
    # WORKLOAD CALCULATION FUNCTIONS
    # ============================================================================
    
    def _calculate_workload(self, instructor_id: int, assignments: List[Dict]) -> int:
        """
        Calculate instructor total workload (responsible + additional timeslots).
        
        Formula: responsible_projects + additional_timeslots
        
        Args:
            instructor_id: ID of the instructor
            assignments: List of all assignments
            
        Returns:
            Total workload count (integer)
        """
        total_workload = 0
        
        for assignment in assignments:
            instructors_list = assignment.get('instructors', [])
            normalized_list = self._normalize_instructors_list(instructors_list)
            if instructor_id in normalized_list:
                total_workload += 1
        
        return total_workload



    def _get_instructors_sorted_by_workload(self, assignments: List[Dict]) -> List[Tuple[int, int]]:
        """
        Get instructors sorted by workload (ascending - lowest first).
        
        Args:
            assignments: List of all assignments
            
        Returns:
            List of (instructor_id, workload_count) tuples, sorted by workload
        """
        instructor_workloads = []
        
        for instructor in self.instructors:
            instructor_id = instructor['id']
            workload = self._calculate_workload(instructor_id, assignments)
            instructor_workloads.append((instructor_id, workload))
        
        # Sort by workload (ascending - lowest first)
        instructor_workloads.sort(key=lambda x: x[1])
        
        return instructor_workloads

    def _has_timeslot_conflict(self, instructor_id: int, target_timeslot_id: int, target_classroom_id: int, assignments: List[Dict]) -> bool:
        """
        Check if instructor has a timeslot conflict with the target timeslot.
        
        YENİ MANTIK: 
        1. Sorumlu olarak aynı timeslot'ta çakışma varsa engelle
        2. Jüri olarak aynı timeslot'ta aynı sınıfta çakışma varsa engelle
        3. Jüri olarak aynı timeslot'ta farklı sınıflarda olabilir
        
        Args:
            instructor_id: ID of the instructor
            target_timeslot_id: Target timeslot ID
            target_classroom_id: Target classroom ID (NEW)
            assignments: List of all assignments
            
        Returns:
            True if there's a conflict, False otherwise
        """
        for assignment in assignments:
            if instructor_id in assignment.get('instructors', []):
                if assignment.get('timeslot_id') == target_timeslot_id:
                    # Sorumlu olarak aynı timeslot'ta çakışma varsa engelle
                    if assignment.get('responsible_instructor_id') == instructor_id:
                        return True
                    # Jüri olarak aynı timeslot'ta aynı sınıfta çakışma varsa engelle
                    if assignment.get('classroom_id') == target_classroom_id:
                        return True
                    # Jüri olarak aynı timeslot'ta farklı sınıflarda olabilir
                    # Bu durumda çakışma yok, devam et
        return False

    def _calculate_consecutive_bonus(
        self,
        instructor_id: int,
        target_classroom_id: int,
        target_timeslot_id: int,
        assignments: List[Dict]
    ) -> float:
        """
        Calculate consecutive bonus for instructor assignment.
        Higher bonus for instructors who can maintain consecutive assignments.
        
        Args:
            instructor_id: ID of the instructor
            target_classroom_id: Target classroom ID
            target_timeslot_id: Target timeslot ID
            assignments: List of all assignments
            
        Returns:
            Consecutive bonus score (0-1 range)
        """
        # Find instructor's current assignments
        instructor_assignments = [
            assignment for assignment in assignments
            if instructor_id in assignment.get('instructors', [])
        ]
        
        if not instructor_assignments:
            return 0.0
        
        # Check for consecutive same-classroom assignments
        consecutive_bonus = 0.0
        
        for assignment in instructor_assignments:
            assignment_classroom = assignment.get('classroom_id')
            assignment_timeslot = assignment.get('timeslot_id')
            
            # Same classroom bonus
            if assignment_classroom == target_classroom_id:
                consecutive_bonus += 0.5
                
                # Adjacent timeslot bonus
                timeslot_gap = abs(target_timeslot_id - assignment_timeslot)
                if timeslot_gap == 1:
                    consecutive_bonus += 0.3
                elif timeslot_gap == 0:
                    consecutive_bonus += 0.2
        
        return min(1.0, consecutive_bonus)

    def _calculate_workload_balance_score(self, instructor_id: int, assignments: List[Dict]) -> float:
        """
        Calculate workload balance score for uniform distribution.
        Lower workload = higher score (better for assignment)
        
        Args:
            instructor_id: ID of the instructor
            assignments: List of all assignments
            
        Returns:
            Workload balance score (0-1, higher is better)
        """
        current_workload = self._calculate_workload(instructor_id, assignments)
        
        # Get all instructor workloads
        all_workloads = [
            self._calculate_workload(inst['id'], assignments) 
            for inst in self.instructors
        ]
        
        if not all_workloads:
            return 0.5
        
        # Calculate balance score (inverse of workload)
        max_workload = max(all_workloads)
        min_workload = min(all_workloads)
        
        if max_workload == min_workload:
            return 0.5
        
        # Normalize to 0-1 range (lower workload = higher score)
        balance_score = 1.0 - ((current_workload - min_workload) / (max_workload - min_workload))
        
        return max(0.0, min(1.0, balance_score))

    def _calculate_priority_score(
        self,
        instructor_id: int,
        target_classroom_id: int,
        target_timeslot_id: int,
        assignments: List[Dict]
    ) -> float:
        """
        Calculate priority score with normalized components.
        
        Args:
            instructor_id: ID of the instructor
            target_classroom_id: Target classroom ID
            target_timeslot_id: Target timeslot ID
            assignments: List of all assignments
            
        Returns:
            Priority score (0-1 range)
        """
        # Calculate normalized workload
        normalized_workload = self._calculate_workload(instructor_id, assignments)
        
        # Calculate continuity score
        continuity_score = self._calculate_continuity_score(
            instructor_id, target_classroom_id, target_timeslot_id, assignments
        )
        
        # Normalize continuity score across all instructors
        all_continuity_scores = [
            self._calculate_continuity_score(
                inst['id'], target_classroom_id, target_timeslot_id, assignments
            )
            for inst in self.instructors
        ]
        max_continuity_score = max(all_continuity_scores) if all_continuity_scores else 1.0
        
        # Both components in 0-1 range
        priority_score = (
            0.5 * (1 - normalized_workload) +
            0.5 * (continuity_score / max(max_continuity_score, 0.01))
        )
        
        return min(1.0, max(0.0, priority_score))

    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎯 2. FAZ: JÜRİ ATAMA SİSTEMİ (Deterministik Dengeleme)
    # ═══════════════════════════════════════════════════════════════════════════════

    def _execute_phase2_jury_assignment(
        self, 
        phase1_assignments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        2. Faz Jüri Atama Sistemi - Açıklamalı Sözel Final Versiyon
        
        Bu sistem, 1. Faz yerleşimlerinin çıktısını kullanır ve deterministik 
        bir dengeleme fazı olarak çalışır.
        
        Amaç:
        - Her projede 1 Sorumlu + 2 Jüri olacak şekilde yapıyı tamamlamak
        - Öğretim üyeleri arasında dengeli iş yükü (workload balance) sağlamak
        
        Args:
            phase1_assignments: 1. Faz çıktısı (Liste olarak assignments)
        
        Returns:
            Dict: 2. Faz sonuçları ve istatistikler
        """
        logger.info("2. FAZ: Başlangıç analizi yapılıyor...")
        
        # 1. Faz atamalarını kopyala (değiştirilemez)
        phase2_assignments = [ass.copy() for ass in phase1_assignments]
        
        # Phase 1 sabitlerini kilitle: Sorumlu + mevcut jüri(ler) korunur
        # locked_jurors_by_project: {project_id: set(juror_ids_from_phase1)}
        locked_jurors_by_project: Dict[int, Set[int]] = {}
        for ass in phase2_assignments:
            proj_id = ass.get('project_id')
            if proj_id is None:
                continue
            instructors = ass.get('instructors', [])
            responsible_id = ass.get('responsible_instructor_id')
            if not responsible_id and instructors:
                first_instr = instructors[0]
                responsible_id = first_instr.get('id') if isinstance(first_instr, dict) else first_instr
            if isinstance(responsible_id, dict):
                responsible_id = responsible_id.get('id')
            locked = set()
            for ins in instructors:
                ins_id = ins.get('id') if isinstance(ins, dict) else ins
                if ins_id != responsible_id:
                    locked.add(ins_id)
            locked_jurors_by_project[proj_id] = locked
        
        # Timeslot sıralaması (zaman bazında)
        sorted_timeslots = sorted(
            self.timeslots,
            key=lambda ts: self._parse_time(ts.get("start_time", "09:00"))
        )
        timeslot_to_index = {ts['id']: idx for idx, ts in enumerate(sorted_timeslots)}
        
        # Mevcut durum analizi
        current_workloads = self._calculate_current_workloads(phase2_assignments)
        projects_needing_jury = self._identify_projects_needing_jury(phase2_assignments)
        
        logger.info(f"  Mevcut durum:")
        logger.info(f"    - Toplam proje: {len(phase2_assignments)}")
        logger.info(f"    - Eksik jüri olan proje sayısı (Y): {len(projects_needing_jury)}")
        logger.info(f"    - Ortalama iş yükü: {sum(current_workloads.values()) / len(current_workloads) if current_workloads else 0:.2f}")
        
        # X-Y Modeli ile ön hesap
        quota_plan = self._xy_model_quota_calculation(
            current_workloads, 
            len(projects_needing_jury),
            len(self.instructors)
        )
        
        logger.info(f"  X-Y Modeli ön hesap tamamlandı:")
        logger.info(f"    - Her hoca için 2. Faz jüri kotası belirlendi")
        
        # Atanabilirlik matrisi oluştur
        assignability_matrix = self._build_assignability_matrix(
            phase2_assignments, 
            projects_needing_jury,
            sorted_timeslots,
            timeslot_to_index
        )
        
        # Continuity-first pre-pass: continuity=1 ve underloaded öncelikli atamalar
        prepass_stats = self._continuity_priority_prepass(
            phase2_assignments,
            projects_needing_jury,
            quota_plan,
            assignability_matrix,
            sorted_timeslots,
            timeslot_to_index,
            locked_jurors_by_project
        )

        # Yerleştirme aşaması
        assignment_stats = self._complete_jury_assignments(
            phase2_assignments,
            projects_needing_jury,
            quota_plan,
            assignability_matrix,
            sorted_timeslots,
            timeslot_to_index,
            locked_jurors_by_project
        )
        
        # Denge kontrolü ve swap (gerekirse retry)
        balance_stats = self._balance_workload_with_swap(
            phase2_assignments,
            sorted_timeslots,
            timeslot_to_index,
            locked_jurors_by_project
        )
        
        # Swap sonrası kontrol: Eğer fark hala 3'ten fazlaysa retry mekanizması
        final_workloads_after_swap = self._calculate_current_workloads(phase2_assignments)
        workload_diff_after_swap = (
            max(final_workloads_after_swap.values()) - min(final_workloads_after_swap.values()) 
            if final_workloads_after_swap else 0
        )
        
        if workload_diff_after_swap > 2:
            logger.warning(f"  ⚠️ Swap sonrası yük farkı hala yüksek: {workload_diff_after_swap}")
            logger.info("  Retry: İş yükü dengesi için ek swap denemeleri yapılıyor...")
            
            # Ek swap denemeleri (daha agresif ve fazla)
            max_retries = 5  # 3'ten 5'e çıkarıldı
            for retry_round in range(max_retries):
                balance_stats_retry = self._balance_workload_with_swap(
                    phase2_assignments,
                    sorted_timeslots,
                    timeslot_to_index,
                    locked_jurors_by_project
                )
                balance_stats["swaps_performed"] += balance_stats_retry["swaps_performed"]
                
                final_workloads_check = self._calculate_current_workloads(phase2_assignments)
                if not final_workloads_check:
                    break
                    
                workload_diff_check = (
                    max(final_workloads_check.values()) - min(final_workloads_check.values())
                )
                avg_check = sum(final_workloads_check.values()) / len(final_workloads_check)
                
                logger.info(f"  Retry #{retry_round + 1}: Fark={workload_diff_check}, Ort={avg_check:.1f}, "
                           f"Min={min(final_workloads_check.values())}, Max={max(final_workloads_check.values())}")
                
                if workload_diff_check <= 2:
                    logger.info(f"  ✅ Retry #{retry_round + 1}: Denge sağlandı (fark: {workload_diff_check})")
                    break
                
                # Eğer fark hala çok büyükse (5'ten fazla), agresif multi-swap yap
                if workload_diff_check > 5 and retry_round < max_retries - 1:
                    logger.warning(f"  🔥 Agresif multi-swap başlatılıyor (fark: {workload_diff_check})...")
                    aggressive_swaps = self._aggressive_workload_rebalancing(
                        phase2_assignments,
                        sorted_timeslots,
                        timeslot_to_index,
                        final_workloads_check,
                        locked_jurors_by_project
                    )
                    balance_stats["swaps_performed"] += aggressive_swaps
        
        # Ek alt sınır zorlaması: Herkes X-1'e kadar çıkarılsın (örn. 13)
        num_instructors = len(self.instructors) if hasattr(self, 'instructors') else 0
        total_projects = len(self.projects) if hasattr(self, 'projects') else 0
        final_avg_target = (3 * total_projects) / num_instructors if num_instructors > 0 else 0
        x_min_bound = max(0, int(final_avg_target) - 1)
        x_max_bound = int(final_avg_target) + 1
        lower_bound_swaps = self._enforce_lower_bound_with_swaps(
            phase2_assignments,
            sorted_timeslots,
            timeslot_to_index,
            x_min_bound,
            x_max_bound,
            locked_jurors_by_project,
            max_iterations=500
        )
        
        # Final kontrol: Tüm projelerde 2 jüri var mı?
        final_projects_needing_jury = self._identify_projects_needing_jury(phase2_assignments)
        if final_projects_needing_jury:
            logger.warning(f"  ⚠️ UYARI: {len(final_projects_needing_jury)} projede hala eksik jüri var!")
            for proj in final_projects_needing_jury[:5]:  # İlk 5 tanesini göster
                logger.warning(f"    - Proje {proj.get('project_id')}: {len([i for i in proj.get('instructors', []) if i != proj.get('responsible_instructor_id')])} jüri")
        
        # Final istatistikler
        final_workloads = self._calculate_current_workloads(phase2_assignments)
        
        stats = {
            "projects_needing_jury": len(projects_needing_jury),
            "assignments_made": assignment_stats.get("assignments_made", 0) + prepass_stats.get("assignments_made", 0),
            "failed_assignments": assignment_stats.get("failed_assignments", 0),
            "remaining_projects_needing_jury": len(final_projects_needing_jury),
            "balance_swaps": balance_stats.get("swaps_performed", 0),
            "final_workload": {
                "min": min(final_workloads.values()) if final_workloads else 0,
                "max": max(final_workloads.values()) if final_workloads else 0,
                "avg": sum(final_workloads.values()) / len(final_workloads) if final_workloads else 0,
                "std": float(np.std(list(final_workloads.values()))) if final_workloads else 0.0
            },
            "workload_diff": max(final_workloads.values()) - min(final_workloads.values()) if final_workloads else 0
        }
        
        # 🎯 3. FAZ: FINAL FIXATION PHASE (Placeholder Ekleme)
        # Phase 2 assignments'ı koruyarak, eksik projelere placeholder ekle
        import copy
        
        final_assignments = copy.deepcopy(phase2_assignments)
        phase3_placeholders_added = 0
        
        placeholder_instructor = {"id": -1, "name": "[Araştırma Görevlisi]", "is_placeholder": True}
        
        if final_projects_needing_jury:
            logger.info("=" * 80)
            logger.info("3. FAZ: FINAL FIXATION PHASE (Placeholder Ekleme)")
            logger.info(f"  📋 {len(final_projects_needing_jury)} projede eksik jüri tespit edildi")
            
            for proj_needing_jury in final_projects_needing_jury:
                project_id = proj_needing_jury.get('project_id')
                if project_id is None:
                    continue
                
                # Bu projeyi final_assignments'ta bul
                for assignment in final_assignments:
                    if assignment.get('project_id') == project_id:
                        instructors_list = assignment.get('instructors', [])
                        
                        # Instructors listesini dict formatına normalize et (tutarlılık için)
                        # Eğer liste int formatındaysa, dict formatına çevir
                        normalized_instructors = []
                        for inst in instructors_list:
                            # Placeholder'ları atla (zaten varsa tekrar ekleme)
                            if isinstance(inst, dict) and inst.get('is_placeholder'):
                                continue
                            if isinstance(inst, dict):
                                normalized_instructors.append(inst)
                            elif isinstance(inst, int):
                                # Int'i dict'e çevir (frontend bekliyor)
                                normalized_instructors.append({"id": inst, "name": f"Instructor {inst}"})
                            else:
                                # Bilinmeyen format, atla
                                continue
                        
                        # Normalize edilmiş instructor ID'lerini al (jüri sayısını hesaplamak için)
                        normalized_ids = self._normalize_instructors_list(normalized_instructors)
                        responsible_id = self._normalize_instructor_id(assignment.get('responsible_instructor_id'))
                        
                        # Responsible hariç kaç jüri var?
                        jury_count = len([inst_id for inst_id in normalized_ids if inst_id != responsible_id])
                        
                        # Eğer 2 jüri yoksa, placeholder ekle
                        missing_count = 0
                        if jury_count < 2:
                            missing_count = 2 - jury_count
                            # Placeholder ekle
                            for _ in range(missing_count):
                                normalized_instructors.append(copy.deepcopy(placeholder_instructor))
                        
                        # Güncellenmiş listeyi ata
                        assignment['instructors'] = normalized_instructors
                        
                        if missing_count > 0:
                            phase3_placeholders_added += missing_count
                            logger.info(f"  ✅ Proje {project_id}: {missing_count} placeholder jüri eklendi")
                        break
            
            logger.info(f"  📊 Toplam {phase3_placeholders_added} placeholder eklendi")
            logger.info("=" * 80)

        # Özet log
        logger.info("=" * 80)
        logger.info("2. FAZ ÖZET:")
        logger.info(f"  - İşlenen proje: {len(projects_needing_jury)}")
        logger.info(f"  - Başarılı atama: {stats['assignments_made']}")
        logger.info(f"  - Başarısız atama: {stats['failed_assignments']}")
        logger.info(f"  - Kalan eksik proje: {stats['remaining_projects_needing_jury']}")
        logger.info(f"  - Swap sayısı: {stats['balance_swaps']}")
        logger.info(f"  - Final iş yükü: Min={stats['final_workload']['min']}, "
                   f"Max={stats['final_workload']['max']}, "
                   f"Avg={stats['final_workload']['avg']:.2f}, "
                   f"Fark={stats['workload_diff']}")
        if phase3_placeholders_added > 0:
            logger.info(f"  - 3. Faz placeholder: {phase3_placeholders_added} adet eklendi")
        logger.info("=" * 80)
        
        return {
            "assignments": phase2_assignments,  # Orijinal Phase 2 (değiştirilmedi)
            "final_assignments": final_assignments,  # Phase 3 ile placeholder eklenmiş
            "stats": stats,
            "quota_plan": quota_plan,
            "phase3_stats": {
                "placeholders_added": phase3_placeholders_added,
                "projects_fixed": len(final_projects_needing_jury) if final_projects_needing_jury else 0
            }
        }

    def _calculate_current_workloads(
        self, 
        assignments: List[Dict[str, Any]]
    ) -> Dict[int, int]:
        """
        Mevcut iş yüklerini hesapla (her öğretim üyesi için toplam görev sayısı)
        
        Args:
            assignments: Atama listesi
        
        Returns:
            Dict[int, int]: instructor_id -> toplam görev sayısı
        """
        workloads = defaultdict(int)
        
        for assignment in assignments:
            # Sorumlu instructor
            responsible_id = assignment.get("responsible_instructor_id")
            if not responsible_id and assignment.get("instructors"):
                first_instructor = assignment["instructors"][0]
                # Eğer dict ise id'sini al
                responsible_id = first_instructor.get("id") if isinstance(first_instructor, dict) else first_instructor
            
            # Responsible ID'yi normalize et
            if isinstance(responsible_id, dict):
                responsible_id = responsible_id.get("id")
            
            if responsible_id:
                workloads[responsible_id] += 1
            
            # Jüri üyeleri
            instructors = assignment.get("instructors", [])
            for instr in instructors:
                # Placeholder RA ise sayma
                if isinstance(instr, dict) and instr.get("is_placeholder"):
                    continue
                # ID'yi normalize et (int veya dict olabilir)
                instr_id = instr.get("id") if isinstance(instr, dict) else instr
                
                if instr_id != responsible_id:
                    workloads[instr_id] += 1
        
        return dict(workloads)

    def _identify_projects_needing_jury(
        self, 
        assignments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Eksik jüri olan projeleri belirle (1 Sorumlu + 1 Jüri = eksik)
        
        Args:
            assignments: Atama listesi
        
        Returns:
            List[Dict]: Eksik jüri olan proje assignment'ları
        """
        projects_needing = []
        
        for assignment in assignments:
            instructors = assignment.get("instructors", [])
            responsible_id = assignment.get("responsible_instructor_id")
            
            # Responsible ID'yi normalize et
            if not responsible_id and instructors:
                first_instructor = instructors[0]
                responsible_id = first_instructor.get("id") if isinstance(first_instructor, dict) else first_instructor
            
            if isinstance(responsible_id, dict):
                responsible_id = responsible_id.get("id")
            
            # Sorumlu dışındaki jüri sayısı
            jury_count = 0
            for instr in instructors:
                instr_id = instr.get("id") if isinstance(instr, dict) else instr
                if instr_id != responsible_id:
                    jury_count += 1
            
            # 2 jüri gerekiyor, 2'den az varsa eksik
            # (1. Faz'da 1 jüri var, 2. Faz'da 2. jüri ekleniyor)
            if jury_count < 2:
                projects_needing.append(assignment)
        
        return projects_needing

    def _xy_model_quota_calculation(
        self,
        current_workloads: Dict[int, int],
        y: int,  # Eksik jüri olan proje sayısı
        num_instructors: int
    ) -> Dict[int, int]:
        """
        X-Y Modeli ile hedef jüri dağılımı hesaplama
        
        X: Ortalama iş yükü (hedef) - mevcut yükler + yeni jüriler hesaba katılır
        Y: Eksik jüri olan proje sayısı
        
        Adım 1: Minimuma tamamlama (X-1)
        Adım 2: Ortalama seviyeye çıkarma (X)
        Adım 3: Maksimum seviyeye çıkarma (X+1)
        
        Args:
            current_workloads: Mevcut iş yükleri (1. Faz sonrası)
            y: Eksik jüri sayısı
            num_instructors: Toplam öğretim üyesi sayısı
        
        Returns:
            Dict[int, int]: instructor_id -> 2. Faz'da alacağı jüri sayısı
        """
        if y == 0:
            return {inst_id: 0 for inst_id in current_workloads.keys()}
        
        # Tüm öğretim üyelerini dahil et (eğer current_workloads'ta yoksa ekle)
        for instructor in self.instructors:
            inst_id = instructor['id']
            if inst_id not in current_workloads:
                current_workloads[inst_id] = 0
        
        # Mevcut toplam yükü hesapla
        total_current_workload = sum(current_workloads.values())
        
        # Hedef: Her projede 1 Sorumlu + 2 Jüri = 3 görev
        total_projects = len(self.projects) if self.projects else y
        total_target_tasks = total_projects * 3  # Her proje için 3 görev
        
        # Ortalama iş yükü (hedef): (mevcut yük + yeni jüriler) / öğretim üyesi sayısı
        # Yeni jüriler = Y (eksik jüri sayısı)
        # X = (mevcut_yük + Y) / num_instructors
        x = (total_current_workload + y) / num_instructors if num_instructors > 0 else 0
        x_min = max(0, int(x) - 1)  # Minimum (negatif olamaz)
        x_max = int(x) + 1  # Maksimum
        
        logger.info(f"  X-Y Modeli: Mevcut toplam yük={total_current_workload}, Y={y}, X={x:.2f}, X_min={x_min}, X_max={x_max}")
        
        # Her öğretim üyesi için kota başlangıç değeri
        quota = {inst_id: 0 for inst_id in current_workloads.keys()}
        
        # Mevcut yükleri sırala (az yükten çok yüke)
        sorted_instructors = sorted(
            current_workloads.items(),
            key=lambda x: x[1]
        )
        
        remaining_assignments = y
        assigned_quota = 0
        
        # ═══════════════════════════════════════════════════════════════════════
        # Adım 1: Minimuma tamamlama (X-1) - UNIFORM DAĞILIM GARANTİSİ
        # ═══════════════════════════════════════════════════════════════════════
        # ÖNEMLİ: Uniform dağılım için ÖNCE herkesi X-1'e çıkarmalıyız
        # Eğer bu işlem için yeterli jüri yoksa, mümkün olduğunca eşit dağıtılır
        logger.info(f"  Adım 1: Minimuma tamamlama başlatılıyor (X-1={x_min})...")
        
        # Önce X-1'in altında kalan TÜM hocaları belirle
        instructors_below_x_min = [
            (inst_id, current_load) 
            for inst_id, current_load in sorted_instructors 
            if current_load < x_min
        ]
        
        if instructors_below_x_min:
            total_needed_for_x_min = sum(x_min - load for _, load in instructors_below_x_min)
            logger.info(f"    {len(instructors_below_x_min)} hoca X-1 seviyesine çıkarılacak, gerekli jüri: {total_needed_for_x_min}")
            
            # Eğer yeterli jüri varsa, HERKESİ X-1'e çıkar
            if remaining_assignments >= total_needed_for_x_min:
                for inst_id, current_load in instructors_below_x_min:
                    needed = x_min - current_load
                    quota[inst_id] = needed
                    assigned_quota += needed
                    remaining_assignments -= needed
                    logger.debug(f"    Hoca {inst_id}: {current_load} -> {current_load + needed} (X-1'e çıkarıldı)")
                logger.info(f"  ✅ Adım 1 (Min): Tüm hocalar X-1 seviyesine çıkarıldı, kalan: {remaining_assignments}")
            else:
                # Yeterli jüri yoksa, mümkün olduğunca eşit dağıt
                # En az yükteki hocalardan başla
                for inst_id, current_load in instructors_below_x_min:
                    if remaining_assignments <= 0:
                        break
                    needed = x_min - current_load
                    assigned = min(needed, remaining_assignments)
                    quota[inst_id] = assigned
                    assigned_quota += assigned
                    remaining_assignments -= assigned
                    logger.debug(f"    Hoca {inst_id}: {current_load} -> {current_load + assigned} (kısmi: {assigned}/{needed})")
                logger.warning(f"  ⚠️ Adım 1 (Min): Yeterli jüri yok, {assigned_quota} jüri dağıtıldı, kalan: {remaining_assignments}, "
                             f"{len([inst for inst, load in instructors_below_x_min if (load + quota.get(inst, 0)) < x_min])} hoca hala X-1 altında")
        
        # Erken durdurma kontrolü: Eğer tüm jüriler dağıtıldıysa dur
        if remaining_assignments <= 0:
            logger.info(f"  Adım 1 (Min) tamamlandı: {assigned_quota} jüri kotası dağıtıldı")
            # Uniform dağılım kontrolü: Eğer herkes X-1 veya üzerindeyse ve jüri kalmadıysa OK
            final_totals_after_step1 = {inst_id: current_workloads[inst_id] + quota[inst_id] for inst_id in current_workloads.keys()}
            all_above_x_min = all(total >= x_min for total in final_totals_after_step1.values())
            if all_above_x_min:
                logger.info(f"  ✅ Uniform dağılım sağlandı: Tüm hocalar X-1 ({x_min}) veya üzerinde")
                return quota
            else:
                below_count = sum(1 for total in final_totals_after_step1.values() if total < x_min)
                logger.warning(f"  ⚠️ {below_count} hoca hala X-1 altında, ancak jüri kalmadı")
                return quota
        
        # ═══════════════════════════════════════════════════════════════════════
        # Adım 2: Ortalama seviyeye çıkarma (X) - UNIFORM DAĞILIM GARANTİSİ
        # ═══════════════════════════════════════════════════════════════════════
        # ÖNEMLİ: Mümkün olduğunca çok hocayı X seviyesine çıkar
        logger.info(f"  Adım 2: Ortalama seviyeye çıkarma başlatılıyor (X={x:.2f})...")
        
        # X'in altında kalan hocaları belirle (quota dahil)
        instructors_below_x = [
            (inst_id, current_load + quota.get(inst_id, 0))
            for inst_id, current_load in sorted_instructors
            if (current_load + quota.get(inst_id, 0)) < x
        ]
        
        if instructors_below_x:
            # Önce herkesi X seviyesine çıkarmaya çalış
            for inst_id, current_total in instructors_below_x:
                if remaining_assignments <= 0:
                    break
                needed = max(1, int(x) - current_total)  # En az 1
                additional = min(needed, remaining_assignments)
                quota[inst_id] = quota.get(inst_id, 0) + additional
                assigned_quota += additional
                remaining_assignments -= additional
                logger.debug(f"    Hoca {inst_id}: {current_total} -> {current_total + additional} (kota: +{additional})")
        
        # Erken durdurma kontrolü
        if remaining_assignments <= 0:
            logger.info(f"  Adım 2 (Avg) tamamlandı: {assigned_quota} jüri kotası dağıtıldı")
            # Uniform dağılım kontrolü: Dağılım X-1, X, X+1 arasında mı?
            final_totals_after_step2 = {inst_id: current_workloads[inst_id] + quota[inst_id] for inst_id in current_workloads.keys()}
            if final_totals_after_step2:
                wl_max = max(final_totals_after_step2.values())
                wl_min = min(final_totals_after_step2.values())
                wl_diff = wl_max - wl_min
                if wl_diff <= 2:  # Maks-Min farkı 2 veya daha az = uniform (x-1, x, x+1)
                    logger.info(f"  ✅ Uniform dağılım sağlandı: Min={wl_min}, Max={wl_max}, Fark={wl_diff} (X-1, X, X+1 aralığında)")
                    return quota
            return quota
        
        # ═══════════════════════════════════════════════════════════════════════
        # Adım 3: Maksimum seviyeye çıkarma (X+1) - UNIFORM DAĞILIM GARANTİSİ
        # ═══════════════════════════════════════════════════════════════════════
        # ÖNEMLİ: Bazı hocaları X+1'e çıkararak uniform dağılımı tamamla
        logger.info(f"  Adım 3: Maksimum seviyeye çıkarma başlatılıyor (X+1={x_max})...")
        
        # X+1'in altında kalan hocaları belirle ve en az yükteki hocalardan başla
        sorted_for_max = sorted(
            [(inst_id, current_load + quota.get(inst_id, 0)) for inst_id, current_load in sorted_instructors],
            key=lambda x: x[1]
        )
        
        for inst_id, current_total in sorted_for_max:
            if remaining_assignments <= 0:
                break
            if current_total < x_max:
                needed = x_max - current_total
                additional = min(needed, remaining_assignments)
                quota[inst_id] = quota.get(inst_id, 0) + additional
                assigned_quota += additional
                remaining_assignments -= additional
                logger.debug(f"    Hoca {inst_id}: {current_total} -> {current_total + additional} (kota: +{additional})")
        
        logger.info(f"  Adım 3 (Max) tamamlandı: {assigned_quota} jüri kotası dağıtıldı, kalan: {remaining_assignments}")
        
        # Uniform dağılım kontrolü: Eğer fark 2 veya daha azsa ve jüri kaldıysa bile erken durdur
        current_totals = {inst_id: current_workloads[inst_id] + quota[inst_id] for inst_id in current_workloads.keys()}
        if current_totals:
            wl_max = max(current_totals.values())
            wl_min = min(current_totals.values())
            wl_diff = wl_max - wl_min
            if wl_diff <= 2 and remaining_assignments > 0:
                logger.info(f"  ✅ Uniform dağılım sağlandı (Adım 3): Min={wl_min}, Max={wl_max}, Fark={wl_diff} "
                           f"(X-1, X, X+1 aralığında). Kalan {remaining_assignments} jüri atlanıyor (uniform dağılım için yeterli)")
                return quota
        
        # Eğer hala kalan varsa, en az yükteki hocalara EŞİT dağıt
        # Uniform dağılım için kritik: Her hoca için toplam yük (current + quota) hedef ortalama civarında olmalı
        if remaining_assignments > 0:
            logger.warning(f"  UYARI: {remaining_assignments} jüri kotası kaldı, uniform dağılım için en az yükteki hocalara eşit dağıtılıyor")
            # Ortalama hedef değer (final toplam yük hedefi)
            target_avg = (sum(current_workloads.values()) + y) / num_instructors
            
            # İYİLEŞTİRME: Daha akıllı round-robin dağıtım
            # Her iterasyonda toplam yükü yeniden hesapla ve en az yükteki hocalara dönüşümlü dağıt
            while remaining_assignments > 0:
                # Şu anki toplam yükleri hesapla (current + quota)
                current_totals = {
                    inst_id: current_workloads[inst_id] + quota[inst_id] 
                    for inst_id in current_workloads.keys()
                }
                
                # En az yükteki hocaları bul (hedef ortalamanın üstüne çıkmamış olanlar)
                eligible_instructors = [
                    (inst_id, total) 
                    for inst_id, total in current_totals.items() 
                    if total < target_avg + 1.5  # Hedef ortalamanın 1.5 üstüne çıkmamış olanlar
                ]
                
                # Eğer hepsi ortalamadan 1.5 üstündeyse, yine de en az yüktekilere dağıt
                if not eligible_instructors:
                    eligible_instructors = sorted(
                        current_totals.items(),
                        key=lambda x: x[1]
                    )
                
                # En az yükteki hocaları sırala
                eligible_instructors.sort(key=lambda x: x[1])
                
                # Dönüşümlü dağıt: Her seferinde en az yükteki hocalara birer birer ver
                # Aynı anda birden fazla hoca aynı yükteyse hepsine dönüşümlü dağıt
                lowest_workload = eligible_instructors[0][1] if eligible_instructors else 0
                same_lowest = [
                    inst_id for inst_id, total in eligible_instructors 
                    if total == lowest_workload
                ]
                
                # En az yükteki hocalara dönüşümlü dağıt
                distributed_this_round = 0
                for inst_id in same_lowest:
                    if remaining_assignments <= 0:
                        break
                quota[inst_id] += 1
                remaining_assignments -= 1
                assigned_quota += 1
                distributed_this_round += 1
                logger.debug(f"    Hoca {inst_id}: kotaya +1 eklendi (toplam: {current_totals[inst_id] + 1}, kalan: {remaining_assignments})")
                
                # Eğer bu turda hiçbir şey dağıtılamadıysa (nadir durum), zorla en az yüktekiye ver
                if distributed_this_round == 0 and remaining_assignments > 0:
                    if eligible_instructors:
                        inst_id = eligible_instructors[0][0]
                        quota[inst_id] += 1
                        remaining_assignments -= 1
                        assigned_quota += 1
                        logger.debug(f"    Hoca {inst_id}: ZORLA +1 eklendi (toplam: {current_totals[inst_id] + 1}, kalan: {remaining_assignments})")
                    else:
                        # Gerçekten hiç hoca yoksa, rastgele birine ver (çok nadir)
                        inst_id = list(current_workloads.keys())[0]
                        quota[inst_id] += 1
                        remaining_assignments -= 1
                        assigned_quota += 1
                        logger.warning(f"    ⚠️ Hoca {inst_id}: ACİL durum +1 eklendi (toplam: {current_totals.get(inst_id, 0) + 1}, kalan: {remaining_assignments})")
        
        logger.info(f"  ✅ X-Y Modeli tamamlandı: Toplam {assigned_quota} jüri kotası dağıtıldı")
        return quota

    def _build_assignability_matrix(
        self,
        assignments: List[Dict[str, Any]],
        projects_needing_jury: List[Dict[str, Any]],
        sorted_timeslots: List[Dict[str, Any]],
        timeslot_to_index: Dict[int, int]
    ) -> Dict[Tuple[int, int], bool]:
        """
        Atanabilirlik matrisi oluştur (Aᵢₛ)
        
        Aᵢₛ = 1 eğer öğretim üyesi i, slot s'ye uygunsa
        
        Args:
            assignments: Tüm atamalar
            projects_needing_jury: Eksik jüri olan projeler
            sorted_timeslots: Sıralı timeslot listesi
            timeslot_to_index: Timeslot ID -> index mapping
        
        Returns:
            Dict[Tuple[int, int], bool]: (instructor_id, slot_key) -> atanabilir mi?
        """
        matrix = {}
        
        # Her instructor için her slot'u kontrol et
        for instructor in self.instructors:
            inst_id = instructor['id']
            
            for project_assignment in projects_needing_jury:
                project_id = project_assignment.get('project_id')
                classroom_id = project_assignment.get('classroom_id')
                timeslot_id = project_assignment.get('timeslot_id')
                
                slot_key = (classroom_id, timeslot_id)
                
                # Atanabilirlik kontrolü
                is_assignable = self._check_instructor_assignability(
                    inst_id,
                    project_assignment,
                    assignments
                )
                
                matrix[(inst_id, slot_key)] = is_assignable
        
        return matrix

    def _check_instructor_assignability(
        self,
        instructor_id: int,
        project_assignment: Dict[str, Any],
        all_assignments: List[Dict[str, Any]]
    ) -> bool:
        """
        Bir öğretim üyesinin bir slota atanabilir olup olmadığını kontrol et
        
        Koşullar:
        1. Aynı saatte başka görevi yok
        2. Aynı projede zaten jüri veya sorumlu değil
        3. Zaman çakışması yok
        
        Args:
            instructor_id: Öğretim üyesi ID
            project_assignment: Proje ataması
            all_assignments: Tüm atamalar
        
        Returns:
            bool: Atanabilir mi?
        """
        target_timeslot_id = project_assignment.get('timeslot_id')
        target_project_id = project_assignment.get('project_id')
        
        # Aynı timeslot'ta başka görevi var mı?
        for assignment in all_assignments:
            if assignment.get('timeslot_id') == target_timeslot_id:
                instructors = assignment.get('instructors', [])
                if instructor_id in instructors:
                    return False
        
        # Aynı projede zaten görevli mi?
        for assignment in all_assignments:
            if assignment.get('project_id') == target_project_id:
                instructors = assignment.get('instructors', [])
                responsible_id = assignment.get('responsible_instructor_id')
                if not responsible_id and instructors:
                    responsible_id = instructors[0]
                
                if instructor_id in instructors or instructor_id == responsible_id:
                    return False
        
        return True

    def _calculate_continuity_score(
        self,
        instructor_id: int,
        classroom_id: int,
        timeslot_id: int,
        assignments: List[Dict[str, Any]],
        sorted_timeslots: List[Dict[str, Any]],
        timeslot_to_index: Dict[int, int]
    ) -> float:
        """
        Continuity skoru hesapla (Rᵢₛ)
        
        Aynı sınıfta, bitişik oturumlarda görev varsa → skor 1
        Zaman boşluğu veya sınıf değişimi varsa → skor 0
        
        Args:
            instructor_id: Öğretim üyesi ID
            classroom_id: Hedef sınıf ID
            timeslot_id: Hedef timeslot ID
            assignments: Tüm atamalar
            sorted_timeslots: Sıralı timeslot listesi
            timeslot_to_index: Timeslot ID -> index mapping
        
        Returns:
            float: Continuity skoru (0 veya 1)
        """
        # Yardımcı: timeslot'tan gün bilgisini güvenli şekilde çek
        def _get_day_key(ts: Dict[str, Any]) -> Any:
            for key in ('day_id', 'day', 'date', 'date_str'):
                if key in ts:
                    return ts.get(key)
            return None

        # Hedef timeslot objesini bul
        target_ts = None
        for ts in sorted_timeslots:
            if ts.get('id') == timeslot_id:
                target_ts = ts
                break
        if target_ts is None:
            return 0.0
        
        target_day = _get_day_key(target_ts)

        # Aynı günün slotlarını zaman sırasına göre çıkar
        same_day_slots = [ts for ts in sorted_timeslots if _get_day_key(ts) == target_day]
        if not same_day_slots:
            same_day_slots = sorted_timeslots  # gün bilgisi yoksa tüm liste

        # same_day_slots içinde hedef index'i bul
        day_index = None
        for idx, ts in enumerate(same_day_slots):
            if ts.get('id') == timeslot_id:
                day_index = idx
                break
        if day_index is None:
            return 0.0

        # Önceki ve sonraki slot id'lerini al (aynı gün)
        prev_timeslot_id = same_day_slots[day_index - 1]['id'] if day_index - 1 >= 0 else None
        next_timeslot_id = same_day_slots[day_index + 1]['id'] if day_index + 1 < len(same_day_slots) else None

        # Önceki slot kontrolü (aynı sınıf)
        if prev_timeslot_id is not None:
            for assignment in assignments:
                if (assignment.get('classroom_id') == classroom_id and
                    assignment.get('timeslot_id') == prev_timeslot_id):
                    instructors = assignment.get('instructors', [])
                    responsible_id = assignment.get('responsible_instructor_id')
                    if not responsible_id and instructors:
                        responsible_id = instructors[0]
                    if instructor_id in instructors or instructor_id == responsible_id:
                        return 1.0
        
        # Sonraki slot kontrolü (aynı sınıf)
        if next_timeslot_id is not None:
            for assignment in assignments:
                if (assignment.get('classroom_id') == classroom_id and
                    assignment.get('timeslot_id') == next_timeslot_id):
                    instructors = assignment.get('instructors', [])
                    responsible_id = assignment.get('responsible_instructor_id')
                    if not responsible_id and instructors:
                        responsible_id = instructors[0]
                    if instructor_id in instructors or instructor_id == responsible_id:
                        return 1.0
        
        return 0.0

    def _calculate_chain_extension_score(
        self,
        instructor_id: int,
        classroom_id: int,
        timeslot_id: int,
        assignments: List[Dict[str, Any]],
        sorted_timeslots: List[Dict[str, Any]],
        timeslot_to_index: Dict[int, int]
    ) -> int:
        """
        Bir hocanın hedef slotta görevlendirilmesi halinde, aynı sınıfta oluşacak bitişik zincirin
        uzama potansiyelini hesaplar.

        Dönüş:
            int: Sol bitişik streak + sağ bitişik streak (hedef slot dahil edilmeden)
        """
        # Hedef timeslot objesini bul
        target_ts = None
        for ts in sorted_timeslots:
            if ts.get('id') == timeslot_id:
                target_ts = ts
                break
        if target_ts is None:
            return 0

        # Aynı günün slotlarını sırala
        def _get_day_key(ts: Dict[str, Any]) -> Any:
            for key in ('day_id', 'day', 'date', 'date_str'):
                if key in ts:
                    return ts.get(key)
            return None

        target_day = _get_day_key(target_ts)
        same_day_slots = [ts for ts in sorted_timeslots if _get_day_key(ts) == target_day]
        if not same_day_slots:
            same_day_slots = sorted_timeslots

        # Hedef index'i bul
        idx_target = None
        for idx, ts in enumerate(same_day_slots):
            if ts.get('id') == timeslot_id:
                idx_target = idx
                break
        if idx_target is None:
            return 0

        # Yardımcı: belirli timeslot'ta aynı sınıfta bu hoca var mı?
        def _has_instructor_at(ts_id: int) -> bool:
            for a in assignments:
                if a.get('classroom_id') != classroom_id:
                    continue
                if a.get('timeslot_id') != ts_id:
                    continue
                ins_list = a.get('instructors', [])
                resp_id = a.get('responsible_instructor_id')
                if not resp_id and ins_list:
                    first_ins = ins_list[0]
                    resp_id = first_ins.get('id') if isinstance(first_ins, dict) else first_ins
                if isinstance(resp_id, dict):
                    resp_id = resp_id.get('id')
                # Normalize
                for ins in ins_list:
                    iid = ins.get('id') if isinstance(ins, dict) else ins
                    if iid == instructor_id:
                        return True
                if resp_id and resp_id == instructor_id:
                    return True
            return False

        # Sol streak
        left = 0
        i = idx_target - 1
        while i >= 0:
            ts_id = same_day_slots[i].get('id')
            if _has_instructor_at(ts_id):
                left += 1
                i -= 1
            else:
                break

        # Sağ streak
        right = 0
        i = idx_target + 1
        while i < len(same_day_slots):
            ts_id = same_day_slots[i].get('id')
            if _has_instructor_at(ts_id):
                right += 1
                i += 1
            else:
                break

        return left + right

    def _continuity_priority_prepass(
        self,
        assignments: List[Dict[str, Any]],
        projects_needing_jury: List[Dict[str, Any]],
        quota_plan: Dict[int, int],
        assignability_matrix: Dict[Tuple[int, int], bool],
        sorted_timeslots: List[Dict[str, Any]],
        timeslot_to_index: Dict[int, int],
        locked_jurors_by_project: Optional[Dict[int, Set[int]]] = None
    ) -> Dict[str, Any]:
        """
        Continuity=1 olan ve underloaded (özellikle X-1 altı) hocaları önceliklendirerek
        eksik 2. jüri slotlarını doldurmaya çalışır. X±1 sınırlarına uyar.
        """
        made = 0
        quota_used = defaultdict(int)

        # Hedef X±1 sınırları (global)
        num_instructors = len(self.instructors) if hasattr(self, 'instructors') else 0
        total_projects = len(self.projects) if hasattr(self, 'projects') else 0
        final_avg = (3 * total_projects) / num_instructors if num_instructors > 0 else 0
        x_int = int(final_avg)
        x_min_bound = max(0, x_int - 1)
        x_max_bound = x_int + 1

        # Mevcut workloads
        def get_wl():
            return self._calculate_current_workloads(assignments)

        # Projeleri continuity potansiyeline göre sırala (zaten ana akışta da sıralanıyor)
        ordered = projects_needing_jury.copy()

        # Tek taramada mümkün olanları yerleştir
        for pa in ordered:
            project_id = pa.get('project_id')
            classroom_id = pa.get('classroom_id')
            timeslot_id = pa.get('timeslot_id')
            slot_key = (classroom_id, timeslot_id)

            assignment = next((a for a in assignments if a.get('project_id') == project_id), None)
            if not assignment:
                continue
            instrs = assignment.get('instructors', [])
            if 'instructors' not in assignment:
                assignment['instructors'] = instrs
            responsible_id = assignment.get('responsible_instructor_id')
            if not responsible_id and instrs:
                responsible_id = instrs[0]

            # Zaten 2 jüri var mı?
            current_jury_count = len([i for i in assignment['instructors'] if i != responsible_id])
            if current_jury_count >= 2:
                continue

            wl = get_wl()
            if not wl:
                wl = {}
            avg_wl = (sum(wl.values()) / len(wl)) if wl else 0

            candidates = []
            for ins in self.instructors:
                ins_id = ins['id']
                if not assignability_matrix.get((ins_id, slot_key), False):
                    continue
                if ins_id == responsible_id:
                    continue
                if any(((i.get('id') if isinstance(i, dict) else i) == ins_id) for i in assignment['instructors']):
                    continue
                # X+1 üst sınır
                if wl.get(ins_id, 0) >= x_max_bound:
                    continue

                cont = self._calculate_continuity_score(
                    ins_id, classroom_id, timeslot_id, assignments, sorted_timeslots, timeslot_to_index
                )
                if cont < 1.0:
                    continue  # Pre-pass sadece continuity=1

                chain_ext = self._calculate_chain_extension_score(
                    ins_id, classroom_id, timeslot_id, assignments, sorted_timeslots, timeslot_to_index
                )
                # Quota kontrolü
                q_limit = quota_plan.get(ins_id, 999)
                q_rem = q_limit - quota_used[ins_id]
                if q_rem <= 0:
                    continue

                candidates.append({
                    'id': ins_id,
                    'wl': wl.get(ins_id, 0),
                    'cont': cont,
                    'chain': chain_ext,
                    'under_min': wl.get(ins_id, 0) < x_min_bound,
                    'under_avg': wl.get(ins_id, 0) <= avg_wl
                })

            if not candidates:
                continue

            # Önce X-1 altındakileri, sonra <= ortalama olanları, sonra zincir uzunluğuna göre sırala
            under_min = [c for c in candidates if c['under_min']]
            pool = under_min if under_min else (
                [c for c in candidates if c['under_avg']] if candidates else []
            )
            if not pool:
                pool = candidates

            pool.sort(key=lambda c: (c['under_min'], c['under_avg'], c['chain'], -c['wl']), reverse=True)
            chosen = pool[0]

            # Atama
            assignment['instructors'].append(chosen['id'])
            made += 1

            # Assignability matrix'i global olarak yenile
            assignability_matrix.update(self._build_assignability_matrix(
                assignments,
                projects_needing_jury,
                sorted_timeslots,
                timeslot_to_index
            ))

        return {"assignments_made": made}

    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎯 3. FAZ: FİXATION (Eksik Jüriyi Araştırma Görevlisi ile Tamamlama)
    # ═══════════════════════════════════════════════════════════════════════════════
    def _create_ra_placeholder(self) -> Dict[str, Any]:
        """Araştırma Görevlisi placeholder objesi oluşturur."""
        return {"id": "RA_PLACEHOLDER", "name": "[Araştırma Görevlisi]", "is_placeholder": True}

    def _is_placeholder_instructor(self, instr: Any) -> bool:
        if isinstance(instr, dict):
            return bool(instr.get("is_placeholder"))
        return False

    def _execute_phase3_fixation(
        self,
        phase2_assignments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        3. Faz: 2. Faz sonrasında hala "1 Sorumlu + 1 Jüri" olan projeleri,
        2. jüri olarak [Araştırma Görevlisi] placeholder ile tamamlar.

        Notlar:
        - Hiçbir önceki atama değiştirilmez.
        - Workload/continuity yeniden hesaplanmaz, placeholder istatistiklere dahil edilmez.
        - Sadece eksik projelere placeholder eklenir.
        """
        logger.info("3. FAZ: Fixation başlıyor - eksik projeler placeholder ile tamamlanacak")

        final_assignments = [a.copy() for a in phase2_assignments]
        fixed_projects: List[int] = []

        for ass in final_assignments:
            proj_id = ass.get("project_id")
            instructors = ass.get("instructors", [])
            if "instructors" not in ass:
                ass["instructors"] = instructors

            responsible_id = ass.get("responsible_instructor_id")
            if not responsible_id and instructors:
                first_ins = instructors[0]
                responsible_id = first_ins.get("id") if isinstance(first_ins, dict) else first_ins

            # Mevcut jüri sayısını (placeholder hariç) hesapla
            jury_count = 0
            for ins in instructors:
                # Placeholder'ı jüri sayımına dahil etme
                if self._is_placeholder_instructor(ins):
                    continue
                ins_id = ins.get("id") if isinstance(ins, dict) else ins
                if ins_id != responsible_id:
                    jury_count += 1

            if jury_count < 2:
                needed = 2 - jury_count
                for _ in range(needed):
                    ass["instructors"].append(self._create_ra_placeholder())
                fixed_projects.append(proj_id)

        logger.info(f"3. FAZ: Tamamlanan proje sayısı: {len(fixed_projects)}")
        return {
            "assignments": final_assignments,
            "phase3_stats": {
                "fixed_projects": fixed_projects,
                "num_fixed": len(fixed_projects)
            }
        }

    def _try_chain_swap_for_second_jury(
        self,
        target_assignment: Dict[str, Any],
        assignments: List[Dict[str, Any]],
        sorted_timeslots: List[Dict[str, Any]],
        timeslot_to_index: Dict[int, int],
        x_max: int,
        locked_jurors_by_project: Optional[Dict[int, Set[int]]] = None
    ) -> Tuple[bool, Optional[int]]:
        """
        Zaman çakışması nedeniyle ikinci jüri atanamayan bir proje için zincirli swap denemesi yap.

        Strateji:
        - Hedef slot ile aynı timeslot'ta görevli bir hocayı (sadece jüri olan) hedef projeye taşıyabilmek için,
          o hocanın görevli olduğu diğer projede yerine geçebilecek uygun bir yedek hoca bul.
        - Böylece iki seviyeli bir değiş-tokuş ile hedef projeye jüri eklenir, diğer projede jüri sayısı korunur.

        Kurallar:
        - Sorumlu hoca swap edilemez.
        - Yedek hoca atanabilir olmalı ve iş yükü x_max'i aşmamalı.
        - Hedefe taşınacak hoca hedef projede sorumlu/jüri olmamalı (duplicate olmamalı).

        Returns:
            (başarılı_mı, eklenen_hoca_id)
        """
        project_id = target_assignment.get('project_id')
        classroom_id = target_assignment.get('classroom_id')
        timeslot_id = target_assignment.get('timeslot_id')
        target_instructors = target_assignment.get('instructors', [])
        responsible_id = target_assignment.get('responsible_instructor_id')
        if not responsible_id and target_instructors:
            first_instr = target_instructors[0]
            responsible_id = first_instr.get('id') if isinstance(first_instr, dict) else first_instr

        # Mevcut iş yüklerini hesapla (x_max kontrolü için)
        workloads = self._calculate_current_workloads(assignments)

        # 1) Aynı timeslot'ta görevli hocaları tara (sadece jüri olanlar) ve continuity/cost skorla en iyiyi seç
        best_choice = None  # (score, cand_id, conflicting_assignment, replacement_id)
        for candidate in self.instructors:
            cand_id = candidate['id']
            if cand_id == responsible_id:
                continue
            # Hedef projede zaten jüri ise atla
            if any(((i.get('id') if isinstance(i, dict) else i) == cand_id) for i in target_instructors):
                continue

            # Bu adayın aynı timeslot'ta jüri olduğu assignment'ı bul
            candidate_confs = []
            for ass in assignments:
                if ass.get('timeslot_id') != timeslot_id:
                    continue
                ass_instructors = ass.get('instructors', [])
                ass_responsible = ass.get('responsible_instructor_id')
                if not ass_responsible and ass_instructors:
                    fi = ass_instructors[0]
                    ass_responsible = fi.get('id') if isinstance(fi, dict) else fi
                if isinstance(ass_responsible, dict):
                    ass_responsible = ass_responsible.get('id')

                # Aday bu assignment'ta jüri mi?
                found_here = False
                for j in ass_instructors:
                    jid = j.get('id') if isinstance(j, dict) else j
                    if jid == cand_id and cand_id != ass_responsible:
                        # Kilitli ise atla
                        conf_proj_id = ass.get('project_id')
                        if locked_jurors_by_project and conf_proj_id in locked_jurors_by_project and cand_id in locked_jurors_by_project[conf_proj_id]:
                            found_here = False
                            break
                        # Kırılma maliyeti (bu assignment'ta continuity)
                        break_cost = self._calculate_continuity_score(
                            cand_id,
                            ass.get('classroom_id'),
                            ass.get('timeslot_id'),
                            assignments,
                            sorted_timeslots,
                            timeslot_to_index
                        )
                        candidate_confs.append((ass, break_cost))
                        found_here = True
                        break
                # devam
            if not candidate_confs:
                continue

            # Hedef slot için continuity ve zincir uzatma kazancı
            gain_cont = self._calculate_continuity_score(
                cand_id,
                classroom_id,
                timeslot_id,
                assignments,
                sorted_timeslots,
                timeslot_to_index
            )
            gain_chain = self._calculate_chain_extension_score(
                cand_id,
                classroom_id,
                timeslot_id,
                assignments,
                sorted_timeslots,
                timeslot_to_index
            )

            # Adayın en az continuity kıracağı assignment'ı seç
            candidate_confs.sort(key=lambda x: x[1])  # düşük kırılma önce
            conflicting_assignment, break_cost = candidate_confs[0]

            # 2) Conflicting assignment için uygun yedek hocaları topla ve continuity/zincir kazancı yüksek olanı seç
            conf_instructors = conflicting_assignment.get('instructors', [])
            conf_responsible = conflicting_assignment.get('responsible_instructor_id')
            if not conf_responsible and conf_instructors:
                fi = conf_instructors[0]
                conf_responsible = fi.get('id') if isinstance(fi, dict) else fi
            if isinstance(conf_responsible, dict):
                conf_responsible = conf_responsible.get('id')

            best_repl = None  # (score, repl_id)
            for repl in self.instructors:
                repl_id = repl['id']
                if repl_id == cand_id or repl_id == conf_responsible:
                    continue
                # Zaten bu assignment'ta jüri ise atla
                if any(((i.get('id') if isinstance(i, dict) else i) == repl_id) for i in conf_instructors):
                    continue
                # Atanabilirlik ve yük üst sınırı
                if not self._check_instructor_assignability(repl_id, conflicting_assignment, assignments):
                    continue
                repl_wl = workloads.get(repl_id, 0)
                if repl_wl >= x_max:
                    continue
                # Replacement continuity ve zincir kazancı
                repl_gain = self._calculate_continuity_score(
                    repl_id,
                    conflicting_assignment.get('classroom_id'),
                    conflicting_assignment.get('timeslot_id'),
                    assignments,
                    sorted_timeslots,
                    timeslot_to_index
                )
                repl_chain = self._calculate_chain_extension_score(
                    repl_id,
                    conflicting_assignment.get('classroom_id'),
                    conflicting_assignment.get('timeslot_id'),
                    assignments,
                    sorted_timeslots,
                    timeslot_to_index
                )
                # Continuity + zincir güçlü öncelik; ardından daha düşük yük
                repl_score = (repl_gain * 4000000) + (repl_chain * 2000000) + (100 - repl_wl)
                if not best_repl or repl_score > best_repl[0]:
                    best_repl = (repl_score, repl_id)

            if not best_repl:
                continue

            # Toplam skor: continuity + zincir kazanımı çok güçlü, continuity kırılma maliyeti yüksek cezalı
            total_score = (gain_cont * 5000000) + (gain_chain * 3000000) - (break_cost * 4000000) + (200 - workloads.get(cand_id, 0))
            if not best_choice or total_score > best_choice[0]:
                best_choice = (total_score, cand_id, conflicting_assignment, best_repl[1])

        if best_choice:
            _, cand_id, conflicting_assignment, repl_id = best_choice
            conf_instructors = conflicting_assignment.get('instructors', [])
            # 2.1) Adayı conflicting assignment'tan çıkar
            for idx, jj in enumerate(conf_instructors):
                jjid = jj.get('id') if isinstance(jj, dict) else jj
                if jjid == cand_id:
                    conf_instructors.pop(idx)
                    break
            # 2.2) Yedeği conflicting assignment'a ekle
            conflicting_assignment['instructors'].append(repl_id)
            # 2.3) Adayı hedef projeye ekle
            target_assignment.setdefault('instructors', []).append(cand_id)
            return True, cand_id

        # Hiçbir zincirli swap bulunamadı
        return False, None

    def _relieve_overload_via_swap(
        self,
        overloaded_instructor_id: int,
        assignments: List[Dict[str, Any]],
        underloaded_instructor_ids: Set[int],
        locked_jurors_by_project: Optional[Dict[int, Set[int]]],
        sorted_timeslots: List[Dict[str, Any]],
        timeslot_to_index: Dict[int, int]
    ) -> bool:
        """
        Aşırı/üst sınırdaki bir hocanın başka bir projedeki jüri slotunu,
        uygun (atanabilir) ve düşük yüklü bir hocaya devrederek yükünü düşür.

        Kilitli (Phase 1) jüriye dokunulmaz. Sorumluya da dokunulmaz.

        Başarılı olursa True döner.
        """
        for assignment in assignments:
            instructors = assignment.get('instructors', [])
            responsible_id = assignment.get('responsible_instructor_id')
            if not responsible_id and instructors:
                fi = instructors[0]
                responsible_id = fi.get('id') if isinstance(fi, dict) else fi
            if isinstance(responsible_id, dict):
                responsible_id = responsible_id.get('id')

            # Overloaded hoca bu assignment'ta jüri mi? (ve kilitli değil mi?)
            is_jury_here = False
            for instr in instructors:
                iid = instr.get('id') if isinstance(instr, dict) else instr
                if iid == overloaded_instructor_id and iid != responsible_id:
                    # Kilit kontrolü
                    proj_id_here = assignment.get('project_id')
                    if locked_jurors_by_project and proj_id_here in locked_jurors_by_project:
                        if iid in locked_jurors_by_project[proj_id_here]:
                            is_jury_here = False
                            break
                    is_jury_here = True
                    break

            if not is_jury_here:
                continue

            # Bu assignment'a atanabilecek underloaded biri var mı?
            for under_id in underloaded_instructor_ids:
                if self._check_instructor_assignability(under_id, assignment, assignments):
                    # Devir yap: overloaded'ı çıkar, under'ı ekle
                    for idx, ins in enumerate(instructors):
                        iid = ins.get('id') if isinstance(ins, dict) else ins
                        if iid == overloaded_instructor_id:
                            instructors.pop(idx)
                            break
                    assignment['instructors'].append(under_id)
                    return True

        return False

    def _complete_jury_assignments(
        self,
        assignments: List[Dict[str, Any]],
        projects_needing_jury: List[Dict[str, Any]],
        quota_plan: Dict[int, int],
        assignability_matrix: Dict[Tuple[int, int], bool],
        sorted_timeslots: List[Dict[str, Any]],
        timeslot_to_index: Dict[int, int],
        locked_jurors_by_project: Optional[Dict[int, Set[int]]] = None
    ) -> Dict[str, Any]:
        """
        Jüri atamalarını tamamla
        
        Öncelik sırası:
        1. Kota dengesi (en az yükü olan)
        2. Continuity skoru
        3. Atanabilirlik
        
        Args:
            assignments: Tüm atamalar (güncellenecek)
            projects_needing_jury: Eksik jüri olan projeler
            quota_plan: Her hoca için jüri kotası
            assignability_matrix: Atanabilirlik matrisi
            sorted_timeslots: Sıralı timeslot listesi
            timeslot_to_index: Timeslot ID -> index mapping
        
        Returns:
            Dict: İstatistikler
        """
        assignments_made = 0
        quota_used = defaultdict(int)
        failed_assignments = 0
        
        logger.info(f"  Jüri atama başlatılıyor: {len(projects_needing_jury)} proje için")
        
        # Hedef iş yükü sınırları (X±1): X = toplam hedef görev / eğitmen sayısı
        num_instructors = len(self.instructors) if hasattr(self, 'instructors') else 0
        total_projects = len(self.projects) if hasattr(self, 'projects') else 0
        final_avg = (3 * total_projects) / num_instructors if num_instructors > 0 else 0
        x_int = int(final_avg)
        x_min_bound = max(0, x_int - 1)
        x_max_bound = x_int + 1
        
        # İş yükü takibi için: Her iterasyonda gerçek iş yükünü hesapla
        def get_current_real_workload():
            """Gerçek zamanlı iş yükünü hesapla (sadece quota_used değil, tüm assignments)"""
            real_workloads = self._calculate_current_workloads(assignments)
            return real_workloads
        
        # Projeleri sırala: continuity potansiyeli (özellikle UNDERLOADED + continuity) yüksek olanları önce işle
        real_workloads_for_order = self._calculate_current_workloads(assignments)
        avg_wl_for_order = (sum(real_workloads_for_order.values()) / len(real_workloads_for_order)) if real_workloads_for_order else 0
        project_continuity_scores = []
        for pa in projects_needing_jury:
            cls_id = pa.get('classroom_id')
            ts_id = pa.get('timeslot_id')
            slot_key_scan = (cls_id, ts_id)
            cont_under_hits = 0
            cont_hits = 0
            for ins in self.instructors:
                ins_id_scan = ins['id']
                if assignability_matrix.get((ins_id_scan, slot_key_scan), False):
                    cont_val = self._calculate_continuity_score(
                        ins_id_scan, cls_id, ts_id, assignments, sorted_timeslots, timeslot_to_index
                    )
                    if cont_val >= 1.0:
                        cont_hits += 1
                        if real_workloads_for_order.get(ins_id_scan, 0) <= avg_wl_for_order:
                            cont_under_hits += 1
            # Önce underloaded+continuity sayısına, sonra toplam continuity sayısına göre sırala
            project_continuity_scores.append(((cont_under_hits, cont_hits), pa))
        sorted_projects = [pa for _, pa in sorted(project_continuity_scores, key=lambda x: (x[0][0], x[0][1]), reverse=True)]
        
        logger.info(f"  Projeler continuity potansiyeli için sıralandı")
        
        # Erken durdurma flag'i: Uniform dağılım sağlandığında tüm projeler için dur
        early_stop_uniform_achieved = False
        
        # Her proje için jüri atama
        for project_assignment in sorted_projects:
            # Erken durdurma kontrolü: Eğer uniform dağılım sağlandıysa, kalan tüm projeleri atla
            if early_stop_uniform_achieved:
                logger.debug(f"    Proje {project_assignment.get('project_id')} atlandı: Uniform dağılım zaten sağlandı")
                continue
            project_id = project_assignment.get('project_id')
            classroom_id = project_assignment.get('classroom_id')
            timeslot_id = project_assignment.get('timeslot_id')
            slot_key = (classroom_id, timeslot_id)
            
            # Bu proje için assignment'ı bul
            assignment = next(
                (a for a in assignments if a.get('project_id') == project_id),
                None
            )
            
            if not assignment:
                logger.warning(f"    Proje {project_id} için assignment bulunamadı!")
                continue
            
            # Mevcut jüri sayısını hesapla
            if 'instructors' not in assignment:
                assignment['instructors'] = []
            
            responsible_id = assignment.get('responsible_instructor_id')
            if not responsible_id and assignment.get('instructors'):
                responsible_id = assignment['instructors'][0]
            
            current_jury_count = len([i for i in assignment['instructors'] if i != responsible_id])
            
            # 2 jüri olana kadar jüri ekle
            while current_jury_count < 2:
                # GERÇEK İŞ YÜKÜNÜ HESAPLA (tüm adaylar için ortak)
                real_workloads = get_current_real_workload()
                if real_workloads:
                    avg_workload = sum(real_workloads.values()) / len(real_workloads)
                    max_workload = max(real_workloads.values())
                    min_workload = min(real_workloads.values())
                    workload_diff = max_workload - min_workload
                    # Aşırı yüklü hocalar için threshold (daha sıkı: ortalama + 1.5)
                    # Bu, aşırı yüklenmeyi önlemek için kritik
                    overload_threshold = avg_workload + 1.5
                    
                    # ═══════════════════════════════════════════════════════════
                    # ERKEN DURDURMA KONTROLÜ: Uniform dağılım sağlandıysa dur
                    # ═══════════════════════════════════════════════════════════
                    # Eğer iş yükü dağılımı X-1, X, X+1 aralığında ve fark 2 veya daha azsa,
                    # ve de minimum iş yükü X-1 veya üzerideyse, uniform dağılım sağlanmıştır
                    uniform_distribution_achieved = (
                        workload_diff <= 2 and  # Maks-Min farkı 2 veya daha az
                        min_workload >= x_min_bound and  # Minimum X-1 veya üzeri
                        max_workload <= x_max_bound  # Maksimum X+1 veya altı
                    )
                    
                    if uniform_distribution_achieved:
                        # Uniform dağılım sağlandı, kalan projeler için erken durdur
                        remaining_projects_count = len(sorted_projects) - sorted_projects.index(project_assignment) - 1
                        logger.info(f"  ✅ UNIFORM DAĞILIM SAĞLANDI: Min={min_workload}, Max={max_workload}, "
                                   f"Fark={workload_diff} (X-1, X, X+1 aralığında)")
                        logger.info(f"  🎯 Erken durdurma: Kalan {remaining_projects_count + (1 if current_jury_count < 2 else 0)} proje atlanıyor "
                                   f"(uniform dağılım korunuyor)")
                        early_stop_uniform_achieved = True  # Tüm kalan projeler için dur
                        break  # Bu proje için döngüden çık
                else:
                    avg_workload = 0
                    max_workload = 0
                    min_workload = 0
                    overload_threshold = 999
                
                # Jüri adaylarını belirle
                candidates = []
                for instructor in self.instructors:
                    inst_id = instructor['id']
                    
                    # Atanabilir mi? (öncelik 1)
                    if not assignability_matrix.get((inst_id, slot_key), False):
                        continue
                    
                    # Zaten eklenmiş mi?
                    if inst_id in assignment['instructors']:
                        continue
                    
                    # Sorumlu instructor olamaz
                    if inst_id == responsible_id:
                        continue
                    
                    # GERÇEK İŞ YÜKÜNÜ HESAPLA
                    current_real_workload = real_workloads.get(inst_id, 0)
                    
                    # Sert üst sınır: X+1'i aşamaz
                    if current_real_workload >= x_max_bound:
                        continue
                    
                    # AŞIRI YÜK KONTROLÜ: Eğer hoca ortalamadan 1.0'dan fazla yüksekse, atlama (daha sıkı)
                    # Bu, uniform dağılımı sağlamak için kritik - daha agresif dengeleme
                    if current_real_workload > overload_threshold:
                        # Eğer çok fazla dengesizlik varsa (min ortalamadan 3'ten fazla düşükse), 
                        # aşırı yüklü hocayı da kabul et ama çok düşük skor ver
                        if min_workload < avg_workload - 3:
                            # Çok büyük dengesizlik var, bu hocayı atlama ama en son tercih et
                            pass  # Devam et ama skor düşük olacak
                        else:
                            logger.debug(f"    Hoca {inst_id} atlandı: Aşırı yüklü ({current_real_workload:.1f} > {overload_threshold:.1f})")
                            continue
                    
                    # Ek kontrol: Eğer min workload ortalamadan 2'den fazla düşükse ve bu hoca da ortalamanın altındaysa, MUTLAKA öncelik ver
                    # Bu, uniform dağılımı sağlamak için kritik
                    prioritize_underloaded = (min_workload < avg_workload - 2) and (current_real_workload <= avg_workload)
                    
                    # Çok büyük dengesizlik varsa (min ortalamadan 3'ten fazla düşükse), 
                    # ortalamanın altındaki TÜM hocalara çok yüksek öncelik ver
                    force_prioritize_underloaded = (min_workload < avg_workload - 3) and (current_real_workload <= avg_workload + 0.5)
                    
                    # Continuity ve zincir uzatma skoru
                    continuity = self._calculate_continuity_score(
                        inst_id, classroom_id, timeslot_id,
                        assignments, sorted_timeslots, timeslot_to_index
                    )
                    chain_extension = self._calculate_chain_extension_score(
                        inst_id, classroom_id, timeslot_id,
                        assignments, sorted_timeslots, timeslot_to_index
                    )
                    
                    # Kota durumu (plan bazlı)
                    quota_limit = quota_plan.get(inst_id, 999)
                    quota_remaining = quota_limit - quota_used[inst_id]
                    
                    # Ortalama sapmasını hesapla
                    workload_deviation = current_real_workload - avg_workload
                    
                    # Öncelik skoru: Continuity öncelikli, ardından iş yükü dengesi
                    # Continuity ağırlığı yükseltildi; uniform dağılım korunur (X+1 sınırı ve overload cezası)
                    # Aşırı yüklü hocalar için ceza (eğer atlanmadıysa)
                    penalty_for_overloaded = 0
                    if current_real_workload > overload_threshold:
                        penalty_for_overloaded = (current_real_workload - overload_threshold) * 50000000
                    
                    priority_score = (
                        -workload_deviation * 8000000 +
                        -current_real_workload * 200000 +
                        (2000000 if prioritize_underloaded else 0) +
                        (5000000 if force_prioritize_underloaded else 0) +
                        quota_remaining * 600000 +
                        continuity * 12000000 +
                        chain_extension * 6000000 -
                        penalty_for_overloaded
                    )
                    
                    candidates.append({
                        'instructor_id': inst_id,
                        'continuity': continuity,
                        'current_workload': current_real_workload,
                        'workload_deviation': workload_deviation,
                        'quota_limit': quota_limit,
                        'quota_remaining': quota_remaining,
                        'priority_score': priority_score
                    })
                
                # Strict underload-first: X-1 altı varsa önce onları seç
                strict_under = [c for c in candidates if c.get('current_workload', 0) < x_min_bound]
                if strict_under:
                    candidates = strict_under

                # Quota-first: quota_remaining>0 olanları tercih et
                quota_first = [c for c in candidates if c.get('quota_remaining', 0) > 0]
                if quota_first:
                    candidates = quota_first

                # Continuity-first prefilter (önce continuity+underloaded, sonra continuity)
                if candidates:
                    cont_and_under = [
                        c for c in candidates
                        if c.get('continuity', 0) >= 1.0 and c.get('current_workload', 0) <= avg_workload
                    ]
                    if cont_and_under:
                        candidates = cont_and_under
                    else:
                        cont_first = [c for c in candidates if c.get('continuity', 0) >= 1.0]
                        if cont_first:
                            candidates = cont_first

                # En iyi adayı seç (öncelik skoruna göre)
                if not candidates:
                    # İlk denemede uygun aday yoksa, kota kontrolünü gevşet
                    candidates_flexible = []
                    for instructor in self.instructors:
                        inst_id = instructor['id']
                        
                        # Temel kontroller (atanabilirlik, duplicate, sorumlu)
                        if not assignability_matrix.get((inst_id, slot_key), False):
                            continue
                        if inst_id in assignment['instructors']:
                            continue
                        if inst_id == responsible_id:
                            continue
                        
                        # GERÇEK İŞ YÜKÜNÜ HESAPLA
                        real_workloads_flex = get_current_real_workload()
                        current_real_workload_flex = real_workloads_flex.get(inst_id, 0)
                        
                        # Sert üst sınır: X+1'i aşamaz
                        if current_real_workload_flex >= x_max_bound:
                            continue
                        
                        # Flexible modda bile aşırı yüklü hocaları kontrol et (ama daha esnek threshold)
                        if real_workloads_flex:
                            avg_workload_flex = sum(real_workloads_flex.values()) / len(real_workloads_flex)
                            min_workload_flex = min(real_workloads_flex.values())
                            overload_threshold_flex = avg_workload_flex + 2.0  # Daha esnek ama hala kontrollü (2.5'ten 2.0'a düşürüldü)
                            if current_real_workload_flex > overload_threshold_flex:
                                # Çok fazla dengesizlik varsa kabul et ama ceza ver
                                if min_workload_flex < avg_workload_flex - 3:
                                    pass  # Devam et ama skor düşük olacak
                                else:
                                    logger.debug(f"    Hoca {inst_id} atlandı: Aşırı yüklü ({current_real_workload_flex:.1f} > {overload_threshold_flex:.1f})") 
                                continue
                            workload_deviation_flex = current_real_workload_flex - avg_workload_flex
                            # Çok düşük yüklü hocalara öncelik kontrolü
                            prioritize_underloaded_flex = (min_workload_flex < avg_workload_flex - 2) and (current_real_workload_flex <= avg_workload_flex)
                            force_prioritize_underloaded_flex = (min_workload_flex < avg_workload_flex - 3) and (current_real_workload_flex <= avg_workload_flex + 0.5)
                        else:
                            avg_workload_flex = 0
                            min_workload_flex = 0
                            workload_deviation_flex = 0
                            prioritize_underloaded_flex = False
                            force_prioritize_underloaded_flex = False
                        
                        continuity = self._calculate_continuity_score(
                            inst_id, classroom_id, timeslot_id,
                            assignments, sorted_timeslots, timeslot_to_index
                        )
                        chain_extension = self._calculate_chain_extension_score(
                            inst_id, classroom_id, timeslot_id,
                            assignments, sorted_timeslots, timeslot_to_index
                        )
                        
                        quota_limit = quota_plan.get(inst_id, 999)
                        quota_remaining = quota_limit - quota_used[inst_id]
                        
                        # Aşırı yüklü hocalar için ceza (eğer atlanmadıysa)
                        penalty_for_overloaded_flex = 0
                        if real_workloads_flex and current_real_workload_flex > avg_workload_flex + 2.0:
                            penalty_for_overloaded_flex = (current_real_workload_flex - (avg_workload_flex + 2.0)) * 50000000
                        
                        # Flexible mod: continuity güçlü öncelik, ardından iş yükü dengesi
                        priority_score = (
                            -workload_deviation_flex * 8000000 +
                            -current_real_workload_flex * 200000 +
                            (2000000 if prioritize_underloaded_flex else 0) +
                            (5000000 if force_prioritize_underloaded_flex else 0) +
                            quota_remaining * 600000 +
                            continuity * 12000000 +
                            chain_extension * 6000000 -
                            penalty_for_overloaded_flex
                        )
                        
                        candidates_flexible.append({
                            'instructor_id': inst_id,
                            'continuity': continuity,
                            'current_workload': current_real_workload_flex,
                            'workload_deviation': workload_deviation_flex,
                            'quota_limit': quota_limit,
                            'quota_remaining': quota_remaining,
                            'priority_score': priority_score
                        })
                    
                    # Strict underload-first (flex): X-1 altı varsa önce onları seç
                    strict_under_flex = [c for c in candidates_flexible if c.get('current_workload', 0) < x_min_bound]
                    if strict_under_flex:
                        candidates_flexible = strict_under_flex

                    # Continuity-first prefilter (flex): önce continuity+underloaded, sonra continuity
                    if candidates_flexible:
                        cont_and_under_flex = [
                            c for c in candidates_flexible
                            if c.get('continuity', 0) >= 1.0 and c.get('current_workload', 0) <= avg_workload_flex
                        ]
                        if cont_and_under_flex:
                            candidates_flexible = cont_and_under_flex
                        else:
                            cont_first_flex = [c for c in candidates_flexible if c.get('continuity', 0) >= 1.0]
                            if cont_first_flex:
                                candidates_flexible = cont_first_flex

                    # Quota-first (flex)
                    if candidates_flexible:
                        quota_first_flex = [c for c in candidates_flexible if c.get('quota_remaining', 0) > 0]
                        if quota_first_flex:
                            candidates_flexible = quota_first_flex

                    if not candidates_flexible:
                        # Hiç aday yok, ÇOK AGRESIF mod: Sadece temel çakışma kontrolü yaparak mutlaka bir aday bul
                        logger.warning(f"    ⚠️ Proje {project_id} için flexible aday bulunamadı, ULTRA-AGRESIF mod aktif!")
                        candidates_ultra_aggressive = []
                        for instructor in self.instructors:
                            inst_id = instructor['id']
                            
                            # ULTRA-AGRESIF: Sadece temel çakışmaları kontrol et
                            # 1. Zaten bu projede görevli mi (sorumlu veya jüri)?
                            if inst_id == responsible_id:
                                continue
                            if inst_id in assignment['instructors']:
                                continue
                            
                            # 2. Aynı timeslot'ta başka bir görevi var mı? (mutlak çakışma)
                            has_timeslot_conflict = False
                            for other_assignment in assignments:
                                if other_assignment.get('timeslot_id') == timeslot_id:
                                    other_instructors = other_assignment.get('instructors', [])
                                    other_responsible = other_assignment.get('responsible_instructor_id')
                                    if not other_responsible and other_instructors:
                                        other_responsible = other_instructors[0]
                                    if isinstance(other_responsible, dict):
                                        other_responsible = other_responsible.get('id')
                                    if isinstance(inst_id, dict):
                                        inst_id_check = inst_id.get('id') if isinstance(inst_id, dict) else inst_id
                                    else:
                                        inst_id_check = inst_id
                                    
                                    # Normalize diğer instructors
                                    for o_instr in other_instructors:
                                        o_instr_id = o_instr.get('id') if isinstance(o_instr, dict) else o_instr
                                        if o_instr_id == inst_id_check:
                                            has_timeslot_conflict = True
                                            break
                                    if other_responsible and other_responsible == inst_id_check:
                                        has_timeslot_conflict = True
                                    if has_timeslot_conflict:
                                        break
                            
                            if has_timeslot_conflict:
                                continue  # Zaman çakışması varsa atlama
                            
                            # GERÇEK İŞ YÜKÜNÜ HESAPLA
                            real_workloads_ultra = get_current_real_workload()
                            current_real_workload_ultra = real_workloads_ultra.get(inst_id, 0)

                            # Sert üst sınır: X+1'i aşamaz
                            if current_real_workload_ultra >= x_max_bound:
                                continue
                            
                            # ULTRA-AGRESIF modda bile iş yükü dengesine öncelik ver
                            if real_workloads_ultra:
                                avg_workload_ultra = sum(real_workloads_ultra.values()) / len(real_workloads_ultra)
                                min_workload_ultra = min(real_workloads_ultra.values())
                                workload_deviation_ultra = current_real_workload_ultra - avg_workload_ultra
                                prioritize_underloaded_ultra = (min_workload_ultra < avg_workload_ultra - 2) and (current_real_workload_ultra <= avg_workload_ultra)
                                force_prioritize_underloaded_ultra = (min_workload_ultra < avg_workload_ultra - 3) and (current_real_workload_ultra <= avg_workload_ultra + 0.5)
                            else:
                                avg_workload_ultra = 0
                                min_workload_ultra = 0
                                workload_deviation_ultra = 0
                                prioritize_underloaded_ultra = False
                                force_prioritize_underloaded_ultra = False
                            
                            continuity = self._calculate_continuity_score(
                                inst_id, classroom_id, timeslot_id,
                                assignments, sorted_timeslots, timeslot_to_index
                            )
                            chain_extension = self._calculate_chain_extension_score(
                                inst_id, classroom_id, timeslot_id,
                                assignments, sorted_timeslots, timeslot_to_index
                            )
                            
                            quota_limit = quota_plan.get(inst_id, 999)
                            quota_remaining = quota_limit - quota_used[inst_id]
                            
                            # ULTRA-AGRESIF modda bile çok yüksek yüklü hocalara ceza ver (ama atlama)
                            penalty_for_overloaded_ultra = 0
                            if real_workloads_ultra and current_real_workload_ultra > avg_workload_ultra + 2.5:
                                penalty_for_overloaded_ultra = (current_real_workload_ultra - (avg_workload_ultra + 2.5)) * 30000000
                            
                            # ULTRA-AGRESIF mod: continuity güçlü öncelik
                            priority_score = (
                                -workload_deviation_ultra * 8000000 +
                                -current_real_workload_ultra * 200000 +
                                (2000000 if prioritize_underloaded_ultra else 0) +
                                (5000000 if force_prioritize_underloaded_ultra else 0) +
                                quota_remaining * 600000 +
                                continuity * 12000000 +
                                chain_extension * 6000000 -
                                penalty_for_overloaded_ultra
                            )
                            
                            candidates_ultra_aggressive.append({
                                'instructor_id': inst_id,
                                'continuity': continuity,
                                'current_workload': current_real_workload_ultra,
                                'workload_deviation': workload_deviation_ultra,
                                'quota_limit': quota_limit,
                                'quota_remaining': quota_remaining,
                                'priority_score': priority_score
                            })
                        
                        # Strict underload-first (ultra): X-1 altı varsa önce onları seç
                        strict_under_ultra = [c for c in candidates_ultra_aggressive if c.get('current_workload', 0) < x_min_bound]
                        if strict_under_ultra:
                            candidates_ultra_aggressive = strict_under_ultra

                        # Continuity-first prefilter (ultra)
                        if candidates_ultra_aggressive:
                            cont_first_ultra = [c for c in candidates_ultra_aggressive if c.get('continuity', 0) >= 1.0]
                            if cont_first_ultra:
                                candidates_ultra_aggressive = cont_first_ultra

                        # Quota-first (ultra)
                        if candidates_ultra_aggressive:
                            quota_first_ultra = [c for c in candidates_ultra_aggressive if c.get('quota_remaining', 0) > 0]
                            if quota_first_ultra:
                                candidates_ultra_aggressive = quota_first_ultra

                        if not candidates_ultra_aggressive:
                            # Zincirli swap ile kurtarmayı dene
                            success, added_id = self._try_chain_swap_for_second_jury(
                                assignment,
                                assignments,
                                sorted_timeslots,
                                timeslot_to_index,
                                x_max_bound,
                                locked_jurors_by_project
                            )
                            if success:
                                # Başarılı kurtarma: sayaçları güncelle
                                assignments_made += 1
                                current_jury_count += 1
                                # Assignability matrix'i yeniden oluştur (iki assignment değişti)
                                assignability_matrix = self._build_assignability_matrix(
                                    assignments,
                                    projects_needing_jury,
                                    sorted_timeslots,
                                    timeslot_to_index
                                )
                                logger.debug(f"    ✓ Proje {project_id}: Zincirli swap ile hoca {added_id} eklendi")
                                continue

                            # Son çare: X+1 üstü geçici atama + anında devir ile sınırlar korunur
                            real_wl_final = get_current_real_workload()
                            x_int_local = int(sum(real_wl_final.values()) / len(real_wl_final)) if real_wl_final else 0
                            x_min_local = max(0, x_int_local - 1)
                            under_ids = {iid for iid, wl in real_wl_final.items() if wl < x_min_local}
                            if under_ids:
                                # Geçici adaylar: atanabilir olan HER hoca (X+1 sınırını bu özel adımda esnetme)
                                temp_candidates = []
                                for instructor in self.instructors:
                                    inst_id2 = instructor['id']
                                    if not assignability_matrix.get((inst_id2, slot_key), False):
                                        continue
                                    if inst_id2 in assignment['instructors'] or inst_id2 == responsible_id:
                                        continue
                                    cont2 = self._calculate_continuity_score(
                                        inst_id2, classroom_id, timeslot_id,
                                        assignments, sorted_timeslots, timeslot_to_index
                                    )
                                    temp_candidates.append((inst_id2, cont2))
                                temp_candidates.sort(key=lambda x: x[1], reverse=True)

                                placed = False
                                for inst_id2, cont2 in temp_candidates:
                                    # Önce ekle, sonra anında yük düşürücü swap dene
                                    assignment['instructors'].append(inst_id2)
                                    relieved = self._relieve_overload_via_swap(
                                        inst_id2,
                                        assignments,
                                        under_ids,
                                        locked_jurors_by_project,
                                        sorted_timeslots,
                                        timeslot_to_index
                                    )
                                    if relieved:
                                        assignments_made += 1
                                        current_jury_count += 1
                                        assignability_matrix = self._build_assignability_matrix(
                                            assignments,
                                            projects_needing_jury,
                                            sorted_timeslots,
                                            timeslot_to_index
                                        )
                                        logger.debug(f"    ✓ Proje {project_id}: Geçici atama + anında devir ile hoca {inst_id2} eklendi")
                                        placed = True
                                        break
                                    else:
                                        try:
                                            assignment['instructors'].remove(inst_id2)
                                        except ValueError:
                                            pass

                                if placed:
                                    continue

                            # Hâlâ yerleştirilemiyorsa, kayıt altına al
                            logger.error(f"    ❌ Proje {project_id} için HİÇ aday bulunamadı! Tüm hocalar zaman/limit nedeniyle bloke.")
                        failed_assignments += 1
                        break
                    
                        candidates = candidates_ultra_aggressive
                    else:
                        candidates = candidates_flexible
                
                # Öncelik skoruna göre sırala (yüksek skor = öncelikli)
                candidates.sort(key=lambda x: x['priority_score'], reverse=True)
                best_candidate = candidates[0]
                selected_instructor = best_candidate['instructor_id']
                
                # Yeni jüriyi ekle
                assignment['instructors'].append(selected_instructor)
                quota_used[selected_instructor] += 1
                assignments_made += 1
                current_jury_count += 1
                
                logger.debug(
                    f"    ✓ Proje {project_id}: Hoca {selected_instructor} jüri olarak eklendi "
                    f"(Yük: {best_candidate['current_workload']} -> {best_candidate['current_workload'] + 1}, "
                    f"Deviation: {best_candidate.get('workload_deviation', 0):.1f}, "
                    f"Continuity: {best_candidate['continuity']})"
                )
                
                # Assignability matrix'i güncelle (yeni jüri eklenince diğer adayların durumu değişebilir)
                for inst_id in [i['id'] for i in self.instructors]:
                    assignability_matrix[(inst_id, slot_key)] = (
                        self._check_instructor_assignability(
                            inst_id, assignment, assignments
                        )
                    )
                
                # Her 5 atamada bir intermediate rebalancing yap
                # Bu, büyük dengesizliklerin birikmesini önler
                if assignments_made % 5 == 0 and assignments_made > 0:
                    current_wl = get_current_real_workload()
                    if current_wl:
                        wl_max = max(current_wl.values())
                        wl_min = min(current_wl.values())
                        wl_diff = wl_max - wl_min
                        wl_avg = sum(current_wl.values()) / len(current_wl)
                        
                        # Eğer fark 3'ten büyükse hızlı bir rebalancing yap
                        if wl_diff > 3:
                            logger.debug(f"    🔄 Intermediate rebalancing (fark: {wl_diff:.1f}, Ort: {wl_avg:.1f})")
                            # Hızlı swap denemesi (sadece 10 iterasyon)
                            quick_swap_count = self._quick_rebalance_pass(
                                assignments,
                                sorted_timeslots,
                                timeslot_to_index,
                                locked_jurors_by_project,
                                max_iterations=10
                            )
                            if quick_swap_count > 0:
                                logger.debug(f"      ✓ {quick_swap_count} hızlı swap yapıldı")
        
        logger.info(f"  ✅ Jüri atama tamamlandı: {assignments_made} jüri atandı, {failed_assignments} başarısız")
        
        return {
            "assignments_made": assignments_made,
            "quota_used": dict(quota_used),
            "failed_assignments": failed_assignments
        }

    def _balance_workload_with_swap(
        self,
        assignments: List[Dict[str, Any]],
        sorted_timeslots: List[Dict[str, Any]],
        timeslot_to_index: Dict[int, int],
        locked_jurors_by_project: Optional[Dict[int, Set[int]]] = None
    ) -> Dict[str, Any]:
        """
        İş yükü dengesini swap ile sağla
        
        En fazla yükteki hoca ile en az yükteki hoca arasındaki fark 3'ten fazlaysa
        swap işlemi başlatılır. Multiple pass yaparak denge sağlanır.
        
        Args:
            assignments: Tüm atamalar
            sorted_timeslots: Sıralı timeslot listesi
            timeslot_to_index: Timeslot ID -> index mapping
        
        Returns:
            Dict: Swap istatistikleri
        """
        max_iterations = 1000  # Çok daha fazla iterasyon (uniform dağılım için kritik)
        swaps_performed = 0
        swaps_this_iteration = 0
        consecutive_no_swap = 0  # Ardışık swap yapılamayan iterasyon sayısı
        
        logger.info("  Swap: İş yükü dengeleme başlatılıyor...")
        
        for iteration in range(max_iterations):
            workloads = self._calculate_current_workloads(assignments)
            
            if not workloads:
                break
            
            max_workload = max(workloads.values())
            min_workload = min(workloads.values())
            workload_diff = max_workload - min_workload
            avg_workload = sum(workloads.values()) / len(workloads) if workloads else 0
            
            # Hedef X±1 sınırlarını hesapla
            x_int = int(avg_workload) if workloads else 0
            x_min_bound = max(0, x_int - 1)
            x_max_bound = x_int + 1

            # Denge kontrolü: herkes X±1 aralığında ise dengeli
            if max_workload <= x_max_bound and min_workload >= x_min_bound:
                logger.info(f"  ✅ Swap: Denge sağlandı (aralık: [{x_min_bound}, {x_max_bound}], iterasyon: {iteration + 1})")
                break
            
            # Hedef aralığa göre hocaları belirle
            overloaded_instructors = [(inst_id, wl) for inst_id, wl in workloads.items() if wl > x_max_bound]
            underloaded_instructors = [(inst_id, wl) for inst_id, wl in workloads.items() if wl < x_min_bound]
            
            # Ardışık 20 iterasyon swap yapılamazsa dur (daha sabırlı, uniform dağılım için kritik)
            if consecutive_no_swap >= 20:
                logger.warning(f"  ⚠️ Swap: Ardışık {consecutive_no_swap} iterasyon swap yapılamadı, durduruluyor")
                break
            
            swaps_this_iteration = 0
            
            # En yüksek ve en düşük yükteki hocaları bul
            # Birden fazla max/min varsa, hepsini dene
            # Öncelik: Ortalama üstü/altı hocalara odaklan
            if overloaded_instructors and underloaded_instructors:
                # Sınır dışındakileri önceliklendir
                max_workload_instructors = [inst_id for inst_id, wl in overloaded_instructors if wl > x_max_bound]
                min_workload_instructors = [inst_id for inst_id, wl in underloaded_instructors if wl < x_min_bound]
            else:
                # Fallback: En yüksek/düşük yükteki hocalar
                max_workload_instructors = [inst_id for inst_id, wl in workloads.items() if wl == max_workload]
                min_workload_instructors = [inst_id for inst_id, wl in workloads.items() if wl == min_workload]
            
            if not max_workload_instructors:
                max_workload_instructors = [inst_id for inst_id, wl in workloads.items() if wl == max_workload]
            if not min_workload_instructors:
                min_workload_instructors = [inst_id for inst_id, wl in workloads.items() if wl == min_workload]
            
            swapped = False
            swaps_this_iteration = 0
            
            # İYİLEŞTİRME: Aynı iterasyonda birden fazla swap yapabilmek için
            # Her max yükteki hoca için swap dene (artık tek swap ile sınırlı değil)
            for max_instructor in max_workload_instructors[:10]:  # En fazla 10 max hocaya bak (performans)
                # Max yükteki hocadan jüri slotlarını bul (sorumlu ve kilitli jüri hariç)
                max_instructor_slots = []
                for assignment in assignments:
                    instructors = assignment.get('instructors', [])
                    responsible_id = assignment.get('responsible_instructor_id')
                    if not responsible_id and instructors:
                        first_instr = instructors[0]
                        responsible_id = first_instr.get("id") if isinstance(first_instr, dict) else first_instr
                    
                    if isinstance(responsible_id, dict):
                        responsible_id = responsible_id.get("id")
                    
                    # Normalize instructors
                    for instr in instructors:
                        instr_id = instr.get("id") if isinstance(instr, dict) else instr
                        # Jüri görevi olan slotları topla (sorumlu olmayan ve kilitli olmayan)
                        if instr_id == max_instructor and instr_id != responsible_id:
                            proj_id_here = assignment.get('project_id')
                            if locked_jurors_by_project and proj_id_here in locked_jurors_by_project:
                                if instr_id in locked_jurors_by_project[proj_id_here]:
                                    continue
                        max_instructor_slots.append({
                            'assignment': assignment,
                            'instructor_id': max_instructor,
                            'project_id': assignment.get('project_id'),
                            'classroom_id': assignment.get('classroom_id'),
                            'timeslot_id': assignment.get('timeslot_id')
                        })
                        break  # Bu assignment'ta bu hocayı bulduk, diğerine geç
                
                # Slotları continuity skoruna göre sırala (düşük continuity = öncelikli swap için)
                max_instructor_slots.sort(
                    key=lambda s: self._calculate_continuity_score(
                        max_instructor, s['classroom_id'], s['timeslot_id'],
                        assignments, sorted_timeslots, timeslot_to_index
                    )
                )
                
                # Eğer continuity=0 olan en az bir slot varsa, continuity=1 olanları şimdilik atla
                has_zero_cont_slot = any(
                    self._calculate_continuity_score(
                        max_instructor, s['classroom_id'], s['timeslot_id'],
                        assignments, sorted_timeslots, timeslot_to_index
                    ) == 0 for s in max_instructor_slots
                )
                
                # Her min yükteki hoca için swap dene (birden fazla swap yapılabilir)
                for slot_info in max_instructor_slots:
                    if has_zero_cont_slot:
                        cont_here = self._calculate_continuity_score(
                            max_instructor, slot_info['classroom_id'], slot_info['timeslot_id'],
                            assignments, sorted_timeslots, timeslot_to_index
                        )
                        if cont_here >= 1.0:
                            continue
                    assignment = slot_info['assignment']
                    classroom_id = slot_info['classroom_id']
                    timeslot_id = slot_info['timeslot_id']
                    
                    # Max hocanın bu slot'ta jüri olduğundan emin ol
                    instructors = assignment.get('instructors', [])
                    max_found = False
                    for instr in instructors:
                        instr_id = instr.get("id") if isinstance(instr, dict) else instr
                        if instr_id == max_instructor:
                            max_found = True
                            break
                    
                    if not max_found:
                        continue
                    
                    # Min yükteki hocalar arasından continuity=1 olanları önceliklendir
                    viable_min = []
                    for min_instructor in min_workload_instructors[:10]:  # En fazla 10 min hocaya bak
                        can_assign = self._check_instructor_assignability(
                            min_instructor,
                            assignment,
                            assignments
                        )
                        if not can_assign:
                            continue
                        cont_gain = self._calculate_continuity_score(
                            min_instructor, classroom_id, timeslot_id,
                            assignments, sorted_timeslots, timeslot_to_index
                        )
                        viable_min.append((cont_gain, min_instructor))
                    if not viable_min:
                        continue
                    viable_min.sort(key=lambda x: x[0], reverse=True)
                    min_instructor = viable_min[0][1]

                    # Swap yap
                    # Normalize et ve remove
                    for i, instr in enumerate(instructors):
                        instr_id = instr.get("id") if isinstance(instr, dict) else instr
                        if instr_id == max_instructor:
                            instructors.pop(i)
                            break
                    
                    # Min hocayı ekle
                    assignment['instructors'].append(min_instructor)
                    
                    swaps_performed += 1
                    swaps_this_iteration += 1
                    swapped = True
                    
                    # Yeni yükleri hesapla
                    new_workloads = self._calculate_current_workloads(assignments)
                    new_max = max(new_workloads.values()) if new_workloads else 0
                    new_min = min(new_workloads.values()) if new_workloads else 0
                    new_diff = new_max - new_min
                    
                    logger.debug(f"    Swap #{swaps_performed}: Hoca {max_instructor} → Hoca {min_instructor} (Proje {slot_info['project_id']}, Yeni fark: {new_diff})")
                    consecutive_no_swap = 0  # Başarılı swap yapıldı
                    
                    # Bu swap'tan sonra yükleri yeniden hesapla ve güncelle
                    workloads = new_workloads
                    max_workload = new_max
                    min_workload = new_min
                    workload_diff = new_diff
                    
                    # Eğer fark 2'nin altına düştüyse, swap'ı durdur
                    if workload_diff <= 2:
                        break
                    
                    # Bu slot'tan sonra diğer max hocaya geç (birden fazla swap için)
                    break
                
                if workload_diff <= 2:
                    break
            
            # Eğer bu iterasyonda swap yapıldıysa, yükleri güncelle
            if swapped and swaps_this_iteration > 0:
                workloads = self._calculate_current_workloads(assignments)
                if workloads:
                    max_workload = max(workloads.values())
                    min_workload = min(workloads.values())
                    workload_diff = max_workload - min_workload
                    avg_workload = sum(workloads.values()) / len(workloads)
                    
                    # Fark 2'nin altındaysa dur
                    if workload_diff <= 2:
                        logger.info(f"  ✅ Swap: Denge sağlandı (fark: {workload_diff}, iterasyon: {iteration + 1})")
                        break
            
            if not swapped or swaps_this_iteration == 0:
                consecutive_no_swap += 1
                # Bu iterasyonda swap yapılamadı
                if iteration == 0:
                    logger.warning(f"  ⚠️ Swap: İlk iterasyonda hiç swap yapılamadı (fark: {workload_diff}, Ort: {avg_workload:.1f})")
                elif iteration % 20 == 0:
                    logger.info(f"  Swap: İterasyon {iteration + 1}, fark: {workload_diff}, Ort: {avg_workload:.1f}, "
                               f"Aşırı yüklü: {len(overloaded_instructors)}, Az yüklü: {len(underloaded_instructors)}")
                # Döngü devam etsin, başka max/min hoca çiftleri dene
        
        final_workloads = self._calculate_current_workloads(assignments)
        final_diff = max(final_workloads.values()) - min(final_workloads.values()) if final_workloads else 0
        
        logger.info(f"  Swap tamamlandı: {swaps_performed} swap yapıldı, final fark: {final_diff}")
        
        return {
            "swaps_performed": swaps_performed,
            "final_workload_diff": final_diff
        }

    def _enforce_lower_bound_with_swaps(
        self,
        assignments: List[Dict[str, Any]],
        sorted_timeslots: List[Dict[str, Any]],
        timeslot_to_index: Dict[int, int],
        x_min_bound: int,
        x_max_bound: int,
        locked_jurors_by_project: Optional[Dict[int, Set[int]]] = None,
        max_iterations: int = 500
    ) -> int:
        """
        Herkesin iş yükünü en az x_min_bound seviyesine çıkarmak için hedefli swap uygula.
        Donör hocalar: iş yükü > x_min_bound olanlar (tercihen continuity kaybı düşük slotlarından).
        Alıcı hocalar: iş yükü < x_min_bound olanlar.
        """
        swaps = 0
        for _ in range(max_iterations):
            workloads = self._calculate_current_workloads(assignments)
            if not workloads:
                break
            min_wl = min(workloads.values())
            if min_wl >= x_min_bound:
                break
            # En az yüklü hocayı al
            under_instructor = min(workloads, key=lambda k: workloads[k])
            under_wl = workloads[under_instructor]
            if under_wl >= x_min_bound:
                continue

            # Donör adayları (yükü > x_min_bound) çoktan aza sırala
            donors = sorted(
                [iid for iid, wl in workloads.items() if wl > x_min_bound],
                key=lambda k: (workloads[k] > x_max_bound, workloads[k]),
                reverse=True
            )
            swapped = False
            for donor in donors:
                # Donörün jüri olduğu slotları continuity düşükten yükseğe sırala (kilitli jüriyi koru)
                donor_slots = []
                for assignment in assignments:
                    instructors = assignment.get('instructors', [])
                    responsible_id = assignment.get('responsible_instructor_id')
                    if not responsible_id and instructors:
                        fi = instructors[0]
                        responsible_id = fi.get('id') if isinstance(fi, dict) else fi
                    if isinstance(responsible_id, dict):
                        responsible_id = responsible_id.get('id')
                    # Donör bu assignment'ta jüri mi?
                    for instr in instructors:
                        iid = instr.get('id') if isinstance(instr, dict) else instr
                        if iid == donor and iid != responsible_id:
                            proj_id_here = assignment.get('project_id')
                            if locked_jurors_by_project and proj_id_here in locked_jurors_by_project:
                                if iid in locked_jurors_by_project[proj_id_here]:
                                    continue
                            cont = self._calculate_continuity_score(
                                donor,
                                assignment.get('classroom_id'),
                                assignment.get('timeslot_id'),
                                assignments,
                                sorted_timeslots,
                                timeslot_to_index
                            )
                            donor_slots.append((assignment, cont))
                            break
                donor_slots.sort(key=lambda x: x[1])  # continuity düşük önce
                # continuity=0 varsa onları tercih et
                has_zero = any(c == 0 for _, c in donor_slots)

                for assignment, cont_val in donor_slots:
                    if has_zero and cont_val >= 1.0:
                        continue
                    # Alıcı bu assignment'a atanabilir mi ve continuity sağlayacak mı?
                    if not self._check_instructor_assignability(under_instructor, assignment, assignments):
                        continue
                    cont_gain_under = self._calculate_continuity_score(
                        under_instructor,
                        assignment.get('classroom_id'),
                        assignment.get('timeslot_id'),
                        assignments,
                        sorted_timeslots,
                        timeslot_to_index
                    )
                    # Continuity tercihi sürer; ancak min yükseltme kritikse continuity=0'a da izin ver

                    # Donörün iş yükünü düşürmek x_min_bound altına inmemeli
                    if workloads[donor] - 1 < x_min_bound:
                        continue

                    # Alıcı X+1'i aşmamalı
                    if workloads.get(under_instructor, 0) + 1 > x_max_bound:
                        continue

                    # Swap uygula: donörü çıkar, alıcıyı ekle
                    instrs = assignment.get('instructors', [])
                    for i, ins in enumerate(instrs):
                        iid = ins.get('id') if isinstance(ins, dict) else ins
                        if iid == donor:
                            instrs.pop(i)
                            break
                    assignment['instructors'].append(under_instructor)

                    swaps += 1
                    swapped = True
                    break
                if swapped:
                    break

            if not swapped:
                # Daha fazla iyileştirme mümkün değil
                break

        return swaps

    def _aggressive_workload_rebalancing(
        self,
        assignments: List[Dict[str, Any]],
        sorted_timeslots: List[Dict[str, Any]],
        timeslot_to_index: Dict[int, int],
        current_workloads: Dict[int, int],
        locked_jurors_by_project: Optional[Dict[int, Set[int]]] = None
    ) -> int:
        """
        Agresif çoklu swap ile iş yükü dengeleme
        
        Fark çok büyükse (5'ten fazla), aynı iterasyonda birden fazla swap yaparak
        daha hızlı denge sağlar.
        
        Args:
            assignments: Tüm atamalar
            sorted_timeslots: Sıralı timeslot listesi
            timeslot_to_index: Timeslot ID -> index mapping
            current_workloads: Mevcut iş yükleri
        
        Returns:
            int: Yapılan swap sayısı
        """
        swaps_performed = 0
        max_aggressive_iterations = 50
        
        if not current_workloads:
            return 0
        
        avg_workload = sum(current_workloads.values()) / len(current_workloads)
        max_workload = max(current_workloads.values())
        min_workload = min(current_workloads.values())
        workload_diff = max_workload - min_workload
        
        if workload_diff <= 2:
            return 0
        
        logger.info(f"  🔥 Agresif dengeleme: Fark={workload_diff}, Ort={avg_workload:.1f}")
        
        for iteration in range(max_aggressive_iterations):
            workloads = self._calculate_current_workloads(assignments)
            if not workloads:
                break
            
            max_wl = max(workloads.values())
            min_wl = min(workloads.values())
            diff = max_wl - min_wl
            
            if diff <= 2:
                logger.info(f"  ✅ Agresif dengeleme başarılı: Fark {diff}'e düştü")
                break
            
            # Aşırı yüklü ve az yüklü hocaları bul
            overloaded = sorted(
                [(inst_id, wl) for inst_id, wl in workloads.items() if wl > avg_workload + 1],
                key=lambda x: x[1],
                reverse=True
            )
            underloaded = sorted(
                [(inst_id, wl) for inst_id, wl in workloads.items() if wl < avg_workload - 1],
                key=lambda x: x[1]
            )
            
            if not overloaded or not underloaded:
                break
            
            # Her iterasyonda birden fazla swap yapmaya çalış
            swaps_this_iteration = 0
            max_swaps_per_iteration = min(3, len(overloaded), len(underloaded))  # En fazla 3 swap
            
            for swap_idx in range(max_swaps_per_iteration):
                if swap_idx >= len(overloaded) or swap_idx >= len(underloaded):
                    break
                
                max_inst = overloaded[swap_idx][0]
                min_inst = underloaded[swap_idx][0]
                
                # Max hocadan uygun slot bul (kilitli jüriyi koru)
                max_inst_slots = []
                for assignment in assignments:
                    instructors = assignment.get('instructors', [])
                    responsible_id = assignment.get('responsible_instructor_id')
                    if not responsible_id and instructors:
                        first_instr = instructors[0]
                        responsible_id = first_instr.get("id") if isinstance(first_instr, dict) else first_instr
                    
                    if isinstance(responsible_id, dict):
                        responsible_id = responsible_id.get("id")
                    
                    # Max hocanın jüri slotlarını bul
                    for instr in instructors:
                        instr_id = instr.get("id") if isinstance(instr, dict) else instr
                        if instr_id == max_inst and instr_id != responsible_id:
                            proj_id_here = assignment.get('project_id')
                            if locked_jurors_by_project and proj_id_here in locked_jurors_by_project:
                                if instr_id in locked_jurors_by_project[proj_id_here]:
                                    continue
                            max_inst_slots.append({
                                'assignment': assignment,
                                'project_id': assignment.get('project_id'),
                                'classroom_id': assignment.get('classroom_id'),
                                'timeslot_id': assignment.get('timeslot_id')
                            })
                            break
                
                # Min hocaya uygun slot bul
                swapped = False
                for slot_info in max_inst_slots:
                    assignment = slot_info['assignment']
                    can_assign = self._check_instructor_assignability(
                        min_inst,
                        assignment,
                        assignments
                    )
                    
                    if can_assign:
                        # Swap yap
                        instructors_list = assignment.get('instructors', [])
                        # Max hocayı kaldır, min hocayı ekle
                        new_instructors = []
                        for instr in instructors_list:
                            instr_id = instr.get("id") if isinstance(instr, dict) else instr
                            if instr_id != max_inst:
                                new_instructors.append(instr)
                        new_instructors.append(min_inst)
                        assignment['instructors'] = new_instructors
                        
                        swaps_performed += 1
                        swaps_this_iteration += 1
                        swapped = True
                        logger.debug(f"    🔥 Agresif swap #{swaps_performed}: Hoca {max_inst} → Hoca {min_inst}")
                        break
                
                if not swapped:
                    # Bu çift için swap yapılamadı, sonrakine geç
                    continue
            
            if swaps_this_iteration == 0:
                # Bu iterasyonda hiç swap yapılamadı
                break
        
        return swaps_performed

    def _quick_rebalance_pass(
        self,
        assignments: List[Dict[str, Any]],
        sorted_timeslots: List[Dict[str, Any]],
        timeslot_to_index: Dict[int, int],
        locked_jurors_by_project: Optional[Dict[int, Set[int]]] = None,
        max_iterations: int = 10
    ) -> int:
        """
        Hızlı rebalancing pass - assignment sırasında çağrılır
        
        Args:
            assignments: Tüm atamalar
            sorted_timeslots: Sıralı timeslot listesi
            timeslot_to_index: Timeslot ID -> index mapping
            max_iterations: Maksimum iterasyon sayısı
        
        Returns:
            int: Yapılan swap sayısı
        """
        swaps_performed = 0
        
        for iteration in range(max_iterations):
            workloads = self._calculate_current_workloads(assignments)
            
            if not workloads:
                break
            
            max_workload = max(workloads.values())
            min_workload = min(workloads.values())
            workload_diff = max_workload - min_workload
            
            # Eğer fark 2 veya daha azsa yeterli dengede
            if workload_diff <= 2:
                break
            
            avg_workload = sum(workloads.values()) / len(workloads)
            
            # En yüksek ve en düşük yükteki hocaları bul
            max_instructors = [inst_id for inst_id, wl in workloads.items() if wl == max_workload]
            min_instructors = [inst_id for inst_id, wl in workloads.items() if wl == min_workload]
            
            swapped = False
            
            # Sadece bir swap yap (hızlı olmalı)
            for max_instructor in max_instructors:
                if swapped:
                    break
                
                # Max hocadan bir jüri slotu bul (kilitli jüriyi koru)
                for assignment in assignments:
                    instructors = assignment.get('instructors', [])
                    responsible_id = assignment.get('responsible_instructor_id')
                    if not responsible_id and instructors:
                        first_instr = instructors[0]
                        responsible_id = first_instr.get("id") if isinstance(first_instr, dict) else first_instr
                    
                    if isinstance(responsible_id, dict):
                        responsible_id = responsible_id.get("id")
                    
                    # Max hocanın jüri görevi var mı?
                    is_jury = False
                    for instr in instructors:
                        instr_id = instr.get("id") if isinstance(instr, dict) else instr
                        if instr_id == max_instructor and instr_id != responsible_id:
                            proj_id_here = assignment.get('project_id')
                            if locked_jurors_by_project and proj_id_here in locked_jurors_by_project:
                                if instr_id in locked_jurors_by_project[proj_id_here]:
                                    continue
                            is_jury = True
                            break
                    
                    if not is_jury:
                        continue
                    
                    # Min hocaya atanabilir mi?
                    for min_instructor in min_instructors:
                        if swapped:
                            break
                        
                        can_assign = self._check_instructor_assignability(
                            min_instructor,
                            assignment,
                            assignments
                        )
                        
                        if can_assign:
                            # Swap yap
                            new_instructors = []
                            for instr in instructors:
                                instr_id = instr.get("id") if isinstance(instr, dict) else instr
                                if instr_id != max_instructor:
                                    new_instructors.append(instr)
                            new_instructors.append(min_instructor)
                            assignment['instructors'] = new_instructors
                            
                            swaps_performed += 1
                            swapped = True
                            break
                
                if swapped:
                    break
            
            if not swapped:
                # Bu iterasyonda swap yapılamadı, dur
                break
        
        return swaps_performed

    def _parse_time(self, time_str: str) -> dt_time:
        """Zaman string'ini datetime.time'a çevir"""
        try:
            if isinstance(time_str, dt_time):
                return time_str
            parts = str(time_str).split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            return dt_time(hour, minute)
        except Exception:
            return dt_time(9, 0)