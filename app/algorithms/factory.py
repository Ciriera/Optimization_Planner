"""
Algorithm factory module for creating optimization algorithms.
"""
from typing import Dict, Any, Optional, List

from app.models.algorithm import AlgorithmType
from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.genetic_algorithm import GeneticAlgorithm
from app.algorithms.simulated_annealing import SimulatedAnnealing
from app.algorithms.ant_colony import AntColony
from app.algorithms.nsga_ii import NSGAII
from app.algorithms.greedy import Greedy
from app.algorithms.tabu_search import TabuSearch
from app.algorithms.pso import PSO
from app.algorithms.harmony_search import HarmonySearch
from app.algorithms.firefly import Firefly
from app.algorithms.grey_wolf import GreyWolf
from app.algorithms.cp_sat import CPSAT
from app.algorithms.deep_search import DeepSearch


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
            return GeneticAlgorithm(params)
        elif algorithm_type == AlgorithmType.SIMULATED_ANNEALING:
            return SimulatedAnnealing(params)
        elif algorithm_type == AlgorithmType.SIMPLEX:
            raise NotImplementedError("Simplex algorithm is temporarily disabled")
        elif algorithm_type == AlgorithmType.ANT_COLONY:
            return AntColony(params)
        elif algorithm_type == AlgorithmType.NSGA_II:
            return NSGAII(params)
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
        else:
            raise ValueError(f"Unsupported algorithm type: {algorithm_type}")


def get_algorithm_types() -> List[str]:
    """
    Get a list of available algorithm types.
    
    Returns:
        List[str]: List of available algorithm types.
    """
    return [algo_type.value for algo_type in AlgorithmType] 