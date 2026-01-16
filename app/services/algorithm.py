"""
Algorithm service module for managing algorithm operations.
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
import time
import math
from datetime import datetime

from app.models.algorithm import AlgorithmType, AlgorithmRun
from app.schemas.algorithm import AlgorithmRunCreate, AlgorithmRunUpdate
from app.crud.algorithm import crud_algorithm
from app.algorithms.factory import AlgorithmFactory
from app.db.base import get_db
from app.i18n import translate
from app.services.gap_free_scheduler import GapFreeScheduler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
_ = translate

class AlgorithmService:
    """
    Service class for managing algorithm operations.
    """

    @staticmethod
    def get_algorithm_info(algorithm_type: AlgorithmType) -> Dict[str, Any]:
        """
        Get information about an algorithm.

        Args:
            algorithm_type: The algorithm type.

        Returns:
            Dict[str, Any]: Information about the algorithm.
        """
        algorithm_info = {
            AlgorithmType.GENETIC_ALGORITHM: {
                "name": _("Genetic Algorithm"),
                "description": _("Adaptive parameters, self-learning weights, diversity maintenance, pattern recognition, and 7+ more AI features. ZERO HARD CONSTRAINTS - Pure AI optimization!"),
                "best_for": _("Complex scheduling with: (1) Adaptive mutation/crossover rates, (2) Self-learning fitness weights, (3) Diversity protection, (4) Smart initialization, (5) Pattern recognition, (6-11) AI selection/crossover/mutation/local search/convergence. Revolutionary optimization power!"),
                "category": "AI-Enhanced Bio-inspired",
                "parameters": {
                    # Basic GA Parameters (OPTIMIZED FOR PERFORMANCE)
                    "population_size": {"type": "int", "default": 100, "description": _("Population size (number of solutions in each generation).")},
                    "n_generations": {"type": "int", "default": 100, "description": _("Number of generations to evolve.")},
                    "crossover_rate": {"type": "float", "default": 0.85, "description": _("Initial crossover rate (will adapt with AI).")},
                    "mutation_rate": {"type": "float", "default": 0.15, "description": _("Initial mutation rate (will adapt with AI).")},
                    "elite_size": {"type": "int", "default": 15, "description": _("Elite preservation size.")},
                    "tournament_size": {"type": "int", "default": 3, "description": _("Tournament selection size.")},
                    # AI Features (All default True)
                    "adaptive_enabled": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 1: Adaptive mutation & crossover rates based on performance.")},
                    "ai_selection_enabled": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 6: AI-powered parent selection strategies.")},
                    "ai_crossover_enabled": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 7: Smart genetic recombination.")},
                    "ai_mutation_enabled": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 8: Adaptive mutation strategies with AI guidance.")},
                    "ai_fitness_landscape_enabled": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 9: Dynamic fitness landscape analysis.")},
                    "ai_local_search_enabled": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 10: Intelligent neighborhood search.")},
                    "ai_convergence_enabled": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 11: Early stopping and restart strategies.")},
                    "conflict_resolution_enabled": {"type": "bool", "default": True, "description": _("Enable automatic conflict detection and resolution.")},
                    "diversity_threshold": {"type": "float", "default": 0.3, "description": _("🤖 AI FEATURE 3: Diversity maintenance threshold.")},
                    "local_search_frequency": {"type": "int", "default": 10, "description": _("Local search frequency (every N generations).")}
                }
            },
            AlgorithmType.SIMULATED_ANNEALING: {
                "name": _("Simulated Annealing"),
                "description": _("Temperature-driven intelligence with 16+ AI features. Adaptive cooling, conflict resolution, dynamic exploration/exploitation, and temperature-based decision making. NO HARD CONSTRAINTS!"),
                "best_for": _("Global optimization with: (1) AI temperature control (exponential/linear/adaptive cooling), (2) Temperature-based timeslot selection, (3) AI jury assignment, (4) Adaptive neighborhood search, (5) AI conflict resolution, (6-16) Early timeslot optimization, gap-free scheduling, classroom-wise optimization. Perfect for avoiding local optima!"),
                "category": "AI-Enhanced Metaheuristic",
                "parameters": {
                    # Basic SA Parameters
                    "initial_temp": {"type": "float", "default": 1000.0, "description": _("Initial temperature (higher = more exploration).")},
                    "cooling_rate": {"type": "float", "default": 0.90, "description": _("Cooling rate (0.9 = faster cooling).")},
                    "n_iterations": {"type": "int", "default": 20, "description": _("Maximum number of iterations.")},
                    "final_temperature": {"type": "float", "default": 1.0, "description": _("Final temperature (stopping criterion).")},
                    "reheat_temperature": {"type": "float", "default": 500.0, "description": _("Reheat temperature when stuck.")},
                    # AI Features
                    "cooling_strategy": {"type": "str", "default": "exponential", "description": _("🤖 AI FEATURE 1: Cooling strategy (exponential/linear/adaptive).")},
                    "ai_based_timeslot_selection": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 7: Temperature-based timeslot selection.")},
                    "ai_based_jury_assignment": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 8: AI-powered jury assignment with load balancing.")},
                    "ai_based_conflict_resolution": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 11: AI-based conflict resolution.")},
                    "temperature_based_resolution": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 12: Temperature-driven conflict resolution strategy.")},
                    "adaptive_neighborhood_search": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 13: Adaptive neighborhood search based on temperature.")},
                    "conflict_resolution_enabled": {"type": "bool", "default": True, "description": _("Enable automatic conflict detection and resolution.")},
                    "auto_resolve_conflicts": {"type": "bool", "default": True, "description": _("Auto-resolve conflicts during optimization.")},
                    "early_stopping_threshold": {"type": "int", "default": 5, "description": _("Early stopping threshold (no improvement iterations).")}
                }
            },
            AlgorithmType.SIMPLEX: {
                "name": _("Simplex Algorithm"),
                "description": _("Instructor pairing with consecutive grouping, bi-directional jury assignment, and 5 AI learning features. SELF-IMPROVING algorithm with NO HARD CONSTRAINTS."),
                "best_for": _("Advanced scheduling with: (1) Adaptive scoring weights that self-optimize, (2) Workload-aware jury assignment, (3) Smart classroom memory, (4) Learning-based pairing, (5) Conflict prediction & prevention. Perfect for complex scheduling with continuous improvement. 100% AI-driven soft constraints."),
                "category": "AI-Enhanced Linear Programming",
                "parameters": {
                    "random_seed": {"type": "int", "default": None, "description": _("Random seed for reproducibility (optional).")},
                    "enable_ultra_consecutive": {"type": "bool", "default": True, "description": _("Enable ultra-aggressive consecutive grouping.")},
                    "enable_gap_elimination": {"type": "bool", "default": True, "description": _("Enable aggressive gap elimination.")},
                    "enable_early_optimization": {"type": "bool", "default": True, "description": _("Enable early timeslot prioritization.")},
                    "enable_smart_pairing": {"type": "bool", "default": True, "description": _("Enable smart instructor pairing (high↔low).")},
                    "enable_adaptive_learning": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 1: Auto-adjust reward/penalty values based on performance.")},
                    "enable_workload_balance": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 2: Balance instructor workload in jury assignments.")},
                    "enable_classroom_memory": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 3: Remember successful classroom selections.")},
                    "enable_pairing_learning": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 4: Learn which instructor pairs work best.")},
                    "enable_conflict_prediction": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 5: Predict and prevent conflicts proactively.")}
                }
            },
            AlgorithmType.ANT_COLONY: {
                "name": _("Ant Colony Optimization"),
                "description": _("A probabilistic technique for solving computational problems which can be reduced to finding good paths through graphs."),
                "best_for": _("Path finding and routing problems."),
                "parameters": {
                    "n_ants": {"type": "int", "default": 30, "description": _("Number of ants.")},
                    "n_iterations": {"type": "int", "default": 100, "description": _("Number of iterations.")},
                    "alpha": {"type": "float", "default": 1.0, "description": _("Pheromone importance factor.")},
                    "beta": {"type": "float", "default": 2.0, "description": _("Heuristic information importance factor.")},
                    "evaporation_rate": {"type": "float", "default": 0.5, "description": _("Pheromone evaporation rate.")}
                }
            },
            AlgorithmType.NSGA_II: {
                "name": _("🤖 NSGA-II"),
                "description": _("Strategic instructor pairing, consecutive grouping, multi-objective optimization with Pareto front, non-dominated sorting, crowding distance, and 10 AI features. NO HARD CONSTRAINTS - Pure soft constraint optimization!"),
                "best_for": _("Multi-objective scheduling with: (1) Strategic Pairing (sort instructors by project count, split and pair HIGH↔LOW), (2) Consecutive Grouping (X responsible → Y jury, then Y responsible → X jury), (3) Multi-objective optimization (6 objectives: minimize conflicts, maximize balance/consecutiveness/pairing/early slots), (4) Non-dominated sorting (Pareto-optimal solutions), (5) Crowding distance (diversity maintenance), (6) AI-based genetic operators (smart crossover/mutation), (7) Adaptive parameters (mutation/crossover rates evolve), (8) Elite preservation with diversity, (9) Smart initialization (strategic pairing-based population), (10) AI-powered conflict resolution. Revolutionary multi-objective power!"),
                "category": "AI-Enhanced Multi-Objective Genetic",
                "parameters": {
                    # Core NSGA-II Parameters
                    "population_size": {"type": "int", "default": 100, "description": _("Population size (number of solutions in each generation).")},
                    "generations": {"type": "int", "default": 200, "description": _("Number of generations to evolve.")},
                    "crossover_rate": {"type": "float", "default": 0.85, "description": _("Initial crossover rate (will adapt with AI).")},
                    "mutation_rate": {"type": "float", "default": 0.15, "description": _("Initial mutation rate (will adapt with AI).")},
                    "elite_size": {"type": "int", "default": 20, "description": _("Elite preservation size (top solutions kept).")},
                    # AI Features Enablers
                    "enable_strategic_pairing": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 1: Strategic instructor pairing (HIGH project count ↔ LOW project count).")},
                    "enable_consecutive_grouping": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 2: Consecutive grouping (X responsible → Y jury, then Y responsible → X jury).")},
                    "enable_diversity_maintenance": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 5: Diversity maintenance via crowding distance.")},
                    "enable_adaptive_params": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 7: Adaptive mutation/crossover rates based on progress.")},
                    "enable_conflict_resolution": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 10: AI-powered conflict resolution during optimization.")},
                    # Soft Constraint Weights (Auto-adjustable)
                    "w_instructor_conflict": {"type": "float", "default": 100.0, "description": _("Weight for instructor conflict penalty (soft constraint).")},
                    "w_classroom_conflict": {"type": "float", "default": 80.0, "description": _("Weight for classroom conflict penalty (soft constraint).")},
                    "w_workload_balance": {"type": "float", "default": 50.0, "description": _("Weight for workload balance reward (soft constraint).")},
                    "w_consecutive_bonus": {"type": "float", "default": 70.0, "description": _("Weight for consecutive grouping bonus (soft constraint).")},
                    "w_pairing_quality": {"type": "float", "default": 60.0, "description": _("Weight for pairing quality reward (soft constraint).")},
                    "w_early_timeslot": {"type": "float", "default": 40.0, "description": _("Weight for early timeslot bonus (soft constraint).")}
                }
            },
            AlgorithmType.NSGA_II_ENHANCED: {
                "name": _("NSGA-II Enhanced"),
                "description": _("Strategic instructor pairing, consecutive grouping, multi-objective optimization with Pareto front, non-dominated sorting, crowding distance, and 10 AI features. NO HARD CONSTRAINTS - Pure soft constraint optimization!"),
                "best_for": _("Multi-objective scheduling with: (1) Strategic Pairing (sort instructors by project count, split and pair HIGH↔LOW), (2) Consecutive Grouping (X responsible → Y jury, then Y responsible → X jury), (3) Multi-objective optimization (6 objectives: minimize conflicts, maximize balance/consecutiveness/pairing/early slots), (4) Non-dominated sorting (Pareto-optimal solutions), (5) Crowding distance (diversity maintenance), (6) AI-based genetic operators (smart crossover/mutation), (7) Adaptive parameters (mutation/crossover rates evolve), (8) Elite preservation with diversity, (9) Smart initialization (strategic pairing-based population), (10) AI-powered conflict resolution. Revolutionary multi-objective power!"),
                "parameters": {
                    "population_size": {"type": "int", "default": 50, "description": _("Size of the population.")},
                    "generations": {"type": "int", "default": 20, "description": _("Number of generations.")},
                    "crossover_rate": {"type": "float", "default": 0.8, "description": _("Crossover rate.")},
                    "mutation_rate": {"type": "float", "default": 0.1, "description": _("Mutation rate.")}
                }
            },
            AlgorithmType.GREEDY: {
                "name": _("Greedy Algorithm"),
                "description": _("An algorithm that makes the locally optimal choice at each stage."),
                "best_for": _("Problems where local optimal choices lead to a global optimum."),
                "parameters": {
                    "local_search_iterations": {"type": "int", "default": 100, "description": _("Number of local search iterations.")}
                }
            },
            AlgorithmType.TABU_SEARCH: {
                "name": _("Tabu Search"),
                "description": _("Adaptive tabu tenure, frequency memory, aspiration criteria, intelligent classroom selection, smart neighborhood search, adaptive learning weights, pattern recognition, and dynamic strategy switching. Memory-based learning with NO HARD CONSTRAINTS!"),
                "best_for": _("Combinatorial optimization with: (1) Adaptive tabu tenure (dynamic list size), (2) Frequency-based learning (move memory), (3) Aspiration criteria (intelligent tabu override), (4) Intelligent classroom selection, (5) Smart neighborhood (conflict-based + load-balanced), (6) Adaptive learning weights, (7) Pattern recognition & learning, (8) Dynamic intensification/diversification strategy. Memory-driven optimization!"),
                "category": "AI-Enhanced Search-based",
                "parameters": {
                    # Basic Tabu Parameters
                    "max_iterations": {"type": "int", "default": 100, "description": _("Maximum number of iterations (reduced for faster execution).")},
                    "tabu_list_size": {"type": "int", "default": 10, "description": _("Initial tabu list size (will adapt with AI).")},
                    "neighborhood_size": {"type": "int", "default": 30, "description": _("Neighborhood size for local search.")},
                    # AI Features
                    "adaptive_tabu": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 1: Adaptive tabu tenure (dynamic list size based on performance).")},
                    "aspiration_enabled": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 3: Aspiration criteria (intelligent tabu override).")},
                    "intelligent_classroom": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 4: Intelligent classroom selection (consecutive + uniform).")},
                    "smart_neighborhood": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 5: Smart neighborhood search (conflict-based + load-balanced).")},
                    "enable_adaptive_weights": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 6: Adaptive learning weights (self-adjusting objectives).")},
                    "enable_pattern_learning": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 7: Pattern recognition & learning (successful pattern memory).")},
                    "enable_dynamic_strategy": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 8: Dynamic intensification/diversification strategy switching.")},
                    "min_tabu_tenure": {"type": "int", "default": 5, "description": _("Minimum tabu tenure (for adaptive tabu).")},
                    "max_tabu_tenure": {"type": "int", "default": 20, "description": _("Maximum tabu tenure (for adaptive tabu).")},
                    "conflict_based_moves": {"type": "float", "default": 0.5, "description": _("Percentage of conflict-based moves (0.5 = 50%).")},
                    "load_balance_moves": {"type": "float", "default": 0.25, "description": _("Percentage of load-balance moves (0.25 = 25%).")}
                }
            },
            AlgorithmType.PSO: {
                "name": _("Particle Swarm Optimization"),
                "description": _("A computational method that optimizes a problem by iteratively trying to improve a candidate solution with swarm intelligence approach for repair."),
                "best_for": _("Continuous optimization problems. Uses swarm intelligence approach for gap repair and coverage optimization."),
                "parameters": {
                    "n_particles": {"type": "int", "default": 30, "description": _("Number of particles.")},
                    "n_iterations": {"type": "int", "default": 100, "description": _("Number of iterations.")},
                    "w": {"type": "float", "default": 0.7, "description": _("Inertia weight.")},
                    "c1": {"type": "float", "default": 1.5, "description": _("Cognitive coefficient.")},
                    "c2": {"type": "float", "default": 1.5, "description": _("Social coefficient.")}
                }
            },
            AlgorithmType.HARMONY_SEARCH: {
                "name": _("Harmony Search"),
                "description": _("A music-inspired metaheuristic optimization algorithm with musical harmony approach for repair."),
                "best_for": _("Combinatorial optimization problems. Uses musical harmony approach for gap repair and duplicate handling."),
                "parameters": {
                    "harmony_memory_size": {"type": "int", "default": 30, "description": _("Size of the harmony memory.")},
                    "max_iterations": {"type": "int", "default": 100, "description": _("Maximum number of iterations.")},
                    "hmcr": {"type": "float", "default": 0.9, "description": _("Harmony memory considering rate.")},
                    "par": {"type": "float", "default": 0.3, "description": _("Pitch adjustment rate.")}
                }
            },
            AlgorithmType.FIREFLY: {
                "name": _("Firefly Algorithm"),
                "description": _("A metaheuristic algorithm inspired by the flashing behavior of fireflies."),
                "best_for": _("Multimodal optimization problems."),
                "parameters": {
                    "n_fireflies": {"type": "int", "default": 30, "description": _("Number of fireflies.")},
                    "n_iterations": {"type": "int", "default": 100, "description": _("Number of iterations.")},
                    "alpha": {"type": "float", "default": 0.2, "description": _("Randomization parameter.")},
                    "beta0": {"type": "float", "default": 1.0, "description": _("Attractiveness parameter.")},
                    "gamma": {"type": "float", "default": 1.0, "description": _("Light absorption coefficient.")}
                }
            },
            AlgorithmType.GREY_WOLF: {
                "name": _("Grey Wolf Optimizer"),
                "description": _("A metaheuristic algorithm inspired by the leadership hierarchy and hunting mechanism of grey wolves."),
                "best_for": _("Continuous optimization problems."),
                "parameters": {
                    "n_wolves": {"type": "int", "default": 30, "description": _("Number of wolves.")},
                    "n_iterations": {"type": "int", "default": 100, "description": _("Number of iterations.")},
                    "a_decrease_factor": {"type": "float", "default": 2.0, "description": _("Decrease factor for a parameter.")}
                }
            },
            AlgorithmType.CP_SAT: {
                "name": _("CP-SAT"),
                "description": _("Mathematical precision. Intelligent timeslot scoring, AI classroom selection, conflict resolution, workload balancing, capacity management, multi-objective optimization, and adaptive learning. Soft constraints with CP-SAT power!"),
                "best_for": _("Complex constraints with AI enhancement: (1) AI timeslot scoring, (2) AI classroom selection, (3) AI conflict resolution, (4) Workload balancing, (5) Capacity management, (6) Multi-objective optimization, (7) Adaptive learning. Mathematical precision + AI intelligence!"),
                "category": "AI-Enhanced Mathematical",
                "parameters": {
                    # Basic CP-SAT Parameters
                    "time_limit": {"type": "int", "default": 60, "description": _("Time limit in seconds for CP-SAT solver.")},
                    "log_search_progress": {"type": "bool", "default": False, "description": _("Log CP-SAT search progress (verbose).")},
                    # AI Features (All default True)
                    "ai_timeslot_scoring": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 1: Intelligent timeslot scoring with preferences.")},
                    "ai_classroom_selection": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 2: AI-powered classroom selection.")},
                    "ai_conflict_resolution": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 3: AI-based conflict resolution.")},
                    "ai_workload_balancing": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 4: Dynamic workload balancing across instructors.")},
                    "ai_capacity_management": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 5: Intelligent capacity management.")},
                    "ai_multi_objective": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 6: Multi-objective optimization.")},
                    "ai_adaptive_learning": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 7: Adaptive learning from instructor preferences.")}
                }
            },
            AlgorithmType.DEEP_SEARCH: {
                "name": _("Deep Search"),
                "description": _("Deep Search (DS) is a search algorithm that combines beam search and iterative deepening. It is a population-based algorithm that uses a colony of cuckoos to search for the best solution to a problem."),
                "best_for": _("Problems requiring thorough exploration of the solution space."),
                "parameters": {
                    "max_depth": {"type": "int", "default": 5, "description": _("Maximum search depth.")},
                    "beam_width": {"type": "int", "default": 10, "description": _("Beam search width.")},
                    "time_limit": {"type": "int", "default": 60, "description": _("Time limit in seconds.")}
                }
            },
            AlgorithmType.ARTIFICIAL_BEE_COLONY: {
                "name": _("Artificial Bee Colony"),
                "description": _("Artificial Bee Colony (ABC) is a metaheuristic optimization algorithm inspired by the foraging behavior of honey bees. It is a population-based algorithm that uses a colony of bees to search for the best solution to a problem."),
                "best_for": _("Combinatorial optimization problems with good exploration-exploitation balance."),
                "parameters": {
                    "colony_size": {"type": "int", "default": 50, "description": _("Total number of bees in the colony.")},
                    "max_iterations": {"type": "int", "default": 100, "description": _("Maximum number of iterations.")},
                    "limit": {"type": "int", "default": 10, "description": _("Scout bee limit.")}
                }
            },
            AlgorithmType.CUCKOO_SEARCH: {
                "name": _("Cuckoo Search"),
                "description": _("Cuckoo Search (CS) is a metaheuristic optimization algorithm inspired by the obligate brood parasitism of some cuckoo species. It is a population-based algorithm that uses a colony of cuckoos to search for the best solution to a problem."),
                "best_for": _("Global optimization problems with Levy flight behavior."),
                "parameters": {
                    "n_cuckoos": {"type": "int", "default": 25, "description": _("Number of cuckoos.")},
                    "max_iterations": {"type": "int", "default": 100, "description": _("Maximum number of iterations.")},
                    "pa": {"type": "float", "default": 0.25, "description": _("Probability of abandoning eggs.")},
                    "alpha": {"type": "float", "default": 0.01, "description": _("Step size parameter.")}
                }
            },
            AlgorithmType.BRANCH_AND_BOUND: {
                "name": _("Branch and Bound"),
                "description": _("Branch and Bound (BnB) is a mathematical optimization algorithm for solving combinatorial optimization problems."),
                "best_for": _("Exact solutions for small to medium-sized problems."),
                "parameters": {
                    "time_limit": {"type": "int", "default": 10, "description": _("Time limit in seconds.")},
                    "max_nodes": {"type": "int", "default": 1000, "description": _("Maximum number of nodes to explore.")}
                }
            },
            AlgorithmType.DYNAMIC_PROGRAMMING: {
                "name": _("Dynamic Programming"),
                "description": _("Single-phase, deterministic assignment system. Fully automated scheduling with workload-based sequencing, block-based distribution, zigzag class assignment, uniform load balancing, and workload-based time-slot prioritization."),
                "best_for": _("Single-phase, deterministic assignment system. Fully automated scheduling with workload-based sequencing, block-based distribution, zigzag class assignment, uniform load balancing, and workload-based time-slot prioritization."),
                "category": "Deterministic Optimization",
                "parameters": {
                    "workload_threshold": {"type": "int", "default": 2, "description": _("Uniform distribution for workload threshold (±2).")}
                }
            },
            AlgorithmType.WHALE_OPTIMIZATION: {
                "name": _("Whale Optimization Algorithm"),
                "description": _("A metaheuristic algorithm inspired by the hunting behavior of humpback whales."),
                "best_for": _("Continuous and discrete optimization problems with bubble-net feeding behavior."),
                "parameters": {
                    "n_whales": {"type": "int", "default": 30, "description": _("Number of whales.")},
                    "max_iterations": {"type": "int", "default": 100, "description": _("Maximum number of iterations.")}
                }
            },
            AlgorithmType.LEXICOGRAPHIC: {
                "name": _("Lexicographic"),
                "description": _("Lexicographic is a multi-objective optimization algorithm that uses a priority queue to select the next node to explore. The algorithm uses a heuristic function to estimate the cost of reaching the goal from the current node, and it uses this estimate to guide the search process. This approach allows the algorithm to find the optimal solution in many cases."),
                "best_for": _("Multi-criteria optimization with: (1) Smart instructor pairing, (2) Dynamic time slot assignment, (3) Multi-solution generation, (4) Stochastic optimization, (5) Diversity metrics, (6) Conflict resolution, (7) Gap filling, (8) Workload balancing, (9) Adaptive parameter tuning, (10) Solution memory & learning, (11) Dynamic fitness weights, (12) Smart mutation strategies, (13) Beam search integration, (14) Solution clustering, (15) Performance prediction. Pure AI optimization!"),
                "category": "AI-Enhanced Multi-Criteria",
                "parameters": {
                    "max_iterations": {"type": "int", "default": 1000, "description": _("Maximum number of iterations.")},
                    "num_solutions": {"type": "int", "default": 15, "description": _("🤖 AI FEATURE 3: Number of diverse solutions to generate.")},
                    "temperature": {"type": "float", "default": 150.0, "description": _("🤖 AI FEATURE 4: Initial temperature for simulated annealing.")},
                    "cooling_rate": {"type": "float", "default": 0.92, "description": _("Cooling rate for simulated annealing.")},
                    "randomization_level": {"type": "float", "default": 0.85, "description": _("Randomization level (0-1).")},
                    "adaptive_tuning": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 9: Enable adaptive parameter tuning.")},
                    "solution_memory": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 10: Enable solution memory & learning.")},
                    "dynamic_weights": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 11: Enable dynamic fitness weights.")},
                    "beam_search": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 13: Enable beam search integration.")},
                    "solution_clustering": {"type": "bool", "default": True, "description": _("🤖 AI FEATURE 14: Enable solution clustering.")}
                }
            },
            AlgorithmType.COMPREHENSIVE_OPTIMIZER: {
                "name": _("Comprehensive Optimizer"),
                "description": _("Comprehensive multi-objective optimizer with hard constraints (no slot gaps, no assignments after 16:30). It is a population-based algorithm that uses a colony of cuckoos to search for the best solution to a problem."),
                "best_for": _("Balanced optimization across multiple criteria with strict slot rules."),
                "parameters": {
                    "population_size": {"type": "int", "default": 100, "description": _("Genetic algorithm population size.")},
                    "generations": {"type": "int", "default": 50, "description": _("Number of generations.")},
                    "mutation_rate": {"type": "float", "default": 0.1, "description": _("Mutation rate.")},
                    "crossover_rate": {"type": "float", "default": 0.8, "description": _("Crossover rate.")}
                }
            },
            AlgorithmType.HUNGARIAN: {
                "name": _("Hungarian Algorithm (Kuhn-Munkres)"),
                "description": _("Hungarian Algorithm (Kuhn-Munkres) is a combinatorial optimization algorithm that solves the assignment problem in polynomial time. It is a variant of the Hungarian method that uses a priority queue to select the next node to explore. The algorithm uses a heuristic function to estimate the cost of reaching the goal from the current node, and it uses this estimate to guide the search process. This approach allows the algorithm to find the optimal solution in many cases."),
                "best_for": _("Assignment problems, project-slot matching, jury assignment, optimal matching required problems."),
                "category": "Mathematical",
                "parameters": {
                    "max_iterations": {"type": "int", "default": 1000, "description": _("Maximum number of iterations.")},
                    "tolerance": {"type": "float", "default": 0.001, "description": _("Convergence tolerance.")}
                }
            },
            AlgorithmType.HYBRID_CP_SAT_NSGA: {
                "name": _("CP-SAT + NSGA-II Hybrid"),
                "description": _("Constraint programming (CP-SAT) with multi-objective genetic algorithm (NSGA-II) combination. First feasible solutions are generated, then Pareto optimal solutions are found."),
                "best_for": _("Multi-objective optimization problems for hybrid approach. Exact constraint satisfaction and multi-objective balance."),
                "category": "Hybrid",
                "parameters": {
                    "time_limit": {"type": "int", "default": 180, "description": _("Total execution time limit in seconds.")}
                }
            },
            AlgorithmType.BAT_ALGORITHM: {
                "name": _("Bat Algorithm"),
                "description": _("Bat Algorithm is a metaheuristic optimization algorithm that models the echolocation behavior of bats. It uses a population of candidate solutions and applies genetic operators (mutation, crossover, and selection) to generate new solutions. The algorithm then uses a local search strategy to refine the solutions, often using a neighborhood structure to explore the solution space. This approach allows the algorithm to balance exploration and exploitation, leading to better solutions in many cases."),
                "best_for": _("Continuous optimization problems, frequency-based search, global optimization."),
                "category": "Metaheuristic",
                "parameters": {
                    "population_size": {"type": "int", "default": 30, "description": _("Number of bats in the population.")}
                }
            },
            AlgorithmType.DRAGONFLY_ALGORITHM: {
                "name": _("Dragonfly Algorithm"),
                "description": _("Dragonfly Algorithm is a swarm intelligence algorithm that models the static and dynamic behavior of a dragonfly swarm. It ensures a balance between exploration and exploitation."),
                "best_for": _("Swarm-based optimization, multi-objective problems, exploration-exploitation balance."),
                "category": "Metaheuristic",
                "parameters": {
                    "population_size": {"type": "int", "default": 30, "description": _("Number of dragonflies in the swarm.")}
                }
            },
            AlgorithmType.A_STAR_SEARCH: {
                "name": _("A* Search"),
                "description": _("A* Search is a search algorithm that uses a heuristic function to guide the search process. It is a variant of Dijkstra's algorithm that uses a priority queue to select the next node to explore. The algorithm uses a heuristic function to estimate the cost of reaching the goal from the current node, and it uses this estimate to guide the search process. This approach allows the algorithm to find the optimal solution in many cases."),
                "best_for": _("Pathfinding problems, graph search, optimal route calculation."),
                "category": "Search-based",
                "parameters": {
                    "heuristic_weight": {"type": "float", "default": 1.0, "description": _("Weight for heuristic function.")}
                }
            },
            AlgorithmType.INTEGER_LINEAR_PROGRAMMING: {
                "name": _("Integer Linear Programming"),
                "description": _("Integer Linear Programming (ILP) is an optimization method where decision variables must be integers and both the objective function and constraints are linear. It is generally used in problems requiring yes/no or quantity-based decisions, such as production planning, scheduling, and route optimization. It is more difficult to solve than Continuous LP but is much more applicable to real-world situations."),
                "best_for": _("Integer solution required problems, linear constraints, exact optimization."),
                "category": "Mathematical",
                "parameters": {
                    "time_limit": {"type": "int", "default": 300, "description": _("Maximum solving time in seconds.")}
                }
            },
            AlgorithmType.GENETIC_LOCAL_SEARCH: {
                "name": _("Genetic Local Search"),
                "description": _("Genetic Local Search is a hybrid optimization algorithm that combines the strengths of both genetic algorithms and local search. It uses a population of candidate solutions and applies genetic operators (mutation, crossover, and selection) to generate new solutions. The algorithm then uses a local search strategy to refine the solutions, often using a neighborhood structure to explore the solution space. This approach allows the algorithm to balance exploration and exploitation, leading to better solutions in many cases."),
                "best_for": _("Hybrid optimization, local improvement required problems, global search + local search."),
                "category": "Hybrid",
                "parameters": {
                    "population_size": {"type": "int", "default": 50, "description": _("Number of individuals in the population.")}
                }
            }
        }

        if algorithm_type in algorithm_info:
            return algorithm_info[algorithm_type]
        else:
            return {
                "name": _("Unknown Algorithm"),
                "description": _("Information not available."),
                "best_for": _("Unknown."),
                "parameters": {}
            }

    @staticmethod
    def list_algorithms() -> List[Dict[str, Any]]:
        """
        List all available algorithms with their information.

        Returns:
            List[Dict[str, Any]]: List of algorithm information.
        """
        algorithms = []
        for algorithm_type in AlgorithmType:
            info = AlgorithmService.get_algorithm_info(algorithm_type)
            algorithms.append({
                "type": algorithm_type,
                "name": info["name"],
                "description": info["description"],
                "best_for": info["best_for"]
            })
        return algorithms

    @staticmethod
    def sanitize_for_json(obj: Any) -> Any:
        """
        Recursively sanitize values for JSON compatibility.
        Converts float('inf'), float('-inf'), and float('nan') to None.
        PostgreSQL JSON doesn't support these special float values.
        """
        if obj is None:
            return None
        
        if isinstance(obj, float):
            if math.isinf(obj) or math.isnan(obj):
                return None
            return obj
        
        if isinstance(obj, dict):
            return {k: AlgorithmService.sanitize_for_json(v) for k, v in obj.items()}
        
        if isinstance(obj, list):
            return [AlgorithmService.sanitize_for_json(item) for item in obj]
        
        if isinstance(obj, tuple):
            return tuple(AlgorithmService.sanitize_for_json(item) for item in obj)
        
        return obj

    @staticmethod
    def recommend_algorithm(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend the best algorithm based on the input data.

        Args:
            data: Input data for the algorithm.

        Returns:
            Dict[str, Any]: Recommended algorithm information.
        """
        # Extract relevant information from the data
        projects = data.get("projects", [])
        instructors = data.get("instructors", [])
        classrooms = data.get("classrooms", [])
        timeslots = data.get("timeslots", [])

        # Calculate problem size
        problem_size = len(projects) * len(classrooms) * len(timeslots)

        # Determine the complexity of the problem
        if problem_size < 1000:
            # Small problem size
            if len(projects) < 20:
                # Very small problem
                return AlgorithmService.get_algorithm_info(AlgorithmType.SIMPLEX)
            else:
                # Small to medium problem
                return AlgorithmService.get_algorithm_info(AlgorithmType.GREEDY)
        elif problem_size < 10000:
            # Medium problem size
            if len(instructors) > 50:
                # Many instructors, focus on load balancing
                return AlgorithmService.get_algorithm_info(AlgorithmType.NSGA_II)
            else:
                # Focus on classroom changes
                return AlgorithmService.get_algorithm_info(AlgorithmType.TABU_SEARCH)
        else:
            # Large problem size
            if len(classrooms) < 10:
                # Few classrooms, focus on time optimization
                return AlgorithmService.get_algorithm_info(AlgorithmType.ANT_COLONY)
            else:
                # Complex problem with many variables
                return AlgorithmService.get_algorithm_info(AlgorithmType.GENETIC_ALGORITHM)

    @staticmethod
    async def run_algorithm(algorithm_type, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> Tuple[Dict[str, Any], AlgorithmRun]:
        """
        Run the specified algorithm with the given data and parameters.

        Args:
            algorithm_type: The algorithm type to run (can be AlgorithmType enum or string).
            data: Input data for the algorithm.
            params: Algorithm parameters.
            user_id: User ID for WebSocket progress tracking.

        Returns:
            Tuple[Dict[str, Any], AlgorithmRun]: Algorithm result and run record.
        """
        # Convert string to AlgorithmType enum if necessary
        if isinstance(algorithm_type, str):
            algorithm_type = AlgorithmType(algorithm_type.lower())
        
        start_time = time.time()

        logger.info(f"Starting algorithm {algorithm_type} with {len(data.get('projects', []))} projects, {len(data.get('instructors', []))} instructors, {len(data.get('classrooms', []))} classrooms, {len(data.get('timeslots', []))} timeslots")

        # Create algorithm run record
        # Ensure algorithm_type is converted to string value for database
        algorithm_type_str = algorithm_type.value if isinstance(algorithm_type, AlgorithmType) else str(algorithm_type)
        algorithm_run_data = AlgorithmRunCreate(
            algorithm_type=algorithm_type_str,
            parameters=params or {},
            data=data or {},
            status="running",
            started_at=datetime.now()
        )

        from app.db.base import async_session
        async with async_session() as db:
            algorithm_run = await crud_algorithm.create(db, obj_in=algorithm_run_data)
            algorithm_run_id = algorithm_run.id  # Cache ID to avoid lazy loading issues

            try:
                # WebSocket progress tracking - başlangıç
                if user_id:
                    from app.api.v1.endpoints.websocket import update_algorithm_progress
                    await update_algorithm_progress(
                        user_id, algorithm_run.id, 0, "starting",
                        f"Algorithm {algorithm_type.value} is starting..."
                    )

                # Load data for all algorithms including Greedy
                if not data or not any(data.values()):
                    print("AlgorithmService: Loading real data...")
                    classroom_count = params.get("classroom_count", 7) if params else 7
                    data = await AlgorithmService._get_real_data(db, classroom_count)
                
                # CRITICAL: Add classroom_count to data dictionary so algorithms can access it
                # Algoritmalar data.get("classroom_count") ile kontrol ediyor
                if params and "classroom_count" in params:
                    data["classroom_count"] = params["classroom_count"]
                    logger.info(f"AlgorithmService: Added classroom_count={params['classroom_count']} to data dictionary")
                
                # CRITICAL: Add entire params dictionary to data so algorithms can access all parameters
                # Bu, NSGA-II, SA, GA gibi algoritmaların data.get('params') ile parametrelere erişmesini sağlar
                # Özellikle project_priority parametresi için gerekli!
                if params:
                    data["params"] = params
                    logger.info(f"AlgorithmService: Added params to data dictionary: {params}")

                # Create algorithm instance
                algorithm = AlgorithmFactory().create_algorithm(
                    algorithm_name=algorithm_type.value,
                    params=params
                )
                
                # DEBUG: Log jury refinement parameters
                logger.info("ALGORITHM SERVICE DEBUG:")
                logger.info(f"  Algorithm type: {algorithm_type.value}")
                logger.info(f"  Parameters: {params}")
                logger.info(f"  Jury refinement layer: {params.get('jury_refinement_layer', True) if params else True}")
                logger.info(f"  Algorithm instance: {type(algorithm)}")

                # WebSocket progress tracking - başlatıldı
                if user_id:
                    await update_algorithm_progress(
                        user_id, algorithm_run.id, 10, "running",
                        f"Algorithm {algorithm_type.value} is running..."
                    )

                # Run algorithm and get result
                print(f"AlgorithmService Debug: Passing data with {len(data.get('projects', []))} projects to algorithm")
                result = algorithm.execute(data)
                print(f"AlgorithmService Debug: Algorithm returned result: {result}")
                
                # DEBUG: Check algorithm name in result
                if isinstance(result, dict):
                    algorithm_name = result.get('algorithm', 'Unknown')
                    print(f"AlgorithmService Debug: Algorithm name in result: {algorithm_name}")
                else:
                    print(f"AlgorithmService Debug: Result is not dict: {type(result)}")

                # ============================================================
                # FALLBACK: Eğer algoritma boş sonuç veya failed döndürdüyse
                # ComprehensiveOptimizer'a fallback yap (PSO hariç)
                # ============================================================
                should_fallback = False
                if isinstance(result, dict):
                    result_status = result.get('status', '').lower()
                    has_assignments = bool(result.get('assignments') or result.get('schedule') or result.get('solution'))
                    
                    # PSO için fallback yapma - kendi mantığı var
                    is_pso = 'pso' in str(algorithm_type).lower() or 'pso' in result.get('algorithm', '').lower()
                    
                    if not is_pso and (result_status in ('failed', 'error', 'infeasible') or not has_assignments):
                        should_fallback = True
                        logger.info(f"Algorithm {algorithm_type} returned empty/failed result, falling back to ComprehensiveOptimizer")
                
                if should_fallback:
                    try:
                        logger.info("FALLBACK: Running ComprehensiveOptimizer due to empty/failed result")
                        fallback_algo = AlgorithmFactory().create_algorithm(
                            algorithm_name="comprehensive_optimizer",
                            params=params or {}
                        )
                        
                        fallback_algo.initialize(data)
                        fallback_result = fallback_algo.optimize(data)
                        
                        if fallback_result and (fallback_result.get('assignments') or fallback_result.get('schedule') or fallback_result.get('solution')):
                            # Fallback başarılı - sonucu kullan
                            result = {
                                **(fallback_result or {}),
                                "fallback_used": True,
                                "fallback_from": algorithm_type.value if hasattr(algorithm_type, 'value') else str(algorithm_type),
                                "original_status": result.get('status', 'unknown'),
                                "status": "completed"
                            }
                            logger.info(f"FALLBACK SUCCESS: ComprehensiveOptimizer returned {len(result.get('assignments', []))} assignments")
                        else:
                            logger.warning("FALLBACK: ComprehensiveOptimizer also returned empty result")
                    except Exception as fallback_error:
                        logger.error(f"FALLBACK ERROR: {fallback_error}")

                # 🎯 JURY REFINEMENT - DISABLED FOR GENETIC ALGORITHM
                # Genetic Algorithm has its own jury refinement system
                # Service level jury refinement causes conflicts
                try:
                    if isinstance(result, dict) and params.get('jury_refinement_layer', True):
                        # Check if this is Genetic Algorithm - if so, skip service level refinement
                        algorithm_name = result.get('algorithm', '').lower()
                        if 'genetic' in algorithm_name:
                            logger.info("🎯 SKIPPING SERVICE LEVEL JURY REFINEMENT FOR GENETIC ALGORITHM")
                            logger.info("   Genetic Algorithm has its own integrated jury refinement system")
                        else:
                            logger.info("🎯 APPLYING JURY REFINEMENT AT SERVICE LEVEL")
                            for key in ("schedule", "assignments", "solution"):
                                lst = result.get(key)
                                if isinstance(lst, list) and lst:
                                    try:
                                        # Apply jury refinement using base class method
                                        refined = algorithm.apply_jury_refinement(lst, enable_refinement=True)
                                        if refined and len(refined) > 0:
                                            result[key] = refined
                                            logger.info(f"✅ Jury refinement applied to {key}")
                                    except Exception as e:
                                        logger.warning(f"⚠️ Jury refinement failed for {key}: {e}")
                except Exception as e:
                    logger.warning(f"⚠️ Service-level jury refinement failed: {e}")

                # 🔧 INSTRUCTOR DATA ENRICHMENT - DISABLED FOR DEBUGGING
                # This causes issues with jury filtering in frontend
                # Frontend expects only instructor IDs, not full objects
                try:
                    if isinstance(result, dict):
                        logger.info("🔧 SKIPPING INSTRUCTOR DATA ENRICHMENT FOR DEBUGGING")
                        logger.info("   Frontend expects only instructor IDs, not full objects")
                        logger.info("   This prevents jury filtering issues")
                        
                        # Log current instructor data format
                        for key in ("schedule", "assignments", "solution"):
                            lst = result.get(key)
                            if isinstance(lst, list) and lst:
                                for assignment in lst[:3]:  # First 3 assignments
                                    if isinstance(assignment, dict) and 'instructors' in assignment:
                                        instructors = assignment.get('instructors', [])
                                        logger.info(f"   {key} assignment {assignment.get('project_id')}: instructors format = {type(instructors[0]) if instructors else 'empty'}")
                                        break
                except Exception as e:
                    logger.warning(f"⚠️ Instructor data enrichment check failed: {e}")

                # 🔧 INSTRUCTOR DATA ENRICHMENT - DISABLED FOR DEBUGGING (SECOND BLOCK)
                # This causes issues with jury filtering in frontend
                # Frontend expects only instructor IDs, not full objects
                try:
                    if isinstance(result, dict):
                        logger.info("🔧 SKIPPING SECOND INSTRUCTOR DATA ENRICHMENT FOR DEBUGGING")
                        logger.info("   Frontend expects only instructor IDs, not full objects")
                        logger.info("   This prevents jury filtering issues")
                except Exception as e:
                    logger.warning(f"⚠️ Second instructor data enrichment check failed: {e}")

                # Enforce global gap-free compaction, late-slot removal and reporting at service level
                try:
                    if isinstance(result, dict):
                        # Use GapFreeScheduler + iterative reflow to aggressively remove gaps and late slots
                        gap_scheduler = GapFreeScheduler()

                        max_iters = 8
                        for iteration in range(max_iters):
                            improved = False
                            for key in ("schedule", "assignments", "solution"):
                                lst = result.get(key)
                                if not isinstance(lst, list) or not lst:
                                    continue

                                # 1) Local and global compaction
                                try:
                                    algorithm._compact_schedule_classrooms(lst)  # type: ignore[attr-defined]
                                except Exception:
                                    pass
                                try:
                                    algorithm._compact_schedule_globally(lst)  # type: ignore[attr-defined]
                                except Exception:
                                    pass

                                # 2) Gap-free optimizer from service - attempt to create continuous blocks
                                try:
                                    before = gap_scheduler.validate_gap_free_schedule(lst).get("total_gaps", 0)
                                    optimized = gap_scheduler.optimize_for_gap_free(lst, getattr(algorithm, "timeslots", []))
                                    # If optimizer returned something, replace list in-place
                                    if optimized and len(optimized) > 0:
                                        # replace contents preserving list object
                                        lst.clear()
                                        lst.extend(optimized)
                                    after = gap_scheduler.validate_gap_free_schedule(lst).get("total_gaps", 0)
                                    if after < before:
                                        improved = True
                                except Exception:
                                    pass

                                # 3) Try to move late assignments earlier
                                try:
                                    before_late = AlgorithmService._count_late_slots_static(lst, getattr(algorithm, "timeslots", []))
                                    AlgorithmService._remove_late_assignments(
                                        lst,
                                        getattr(algorithm, "timeslots", []),
                                        getattr(algorithm, "classrooms", []),
                                        getattr(algorithm, "instructors", []),
                                    )
                                    after_late = AlgorithmService._count_late_slots_static(lst, getattr(algorithm, "timeslots", []))
                                    if after_late < before_late:
                                        improved = True
                                except Exception:
                                    pass

                                # 4) Final greedy reflow earliest-first
                                try:
                                    moved = AlgorithmService._reflow_schedule_earliest_first(
                                        lst,
                                        getattr(algorithm, "timeslots", []),
                                        getattr(algorithm, "classrooms", []),
                                        getattr(algorithm, "instructors", []),
                                    )
                                    if moved > 0:
                                        improved = True
                                except Exception:
                                    pass

                            # If no improvement across all lists, break early
                            if not improved:
                                break

                        # After iterations build gap and policy summary reports
                        gap_reports = {}
                        policy_summary = {"lists": {}}
                        for key in ("schedule", "assignments", "solution"):
                            lst = result.get(key)
                            if isinstance(lst, list) and lst:
                                try:
                                    gap_reports[key] = algorithm._detect_classroom_gaps(lst)  # type: ignore[attr-defined]
                                except Exception:
                                    gap_reports[key] = {"total_gaps": None}
                                try:
                                    policy_summary["lists"][key] = AlgorithmService._summarize_schedule_policies(
                                        lst,
                                        getattr(algorithm, "timeslots", []),
                                        getattr(algorithm, "classrooms", []),
                                    )
                                except Exception:
                                    policy_summary["lists"][key] = {}
                        if gap_reports:
                            result["gap_report_service_level"] = gap_reports
                        if policy_summary.get("lists"):
                            result["policy_summary"] = policy_summary
                except Exception:
                    # Fail-safe: do not break algorithm result saving on post-processing errors
                    logger.exception("Service-level schedule post-processing failed")

                # Generic dedup for algorithms not inheriting OptimizationAlgorithm (safety net for response)
                try:
                    if isinstance(result, dict):
                        def _dedup_list(items: Any) -> Any:
                            if not isinstance(items, list):
                                return items

                            def _extract_key(obj: Any) -> Tuple[str, int, int]:
                                pid = None
                                ts = 10**9
                                room = 10**9
                                if isinstance(obj, dict):
                                    pid = obj.get("project_id", obj.get("id"))
                                    ts = obj.get("timeslot_id", ts)
                                    room = obj.get("classroom_id", room)
                                else:
                                    pid = getattr(obj, "project_id", getattr(obj, "id", None))
                                    ts = getattr(obj, "timeslot_id", ts)
                                    room = getattr(obj, "classroom_id", room)
                                key = str(pid) if pid is not None else ""
                                try:
                                    ts_val = int(ts)
                                except Exception:
                                    ts_val = 10**9
                                try:
                                    room_val = int(room)
                                except Exception:
                                    room_val = 10**9
                                return key, ts_val, room_val

                            seen: Dict[str, Any] = {}
                            for it in items:
                                key, ts_val, room_val = _extract_key(it)
                                if not key:
                                    continue
                                prev = seen.get(key)
                                if prev is None:
                                    seen[key] = it
                                else:
                                    _, prev_ts, prev_room = _extract_key(prev)
                                    if (ts_val, room_val) < (prev_ts, prev_room):
                                        seen[key] = it
                            return list(seen.values()) if seen else items

                        if "schedule" in result:
                            result["schedule"] = _dedup_list(result.get("schedule"))
                        if "assignments" in result:
                            result["assignments"] = _dedup_list(result.get("assignments"))
                        if "solution" in result:
                            sol = result.get("solution")
                            if isinstance(sol, list) and any(isinstance(x, dict) and ("project_id" in x) for x in sol):
                                result["solution"] = _dedup_list(sol)
                except Exception as _e:
                    logger.error(f"Response dedup failed: {_e}")
                schedules_len = len(result.get('schedule', [])) if isinstance(result, dict) else (len(result) if isinstance(result, list) else 0)
                print(f"AlgorithmService Debug: Algorithm returned result with {schedules_len} schedules")

                # Save schedules to database if result contains schedule data
                if result:
                    print(f"DEBUG: Saving schedules to database. Result type: {type(result)}")
                    print(f"DEBUG: Result content: {result}")
                    await AlgorithmService._save_schedules_to_db(db, result)
                    print("DEBUG: Schedules saved to database")
                else:
                    print("DEBUG: No result to save to database")

                # WebSocket progress tracking - tamamlandı
                if user_id:
                    from app.api.v1.endpoints.websocket import complete_algorithm
                    await complete_algorithm(user_id, algorithm_run.id, result)

                # Calculate execution time
                execution_time = time.time() - start_time

                # Determine final status - result içindeki status'ü kontrol et
                # Eğer result içinde "status" varsa ve "error" ise, yine de "completed" olarak kaydet
                # çünkü algoritma çalıştı ve sonuç döndü (hata olsa bile)
                final_status = "completed"
                if isinstance(result, dict):
                    result_status = result.get("status", "").lower()
                    # Eğer result içinde "error" status varsa, yine de "completed" olarak kaydet
                    # çünkü algoritma çalıştı ve sonuç döndü
                    if result_status in ("error", "failed", "infeasible"):
                        # Sonuç döndü ama hata var - yine de "completed" olarak kaydet
                        # çünkü algoritma çalıştı ve sonuç döndü
                        final_status = "completed"
                    elif result_status == "completed":
                        final_status = "completed"
                    else:
                        # Diğer durumlarda da "completed" olarak kaydet
                        final_status = "completed"

                # Update algorithm run record
                # Sanitize result to remove infinity/nan values (PostgreSQL JSON incompatible)
                sanitized_result = AlgorithmService.sanitize_for_json(result)
                algorithm_run_update = AlgorithmRunUpdate(
                    status=final_status,
                    result=sanitized_result,
                    execution_time=execution_time,
                    completed_at=datetime.now()
                )
                algorithm_run = await crud_algorithm.update(db, db_obj=algorithm_run, obj_in=algorithm_run_update)

                return result, algorithm_run

            except Exception as e:
                import traceback
                error_traceback = traceback.format_exc()
                logger.error(f"=== ALGORITHM ERROR ===")
                logger.error(f"Algorithm: {algorithm_type}")
                logger.error(f"Error Type: {type(e).__name__}")
                logger.error(f"Error Message: {str(e)}")
                logger.error(f"Full Traceback:\n{error_traceback}")
                logger.error(f"======================")

                # FALLBACK: Comprehensive Optimizer ile çalıştır ve sonuç dön
                try:
                    logger.info("Falling back to Comprehensive Optimizer due to error")
                    fallback_algo = AlgorithmFactory().create_algorithm(
                        algorithm_name="comprehensive_optimizer",
                        params=params or {}
                    )

                    # Ensure data exists
                    if not data or not any(data.values()):
                        data = await AlgorithmService._get_real_data(db)

                    fallback_algo.initialize(data)
                    fallback_result = fallback_algo.optimize(data)

                    # Save schedules
                    if fallback_result:
                        await AlgorithmService._save_schedules_to_db(db, fallback_result)

                    # Update run as completed with fallback
                    execution_time = time.time() - start_time
                    fallback_result_dict = {
                        **(fallback_result or {}),
                        "fallback_used": True,
                        "fallback_from": algorithm_type.value if hasattr(algorithm_type, 'value') else str(algorithm_type),
                        "original_error": str(e),
                        "status": "completed"  # Fallback sonucu da "completed" olarak işaretle
                    }
                    algorithm_run_update = AlgorithmRunUpdate(
                        status="completed",  # Her zaman "completed" olarak kaydet
                        result=AlgorithmService.sanitize_for_json(fallback_result_dict),
                        execution_time=execution_time,
                        completed_at=datetime.now()
                    )
                    algorithm_run = await crud_algorithm.update(db, db_obj=algorithm_run, obj_in=algorithm_run_update)

                    # WebSocket: report completion with fallback
                    if user_id:
                        from app.api.v1.endpoints.websocket import complete_algorithm
                        await complete_algorithm(user_id, algorithm_run.id, algorithm_run_update.result)  # type: ignore

                    return algorithm_run_update.result, algorithm_run  # type: ignore
                except Exception as fe:
                    # WebSocket progress tracking - hata
                    if user_id:
                        from app.api.v1.endpoints.websocket import fail_algorithm
                        try:
                            await fail_algorithm(user_id, algorithm_run_id, f"Fallback failed: {fe}")
                        except Exception:
                            pass  # Ignore websocket errors during error handling

                    # Update algorithm run record with error
                    algorithm_run_update = AlgorithmRunUpdate(
                        status="failed",
                        error=f"{str(e)} | Fallback failed: {str(fe)}",
                        completed_at=datetime.now()
                    )
                    
                    # Start a new transaction for the update
                    try:
                        await db.rollback()
                    except Exception:
                        pass
                    
                    algorithm_run = await crud_algorithm.update(db, db_obj=algorithm_run, obj_in=algorithm_run_update)

                    # Re-raise the original exception
                    raise e

    @staticmethod
    async def _save_schedules_to_db(db, result: Dict[str, Any]) -> None:
        """
        Save algorithm results to schedules table
        
        Args:
            db: Database session
            result: Algorithm result containing schedule data
        """
        print(f"DEBUG: _save_schedules_to_db called with result type: {type(result)}")
        print(f"DEBUG: _save_schedules_to_db result content: {result}")
        
        try:
            from sqlalchemy import delete
            from app.models.schedule import Schedule
            
            # Clear existing schedules
            await db.execute(delete(Schedule))
            print("DEBUG: Existing schedules cleared")
            
            # Extract schedule data from different possible formats
            schedules = []
            
            # Format 0: Phase 3 "final_assignments" key (öncelikli, placeholder ile)
            if "final_assignments" in result and result["final_assignments"]:
                schedules = result["final_assignments"]
            # Format 1: Direct "schedule" key
            elif "schedule" in result and result["schedule"]:
                schedules = result["schedule"]
            # Format 2: "assignments" key
            elif "assignments" in result and result["assignments"]:
                schedules = result["assignments"]
            # Format 3: Direct list in result
            elif isinstance(result, list):
                schedules = result
            # Format 4: "solution" key
            elif "solution" in result and result["solution"]:
                schedules = result["solution"]
            
            # Ensure schedules is a list
            if not isinstance(schedules, list):
                logger.warning(f"Invalid schedule format: {type(schedules)}")
                return
            
            # Final guard: deduplicate by project_id before saving (keep earliest timeslot_id)
            try:
                def _normalize_entry(item: Any) -> Optional[Dict[str, Any]]:
                    if isinstance(item, dict):
                        return {
                            "project_id": item.get("project_id"),
                            "classroom_id": item.get("classroom_id"),
                            "timeslot_id": item.get("timeslot_id"),
                            "is_makeup": item.get("is_makeup", False),
                            "instructors": item.get("instructors", []),  # Jüri üyeleri
                        }
                    try:
                        return {
                            "project_id": getattr(item, "project_id", getattr(item, "id", None)),
                            "classroom_id": getattr(item, "classroom_id", None),
                            "timeslot_id": getattr(item, "timeslot_id", None),
                            "is_makeup": getattr(item, "is_makeup", False),
                            "instructors": getattr(item, "instructors", []),  # Jüri üyeleri
                        }
                    except Exception:
                        return None

                def _key(entry: Dict[str, Any]) -> str:
                    pid = entry.get("project_id")
                    return str(pid) if pid is not None else ""

                def _order(entry: Dict[str, Any]) -> Tuple[int, int]:
                    try:
                        ts_val = int(entry.get("timeslot_id", 10**9))
                    except Exception:
                        ts_val = 10**9
                    try:
                        room_val = int(entry.get("classroom_id", 10**9))
                    except Exception:
                        room_val = 10**9
                    return ts_val, room_val

                by_project: Dict[str, Dict[str, Any]] = {}
                for raw in schedules:
                    normalized = _normalize_entry(raw)
                    if not normalized:
                        continue
                    key = _key(normalized)
                    if not key:
                        continue
                    prev = by_project.get(key)
                    if prev is None or _order(normalized) < _order(prev):
                        by_project[key] = normalized
                if by_project and len(by_project) != len(schedules):
                    logger.warning(
                        "Duplicate projects pruned before save | total=%s unique=%s removed=%s",
                        len(schedules), len(by_project), len(schedules) - len(by_project),
                    )
                schedules = list(by_project.values()) if by_project else schedules
            except Exception as e:
                logger.error(f"Dedup before save failed: {e}")

            # Add new schedules
            saved_count = 0
            for schedule_data in schedules:
                # Handle different data structures
                if isinstance(schedule_data, dict):
                    project_id = schedule_data.get("project_id")
                    classroom_id = schedule_data.get("classroom_id")
                    timeslot_id = schedule_data.get("timeslot_id")
                    is_makeup = schedule_data.get("is_makeup", False)
                    instructors = schedule_data.get("instructors", [])  # Jüri üyeleri
                    
                    # Validate required fields
                    if project_id and classroom_id and timeslot_id:
                        schedule = Schedule(
                            project_id=project_id,
                            classroom_id=classroom_id,
                            timeslot_id=timeslot_id,
                            is_makeup=is_makeup,
                            instructors=instructors  # Jüri üyelerini kaydet
                        )
                        db.add(schedule)
                        saved_count += 1
                    else:
                        logger.warning(f"Invalid schedule data: {schedule_data}")
            
            await db.commit()
            logger.info(f"Saved {saved_count} schedules to database")
            
        except Exception as e:
            logger.error(f"Error saving schedules to database: {str(e)}")
            await db.rollback()
            raise e

    # Internal helpers -------------------------------------------------------
    def _remove_late_assignments(self, assignments: List[Dict[str, Any]], timeslots: List[Any] = None, classrooms: List[Any] = None, instructors: List[Any] = None) -> None:
        """
        Service-level late slot enforcement. Attempts to move any assignment
        scheduled at 16:30 or later into the earliest feasible pre-16:30 slot.
        If no feasible slot exists, the assignment remains but is marked with
        a heavy penalty flag for downstream reporting/UI.

        Modifies the given assignments list in-place.
        """
        try:
            if not assignments:
                return
            # Build simple lookup/indexing using algorithm-like helpers
            # Timeslots and classrooms may be needed for feasibility checks
            timeslots = timeslots or []
            classrooms = classrooms or []
            instructors = instructors or []

            # Local functions to identify late slots and parse ordering
            def is_late_slot(ts: Any) -> bool:
                try:
                    start = ts.get("start_time", "") if isinstance(ts, dict) else getattr(ts, "start_time", "")
                    parts = str(start).split(":")
                    hour = int(parts[0]) if parts and parts[0].isdigit() else 0
                    minute = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                    return hour > 16 or (hour == 16 and minute >= 30)
                except Exception:
                    return False

            # Build ordered slot ids and id->ts map
            def parse_start(ts: Any) -> tuple:
                try:
                    s = ts.get("start_time") if isinstance(ts, dict) else getattr(ts, "start_time", None)
                    from datetime import datetime as _dt
                    for fmt in ("%H:%M:%S", "%H:%M"):
                        try:
                            dt = _dt.strptime(str(s), fmt)
                            return (dt.hour, dt.minute, dt.second)
                        except Exception:
                            continue
                except Exception:
                    pass
                return (24, 0, 0)

            ts_list = list(timeslots) if isinstance(timeslots, list) else []
            ts_en = list(enumerate(ts_list))
            ts_en.sort(key=lambda item: (parse_start(item[1]), item[0]))
            id_to_ts: Dict[Any, Any] = {}
            sorted_ids: List[Any] = []
            ts_index: Dict[Any, int] = {}
            for idx, ts in ts_en:
                tid = ts.get("id") if isinstance(ts, dict) else getattr(ts, "id", idx)
                if tid is None:
                    tid = idx
                id_to_ts[tid] = ts
                sorted_ids.append(tid)
                ts_index[tid] = len(sorted_ids) - 1

            # Determine last acceptable index (<16:30)
            last_ok_idx = len(sorted_ids) - 1
            for i, tid in enumerate(sorted_ids):
                ts = id_to_ts.get(tid)
                if ts and is_late_slot(ts):
                    last_ok_idx = i - 1
                    break

            if last_ok_idx < 0:
                # No acceptable slots; just flag all as late
                for a in assignments:
                    a["late_penalized"] = True
                return

            # Build occupancy and instructor busy maps
            occupied: Dict[tuple, bool] = {}
            instructor_busy: Dict[Any, set] = {}
            classroom_ids: List[Any] = []
            for c in classrooms or []:
                try:
                    cid = c.get("id") if isinstance(c, dict) else getattr(c, "id", None)
                    if cid is not None:
                        classroom_ids.append(cid)
                except Exception:
                    continue
            if not classroom_ids:
                # Infer from assignments
                for a in assignments:
                    cid = a.get("classroom_id") if isinstance(a, dict) else None
                    if cid is not None and cid not in classroom_ids:
                        classroom_ids.append(cid)

            for a in assignments:
                if not isinstance(a, dict):
                    continue
                idx = ts_index.get(a.get("timeslot_id"))
                cid = a.get("classroom_id")
                if cid is not None and idx is not None:
                    occupied[(cid, idx)] = True
                for instr in a.get("instructors", []) or []:
                    instructor_busy.setdefault(instr, set()).add(idx)

            # Collect late assignments
            late_list: List[Dict[str, Any]] = []
            for a in assignments:
                if not isinstance(a, dict):
                    continue
                ts = id_to_ts.get(a.get("timeslot_id"))
                if ts and is_late_slot(ts):
                    late_list.append(a)

            # Try moving each late assignment
            for a in late_list:
                current_idx = ts_index.get(a.get("timeslot_id"))
                if current_idx is None:
                    a["late_penalized"] = True
                    continue
                instructors_ids = a.get("instructors", []) or []
                moved = False
                for target_idx in range(0, last_ok_idx + 1):
                    for cid in sorted(classroom_ids):
                        if occupied.get((cid, target_idx)):
                            continue
                        # Check instructor availability
                        ok = True
                        for instr in instructors_ids:
                            if target_idx in instructor_busy.get(instr, set()):
                                ok = False
                                break
                        if not ok:
                            continue
                        # Place
                        old_cid = a.get("classroom_id")
                        if old_cid is not None:
                            occupied.pop((old_cid, current_idx), None)
                        a["classroom_id"] = cid
                        a["timeslot_id"] = sorted_ids[target_idx]
                        occupied[(cid, target_idx)] = True
                        for instr in instructors_ids:
                            instructor_busy.setdefault(instr, set()).discard(current_idx)
                            instructor_busy[instr].add(target_idx)
                        moved = True
                        break
                    if moved:
                        break
                if not moved:
                    # Could not move -> flag for penalty/reporting
                    a["late_penalized"] = True
        except Exception:
            # Fail-safe: do nothing if any error occurs
            return

    def _reflow_schedule_earliest_first(self, assignments: List[Dict[str, Any]], timeslots: List[Any], classrooms: List[Any], instructors: List[Any]) -> int:
        """
        Algorithm-agnostic greedy packing:
        - Build chronological timeslot order
        - For each assignment in chronological order, try to move it to the
          earliest feasible slot (strictly earlier), any classroom
        - Feasibility: target classroom free and all instructors free in target slot
        Returns number of moved assignments.
        """
        try:
            if not assignments:
                return 0
            # Build slot ordering and maps
            from datetime import datetime as _dt
            def _parse_start(ts: Any) -> tuple:
                try:
                    s = ts.get("start_time") if isinstance(ts, dict) else getattr(ts, "start_time", None)
                    for fmt in ("%H:%M:%S", "%H:%M"):
                        try:
                            dt = _dt.strptime(str(s), fmt)
                            return (dt.hour, dt.minute, dt.second)
                        except Exception:
                            continue
                except Exception:
                    pass
                return (24, 0, 0)

            ts_en = list(enumerate(timeslots or []))
            ts_en.sort(key=lambda item: (_parse_start(item[1]), item[0]))
            ts_index: Dict[Any, int] = {}
            id_to_ts: Dict[Any, Any] = {}
            ordered_ids: List[Any] = []
            for _, ts in ts_en:
                tid = ts.get("id") if isinstance(ts, dict) else getattr(ts, "id", None)
                if tid is None:
                    tid = len(ordered_ids)
                ts_index[tid] = len(ordered_ids)
                id_to_ts[tid] = ts
                ordered_ids.append(tid)
            if not ts_index:
                return 0

            # Build classroom id list
            classroom_ids: List[Any] = []
            for c in classrooms or []:
                try:
                    cid = c.get("id") if isinstance(c, dict) else getattr(c, "id", None)
                    if cid is not None:
                        classroom_ids.append(cid)
                except Exception:
                    continue
            if not classroom_ids:
                # Infer from assignments
                for a in assignments:
                    if isinstance(a, dict):
                        cid = a.get("classroom_id")
                        if cid is not None and cid not in classroom_ids:
                            classroom_ids.append(cid)

            # Build occupancy and instructor busy maps
            occupied: Dict[Tuple[Any, int], bool] = {}
            busy: Dict[Any, set] = {}
            for a in assignments:
                if not isinstance(a, dict):
                    continue
                cid = a.get("classroom_id")
                idx = ts_index.get(a.get("timeslot_id"))
                if cid is not None and idx is not None:
                    occupied[(cid, idx)] = True
                for i in a.get("instructors", []) or []:
                    busy.setdefault(i, set()).add(idx)

            # Order assignments by current slot index to move earlier ones first
            ordered = [a for a in assignments if isinstance(a, dict) and a.get("timeslot_id") in ts_index]
            ordered.sort(key=lambda a: ts_index.get(a.get("timeslot_id"), 10**9))

            moved = 0
            for a in ordered:
                cur_idx = ts_index.get(a.get("timeslot_id"))
                if cur_idx is None:
                    continue
                instrs = a.get("instructors", []) or []
                for target_idx in range(0, cur_idx):
                    placed = False
                    for cid in classroom_ids:
                        if occupied.get((cid, target_idx)):
                            continue
                        # Instructors must be free
                        ok = True
                        for i in instrs:
                            if target_idx in busy.get(i, set()):
                                ok = False
                                break
                        if not ok:
                            continue
                        # Move
                        old_cid = a.get("classroom_id")
                        if old_cid is not None:
                            occupied.pop((old_cid, cur_idx), None)
                        a["classroom_id"] = cid
                        a["timeslot_id"] = ordered_ids[target_idx]
                        occupied[(cid, target_idx)] = True
                        for i in instrs:
                            busy.setdefault(i, set()).discard(cur_idx)
                            busy[i].add(target_idx)
                        moved += 1
                        placed = True
                        break
                    if placed:
                        break
            return moved
        except Exception:
            return 0

    def _summarize_schedule_policies(self, assignments: List[Dict[str, Any]], timeslots: List[Any], classrooms: List[Any]) -> Dict[str, Any]:
        """
        Produce a compact summary for reporting:
        - total assignments
        - count of late slots (>=16:30)
        - distribution by timeslot
        - classrooms having internal gaps after compaction
        """
        summary = {
            "total": 0,
            "late": 0,
            "by_timeslot": {},
            "classrooms_with_gap": 0,
        }
        try:
            if not assignments:
                return summary
            summary["total"] = len(assignments)
            # Build id->ts map
            id_to_ts: Dict[Any, Any] = {}
            for ts in timeslots or []:
                tid = ts.get("id") if isinstance(ts, dict) else getattr(ts, "id", None)
                if tid is not None:
                    id_to_ts[tid] = ts
            def is_late(ts: Any) -> bool:
                try:
                    start = ts.get("start_time", "") if isinstance(ts, dict) else getattr(ts, "start_time", "")
                    parts = str(start).split(":")
                    h = int(parts[0]) if parts and parts[0].isdigit() else 0
                    m = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                    return h > 16 or (h == 16 and m >= 30)
                except Exception:
                    return False
            def fmt_key(ts: Any) -> str:
                try:
                    start = str(ts.get("start_time", "")) if isinstance(ts, dict) else str(getattr(ts, "start_time", ""))
                    end = str(ts.get("end_time", "")) if isinstance(ts, dict) else str(getattr(ts, "end_time", ""))
                    sh = ":".join(start.split(":")[:2])
                    eh = ":".join(end.split(":")[:2])
                    return f"{sh}-{eh}"
                except Exception:
                    return "unknown"
            for a in assignments:
                if not isinstance(a, dict):
                    continue
                ts = id_to_ts.get(a.get("timeslot_id"))
                if not ts:
                    continue
                key = fmt_key(ts)
                summary["by_timeslot"][key] = summary["by_timeslot"].get(key, 0) + 1
                if is_late(ts):
                    summary["late"] += 1
            # Gap detection via simple per-classroom continuity check
            from collections import defaultdict
            ts_order: Dict[Any, int] = {}
            ordered = []
            # Build ordering
            def parse_start(ts: Any) -> tuple:
                try:
                    s = ts.get("start_time") if isinstance(ts, dict) else getattr(ts, "start_time", None)
                    from datetime import datetime as _dt
                    for fmt in ("%H:%M:%S", "%H:%M"):
                        try:
                            dt = _dt.strptime(str(s), fmt)
                            return (dt.hour, dt.minute, dt.second)
                        except Exception:
                            continue
                except Exception:
                    pass
                return (24, 0, 0)
            ts_en = list(enumerate(timeslots or []))
            ts_en.sort(key=lambda item: (parse_start(item[1]), item[0]))
            for idx, ts in ts_en:
                tid = ts.get("id") if isinstance(ts, dict) else getattr(ts, "id", idx)
                ts_order[tid] = len(ordered)
                ordered.append(tid)
            per_class: Dict[Any, list] = defaultdict(list)
            for a in assignments:
                if not isinstance(a, dict):
                    continue
                cid = a.get("classroom_id")
                tid = a.get("timeslot_id")
                if cid is None or tid not in ts_order:
                    continue
                per_class[cid].append(ts_order[tid])
            gaps = 0
            for cid, idxs in per_class.items():
                s = sorted(set(idxs))
                for prev, curr in zip(s, s[1:]):
                    if curr - prev > 1:
                        gaps += 1
                        break
            summary["classrooms_with_gap"] = gaps
        except Exception:
            return summary
        return summary

    @staticmethod
    async def _get_real_data(db, classroom_count: int = 7) -> Dict[str, Any]:
        """
        Get real data from database for algorithm execution
        
        Args:
            db: Database session
            classroom_count: Number of classrooms to use (default: 7)
            
        Returns:
            Dict[str, Any]: Real data from database
        """
        try:
            from sqlalchemy import select, text
            
            # Get projects with project_assistants to avoid N+1 queries
            result = await db.execute(text("""
                SELECT p.id, p.title, p.type, p.responsible_instructor_id, p.advisor_id, p.co_advisor_id,
                       STRING_AGG(pa.instructor_id::text, ',') as assistant_ids,
                       STRING_AGG(i.name, '|||') as assistant_names,
                       STRING_AGG(i.type, '|||') as assistant_types
                FROM projects p
                LEFT JOIN project_assistants pa ON p.id = pa.project_id
                LEFT JOIN instructors i ON pa.instructor_id = i.id
                GROUP BY p.id, p.title, p.type, p.responsible_instructor_id, p.advisor_id, p.co_advisor_id
            """))
            projects_data = result.fetchall()
            
            # Get instructors with project counts (instructors tablosunda 'type' sutunu var)
            result = await db.execute(text("SELECT id, name, type, bitirme_count, ara_count, total_load FROM instructors"))
            instructors_data = result.fetchall()
            
            # Get classrooms (limit to selected count)
            result = await db.execute(text(f"SELECT id, name, capacity, location FROM classrooms ORDER BY id LIMIT {classroom_count}"))
            classrooms_data = result.fetchall()
            
            # Get timeslots
            result = await db.execute(text("SELECT id, start_time, end_time, session_type, is_morning FROM timeslots"))
            timeslots_data = result.fetchall()
            
            # Format data
            data = {
                "projects": [
                    {
                        "id": row[0],
                        "title": row[1],
                        "type": row[2].lower() if row[2] else "ara",
                        "project_type": row[2].lower() if row[2] else "ara",  # Standart alan
                        "instructor_id": row[3] or 1,  # FIXED: instructor_id kullan (tüm algoritmalarla uyumlu)
                        "responsible_id": row[3] or 1,  # Geriye uyumluluk
                        "responsible_instructor_id": row[3] or 1,  # Jury refinement için gerekli
                        "advisor_id": row[4],
                        "co_advisor_id": row[5],
                        "assistant_ids": [int(x) for x in row[6].split(',')] if row[6] else [],
                        "assistant_instructors": [
                            {
                                "id": int(assistant_id),
                                "name": assistant_name,
                                "type": assistant_type
                            }
                            for assistant_id, assistant_name, assistant_type in zip(
                                (row[6].split(',') if row[6] else []),
                                (row[7].split('|||') if row[7] else []),
                                (row[8].split('|||') if row[8] else [])
                            )
                        ] if row[6] and row[7] and row[8] else []
                    }
                    for row in projects_data
                ],
                "instructors": [
                    {
                        "id": row[0],
                        "name": row[1],
                        "type": row[2],
                        "bitirme_count": row[3] or 0,
                        "ara_count": row[4] or 0,
                        "total_load": row[5] or 0
                    }
                    for row in instructors_data
                ],
                "classrooms": [
                    {
                        "id": row[0],
                        "name": row[1],
                        "capacity": row[2],
                        "location": row[3] or ""
                    }
                    for row in classrooms_data
                ],
                "timeslots": [
                    {
                        "id": row[0],
                        "start_time": row[1],
                        "end_time": row[2],
                        "session_type": row[3],
                        "is_morning": bool(row[4]) if row[4] is not None else True
                    }
                    for row in timeslots_data
                ],
                "classroom_count": classroom_count  # CRITICAL: Add classroom_count to data so algorithms can access it
            }
            
            logger.info(f"Loaded real data: {len(data['projects'])} projects, {len(data['instructors'])} instructors, {len(data['classrooms'])} classrooms, {len(data['timeslots'])} timeslots, classroom_count={classroom_count}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading real data: {str(e)}")
            raise e

    @staticmethod
    async def get_run_result(run_id: int) -> Dict[str, Any]:
        """
        Get the result of an algorithm run.

        Args:
            run_id: The ID of the algorithm run.

        Returns:
            Dict[str, Any]: Algorithm run result.

        Raises:
            ValueError: If the algorithm run is not found.
        """
        from app.db.base import async_session
        async with async_session() as db:
            algorithm_run = await crud_algorithm.get(db, id=run_id)

            if not algorithm_run:
                raise ValueError(f"Algorithm run with ID {run_id} not found.")
        
        return {
                "id": algorithm_run.id,
                "algorithm_type": algorithm_run.algorithm_type,
                "parameters": algorithm_run.parameters,
                "status": algorithm_run.status,
                "result": algorithm_run.result,
                "error": algorithm_run.error,
                "execution_time": algorithm_run.execution_time,
                "started_at": algorithm_run.started_at,
                "completed_at": algorithm_run.completed_at
        }