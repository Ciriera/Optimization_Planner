from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import random

class Algorithm(ABC):
    """Temel algoritma sınıfı"""
    def __init__(self, projects: Dict[int, Dict], instructors: Dict[int, Dict], params: Dict[str, Any]):
        self.projects = projects
        self.instructors = instructors
        self.params = params

    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """Algoritmayı çalıştır"""
        pass

class GeneticAlgorithm(Algorithm):
    """Genetik algoritma sınıfı"""
    def run(self) -> Dict[str, Any]:
        population_size = self.params.get("population_size", 50)
        generations = self.params.get("generations", 100)
        mutation_rate = self.params.get("mutation_rate", 0.1)

        # Basit bir genetik algoritma simülasyonu
        assignments = {
            project_id: random.choice(list(self.instructors.keys()))
            for project_id in self.projects.keys()
        }
        fitness = random.random()  # Simüle edilmiş uygunluk değeri

        return {
            "assignments": assignments,
            "fitness": fitness
        }

class SimulatedAnnealing(Algorithm):
    """Simulated Annealing algoritma sınıfı"""
    def run(self) -> Dict[str, Any]:
        initial_temperature = self.params.get("initial_temperature", 100.0)
        cooling_rate = self.params.get("cooling_rate", 0.01)
        iterations = self.params.get("iterations", 1000)

        # Basit bir simulated annealing simülasyonu
        assignments = {
            project_id: random.choice(list(self.instructors.keys()))
            for project_id in self.projects.keys()
        }
        energy = random.random()  # Simüle edilmiş enerji değeri

        return {
            "assignments": assignments,
            "energy": energy
        }

class AntColony(Algorithm):
    """Ant Colony Optimization algoritma sınıfı"""
    def run(self) -> Dict[str, Any]:
        n_ants = self.params.get("n_ants", 10)
        n_iterations = self.params.get("n_iterations", 100)
        decay = self.params.get("decay", 0.1)
        alpha = self.params.get("alpha", 1)
        beta = self.params.get("beta", 2)

        # Basit bir ant colony optimization simülasyonu
        assignments = {
            project_id: random.choice(list(self.instructors.keys()))
            for project_id in self.projects.keys()
        }
        pheromone_levels = random.random()  # Simüle edilmiş feromon seviyeleri

        return {
            "assignments": assignments,
            "pheromone_levels": pheromone_levels
        }

class AlgorithmFactory:
    """Algoritma factory sınıfı"""
    _algorithms = {
        "genetic": GeneticAlgorithm,
        "simulated_annealing": SimulatedAnnealing,
        "ant_colony": AntColony
    }

    @classmethod
    def create_algorithm(
        cls,
        name: str,
        projects: Dict[int, Dict],
        instructors: Dict[int, Dict],
        params: Optional[Dict[str, Any]] = None
    ) -> Algorithm:
        """Algoritma örneği oluştur"""
        if name not in cls._algorithms:
            raise ValueError(f"Bilinmeyen algoritma: {name}")

        algorithm_class = cls._algorithms[name]
        return algorithm_class(projects, instructors, params or {})

    @classmethod
    def get_available_algorithms(cls) -> List[Dict[str, str]]:
        """Kullanılabilir algoritmaları listele"""
        return [
            {
                "name": "genetic",
                "description": "Genetik algoritma, evrimsel hesaplama tabanlı optimizasyon"
            },
            {
                "name": "simulated_annealing",
                "description": "Simulated Annealing, fizik tabanlı optimizasyon"
            },
            {
                "name": "ant_colony",
                "description": "Ant Colony Optimization, sürü zekası tabanlı optimizasyon"
            }
        ]

    @classmethod
    def recommend_algorithm(
        cls,
        projects: Dict[int, Dict],
        instructors: Dict[int, Dict]
    ) -> Dict[str, Any]:
        """Problem özelliklerine göre algoritma öner"""
        problem_size = len(projects)

        if problem_size < 10:
            return {
                "name": "simulated_annealing",
                "params": {
                    "initial_temperature": 100.0,
                    "cooling_rate": 0.01,
                    "iterations": 1000
                },
                "reason": "Küçük boyutlu problem için hızlı ve etkili çözüm sağlar"
            }
        elif problem_size < 50:
            return {
                "name": "genetic",
                "params": {
                    "population_size": 100,
                    "generations": 200,
                    "mutation_rate": 0.1
                },
                "reason": "Orta boyutlu problem için dengeli çözüm sağlar"
            }
        else:
            return {
                "name": "ant_colony",
                "params": {
                    "n_ants": 20,
                    "n_iterations": 500,
                    "decay": 0.1,
                    "alpha": 1,
                    "beta": 2
                },
                "reason": "Büyük boyutlu problem için paralel arama yapabilir"
            } 