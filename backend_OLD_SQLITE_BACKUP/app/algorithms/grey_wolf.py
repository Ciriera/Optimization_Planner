import random
import numpy as np
from typing import Dict, Any, List, Tuple
from app.algorithms.base import BaseAlgorithm

class GreyWolfOptimizer(BaseAlgorithm):
    """Grey Wolf Optimizer algorithm implementation."""
    
    def __init__(
        self,
        projects=None,
        instructors=None,
        population_size=30,
        iterations=100,
        rule_weight=100,
        load_weight=10,
        classroom_weight=5
    ):
        super().__init__(projects, instructors, {
            'population_size': population_size,
            'iterations': iterations,
            'rule_weight': rule_weight,
            'load_weight': load_weight,
            'classroom_weight': classroom_weight
        })
        
    def validate_parameters(self) -> bool:
        """Validate algorithm parameters."""
        if not self.parameters:
            return False
            
        required_params = ['population_size', 'iterations', 
                          'rule_weight', 'load_weight', 'classroom_weight']
        for param in required_params:
            if param not in self.parameters:
                return False
                
            # Check numeric parameters are positive
            if self.parameters[param] <= 0:
                return False
                
        return True
    
    def _evaluate_fitness_with_rules(self, wolf):
        """Kurallara uygun fitness hesaplama"""
        fitness = 0.0
        project_ids = list(self.projects.keys())
        
        # 1. Proje türü kuralları kontrolü (büyük bonus)
        for i, (responsible, assistant1, assistant2) in enumerate(wolf):
            project_id = project_ids[i]
            project = self.projects[project_id]
            project_type = project.get("type", "interim")
            
            professor_count = 0
            for instructor_id in [responsible, assistant1, assistant2]:
                if self.instructors[instructor_id]["type"] == "professor":
                    professor_count += 1
            
            if project_type == "final" and professor_count >= 2:
                fitness += 100  # Büyük bonus
            elif project_type == "interim" and professor_count >= 1:
                fitness += 100  # Büyük bonus
            else:
                fitness -= 200  # Büyük ceza
        
        # 2. Yük dengesizliği kontrolü
        instructor_loads = {}
        for assignment in wolf:
            responsible, assistant1, assistant2 = assignment
            for instructor_id in [responsible, assistant1, assistant2]:
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if instructor_loads:
            loads = list(instructor_loads.values())
            max_load = max(loads)
            min_load = min(loads)
            load_balance_penalty = (max_load - min_load) * 10
            fitness -= load_balance_penalty
        
        # 3. Çakışma kontrolü
        timeslot_usage = {}
        conflict_penalty = 0
        for i, (responsible, assistant1, assistant2) in enumerate(wolf):
            for instructor_id in [responsible, assistant1, assistant2]:
                if instructor_id in timeslot_usage:
                    conflict_penalty += 50
                timeslot_usage[instructor_id] = True
        
        fitness -= conflict_penalty
        
        return fitness
        
    def optimize(self) -> Dict[str, Any]:
        """Run Grey Wolf Optimizer algorithm - Kurallara uygun"""
        if not self.projects or not self.instructors:
            return {"error": "No projects or instructors provided"}
        
        # Her çalıştırmada farklı sonuç için random seed
        import time
        random.seed(int(time.time() * 1000) % 2**32)
        np.random.seed(int(time.time() * 1000) % 2**32)
            
        # Initialize wolf pack (population)
        wolves = self._initialize_population()
        
        # Evaluate wolves with rules
        fitness_values = [self._evaluate_fitness_with_rules(w) for w in wolves]
        
        # Sort wolves based on fitness - Alpha, Beta, Delta hierarchy
        sorted_indices = np.argsort([-f for f in fitness_values])  # Descending order
        wolves = [wolves[i] for i in sorted_indices]
        fitness_values = [fitness_values[i] for i in sorted_indices]
        
        # Main optimization loop - Grey Wolf prensiplerine göre
        for iteration in range(self.parameters['iterations']):
            # Update a, a decreases linearly from 2 to 0 (Grey Wolf prensibi)
            a = 2 - iteration * (2 / self.parameters['iterations'])
            
            # Update each wolf's position - Grey Wolf hierarchy
            for i in range(1, self.parameters['population_size']):
                # Update wolf position based on alpha, beta, and delta wolves
                if i >= 3:  # Omega wolves follow alpha, beta, delta
                    wolves[i] = self._update_wolf_position(
                        wolves[i], wolves[0], wolves[1], wolves[2], a
                    )
                elif i == 2:  # Delta wolf follows alpha, beta
                    wolves[i] = self._update_wolf_position(
                        wolves[i], wolves[0], wolves[1], wolves[1], a
                    )
                elif i == 1:  # Beta wolf follows alpha
                    wolves[i] = self._update_wolf_position(
                        wolves[i], wolves[0], wolves[0], wolves[0], a
                    )
                
                # Re-evaluate wolf with rules
                fitness_values[i] = self._evaluate_fitness_with_rules(wolves[i])
            
            # Re-sort wolves based on updated fitness - hierarchy maintained
            sorted_indices = np.argsort([-f for f in fitness_values])
            wolves = [wolves[i] for i in sorted_indices]
            fitness_values = [fitness_values[i] for i in sorted_indices]
        
        # Alpha wolf is the best solution
        best_solution = wolves[0]
        best_fitness = fitness_values[0]
        
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
        """Initialize population of wolves."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        wolves = []
        
        for _ in range(self.parameters['population_size']):
            wolf = []
            
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
                
                wolf.append((responsible_idx, assistant1_idx, assistant2_idx))
            
            # Add some randomization to create diversity in the population
            if random.random() < 0.5:  # 50% chance to randomize
                self._randomize_wolf(wolf)
            
            wolves.append(wolf)
        
        return wolves
        
    def _randomize_wolf(self, wolf: List[Tuple[int, int, int]]) -> None:
        """Add some randomization to a wolf's position."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        # Select a subset of projects to randomize
        num_to_randomize = random.randint(1, max(1, len(wolf) // 3))
        projects_to_randomize = random.sample(range(len(wolf)), num_to_randomize)
        
        for project_idx in projects_to_randomize:
            project_id = project_ids[project_idx]
            project = self.projects[project_id]
            
            # For final projects, ensure responsible is professor
            if project.get("type") == "final" and professor_indices:
                responsible_idx = random.choice(professor_indices)
            else:
                responsible_idx = random.randrange(len(instructor_ids))
            
            # Select assistants
            available = [i for i in range(len(instructor_ids)) if i != responsible_idx]
            if available:
                if len(available) >= 2:
                    assistant1_idx, assistant2_idx = random.sample(available, 2)
                else:
                    assistant1_idx = available[0]
                    assistant2_idx = available[0]
            else:
                assistant1_idx = responsible_idx
                assistant2_idx = responsible_idx
            
            wolf[project_idx] = (responsible_idx, assistant1_idx, assistant2_idx)
        
    def _update_wolf_position(
        self, 
        current_wolf: List[Tuple[int, int, int]], 
        alpha_wolf: List[Tuple[int, int, int]], 
        beta_wolf: List[Tuple[int, int, int]], 
        delta_wolf: List[Tuple[int, int, int]], 
        a: float
    ) -> List[Tuple[int, int, int]]:
        """Update wolf position based on alpha, beta, and delta wolves."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        new_wolf = []
        
        for i in range(len(current_wolf)):
            project_id = project_ids[i]
            project = self.projects[project_id]
            
            # Get current positions
            curr_resp, curr_asst1, curr_asst2 = current_wolf[i]
            alpha_resp, alpha_asst1, alpha_asst2 = alpha_wolf[i]
            beta_resp, beta_asst1, beta_asst2 = beta_wolf[i]
            delta_resp, delta_asst1, delta_asst2 = delta_wolf[i]
            
            # Calculate new position for responsible instructor
            new_resp = self._calculate_new_position(
                curr_resp, alpha_resp, beta_resp, delta_resp, a
            )
            
            # For final projects, ensure responsible is professor
            if project.get("type") == "final" and professor_indices:
                if new_resp not in professor_indices:
                    # Find closest professor
                    closest_prof = min(professor_indices, key=lambda p: abs(p - new_resp))
                    new_resp = closest_prof
            
            # Calculate new position for assistant1
            new_asst1 = self._calculate_new_position(
                curr_asst1, alpha_asst1, beta_asst1, delta_asst1, a
            )
            
            # Calculate new position for assistant2
            new_asst2 = self._calculate_new_position(
                curr_asst2, alpha_asst2, beta_asst2, delta_asst2, a
            )
            
            # Ensure assistants are different from responsible if possible
            if new_asst1 == new_resp:
                available = [i for i in range(len(instructor_ids)) if i != new_resp]
                if available:
                    new_asst1 = random.choice(available)
            
            if new_asst2 == new_resp or new_asst2 == new_asst1:
                available = [i for i in range(len(instructor_ids)) if i != new_resp and i != new_asst1]
                if available:
                    new_asst2 = random.choice(available)
            
            new_wolf.append((new_resp, new_asst1, new_asst2))
        
        return new_wolf
        
    def _calculate_new_position(
        self, 
        current_pos: int, 
        alpha_pos: int, 
        beta_pos: int, 
        delta_pos: int, 
        a: float
    ) -> int:
        """Calculate new position for a single instructor index."""
        instructor_ids = list(self.instructors.keys())
        
        # Calculate A and C coefficients
        A1 = 2 * a * random.random() - a
        A2 = 2 * a * random.random() - a
        A3 = 2 * a * random.random() - a
        
        C1 = 2 * random.random()
        C2 = 2 * random.random()
        C3 = 2 * random.random()
        
        # Calculate D vectors (distance)
        D_alpha = abs(C1 * alpha_pos - current_pos)
        D_beta = abs(C2 * beta_pos - current_pos)
        D_delta = abs(C3 * delta_pos - current_pos)
        
        # Calculate X vectors (position updates)
        X1 = alpha_pos - A1 * D_alpha
        X2 = beta_pos - A2 * D_beta
        X3 = delta_pos - A3 * D_delta
        
        # Calculate new position as average of X vectors
        new_pos_float = (X1 + X2 + X3) / 3
        
        # Round to nearest integer and ensure within bounds
        new_pos = round(new_pos_float)
        new_pos = max(0, min(new_pos, len(instructor_ids) - 1))
        
        return new_pos
        
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
