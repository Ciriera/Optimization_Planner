import random
import numpy as np
import math
from typing import Dict, Any, List, Tuple
from app.algorithms.base import BaseAlgorithm

class FireflyAlgorithm(BaseAlgorithm):
    """Firefly Algorithm implementation."""
    
    def __init__(
        self,
        projects=None,
        instructors=None,
        population_size=30,
        iterations=100,
        alpha=0.5,  # Randomization parameter
        beta0=1.0,  # Attractiveness at distance=0
        gamma=0.1,  # Light absorption coefficient
        rule_weight=100,
        load_weight=10,
        classroom_weight=5
    ):
        super().__init__(projects, instructors, {
            'population_size': population_size,
            'iterations': iterations,
            'alpha': alpha,
            'beta0': beta0,
            'gamma': gamma,
            'rule_weight': rule_weight,
            'load_weight': load_weight,
            'classroom_weight': classroom_weight
        })
        
    def validate_parameters(self) -> bool:
        """Validate algorithm parameters."""
        if not self.parameters:
            return False
            
        required_params = ['population_size', 'iterations', 'alpha', 'beta0', 'gamma',
                          'rule_weight', 'load_weight', 'classroom_weight']
        for param in required_params:
            if param not in self.parameters:
                return False
                
            # Check numeric parameters are positive
            if self.parameters[param] <= 0:
                return False
                
        return True
        
    def optimize(self) -> Dict[str, Any]:
        """Run Firefly Algorithm optimization."""
        if not self.projects or not self.instructors:
            return {"error": "No projects or instructors provided"}
            
        # Initialize population of fireflies
        fireflies = self._initialize_population()
        
        # Evaluate fireflies
        fitness_values = [self._evaluate_fitness(f) for f in fireflies]
        
        # Main optimization loop
        for iteration in range(self.parameters['iterations']):
            # Reduce alpha over iterations (optional)
            alpha = self.parameters['alpha'] * (0.97 ** iteration)
            
            # Move fireflies
            for i in range(self.parameters['population_size']):
                for j in range(self.parameters['population_size']):
                    # Firefly j is brighter than firefly i, move i towards j
                    if fitness_values[j] > fitness_values[i]:
                        fireflies[i] = self._move_firefly(
                            fireflies[i], 
                            fireflies[j], 
                            alpha, 
                            self.parameters['beta0'], 
                            self.parameters['gamma']
                        )
                        
                        # Re-evaluate moved firefly
                        fitness_values[i] = self._evaluate_fitness(fireflies[i])
        
        # Find best solution
        best_idx = np.argmax(fitness_values)
        best_solution = fireflies[best_idx]
        best_fitness = fitness_values[best_idx]
        
        # Convert best solution to assignments
        assignments = self._solution_to_assignments(best_solution)
        
        # Calculate metrics
        metrics = self._calculate_metrics(best_solution)
        
        return {
            "assignments": assignments,
            "metrics": metrics,
            "fitness": best_fitness
        }
        
    def _initialize_population(self) -> List[List[Tuple[int, int, int]]]:
        """Initialize population of fireflies."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        fireflies = []
        
        for _ in range(self.parameters['population_size']):
            firefly = []
            
            # Track instructor assignments for load balancing
            instructor_counts = [0] * len(instructor_ids)
            
            for project_idx in range(len(project_ids)):
                project_id = project_ids[project_idx]
                project = self.projects[project_id]
                
                # For final projects, ensure responsible is professor
                if project.get("type") == "final" and professor_indices:
                    # Select professor with lowest load
                    professor_loads = [(i, instructor_counts[i]) for i in professor_indices]
                    responsible_idx = min(professor_loads, key=lambda x: x[1])[0]
                else:
                    # For other projects, select any instructor with preference for professors
                    candidates = []
                    for i in range(len(instructor_ids)):
                        # Calculate score based on type and load
                        score = instructor_counts[i]
                        # Prefer professors (lower score)
                        if i in professor_indices:
                            score -= 5
                        candidates.append((i, score))
                    
                    responsible_idx = min(candidates, key=lambda x: x[1])[0]
                
                # Select assistants based on load balance
                remaining_instructors = [i for i in range(len(instructor_ids)) if i != responsible_idx]
                
                # For final projects, ensure at least one more professor if possible
                if project.get("type") == "final" and professor_indices:
                    remaining_professors = [i for i in professor_indices if i != responsible_idx]
                    if remaining_professors:
                        # Select professor with lowest load as first assistant
                        professor_loads = [(i, instructor_counts[i]) for i in remaining_professors]
                        assistant1_idx = min(professor_loads, key=lambda x: x[1])[0]
                        remaining_instructors = [i for i in remaining_instructors if i != assistant1_idx]
                    else:
                        # If no more professors, select based on load
                        if remaining_instructors:
                            instructor_loads = [(i, instructor_counts[i]) for i in remaining_instructors]
                            assistant1_idx = min(instructor_loads, key=lambda x: x[1])[0]
                            remaining_instructors.remove(assistant1_idx)
                        else:
                            assistant1_idx = responsible_idx
                else:
                    # For other projects, select based on load
                    if remaining_instructors:
                        instructor_loads = [(i, instructor_counts[i]) for i in remaining_instructors]
                        assistant1_idx = min(instructor_loads, key=lambda x: x[1])[0]
                        remaining_instructors.remove(assistant1_idx)
                    else:
                        assistant1_idx = responsible_idx
                
                # Select second assistant based on load
                if remaining_instructors:
                    instructor_loads = [(i, instructor_counts[i]) for i in remaining_instructors]
                    assistant2_idx = min(instructor_loads, key=lambda x: x[1])[0]
                else:
                    assistant2_idx = assistant1_idx
                
                # Update instructor counts
                instructor_counts[responsible_idx] += 1
                instructor_counts[assistant1_idx] += 1
                instructor_counts[assistant2_idx] += 1
                
                firefly.append((responsible_idx, assistant1_idx, assistant2_idx))
            
            fireflies.append(firefly)
        
        return fireflies
        
    def _calculate_distance(self, firefly1: List[Tuple[int, int, int]], firefly2: List[Tuple[int, int, int]]) -> float:
        """Calculate distance between two fireflies."""
        distance = 0
        
        for i in range(len(firefly1)):
            resp1, asst1_1, asst2_1 = firefly1[i]
            resp2, asst1_2, asst2_2 = firefly2[i]
            
            # Calculate Euclidean distance between assignments
            # For each position, calculate squared difference
            d_resp = (resp1 - resp2) ** 2
            d_asst1 = (asst1_1 - asst1_2) ** 2
            d_asst2 = (asst2_1 - asst2_2) ** 2
            
            # Add to total distance
            distance += d_resp + d_asst1 + d_asst2
        
        return math.sqrt(distance)
        
    def _move_firefly(
        self, 
        firefly1: List[Tuple[int, int, int]], 
        firefly2: List[Tuple[int, int, int]], 
        alpha: float, 
        beta0: float, 
        gamma: float
    ) -> List[Tuple[int, int, int]]:
        """Move firefly1 towards firefly2 based on attractiveness."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        # Calculate distance between fireflies
        distance = self._calculate_distance(firefly1, firefly2)
        
        # Calculate attractiveness
        beta = beta0 * math.exp(-gamma * distance ** 2)
        
        new_firefly = []
        
        for i in range(len(firefly1)):
            project_id = project_ids[i]
            project = self.projects[project_id]
            
            resp1, asst1_1, asst2_1 = firefly1[i]
            resp2, asst1_2, asst2_2 = firefly2[i]
            
            # Calculate new position components
            # x_i = x_i + beta * (x_j - x_i) + alpha * epsilon
            # Where epsilon is a random vector
            
            # For responsible
            new_resp_float = resp1 + beta * (resp2 - resp1) + alpha * random.uniform(-0.5, 0.5)
            # Round to nearest integer and ensure within bounds
            new_resp = round(new_resp_float)
            new_resp = max(0, min(new_resp, len(instructor_ids) - 1))
            
            # For final projects, ensure responsible is professor
            if project.get("type") == "final" and professor_indices:
                if new_resp not in professor_indices:
                    # Find closest professor
                    closest_prof = min(professor_indices, key=lambda p: abs(p - new_resp))
                    new_resp = closest_prof
            
            # For assistant1
            new_asst1_float = asst1_1 + beta * (asst1_2 - asst1_1) + alpha * random.uniform(-0.5, 0.5)
            new_asst1 = round(new_asst1_float)
            new_asst1 = max(0, min(new_asst1, len(instructor_ids) - 1))
            
            # For assistant2
            new_asst2_float = asst2_1 + beta * (asst2_2 - asst2_1) + alpha * random.uniform(-0.5, 0.5)
            new_asst2 = round(new_asst2_float)
            new_asst2 = max(0, min(new_asst2, len(instructor_ids) - 1))
            
            # Ensure assistants are different from responsible if possible
            if new_asst1 == new_resp:
                available = [i for i in range(len(instructor_ids)) if i != new_resp]
                if available:
                    new_asst1 = random.choice(available)
            
            if new_asst2 == new_resp or new_asst2 == new_asst1:
                available = [i for i in range(len(instructor_ids)) if i != new_resp and i != new_asst1]
                if available:
                    new_asst2 = random.choice(available)
            
            new_firefly.append((new_resp, new_asst1, new_asst2))
        
        return new_firefly
        
    def _evaluate_fitness(self, solution: List[Tuple[int, int, int]]) -> float:
        """Evaluate fitness of a solution (higher is better)."""
        rule_violations = self._calculate_rule_violations(solution)
        load_imbalance = self._calculate_load_imbalance(solution)
        classroom_changes = self._calculate_classroom_changes(solution)
        
        # Calculate weighted fitness (negative because lower violations/imbalance/changes is better)
        fitness = -(
            rule_violations * self.parameters['rule_weight'] +
            load_imbalance * self.parameters['load_weight'] +
            classroom_changes * self.parameters['classroom_weight']
        )
        
        return fitness
        
    def _calculate_rule_violations(self, solution: List[Tuple[int, int, int]]) -> float:
        """Calculate number of rule violations in a solution."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        violations = 0
        
        for i, (responsible_idx, assistant1_idx, assistant2_idx) in enumerate(solution):
            project_id = project_ids[i]
            project = self.projects[project_id]
            
            responsible_id = instructor_ids[responsible_idx]
            
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
            "fitness": -(rule_violations * self.parameters['rule_weight'] + 
                       load_imbalance * self.parameters['load_weight'] + 
                       classroom_changes * self.parameters['classroom_weight'])
        }
