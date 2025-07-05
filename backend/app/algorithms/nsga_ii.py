import random
import numpy as np
from typing import Dict, Any, List, Tuple
from app.algorithms.base import BaseAlgorithm

class NSGAII(BaseAlgorithm):
    """Non-dominated Sorting Genetic Algorithm II (NSGA-II) implementation."""
    
    def __init__(
        self,
        projects=None,
        instructors=None,
        population_size=100,
        generations=50,
        crossover_rate=0.8,
        mutation_rate=0.2
    ):
        super().__init__(projects, instructors, {
            'population_size': population_size,
            'generations': generations,
            'crossover_rate': crossover_rate,
            'mutation_rate': mutation_rate
        })
        
    def validate_parameters(self) -> bool:
        """Validate algorithm parameters."""
        if not self.parameters:
            return False
            
        required_params = ['population_size', 'generations', 'crossover_rate', 'mutation_rate']
        for param in required_params:
            if param not in self.parameters:
                return False
                
            # Check numeric parameters are positive
            if self.parameters[param] <= 0:
                return False
                
        # Check rates are between 0 and 1
        if not (0 <= self.parameters['crossover_rate'] <= 1):
            return False
        if not (0 <= self.parameters['mutation_rate'] <= 1):
            return False
            
        return True
        
    def optimize(self) -> Dict[str, Any]:
        """Run NSGA-II optimization algorithm."""
        if not self.projects or not self.instructors:
            return {"error": "No projects or instructors provided"}
            
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        
        # Initialize population
        population = self._initialize_population()
        
        # Evaluate initial population
        objectives = self._evaluate_population(population)
        
        # Main evolution loop
        for generation in range(self.parameters['generations']):
            # Create offspring through selection, crossover, and mutation
            offspring = self._create_offspring(population, objectives)
            
            # Evaluate offspring
            offspring_objectives = self._evaluate_population(offspring)
            
            # Combine parent and offspring populations
            combined_pop = population + offspring
            combined_obj = objectives + offspring_objectives
            
            # Non-dominated sorting and crowding distance calculation
            fronts = self._fast_non_dominated_sort(combined_obj)
            crowding_distances = self._calculate_crowding_distance(combined_obj, fronts)
            
            # Select next generation
            population, objectives = self._select_next_generation(
                combined_pop, combined_obj, fronts, crowding_distances
            )
        
        # Find best solution from final population
        best_idx = self._find_best_solution(objectives)
        best_solution = population[best_idx]
        
        # Convert solution to assignments
        assignments = self._solution_to_assignments(best_solution)
        
        # Calculate metrics
        metrics = self._calculate_metrics(best_solution)
        
        return {
            "assignments": assignments,
            "metrics": metrics,
            "objectives": objectives[best_idx]
        }
        
    def _initialize_population(self) -> List[List[Tuple[int, int, int]]]:
        """Initialize random population of solutions."""
        population = []
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                            if self.instructors[id].get("type") == "professor"]
        
        for _ in range(self.parameters['population_size']):
            solution = []
            
            # Track instructor assignments for load balancing
            instructor_counts = [0] * len(instructor_ids)
            
            for project_idx in range(len(project_ids)):
                # For responsible position, prefer professors
                if professor_indices and random.random() < 0.8:  # 80% chance to select professor
                    responsible_idx = random.choice(professor_indices)
                else:
                    responsible_idx = random.randrange(len(instructor_ids))
                
                # For assistants, select randomly but try to balance load
                available_instructors = list(range(len(instructor_ids)))
                available_instructors.sort(key=lambda i: instructor_counts[i])
                
                assistant1_idx = available_instructors[0]
                if len(available_instructors) > 1:
                    assistant2_idx = available_instructors[1]
                else:
                    assistant2_idx = available_instructors[0]
                
                # Update instructor counts
                instructor_counts[responsible_idx] += 1
                instructor_counts[assistant1_idx] += 1
                instructor_counts[assistant2_idx] += 1
                
                solution.append((responsible_idx, assistant1_idx, assistant2_idx))
            
            population.append(solution)
        
        return population
        
    def _evaluate_population(self, population: List[List[Tuple[int, int, int]]]) -> List[Dict[str, float]]:
        """Evaluate multiple objectives for each solution in the population."""
        objectives = []
        
        for solution in population:
            # Calculate multiple objectives
            rule_violations = self._calculate_rule_violations(solution)
            load_imbalance = self._calculate_load_imbalance(solution)
            classroom_changes = self._calculate_classroom_changes(solution)
            
            objectives.append({
                "rule_violations": rule_violations,
                "load_imbalance": load_imbalance,
                "classroom_changes": classroom_changes
            })
            
        return objectives
        
    def _calculate_rule_violations(self, solution: List[Tuple[int, int, int]]) -> float:
        """Calculate number of rule violations in a solution."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        violations = 0
        
        for i, (responsible_idx, assistant1_idx, assistant2_idx) in enumerate(solution):
            project_id = project_ids[i]
            project = self.projects[project_id]
            
            responsible_id = instructor_ids[responsible_idx]
            assistant1_id = instructor_ids[assistant1_idx]
            assistant2_id = instructor_ids[assistant2_idx]
            
            # Rule 1: Responsible should be professor
            if self.instructors[responsible_id].get("type") != "professor":
                violations += 1
            
            # Rule 2: Final projects need at least 2 professors
            if project.get("type") == "final":
                professor_count = 0
                for instr_idx in [responsible_idx, assistant1_idx, assistant2_idx]:
                    instr_id = instructor_ids[instr_idx]
                    if self.instructors[instr_id].get("type") == "professor":
                        professor_count += 1
                
                if professor_count < 2:
                    violations += 1
        
        return violations
        
    def _calculate_load_imbalance(self, solution: List[Tuple[int, int, int]]) -> float:
        """Calculate load imbalance among instructors."""
        instructor_ids = list(self.instructors.keys())
        instructor_loads = [0] * len(instructor_ids)
        
        for responsible_idx, assistant1_idx, assistant2_idx in solution:
            instructor_loads[responsible_idx] += 1
            instructor_loads[assistant1_idx] += 1
            instructor_loads[assistant2_idx] += 1
        
        # Calculate standard deviation as measure of imbalance
        if instructor_loads:
            return np.std(instructor_loads)
        return 0
        
    def _calculate_classroom_changes(self, solution: List[Tuple[int, int, int]]) -> float:
        """Calculate total classroom changes for instructors."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        
        # Track classrooms for each instructor
        instructor_classrooms = {i: [] for i in range(len(instructor_ids))}
        
        for i, (responsible_idx, assistant1_idx, assistant2_idx) in enumerate(solution):
            project_id = project_ids[i]
            project = self.projects[project_id]
            
            if project.get("classroom"):
                instructor_classrooms[responsible_idx].append(project.get("classroom"))
                instructor_classrooms[assistant1_idx].append(project.get("classroom"))
                instructor_classrooms[assistant2_idx].append(project.get("classroom"))
        
        # Calculate changes
        total_changes = 0
        for instructor_idx, classrooms in instructor_classrooms.items():
            if classrooms:
                # Count unique classrooms - 1 = number of changes
                changes = len(set(classrooms)) - 1
                if changes > 0:
                    # Professors have higher penalty for changes
                    instructor_id = instructor_ids[instructor_idx]
                    if self.instructors[instructor_id].get("type") == "professor":
                        total_changes += changes * 2  # Higher weight for professors
                    else:
                        total_changes += changes
        
        return total_changes
        
    def _create_offspring(self, population: List, objectives: List[Dict[str, float]]) -> List:
        """Create offspring through selection, crossover, and mutation."""
        offspring = []
        
        while len(offspring) < len(population):
            # Tournament selection
            parent1 = self._tournament_selection(population, objectives)
            parent2 = self._tournament_selection(population, objectives)
            
            # Crossover
            if random.random() < self.parameters['crossover_rate']:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = parent1[:], parent2[:]
            
            # Mutation
            child1 = self._mutate(child1)
            child2 = self._mutate(child2)
            
            offspring.append(child1)
            if len(offspring) < len(population):
                offspring.append(child2)
        
        return offspring
        
    def _tournament_selection(self, population: List, objectives: List[Dict[str, float]]) -> List:
        """Select individual using tournament selection."""
        tournament_size = 3
        candidates = random.sample(range(len(population)), tournament_size)
        
        # Find best candidate based on dominance
        best_idx = candidates[0]
        for idx in candidates[1:]:
            if self._dominates(objectives[idx], objectives[best_idx]):
                best_idx = idx
        
        return population[best_idx][:]
        
    def _dominates(self, obj1: Dict[str, float], obj2: Dict[str, float]) -> bool:
        """Check if obj1 dominates obj2 (lower is better for all objectives)."""
        better_in_any = False
        for key in obj1:
            if obj1[key] > obj2[key]:
                return False
            if obj1[key] < obj2[key]:
                better_in_any = True
        return better_in_any
        
    def _crossover(self, parent1: List, parent2: List) -> Tuple[List, List]:
        """Perform crossover between two parents."""
        crossover_point = random.randint(1, len(parent1) - 1)
        
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]
        
        return child1, child2
        
    def _mutate(self, solution: List) -> List:
        """Mutate solution by randomly changing some assignments."""
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                            if self.instructors[id].get("type") == "professor"]
        
        for i in range(len(solution)):
            if random.random() < self.parameters['mutation_rate']:
                responsible_idx, assistant1_idx, assistant2_idx = solution[i]
                
                # Mutate responsible (prefer professors)
                if random.random() < 0.3:  # 30% chance to mutate responsible
                    if professor_indices and random.random() < 0.8:
                        responsible_idx = random.choice(professor_indices)
                    else:
                        responsible_idx = random.randrange(len(instructor_ids))
                
                # Mutate assistants
                if random.random() < 0.3:  # 30% chance to mutate assistant1
                    assistant1_idx = random.randrange(len(instructor_ids))
                    
                if random.random() < 0.3:  # 30% chance to mutate assistant2
                    assistant2_idx = random.randrange(len(instructor_ids))
                
                solution[i] = (responsible_idx, assistant1_idx, assistant2_idx)
        
        return solution
        
    def _fast_non_dominated_sort(self, objectives: List[Dict[str, float]]) -> List[List[int]]:
        """Perform fast non-dominated sorting to identify Pareto fronts."""
        n = len(objectives)
        domination_count = [0] * n
        dominated_solutions = [[] for _ in range(n)]
        fronts = [[]]
        
        # Calculate domination relationships
        for i in range(n):
            for j in range(n):
                if i != j:
                    if self._dominates(objectives[i], objectives[j]):
                        dominated_solutions[i].append(j)
                    elif self._dominates(objectives[j], objectives[i]):
                        domination_count[i] += 1
            
            if domination_count[i] == 0:
                fronts[0].append(i)
        
        # Build fronts
        i = 0
        while fronts[i]:
            next_front = []
            for solution_idx in fronts[i]:
                for dominated_idx in dominated_solutions[solution_idx]:
                    domination_count[dominated_idx] -= 1
                    if domination_count[dominated_idx] == 0:
                        next_front.append(dominated_idx)
            i += 1
            if next_front:
                fronts.append(next_front)
        
        return fronts
        
    def _calculate_crowding_distance(self, objectives: List[Dict[str, float]], fronts: List[List[int]]) -> List[float]:
        """Calculate crowding distance for each solution."""
        n = len(objectives)
        crowding_distance = [0.0] * n
        
        for front in fronts:
            if len(front) <= 2:
                for i in front:
                    crowding_distance[i] = float('inf')
                continue
                
            for objective_key in objectives[0].keys():
                # Sort front by current objective
                sorted_front = sorted(front, key=lambda i: objectives[i][objective_key])
                
                # Set boundary points to infinity
                crowding_distance[sorted_front[0]] = float('inf')
                crowding_distance[sorted_front[-1]] = float('inf')
                
                # Calculate crowding distance
                obj_range = max(objectives[i][objective_key] for i in front) - \
                            min(objectives[i][objective_key] for i in front)
                
                if obj_range > 0:
                    for i in range(1, len(sorted_front) - 1):
                        idx = sorted_front[i]
                        prev_idx = sorted_front[i - 1]
                        next_idx = sorted_front[i + 1]
                        
                        crowding_distance[idx] += (objectives[next_idx][objective_key] - 
                                                  objectives[prev_idx][objective_key]) / obj_range
        
        return crowding_distance
        
    def _select_next_generation(self, population: List, objectives: List[Dict[str, float]], 
                               fronts: List[List[int]], crowding_distances: List[float]) -> Tuple[List, List]:
        """Select next generation based on non-dominated sorting and crowding distance."""
        new_population = []
        new_objectives = []
        
        # Add solutions from each front until we reach population size
        for front in fronts:
            if len(new_population) + len(front) <= self.parameters['population_size']:
                # Add all solutions from this front
                for idx in front:
                    new_population.append(population[idx])
                    new_objectives.append(objectives[idx])
            else:
                # Sort front by crowding distance
                sorted_front = sorted(front, key=lambda i: -crowding_distances[i])
                
                # Add solutions until we reach population size
                remaining = self.parameters['population_size'] - len(new_population)
                for i in range(remaining):
                    idx = sorted_front[i]
                    new_population.append(population[idx])
                    new_objectives.append(objectives[idx])
                break
        
        return new_population, new_objectives
        
    def _find_best_solution(self, objectives: List[Dict[str, float]]) -> int:
        """Find index of best solution based on weighted sum of objectives."""
        best_idx = 0
        best_score = float('inf')
        
        for i, obj in enumerate(objectives):
            # Lower is better for all objectives
            # Weight rule violations most heavily
            score = (obj["rule_violations"] * 100 + 
                    obj["load_imbalance"] * 10 + 
                    obj["classroom_changes"] * 5)
            
            if score < best_score:
                best_score = score
                best_idx = i
        
        return best_idx
        
    def _solution_to_assignments(self, solution: List[Tuple[int, int, int]]) -> Dict[int, Dict]:
        """Convert solution to assignment dictionary."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        
        assignments = {}
        for i, (responsible_idx, assistant1_idx, assistant2_idx) in enumerate(solution):
            project_id = project_ids[i]
            
            assignments[project_id] = {
                "responsible": instructor_ids[responsible_idx],
                "assistant1": instructor_ids[assistant1_idx],
                "assistant2": instructor_ids[assistant2_idx]
            }
        
        return assignments
        
    def _calculate_metrics(self, solution: List[Tuple[int, int, int]]) -> Dict[str, float]:
        """Calculate metrics for the solution."""
        rule_violations = self._calculate_rule_violations(solution)
        load_imbalance = self._calculate_load_imbalance(solution)
        classroom_changes = self._calculate_classroom_changes(solution)
        
        return {
            "rule_violations": rule_violations,
            "load_imbalance": load_imbalance,
            "classroom_changes": classroom_changes,
            "fitness": -(rule_violations * 100 + load_imbalance * 10 + classroom_changes * 5)
        }
