"""
Algorithm service module for managing algorithm operations.
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
import time
from datetime import datetime

from app.models.algorithm import AlgorithmType, AlgorithmRun
from app.schemas.algorithm import AlgorithmRunCreate, AlgorithmRunUpdate
from app.crud.algorithm import crud_algorithm
from app.algorithms.factory import AlgorithmFactory
from app.db.base import get_db
from app.i18n import translate

logger = logging.getLogger(__name__)
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
                "description": _("A search heuristic inspired by natural selection."),
                "best_for": _("Complex problems with many variables."),
                "parameters": {
                    "population_size": {"type": "int", "default": 100, "description": _("Size of the population.")},
                    "n_generations": {"type": "int", "default": 50, "description": _("Number of generations.")},
                    "crossover_rate": {"type": "float", "default": 0.8, "description": _("Crossover rate.")},
                    "mutation_rate": {"type": "float", "default": 0.2, "description": _("Mutation rate.")}
                }
            },
            AlgorithmType.SIMULATED_ANNEALING: {
                "name": _("Simulated Annealing"),
                "description": _("A probabilistic technique for approximating the global optimum."),
                "best_for": _("Problems where finding an approximate global optimum is more important than finding a precise local optimum."),
                "parameters": {
                    "initial_temp": {"type": "float", "default": 100.0, "description": _("Initial temperature.")},
                    "cooling_rate": {"type": "float", "default": 0.95, "description": _("Cooling rate.")},
                    "n_iterations": {"type": "int", "default": 1000, "description": _("Number of iterations.")}
                }
            },
            AlgorithmType.SIMPLEX: {
                "name": _("Simplex"),
                "description": _("A method for solving linear programming problems."),
                "best_for": _("Problems with linear constraints and objective function."),
                "parameters": {
                    "max_iterations": {"type": "int", "default": 1000, "description": _("Maximum number of iterations.")},
                    "tolerance": {"type": "float", "default": 1e-6, "description": _("Convergence tolerance.")}
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
                "name": _("NSGA-II"),
                "description": _("A multi-objective genetic algorithm."),
                "best_for": _("Problems with multiple competing objectives."),
                "parameters": {
                    "population_size": {"type": "int", "default": 100, "description": _("Size of the population.")},
                    "n_generations": {"type": "int", "default": 50, "description": _("Number of generations.")},
                    "crossover_rate": {"type": "float", "default": 0.8, "description": _("Crossover rate.")},
                    "mutation_rate": {"type": "float", "default": 0.2, "description": _("Mutation rate.")}
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
                "description": _("A metaheuristic search method employing local search methods with memory structures."),
                "best_for": _("Combinatorial optimization problems."),
                "parameters": {
                    "max_iterations": {"type": "int", "default": 200, "description": _("Maximum number of iterations.")},
                    "tabu_list_size": {"type": "int", "default": 20, "description": _("Size of the tabu list.")},
                    "neighborhood_size": {"type": "int", "default": 30, "description": _("Size of the neighborhood.")}
                }
            },
            AlgorithmType.PSO: {
                "name": _("Particle Swarm Optimization"),
                "description": _("A computational method that optimizes a problem by iteratively trying to improve a candidate solution."),
                "best_for": _("Continuous optimization problems."),
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
                "description": _("A music-inspired metaheuristic optimization algorithm."),
                "best_for": _("Combinatorial optimization problems."),
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
                "description": _("Constraint Programming with SAT solver."),
                "best_for": _("Problems with complex constraints."),
                "parameters": {
                    "time_limit": {"type": "int", "default": 60, "description": _("Time limit in seconds.")}
                }
            },
            AlgorithmType.DEEP_SEARCH: {
                "name": _("Deep Search"),
                "description": _("A deep search algorithm that combines beam search and iterative deepening."),
                "best_for": _("Problems requiring thorough exploration of the solution space."),
                "parameters": {
                    "max_depth": {"type": "int", "default": 5, "description": _("Maximum search depth.")},
                    "beam_width": {"type": "int", "default": 10, "description": _("Beam search width.")},
                    "time_limit": {"type": "int", "default": 60, "description": _("Time limit in seconds.")}
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
    async def run_algorithm(algorithm_type: AlgorithmType, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], AlgorithmRun]:
        """
        Run the specified algorithm with the given data and parameters.

        Args:
            algorithm_type: The algorithm type to run.
            data: Input data for the algorithm.
            params: Algorithm parameters.

        Returns:
            Tuple[Dict[str, Any], AlgorithmRun]: Algorithm result and run record.
        """
        start_time = time.time()

        # Create algorithm run record
        algorithm_run_data = AlgorithmRunCreate(
            algorithm_type=algorithm_type,
            parameters=params or {},
            status="running",
            started_at=datetime.now()
        )

        async with get_db() as db:
            algorithm_run = await crud_algorithm.create(db, obj_in=algorithm_run_data)

            try:
                # Create algorithm instance
                algorithm = AlgorithmFactory.create(algorithm_type, params)

                # Initialize algorithm
                algorithm.initialize(data)

                # Run optimization
                result = algorithm.optimize(data)

                # Calculate execution time
                execution_time = time.time() - start_time

                # Update algorithm run record
                algorithm_run_update = AlgorithmRunUpdate(
                    status="completed",
                    result=result,
                    execution_time=execution_time,
                    completed_at=datetime.now()
                )
                algorithm_run = await crud_algorithm.update(db, db_obj=algorithm_run, obj_in=algorithm_run_update)

                return result, algorithm_run

            except Exception as e:
                logger.exception(f"Error running algorithm {algorithm_type}: {str(e)}")

                # Update algorithm run record with error
                algorithm_run_update = AlgorithmRunUpdate(
                    status="failed",
                    error=str(e),
                    completed_at=datetime.now()
                )
                algorithm_run = await crud_algorithm.update(db, db_obj=algorithm_run, obj_in=algorithm_run_update)

                # Re-raise the exception
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
        async with get_db() as db:
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