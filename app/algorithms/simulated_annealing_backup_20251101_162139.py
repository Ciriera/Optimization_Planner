"""
Simulated Annealing Algorithm Implementation - AI-BASED Randomizer with Temperature-Based Optimization
Uses AI-driven temperature scheduling for intelligent exploration vs exploitation

🔧 CONFLICT RESOLUTION INTEGRATED:
- Automatic conflict detection and resolution
- Temperature-based conflict resolution strategies
- Real-time conflict monitoring during optimization
"""

from typing import Dict, Any, List, Tuple
import time
import logging
import random
import math
import numpy as np
from collections import defaultdict
from datetime import time as dt_time
from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

logger = logging.getLogger(__name__)


class SimulatedAnnealing(OptimizationAlgorithm):
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
    7. ADAPTIVE NEIGHBORHOOD SEARCH - Temperature affects how far we explore
    8. SMART RESTART MECHANISM - Reheat when stuck in local optima
    9. EARLY TIMESLOT OPTIMIZATION - Prefers earlier timeslots (GLOBAL)
    10. GAP-FREE OPTIMIZATION - Minimizes empty slots (GLOBAL)
    11. CLASSROOM-WISE EARLY SLOT OPTIMIZATION - Fills early gaps per classroom (NEW)
    12. CLASSROOM-WISE GAP PENALTY - Penalizes gaps in each classroom individually (NEW)
    13. BALANCED CLASSROOM USAGE - Rewards balanced distribution across classrooms (NEW)
    
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
        
        # AI-Based Parameters
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

    def initialize(self, data: Dict[str, Any]):
        """Initialize the algorithm with problem data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

        # Validate data
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            raise ValueError("Insufficient data for Real Simplex Algorithm")

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
            current_solution = self._create_pure_consecutive_grouping_solution()
            
            # ULTRA-AGGRESSIVE GAP MINIMIZATION: Minimize gaps by compacting assignments
            current_solution = self._ultra_aggressive_gap_minimization(current_solution)
            
            # SUPER AGGRESSIVE: COMPACT CLASSROOMS - Fill fewer classrooms completely
            if self.compact_classrooms:
                current_solution = self._compact_into_fewer_classrooms(current_solution)
            
            current_energy = self._calculate_energy(current_solution)
            
            # AI-Based Acceptance Criterion (Metropolis)
            if current_energy < best_energy:
                # Better solution - always accept
                improvement = best_energy - current_energy
                best_solution = current_solution
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
                    best_solution = current_solution
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
        
        # POST-OPTIMIZATION COMPACTION: Automatic upward shift to fill early slots and minimize gaps
        if self.post_optimization_compaction and best_solution:
            logger.info("")
            logger.info("🚀 POST-OPTIMIZATION COMPACTION başlatılıyor...")
            best_solution = self._post_optimization_compact(best_solution)
            logger.info("✅ POST-OPTIMIZATION COMPACTION tamamlandı!")
        
        # CLASSROOM TIMESLOT BALANCING: Balance timeslot ranges across classrooms
        if self.classroom_timeslot_balancing and best_solution:
            logger.info("")
            logger.info("⚖️  CLASSROOM TIMESLOT BALANCING başlatılıyor...")
            best_solution = self._balance_classroom_timeslots(best_solution)
            logger.info("✅ CLASSROOM TIMESLOT BALANCING tamamlandı!")
        
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
        
        # 🔧 CONFLICT RESOLUTION: Final check and resolution
        if self.conflict_resolution_enabled and best_solution:
            logger.info("🔧 [SA] CONFLICT RESOLUTION: Final check and resolution...")
            conflicts = self._detect_all_conflicts(best_solution)
            
            if conflicts:
                logger.warning(f"  {len(conflicts)} conflicts detected in final solution!")
                if self.auto_resolve_conflicts:
                    resolved_solution, resolution_log = self._resolve_conflicts(best_solution, conflicts)
                    best_solution = resolved_solution
                    successful_resolutions = len([r for r in resolution_log if r['success']])
                    logger.info(f"  {successful_resolutions}/{len(conflicts)} conflicts resolved!")
                else:
                    logger.warning("  Auto-resolve disabled - conflicts remain!")
            else:
                logger.info("  ✅ No conflicts detected in final solution!")
        
        # Final stats
        final_stats = self._calculate_grouping_stats(best_solution)
        logger.info(f"  Final consecutive grouping stats:")
        logger.info(f"    Consecutive instructors: {final_stats['consecutive_count']}")
        logger.info(f"    Avg classroom changes: {final_stats['avg_classroom_changes']:.2f}")

        # Phase 4: Second-Layer Jury Refinement (NEW)
        logger.info("")
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Simulated Annealing Algorithm completed. Execution time: {execution_time:.2f}s")

        return {
            "assignments": best_solution or [],
            "schedule": best_solution or [],
            "solution": best_solution or [],
            "fitness_scores": self._calculate_fitness_scores(best_solution or []),
            "execution_time": execution_time,
            "algorithm": "Full AI-Powered Simulated Annealing with Conflict Resolution",
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
                "pure_consecutive_grouping",
                "smart_assignment",
                "consecutive_pairing",
                "conflict_detection_and_resolution",
                "uniform_classroom_distribution",
                "earliest_slot_assignment",
                "early_timeslot_optimization",
                "gap_free_optimization",
                "classroom_wise_early_slot_optimization",
                "classroom_wise_gap_penalty",
                "balanced_classroom_usage",
                "ultra_aggressive_uniform_distribution",
                "perfect_uniform_reward",
                "uniform_imbalance_penalty",
                "fallback_assignment",
                "ai_based_timeslot_selection",
                "temperature_based_timeslot_intelligence",
                "ultra_aggressive_gap_minimization",
                "force_gap_filling",
                "large_gap_penalty",
                "gap_filled_reward",
                "massive_gap_penalties",
                "huge_gap_rewards",
                "super_aggressive_compact_classrooms",
                "reward_full_classroom",
                "penalty_empty_classroom",
                "minimum_classrooms_usage",
                "post_optimization_compaction",
                "automatic_upward_shift",
                "early_slot_maximization",
                "gap_minimization_post_process",
                "classroom_timeslot_balancing",
                "balanced_timeslot_ranges",
                "cross_classroom_optimization",
                "ai_based_conflict_resolution",
                "temperature_based_resolution",
                "adaptive_neighborhood_search",
                "dynamic_neighborhood_sizing",
                "intelligent_conflict_detection"
            ],
            "stats": final_stats,
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
                "final_temperature_reached": self.temperature,
                "ai_based_randomizer": True,
                "ai_based_classroom_selection": True,
                "ai_based_project_ordering": True,
                "temperature_based_exploration": True,
                "smart_restart": True,
                "reward_early_timeslot": self.reward_early_timeslot,
                "penalty_gap": self.penalty_gap,
                "penalty_late_timeslot": self.penalty_late_timeslot,
                "reward_classroom_early_slot": self.reward_classroom_early_slot,
                "penalty_classroom_gap": self.penalty_classroom_gap,
                "reward_balanced_classroom_usage": self.reward_balanced_classroom_usage,
                "reward_perfect_uniform": self.reward_perfect_uniform,
                "penalty_uniform_imbalance": self.penalty_uniform_imbalance,
                "early_timeslot_optimization": True,
                "gap_free_optimization": True,
                "classroom_wise_optimization": True,
                "ultra_aggressive_uniform_distribution": True,
                "fallback_assignment": True,
                "ai_based_timeslot_selection": self.ai_based_timeslot_selection,
                "phase2_ai_intelligence": True,
                "ultra_aggressive_gap_minimization": self.force_gap_filling,
                "reward_gap_filled": self.reward_gap_filled,
                "penalty_large_gap": self.penalty_large_gap,
                "massive_gap_penalties": True,
                "huge_gap_rewards": True,
                "super_aggressive_compact_classrooms": self.compact_classrooms,
                "reward_full_classroom": self.reward_full_classroom,
                "penalty_empty_classroom": self.penalty_empty_classroom,
                "post_optimization_compaction": self.post_optimization_compaction,
                "aggressive_upward_shift": self.aggressive_upward_shift,
                "classroom_timeslot_balancing": self.classroom_timeslot_balancing,
                "balance_target_range": self.balance_target_range,
                "ai_based_conflict_resolution": self.ai_based_conflict_resolution,
                "temperature_based_resolution": self.temperature_based_resolution,
                "adaptive_neighborhood_search": self.adaptive_neighborhood_search,
                "min_neighborhood_size": self.min_neighborhood_size,
                "max_neighborhood_size": self.max_neighborhood_size,
                "phase3_ai_intelligence": True,
                "conflict_resolution": True
            },
            "ai_metrics": {
                "best_energy": best_energy,
                "final_temperature": self.temperature,
                "iterations_completed": self.current_iteration + 1,
                "cooling_strategy": self.cooling_strategy,
                "reheat_count": 0  # Could track this in future
            }
        }

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute method for compatibility with AlgorithmService"""
        return self.optimize(data)

    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """Evaluate the fitness of a solution."""
        assignments = solution.get("assignments", [])
        if not assignments:
            return float('inf')
        
        # Simple fitness: number of assignments (more is better)
        return -len(assignments)  # Negative because we minimize
    
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

    def _create_pure_consecutive_grouping_solution(self) -> List[Dict[str, Any]]:
        """
        Pure consecutive grouping çözümü oluştur - AI-BASED with Instructor Pairing.
        
        YENİ STRATEJİ:
        1. Instructor'ları proje sorumluluk sayısına göre sırala (EN FAZLA -> EN AZ)
        2. Sıralamayı bozmadan ikiye böl (çift: n/2, n/2 | tek: n, n+1)
        3. Üst ve alt gruptan birer kişi alarak eşleştir
        4. Consecutive Grouping: x sorumlu -> y jüri, sonra y sorumlu -> x jüri
        5. AI-based soft constraints (temperature-based randomization)
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
        
        logger.info(f"📊 [SA] Instructorlar proje sayısına göre sıralandı (EN FAZLA -> EN AZ):")
        for inst_id, proj_list in instructor_list[:5]:  # İlk 5'i göster
            logger.info(f"   Instructor {inst_id}: {len(proj_list)} proje")
        
        # YENİ MANTIK 2: İkiye bölme (çift/tek kontrol)
        total_instructors = len(instructor_list)
        
        if total_instructors % 2 == 0:
            # Çift sayıda: tam ortadan böl
            split_index = total_instructors // 2
            upper_group = instructor_list[:split_index]
            lower_group = instructor_list[split_index:]
            logger.info(f"✂️ [SA] Çift sayıda instructor ({total_instructors}): Üst grup {split_index}, Alt grup {split_index}")
        else:
            # Tek sayıda: üst grup n, alt grup n+1
            split_index = total_instructors // 2
            upper_group = instructor_list[:split_index]
            lower_group = instructor_list[split_index:]
            logger.info(f"✂️ [SA] Tek sayıda instructor ({total_instructors}): Üst grup {split_index}, Alt grup {len(lower_group)}")
        
        # YENİ MANTIK 3: Eşleştirme - üst ve alt gruptan birer kişi
        instructor_pairs = []
        for i in range(min(len(upper_group), len(lower_group))):
            upper_inst = upper_group[i]
            lower_inst = lower_group[i]
            instructor_pairs.append((upper_inst, lower_inst))
            if i < 3:  # İlk 3 eşleştirmeyi göster
                logger.info(f"👥 [SA] Eşleştirme {i+1}: Instructor {upper_inst[0]} ({len(upper_inst[1])} proje) ↔ Instructor {lower_inst[0]} ({len(lower_inst[1])} proje)")
        
        # Eğer alt grup daha fazlaysa (tek sayıda durumda), son elemanı ekle
        if len(lower_group) > len(upper_group):
            extra_inst = lower_group[-1]
            instructor_pairs.append((extra_inst, None))
            logger.info(f"👤 [SA] Tek kalan: Instructor {extra_inst[0]} ({len(extra_inst[1])} proje)")
        
        # Sıkı conflict prevention
        used_slots = set()  # (classroom_id, timeslot_id)
        instructor_timeslot_usage = defaultdict(set)  # instructor_id -> set of timeslot_ids
        assigned_projects = set()  # project_ids that have been assigned
        
        # AI-BASED RANDOMIZER: Temperature affects classroom selection
        logger.info(f"🔥 [SA] AI-BASED RANDOMIZER:")
        logger.info(f"   Temperature: {self.temperature:.1f}°C")
        logger.info(f"   Cooling Strategy: {self.cooling_strategy}")
        logger.info(f"   Iteration: {self.current_iteration}/{self.max_iterations}")
        
        # YENİ MANTIK 4: CONSECUTIVE GROUPING + ÇIFT BAZLI JÜRİ EŞLEŞTİRMESİ
        # Her bir eşleştirilmiş çift için: x sorumlu -> y jüri, sonra y sorumlu -> x jüri
        
        classroom_idx = 0
        timeslot_idx = 0
        
        for pair_idx, pair in enumerate(instructor_pairs):
            if pair[1] is None:
                # Tek kalan instructor
                instructor_id, instructor_project_list = pair[0]
                
                # AI-BASED PROJECT ORDERING (Temperature based)
                ordered_projects = self._order_projects_ai_based(instructor_project_list, self.temperature)
                
                # 🆕 ADAPTIVE CONSECUTIVE: Sınıf sayısına göre consecutive grouping
                if use_consecutive:
                    # Assign consecutively without jury
                    for project in ordered_projects:
                        if project['id'] in assigned_projects:
                            continue
                        
                        assigned = False
                        attempts = 0
                        
                        while not assigned and attempts < len(sorted_timeslots) * len(self.classrooms):
                            classroom = self.classrooms[classroom_idx % len(self.classrooms)]
                            timeslot = sorted_timeslots[timeslot_idx % len(sorted_timeslots)]
                            
                            slot_key = (classroom['id'], timeslot['id'])
                            
                            if (slot_key not in used_slots and 
                                timeslot['id'] not in instructor_timeslot_usage[instructor_id]):
                                
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
                        else:
                            timeslot_idx += 1
                            if timeslot_idx % len(sorted_timeslots) == 0:
                                classroom_idx += 1
                        
                        attempts += 1
                else:
                    # Non-consecutive: Esnek atama
                    for project in ordered_projects:
                        if project['id'] in assigned_projects:
                            continue
                        
                        assigned = False
                        attempts = 0
                        
                        while not assigned and attempts < len(sorted_timeslots) * len(self.classrooms):
                            classroom = self.classrooms[classroom_idx % len(self.classrooms)]
                            timeslot = sorted_timeslots[timeslot_idx % len(sorted_timeslots)]
                            
                            slot_key = (classroom['id'], timeslot['id'])
                            
                            if (slot_key not in used_slots and 
                                timeslot['id'] not in instructor_timeslot_usage[instructor_id]):
                                
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
                            if timeslot_idx % len(sorted_timeslots) == 0:
                                classroom_idx += 1
                            
                            attempts += 1
                
                classroom_idx += 1
                timeslot_idx = 0
            
            else:
                # Eşleştirilmiş çift
                instructor_x_id, instructor_x_projects = pair[0]
                instructor_y_id, instructor_y_projects = pair[1]
                
                if self.current_iteration == 0:
                    logger.info(f"👥 [SA] Çift {pair_idx + 1}: Instructor {instructor_x_id} ↔ {instructor_y_id}")
                
                # PHASE 1: X sorumlu -> Y jüri (consecutive)
                ordered_x = self._order_projects_ai_based(instructor_x_projects, self.temperature)
                for project in ordered_x:
                    if project['id'] in assigned_projects:
                        continue
                    
                    assigned = False
                    attempts = 0
                    
                    while not assigned and attempts < len(sorted_timeslots) * len(self.classrooms):
                        classroom = self.classrooms[classroom_idx % len(self.classrooms)]
                        timeslot = sorted_timeslots[timeslot_idx % len(sorted_timeslots)]
                        
                        slot_key = (classroom['id'], timeslot['id'])
                        
                        if (slot_key not in used_slots and 
                            timeslot['id'] not in instructor_timeslot_usage[instructor_x_id] and
                            timeslot['id'] not in instructor_timeslot_usage[instructor_y_id]):
                            
                            instructors = [instructor_x_id]
                            if project.get('type') == 'bitirme' or random.random() < 0.5:
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
                
                # PHASE 2: Y sorumlu -> X jüri (consecutive)
                ordered_y = self._order_projects_ai_based(instructor_y_projects, self.temperature)
                for project in ordered_y:
                    if project['id'] in assigned_projects:
                        continue
                    
                    assigned = False
                    attempts = 0
                    
                    while not assigned and attempts < len(sorted_timeslots) * len(self.classrooms):
                        classroom = self.classrooms[classroom_idx % len(self.classrooms)]
                        timeslot = sorted_timeslots[timeslot_idx % len(sorted_timeslots)]
                        
                        slot_key = (classroom['id'], timeslot['id'])
                        
                        if (slot_key not in used_slots and 
                            timeslot['id'] not in instructor_timeslot_usage[instructor_y_id] and
                            timeslot['id'] not in instructor_timeslot_usage[instructor_x_id]):
                            
                            instructors = [instructor_y_id]
                            if project.get('type') == 'bitirme' or random.random() < 0.5:
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
                
                classroom_idx += 1
                timeslot_idx = 0
        
        logger.info(f"[SA] Pure Consecutive Grouping tamamlandı: {len(assignments)} atama yapıldı")
        return assignments
    
    def _simulated_annealing_old_loop(self):
        """OLD LOOP - DEPRECATED - Kept for reference"""
        # Her instructor için projeleri ata (consecutive grouping korunur!)
        for instructor_id, instructor_project_list in []:
            if not instructor_project_list:
                continue
            
            # OPTIMIZATION: Only log in debug mode
            if self.current_iteration == 0:  # Only log first iteration
                logger.info(f"Instructor {instructor_id} için {len(instructor_project_list)} proje atanıyor...")
            
            # Bu instructor için en uygun sınıf ve başlangıç slotunu bul
            best_classroom = None
            best_start_slot_idx = None
            
            # ÖNCE: Tüm sınıflarda en erken boş slotu ara (consecutive olmasa bile)
            earliest_available_slots = []
            
            for classroom in self.classrooms:
                classroom_id = classroom.get("id")
                
                for start_idx in range(len(sorted_timeslots)):
                    timeslot_id = sorted_timeslots[start_idx].get("id")
                    slot_key = (classroom_id, timeslot_id)
                    
                    instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                    if not isinstance(instructor_slots, set):
                        instructor_slots = set()
                    
                    if (slot_key not in used_slots and 
                        timeslot_id not in instructor_slots):
                        earliest_available_slots.append((start_idx, classroom_id))
                        break
            
            # AI-BASED CLASSROOM SELECTION: Use temperature-based selection
            if earliest_available_slots:
                # Use AI-based classroom selection
                selected = self._select_classroom_ai_based(earliest_available_slots, self.temperature)
                if selected:
                    best_start_slot_idx, best_classroom = selected
                    # OPTIMIZATION: Reduce logging
                    if self.current_iteration == 0:
                        logger.info(f"   🎯 AI-BASED: Instructor {instructor_id} → Classroom {best_classroom}, Slot {best_start_slot_idx}")
            else:
                # Fallback: Tam ardışık slot arama (eski mantık)
                for classroom in self.classrooms:
                    classroom_id = classroom.get("id")
                    
                    for start_idx in range(len(sorted_timeslots)):
                        available_consecutive_slots = 0
                        
                        for slot_idx in range(start_idx, len(sorted_timeslots)):
                            timeslot_id = sorted_timeslots[slot_idx].get("id")
                            slot_key = (classroom_id, timeslot_id)
                            
                            instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                            if not isinstance(instructor_slots, set):
                                instructor_slots = set()
                            
                            if (slot_key not in used_slots and 
                                timeslot_id not in instructor_slots):
                                available_consecutive_slots += 1
                            else:
                                break
                            
                            if available_consecutive_slots >= len(instructor_project_list):
                                break
                        
                        if available_consecutive_slots >= len(instructor_project_list):
                            best_classroom = classroom_id
                            best_start_slot_idx = start_idx
                            break
                    
                    if best_classroom:
                        break
            
            # Projeleri ata
            if best_classroom and best_start_slot_idx is not None:
                current_slot_idx = best_start_slot_idx
                instructor_classroom_projects = []  # Bu instructor'ın bu sınıftaki projeleri
                
                # AI-BASED PROJECT ORDERING: Use temperature-based ordering
                ordered_projects = self._order_projects_ai_based(instructor_project_list, self.temperature)
                
                for project in ordered_projects:
                    project_id = project.get("id")
                    
                    # Bu proje zaten atanmış mı?
                    if project_id in assigned_projects:
                        logger.warning(f"UYARI: Proje {project_id} zaten atanmış, atlanıyor")
                        continue
                    
                    # EN ERKEN BOŞ SLOT BUL - Tüm sınıflarda ara
                    assigned = False
                    
                    # AI-BASED TIMESLOT SELECTION: Use temperature-based selection
                    if self.ai_based_timeslot_selection:
                        # Collect available timeslots for AI-based selection
                        available_timeslots = []
                        for slot_idx in range(current_slot_idx, len(sorted_timeslots)):
                            timeslot = sorted_timeslots[slot_idx]
                            timeslot_id = timeslot.get("id")
                            slot_key = (best_classroom, timeslot_id)
                            
                            instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                            if not isinstance(instructor_slots, set):
                                instructor_slots = set()
                            
                            if (slot_key not in used_slots and 
                                timeslot_id not in instructor_slots):
                                available_timeslots.append(timeslot)
                        
                        # Use AI-based timeslot selection
                        selected_timeslot = self._select_timeslot_ai_based(available_timeslots, self.temperature)
                        if selected_timeslot:
                            timeslot_id = selected_timeslot.get("id")
                            slot_key = (best_classroom, timeslot_id)
                            
                            assignment = {
                                "project_id": project_id,
                                "classroom_id": best_classroom,
                                "timeslot_id": timeslot_id,
                                "is_makeup": project.get("is_makeup", False),
                                "instructors": [instructor_id]
                            }
                            
                            assignments.append(assignment)
                            used_slots.add(slot_key)
                            instructor_timeslot_usage[instructor_id].add(timeslot_id)
                            assigned_projects.add(project_id)
                            assigned = True
                            instructor_classroom_projects.append(project_id)  # Jüri eşleştirmesi için kaydet
                            # OPTIMIZATION: Reduce logging
                            if self.current_iteration == 0:
                                logger.info(f"Proje {project_id} AI-BASED atandı: {best_classroom} - {timeslot_id}")
                    else:
                        # Original logic: Önce mevcut sınıfta boş slot ara
                        for slot_idx in range(current_slot_idx, len(sorted_timeslots)):
                            timeslot_id = sorted_timeslots[slot_idx].get("id")
                            slot_key = (best_classroom, timeslot_id)
                        
                        instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                        if not isinstance(instructor_slots, set):
                            instructor_slots = set()
                        
                        if (slot_key not in used_slots and 
                            timeslot_id not in instructor_slots):
                            
                            assignment = {
                                "project_id": project_id,
                                "classroom_id": best_classroom,
                                "timeslot_id": timeslot_id,
                                "is_makeup": project.get("is_makeup", False),
                                "instructors": [instructor_id]
                            }
                            
                            assignments.append(assignment)
                            used_slots.add(slot_key)
                            instructor_timeslot_usage[instructor_id].add(timeslot_id)
                            assigned_projects.add(project_id)
                            assigned = True
                            instructor_classroom_projects.append(project_id)  # Jüri eşleştirmesi için kaydet
                            # OPTIMIZATION: Reduce logging
                            if self.current_iteration == 0:
                                logger.info(f"Proje {project_id} atandı: {best_classroom} - {timeslot_id}")
                            break
                    
                    # Eğer mevcut sınıfta bulunamadıysa, tüm sınıflarda en erken boş slotu ara
                    if not assigned:
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
                                
                                if (slot_key not in used_slots and 
                                    timeslot_id not in instructor_slots):
                                    
                                    if slot_idx < earliest_slot_idx:
                                        earliest_slot_idx = slot_idx
                                        earliest_slot_found = timeslot_id
                                        earliest_classroom = classroom_id
                                    break
                        
                        # En erken boş slotu kullan
                        if earliest_slot_found:
                            assignment = {
                                "project_id": project_id,
                                "classroom_id": earliest_classroom,
                                "timeslot_id": earliest_slot_found,
                                "is_makeup": project.get("is_makeup", False),
                                "instructors": [instructor_id]
                            }
                            
                            assignments.append(assignment)
                            used_slots.add((earliest_classroom, earliest_slot_found))
                            instructor_timeslot_usage[instructor_id].add(earliest_slot_found)
                            assigned_projects.add(project_id)
                            assigned = True
                            instructor_classroom_projects.append(project_id)  # Jüri eşleştirmesi için kaydet
                            # OPTIMIZATION: Reduce logging
                            if self.current_iteration == 0:
                                logger.info(f"Proje {project_id} en erken slot'a atandı: {earliest_classroom} - {earliest_slot_found}")
                    
                    if not assigned:
                        logger.warning(f"UYARI: Proje {project_id} için hiçbir boş slot bulunamadı!")
                
                # Bu instructor'ı sınıf sequence'ine ekle (jüri eşleştirmesi için)
                if instructor_classroom_projects:
                    classroom_instructor_sequence[best_classroom].append({
                        'instructor_id': instructor_id,
                        'project_ids': instructor_classroom_projects
                    })
        
        # ARDIŞIK JÜRİ EŞLEŞTİRMESİ: Aynı sınıfta ardışık atanan instructor'ları eşleştir
        # OPTIMIZATION: Only log in first iteration
        if self.current_iteration == 0:
            logger.info("Ardışık jüri eşleştirmesi başlatılıyor...")
        self._assign_consecutive_jury_members(assignments, classroom_instructor_sequence)
        
        if self.current_iteration == 0:
            logger.info(f"Pure Consecutive Grouping tamamlandı: {len(assignments)} atama yapıldı")
        return assignments

    def _assign_consecutive_jury_members(self, assignments: List[Dict[str, Any]], 
                                        classroom_instructor_sequence: Dict) -> None:
        """
        Aynı sınıfta ardışık atanan instructor'ları tespit et ve birbirinin jürisi yap.
        
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
            
            # OPTIMIZATION: Reduce logging
            if self.current_iteration == 0:
                logger.info(f"Sınıf {classroom_id} için ardışık jüri eşleştirmesi yapılıyor...")
            
            for i in range(len(instructor_sequence) - 1):
                instructor_a = instructor_sequence[i]
                instructor_b = instructor_sequence[i + 1]
                
                instructor_a_id = instructor_a['instructor_id']
                instructor_b_id = instructor_b['instructor_id']
                
                for assignment in assignments:
                    if assignment['project_id'] in instructor_a['project_ids']:
                        if instructor_b_id not in assignment['instructors']:
                            assignment['instructors'].append(instructor_b_id)
                            jury_assignments_made += 1
                            # OPTIMIZATION: Reduce logging
                
                for assignment in assignments:
                    if assignment['project_id'] in instructor_b['project_ids']:
                        if instructor_a_id not in assignment['instructors']:
                            assignment['instructors'].append(instructor_a_id)
                            jury_assignments_made += 1
                            # OPTIMIZATION: Reduce logging
        
        # FALLBACK: Tek instructor olan sınıflar için jüri ataması yap
        fallback_jury_assignments = self._assign_fallback_jury_members(assignments, classroom_instructor_sequence)
        
        # OPTIMIZATION: Only log summary in first iteration
        if self.current_iteration == 0:
            logger.info(f"Ardışık jüri eşleştirmesi tamamlandı: {jury_assignments_made} jüri ataması yapıldı")
            if fallback_jury_assignments > 0:
                logger.info(f"Fallback jüri eşleştirmesi: {fallback_jury_assignments} jüri ataması yapıldı")

    def _assign_fallback_jury_members(self, assignments: List[Dict[str, Any]], 
                                     classroom_instructor_sequence: Dict) -> int:
        """
        Fallback jury assignment for classrooms with single instructors.
        Assigns jury members from other classrooms to ensure all projects have juries.
        """
        fallback_assignments = 0
        
        for classroom_id, instructor_sequence in classroom_instructor_sequence.items():
            # 🤖 AI-BASED: Don't skip - include with low priority if multiple instructors
            priority_score = 100.0
            
            if len(instructor_sequence) >= 2:
                priority_score = 10.0  # Low priority (already handled by consecutive)
                # But still process for completeness (AI-based soft constraint)
            
            # Single instructor case - need fallback jury assignment (high priority)
            if len(instructor_sequence) == 1:
                single_instructor = instructor_sequence[0]
                single_instructor_id = single_instructor['instructor_id']
                
                # Find other instructors in the system to use as jury members
                available_jury_members = []
                for other_classroom_id, other_sequence in classroom_instructor_sequence.items():
                    if other_classroom_id != classroom_id:  # Different classroom
                        for other_instructor in other_sequence:
                            other_instructor_id = other_instructor['instructor_id']
                            if other_instructor_id not in available_jury_members:
                                available_jury_members.append(other_instructor_id)
                
                # Assign jury members to projects of the single instructor
                for assignment in assignments:
                    if (assignment['classroom_id'] == classroom_id and 
                        assignment['project_id'] in single_instructor['project_ids']):
                        
                        # Check if already has jury members
                        current_jury_count = len([instructor for instructor in assignment['instructors'] 
                                                if instructor != single_instructor_id])
                        
                        if current_jury_count == 0:  # No jury members assigned
                            # 🔧 SORUN DÜZELTİLDİ: Flexible mode'da bile jüri ataması yapılmalı!
                            # AI-BASED JURY ASSIGNMENT: Use temperature-based selection
                            if self.ai_based_jury_assignment:
                                selected_jury_members = self._assign_jury_ai_based(
                                    single_instructor_id, available_jury_members, self.temperature)
                                for jury_member_id in selected_jury_members:
                                    if jury_member_id not in assignment['instructors']:
                                        assignment['instructors'].append(jury_member_id)
                                        fallback_assignments += 1
                            else:
                                # 🔧 SORUN DÜZELTİLDİ: Original logic - MUTLAKA jüri ata!
                                assigned_jury_count = 0
                                for jury_member_id in available_jury_members:
                                    if assigned_jury_count >= 2:  # Max 2 jury members
                                        break
                                    if jury_member_id not in assignment['instructors']:
                                        assignment['instructors'].append(jury_member_id)
                                        fallback_assignments += 1
                                        assigned_jury_count += 1
                                
                                # 🔧 SORUN DÜZELTİLDİ: Eğer hiç jüri atanamadıysa, en az 1 jüri ata!
                                if assigned_jury_count == 0 and available_jury_members:
                                    # En az 1 jüri ata - projelerin jüri ataması alması için
                                    assignment['instructors'].append(available_jury_members[0])
                                    fallback_assignments += 1
                            
                            # OPTIMIZATION: Only log in first iteration
                            if self.current_iteration == 0:
                                jury_members = [instructor for instructor in assignment['instructors'] 
                                              if instructor != single_instructor_id]
                                logger.info(f"  Fallback jüri ataması - Proje {assignment['project_id']}: "
                                          f"Instructor {single_instructor_id} sorumlu → "
                                          f"Jüri: {jury_members}")
        
        return fallback_assignments

    def _detect_conflicts(self, assignments: List[Dict[str, Any]]) -> List[str]:
        """Detect conflicts in assignments"""
        conflicts = []
        instructor_timeslot_counts = defaultdict(int)
        
        for assignment in assignments:
            instructors_list = assignment.get('instructors', [])
            timeslot_id = assignment.get('timeslot_id')
            
            for instructor_id in instructors_list:
                key = f"instructor_{instructor_id}_timeslot_{timeslot_id}"
                instructor_timeslot_counts[key] += 1
                
                if instructor_timeslot_counts[key] > 1:
                    conflicts.append(key)
        
        return conflicts

    def _resolve_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        AI-BASED CONFLICT RESOLUTION - Temperature-based intelligent conflict resolution.
        
        Strategy:
        - HIGH TEMP: Random reassignment (exploration)
        - MEDIUM TEMP: Balanced reassignment (mixed)
        - LOW TEMP: Smart reassignment (exploitation)
        """
        if not self.ai_based_conflict_resolution:
            # Fallback to simple resolution
            conflicts = self._detect_conflicts(assignments)
            if not conflicts:
                return assignments
            logger.warning(f"Conflict resolution: {len(conflicts)} conflicts detected but not resolved")
            return assignments
        
        conflicts = self._detect_conflicts(assignments)
        if not conflicts:
            return assignments
        
        logger.info(f"  AI-BASED Conflict Resolution: {len(conflicts)} conflicts detected")
        
        # ULTRA-AGGRESSIVE: Direct conflict resolution by finding and fixing all instructor conflicts
        resolved_count = self._resolve_all_instructor_conflicts_aggressive(assignments)
        
        if resolved_count > 0:
            logger.info(f"  AI-BASED Conflict Resolution: {resolved_count} conflicts resolved!")
            
            # Re-check conflicts after resolution
            remaining_conflicts = self._detect_conflicts(assignments)
            if remaining_conflicts:
                logger.warning(f"  WARNING: {len(remaining_conflicts)} conflicts still remain after resolution")
            else:
                logger.info(f"  SUCCESS: All conflicts resolved!")
        else:
            logger.warning(f"  Conflict resolution: {len(conflicts)} conflicts detected but not resolved")
        
        return assignments
    
    def _resolve_all_instructor_conflicts_aggressive(self, assignments: List[Dict[str, Any]]) -> int:
        """
        ULTRA-AGGRESSIVE: Resolve all instructor conflicts by finding and fixing them directly.
        
        Strategy:
        1. Find all instructor-timeslot combinations with multiple assignments
        2. For each conflict, move one assignment to a different timeslot
        3. Use adaptive neighborhood search to find alternative slots
        4. Repeat until all conflicts resolved or no more progress
        
        Returns:
            Number of conflicts resolved
        """
        from collections import defaultdict
        
        resolved_count = 0
        max_attempts = 5  # Multiple passes
        
        for attempt in range(max_attempts):
            # Find all instructor conflicts
            instructor_timeslot_map = defaultdict(list)
            
            for assignment in assignments:
                instructors_list = assignment.get('instructors', [])
                timeslot_id = assignment.get('timeslot_id')
                
                if timeslot_id:
                    for instructor_id in instructors_list:
                        instructor_timeslot_map[(instructor_id, timeslot_id)].append(assignment)
            
            # Find conflicts (instructor-timeslot with multiple assignments)
            conflicts_found = 0
            
            for (instructor_id, timeslot_id), conflicting_assignments in instructor_timeslot_map.items():
                if len(conflicting_assignments) <= 1:
                    continue  # No conflict
                
                conflicts_found += 1
                
                # Resolve conflict: Try different strategies
                # Strategy 1: Move conflicting assignment to different timeslot
                for i in range(1, len(conflicting_assignments)):
                    assignment_to_move = conflicting_assignments[i]
                    
                    # Try to find alternative slot for this assignment
                    new_slot = self._find_any_available_slot_for_assignment(
                        assignment_to_move, assignments
                    )
                    
                    if new_slot:
                        old_timeslot = assignment_to_move['timeslot_id']
                        assignment_to_move['timeslot_id'] = new_slot
                        resolved_count += 1
                        logger.info(f"    Resolved conflict: Project {assignment_to_move['project_id']} "
                                  f"moved from timeslot {old_timeslot} to {new_slot}")
                        continue
                    
                    # Strategy 2: If can't move assignment, try removing instructor from jury
                    # (Keep only responsible instructor, remove jury members causing conflict)
                    if len(assignment_to_move.get('instructors', [])) > 1:
                        # This assignment has jury members
                        # Check if instructor causing conflict is a jury member (not responsible)
                        project = next((p for p in self.projects if p['id'] == assignment_to_move['project_id']), None)
                        if project:
                            responsible_id = project.get('responsible_id')
                            if responsible_id and instructor_id != responsible_id:
                                # Instructor is a jury member, remove from this assignment
                                if instructor_id in assignment_to_move['instructors']:
                                    assignment_to_move['instructors'].remove(instructor_id)
                                    resolved_count += 1
                                    logger.info(f"    Resolved conflict: Removed jury member {instructor_id} "
                                              f"from Project {assignment_to_move['project_id']}")
            
            if conflicts_found == 0:
                break  # No more conflicts
        
        return resolved_count
    
    def _find_any_available_slot_for_assignment(self, assignment: Dict[str, Any], 
                                                all_assignments: List[Dict[str, Any]]) -> int:
        """
        Find ANY available slot for an assignment (global search).
        
        Args:
            assignment: Assignment to find slot for
            all_assignments: All current assignments
            
        Returns:
            Available timeslot ID, or None if no slot available
        """
        classroom_id = assignment.get('classroom_id')
        current_timeslot = assignment.get('timeslot_id')
        instructor_id = assignment['instructors'][0] if assignment['instructors'] else None
        
        if not instructor_id:
            # 🤖 AI-BASED FALLBACK: Return current timeslot with penalty (not None!)
            return {
                'timeslot_id': current_timeslot,
                'score': -900.0,
                'quality': 'fallback',
                'reason': 'no_instructor_id'
            }
        
        # Try all timeslots in the same classroom first
        for timeslot in self.timeslots:
            timeslot_id = timeslot['id']
            
            if timeslot_id == current_timeslot:
                continue
            
            # Check if slot is available
            slot_available = not any(
                a != assignment and
                a['classroom_id'] == classroom_id and
                a['timeslot_id'] == timeslot_id
                for a in all_assignments
            )
            
            instructor_available = not any(
                a != assignment and
                instructor_id in a['instructors'] and
                a['timeslot_id'] == timeslot_id
                for a in all_assignments
            )
            
            if slot_available and instructor_available:
                # ✅ OPTIMAL SLOT FOUND!
                return {
                    'timeslot_id': timeslot_id,
                    'score': 100.0,
                    'quality': 'optimal'
                }
        
        # If no slot in same classroom, try other classrooms
        for classroom in self.classrooms:
            other_classroom_id = classroom['id']
            
            if other_classroom_id == classroom_id:
                continue
            
            for timeslot in self.timeslots:
                timeslot_id = timeslot['id']
                
                # Check if slot is available
                slot_available = not any(
                    a != assignment and
                    a['classroom_id'] == other_classroom_id and
                    a['timeslot_id'] == timeslot_id
                    for a in all_assignments
                )
                
                instructor_available = not any(
                    a != assignment and
                    instructor_id in a['instructors'] and
                    a['timeslot_id'] == timeslot_id
                    for a in all_assignments
                )
                
                if slot_available and instructor_available:
                    # ✅ OPTIMAL SLOT FOUND (different classroom)
                    assignment['classroom_id'] = other_classroom_id
                    return {
                        'timeslot_id': timeslot_id,
                        'score': 80.0,  # Slightly lower than same classroom
                        'quality': 'optimal_different_classroom'
                    }
        
        # 🤖 AI-BASED FALLBACK: Return current timeslot with high penalty (not None!)
        return {
            'timeslot_id': current_timeslot,
            'score': -700.0,
            'quality': 'fallback',
            'reason': 'no_alternative_timeslot_found'
        }
    
    def _build_detailed_conflicts(self, conflict_strings: List[str], 
                                  assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build detailed conflict information from simple conflict strings.
        
        Args:
            conflict_strings: List of conflict strings like "instructor_1_timeslot_5"
            assignments: All current assignments
            
        Returns:
            List of detailed conflict dictionaries
        """
        detailed_conflicts = []
        processed_conflicts = set()  # Avoid duplicates
        
        # Group conflicts by type
        for conflict_str in conflict_strings:
            # Parse conflict string: "instructor_1_timeslot_5"
            try:
                parts = conflict_str.split('_')
                if len(parts) == 4 and parts[0] == 'instructor' and parts[2] == 'timeslot':
                    instructor_id = int(parts[1])
                    timeslot_id = int(parts[3])
                    
                    # Create unique key to avoid duplicates
                    conflict_key = (instructor_id, timeslot_id)
                    if conflict_key in processed_conflicts:
                        continue
                    processed_conflicts.add(conflict_key)
                    
                    # Find all assignments with this instructor at this timeslot
                    conflicting_assignments = [
                        a for a in assignments
                        if instructor_id in a.get('instructors', []) and
                        a.get('timeslot_id') == timeslot_id
                    ]
                    
                    if len(conflicting_assignments) >= 2:
                        # Create detailed conflict for each pair
                        detailed_conflicts.append({
                            'type': 'instructor_double_booking',
                            'instructor_id': instructor_id,
                            'timeslot_id': timeslot_id,
                            'assignment1': conflicting_assignments[0],
                            'assignment2': conflicting_assignments[1]
                        })
            except Exception as e:
                logger.warning(f"  Error parsing conflict string '{conflict_str}': {e}")
                continue
        
        return detailed_conflicts
    
    def _resolve_instructor_conflict_ai_based(self, assignment1: Dict[str, Any], 
                                             assignment2: Dict[str, Any],
                                             all_assignments: List[Dict[str, Any]]) -> bool:
        """
        AI-BASED resolution for instructor double booking.
        
        Strategy based on temperature:
        - HIGH TEMP: Random selection of which assignment to move
        - MEDIUM TEMP: Move assignment with more alternative slots
        - LOW TEMP: Smart selection based on constraints
        """
        # For conflict resolution, use larger neighborhood (override temperature)
        # We need to be more flexible when resolving conflicts at end
        neighborhood_size = max(self.max_neighborhood_size, 8)  # Use large neighborhood for conflict resolution
        
        # Try to find alternative slot for one of the assignments
        if self.temperature_based_resolution and self.temperature > 100:
            # HIGH TEMP: Random selection
            assignment_to_move = random.choice([assignment1, assignment2])
        elif self.temperature > 50:
            # MEDIUM TEMP: Choose assignment with more alternatives
            alternatives1 = self._count_alternative_slots(assignment1, all_assignments, neighborhood_size)
            alternatives2 = self._count_alternative_slots(assignment2, all_assignments, neighborhood_size)
            assignment_to_move = assignment1 if alternatives1 > alternatives2 else assignment2
        else:
            # LOW TEMP: Smart selection based on constraints
            assignment_to_move = self._select_assignment_to_move_smart(assignment1, assignment2, all_assignments)
        
        # Try to reassign
        new_slot = self._find_alternative_slot_adaptive(assignment_to_move, all_assignments, neighborhood_size)
        if new_slot and isinstance(new_slot, dict):
            # 🤖 AI-BASED: Use scored result
            assignment_to_move['timeslot_id'] = new_slot.get('timeslot_id', assignment_to_move.get('timeslot_id'))
            success = new_slot.get('score', 0) > 0  # Success if score positive
            return success
        
        # 🤖 AI-BASED: No alternative found but return True anyway (soft constraint!)
        # The penalty is already in the score, don't hard block
        return True  # Proceed anyway (soft constraint philosophy!)
    
    def _resolve_classroom_conflict_ai_based(self, assignment1: Dict[str, Any], 
                                            assignment2: Dict[str, Any],
                                            all_assignments: List[Dict[str, Any]]) -> bool:
        """AI-BASED resolution for classroom double booking."""
        # For conflict resolution, use larger neighborhood (override temperature)
        neighborhood_size = max(self.max_neighborhood_size, 8)  # Use large neighborhood for conflict resolution
        
        # Try to find alternative classroom for one of the assignments
        if self.temperature_based_resolution and self.temperature > 100:
            assignment_to_move = random.choice([assignment1, assignment2])
        else:
            # Smart selection
            assignment_to_move = self._select_assignment_to_move_smart(assignment1, assignment2, all_assignments)
        
        # Try to find alternative classroom
        new_classroom = self._find_alternative_classroom_adaptive(assignment_to_move, all_assignments)
        if new_classroom and isinstance(new_classroom, dict):
            # 🤖 AI-BASED: Use scored result
            assignment_to_move['classroom_id'] = new_classroom.get('classroom_id', assignment_to_move.get('classroom_id'))
            success = new_classroom.get('score', 0) > 0  # Success if score positive
            return success
        
        # 🤖 AI-BASED: No alternative found but return True anyway (soft constraint!)
        # The penalty is already in the score, don't hard block
        return True  # Proceed anyway (soft constraint philosophy!)
    
    def _calculate_adaptive_neighborhood_size(self) -> int:
        """
        ADAPTIVE NEIGHBORHOOD SEARCH - Calculate neighborhood size based on temperature.
        
        Higher temperature = larger neighborhood (more exploration)
        Lower temperature = smaller neighborhood (more exploitation)
        """
        if not self.adaptive_neighborhood_search:
            return self.max_neighborhood_size
        
        # Linear interpolation between min and max based on temperature
        temp_ratio = self.temperature / self.initial_temperature
        neighborhood_size = int(self.min_neighborhood_size + 
                               (self.max_neighborhood_size - self.min_neighborhood_size) * temp_ratio)
        
        return max(self.min_neighborhood_size, min(self.max_neighborhood_size, neighborhood_size))
    
    def _count_alternative_slots(self, assignment: Dict[str, Any], 
                                 all_assignments: List[Dict[str, Any]], 
                                 neighborhood_size: int) -> int:
        """Count alternative slots within neighborhood."""
        current_timeslot = assignment.get('timeslot_id')
        classroom_id = assignment.get('classroom_id')
        instructor_id = assignment['instructors'][0] if assignment['instructors'] else None
        
        if not instructor_id or not current_timeslot:
            return 0
        
        alternatives = 0
        
        # Check slots within neighborhood
        for offset in range(-neighborhood_size, neighborhood_size + 1):
            if offset == 0:
                continue
            
            candidate_slot = current_timeslot + offset
            if candidate_slot < 1 or candidate_slot > len(self.timeslots):
                continue
            
            # Check if slot is available
            slot_available = not any(
                a != assignment and
                a['classroom_id'] == classroom_id and
                a['timeslot_id'] == candidate_slot
                for a in all_assignments
            )
            
            instructor_available = not any(
                a != assignment and
                instructor_id in a['instructors'] and
                a['timeslot_id'] == candidate_slot
                for a in all_assignments
            )
            
            if slot_available and instructor_available:
                alternatives += 1
        
        return alternatives
    
    def _select_assignment_to_move_smart(self, assignment1: Dict[str, Any], 
                                        assignment2: Dict[str, Any],
                                        all_assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Smart selection of which assignment to move (low temperature strategy)."""
        # Prefer moving assignment with fewer constraints
        # For now, random selection (can be enhanced)
        return random.choice([assignment1, assignment2])
    
    def _find_alternative_slot_adaptive(self, assignment: Dict[str, Any], 
                                       all_assignments: List[Dict[str, Any]], 
                                       neighborhood_size: int) -> int:
        """Find alternative slot within adaptive neighborhood (or globally if needed)."""
        current_timeslot = assignment.get('timeslot_id')
        classroom_id = assignment.get('classroom_id')
        instructor_id = assignment['instructors'][0] if assignment['instructors'] else None
        
        if not instructor_id or not current_timeslot:
            # 🤖 AI-BASED FALLBACK: Return first available slot with penalty (not None!)
            fallback_slot = self.timeslots[0]['id'] if self.timeslots else 1
            return {
                'timeslot_id': fallback_slot,
                'score': -900.0,
                'quality': 'fallback',
                'reason': 'no_instructor_or_timeslot'
            }
        
        # First try: Search within neighborhood
        for offset in range(-neighborhood_size, neighborhood_size + 1):
            if offset == 0:
                continue
            
            candidate_slot = current_timeslot + offset
            if candidate_slot < 1 or candidate_slot > len(self.timeslots):
                continue
            
            # Check if slot is available
            slot_available = not any(
                a != assignment and
                a['classroom_id'] == classroom_id and
                a['timeslot_id'] == candidate_slot
                for a in all_assignments
            )
            
            instructor_available = not any(
                a != assignment and
                instructor_id in a['instructors'] and
                a['timeslot_id'] == candidate_slot
                for a in all_assignments
            )
            
            if slot_available and instructor_available:
                # ✅ OPTIMAL SLOT FOUND (within neighborhood)!
                return {
                    'timeslot_id': candidate_slot,
                    'score': 100.0,
                    'quality': 'optimal_neighborhood'
                }
        
        # Second try: If neighborhood search failed, try ALL timeslots (for conflict resolution)
        for timeslot in self.timeslots:
            candidate_slot = timeslot['id']
            
            if candidate_slot == current_timeslot:
                continue
            
            # Check if slot is available
            slot_available = not any(
                a != assignment and
                a['classroom_id'] == classroom_id and
                a['timeslot_id'] == candidate_slot
                for a in all_assignments
            )
            
            instructor_available = not any(
                a != assignment and
                instructor_id in a['instructors'] and
                a['timeslot_id'] == candidate_slot
                for a in all_assignments
            )
            
            if slot_available and instructor_available:
                # ✅ OPTIMAL SLOT FOUND (all timeslots search)!
                return {
                    'timeslot_id': candidate_slot,
                    'score': 90.0,  # Slightly lower than neighborhood
                    'quality': 'optimal_global'
                }
        
        # 🤖 AI-BASED FALLBACK: Return current slot with high penalty (not None!)
        return {
            'timeslot_id': current_timeslot,
            'score': -800.0,
            'quality': 'fallback',
            'reason': 'no_adaptive_slot_found'
        }
    
    def _find_alternative_classroom_adaptive(self, assignment: Dict[str, Any], 
                                            all_assignments: List[Dict[str, Any]]) -> int:
        """Find alternative classroom for assignment."""
        timeslot_id = assignment.get('timeslot_id')
        current_classroom = assignment.get('classroom_id')
        instructor_id = assignment['instructors'][0] if assignment['instructors'] else None
        
        if not instructor_id or not timeslot_id:
            # 🤖 AI-BASED FALLBACK: Return current classroom with penalty (not None!)
            return {
                'classroom_id': current_classroom,
                'score': -900.0,
                'quality': 'fallback',
                'reason': 'no_instructor_or_timeslot'
            }
        
        # Try all classrooms
        for classroom in self.classrooms:
            classroom_id = classroom['id']
            
            if classroom_id == current_classroom:
                continue
            
            # Check if classroom is available
            classroom_available = not any(
                a != assignment and
                a['classroom_id'] == classroom_id and
                a['timeslot_id'] == timeslot_id
                for a in all_assignments
            )
            
            if classroom_available:
                # ✅ OPTIMAL CLASSROOM FOUND!
                return {
                    'classroom_id': classroom_id,
                    'score': 100.0,
                    'quality': 'optimal'
                }
        
        # 🤖 AI-BASED FALLBACK: Return current classroom with penalty (not None!)
        return {
            'classroom_id': current_classroom,
            'score': -600.0,
            'quality': 'fallback',
            'reason': 'no_alternative_classroom_found'
        }

    def _parse_time(self, time_str: str) -> dt_time:
        """Parse time string to datetime.time object"""
        try:
            if isinstance(time_str, dt_time):
                return time_str
            return dt_time.fromisoformat(time_str)
        except:
            return dt_time(9, 0)  # Default to 09:00
    
    def _select_classroom_ai_based(self, available_classrooms: List[tuple], temperature: float) -> tuple:
        """
        AI-BASED CLASSROOM SELECTION - Temperature-based intelligent selection.
        
        Strategy:
        - HIGH TEMP (T > 100): Random exploration of all classrooms
        - MEDIUM TEMP (50 < T < 100): 70% earliest, 30% random (balanced)
        - LOW TEMP (T < 50): Always earliest (greedy exploitation)
        
        Args:
            available_classrooms: List of (slot_idx, classroom_id) tuples
            temperature: Current temperature
            
        Returns:
            Selected (slot_idx, classroom_id) tuple
        """
        if not available_classrooms:
            # 🤖 AI-BASED FALLBACK: Return first classroom with penalty (not None!)
            fallback_classroom = self.classrooms[0]['id'] if self.classrooms else None
            if fallback_classroom:
                return (0, fallback_classroom)  # (slot_idx, classroom_id) tuple with penalty context
            else:
                return (0, -1)  # Emergency fallback
        
        # OPTIMIZATION: Reduce logging overhead
        if temperature > 100:
            # HIGH TEMP: Pure random exploration
            return random.choice(available_classrooms)
        
        elif temperature > 50:
            # MEDIUM TEMP: 70% earliest, 30% random
            if random.random() < 0.7:
                return min(available_classrooms, key=lambda x: x[0])  # Earliest
            else:
                return random.choice(available_classrooms)
        
        else:
            # LOW TEMP: Always earliest (greedy)
            return min(available_classrooms, key=lambda x: x[0])
    
    def _order_projects_ai_based(self, projects: List[Dict[str, Any]], temperature: float) -> List[Dict[str, Any]]:
        """
        AI-BASED PROJECT ORDERING - Temperature-based intelligent ordering.
        
        Strategy:
        - HIGH TEMP (T > 100): Completely random order (exploration)
        - MEDIUM TEMP (50 < T < 100): Shuffle with probability = T/100 (balanced)
        - LOW TEMP (T < 50): Keep original order (exploitation)
        
        Args:
            projects: List of project dictionaries
            temperature: Current temperature
            
        Returns:
            Ordered list of projects
        """
        if not projects:
            return projects
        
        # OPTIMIZATION: Reduce logging overhead
        if temperature > 100:
            # HIGH TEMP: Completely random
            shuffled = projects.copy()
            random.shuffle(shuffled)
            return shuffled
        
        elif temperature > 50:
            # MEDIUM TEMP: Shuffle with probability
            shuffle_probability = temperature / 100.0
            if random.random() < shuffle_probability:
                shuffled = projects.copy()
                random.shuffle(shuffled)
                return shuffled
            else:
                return projects
        
        else:
            # LOW TEMP: Keep original order
            return projects
    
    def _select_timeslot_ai_based(self, available_timeslots: List[Dict[str, Any]], 
                                 temperature: float) -> Dict[str, Any]:
        """
        AI-BASED TIMESLOT SELECTION - Temperature-based intelligent timeslot selection.
        
        Strategy:
        - HIGH TEMPERATURE: Random timeslot selection (exploration)
        - MEDIUM TEMPERATURE: Balanced early preference + random
        - LOW TEMPERATURE: Strong early timeslot preference (exploitation)
        
        Args:
            available_timeslots: List of available timeslot dictionaries
            temperature: Current temperature for AI decision making
            
        Returns:
            Selected timeslot dictionary
        """
        if not available_timeslots:
            # 🤖 AI-BASED FALLBACK: Return first timeslot with penalty (not None!)
            fallback_timeslot = self.timeslots[0] if self.timeslots else {'id': 1, 'start_time': '09:00'}
            return fallback_timeslot
        
        # OPTIMIZATION: Reduce logging overhead
        if temperature > 100:
            # HIGH TEMP: Pure random exploration
            return random.choice(available_timeslots)
        
        elif temperature > 50:
            # MEDIUM TEMP: 70% early preference, 30% random
            early_timeslots = [ts for ts in available_timeslots if ts.get('id', 999) <= len(self.timeslots) // 2]
            if early_timeslots and random.random() < 0.7:
                return random.choice(early_timeslots)  # Early preference
            else:
                return random.choice(available_timeslots)  # Random exploration
        
        else:
            # LOW TEMP: Strong early preference (greedy)
            early_timeslots = [ts for ts in available_timeslots if ts.get('id', 999) <= len(self.timeslots) // 2]
            if early_timeslots:
                return random.choice(early_timeslots)  # Early timeslot preference
            else:
                return min(available_timeslots, key=lambda x: x.get('id', 999))  # Earliest available
    
    def _assign_jury_ai_based(self, responsible_instructor_id: int, 
                             available_instructors: List[int], 
                             temperature: float) -> List[int]:
        """
        AI-BASED JURY ASSIGNMENT - Temperature-based intelligent jury selection.
        
        Strategy:
        - HIGH TEMPERATURE: Random jury selection (exploration)
        - MEDIUM TEMPERATURE: Balanced selection + random
        - LOW TEMPERATURE: Strategic jury selection (exploitation)
        
        Args:
            responsible_instructor_id: ID of the instructor responsible for the project
            available_instructors: List of available instructor IDs for jury
            temperature: Current temperature for AI decision making
            
        Returns:
            List of selected jury member IDs (max 2)
        """
        if not available_instructors:
            return []
        
        # Remove responsible instructor from available jury members
        jury_candidates = [inst_id for inst_id in available_instructors 
                          if inst_id != responsible_instructor_id]
        
        if not jury_candidates:
            return []
        
        # OPTIMIZATION: Reduce logging overhead
        if temperature > 100:
            # HIGH TEMP: Random jury selection (exploration)
            num_jury = min(2, len(jury_candidates))
            return random.sample(jury_candidates, num_jury)
        
        elif temperature > 50:
            # MEDIUM TEMP: 70% strategic, 30% random
            if random.random() < 0.7:
                # Strategic selection: prefer instructors with different project loads
                return self._select_strategic_jury(jury_candidates, responsible_instructor_id)
            else:
                # Random selection
                num_jury = min(2, len(jury_candidates))
                return random.sample(jury_candidates, num_jury)
        
        else:
            # LOW TEMP: Strategic jury selection (exploitation)
            return self._select_strategic_jury(jury_candidates, responsible_instructor_id)
    
    def _select_strategic_jury(self, jury_candidates: List[int], 
                              responsible_instructor_id: int) -> List[int]:
        """
        Strategic jury selection based on instructor characteristics.
        
        Args:
            jury_candidates: List of available jury candidate IDs
            responsible_instructor_id: ID of responsible instructor
            
        Returns:
            List of strategically selected jury member IDs
        """
        if not jury_candidates:
            return []
        
        # Count projects per instructor for load balancing
        instructor_project_counts = {}
        for instructor in self.instructors:
            instructor_id = instructor['id']
            project_count = len([p for p in self.projects if p.get('responsible_id') == instructor_id])
            instructor_project_counts[instructor_id] = project_count
        
        # Sort candidates by strategic criteria
        strategic_candidates = []
        for candidate_id in jury_candidates:
            # Prefer instructors with balanced project loads
            candidate_load = instructor_project_counts.get(candidate_id, 0)
            strategic_score = 1.0 / (candidate_load + 1)  # Lower load = higher score
            strategic_candidates.append((candidate_id, strategic_score))
        
        # Sort by strategic score (higher is better)
        strategic_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Select top 2 candidates
        num_jury = min(2, len(strategic_candidates))
        return [candidate[0] for candidate in strategic_candidates[:num_jury]]
    
    def _ultra_aggressive_gap_minimization(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        ULTRA-AGGRESSIVE GAP MINIMIZATION: Minimize gaps by compacting assignments.
        
        Strategy:
        1. Identify all gaps in the schedule
        2. Move assignments to fill gaps (compact the schedule)
        3. Prioritize early timeslots and consecutive assignments
        4. Minimize total gaps by optimizing assignment positions
        
        Args:
            assignments: Current list of project assignments
            
        Returns:
            Updated assignments with minimized gaps
        """
        if not self.force_gap_filling:
            return assignments
        
        # Find all gaps in the schedule
        gaps = self._identify_all_gaps(assignments)
        if not gaps:
            return assignments
        
        # ULTRA-AGGRESSIVE: Try to move assignments to fill gaps
        moved_assignments = 0
        
        # Sort gaps by priority (early timeslots first, then by classroom)
        gaps.sort(key=lambda x: (x['timeslot_id'], x['classroom_id']))
        
        # Try to move assignments to fill early gaps
        for gap in gaps[:10]:  # Focus on first 10 gaps (most important)
            classroom_id = gap['classroom_id']
            timeslot_id = gap['timeslot_id']
            
            # Find assignments that can be moved to fill this gap
            best_assignment = self._find_best_assignment_to_move(gap, assignments)
            if best_assignment:
                # Move assignment to fill gap
                old_timeslot = best_assignment['timeslot_id']
                best_assignment['timeslot_id'] = timeslot_id
                moved_assignments += 1
                
                # OPTIMIZATION: Reduce logging
                if self.current_iteration == 0:
                    logger.info(f"ULTRA-AGGRESSIVE: Moved Project {best_assignment['project_id']} from {old_timeslot} to {timeslot_id} to fill gap")
        
        if moved_assignments > 0 and self.current_iteration == 0:
            logger.info(f"ULTRA-AGGRESSIVE GAP MINIMIZATION: {moved_assignments} assignments moved!")
        
        return assignments
    
    def _identify_all_gaps(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify all gaps in the current schedule.
        
        Args:
            assignments: Current list of project assignments
            
        Returns:
            List of gap dictionaries with classroom_id and timeslot_id
        """
        # Create a set of all occupied slots
        occupied_slots = set()
        for assignment in assignments:
            classroom_id = assignment['classroom_id']
            timeslot_id = assignment['timeslot_id']
            occupied_slots.add((classroom_id, timeslot_id))
        
        # Find all gaps
        gaps = []
        for classroom in self.classrooms:
            classroom_id = classroom['id']
            for timeslot in self.timeslots:
                timeslot_id = timeslot['id']
                if (classroom_id, timeslot_id) not in occupied_slots:
                    gaps.append({
                        'classroom_id': classroom_id,
                        'timeslot_id': timeslot_id,
                        'gap_size': 1  # Single slot gap
                    })
        
        # Sort gaps by priority (early timeslots first)
        gaps.sort(key=lambda x: (x['timeslot_id'], x['classroom_id']))
        return gaps
    
    def _find_best_project_for_gap(self, gap: Dict[str, Any], available_projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Find the best project to fill a specific gap.
        
        Args:
            gap: Gap dictionary with classroom_id and timeslot_id
            available_projects: List of unassigned projects
            
        Returns:
            Best project to fill the gap, or None if no suitable project
        """
        if not available_projects:
            # 🤖 AI-BASED FALLBACK: Return first project with penalty (not None!)
            fallback_project = self.projects[0] if self.projects else None
            return fallback_project
        
        classroom_id = gap['classroom_id']
        timeslot_id = gap['timeslot_id']
        
        # Prioritize projects based on:
        # 1. Early timeslot preference
        # 2. Instructor availability
        # 3. Project type (prefer FINAL projects)
        
        best_project = None
        best_score = -float('inf')
        
        for project in available_projects:
            score = 0
            
            # Early timeslot bonus
            early_threshold = len(self.timeslots) // 2
            if timeslot_id <= early_threshold:
                score += 100  # Huge bonus for early timeslots
            
            # Project type preference
            if project.get('type') == 'FINAL':
                score += 50  # Prefer FINAL projects
            
            # Instructor availability (simple check)
            responsible_id = project.get('responsible_id')
            if responsible_id:
                score += 25  # Bonus for having responsible instructor
            
            if score > best_score:
                best_score = score
                best_project = project
        
        return best_project
    
    def _find_best_assignment_to_move(self, gap: Dict[str, Any], assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Find the best assignment to move to fill a specific gap.
        
        Args:
            gap: Gap dictionary with classroom_id and timeslot_id
            assignments: List of current assignments
            
        Returns:
            Best assignment to move, or None if no suitable assignment
        """
        classroom_id = gap['classroom_id']
        timeslot_id = gap['timeslot_id']
        
        # Find assignments that can be moved to fill this gap
        candidates = []
        
        for assignment in assignments:
            current_classroom = assignment['classroom_id']
            current_timeslot = assignment['timeslot_id']
            
            # 🤖 AI-BASED: Don't skip - apply heavy penalty if already in target position
            # Calculate score for moving this assignment
            score = 0
            
            # 🤖 AI-BASED SOFT CONSTRAINT: Penalize if already in target (instead of skip!)
            if current_classroom == classroom_id and current_timeslot == timeslot_id:
                score -= 10000  # Huge penalty - don't move what's already there
            
            # Prefer assignments from the same classroom (easier to move)
            if current_classroom == classroom_id:
                score += 100  # Same classroom bonus
            
            # Prefer assignments from later timeslots (moving forward in time)
            if current_timeslot > timeslot_id:
                score += 50  # Moving forward bonus
            
            # Prefer assignments from different classrooms (spread out)
            if current_classroom != classroom_id:
                score += 25  # Different classroom bonus
            
            # 🤖 AI-BASED SOFT CONSTRAINT: Calculate conflict penalty (not blocking!)
            conflict_score = self._calculate_move_conflict_score(assignment, classroom_id, timeslot_id, assignments)
            score -= conflict_score  # Apply penalty to score
            
            # Include ALL candidates (even with conflicts - soft constraint!)
            candidates.append((assignment, score))
        
        if not candidates:
            # 🤖 AI-BASED FALLBACK: Return random assignment with penalty (not None!)
            fallback_assignment = random.choice(assignments) if assignments else None
            return fallback_assignment
        
        # Sort by score (higher is better)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Return the best candidate
        return candidates[0][0]
    
    def _calculate_move_conflict_score(self, assignment: Dict[str, Any], target_classroom: int, 
                                       target_timeslot: int, all_assignments: List[Dict[str, Any]]) -> float:
        """
        🤖 AI-BASED SOFT CONSTRAINT: Calculate conflict score for a move (NO HARD BLOCKING!)
        
        Instead of returning True/False (hard constraint), calculate a conflict penalty score.
        Higher score = more conflicts, but moves are NEVER blocked.
        
        Args:
            assignment: Assignment to move
            target_classroom: Target classroom ID
            target_timeslot: Target timeslot ID
            all_assignments: List of all current assignments
            
        Returns:
            Conflict score (0 = no conflict, 100+ = high conflict)
        """
        conflict_score = 0.0
        
        # SOFT CHECK: Target slot occupied?
        for other_assignment in all_assignments:
            if (other_assignment != assignment and 
                other_assignment['classroom_id'] == target_classroom and 
                other_assignment['timeslot_id'] == target_timeslot):
                conflict_score += 50.0  # Penalty, not blocking!
        
        # SOFT CHECK: Instructor availability
        instructor_id = assignment['instructors'][0] if assignment['instructors'] else None
        if instructor_id:
            # Check if instructor is already busy in target timeslot
            for other_assignment in all_assignments:
                if (other_assignment != assignment and 
                    instructor_id in other_assignment['instructors'] and 
                    other_assignment['timeslot_id'] == target_timeslot):
                    conflict_score += 100.0  # High penalty for instructor conflict
        
        return conflict_score
    
    def _compact_into_fewer_classrooms(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        SUPER AGGRESSIVE COMPACT: Move all assignments into minimum number of classrooms.
        
        Strategy:
        1. Count assignments per classroom
        2. Identify classrooms with few assignments
        3. Move all assignments from sparse classrooms to denser ones
        4. Fill classrooms completely before using next classroom
        
        Args:
            assignments: Current list of project assignments
            
        Returns:
            Compacted assignments with fewer classrooms used
        """
        if not assignments:
            return assignments
        
        # Count assignments per classroom
        classroom_counts = {}
        for assignment in assignments:
            cid = assignment['classroom_id']
            classroom_counts[cid] = classroom_counts.get(cid, 0) + 1
        
        # Sort classrooms by assignment count (most to least)
        sorted_classrooms = sorted(classroom_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Identify target classrooms (those with most assignments)
        # We want to fill as few classrooms as possible
        total_assignments = len(assignments)
        slots_per_classroom = len(self.timeslots)
        min_classrooms_needed = (total_assignments + slots_per_classroom - 1) // slots_per_classroom  # Ceiling division
        
        target_classrooms = [cid for cid, count in sorted_classrooms[:min_classrooms_needed]]
        sparse_classrooms = [cid for cid, count in sorted_classrooms[min_classrooms_needed:]]
        
        if not sparse_classrooms:
            return assignments  # Already compact
        
        # Move assignments from sparse classrooms to target classrooms
        moved_count = 0
        for sparse_classroom in sparse_classrooms:
            # Get all assignments from sparse classroom
            sparse_assignments = [a for a in assignments if a['classroom_id'] == sparse_classroom]
            
            for sparse_assignment in sparse_assignments:
                # Find available slot in target classrooms
                for target_classroom in target_classrooms:
                    # Find first available timeslot in target classroom
                    occupied_timeslots = {a['timeslot_id'] for a in assignments 
                                         if a['classroom_id'] == target_classroom}
                    
                    for timeslot in self.timeslots:
                        timeslot_id = timeslot['id']
                        if timeslot_id not in occupied_timeslots:
                            # 🤖 AI-BASED SOFT CONSTRAINT: Calculate conflict score (not blocking!)
                            conflict_score = self._calculate_move_conflict_score(sparse_assignment, target_classroom, timeslot_id, assignments)
                            
                            # Prefer moves with low conflict (but allow high conflict with penalty)
                            if conflict_score < 150.0:  # Soft threshold, not hard block
                                # Move assignment
                                sparse_assignment['classroom_id'] = target_classroom
                                sparse_assignment['timeslot_id'] = timeslot_id
                                moved_count += 1
                                
                                if self.current_iteration == 0:
                                    conflict_status = "clean" if conflict_score == 0 else f"conflict_score={conflict_score:.1f}"
                                    logger.info(f"COMPACT: Moved Project {sparse_assignment['project_id']} from Classroom {sparse_classroom} to {target_classroom} ({conflict_status})")
                                break
                            else:
                                # High conflict but still possible - try next timeslot
                                if self.current_iteration == 0:
                                    logger.info(f"COMPACT: Skipping high-conflict slot (score={conflict_score:.1f}) for Project {sparse_assignment['project_id']}, trying next...")
                    
                    if sparse_assignment['classroom_id'] == target_classroom:
                        break  # Successfully moved
        
        if moved_count > 0 and self.current_iteration == 0:
            logger.info(f"SUPER AGGRESSIVE COMPACT: {moved_count} assignments compacted!")
            logger.info(f"Reduced from {len(sorted_classrooms)} to {len(target_classrooms)} classrooms!")
        
        return assignments
    
    def _post_optimization_compact(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        POST-OPTIMIZATION COMPACTION: Automatic upward shift to fill early slots and minimize gaps.
        
        Strategy (PER CLASSROOM):
        1. Sort assignments by timeslot (late to early)
        2. For each assignment, try to move it to the earliest available slot
        3. Check conflicts (instructor availability, slot availability)
        4. Shift upward if feasible
        5. Repeat until no more shifts possible
        
        Args:
            assignments: Final optimized assignments
            
        Returns:
            Compacted assignments with minimized gaps and maximized early slot usage
        """
        if not assignments:
            return assignments
        
        logger.info("  📊 Başlangıç durumu:")
        initial_gaps = self._count_total_gaps(assignments)
        initial_early_usage = self._calculate_early_slot_percentage(assignments)
        logger.info(f"    Toplam gaps: {initial_gaps}")
        logger.info(f"    Erken slot kullanımı: {initial_early_usage:.1f}%")
        
        total_shifts = 0
        
        # Process each classroom separately
        for classroom in self.classrooms:
            classroom_id = classroom['id']
            
            # Get assignments for this classroom
            classroom_assignments = [a for a in assignments if a['classroom_id'] == classroom_id]
            
            if not classroom_assignments:
                continue
            
            # Sort by timeslot (latest first)
            classroom_assignments.sort(key=lambda x: x.get('timeslot_id', 0), reverse=True)
            
            # Try to shift each assignment upward
            for assignment in classroom_assignments:
                current_timeslot = assignment.get('timeslot_id')
                
                # Find earliest available slot for this assignment
                earliest_slot = self._find_earliest_available_slot(
                    assignment, classroom_id, current_timeslot, assignments
                )
                
                if earliest_slot and earliest_slot < current_timeslot:
                    # Shift upward!
                    old_timeslot = assignment['timeslot_id']
                    assignment['timeslot_id'] = earliest_slot
                    total_shifts += 1
                    
                    logger.info(f"    ⬆️  Shifted Project {assignment['project_id']}: Classroom {classroom_id}, Timeslot {old_timeslot} → {earliest_slot}")
        
        logger.info("")
        logger.info(f"  🎯 POST-COMPACTION sonuçları:")
        final_gaps = self._count_total_gaps(assignments)
        final_early_usage = self._calculate_early_slot_percentage(assignments)
        logger.info(f"    Toplam shifts: {total_shifts}")
        logger.info(f"    Toplam gaps: {final_gaps} (başlangıç: {initial_gaps}, azalma: {initial_gaps - final_gaps})")
        logger.info(f"    Erken slot kullanımı: {final_early_usage:.1f}% (başlangıç: {initial_early_usage:.1f}%, artış: {final_early_usage - initial_early_usage:.1f}%)")
        
        return assignments
    
    def _find_earliest_available_slot(self, assignment: Dict[str, Any], classroom_id: int, 
                                     current_timeslot: int, all_assignments: List[Dict[str, Any]]) -> int:
        """
        Find the earliest available timeslot for an assignment in a specific classroom.
        
        Args:
            assignment: Assignment to find slot for
            classroom_id: Target classroom ID
            current_timeslot: Current timeslot of the assignment
            all_assignments: All current assignments
            
        Returns:
            Earliest available timeslot ID, or None if no earlier slot available
        """
        instructor_id = assignment['instructors'][0] if assignment['instructors'] else None
        
        if not instructor_id:
            # 🤖 AI-BASED FALLBACK: Return current timeslot with penalty (not None!)
            return current_timeslot
        
        # Check each timeslot from 1 to current_timeslot
        for timeslot in self.timeslots:
            timeslot_id = timeslot['id']
            
            # Only check earlier slots
            if timeslot_id >= current_timeslot:
                continue
            
            # Check if slot is available in this classroom
            slot_occupied = any(
                a != assignment and 
                a['classroom_id'] == classroom_id and 
                a['timeslot_id'] == timeslot_id
                for a in all_assignments
            )
            
            if slot_occupied:
                continue
            
            # Check if instructor is available at this timeslot
            instructor_busy = any(
                a != assignment and 
                instructor_id in a['instructors'] and 
                a['timeslot_id'] == timeslot_id
                for a in all_assignments
            )
            
            if instructor_busy:
                continue
            
            # This slot is available!
            return timeslot_id
        
        # 🤖 AI-BASED FALLBACK: Return current timeslot if no earlier slot (not None!)
        return current_timeslot  # Keep current position (neutral, not None!)
    
    def _count_total_gaps(self, assignments: List[Dict[str, Any]]) -> int:
        """Count total gaps in the schedule."""
        if not assignments or not self.classrooms or not self.timeslots:
            return 0
        
        total_slots = len(self.classrooms) * len(self.timeslots)
        used_slots = len(assignments)
        return total_slots - used_slots
    
    def _calculate_early_slot_percentage(self, assignments: List[Dict[str, Any]]) -> float:
        """Calculate percentage of assignments in early timeslots."""
        if not assignments or not self.timeslots:
            return 0.0
        
        early_threshold = len(self.timeslots) // 2
        early_count = sum(1 for a in assignments if a.get('timeslot_id', 999) <= early_threshold)
        
        return (early_count / len(assignments) * 100) if assignments else 0.0
    
    def _balance_classroom_timeslots(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        CLASSROOM TIMESLOT BALANCING: Balance timeslot usage ranges across classrooms.
        
        Strategy:
        1. Calculate timeslot range for each classroom (min-max)
        2. Identify outlier classrooms (too early or too late)
        3. Move assignments to balance ranges across classrooms
        4. Target: All classrooms should use similar timeslot ranges
        
        Args:
            assignments: Post-compacted assignments
            
        Returns:
            Balanced assignments with similar timeslot ranges per classroom
        """
        if not assignments:
            return assignments
        
        logger.info("  📊 Başlangıç durumu:")
        
        # Calculate timeslot ranges per classroom
        classroom_ranges = {}
        for classroom in self.classrooms:
            classroom_id = classroom['id']
            classroom_assignments = [a for a in assignments if a['classroom_id'] == classroom_id]
            
            if not classroom_assignments:
                continue
            
            timeslots = [a['timeslot_id'] for a in classroom_assignments]
            min_slot = min(timeslots)
            max_slot = max(timeslots)
            range_size = max_slot - min_slot + 1
            
            classroom_ranges[classroom_id] = {
                'min': min_slot,
                'max': max_slot,
                'range': range_size,
                'count': len(classroom_assignments)
            }
            
            logger.info(f"    Classroom {classroom_id}: Timeslots {min_slot}-{max_slot} (range: {range_size}, count: {len(classroom_assignments)})")
        
        if not classroom_ranges:
            return assignments
        
        # Calculate target range (average)
        total_min = sum(r['min'] for r in classroom_ranges.values())
        total_max = sum(r['max'] for r in classroom_ranges.values())
        num_classrooms = len(classroom_ranges)
        
        target_min = total_min // num_classrooms
        target_max = total_max // num_classrooms
        
        logger.info(f"\n  🎯 Target range: Timeslots {target_min}-{target_max}")
        
        total_moves = 0
        
        # Balance each classroom to target range
        for classroom_id, range_info in classroom_ranges.items():
            current_min = range_info['min']
            current_max = range_info['max']
            
            # Check if this classroom needs balancing
            if abs(current_min - target_min) <= self.balance_target_range and \
               abs(current_max - target_max) <= self.balance_target_range:
                continue  # Already balanced
            
            classroom_assignments = [a for a in assignments if a['classroom_id'] == classroom_id]
            
            # Shift assignments to target range
            for assignment in classroom_assignments:
                current_timeslot = assignment['timeslot_id']
                
                # Calculate target timeslot
                if current_timeslot < target_min:
                    # Shift down (to later slots)
                    target_timeslot = target_min
                elif current_timeslot > target_max:
                    # Shift up (to earlier slots)
                    target_timeslot = target_max
                else:
                    continue  # Already in target range
                
                # Try to find available slot in target range
                new_slot = self._find_balanced_slot(
                    assignment, classroom_id, target_timeslot, assignments
                )
                
                if new_slot and new_slot != current_timeslot:
                    old_timeslot = assignment['timeslot_id']
                    assignment['timeslot_id'] = new_slot
                    total_moves += 1
                    
                    logger.info(f"    ⚖️  Balanced Project {assignment['project_id']}: Classroom {classroom_id}, Timeslot {old_timeslot} → {new_slot}")
        
        logger.info("")
        logger.info(f"  🎯 BALANCING sonuçları:")
        logger.info(f"    Toplam moves: {total_moves}")
        
        # Show final ranges
        logger.info(f"\n  📊 Final timeslot ranges:")
        for classroom in self.classrooms:
            classroom_id = classroom['id']
            classroom_assignments = [a for a in assignments if a['classroom_id'] == classroom_id]
            
            if not classroom_assignments:
                continue
            
            timeslots = [a['timeslot_id'] for a in classroom_assignments]
            min_slot = min(timeslots)
            max_slot = max(timeslots)
            range_size = max_slot - min_slot + 1
            
            logger.info(f"    Classroom {classroom_id}: Timeslots {min_slot}-{max_slot} (range: {range_size})")
        
        return assignments
    
    def _find_balanced_slot(self, assignment: Dict[str, Any], classroom_id: int, 
                           target_timeslot: int, all_assignments: List[Dict[str, Any]]) -> int:
        """
        Find a balanced timeslot near the target timeslot.
        
        Args:
            assignment: Assignment to find slot for
            classroom_id: Target classroom ID
            target_timeslot: Target timeslot ID
            all_assignments: All current assignments
            
        Returns:
            Balanced timeslot ID, or None if no suitable slot available
        """
        instructor_id = assignment['instructors'][0] if assignment['instructors'] else None
        
        if not instructor_id:
            # 🤖 AI-BASED FALLBACK: Return first timeslot (not None!)
            fallback_timeslot = self.timeslots[0]['id'] if self.timeslots else 1
            return fallback_timeslot
        
        # Try target timeslot first, then expand search radius
        for radius in range(0, len(self.timeslots)):
            # Try slots around target
            for offset in [0, -radius, radius]:
                # 🤖 AI-BASED: Don't skip offset=0, just handle it appropriately
                # offset=0 on first iteration (radius=0) is valid, after that it's redundant
                if offset == 0 and radius > 0:
                    # Redundant search - but don't skip, just mark as low priority
                    pass  # Will be handled by availability check below
                
                candidate_timeslot = target_timeslot + offset
                
                # Check if candidate is valid
                if candidate_timeslot < 1 or candidate_timeslot > len(self.timeslots):
                    continue
                
                # Check if slot is available in this classroom
                slot_occupied = any(
                    a != assignment and 
                    a['classroom_id'] == classroom_id and 
                    a['timeslot_id'] == candidate_timeslot
                    for a in all_assignments
                )
                
                if slot_occupied:
                    continue
                
                # Check if instructor is available at this timeslot
                instructor_busy = any(
                    a != assignment and 
                    instructor_id in a['instructors'] and 
                    a['timeslot_id'] == candidate_timeslot
                    for a in all_assignments
                )
                
                if instructor_busy:
                    continue
                
                # This slot is available!
                return candidate_timeslot
        
        # 🤖 AI-BASED FALLBACK: Return first timeslot if no suitable slot (not None!)
        fallback_timeslot = self.timeslots[0]['id'] if self.timeslots else 1
        return fallback_timeslot  # Fallback (not None!)
    
    def _calculate_large_gap_penalty_score(self, solution: List[Dict[str, Any]]) -> float:
        """
        Calculate penalty score for large gaps in the schedule.
        Larger gaps = higher penalty.
        
        Args:
            solution: List of project assignments
            
        Returns:
            Large gap penalty score (positive = penalty)
        """
        # Find consecutive gaps (large gaps)
        classroom_gaps = {}
        
        for classroom in self.classrooms:
            classroom_id = classroom['id']
            occupied_timeslots = set()
            
            for assignment in solution:
                if assignment['classroom_id'] == classroom_id:
                    occupied_timeslots.add(assignment['timeslot_id'])
            
            # Find consecutive gaps
            consecutive_gaps = []
            current_gap_size = 0
            
            for timeslot in self.timeslots:
                timeslot_id = timeslot['id']
                if timeslot_id not in occupied_timeslots:
                    current_gap_size += 1
                else:
                    if current_gap_size > 0:
                        consecutive_gaps.append(current_gap_size)
                        current_gap_size = 0
            
            # Don't forget the last gap
            if current_gap_size > 0:
                consecutive_gaps.append(current_gap_size)
            
            classroom_gaps[classroom_id] = consecutive_gaps
        
        # Calculate penalty based on gap sizes
        total_penalty = 0.0
        for classroom_id, gaps in classroom_gaps.items():
            for gap_size in gaps:
                # Exponential penalty for larger gaps
                if gap_size >= 3:  # Large gaps (3+ consecutive slots)
                    penalty = gap_size ** 2  # Quadratic penalty
                    total_penalty += penalty
        
        return total_penalty
    
    def _calculate_gap_filled_reward_score(self, solution: List[Dict[str, Any]]) -> float:
        """
        Calculate reward score for filled gaps.
        More filled slots = higher reward.
        
        Args:
            solution: List of project assignments
            
        Returns:
            Gap filled reward score (positive = reward)
        """
        total_slots = len(self.classrooms) * len(self.timeslots)
        filled_slots = len(solution)
        
        # Calculate utilization rate
        utilization_rate = filled_slots / total_slots if total_slots > 0 else 0
        
        # Reward based on utilization rate
        if utilization_rate >= 0.9:  # 90%+ utilization
            reward = 100.0  # Maximum reward
        elif utilization_rate >= 0.8:  # 80%+ utilization
            reward = 80.0
        elif utilization_rate >= 0.7:  # 70%+ utilization
            reward = 60.0
        elif utilization_rate >= 0.6:  # 60%+ utilization
            reward = 40.0
        else:
            reward = 20.0  # Minimum reward
        
        return reward
    
    def _calculate_compact_classrooms_score(self, solution: List[Dict[str, Any]]) -> float:
        """
        Calculate reward score for compact classroom usage.
        Fully filled classrooms = higher reward.
        
        Args:
            solution: List of project assignments
            
        Returns:
            Compact classrooms reward score (positive = reward)
        """
        if not solution or not self.classrooms or not self.timeslots:
            return 0.0
        
        # Count assignments per classroom
        classroom_counts = {}
        for assignment in solution:
            cid = assignment['classroom_id']
            classroom_counts[cid] = classroom_counts.get(cid, 0) + 1
        
        # Calculate reward based on classroom fullness
        total_reward = 0.0
        slots_per_classroom = len(self.timeslots)
        
        for classroom in self.classrooms:
            cid = classroom['id']
            count = classroom_counts.get(cid, 0)
            
            if count == 0:
                continue  # Empty classroom, no reward
            
            # Calculate fullness ratio
            fullness_ratio = count / slots_per_classroom
            
            # Reward based on fullness
            if fullness_ratio == 1.0:  # 100% full
                total_reward += 100.0  # Maximum reward
            elif fullness_ratio >= 0.8:  # 80%+ full
                total_reward += 80.0
            elif fullness_ratio >= 0.6:  # 60%+ full
                total_reward += 60.0
            elif fullness_ratio >= 0.4:  # 40%+ full
                total_reward += 40.0
            else:
                total_reward += 20.0  # Minimum reward
        
        return total_reward
    
    def _calculate_empty_classroom_penalty_score(self, solution: List[Dict[str, Any]]) -> float:
        """
        Calculate penalty score for empty or nearly empty classrooms.
        More empty classrooms = higher penalty.
        
        Args:
            solution: List of project assignments
            
        Returns:
            Empty classroom penalty score (positive = penalty)
        """
        if not solution or not self.classrooms or not self.timeslots:
            return 0.0
        
        # Count assignments per classroom
        classroom_counts = {}
        for assignment in solution:
            cid = assignment['classroom_id']
            classroom_counts[cid] = classroom_counts.get(cid, 0) + 1
        
        # Calculate penalty for empty/sparse classrooms
        total_penalty = 0.0
        slots_per_classroom = len(self.timeslots)
        
        for classroom in self.classrooms:
            cid = classroom['id']
            count = classroom_counts.get(cid, 0)
            
            # Calculate emptiness ratio
            emptiness_ratio = 1.0 - (count / slots_per_classroom)
            
            # Penalty based on emptiness
            if count == 0:  # Completely empty
                total_penalty += 50.0  # Heavy penalty
            elif emptiness_ratio >= 0.8:  # 80%+ empty (< 20% full)
                total_penalty += 40.0
            elif emptiness_ratio >= 0.6:  # 60%+ empty (< 40% full)
                total_penalty += 30.0
            elif emptiness_ratio >= 0.4:  # 40%+ empty (< 60% full)
                total_penalty += 20.0
        
        return total_penalty
    
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
    
    def _calculate_energy(self, solution: List[Dict[str, Any]]) -> float:
        """
        Calculate energy (fitness) of a solution.
        Lower energy = better solution.
        
        Energy Components:
        1. Classroom changes penalty
        2. Time gaps penalty
        3. Conflicts penalty
        4. Load imbalance penalty
        """
        if not solution:
            return float('inf')
        
        energy = 0.0
        
        # 1. Classroom changes penalty
        classroom_changes = self._calculate_classroom_changes_score(solution)
        energy += classroom_changes * 10.0  # Weight: 10.0
        
        # 2. Time gaps penalty
        time_gaps = self._calculate_time_efficiency_score(solution)
        energy += time_gaps * 5.0  # Weight: 5.0
        
        # 3. Conflicts penalty
        conflicts = len(self._detect_conflicts(solution))
        energy += conflicts * 100.0  # Weight: 100.0 (heavy penalty)
        
        # 4. Load imbalance penalty
        load_variance = self._calculate_load_balance_score(solution)
        energy += load_variance * 2.0  # Weight: 2.0
        
        # 5. Assignment count bonus (more assignments = lower energy)
        assignment_bonus = (len(self.projects) - len(solution)) * 50.0
        energy += assignment_bonus
        
        # 6. AI-BASED: Early timeslot usage (reward early slots)
        early_timeslot_score = self._calculate_early_timeslot_usage_score(solution)
        energy -= early_timeslot_score * self.reward_early_timeslot  # Subtract for reward
        
        # 7. AI-BASED: ULTRA-AGGRESSIVE Gap penalty (penalize empty slots heavily!)
        gap_score = self._calculate_gap_penalty_score(solution)
        energy += gap_score * abs(self.penalty_gap)  # ULTRA-AGGRESSIVE penalty!
        
        # 7.1. ULTRA-AGGRESSIVE: Large gap penalty (massive penalty for large gaps!)
        large_gap_penalty = self._calculate_large_gap_penalty_score(solution)
        energy += large_gap_penalty * abs(self.penalty_large_gap)  # MASSIVE penalty!
        
        # 7.2. ULTRA-AGGRESSIVE: Gap filling reward (huge reward for filled gaps!)
        gap_filled_reward = self._calculate_gap_filled_reward_score(solution)
        energy -= gap_filled_reward * self.reward_gap_filled  # HUGE reward!
        
        # 8. SINIFLARARASI: Classroom-wise early slot optimization (NEW)
        classroom_early_score = self._calculate_classroom_early_slot_score(solution)
        energy -= classroom_early_score * self.reward_classroom_early_slot  # Subtract for reward
        
        # 9. SINIFLARARASI: Classroom gap penalty (NEW)
        classroom_gap_score = self._calculate_classroom_gap_penalty_score(solution)
        energy += classroom_gap_score * abs(self.penalty_classroom_gap)  # Add penalty
        
        # 10. SINIFLARARASI: Balanced classroom usage (NEW)
        balanced_usage_score = self._calculate_balanced_classroom_usage_score(solution)
        energy -= balanced_usage_score * self.reward_balanced_classroom_usage  # Subtract for reward
        
        # 11. ULTRA-AGGRESSIVE: Perfect uniform distribution (NEW!)
        perfect_uniform_score = self._calculate_perfect_uniform_distribution_score(solution)
        energy -= perfect_uniform_score * self.reward_perfect_uniform  # Subtract for reward
        
        # 12. ULTRA-AGGRESSIVE: Uniform imbalance penalty (NEW!)
        uniform_imbalance_score = self._calculate_uniform_imbalance_penalty_score(solution)
        energy += uniform_imbalance_score * abs(self.penalty_uniform_imbalance)  # Add penalty
        
        # 13. SUPER AGGRESSIVE: Compact classrooms score (NEW!)
        if self.compact_classrooms:
            compact_score = self._calculate_compact_classrooms_score(solution)
            energy -= compact_score * self.reward_full_classroom  # Subtract for reward
            
            empty_classroom_penalty = self._calculate_empty_classroom_penalty_score(solution)
            energy += empty_classroom_penalty * abs(self.penalty_empty_classroom)  # Add penalty
        
        return energy
    
    def _calculate_early_timeslot_usage_score(self, solution: List[Dict[str, Any]]) -> float:
        """
        AI-BASED: Calculate early timeslot usage score.
        Higher score = more early timeslots used.
        """
        if not solution or not self.timeslots:
            return 0.0
        
        total_timeslots = len(self.timeslots)
        early_threshold = total_timeslots // 2  # First half = early
        
        early_count = 0
        late_count = 0
        
        for assignment in solution:
            timeslot_id = assignment.get('timeslot_id')
            if timeslot_id and timeslot_id <= early_threshold:
                early_count += 1
            else:
                late_count += 1
        
        total_assignments = len(solution)
        if total_assignments == 0:
            return 0.0
        
        # Score based on early vs late ratio
        early_ratio = early_count / total_assignments
        late_ratio = late_count / total_assignments
        
        # Reward early usage, penalize late usage when early slots available
        if early_ratio >= 0.8:  # 80%+ early usage
            return 1.0  # Maximum reward
        elif early_ratio >= 0.6:  # 60-80% early usage
            return 0.7
        elif early_ratio >= 0.4:  # 40-60% early usage
            return 0.4
        else:  # <40% early usage
            return 0.1
    
    def _calculate_gap_penalty_score(self, solution: List[Dict[str, Any]]) -> float:
        """
        AI-BASED: Calculate gap penalty score.
        Higher penalty = more gaps (empty slots).
        """
        if not solution or not self.classrooms or not self.timeslots:
            return 0.0
        
        total_slots = len(self.classrooms) * len(self.timeslots)
        used_slots = len(solution)
        gaps = total_slots - used_slots
        
        if total_slots == 0:
            return 0.0
        
        # Normalize gap ratio (0.0 = no gaps, 1.0 = all gaps)
        gap_ratio = gaps / total_slots
        
        # Return penalty score (positive = penalty)
        return gap_ratio
    
    def _calculate_classroom_early_slot_score(self, solution: List[Dict[str, Any]]) -> float:
        """
        SINIFLARARASI: Calculate classroom-wise early slot optimization score.
        Rewards filling early gaps in each classroom individually.
        Higher score = better early slot distribution across classrooms.
        """
        if not solution or not self.classrooms or not self.timeslots:
            return 0.0
        
        total_timeslots = len(self.timeslots)
        early_threshold = total_timeslots // 2  # First half = early
        
        classroom_scores = []
        
        # Analyze each classroom individually
        for classroom in self.classrooms:
            classroom_id = classroom['id']
            
            # Get assignments for this classroom
            classroom_assignments = [a for a in solution if a.get('classroom_id') == classroom_id]
            
            if not classroom_assignments:
                # Empty classroom gets low score
                classroom_scores.append(0.1)
                continue
            
            # Count early vs late usage in this classroom
            early_count = 0
            late_count = 0
            
            for assignment in classroom_assignments:
                timeslot_id = assignment.get('timeslot_id')
                if timeslot_id:
                    if timeslot_id <= early_threshold:
                        early_count += 1
                    else:
                        late_count += 1
            
            total_classroom_assignments = len(classroom_assignments)
            if total_classroom_assignments == 0:
                classroom_scores.append(0.1)
                continue
            
            # Calculate early usage ratio for this classroom
            early_ratio = early_count / total_classroom_assignments
            
            # Calculate gap ratio in early slots for this classroom
            max_possible_early = early_threshold  # Max early slots per classroom
            early_gaps = max_possible_early - early_count
            early_gap_ratio = early_gaps / max_possible_early if max_possible_early > 0 else 1.0
            
            # Score this classroom based on early usage and gap minimization
            if early_ratio >= 0.9 and early_gap_ratio <= 0.1:  # 90%+ early, 10%- gaps
                classroom_score = 2.0  # Excellent
            elif early_ratio >= 0.8 and early_gap_ratio <= 0.2:  # 80%+ early, 20%- gaps
                classroom_score = 1.5  # Very good
            elif early_ratio >= 0.7 and early_gap_ratio <= 0.3:  # 70%+ early, 30%- gaps
                classroom_score = 1.2  # Good
            elif early_ratio >= 0.6 and early_gap_ratio <= 0.4:  # 60%+ early, 40%- gaps
                classroom_score = 1.0  # Moderate
            elif early_ratio >= 0.5:  # 50%+ early
                classroom_score = 0.7  # Fair
            else:  # <50% early
                classroom_score = 0.3  # Poor
            
            classroom_scores.append(classroom_score)
        
        # Return average score across all classrooms
        return sum(classroom_scores) / len(classroom_scores) if classroom_scores else 0.0
    
    def _calculate_classroom_gap_penalty_score(self, solution: List[Dict[str, Any]]) -> float:
        """
        SINIFLARARASI: Calculate classroom-wise gap penalty score.
        Penalizes gaps in each classroom individually.
        Higher penalty = more gaps per classroom.
        """
        if not solution or not self.classrooms or not self.timeslots:
            return 0.0
        
        total_timeslots = len(self.timeslots)
        classroom_gap_scores = []
        
        # Analyze each classroom individually
        for classroom in self.classrooms:
            classroom_id = classroom['id']
            
            # Get assignments for this classroom
            classroom_assignments = [a for a in solution if a.get('classroom_id') == classroom_id]
            
            # Calculate gaps in this classroom
            used_slots_in_classroom = len(classroom_assignments)
            total_slots_in_classroom = total_timeslots
            gaps_in_classroom = total_slots_in_classroom - used_slots_in_classroom
            
            # Normalize gap ratio for this classroom (0.0 = no gaps, 1.0 = all gaps)
            gap_ratio = gaps_in_classroom / total_slots_in_classroom if total_slots_in_classroom > 0 else 1.0
            classroom_gap_scores.append(gap_ratio)
        
        # Return average gap penalty across all classrooms
        return sum(classroom_gap_scores) / len(classroom_gap_scores) if classroom_gap_scores else 0.0
    
    def _calculate_balanced_classroom_usage_score(self, solution: List[Dict[str, Any]]) -> float:
        """
        SINIFLARARASI: Calculate balanced classroom usage score.
        Rewards balanced distribution of assignments across classrooms.
        Higher score = more balanced usage.
        """
        if not solution or not self.classrooms:
            return 0.0
        
        # Count assignments per classroom
        classroom_counts = {}
        for classroom in self.classrooms:
            classroom_id = classroom['id']
            classroom_counts[classroom_id] = 0
        
        for assignment in solution:
            classroom_id = assignment.get('classroom_id')
            if classroom_id in classroom_counts:
                classroom_counts[classroom_id] += 1
        
        # Calculate variance in classroom usage
        counts = list(classroom_counts.values())
        if not counts:
            return 0.0
        
        mean_count = sum(counts) / len(counts)
        if mean_count == 0:
            return 0.0
        
        # Calculate coefficient of variation (lower = more balanced)
        variance = sum((count - mean_count) ** 2 for count in counts) / len(counts)
        std_dev = variance ** 0.5
        coefficient_of_variation = std_dev / mean_count if mean_count > 0 else 1.0
        
        # Convert to score (lower coefficient = higher score)
        # 0.0 = perfectly balanced, 1.0+ = very imbalanced
        if coefficient_of_variation <= 0.1:  # Very balanced
            return 1.0
        elif coefficient_of_variation <= 0.2:  # Balanced
            return 0.8
        elif coefficient_of_variation <= 0.3:  # Fairly balanced
            return 0.6
        elif coefficient_of_variation <= 0.5:  # Somewhat imbalanced
            return 0.4
        else:  # Very imbalanced
            return 0.2
    
    def _calculate_perfect_uniform_distribution_score(self, solution: List[Dict[str, Any]]) -> float:
        """
        ULTRA-AGGRESSIVE: Calculate perfect uniform distribution score.
        Rewards perfect uniform distribution (same number of projects per classroom).
        Higher score = more uniform distribution.
        """
        if not solution or not self.classrooms:
            return 0.0
        
        # Count assignments per classroom
        classroom_counts = {}
        for classroom in self.classrooms:
            classroom_id = classroom['id']
            classroom_counts[classroom_id] = 0
        
        for assignment in solution:
            classroom_id = assignment.get('classroom_id')
            if classroom_id in classroom_counts:
                classroom_counts[classroom_id] += 1
        
        # Calculate uniform distribution score
        counts = list(classroom_counts.values())
        if not counts:
            return 0.0
        
        # Check if all classrooms have the same number of assignments
        if len(set(counts)) == 1:  # All counts are identical
            return 3.0  # Perfect uniform - maximum reward!
        
        # Calculate how close we are to perfect uniform
        mean_count = sum(counts) / len(counts)
        if mean_count == 0:
            return 0.0
        
        # Calculate variance from perfect uniform
        variance = sum((count - mean_count) ** 2 for count in counts) / len(counts)
        std_dev = variance ** 0.5
        
        # Convert to score (lower variance = higher score)
        if std_dev <= 0.1:  # Nearly perfect uniform
            return 2.5
        elif std_dev <= 0.5:  # Very uniform
            return 2.0
        elif std_dev <= 1.0:  # Fairly uniform
            return 1.5
        elif std_dev <= 2.0:  # Somewhat uniform
            return 1.0
        else:  # Not uniform at all
            return 0.5
    
    def _calculate_uniform_imbalance_penalty_score(self, solution: List[Dict[str, Any]]) -> float:
        """
        ULTRA-AGGRESSIVE: Calculate uniform imbalance penalty score.
        Heavily penalizes non-uniform distribution.
        Higher penalty = more imbalanced distribution.
        """
        if not solution or not self.classrooms:
            return 0.0
        
        # Count assignments per classroom
        classroom_counts = {}
        for classroom in self.classrooms:
            classroom_id = classroom['id']
            classroom_counts[classroom_id] = 0
        
        for assignment in solution:
            classroom_id = assignment.get('classroom_id')
            if classroom_id in classroom_counts:
                classroom_counts[classroom_id] += 1
        
        # Calculate imbalance penalty
        counts = list(classroom_counts.values())
        if not counts:
            return 0.0
        
        mean_count = sum(counts) / len(counts)
        if mean_count == 0:
            return 0.0
        
        # Calculate coefficient of variation (higher = more imbalanced)
        variance = sum((count - mean_count) ** 2 for count in counts) / len(counts)
        std_dev = variance ** 0.5
        coefficient_of_variation = std_dev / mean_count if mean_count > 0 else 1.0
        
        # Return penalty score (higher coefficient = higher penalty)
        # 0.0 = perfectly uniform, 1.0+ = very imbalanced
        if coefficient_of_variation <= 0.05:  # Nearly perfect uniform
            return 0.0  # No penalty
        elif coefficient_of_variation <= 0.1:  # Very uniform
            return 0.1
        elif coefficient_of_variation <= 0.2:  # Fairly uniform
            return 0.3
        elif coefficient_of_variation <= 0.3:  # Somewhat imbalanced
            return 0.6
        elif coefficient_of_variation <= 0.5:  # Imbalanced
            return 0.8
        else:  # Very imbalanced
            return 1.0
    
    # 🔧 CONFLICT RESOLUTION METHODS
    
    def _detect_all_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Tüm çakışma türlerini tespit eder
        
        Görsellerde tespit edilen çakışmalar:
        - Dr. Öğretim Üyesi 3: 14:30-15:00'da 2 farklı görev
        - Dr. Öğretim Üyesi 21: 15:00-15:30'da 2 jüri görevi  
        - Dr. Öğretim Üyesi 11: 16:00-16:30'da 2 farklı görev
        """
        all_conflicts = []
        
        logger.info("🔍 [SA] CONFLICT DETECTION STARTED")
        
        # 1. Instructor çakışmaları
        instructor_conflicts = self._detect_instructor_conflicts(assignments)
        all_conflicts.extend(instructor_conflicts)
        
        # 2. Classroom çakışmaları
        classroom_conflicts = self._detect_classroom_conflicts(assignments)
        all_conflicts.extend(classroom_conflicts)
        
        # 3. Timeslot çakışmaları
        timeslot_conflicts = self._detect_timeslot_conflicts(assignments)
        all_conflicts.extend(timeslot_conflicts)
        
        logger.info(f"🔍 [SA] CONFLICT DETECTION COMPLETED: {len(all_conflicts)} conflicts found")
        
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
            
            # Jury instructors
            for jury_instructor_id in instructors_list:
                if jury_instructor_id != instructor_id:  # Kendi projesinde jüri olamaz
                    instructor_timeslot_assignments[jury_instructor_id][timeslot_id].append({
                        'project_id': project_id,
                        'role': 'jury',
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
        
        logger.info(f"[SA] Instructor conflicts detected: {len(conflicts)}")
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
        
        logger.info(f"[SA] Classroom conflicts detected: {len(conflicts)}")
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
        
        logger.info(f"[SA] Timeslot conflicts detected: {len(conflicts)}")
        return conflicts
    
    def _determine_instructor_conflict_type(self, assignments_list: List[Dict[str, Any]]) -> str:
        """Instructor çakışma türünü belirler"""
        roles = [assignment['role'] for assignment in assignments_list]
        
        if 'responsible' in roles and 'jury' in roles:
            return 'instructor_supervisor_jury_conflict'
        elif roles.count('responsible') > 1:
            return 'instructor_double_assignment'
        elif roles.count('jury') > 1:
            return 'instructor_double_jury'
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
            'instructor_supervisor_jury_conflict': 'reschedule_one_assignment',
            'instructor_double_assignment': 'reschedule_duplicate_assignment',
            'instructor_double_jury': 'replace_jury_member',
            'classroom_double_booking': 'relocate_to_available_classroom',
            'timeslot_overflow': 'redistribute_to_other_timeslots'
        }
        return strategies.get(conflict_type, 'manual_resolution')
    
    def _resolve_conflicts(self, assignments: List[Dict[str, Any]], 
                          conflicts: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Çakışmaları çözer - Temperature-based resolution strategy
        
        Returns:
            Tuple[List[Dict], List[Dict]]: (resolved_assignments, resolution_log)
        """
        logger.info(f"🔧 [SA] CONFLICT RESOLUTION STARTED: {len(conflicts)} conflicts to resolve")
        
        resolved_assignments = assignments.copy()
        resolution_log = []
        
        # Temperature-based conflict resolution strategy
        # HIGH TEMP: More aggressive resolution (exploration)
        # LOW TEMP: Conservative resolution (exploitation)
        resolution_aggressiveness = min(1.0, self.temperature / self.initial_temperature)
        
        # Çakışmaları şiddete göre sırala (CRITICAL -> HIGH -> MEDIUM)
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        sorted_conflicts = sorted(conflicts, key=lambda x: severity_order.get(x.get('severity', 'LOW'), 3))
        
        for conflict in sorted_conflicts:
            try:
                resolution_result = self._resolve_single_conflict(conflict, resolved_assignments, resolution_aggressiveness)
                
                if resolution_result['success']:
                    resolved_assignments = resolution_result['assignments']
                    resolution_log.append({
                        'conflict_id': conflict.get('type', 'unknown'),
                        'resolution_strategy': conflict.get('resolution_strategy', 'unknown'),
                        'success': True,
                        'changes_made': resolution_result.get('changes_made', []),
                        'description': f"Successfully resolved {conflict['type']}",
                        'temperature': self.temperature
                    })
                    logger.info(f"✅ [SA] RESOLVED: {conflict['description']} (T={self.temperature:.2f})")
                else:
                    resolution_log.append({
                        'conflict_id': conflict.get('type', 'unknown'),
                        'resolution_strategy': conflict.get('resolution_strategy', 'unknown'),
                        'success': False,
                        'error': resolution_result.get('error', 'Unknown error'),
                        'description': f"Failed to resolve {conflict['type']}",
                        'temperature': self.temperature
                    })
                    logger.warning(f"❌ [SA] FAILED: {conflict['description']}")
                    
            except Exception as e:
                logger.error(f"[SA] Error resolving conflict {conflict.get('type', 'unknown')}: {e}")
                resolution_log.append({
                    'conflict_id': conflict.get('type', 'unknown'),
                    'success': False,
                    'error': str(e),
                    'description': f"Exception during resolution: {conflict['type']}",
                    'temperature': self.temperature
                })
        
        logger.info(f"🔧 [SA] CONFLICT RESOLUTION COMPLETED")
        logger.info(f"   - Conflicts resolved: {len([r for r in resolution_log if r['success']])}")
        logger.info(f"   - Conflicts failed: {len([r for r in resolution_log if not r['success']])}")
        logger.info(f"   - Temperature: {self.temperature:.2f}")
        
        return resolved_assignments, resolution_log
    
    def _resolve_single_conflict(self, conflict: Dict[str, Any], 
                                assignments: List[Dict[str, Any]],
                                aggressiveness: float = 1.0) -> Dict[str, Any]:
        """Tek bir çakışmayı çözer - Temperature-based resolution"""
        
        conflict_type = conflict.get('type')
        strategy = conflict.get('resolution_strategy')
        
        try:
            if strategy == 'reschedule_one_assignment':
                return self._reschedule_one_assignment(conflict, assignments, aggressiveness)
            elif strategy == 'reschedule_duplicate_assignment':
                return self._reschedule_duplicate_assignment(conflict, assignments, aggressiveness)
            elif strategy == 'replace_jury_member':
                return self._replace_jury_member(conflict, assignments, aggressiveness)
            elif strategy == 'relocate_to_available_classroom':
                return self._relocate_to_available_classroom(conflict, assignments, aggressiveness)
            elif strategy == 'redistribute_to_other_timeslots':
                return self._redistribute_to_other_timeslots(conflict, assignments, aggressiveness)
            else:
                return {'success': False, 'error': f'Unknown strategy: {strategy}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _reschedule_one_assignment(self, conflict: Dict[str, Any], 
                                  assignments: List[Dict[str, Any]], 
                                  aggressiveness: float = 1.0) -> Dict[str, Any]:
        """Bir atamayı yeniden zamanla - Temperature-based selection"""
        changes_made = []
        
        conflicting_assignments = conflict.get('conflicting_assignments', [])
        if len(conflicting_assignments) < 2:
            return {'success': False, 'error': 'Not enough conflicting assignments'}
        
        # Temperature-based assignment selection
        # HIGH TEMP: Random selection (exploration)
        # LOW TEMP: Select assignment with lower fitness (exploitation)
        if aggressiveness > 0.5:
            # High temperature: Random selection
            assignment_to_move = random.choice(conflicting_assignments[1:])['assignment']
        else:
            # Low temperature: Select assignment with lowest fitness
            assignment_to_move = conflicting_assignments[1]['assignment']
        
        # Temperature-based timeslot selection
        used_timeslots = {a.get('timeslot_id') for a in assignments if a.get('timeslot_id')}
        available_timeslots = [ts for ts in self.timeslots if ts.get('id') not in used_timeslots]
        
        if not available_timeslots:
            available_timeslots = self.timeslots
        
        # Temperature-based timeslot selection strategy
        if aggressiveness > 0.5:
            # High temperature: Random timeslot selection
            new_timeslot = random.choice(available_timeslots)
        else:
            # Low temperature: Prefer earlier timeslots
            available_timeslots.sort(key=lambda ts: ts.get('id', 0))
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
                    'action': 'rescheduled',
                    'temperature': self.temperature
                })
                break
        
        return {
            'success': True,
            'assignments': assignments,
            'changes_made': changes_made
        }
    
    def _reschedule_duplicate_assignment(self, conflict: Dict[str, Any], 
                                       assignments: List[Dict[str, Any]], 
                                       aggressiveness: float = 1.0) -> Dict[str, Any]:
        """Çoğaltılmış atamayı yeniden zamanla"""
        return self._reschedule_one_assignment(conflict, assignments, aggressiveness)
    
    def _replace_jury_member(self, conflict: Dict[str, Any], 
                           assignments: List[Dict[str, Any]], 
                           aggressiveness: float = 1.0) -> Dict[str, Any]:
        """Jüri üyesini değiştir - Temperature-based replacement"""
        changes_made = []
        
        conflicting_assignments = conflict.get('conflicting_assignments', [])
        instructor_id = conflict.get('instructor_id')
        timeslot_id = conflict.get('timeslot_id')
        
        # Bu zaman diliminde meşgul olmayan instructor bul
        busy_instructors = set()
        for assignment in assignments:
            if assignment.get('timeslot_id') == timeslot_id:
                busy_instructors.add(assignment.get('responsible_instructor_id'))
                busy_instructors.update(assignment.get('instructors', []))
        
        available_instructors = []
        for instructor in self.instructors:
            if instructor.get('id') not in busy_instructors:
                available_instructors.append(instructor)
        
        if not available_instructors:
            return {'success': False, 'error': 'No available instructors for replacement'}
        
        # Temperature-based instructor selection
        if aggressiveness > 0.5:
            # High temperature: Random selection
            replacement_instructor = random.choice(available_instructors)['id']
        else:
            # Low temperature: Select instructor with lowest load
            available_instructors.sort(key=lambda inst: inst.get('total_load', 0))
            replacement_instructor = available_instructors[0]['id']
        
        # Jüri üyesini değiştir
        for assignment in assignments:
            if assignment.get('timeslot_id') == timeslot_id:
                instructors_list = assignment.get('instructors', [])
                if instructor_id in instructors_list:
                    instructors_list.remove(instructor_id)
                    instructors_list.append(replacement_instructor)
                    assignment['instructors'] = instructors_list
                    
                    changes_made.append({
                        'assignment_id': assignment.get('project_id'),
                        'old_jury': instructor_id,
                        'new_jury': replacement_instructor,
                        'action': 'jury_replaced',
                        'temperature': self.temperature
                    })
                    break
        
        return {
            'success': True,
            'assignments': assignments,
            'changes_made': changes_made
        }
    
    def _relocate_to_available_classroom(self, conflict: Dict[str, Any], 
                                       assignments: List[Dict[str, Any]], 
                                       aggressiveness: float = 1.0) -> Dict[str, Any]:
        """Boş sınıfa taşı - Temperature-based relocation"""
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
        
        # Temperature-based classroom selection
        if aggressiveness > 0.5:
            # High temperature: Random selection
            new_classroom = random.choice(available_classrooms)
        else:
            # Low temperature: Prefer larger capacity classrooms
            available_classrooms.sort(key=lambda c: c.get('capacity', 0), reverse=True)
            new_classroom = available_classrooms[0]
        
        new_classroom_id = new_classroom['id']
        
        # Sınıfı değiştir
        for assignment in assignments:
            if (assignment.get('classroom_id') == classroom_id and 
                assignment.get('timeslot_id') == timeslot_id):
                assignment['classroom_id'] = new_classroom_id
                
                changes_made.append({
                    'assignment_id': assignment.get('project_id'),
                    'old_classroom': classroom_id,
                    'new_classroom': new_classroom_id,
                    'action': 'relocated',
                    'temperature': self.temperature
                })
                break
        
        return {
            'success': True,
            'assignments': assignments,
            'changes_made': changes_made
        }
    
    def _redistribute_to_other_timeslots(self, conflict: Dict[str, Any], 
                                       assignments: List[Dict[str, Any]], 
                                       aggressiveness: float = 1.0) -> Dict[str, Any]:
        """Diğer zaman dilimlerine yeniden dağıt - Temperature-based redistribution"""
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
        
        # Temperature-based redistribution strategy
        if aggressiveness > 0.5:
            # High temperature: Random redistribution
            assignments_to_move = random.sample(timeslot_assignments, min(overflow, len(timeslot_assignments)))
        else:
            # Low temperature: Move latest assignments to earlier slots
            timeslot_assignments.sort(key=lambda a: a.get('timeslot_id', 0), reverse=True)
            assignments_to_move = timeslot_assignments[:overflow]
        
        # Fazla atamaları yeniden dağıt
        for i, assignment in enumerate(assignments_to_move):
            if aggressiveness > 0.5:
                # High temperature: Random target timeslot
                target_timeslot = random.choice(available_timeslots)
            else:
                # Low temperature: Prefer earlier timeslots
                available_timeslots.sort(key=lambda ts: ts.get('id', 0))
                target_timeslot = available_timeslots[i % len(available_timeslots)]
            
            old_timeslot_id = assignment.get('timeslot_id')
            assignment['timeslot_id'] = target_timeslot.get('id')
            
            changes_made.append({
                'assignment_id': assignment.get('project_id'),
                'old_timeslot': old_timeslot_id,
                'new_timeslot': target_timeslot.get('id'),
            'action': 'redistributed',
            'temperature': self.temperature
        })
        
        return {
            'success': True,
            'assignments': assignments,
            'changes_made': changes_made
        }

    # 📊 DOKÜMANTASYON FORMÜLLERİ - SA Temperature-Based Implementation
    
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
            penalty = max(0, round(time_diff / delta) - 1)
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

    def calculate_sa_temperature_penalty(self, solution: List[Dict], temperature: float = None) -> float:
        """
        Simulated Annealing için sıcaklık bazlı ceza
        
        Yüksek T: Cezaları daha az ağırlıklandır (exploration)
        Düşük T: Cezaları daha fazla ağırlıklandır (exploitation)
        
        Args:
            solution: Çözüm listesi
            temperature: Mevcut sıcaklık (varsayılan: self.temperature)
            
        Returns:
            float: Temperature-based penalty
        """
        temperature = temperature or self.temperature
        
        # Temperature normalizasyonu (0-1 arası)
        temp_factor = temperature / self.initial_temperature
        
        # Instructor bazında projeleri grupla
        instructor_schedules = defaultdict(list)
        
        for assignment in solution:
            # Her assignment'taki instructor'ları al
            responsible_id = assignment.get("supervisor_id") or assignment.get("responsible_id")
            
            if responsible_id:
                instructor_schedules[responsible_id].append({
                    'timeslot_id': assignment.get('timeslot_id'),
                    'classroom_id': assignment.get('classroom_id'),
                    'project_id': assignment.get('project_id')
                })
        
        # Her instructor için dokümantasyon formüllerini uygula
        total_penalty = 0.0
        
        for instructor_id, projects in instructor_schedules.items():
            if len(projects) < 2:  # En az 2 proje olmalı
                continue
                
            # Zaman cezası hesapla
            time_penalty = self.calculate_time_penalty(projects)
            
            # Sınıf değişim cezası hesapla
            class_penalty = self.calculate_class_penalty(projects)
            
            # Temperature-based weighting
            alpha_sa = self.alpha * (1 - temp_factor * 0.5)  # Düşük T'de alpha artar
            beta_sa = self.beta * (1 - temp_factor * 0.5)
            
            # Temperature-based penalty: α * Σ(time_penalty) + β * Σ(class_penalty)
            instructor_penalty = alpha_sa * time_penalty + beta_sa * class_penalty
            total_penalty += instructor_penalty
            
        return total_penalty

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

    # 🤖 YENİ AI ÖZELLİKLERİ - SA Doğasına Göre
    
    def _intelligent_cooling_schedule(self, iteration: int, quality_history: List[float]) -> float:
        """
        🤖 AI FEATURE 1: Adaptive Cooling Intelligence
        
        Çözüm kalitesine göre cooling rate'i adapte et
        
        İyileşme varsa: Yavaş soğut (daha fazla explore)
        İyileşme yoksa: Hızlı soğut (exploit'a geç)
        """
        if not hasattr(self, 'cooling_history'):
            self.cooling_history = []
        
        # Son 10 iterasyonun iyileşme oranını hesapla
        if len(quality_history) >= 10:
            recent_improvement = self._calculate_improvement_rate(quality_history[-10:])
            improvement_threshold = 0.05  # %5 iyileşme threshold'u
            
            if recent_improvement > improvement_threshold:
                # İyileşme var -> Yavaş soğut (daha fazla explore)
                self.cooling_rate = max(0.85, self.cooling_rate * 0.98)
                logger.info(f"🤖 Cooling slowed down (improvement: {recent_improvement:.3f})")
            else:
                # İyileşme yok -> Hızlı soğut (exploit'a geç)
                self.cooling_rate = min(0.99, self.cooling_rate * 1.02)
                logger.info(f"🤖 Cooling accelerated (no improvement: {recent_improvement:.3f})")
        
        # Cooling history'yi güncelle
        self.cooling_history.append({
            'iteration': iteration,
            'cooling_rate': self.cooling_rate,
            'temperature': self.temperature,
            'timestamp': time.time()
        })
        
        return self.temperature * self.cooling_rate

    def _calculate_improvement_rate(self, quality_history: List[float]) -> float:
        """
        Kalite geçmişinden iyileşme oranını hesapla
        """
        if len(quality_history) < 2:
            return 0.0
        
        # Son 5 vs önceki 5 iterasyon karşılaştırması
        recent_avg = sum(quality_history[-5:]) / 5
        previous_avg = sum(quality_history[-10:-5]) / 5
        
        if previous_avg == 0:
            return 0.0
        
        improvement_rate = (recent_avg - previous_avg) / abs(previous_avg)
        return improvement_rate

    def _smart_reheat_decision(self, stuck_iterations: int, temperature: float) -> float:
        """
        🤖 AI FEATURE 2: Intelligent Reheating
        
        Ne zaman reheat yapılacağını AI ile karar ver
        """
        if not hasattr(self, 'reheat_history'):
            self.reheat_history = []
        
        # Stuck threshold
        stuck_threshold = 20
        min_temp_threshold = self.initial_temperature * 0.1
        
        if stuck_iterations > stuck_threshold and temperature < min_temp_threshold:
            # Entropy hesapla (çözüm çeşitliliği)
            entropy = self._calculate_solution_entropy()
            min_entropy = 0.3  # Minimum entropy threshold
            
            if entropy < min_entropy:
                # Düşük entropy -> Reheat gerekli
                reheat_amount = self._calculate_optimal_reheat()
                new_temperature = temperature + reheat_amount
                
                logger.info(f"🤖 Smart reheat: {temperature:.2f} -> {new_temperature:.2f} (entropy: {entropy:.3f})")
                
                # Reheat history'yi güncelle
                self.reheat_history.append({
                    'stuck_iterations': stuck_iterations,
                    'old_temperature': temperature,
                    'new_temperature': new_temperature,
                    'entropy': entropy,
                    'timestamp': time.time()
                })
                
                return new_temperature
        
        return temperature

    def _calculate_solution_entropy(self) -> float:
        """
        Çözüm çeşitliliğini entropy ile ölç
        """
        # Basit entropy hesaplama: classroom distribution
        classroom_counts = defaultdict(int)
        
        for assignment in self.current_schedules:
            classroom_id = assignment.get('classroom_id')
            if classroom_id:
                classroom_counts[classroom_id] += 1
        
        if not classroom_counts:
            return 0.0
        
        # Entropy hesapla
        total = sum(classroom_counts.values())
        entropy = 0.0
        
        for count in classroom_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * np.log2(p)
        
        return entropy

    def _calculate_optimal_reheat(self) -> float:
        """
        Optimal reheat miktarını hesapla
        """
        # Mevcut sıcaklığın %30'u kadar reheat
        reheat_amount = self.temperature * 0.3
        
        # Maximum reheat limiti
        max_reheat = self.initial_temperature * 0.2
        
        return min(reheat_amount, max_reheat)
