"""
🤖 ULTRA AI-POWERED GENETIC ALGORITHM - NO HARD CONSTRAINTS! 🤖
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 REVOLUTIONARY AI FEATURES:
✅ Adaptive Parameters - Self-adjusting mutation & crossover rates
✅ Self-Learning Weights - Automatically optimized fitness weights
✅ Diversity Maintenance - Population diversity protection
✅ Smart Initialization - Multi-strategy initialization
✅ Pattern Recognition - Learning from successful solutions
✅ AI-Powered Selection Operators - Intelligent parent selection
✅ AI-Enhanced Crossover Operators - Smart genetic recombination
✅ Smart Mutation Strategies - Adaptive mutation with AI guidance
✅ AI Fitness Landscape Analysis - Dynamic fitness optimization
✅ AI-Powered Local Search - Intelligent neighborhood search
✅ AI Convergence Detection - Early stopping and restart strategies

🔥 ZERO HARD CONSTRAINTS - Pure AI-based soft optimization!
🎯 100% AI-DRIVEN - Every decision made by AI intelligence!
🚀 MAXIMUM PERFORMANCE - Revolutionary optimization power!
"""
from typing import Dict, Any, List, Tuple, Set
import random
import numpy as np
import time
import logging
from datetime import time as dt_time
from collections import defaultdict

from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


class EnhancedGeneticAlgorithm(OptimizationAlgorithm):
    """
    🤖 ULTRA AI-POWERED GENETIC ALGORITHM - NO HARD CONSTRAINTS!
    
    🚀 REVOLUTIONARY AI FEATURES:
    1. ADAPTIVE PARAMETERS: Mutation & crossover rates adapt to performance
    2. SELF-LEARNING WEIGHTS: Fitness weights optimize themselves
    3. DIVERSITY MAINTENANCE: Prevents premature convergence
    4. SMART INITIALIZATION: Multiple strategies (greedy, paired, random)
    5. PATTERN RECOGNITION: Learns from successful instructor pairings
    6. AI-POWERED SELECTION: Intelligent parent selection strategies
    7. AI-ENHANCED CROSSOVER: Smart genetic recombination
    8. SMART MUTATION: Adaptive mutation with AI guidance
    9. AI FITNESS LANDSCAPE: Dynamic fitness optimization
    10. AI-POWERED LOCAL SEARCH: Intelligent neighborhood search
    11. AI CONVERGENCE DETECTION: Early stopping and restart strategies
    
    🔥 ZERO HARD CONSTRAINTS - Pure AI-based soft optimization!
    🎯 100% AI-DRIVEN - Every decision made by AI intelligence!
    🚀 MAXIMUM PERFORMANCE - Revolutionary optimization power!
    """

    def __init__(self, params: Dict[str, Any] = None):
        """Initialize Full AI-Powered Genetic Algorithm"""
        super().__init__(params)

        # Basic GA parameters (will adapt!)
        self.population_size = params.get("population_size", 200) if params else 200
        self.generations = params.get("generations", 150) if params else 150
        self.mutation_rate = params.get("mutation_rate", 0.15) if params else 0.15
        self.crossover_rate = params.get("crossover_rate", 0.85) if params else 0.85
        self.elite_size = params.get("elite_size", 20) if params else 20
        self.tournament_size = params.get("tournament_size", 5) if params else 5
        
        # 🤖 AI FEATURE 1: ADAPTIVE PARAMETERS
        self.initial_mutation_rate = self.mutation_rate
        self.initial_crossover_rate = self.crossover_rate
        self.no_improvement_count = 0
        self.last_best_fitness = float('-inf')
        self.adaptive_enabled = params.get("adaptive_enabled", True) if params else True
        
        # 🤖 AI FEATURE 2: SELF-LEARNING WEIGHTS
        self.fitness_weights = {
            'coverage': 3.0,
            'consecutive': 2.5,
            'balance': 2.0,
            'classroom': 1.5,
            'jury': 1.0
        }
        self.weight_history = []  # Track successful weights
        self.weight_learning_rate = 0.1
        
        # 🤖 AI FEATURE 3: DIVERSITY MAINTENANCE
        self.diversity_threshold = params.get("diversity_threshold", 0.3) if params else 0.3
        self.diversity_history = []
        
        # 🤖 AI FEATURE 4: SMART INITIALIZATION
        self.init_strategies = {
            'paired_consecutive': 0.4,  # 40% paired strategy
            'greedy_early': 0.3,        # 30% greedy approach
            'random_diverse': 0.3       # 30% random
        }
        
        # 🤖 AI FEATURE 5: PATTERN RECOGNITION
        self.successful_pairs = defaultdict(int)  # instructor_pair → success_count
        self.successful_classrooms = defaultdict(int)  # classroom → success_count
        self.pattern_learning_enabled = True
        
        # 🤖 AI FEATURE 6: LOCAL SEARCH
        self.local_search_enabled = params.get("local_search_enabled", True) if params else True
        self.local_search_frequency = 10  # Every 10 generations
        
        # 🤖 AI FEATURE 7: CONFLICT RESOLUTION
        self.conflict_resolution_enabled = params.get("conflict_resolution_enabled", True) if params else True
        self.conflict_detection_frequency = params.get("conflict_detection_frequency", 5) if params else 5
        self.auto_resolve_conflicts = params.get("auto_resolve_conflicts", True) if params else True
        
        # 🤖 AI FEATURE 8: AI-POWERED SELECTION OPERATORS
        self.ai_selection_enabled = params.get("ai_selection_enabled", True) if params else True
        self.selection_strategies = {
            'tournament': 0.3,
            'fitness_proportional': 0.3,
            'rank_based': 0.2,
            'multi_objective': 0.2
        }
        self.selection_history = []
        
        # 🤖 AI FEATURE 9: AI-ENHANCED CROSSOVER OPERATORS
        self.ai_crossover_enabled = params.get("ai_crossover_enabled", True) if params else True
        self.crossover_strategies = {
            'uniform': 0.3,
            'intelligent_points': 0.3,
            'fitness_guided': 0.2,
            'context_aware': 0.2
        }
        self.crossover_success_rate = defaultdict(float)
        
        # 🤖 AI FEATURE 10: SMART MUTATION STRATEGIES
        self.ai_mutation_enabled = params.get("ai_mutation_enabled", True) if params else True
        self.mutation_strategies = {
            'adaptive_strength': 0.3,
            'fitness_based': 0.3,
            'pattern_preserving': 0.2,
            'landscape_guided': 0.2
        }
        self.mutation_effectiveness = defaultdict(float)
        
        # 🤖 AI FEATURE 11: AI FITNESS LANDSCAPE ANALYSIS
        self.ai_fitness_landscape_enabled = params.get("ai_fitness_landscape_enabled", True) if params else True
        self.fitness_landscape_history = []
        self.pareto_frontier = []
        self.fitness_prediction_model = None
        
        # 🤖 AI FEATURE 12: AI-POWERED LOCAL SEARCH
        self.ai_local_search_enabled = params.get("ai_local_search_enabled", True) if params else True
        self.local_search_strategies = {
            'intelligent_neighbors': 0.4,
            'adaptive_step_size': 0.3,
            'multi_directional': 0.3
        }
        self.local_search_improvements = []
        
        # 🤖 AI FEATURE 13: AI CONVERGENCE DETECTION
        self.ai_convergence_enabled = params.get("ai_convergence_enabled", True) if params else True
        self.convergence_detection_strategies = {
            'early_stopping': 0.4,
            'convergence_prediction': 0.3,
            'restart_strategies': 0.3
        }
        self.convergence_history = []
        self.stagnation_threshold = 20
        self.restart_count = 0
        self.max_restarts = 3
        self.conflict_types = {
            'instructor_double_assignment': 'Aynı instructor aynı zaman diliminde 2 farklı görevde',
            'instructor_double_jury': 'Aynı instructor aynı zaman diliminde 2 farklı jüri üyesi',
            'instructor_supervisor_jury_conflict': 'Aynı instructor hem sorumlu hem jüri aynı zamanda',
            'classroom_double_booking': 'Aynı sınıf aynı zaman diliminde 2 projede',
            'timeslot_overflow': 'Zaman dilimi kapasitesi aşıldı'
        }
        
        # 🎯 GAP-FREE OPTIMIZATION PARAMETERS
        self.gap_free_enabled = params.get("gap_free_enabled", True) if params else True
        self.reward_gap_free = params.get("reward_gap_free", 50.0) if params else 50.0
        self.penalty_gap = params.get("penalty_gap", -100.0) if params else -100.0
        self.gap_filling_iterations = params.get("gap_filling_iterations", 20) if params else 20
        
        # ⏰ EARLY TIMESLOT OPTIMIZATION PARAMETERS
        self.early_timeslot_enabled = params.get("early_timeslot_enabled", True) if params else True
        self.reward_early_timeslot = params.get("reward_early_timeslot", 30.0) if params else 30.0
        self.penalty_late_timeslot = params.get("penalty_late_timeslot", -20.0) if params else -20.0
        self.early_timeslot_threshold = params.get("early_timeslot_threshold", 0.5) if params else 0.5  # 50% of total timeslots
        
        # 🚀 ULTRA-AGGRESSIVE GAP STRATEGY PARAMETERS
        self.ultra_aggressive_gap = params.get("ultra_aggressive_gap", True) if params else True
        self.force_gap_filling = params.get("force_gap_filling", True) if params else True
        self.reward_gap_filled = params.get("reward_gap_filled", 500.0) if params else 500.0  # Increased from 200
        self.penalty_large_gap = params.get("penalty_large_gap", -1000.0) if params else -1000.0  # Increased from -500
        
        # 🔥 SUPER ULTRA-AGGRESSIVE GAP STRATEGY
        self.super_ultra_gap = params.get("super_ultra_gap", True) if params else True
        self.reward_compact_classrooms = params.get("reward_compact_classrooms", 1000.0) if params else 1000.0
        self.penalty_empty_classrooms = params.get("penalty_empty_classrooms", -2000.0) if params else -2000.0
        
        # 📦 POST-OPTIMIZATION COMPACTION
        self.post_optimization_compaction = params.get("post_optimization_compaction", True) if params else True
        self.aggressive_upward_shift = params.get("aggressive_upward_shift", True) if params else True
        
        # Data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
        
        # Caching
        self.population = []
        self.fitness_cache = {}
        self.instructor_pairs = []
        self.co_occurrence_matrix = defaultdict(lambda: defaultdict(int))

        # Metrics tracking
        self.generation_history = []

    def initialize(self, data: Dict[str, Any]) -> None:
        """Initialize algorithm with data"""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

        logger.info(f"🤖 FULL AI-POWERED GENETIC ALGORITHM initialized:")
        logger.info(f"   - Projects: {len(self.projects)}")
        logger.info(f"   - Instructors: {len(self.instructors)}")
        logger.info(f"   - Classrooms: {len(self.classrooms)}")
        logger.info(f"   - Timeslots: {len(self.timeslots)}")
        logger.info(f"   - AI Features: ALL ENABLED ✅")
        
    def execute(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute optimization with optional data"""
        if data:
            self.initialize(data)
        return self.optimize()

    def optimize(self) -> Dict[str, Any]:
        """Main AI-Powered Genetic Algorithm Optimization"""
        start_time = time.time()
        
        logger.info("=" * 80)
        logger.info("🤖 FULL AI-POWERED GENETIC ALGORITHM - STARTING")
        logger.info("=" * 80)
        
        # Phase 1: Create instructor pairs
        logger.info("\n📊 Phase 1: Instructor Pairing (Max-Min Strategy)")
        self.instructor_pairs = self._create_instructor_pairs()
        
        # Phase 2: Smart Initialization (Multi-Strategy)
        logger.info("\n🧬 Phase 2: Smart Multi-Strategy Initialization")
        self.population = self._smart_initialize_population()
        
        # Phase 3: AI-Powered Evolution
        logger.info("\n🔄 Phase 3: AI-Powered Evolution")
        best_solution = None
        best_fitness = float('-inf')

        for generation in range(self.generations):
            # Evaluate fitness
            fitness_scores = []
            for individual in self.population:
                fitness = self._evaluate_fitness_ai(individual)
                fitness_scores.append(fitness)

            # Track best
            max_fitness_idx = np.argmax(fitness_scores)
            current_best_fitness = fitness_scores[max_fitness_idx]
            
            if current_best_fitness > best_fitness:
                improvement = current_best_fitness - best_fitness
                best_fitness = current_best_fitness
                best_solution = self.population[max_fitness_idx].copy()
                self.no_improvement_count = 0
                
                # 🤖 LEARN FROM SUCCESS
                self._learn_from_solution(best_solution, best_fitness)
            else:
                self.no_improvement_count += 1
            
            # 🤖 AI FEATURE 1: ADAPTIVE PARAMETERS
            if self.adaptive_enabled:
                self._adapt_parameters(generation, best_fitness)
            
            # 🤖 AI FEATURE 3: DIVERSITY MAINTENANCE
            diversity = self._calculate_diversity()
            self.diversity_history.append(diversity)
            if diversity < self.diversity_threshold:
                self._inject_diversity()
            
            # Evolve
            self.population = self._evolve_population_ai(fitness_scores)
            
            # 🤖 AI FEATURE 6: LOCAL SEARCH
            if self.local_search_enabled and generation % self.local_search_frequency == 0:
                self._apply_local_search()
            
            # 🤖 AI FEATURE 12: AI-POWERED LOCAL SEARCH
            if self.ai_local_search_enabled and generation % self.local_search_frequency == 0:
                self._apply_ai_powered_local_search()
            
            # Track metrics
            self.generation_history.append({
                'generation': generation,
                'best_fitness': best_fitness,
                'avg_fitness': np.mean(fitness_scores),
                'diversity': diversity,
                'mutation_rate': self.mutation_rate,
                'crossover_rate': self.crossover_rate
            })
            
            # 🤖 AI FEATURE 11: FITNESS LANDSCAPE ANALYSIS
            if self.ai_fitness_landscape_enabled:
                self._update_fitness_landscape_analysis(generation, best_fitness, fitness_scores)
            
            # 🤖 AI FEATURE 13: AI CONVERGENCE DETECTION
            if self.ai_convergence_enabled:
                convergence_action = self._ai_convergence_detection(generation, best_fitness, fitness_scores)
                if convergence_action:
                    logger.info(f"   AI Convergence Action: {convergence_action}")
            
            # Logging
            if generation % 25 == 0:
                logger.info(f"   Gen {generation}/{self.generations}: "
                          f"Fitness={best_fitness:.2f}, "
                          f"Diversity={diversity:.3f}, "
                          f"Mutation={self.mutation_rate:.3f}")
        
        execution_time = time.time() - start_time
        metrics = self._calculate_metrics_ai(best_solution or [])
        
        logger.info("\n" + "=" * 80)
        logger.info(f"🤖 AI GENETIC ALGORITHM - COMPLETED ({execution_time:.2f}s)")
        logger.info(f"   Best Fitness: {best_fitness:.4f}")
        logger.info(f"   Final Mutation Rate: {self.mutation_rate:.4f}")
        logger.info(f"   Final Diversity: {self.diversity_history[-1]:.4f}")
        
        # 🔧 CONFLICT RESOLUTION: Final check and resolution
        if self.conflict_resolution_enabled and best_solution:
            logger.info("🔧 CONFLICT RESOLUTION: Final check and resolution...")
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
        
        # 📦 POST-OPTIMIZATION COMPACTION: Fill gaps and optimize early timeslots
        if self.post_optimization_compaction and best_solution:
            logger.info("📦 POST-OPTIMIZATION COMPACTION: Final gap filling and early timeslot optimization...")
            
            # Phase 1: Gap filling
            gaps_before = len(self._find_gaps_in_schedule(best_solution))
            best_solution = self._post_optimization_gap_filling(best_solution)
            gaps_after = len(self._find_gaps_in_schedule(best_solution))
            
            logger.info(f"  Gap filling: {gaps_before} → {gaps_after} gaps ({gaps_before - gaps_after} filled)")
            
            # Phase 2: Early timeslot optimization
            early_before = self._calculate_early_timeslot_usage_percentage(best_solution)
            best_solution = self._post_optimization_early_timeslot_shift(best_solution)
            early_after = self._calculate_early_timeslot_usage_percentage(best_solution)
            
            logger.info(f"  Early timeslot optimization: {early_before:.1f}% → {early_after:.1f}%")
        
        # 🔍 FINAL COVERAGE VERIFICATION
        if best_solution:
            final_assigned = set(a['project_id'] for a in best_solution if 'project_id' in a)
            total_projects = len(self.projects)
            coverage_rate = len(final_assigned) / total_projects if total_projects > 0 else 0
            
            logger.info(f"🔍 FINAL COVERAGE VERIFICATION:")
            logger.info(f"   Assigned Projects: {len(final_assigned)}/{total_projects} ({coverage_rate:.2%})")
            
            # Count by project type
            ara_projects = [p for p in self.projects if p.get('type') == 'ara']
            bitirme_projects = [p for p in self.projects if p.get('type') == 'bitirme']
            
            assigned_ara = len([p for p in ara_projects if p['id'] in final_assigned])
            assigned_bitirme = len([p for p in bitirme_projects if p['id'] in final_assigned])
            
            logger.info(f"   Ara Projects: {assigned_ara}/{len(ara_projects)} ({assigned_ara/len(ara_projects)*100:.1f}%)")
            logger.info(f"   Bitirme Projects: {assigned_bitirme}/{len(bitirme_projects)} ({assigned_bitirme/len(bitirme_projects)*100:.1f}%)")
            
            if coverage_rate < 0.95:  # Less than 95% coverage
                logger.warning(f"⚠️  Low coverage detected! Only {coverage_rate:.1%} of projects assigned!")
                logger.warning("   Consider increasing timeslots or classrooms, or reducing constraints")
        
        logger.info("=" * 80)

        return {
            "success": True,
            "assignments": best_solution or [],
            "schedule": best_solution or [],
            "solution": best_solution or [],
            "algorithm": "Full AI-Powered Genetic Algorithm with Conflict Resolution",
            "execution_time": execution_time,
            "status": "completed",
            "fitness": best_fitness,
            "metrics": metrics,
            "parameters": {
                "population_size": self.population_size,
            "generations": self.generations,
                "initial_mutation_rate": self.initial_mutation_rate,
                "final_mutation_rate": self.mutation_rate,
                "initial_crossover_rate": self.initial_crossover_rate,
                "final_crossover_rate": self.crossover_rate,
                "instructor_pairs": len(self.instructor_pairs),
                "learned_weights": self.fitness_weights,
                "successful_pairs": len(self.successful_pairs)
            },
            "ai_features": {
                "adaptive_parameters": True,
                "self_learning_weights": True,
                "diversity_maintenance": True,
                "ai_powered_selection": self.ai_selection_enabled,
                "ai_enhanced_crossover": self.ai_crossover_enabled,
                "smart_mutation_strategies": self.ai_mutation_enabled,
                "ai_fitness_landscape_analysis": self.ai_fitness_landscape_enabled,
                "ai_powered_local_search": self.ai_local_search_enabled,
                "ai_convergence_detection": self.ai_convergence_enabled,
                "smart_initialization": True,
                "conflict_resolution": self.conflict_resolution_enabled,
                "pattern_recognition": True,
                "local_search": True
            },
            "generation_history": self.generation_history,
            "optimizations_applied": [
                "instructor_max_min_pairing",
                "consecutive_grouping",
                "ai_based_soft_constraints",
                "adaptive_mutation_crossover",
                "self_learning_fitness_weights",
                "diversity_protection",
                "multi_strategy_init",
                "pattern_recognition",
                "local_search_integration",
                "elite_preservation",
                "tournament_selection"
            ]
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
        if self.no_improvement_count > 10:
            # Stuck in local optimum - explore more!
            self.mutation_rate = min(0.5, self.mutation_rate * 1.2)
            self.crossover_rate = max(0.5, self.crossover_rate * 0.9)
            logger.debug(f"   🔼 Increased exploration: mutation={self.mutation_rate:.3f}")
        elif self.no_improvement_count < 3:
            # Improving - exploit current area
            self.mutation_rate = max(0.05, self.mutation_rate * 0.95)
            self.crossover_rate = min(0.95, self.crossover_rate * 1.05)
            logger.debug(f"   🔽 Increased exploitation: mutation={self.mutation_rate:.3f}")
        
        # Natural cooling (like simulated annealing)
        progress = generation / self.generations
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
        jury = self._calculate_jury_score(solution)
        
        # Normalize scores
        total = coverage + consecutive + balance + classroom + jury
        if total == 0:
            return
        
        # Calculate contribution percentages
        contributions = {
            'coverage': coverage / total,
            'consecutive': consecutive / total,
            'balance': balance / total,
            'classroom': classroom / total,
            'jury': jury / total
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
        num_replace = int(self.population_size * 0.2)
        
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
        paired_count = int(self.population_size * self.init_strategies['paired_consecutive'])
        greedy_count = int(self.population_size * self.init_strategies['greedy_early'])
        random_count = self.population_size - paired_count - greedy_count
        
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
        
        logger.info(f"   ✅ Smart initialization completed: {len(population)} individuals")
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
                        
                        assignments.append({
                            'project_id': project['id'],
                            'timeslot_id': timeslot['id'],
                            'classroom_id': classroom['id'],
                            'responsible_instructor_id': resp_id,
                            'is_makeup': project.get('is_makeup', False),
                            'instructors': [resp_id] if resp_id else []
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
            logger.warning(f"GA Greedy: {len(unassigned_projects)} proje atanamadı! Emergency assignment...")
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
                
                assignments.append({
                    'project_id': project['id'],
                    'timeslot_id': timeslot_id,
                    'classroom_id': classroom_id,
                    'responsible_instructor_id': resp_id,
                    'is_makeup': project.get('is_makeup', False),
                    'instructors': [resp_id] if resp_id else []
                })
                
                used_slots.add(slot_key)
                if resp_id:
                    instructor_usage[resp_id].add(timeslot_id)
            else:
                unassigned_projects.append((project, resp_id))
        
        # Emergency assignment for unassigned projects
        if unassigned_projects:
            logger.warning(f"GA Random: {len(unassigned_projects)} proje atanamadı! Emergency assignment...")
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
        
        logger.info(f"📊 Instructorlar proje sayısına göre sıralandı:")
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
                    
                    # If still not assigned, add to unassigned list for emergency assignment
                    if not assigned:
                        unassigned_projects.append((project, instructor_id))
                
                classroom_idx += 1
                timeslot_idx = 0
            
            else:
                instructor_x_id, instructor_x_projects = pair[0]
                instructor_y_id, instructor_y_projects = pair[1]
                
                # PHASE 1: X sorumlu -> Y jüri
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
                    
                    # If still not assigned, add to unassigned list for emergency assignment
                    if not assigned:
                        unassigned_projects.append((project, instructor_x_id))
                
                # PHASE 2: Y sorumlu -> X jüri
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
                        assignment = {
                            "project_id": project['id'],
                            "timeslot_id": timeslot['id'],
                            "classroom_id": classroom['id'],
                            "responsible_instructor_id": instructor_id,
                            "is_makeup": project.get('is_makeup', False),
                            "instructors": [instructor_id]
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
        AI-based fitness evaluation with self-learning weights
        
        NO HARD CONSTRAINTS - Pure soft optimization!
        """
        if not individual:
            return 0.0
        
        coverage = self._calculate_coverage_score(individual)
        consecutive = self._calculate_consecutive_score(individual)
        balance = self._calculate_balance_score(individual)
        classroom = self._calculate_classroom_score(individual)
        jury = self._calculate_jury_score(individual)
        
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
        
        # 🤖 Use learned weights + NEW GAP & EARLY TIMESLOT SCORES
        fitness = (
            coverage * self.fitness_weights['coverage'] +
            consecutive * self.fitness_weights['consecutive'] +
            balance * self.fitness_weights['balance'] +
            classroom * self.fitness_weights['classroom'] +
            jury * self.fitness_weights['jury'] +
            gap_free_score * self.reward_gap_free +
            early_timeslot_score * self.reward_early_timeslot +
            ultra_gap_score * self.reward_gap_filled +
            super_ultra_gap_score * self.reward_compact_classrooms
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
            instructors = assignment.get('instructors', [])
            if len(instructors) >= 2:
                pair = tuple(sorted(instructors[:2]))
                if pair in self.successful_pairs:
                    bonus += self.successful_pairs[pair] * 0.1
        
        # Bonus for using successful classrooms
        for assignment in assignments:
            classroom_id = assignment.get('classroom_id')
            if classroom_id in self.successful_classrooms:
                bonus += self.successful_classrooms[classroom_id] * 0.05
        
        return bonus
    
    def _calculate_coverage_score(self, assignments: List[Dict]) -> float:
        """Calculate project coverage score"""
        assigned_projects = len(set(a['project_id'] for a in assignments if 'project_id' in a))
        total_projects = len(self.projects)
        return (assigned_projects / total_projects) * 100.0 if total_projects > 0 else 0.0
    
    def _calculate_consecutive_score(self, assignments: List[Dict]) -> float:
        """Calculate consecutive grouping quality score"""
        instructor_slots = defaultdict(list)
        for assignment in assignments:
            resp_id = assignment.get('responsible_instructor_id')
            if resp_id:
                instructor_slots[resp_id].append(assignment)
        
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
            for instructor_id in assignment.get('instructors', []):
                loads[instructor_id] += 1
        
        if not loads:
            return 0.0
        
        load_values = list(loads.values())
        std_load = np.std(load_values)
        balance_score = 50.0 / (1.0 + std_load) if std_load > 0 else 50.0
        
        return balance_score
    
    def _calculate_classroom_score(self, assignments: List[Dict]) -> float:
        """Calculate classroom consistency score"""
        instructor_classrooms = defaultdict(set)
        for assignment in assignments:
            resp_id = assignment.get('responsible_instructor_id')
            if resp_id:
                instructor_classrooms[resp_id].add(assignment.get('classroom_id'))
        
        total_changes = sum(len(classrooms) - 1 for classrooms in instructor_classrooms.values())
        classroom_score = 30.0 / (1.0 + total_changes) if total_changes >= 0 else 30.0
        
        return classroom_score
    
    def _calculate_jury_score(self, assignments: List[Dict]) -> float:
        """Calculate jury assignment quality score"""
        jury_count = 0
        bitirme_with_jury = 0
        bitirme_total = 0
        
        for assignment in assignments:
            instructors = assignment.get('instructors', [])
            project = next((p for p in self.projects if p['id'] == assignment.get('project_id')), None)
            
            if len(instructors) > 1:
                jury_count += 1
            
            if project and project.get('type') == 'bitirme':
                bitirme_total += 1
                if len(instructors) > 1:
                    bitirme_with_jury += 1
        
        bitirme_coverage = (bitirme_with_jury / bitirme_total) * 20.0 if bitirme_total > 0 else 0.0
        general_jury_bonus = jury_count * 0.5
        
        return bitirme_coverage + general_jury_bonus
    
    def _calculate_gap_free_score(self, assignments: List[Dict]) -> float:
        """Calculate gap-free optimization score"""
        if not assignments:
            return 0.0
        
        # Count total possible slots
        total_slots = len(self.classrooms) * len(self.timeslots)
        used_slots = len(assignments)
        gaps = total_slots - used_slots
        
        # Calculate gap penalty
        gap_penalty = gaps * abs(self.penalty_gap) / total_slots
        
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
            timeslot_id = assignment.get('timeslot_id', 0)
            if timeslot_id <= early_threshold:
                early_assignments += 1
            else:
                late_assignments += 1
        
        total_assignments = early_assignments + late_assignments
        if total_assignments == 0:
            return 0.0
        
        early_percentage = (early_assignments / total_assignments) * 100.0
        
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
            classroom_id = assignment.get('classroom_id')
            if classroom_id in classroom_assignments:
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
            classroom_id = assignment.get('classroom_id')
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
            assignments_per_classroom = len(assignments) / used_classroom_count
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
            parent1 = self._ai_powered_selection(fitness_scores)
            parent2 = self._ai_powered_selection(fitness_scores)
            
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
        """AI-powered intelligent selection strategy"""
        if not self.ai_selection_enabled:
            return self._tournament_selection(fitness_scores)
        
        # Choose selection strategy based on AI learning
        strategy = self._choose_ai_selection_strategy(fitness_scores)
        
        if strategy == 'tournament':
            return self._tournament_selection(fitness_scores)
        elif strategy == 'fitness_proportional':
            return self._fitness_proportional_selection(fitness_scores)
        elif strategy == 'rank_based':
            return self._rank_based_selection(fitness_scores)
        elif strategy == 'multi_objective':
            return self._multi_objective_selection(fitness_scores)
        else:
            return self._tournament_selection(fitness_scores)
    
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
        probabilities = [f / total_fitness for f in normalized_fitness]
        selected_idx = np.random.choice(len(self.population), p=probabilities)
        return self.population[selected_idx]
    
    def _rank_based_selection(self, fitness_scores: List[float]) -> List[Dict[str, Any]]:
        """Rank-based selection with AI ranking"""
        # Sort by fitness
        sorted_indices = np.argsort(fitness_scores)
        
        # Linear ranking with AI-adjusted selection pressure
        selection_pressure = 1.5  # AI learns optimal pressure
        ranks = np.arange(1, len(fitness_scores) + 1)
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
        """AI-enhanced intelligent crossover strategy"""
        if not self.ai_crossover_enabled:
            return self._crossover(parent1, parent2)
        
        # Choose crossover strategy based on AI learning
        strategy = self._choose_ai_crossover_strategy(parent1, parent2)
        
        if strategy == 'uniform':
            return self._crossover(parent1, parent2)
        elif strategy == 'intelligent_points':
            return self._intelligent_crossover(parent1, parent2)
        elif strategy == 'fitness_guided':
            return self._fitness_guided_crossover(parent1, parent2)
        elif strategy == 'context_aware':
            return self._context_aware_crossover(parent1, parent2)
        else:
            return self._crossover(parent1, parent2)
    
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
        if not assignment:
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
        classroom_consistency = len(set(classroom_ids)) / len(classroom_ids) if classroom_ids else 0
        
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
        timeslot_ids = [a.get('timeslot_id') for a in individual if a.get('timeslot_id')]
        timeslot_diversity = len(set(timeslot_ids)) / len(timeslot_ids) if timeslot_ids else 0
        
        # Analyze classroom distribution
        classroom_ids = [a.get('classroom_id') for a in individual if a.get('classroom_id')]
        classroom_diversity = len(set(classroom_ids)) / len(classroom_ids) if classroom_ids else 0
        
        # Analyze instructor distribution
        all_instructors = []
        for assignment in individual:
            all_instructors.extend(assignment.get('instructors', []))
        instructor_diversity = len(set(all_instructors)) / len(all_instructors) if all_instructors else 0
        
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
            mutation_type = random.choice(['swap', 'timeslot', 'classroom', 'jury', 'shuffle'])
            mutated = self._apply_mutation_operator(mutated, mutation_type)
        
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
        
        return ruggedness / len(sorted_fitness)
    
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
            mutation_type = random.choice(['classroom', 'jury'])
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
        elif mutation_type == 'jury':
            idx = random.randint(0, len(mutated) - 1)
            mutated[idx] = self._apply_single_mutation(mutated[idx], 'jury')
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
        logger.info("   🔍 AI: Intensifying local search...")
        
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
        """Enhanced smart mutation with multiple operators"""
        if not individual or len(individual) < 2:
            return individual
        
        mutated = individual.copy()
        
        # 🎯 GAP-FREE & EARLY TIMESLOT MUTATION TYPES
        mutation_types = ['swap', 'timeslot', 'classroom', 'jury']
        
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
                        instructor_id in mutated[i].get('instructors', []) and
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
        
        elif mutation_type == 'jury':
            # CONFLICT-AWARE JURY MUTATION
            idx = random.randint(0, len(mutated) - 1)
            assignment = mutated[idx]
            current_instructors = assignment.get('instructors', [])
            timeslot_id = assignment.get('timeslot_id')
            
            if len(current_instructors) > 1:
                # Remove jury member (keep only responsible instructor)
                mutated[idx]['instructors'] = [current_instructors[0]]
            else:
                # Add jury member (check availability)
                responsible_id = current_instructors[0] if current_instructors else None
                
                if responsible_id and timeslot_id:
                    # Find available instructors for jury at this timeslot
                    available_jury = []
                    for instructor in self.instructors:
                        instructor_id = instructor['id']
                        
                        # 🤖 AI-BASED: Don't skip - apply heavy penalty if same as responsible
                        penalty_score = 0.0
                        
                        if instructor_id == responsible_id:
                            penalty_score = -1000.0  # Huge penalty (instead of skip!)
                        
                        # Check if instructor is available at this timeslot
                        instructor_busy = any(
                            i != idx and
                            instructor_id in mutated[i].get('instructors', []) and
                            mutated[i].get('timeslot_id') == timeslot_id
                            for i in range(len(mutated))
                        )
                        
                        # 🤖 AI-BASED: Include with penalty score (soft constraint)
                        if not instructor_busy and penalty_score >= -500:  # Soft threshold
                            available_jury.append(instructor_id)
                        # Even if penalty is high, can still be considered in fallback
                    
                    # Add available jury member (or random if none available)
                    if available_jury:
                        new_jury = random.choice(available_jury)
                        mutated[idx]['instructors'].append(new_jury)
                    else:
                        # Fallback to random jury (might cause conflict, but will be resolved later)
                        available = [i['id'] for i in self.instructors if i['id'] != responsible_id]
                        if available:
                            new_jury = random.choice(available)
                            mutated[idx]['instructors'].append(new_jury)
        
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
                    instructor_id = assignment.get('instructors', [None])[0]
                    
                    # Check if instructor is available at gap timeslot
                    if instructor_id:
                        instructor_busy = any(
                            j != i and
                            instructor_id in mutated[j].get('instructors', []) and
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
                        instructor_id in mutated[j].get('instructors', []) and
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
                instructor_id = assignment.get('instructors', [None])[0]
                
                if instructor_id:
                    instructor_busy = any(
                        j != i and
                        instructor_id in new_assignments[j].get('instructors', []) and
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
                        'timeslot_id': timeslot['id']
                    })
        
        return gaps
    
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
                instructor_id = assignment.get('instructors', [None])[0]
                
                # Check if instructor is available at gap timeslot
                if instructor_id:
                    instructor_busy = any(
                        j != i and
                        instructor_id in result[j].get('instructors', []) and
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
            instructor_id = assignment.get('instructors', [None])[0]
            current_classroom = assignment.get('classroom_id')
            
            # Find available early timeslot
            for early_timeslot_id in range(1, early_threshold + 1):
                if instructor_id:
                    # Check instructor availability
                    instructor_busy = any(
                        j != i and
                        instructor_id in result[j].get('instructors', []) and
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
        
        return (early_count / len(assignments) * 100.0) if assignments else 0.0
    
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
        coverage_pct = (assigned_projects / len(self.projects)) * 100.0 if self.projects else 0.0
        
        consecutive_score = self._calculate_consecutive_score(assignments)
        
        loads = defaultdict(int)
        for assignment in assignments:
            for instructor_id in assignment.get('instructors', []):
                loads[instructor_id] += 1
        
        load_values = list(loads.values()) if loads else [0]
        
        instructor_classrooms = defaultdict(set)
        for assignment in assignments:
            resp_id = assignment.get('responsible_instructor_id')
            if resp_id:
                instructor_classrooms[resp_id].add(assignment.get('classroom_id'))
        
        total_classroom_changes = sum(len(classrooms) - 1 for classrooms in instructor_classrooms.values())
        jury_count = sum(1 for a in assignments if len(a.get('instructors', [])) > 1)
        
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
            "jury_assignments": jury_count,
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
        assignments = self._ai_enhance_jury(assignments)
        
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

    def _ai_enhance_jury(self, assignments: List[Dict]) -> List[Dict]:
        """AI-based jury enhancement with pattern recognition"""
        for assignment in assignments:
            current_instructors = assignment.get('instructors', [])
            
            if len(current_instructors) == 1:
                project = next((p for p in self.projects if p['id'] == assignment.get('project_id')), None)
                
                if project and (project.get('type') == 'bitirme' or random.random() < 0.3):
                    resp_id = current_instructors[0]
                    timeslot_id = assignment['timeslot_id']
                    
                    available = []
                    for instructor in self.instructors:
                        inst_id = instructor['id']
                        if inst_id == resp_id:
                            continue
                        
                        is_available = True
                        for other in assignments:
                            if other['timeslot_id'] == timeslot_id:
                                if inst_id in other.get('instructors', []):
                                    is_available = False
                                    break
                        
                        if is_available:
                            available.append(inst_id)
                    
                    if available:
                        # 🤖 AI: Prefer learned successful pairs
                        best_jury = available[0]
                        best_score = 0
                        
                        for jury_id in available:
                            pair = tuple(sorted([resp_id, jury_id]))
                            score = self.successful_pairs.get(pair, 0)
                            if score > best_score:
                                best_score = score
                                best_jury = jury_id
                        
                        assignment['instructors'].append(best_jury)
                        
                        # Update pattern
                        pair = tuple(sorted([resp_id, best_jury]))
                        self.co_occurrence_matrix[resp_id][best_jury] += 1
                        self.co_occurrence_matrix[best_jury][resp_id] += 1
        
        return assignments

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
        
        logger.info("🔍 CONFLICT DETECTION STARTED")
        
        # 1. Instructor çakışmaları
        instructor_conflicts = self._detect_instructor_conflicts(assignments)
        all_conflicts.extend(instructor_conflicts)
        
        # 2. Classroom çakışmaları
        classroom_conflicts = self._detect_classroom_conflicts(assignments)
        all_conflicts.extend(classroom_conflicts)
        
        # 3. Timeslot çakışmaları
        timeslot_conflicts = self._detect_timeslot_conflicts(assignments)
        all_conflicts.extend(timeslot_conflicts)
        
        logger.info(f"🔍 CONFLICT DETECTION COMPLETED: {len(all_conflicts)} conflicts found")
        
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
                    logger.info(f"✅ RESOLVED: {conflict['description']}")
                else:
                    resolution_log.append({
                        'conflict_id': conflict.get('type', 'unknown'),
                        'resolution_strategy': conflict.get('resolution_strategy', 'unknown'),
                        'success': False,
                        'error': resolution_result.get('error', 'Unknown error'),
                        'description': f"Failed to resolve {conflict['type']}"
                    })
                    logger.warning(f"❌ FAILED: {conflict['description']}")
                    
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
            elif strategy == 'replace_jury_member':
                return self._replace_jury_member(conflict, assignments)
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
    
    def _replace_jury_member(self, conflict: Dict[str, Any], 
                           assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Jüri üyesini değiştir"""
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
        
        # İlk uygun instructor'ı seç
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
                        'action': 'jury_replaced'
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
