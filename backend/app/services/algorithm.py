from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import json
import time

from app.models.algorithm import AlgorithmRun
from app.models.project import Project
from app.models.instructor import Instructor
from app.schemas.algorithm import AlgorithmCreate, AlgorithmUpdate
from app.algorithms.factory import AlgorithmFactory
from app.core.cache import cache
from app.core.celery import celery_app
from app import crud, models, schemas

class AlgorithmService:
    def __init__(self, db: Session):
        self.db = db
        
    # Detailed algorithm descriptions with parameters explanation
    ALGORITHM_DETAILS = {
        "genetic": {
            "name": "Genetic Algorithm",
            "description": "An evolutionary algorithm inspired by natural selection that uses mechanisms like mutation, crossover, and selection to evolve a population of solutions.",
            "strengths": [
                "Good for large search spaces",
                "Can find multiple good solutions",
                "Parallelizable"
            ],
            "weaknesses": [
                "May converge to local optima",
                "Parameter tuning can be challenging",
                "Computationally intensive for large populations"
            ],
            "parameters": {
                "population_size": "Number of solutions in each generation (higher values increase diversity but slow down execution)",
                "generations": "Maximum number of iterations (higher values allow more evolution but increase runtime)",
                "mutation_rate": "Probability of random changes in solutions (0-1, higher values increase exploration)",
                "crossover_rate": "Probability of combining solutions (0-1, higher values increase exploitation)"
            }
        },
        "simulated_annealing": {
            "name": "Simulated Annealing",
            "description": "A probabilistic technique inspired by the annealing process in metallurgy that gradually reduces the probability of accepting worse solutions as it explores the search space.",
            "strengths": [
                "Can escape local optima",
                "Simple to implement",
                "Works well for many combinatorial problems"
            ],
            "weaknesses": [
                "Sequential nature limits parallelization",
                "Performance depends on cooling schedule",
                "May not find global optimum with poor parameters"
            ],
            "parameters": {
                "initial_temperature": "Starting temperature (higher values increase initial exploration)",
                "cooling_rate": "Rate at which temperature decreases (smaller values lead to slower cooling)",
                "iterations": "Number of iterations at each temperature level",
                "acceptance_probability": "Base probability for accepting worse solutions"
            }
        },
        "ant_colony": {
            "name": "Ant Colony Optimization",
            "description": "A nature-inspired algorithm based on the foraging behavior of ants, using pheromone trails to guide the search toward promising solutions.",
            "strengths": [
                "Good for routing and assignment problems",
                "Can adapt to changing environments",
                "Inherently parallelizable"
            ],
            "weaknesses": [
                "Slow convergence for some problems",
                "Pheromone management can be complex",
                "May stagnate on suboptimal solutions"
            ],
            "parameters": {
                "colony_size": "Number of ants in the colony (larger colonies explore more paths)",
                "iterations": "Number of iterations for the algorithm to run",
                "evaporation_rate": "Rate at which pheromones evaporate (0-1, higher values reduce influence of past solutions)",
                "pheromone_factor": "Weight given to pheromone trails in decision making",
                "heuristic_factor": "Weight given to heuristic information in decision making"
            }
        },
        "nsga_ii": {
            "name": "NSGA-II (Non-dominated Sorting Genetic Algorithm II)",
            "description": "A multi-objective evolutionary algorithm that uses non-dominated sorting and crowding distance to maintain diversity while converging to the Pareto-optimal front.",
            "strengths": [
                "Handles multiple objectives simultaneously",
                "Maintains diverse solutions along Pareto front",
                "Elitist approach preserves good solutions"
            ],
            "weaknesses": [
                "Computationally intensive for many objectives",
                "May struggle with highly constrained problems",
                "Parameter tuning can be challenging"
            ],
            "parameters": {
                "population_size": "Number of solutions in each generation (higher values increase diversity)",
                "generations": "Maximum number of iterations for evolution",
                "crossover_rate": "Probability of combining solutions (0-1)",
                "mutation_rate": "Probability of random changes in solutions (0-1)"
            }
        },
        "greedy": {
            "name": "Greedy Algorithm with Local Search",
            "description": "A two-phase approach that first constructs a solution using greedy choices and then improves it through local search in the neighborhood of the solution.",
            "strengths": [
                "Fast initial solution construction",
                "Simple to implement and understand",
                "Local search improves solution quality"
            ],
            "weaknesses": [
                "May get stuck in local optima",
                "Quality depends on initial greedy construction",
                "Not guaranteed to find global optimum"
            ],
            "parameters": {
                "local_search_iterations": "Number of improvement attempts after greedy construction",
                "neighborhood_size": "Number of neighbors to explore in each iteration",
                "rule_weight": "Weight for rule violations in fitness calculation",
                "load_weight": "Weight for load imbalance in fitness calculation",
                "classroom_weight": "Weight for classroom changes in fitness calculation"
            }
        },
        "tabu_search": {
            "name": "Tabu Search",
            "description": "A metaheuristic that enhances local search by using memory structures (tabu lists) to avoid revisiting recent solutions and escape local optima.",
            "strengths": [
                "Effective at escaping local optima",
                "Memory structures guide search efficiently",
                "Aspiration criteria allow flexibility"
            ],
            "weaknesses": [
                "Memory management can be complex",
                "Parameter tuning is important",
                "Performance depends on neighborhood definition"
            ],
            "parameters": {
                "iterations": "Maximum number of search iterations",
                "tabu_tenure": "How long moves remain tabu (forbidden)",
                "neighborhood_size": "Number of neighbors to explore in each iteration",
                "aspiration_factor": "Factor to override tabu status for very good solutions",
                "rule_weight": "Weight for rule violations in fitness calculation",
                "load_weight": "Weight for load imbalance in fitness calculation",
                "classroom_weight": "Weight for classroom changes in fitness calculation"
            }
        },
        "pso": {
            "name": "Particle Swarm Optimization",
            "description": "A swarm intelligence algorithm inspired by social behavior of birds or fish, where particles move through the search space guided by their own and the swarm's best known positions.",
            "strengths": [
                "Simple concept and implementation",
                "Few parameters to tune",
                "Good convergence properties"
            ],
            "weaknesses": [
                "May converge prematurely",
                "Handling discrete variables requires adaptation",
                "Performance depends on parameter settings"
            ],
            "parameters": {
                "swarm_size": "Number of particles in the swarm",
                "iterations": "Maximum number of iterations",
                "inertia_weight": "Controls influence of previous velocity (typically 0.4-0.9)",
                "cognitive_coefficient": "Weight for particle's own best position (typically ~2)",
                "social_coefficient": "Weight for swarm's best position (typically ~2)",
                "rule_weight": "Weight for rule violations in fitness calculation",
                "load_weight": "Weight for load imbalance in fitness calculation",
                "classroom_weight": "Weight for classroom changes in fitness calculation"
            }
        },
        "harmony_search": {
            "name": "Harmony Search",
            "description": "A music-inspired metaheuristic that mimics the improvisation process of musicians seeking a perfect harmony, balancing exploration and exploitation.",
            "strengths": [
                "Simple concept and implementation",
                "Good balance of exploration and exploitation",
                "Does not require derivative information"
            ],
            "weaknesses": [
                "Parameter tuning can be challenging",
                "May converge slowly for some problems",
                "Performance varies with problem structure"
            ],
            "parameters": {
                "harmony_memory_size": "Number of solution vectors stored in memory",
                "iterations": "Maximum number of improvisations",
                "harmony_memory_considering_rate": "Probability of using values from memory (0-1)",
                "pitch_adjusting_rate": "Probability of local adjustments to values (0-1)",
                "bandwidth": "Maximum adjustment amount for pitch adjustment",
                "rule_weight": "Weight for rule violations in fitness calculation",
                "load_weight": "Weight for load imbalance in fitness calculation",
                "classroom_weight": "Weight for classroom changes in fitness calculation"
            }
        },
        "firefly": {
            "name": "Firefly Algorithm",
            "description": "A nature-inspired algorithm based on the flashing behavior of fireflies, where brighter fireflies (better solutions) attract others toward them.",
            "strengths": [
                "Automatic subdivision of population into groups",
                "Can handle multimodal optimization effectively",
                "Good convergence properties"
            ],
            "weaknesses": [
                "Parameter tuning is important",
                "Computationally intensive for large populations",
                "May converge prematurely with poor parameters"
            ],
            "parameters": {
                "population_size": "Number of fireflies in the population",
                "iterations": "Maximum number of iterations",
                "alpha": "Randomization parameter (typically decreases over iterations)",
                "beta0": "Attractiveness at distance=0 (base attractiveness)",
                "gamma": "Light absorption coefficient (controls visibility)",
                "rule_weight": "Weight for rule violations in fitness calculation",
                "load_weight": "Weight for load imbalance in fitness calculation",
                "classroom_weight": "Weight for classroom changes in fitness calculation"
            }
        },
        "grey_wolf": {
            "name": "Grey Wolf Optimizer",
            "description": "A metaheuristic inspired by the social hierarchy and hunting behavior of grey wolves, with alpha, beta, and delta wolves guiding the search.",
            "strengths": [
                "Hierarchical leadership structure guides search effectively",
                "Good balance of exploration and exploitation",
                "Few parameters to tune"
            ],
            "weaknesses": [
                "May converge prematurely for complex problems",
                "Performance depends on initial population diversity",
                "Limited theoretical foundation"
            ],
            "parameters": {
                "population_size": "Number of wolves in the pack",
                "iterations": "Maximum number of iterations",
                "rule_weight": "Weight for rule violations in fitness calculation",
                "load_weight": "Weight for load imbalance in fitness calculation",
                "classroom_weight": "Weight for classroom changes in fitness calculation"
            }
        },
        "cp_sat": {
            "name": "CP-SAT Solver",
            "description": "A constraint programming approach using a SAT (Boolean satisfiability) solver to find optimal solutions by defining constraints and objectives mathematically.",
            "strengths": [
                "Can find provably optimal solutions",
                "Handles constraints naturally",
                "Efficient for well-structured problems"
            ],
            "weaknesses": [
                "May not scale well to very large problems",
                "Requires OR-Tools library",
                "Modeling constraints can be complex"
            ],
            "parameters": {
                "time_limit_seconds": "Maximum runtime before returning best solution found",
                "num_search_workers": "Number of parallel search threads",
                "rule_weight": "Weight for rule violations in fitness calculation",
                "load_weight": "Weight for load imbalance in fitness calculation",
                "classroom_weight": "Weight for classroom changes in fitness calculation"
            }
        },
        "deep_search": {
            "name": "Deep Search",
            "description": "A hybrid search algorithm combining beam search with iterative deepening to efficiently explore the solution space while managing memory usage.",
            "strengths": [
                "Memory-efficient exploration of large search spaces",
                "Iterative deepening provides anytime solutions",
                "Beam search balances breadth and depth"
            ],
            "weaknesses": [
                "May miss optimal solutions with narrow beam width",
                "Parameter tuning is important",
                "Time-limited search may not explore full space"
            ],
            "parameters": {
                "beam_width": "Number of partial solutions to keep at each step",
                "max_depth": "Maximum search depth (null means all projects)",
                "time_limit_seconds": "Maximum runtime before returning best solution",
                "rule_weight": "Weight for rule violations in fitness calculation",
                "load_weight": "Weight for load imbalance in fitness calculation",
                "classroom_weight": "Weight for classroom changes in fitness calculation"
            }
        }
    }

    def get_available_algorithms(self) -> List[Dict[str, Any]]:
        """Kullanılabilir algoritmaları listele"""
        algorithms = AlgorithmFactory.get_available_algorithms()
        
        # Add detailed descriptions
        for alg in algorithms:
            if alg["id"] in self.ALGORITHM_DETAILS:
                details = self.ALGORITHM_DETAILS[alg["id"]]
                alg.update({
                    "detailed_description": details["description"],
                    "strengths": details["strengths"],
                    "weaknesses": details["weaknesses"],
                    "parameter_descriptions": details["parameters"]
                })
                
        return algorithms

    def recommend_algorithm(self, projects: Dict[int, Dict], instructors: Dict[int, Dict]) -> Dict[str, Any]:
        """Problem özelliklerine göre en uygun algoritmayı öner"""
        recommendation = AlgorithmFactory.recommend_algorithm(projects, instructors)
        
        # Add detailed descriptions
        if recommendation["algorithm"] in self.ALGORITHM_DETAILS:
            details = self.ALGORITHM_DETAILS[recommendation["algorithm"]]
            recommendation.update({
                "detailed_description": details["description"],
                "strengths": details["strengths"],
                "weaknesses": details["weaknesses"],
                "parameter_descriptions": details["parameters"]
            })
            
        return recommendation

    @cache(ttl=3600)  # 1 saat cache
    def get_algorithm_by_id(self, algorithm_id: int) -> Optional[AlgorithmRun]:
        """ID'ye göre algoritma çalıştırma kaydını getir"""
        return self.db.query(AlgorithmRun).filter(AlgorithmRun.id == algorithm_id).first()

    def create_algorithm_run(self, data: AlgorithmCreate) -> AlgorithmRun:
        """Yeni bir algoritma çalıştırma kaydı oluştur"""
        # Parametreleri doğrula
        if not AlgorithmFactory.validate_parameters(data.algorithm, data.params):
            raise ValueError("Geçersiz algoritma parametreleri")

        # Projeleri ve öğretim elemanlarını getir
        projects = {p.id: p.dict() for p in self.db.query(Project).all()}
        instructors = {i.id: i.dict() for p in self.db.query(Instructor).all()}

        # Algoritma kaydını oluştur
        algorithm_run = AlgorithmRun(
            algorithm=data.algorithm,
            params=data.params,
            status="pending",
            created_at=datetime.utcnow()
        )
        self.db.add(algorithm_run)
        self.db.commit()
        self.db.refresh(algorithm_run)

        # Asenkron görevi başlat
        celery_app.send_task(
            "app.tasks.run_algorithm",
            args=[algorithm_run.id, data.algorithm, data.params, projects, instructors]
        )

        return algorithm_run

    def update_algorithm_run(self, algorithm_id: int, data: AlgorithmUpdate) -> Optional[AlgorithmRun]:
        """Algoritma çalıştırma kaydını güncelle"""
        algorithm = self.get_algorithm_by_id(algorithm_id)
        if not algorithm:
            return None

        for field, value in data.dict(exclude_unset=True).items():
            setattr(algorithm, field, value)

        self.db.commit()
        self.db.refresh(algorithm)
        return algorithm

    def delete_algorithm_run(self, algorithm_id: int) -> bool:
        """Algoritma çalıştırma kaydını sil"""
        algorithm = self.get_algorithm_by_id(algorithm_id)
        if not algorithm:
            return False

        self.db.delete(algorithm)
        self.db.commit()
        return True

    def get_algorithm_results(self, algorithm_id: int) -> Optional[Dict[str, Any]]:
        """Algoritma sonuçlarını getir"""
        algorithm = self.get_algorithm_by_id(algorithm_id)
        if not algorithm or algorithm.status != "completed":
            return None

        result = {
            "id": algorithm.id,
            "algorithm": algorithm.algorithm,
            "params": algorithm.params,
            "result": algorithm.result,
            "execution_time": algorithm.execution_time,
            "status": algorithm.status,
            "created_at": algorithm.created_at,
            "completed_at": algorithm.completed_at
        }
        
        # Add algorithm details if available
        if algorithm.algorithm in self.ALGORITHM_DETAILS:
            result["details"] = self.ALGORITHM_DETAILS[algorithm.algorithm]
            
        return result

    def compare_algorithms(
        self,
        projects: Dict[int, Dict],
        instructors: Dict[int, Dict],
        algorithms: List[str]
    ) -> Dict[str, Any]:
        """Seçilen algoritmaları karşılaştır"""
        results = {}
        
        for alg_id in algorithms:
            # Algoritmayı oluştur ve çalıştır
            algorithm = AlgorithmFactory.create_algorithm(
                algorithm=alg_id,
                projects=projects,
                instructors=instructors
            )
            
            # Başlangıç zamanını kaydet
            start_time = datetime.utcnow()
            
            # Algoritmayı çalıştır
            result = algorithm.optimize()
            
            # Bitiş zamanını kaydet
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            # Sonuçları kaydet
            results[alg_id] = {
                "assignments": result["assignments"],
                "quality": result.get("quality") or result.get("fitness") or result.get("energy"),
                "execution_time": execution_time
            }
            
            # Add algorithm details if available
            if alg_id in self.ALGORITHM_DETAILS:
                results[alg_id]["details"] = self.ALGORITHM_DETAILS[alg_id]
        
        return {
            "results": results,
            "comparison": self._compare_results(results)
        }

    def _compare_results(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Algoritma sonuçlarını karşılaştır ve analiz et"""
        comparison = {
            "best_quality": {
                "algorithm": None,
                "value": float('inf')
            },
            "fastest": {
                "algorithm": None,
                "time": float('inf')
            },
            "quality_ranking": [],
            "time_ranking": [],
            "overall_recommendation": None
        }
        
        # En iyi kalite ve en hızlı algoritmayı bul
        for alg_id, result in results.items():
            quality = result["quality"]
            time = result["execution_time"]
            
            if quality < comparison["best_quality"]["value"]:
                comparison["best_quality"] = {
                    "algorithm": alg_id,
                    "value": quality
                }
            
            if time < comparison["fastest"]["time"]:
                comparison["fastest"] = {
                    "algorithm": alg_id,
                    "time": time
                }
        
        # Sıralamaları oluştur
        quality_sorted = sorted(results.items(), key=lambda x: x[1]["quality"])
        time_sorted = sorted(results.items(), key=lambda x: x[1]["execution_time"])
        
        comparison["quality_ranking"] = [alg for alg, _ in quality_sorted]
        comparison["time_ranking"] = [alg for alg, _ in time_sorted]
        
        # Genel öneri
        # En iyi kalite ve hız arasında denge kur
        scores = {}
        for alg_id in results:
            quality_rank = comparison["quality_ranking"].index(alg_id)
            time_rank = comparison["time_ranking"].index(alg_id)
            # Kaliteye daha fazla ağırlık ver
            scores[alg_id] = quality_rank * 0.7 + time_rank * 0.3
        
        comparison["overall_recommendation"] = min(scores.items(), key=lambda x: x[1])[0]
        
        return comparison

async def run_algorithm(
    db: Session, algorithm_run_id: int, algorithm_name: str, params: Dict[str, Any]
) -> None:
    """
    Run an algorithm in the background and update its status in the database.
    """
    try:
        # Update status to running
        algorithm_run = crud.algorithm.get(db, id=algorithm_run_id)
        if not algorithm_run:
            return
        
        crud.algorithm.update(
            db, 
            db_obj=algorithm_run, 
            obj_in={"status": "running", "started_at": datetime.now()}
        )
        
        # Get algorithm instance from factory
        algorithm = AlgorithmFactory.get_algorithm(algorithm_name)
        if not algorithm:
            crud.algorithm.update(
                db, 
                db_obj=algorithm_run, 
                obj_in={
                    "status": "failed", 
                    "result": json.dumps({"error": f"Algorithm {algorithm_name} not found"}),
                    "completed_at": datetime.now()
                }
            )
            return
        
        # Run algorithm (with some delay to simulate processing)
        start_time = time.time()
        result = algorithm.run(params)
        execution_time = time.time() - start_time
        
        # Update with results
        crud.algorithm.update(
            db, 
            db_obj=algorithm_run, 
            obj_in={
                "status": "completed", 
                "result": json.dumps(result),
                "execution_time": execution_time,
                "completed_at": datetime.now()
            }
        )
    
    except Exception as e:
        # Update with error
        crud.algorithm.update(
            db, 
            db_obj=algorithm_run, 
            obj_in={
                "status": "failed", 
                "result": json.dumps({"error": str(e)}),
                "completed_at": datetime.now()
            }
        )


def get_algorithm_result(db: Session, algorithm_run_id: int) -> models.AlgorithmRun:
    """
    Get the result of an algorithm run.
    """
    return crud.algorithm.get(db, id=algorithm_run_id)


def recommend_best_algorithm(
    db: Session, project_type: Optional[str] = None, optimize_for: Optional[str] = None
) -> schemas.AlgorithmRecommendation:
    """
    Recommend the best algorithm for a given problem.
    """
    # Implement logic to recommend an algorithm based on project_type and optimization target
    algorithms = {
        "simplex": {
            "score": 0,
            "reason": ""
        },
        "genetic": {
            "score": 0,
            "reason": ""
        },
        "simulated_annealing": {
            "score": 0,
            "reason": ""
        },
        "ant_colony": {
            "score": 0,
            "reason": ""
        }
    }
    
    # Default scores
    if project_type == "bitirme" or project_type == "final":
        # Bitirme projeleri daha karmaşık, genetic ve annealing daha iyi olabilir
        algorithms["genetic"]["score"] += 2
        algorithms["simulated_annealing"]["score"] += 2
        algorithms["ant_colony"]["score"] += 1
    elif project_type == "ara" or project_type == "interim":
        # Ara projeler için simplex ve ant colony daha hızlı çözüm verebilir
        algorithms["simplex"]["score"] += 2
        algorithms["ant_colony"]["score"] += 1
    
    # Optimize for what?
    if optimize_for == "balanced_load":
        # Yük dengelemesi için genetic daha iyi
        algorithms["genetic"]["score"] += 2
        algorithms["reason"] = "Yük dengeleme için genetik algoritma daha iyi sonuçlar verir"
    elif optimize_for == "min_transitions":
        # Geçişleri minimize etmek için simulated annealing
        algorithms["simulated_annealing"]["score"] += 2
        algorithms["reason"] = "Minimum geçiş için tavlama benzetimi daha iyi"
    elif optimize_for == "speed":
        # Hızlı çözüm için simplex
        algorithms["simplex"]["score"] += 3
        algorithms["reason"] = "Hızlı çözüm için simplex algoritması tercih edilir"
        
    # Get algorithm run stats from database
    algorithm_stats = {
        alg: {
            "runtime": 0, 
            "success_rate": 0
        } for alg in algorithms
    }
    
    # Fetch all completed algorithm runs
    completed_runs = db.query(
        models.AlgorithmRun.algorithm, 
        models.AlgorithmRun.execution_time
    ).filter(
        models.AlgorithmRun.status == "completed"
    ).all()
    
    for alg, exec_time in completed_runs:
        if alg in algorithm_stats:
            algorithm_stats[alg]["runtime"] += exec_time
            algorithm_stats[alg]["success_rate"] += 1
    
    # Calculate average runtimes
    for alg in algorithm_stats:
        if algorithm_stats[alg]["success_rate"] > 0:
            algorithm_stats[alg]["runtime"] /= algorithm_stats[alg]["success_rate"]
            # Add score bonus for algorithms with good history
            algorithms[alg]["score"] += 1
    
    # Find highest scoring algorithm
    best_alg = max(algorithms.items(), key=lambda x: x[1]["score"])
    
    return schemas.AlgorithmRecommendation(
        recommended=best_alg[0],
        reason=best_alg[1]["reason"] or "Bu problem türü için en uygun algoritma",
        scores={k: {"score": v["score"]} for k, v in algorithms.items()}
    ) 