from typing import Dict, Any, List, Optional
from app.algorithms.base import BaseAlgorithm
from app.algorithms.genetic import GeneticAlgorithm
from app.algorithms.ant_colony import AntColonyAlgorithm
from app.algorithms.simulated_annealing import SimulatedAnnealingAlgorithm
from app.algorithms.nsga_ii import NSGAII
from app.algorithms.greedy import GreedyAlgorithm
from app.algorithms.tabu_search import TabuSearchAlgorithm
from app.algorithms.pso import ParticleSwarmOptimization
from app.algorithms.harmony_search import HarmonySearch
from app.algorithms.firefly import FireflyAlgorithm
from app.algorithms.grey_wolf import GreyWolfOptimizer
from app.algorithms.cp_sat import CPSATSolver
from app.algorithms.deep_search import DeepSearch

class AlgorithmFactory:
    """Algoritma seçimi ve yönetimi için factory sınıfı"""
    
    ALGORITHMS = {
        "genetic": {
            "name": "Genetic Algorithm",
            "description": "Genetik algoritma ile çözüm arar",
            "default_params": {
                "population_size": 100,
                "generations": 50,
                "mutation_rate": 0.1,
                "crossover_rate": 0.8
            }
        },
        "simulated_annealing": {
            "name": "Simulated Annealing",
            "description": "Tavlama benzetimi ile çözüm arar",
            "default_params": {
                "initial_temperature": 100.0,
                "cooling_rate": 0.01,
                "iterations": 1000,
                "acceptance_probability": 0.7
            }
        },
        "ant_colony": {
            "name": "Ant Colony Optimization",
            "description": "Karınca kolonisi optimizasyonu ile çözüm arar",
            "default_params": {
                "colony_size": 50,
                "iterations": 100,
                "evaporation_rate": 0.1,
                "pheromone_factor": 1.0,
                "heuristic_factor": 2.0
            }
        },
        "nsga_ii": {
            "name": "NSGA-II",
            "description": "Multi-objective genetic algorithm for Pareto-optimal solutions",
            "default_params": {
                "population_size": 100,
                "generations": 50,
                "crossover_rate": 0.8,
                "mutation_rate": 0.2
            }
        },
        "greedy": {
            "name": "Greedy Algorithm with Local Search",
            "description": "Greedy algorithm followed by local search optimization",
            "default_params": {
                "local_search_iterations": 100,
                "neighborhood_size": 10,
                "rule_weight": 100,
                "load_weight": 10,
                "classroom_weight": 5
            }
        },
        "tabu_search": {
            "name": "Tabu Search",
            "description": "Tabu search metaheuristic with memory structures",
            "default_params": {
                "iterations": 100,
                "tabu_tenure": 10,
                "neighborhood_size": 20,
                "aspiration_factor": 1.1,
                "rule_weight": 100,
                "load_weight": 10,
                "classroom_weight": 5
            }
        },
        "pso": {
            "name": "Particle Swarm Optimization",
            "description": "Swarm intelligence algorithm inspired by social behavior",
            "default_params": {
                "swarm_size": 30,
                "iterations": 100,
                "inertia_weight": 0.7,
                "cognitive_coefficient": 1.5,
                "social_coefficient": 1.5,
                "rule_weight": 100,
                "load_weight": 10,
                "classroom_weight": 5
            }
        },
        "harmony_search": {
            "name": "Harmony Search",
            "description": "Music-inspired metaheuristic search algorithm",
            "default_params": {
                "harmony_memory_size": 30,
                "iterations": 100,
                "harmony_memory_considering_rate": 0.9,
                "pitch_adjusting_rate": 0.3,
                "bandwidth": 0.1,
                "rule_weight": 100,
                "load_weight": 10,
                "classroom_weight": 5
            }
        },
        "firefly": {
            "name": "Firefly Algorithm",
            "description": "Nature-inspired algorithm based on flashing behavior of fireflies",
            "default_params": {
                "population_size": 30,
                "iterations": 100,
                "alpha": 0.5,
                "beta0": 1.0,
                "gamma": 0.1,
                "rule_weight": 100,
                "load_weight": 10,
                "classroom_weight": 5
            }
        },
        "grey_wolf": {
            "name": "Grey Wolf Optimizer",
            "description": "Metaheuristic inspired by grey wolf hunting behavior",
            "default_params": {
                "population_size": 30,
                "iterations": 100,
                "rule_weight": 100,
                "load_weight": 10,
                "classroom_weight": 5
            }
        },
        "cp_sat": {
            "name": "CP-SAT Solver",
            "description": "Constraint programming with SAT solver",
            "default_params": {
                "time_limit_seconds": 60,
                "num_search_workers": 4,
                "rule_weight": 100,
                "load_weight": 10,
                "classroom_weight": 5
            }
        },
        "deep_search": {
            "name": "Deep Search",
            "description": "Deep search with beam search and iterative deepening",
            "default_params": {
                "beam_width": 10,
                "max_depth": None,
                "time_limit_seconds": 60,
                "rule_weight": 100,
                "load_weight": 10,
                "classroom_weight": 5
            }
        }
    }

    @classmethod
    def get_available_algorithms(cls) -> List[Dict[str, Any]]:
        """Kullanılabilir algoritmaları listele"""
        return [
            {
                "id": alg_id,
                "name": info["name"],
                "description": info["description"],
                "default_params": info["default_params"]
            }
            for alg_id, info in cls.ALGORITHMS.items()
        ]

    @classmethod
    def create_algorithm(
        cls,
        algorithm: str,
        projects: Dict[int, Dict],
        instructors: Dict[int, Dict],
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseAlgorithm]:
        """Seçilen algoritmayı oluştur"""
        if algorithm not in cls.ALGORITHMS:
            return None
        
        # Parametreleri birleştir
        algorithm_params = cls.ALGORITHMS[algorithm]["default_params"].copy()
        if params:
            algorithm_params.update(params)
        
        # Algoritmayı oluştur
        if algorithm == "genetic":
            return GeneticAlgorithm(
                projects=projects,
                instructors=instructors,
                population_size=algorithm_params["population_size"],
                generations=algorithm_params["generations"],
                mutation_rate=algorithm_params["mutation_rate"],
                crossover_rate=algorithm_params["crossover_rate"]
            )
        elif algorithm == "simulated_annealing":
            return SimulatedAnnealingAlgorithm(
                projects=projects,
                instructors=instructors,
                initial_temperature=algorithm_params["initial_temperature"],
                cooling_rate=algorithm_params["cooling_rate"],
                iterations=algorithm_params["iterations"],
                acceptance_probability=algorithm_params["acceptance_probability"]
            )
        elif algorithm == "ant_colony":
            return AntColonyAlgorithm(
                projects=projects,
                instructors=instructors,
                colony_size=algorithm_params["colony_size"],
                iterations=algorithm_params["iterations"],
                evaporation_rate=algorithm_params["evaporation_rate"],
                pheromone_factor=algorithm_params["pheromone_factor"],
                heuristic_factor=algorithm_params["heuristic_factor"]
            )
        elif algorithm == "nsga_ii":
            return NSGAII(
                projects=projects,
                instructors=instructors,
                population_size=algorithm_params["population_size"],
                generations=algorithm_params["generations"],
                crossover_rate=algorithm_params["crossover_rate"],
                mutation_rate=algorithm_params["mutation_rate"]
            )
        elif algorithm == "greedy":
            return GreedyAlgorithm(
                projects=projects,
                instructors=instructors,
                local_search_iterations=algorithm_params["local_search_iterations"],
                neighborhood_size=algorithm_params["neighborhood_size"],
                rule_weight=algorithm_params["rule_weight"],
                load_weight=algorithm_params["load_weight"],
                classroom_weight=algorithm_params["classroom_weight"]
            )
        elif algorithm == "tabu_search":
            return TabuSearchAlgorithm(
                projects=projects,
                instructors=instructors,
                iterations=algorithm_params["iterations"],
                tabu_tenure=algorithm_params["tabu_tenure"],
                neighborhood_size=algorithm_params["neighborhood_size"],
                aspiration_factor=algorithm_params["aspiration_factor"],
                rule_weight=algorithm_params["rule_weight"],
                load_weight=algorithm_params["load_weight"],
                classroom_weight=algorithm_params["classroom_weight"]
            )
        elif algorithm == "pso":
            return ParticleSwarmOptimization(
                projects=projects,
                instructors=instructors,
                swarm_size=algorithm_params["swarm_size"],
                iterations=algorithm_params["iterations"],
                inertia_weight=algorithm_params["inertia_weight"],
                cognitive_coefficient=algorithm_params["cognitive_coefficient"],
                social_coefficient=algorithm_params["social_coefficient"],
                rule_weight=algorithm_params["rule_weight"],
                load_weight=algorithm_params["load_weight"],
                classroom_weight=algorithm_params["classroom_weight"]
            )
        elif algorithm == "harmony_search":
            return HarmonySearch(
                projects=projects,
                instructors=instructors,
                harmony_memory_size=algorithm_params["harmony_memory_size"],
                iterations=algorithm_params["iterations"],
                harmony_memory_considering_rate=algorithm_params["harmony_memory_considering_rate"],
                pitch_adjusting_rate=algorithm_params["pitch_adjusting_rate"],
                bandwidth=algorithm_params["bandwidth"],
                rule_weight=algorithm_params["rule_weight"],
                load_weight=algorithm_params["load_weight"],
                classroom_weight=algorithm_params["classroom_weight"]
            )
        elif algorithm == "firefly":
            return FireflyAlgorithm(
                projects=projects,
                instructors=instructors,
                population_size=algorithm_params["population_size"],
                iterations=algorithm_params["iterations"],
                alpha=algorithm_params["alpha"],
                beta0=algorithm_params["beta0"],
                gamma=algorithm_params["gamma"],
                rule_weight=algorithm_params["rule_weight"],
                load_weight=algorithm_params["load_weight"],
                classroom_weight=algorithm_params["classroom_weight"]
            )
        elif algorithm == "grey_wolf":
            return GreyWolfOptimizer(
                projects=projects,
                instructors=instructors,
                population_size=algorithm_params["population_size"],
                iterations=algorithm_params["iterations"],
                rule_weight=algorithm_params["rule_weight"],
                load_weight=algorithm_params["load_weight"],
                classroom_weight=algorithm_params["classroom_weight"]
            )
        elif algorithm == "cp_sat":
            return CPSATSolver(
                projects=projects,
                instructors=instructors,
                time_limit_seconds=algorithm_params["time_limit_seconds"],
                num_search_workers=algorithm_params["num_search_workers"],
                rule_weight=algorithm_params["rule_weight"],
                load_weight=algorithm_params["load_weight"],
                classroom_weight=algorithm_params["classroom_weight"]
            )
        elif algorithm == "deep_search":
            return DeepSearch(
                projects=projects,
                instructors=instructors,
                beam_width=algorithm_params["beam_width"],
                max_depth=algorithm_params["max_depth"],
                time_limit_seconds=algorithm_params["time_limit_seconds"],
                rule_weight=algorithm_params["rule_weight"],
                load_weight=algorithm_params["load_weight"],
                classroom_weight=algorithm_params["classroom_weight"]
            )

    @classmethod
    def recommend_algorithm(
        cls,
        projects: Dict[int, Dict],
        instructors: Dict[int, Dict]
    ) -> Dict[str, Any]:
        """Problem özelliklerine göre en uygun algoritmayı öner"""
        num_projects = len(projects)
        num_instructors = len(instructors)
        
        # Problem boyutuna göre öneriler
        if num_projects <= 10 and num_instructors <= 10:
            # Küçük problemler için CP-SAT
            return {
                "algorithm": "cp_sat",
                "reason": "Küçük boyutlu problem için optimal çözüm sağlayabilir",
                "params": cls.ALGORITHMS["cp_sat"]["default_params"]
            }
        elif num_projects <= 20 and num_instructors <= 15:
            # Küçük-orta boyutlu problemler için Tabu Search
            return {
                "algorithm": "tabu_search",
                "reason": "Küçük-orta boyutlu problem için hızlı ve etkili çözüm sağlar",
                "params": cls.ALGORITHMS["tabu_search"]["default_params"]
            }
        elif num_projects <= 30 and num_instructors <= 20:
            # Orta boyutlu problemler için Ant Colony
            return {
                "algorithm": "ant_colony",
                "reason": "Orta boyutlu problem için dengeli çözüm sağlar",
                "params": cls.ALGORITHMS["ant_colony"]["default_params"]
            }
        elif num_projects <= 50 and num_instructors <= 30:
            # Orta-büyük boyutlu problemler için PSO
            return {
                "algorithm": "pso",
                "reason": "Orta-büyük boyutlu problem için hızlı yakınsama sağlar",
                "params": cls.ALGORITHMS["pso"]["default_params"]
            }
        else:
            # Büyük problemler için NSGA-II
            return {
                "algorithm": "nsga_ii",
                "reason": "Büyük boyutlu problem için çok amaçlı optimizasyon sağlar",
                "params": cls.ALGORITHMS["nsga_ii"]["default_params"]
            }

    @classmethod
    def validate_parameters(cls, algorithm: str, params: Dict[str, Any]) -> bool:
        """Algoritma parametrelerini doğrula"""
        if algorithm not in cls.ALGORITHMS:
            return False
        
        default_params = cls.ALGORITHMS[algorithm]["default_params"]
        
        # Tüm gerekli parametrelerin var olduğunu kontrol et
        for param_name in default_params:
            if param_name not in params:
                return False
            
            # max_depth can be None for deep_search
            if param_name == "max_depth" and params[param_name] is None:
                continue
                
            # Tip kontrolü
            if not isinstance(params[param_name], type(default_params[param_name])):
                return False
            
            # Değer aralığı kontrolü
            if isinstance(params[param_name], (int, float)):
                if params[param_name] <= 0:
                    return False
        
        return True

    @staticmethod
    def get_algorithm(algorithm_name: str) -> Optional[BaseAlgorithm]:
        """
        Get an algorithm instance by name.
        
        Args:
            algorithm_name: Name of the algorithm to get
            
        Returns:
            An instance of the requested algorithm or None if not found
        """
        algorithms = {
            "genetic": GeneticAlgorithm(),
            "ant_colony": AntColonyAlgorithm(),
            "simulated_annealing": SimulatedAnnealingAlgorithm(),
            "nsga_ii": NSGAII(),
            "greedy": GreedyAlgorithm(),
            "tabu_search": TabuSearchAlgorithm(),
            "pso": ParticleSwarmOptimization(),
            "harmony_search": HarmonySearch(),
            "firefly": FireflyAlgorithm(),
            "grey_wolf": GreyWolfOptimizer(),
            "cp_sat": CPSATSolver(),
            "deep_search": DeepSearch()
        }
        
        return algorithms.get(algorithm_name) 