"""
Algorithm factory module for creating optimization algorithms.
"""
from typing import Dict, Any, Optional, List

from app.models.algorithm import AlgorithmType
from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.genetic_algorithm import EnhancedGeneticAlgorithm
from app.algorithms.simulated_annealing import SimulatedAnnealingAlgorithm
from app.algorithms.ant_colony import AntColonyOptimization
from app.algorithms.nsga_ii import NSGA2Scheduler as NSGAII
from app.algorithms.nsga_ii_enhanced import NSGAIIEnhanced
from app.algorithms.greedy import Greedy
from app.algorithms.tabu_search import TabuSearch
from app.algorithms.pso import PSO
from app.algorithms.harmony_search import HarmonySearch
from app.algorithms.firefly import Firefly
from app.algorithms.grey_wolf import GreyWolf
from app.algorithms.cp_sat import CPSAT
from app.algorithms.deep_search import DeepSearch
from app.algorithms.lexicographic import LexicographicAlgorithm
from app.algorithms.hybrid_cp_sat_nsga import HybridCPSATNSGAAlgorithm
from app.algorithms.simplex_new import SimplexAlgorithm
from app.algorithms.real_simplex import RealSimplexAlgorithm
# Yeni algoritmalar
from app.algorithms.artificial_bee_colony import ArtificialBeeColony
from app.algorithms.cuckoo_search import CuckooSearch
from app.algorithms.branch_and_bound import BranchAndBound
from app.algorithms.dynamic_programming import DynamicProgrammingAlgorithm
from app.algorithms.whale_optimization import WhaleOptimization
# Daha fazla algoritma
from app.algorithms.bat_algorithm import BatAlgorithm
from app.algorithms.dragonfly_algorithm import DragonflyAlgorithm
from app.algorithms.a_star_search import AStarSearch
from app.algorithms.integer_linear_programming import IntegerLinearProgramming
from app.algorithms.genetic_local_search import GeneticLocalSearch
from app.algorithms.comprehensive_optimizer import ComprehensiveOptimizer
from app.algorithms.hungarian_algorithm import HungarianAlgorithm
from app.algorithms.bitirme_priority_scheduler import BitirmePriorityScheduler


class AlgorithmFactory:
    """
    Factory class for creating optimization algorithms.
    """

    @staticmethod
    def create(algorithm_type: AlgorithmType, params: Optional[Dict[str, Any]] = None) -> OptimizationAlgorithm:
        """
        Create an optimization algorithm instance based on the algorithm type.

        Args:
            algorithm_type: Type of the algorithm to create.
            params: Algorithm parameters.

        Returns:
            OptimizationAlgorithm: An instance of the optimization algorithm.

        Raises:
            ValueError: If the algorithm type is not supported.
        """
        params = params or {}

        if algorithm_type == AlgorithmType.GENETIC_ALGORITHM:
            return EnhancedGeneticAlgorithm(params)
        elif algorithm_type == AlgorithmType.SIMULATED_ANNEALING:
            return SimulatedAnnealingAlgorithm(params)
        elif algorithm_type == AlgorithmType.SIMPLEX:
            return RealSimplexAlgorithm(params)
        elif algorithm_type == AlgorithmType.ANT_COLONY:
            return AntColonyOptimization(params)
        elif algorithm_type == AlgorithmType.NSGA_II:
            return NSGAII(params)
        elif algorithm_type == AlgorithmType.NSGA_II_ENHANCED:
            return NSGAIIEnhanced(params)
        elif algorithm_type == AlgorithmType.GREEDY:
            return Greedy(params)
        elif algorithm_type == AlgorithmType.TABU_SEARCH:
            return TabuSearch(params)
        elif algorithm_type == AlgorithmType.PSO:
            return PSO(params)
        elif algorithm_type == AlgorithmType.HARMONY_SEARCH:
            return HarmonySearch(params)
        elif algorithm_type == AlgorithmType.FIREFLY:
            return Firefly(params)
        elif algorithm_type == AlgorithmType.GREY_WOLF:
            return GreyWolf(params)
        elif algorithm_type == AlgorithmType.CP_SAT:
            return CPSAT(params)
        elif algorithm_type == AlgorithmType.DEEP_SEARCH:
            return DeepSearch(params)
        elif algorithm_type == AlgorithmType.LEXICOGRAPHIC:
            return LexicographicAlgorithm(params)
        elif algorithm_type == AlgorithmType.HYBRID_CP_SAT_NSGA:
            return HybridCPSATNSGAAlgorithm(params)
        elif algorithm_type == AlgorithmType.ARTIFICIAL_BEE_COLONY:
            return ArtificialBeeColony(params)
        elif algorithm_type == AlgorithmType.CUCKOO_SEARCH:
            return CuckooSearch(params)
        elif algorithm_type == AlgorithmType.BRANCH_AND_BOUND:
            return BranchAndBound(params)
        elif algorithm_type == AlgorithmType.DYNAMIC_PROGRAMMING:
            return DynamicProgrammingAlgorithm(params)
        elif algorithm_type == AlgorithmType.WHALE_OPTIMIZATION:
            return WhaleOptimization(params)
        elif algorithm_type == AlgorithmType.BAT_ALGORITHM:
            return BatAlgorithm(params)
        elif algorithm_type == AlgorithmType.DRAGONFLY_ALGORITHM:
            return DragonflyAlgorithm(params)
        elif algorithm_type == AlgorithmType.A_STAR_SEARCH:
            return AStarSearch(params)
        elif algorithm_type == AlgorithmType.INTEGER_LINEAR_PROGRAMMING:
            return IntegerLinearProgramming(params)
        elif algorithm_type == AlgorithmType.HUNGARIAN:
            return HungarianAlgorithm(params)
        elif algorithm_type == AlgorithmType.GENETIC_LOCAL_SEARCH:
            return GeneticLocalSearch(params)
        elif algorithm_type == AlgorithmType.COMPREHENSIVE_OPTIMIZER:
            return ComprehensiveOptimizer(params)
        elif algorithm_type == AlgorithmType.BITIRME_PRIORITY_SCHEDULER:
            return BitirmePriorityScheduler(params)
        else:
            raise ValueError(f"Unsupported algorithm type: {algorithm_type}")
            
    def list_algorithms(self) -> List[str]:
        """
        Get a list of available algorithm types.
        
        Returns:
            List[str]: List of available algorithm types.
        """
        return [algo_type.value for algo_type in AlgorithmType]
        
    def create_algorithm(self, algorithm_name: str, params: Optional[Dict[str, Any]] = None) -> OptimizationAlgorithm:
        """
        Create an algorithm instance based on the algorithm name.
        
        Args:
            algorithm_name: Name of the algorithm to create.
            params: Algorithm parameters.
            
        Returns:
            OptimizationAlgorithm: An instance of the algorithm.
            
        Raises:
            ValueError: If the algorithm name is not supported.
        """
        params = params or {}
        
        try:
            algorithm_type = AlgorithmType(algorithm_name)
            return self.create(algorithm_type, params)
        except ValueError:
            raise ValueError(f"Unsupported algorithm name: {algorithm_name}")


def get_algorithm_types() -> List[str]:
    """
    Get a list of available algorithm types.
    
    Returns:
        List[str]: List of available algorithm types.
    """
    return [algo_type.value for algo_type in AlgorithmType] 