import random
import numpy as np
from typing import Dict, Any, List, Tuple
from app.algorithms.base import BaseAlgorithm

class GreedyAlgorithm(BaseAlgorithm):
    """Greedy algorithm with local search implementation."""
    
    def __init__(
        self,
        projects=None,
        instructors=None,
        local_search_iterations=100,
        neighborhood_size=10,
        rule_weight=100,
        load_weight=10,
        classroom_weight=5
    ):
        super().__init__(projects, instructors, {
            'local_search_iterations': local_search_iterations,
            'neighborhood_size': neighborhood_size,
            'rule_weight': rule_weight,
            'load_weight': load_weight,
            'classroom_weight': classroom_weight
        })
        
    def validate_parameters(self) -> bool:
        """Validate algorithm parameters."""
        if not self.parameters:
            return False
            
        required_params = ['local_search_iterations', 'neighborhood_size', 
                          'rule_weight', 'load_weight', 'classroom_weight']
        for param in required_params:
            if param not in self.parameters:
                return False
                
            # Check numeric parameters are positive
            if self.parameters[param] <= 0:
                return False
                
        return True
        
    def optimize(self) -> Dict[str, Any]:
        """Run greedy algorithm with local search."""
        if not self.projects or not self.instructors:
            return {"error": "No projects or instructors provided"}
            
        # Initial greedy solution
        solution = self._construct_greedy_solution()
        
        # Evaluate initial solution
        fitness = self._evaluate_fitness(solution)
        
        # Local search improvement
        solution, fitness = self._local_search(solution, fitness)
        
        # Convert solution to assignments
        assignments = self._solution_to_assignments(solution)
        
        # Calculate metrics
        metrics = self._calculate_metrics(solution)
        
        return {
            "assignments": assignments,
            "metrics": metrics,
            "fitness": fitness
        }
        
    def _construct_greedy_solution(self) -> List[Tuple[int, int, int]]:
        """Construct initial solution using greedy approach."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        
        # Get professor indices for rule compliance
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                            if self.instructors[id].get("type") == "professor"]
        
        # Track instructor assignments for load balancing
        instructor_counts = [0] * len(instructor_ids)
        
        # Track instructor classrooms for minimizing changes
        instructor_classrooms = {i: set() for i in range(len(instructor_ids))}
        
        solution = []
        
        # Process final projects first (they have stricter constraints)
        project_indices = list(range(len(project_ids)))
        final_projects = []
        interim_projects = []
        
        for i in project_indices:
            project_id = project_ids[i]
            if self.projects[project_id].get("type") == "final":
                final_projects.append(i)
            else:
                interim_projects.append(i)
                
        # Process projects in order: final projects first, then interim projects
        ordered_projects = final_projects + interim_projects
        
        for project_idx in ordered_projects:
            project_id = project_ids[project_idx]
            project = self.projects[project_id]
            
            # Determine classroom for this project
            classroom = project.get("classroom")
            
            # Select responsible (must be professor for final projects)
            if project.get("type") == "final" and professor_indices:
                # For final projects, select professor with lowest load
                professor_loads = [(i, instructor_counts[i]) for i in professor_indices]
                responsible_idx = min(professor_loads, key=lambda x: x[1])[0]
            else:
                # For other projects, prefer professors but consider load
                candidates = []
                for i in range(len(instructor_ids)):
                    # Calculate score based on type and load
                    score = instructor_counts[i]
                    # Prefer professors (lower score)
                    if i in professor_indices:
                        score -= 5
                    # Prefer instructors already in this classroom
                    if classroom and classroom in instructor_classrooms[i]:
                        score -= 3
                    candidates.append((i, score))
                
                responsible_idx = min(candidates, key=lambda x: x[1])[0]
            
            # Select assistants based on load balance and classroom changes
            remaining_instructors = [i for i in range(len(instructor_ids)) if i != responsible_idx]
            
            # For final projects, ensure at least one more professor
            if project.get("type") == "final" and professor_indices:
                remaining_professors = [i for i in professor_indices if i != responsible_idx]
                if remaining_professors:
                    # Select professor with lowest load as first assistant
                    professor_loads = [(i, instructor_counts[i]) for i in remaining_professors]
                    assistant1_idx = min(professor_loads, key=lambda x: x[1])[0]
                    remaining_instructors = [i for i in remaining_instructors if i != assistant1_idx]
                else:
                    # If no more professors, select based on load
                    candidates = [(i, instructor_counts[i]) for i in remaining_instructors]
                    assistant1_idx = min(candidates, key=lambda x: x[1])[0]
                    remaining_instructors.remove(assistant1_idx)
            else:
                # For other projects, select based on load and classroom
                candidates = []
                for i in remaining_instructors:
                    score = instructor_counts[i]
                    # Prefer instructors already in this classroom
                    if classroom and classroom in instructor_classrooms[i]:
                        score -= 3
                    candidates.append((i, score))
                
                assistant1_idx = min(candidates, key=lambda x: x[1])[0]
                remaining_instructors.remove(assistant1_idx)
            
            # Select second assistant based on load
            if remaining_instructors:
                candidates = []
                for i in remaining_instructors:
                    score = instructor_counts[i]
                    # Prefer instructors already in this classroom
                    if classroom and classroom in instructor_classrooms[i]:
                        score -= 3
                    candidates.append((i, score))
                
                assistant2_idx = min(candidates, key=lambda x: x[1])[0]
            else:
                # If no more instructors, reuse assistant1
                assistant2_idx = assistant1_idx
            
            # Update instructor counts and classrooms
            instructor_counts[responsible_idx] += 1
            instructor_counts[assistant1_idx] += 1
            instructor_counts[assistant2_idx] += 1
            
            if classroom:
                instructor_classrooms[responsible_idx].add(classroom)
                instructor_classrooms[assistant1_idx].add(classroom)
                instructor_classrooms[assistant2_idx].add(classroom)
            
            solution.append((responsible_idx, assistant1_idx, assistant2_idx))
        
        return solution
        
    def _local_search(self, solution: List[Tuple[int, int, int]], 
                     initial_fitness: float) -> Tuple[List[Tuple[int, int, int]], float]:
        """Improve solution using local search."""
        best_solution = solution.copy()
        best_fitness = initial_fitness
        
        for iteration in range(self.parameters['local_search_iterations']):
            # Generate neighborhood
            neighbors = self._generate_neighbors(best_solution)
            
            # Evaluate neighbors
            improved = False
            for neighbor in neighbors:
                neighbor_fitness = self._evaluate_fitness(neighbor)
                if neighbor_fitness > best_fitness:
                    best_solution = neighbor
                    best_fitness = neighbor_fitness
                    improved = True
                    break  # First improvement strategy
            
            # If no improvement found in this iteration, try more diverse moves
            if not improved and iteration % 10 == 0:
                # Try a more disruptive move
                neighbor = self._generate_disruptive_move(best_solution)
                neighbor_fitness = self._evaluate_fitness(neighbor)
                if neighbor_fitness > best_fitness:
                    best_solution = neighbor
                    best_fitness = neighbor_fitness
        
        return best_solution, best_fitness
        
    def _generate_neighbors(self, solution: List[Tuple[int, int, int]]) -> List[List[Tuple[int, int, int]]]:
        """Generate neighborhood of current solution."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        neighbors = []
        
        for _ in range(self.parameters['neighborhood_size']):
            # Copy current solution
            neighbor = solution.copy()
            
            # Select random project to modify
            project_idx = random.randrange(len(neighbor))
            project_id = project_ids[project_idx]
            project = self.projects[project_id]
            
            # Determine move type
            move_type = random.choice(["responsible", "assistant1", "assistant2", "swap"])
            
            if move_type == "responsible":
                # Change responsible instructor
                responsible_idx, assistant1_idx, assistant2_idx = neighbor[project_idx]
                
                # For final projects, ensure responsible is professor
                if project.get("type") == "final" and professor_indices:
                    # Select different professor
                    available_professors = [i for i in professor_indices if i != responsible_idx]
                    if available_professors:
                        new_responsible_idx = random.choice(available_professors)
                        neighbor[project_idx] = (new_responsible_idx, assistant1_idx, assistant2_idx)
                else:
                    # Select any instructor
                    new_responsible_idx = random.randrange(len(instructor_ids))
                    neighbor[project_idx] = (new_responsible_idx, assistant1_idx, assistant2_idx)
                    
            elif move_type == "assistant1":
                # Change first assistant
                responsible_idx, assistant1_idx, assistant2_idx = neighbor[project_idx]
                
                # Select any instructor except current responsible
                available = [i for i in range(len(instructor_ids)) if i != responsible_idx]
                if available:
                    new_assistant1_idx = random.choice(available)
                    neighbor[project_idx] = (responsible_idx, new_assistant1_idx, assistant2_idx)
                    
            elif move_type == "assistant2":
                # Change second assistant
                responsible_idx, assistant1_idx, assistant2_idx = neighbor[project_idx]
                
                # Select any instructor except current responsible
                available = [i for i in range(len(instructor_ids)) if i != responsible_idx]
                if available:
                    new_assistant2_idx = random.choice(available)
                    neighbor[project_idx] = (responsible_idx, assistant1_idx, new_assistant2_idx)
                    
            elif move_type == "swap":
                # Swap instructors between two projects
                if len(neighbor) > 1:
                    # Select another project
                    other_idx = random.randrange(len(neighbor))
                    while other_idx == project_idx:
                        other_idx = random.randrange(len(neighbor))
                    
                    # Select positions to swap
                    pos1 = random.randint(0, 2)  # 0=responsible, 1=assistant1, 2=assistant2
                    pos2 = random.randint(0, 2)
                    
                    # Get current assignments
                    assignment1 = list(neighbor[project_idx])
                    assignment2 = list(neighbor[other_idx])
                    
                    # Swap instructors
                    temp = assignment1[pos1]
                    assignment1[pos1] = assignment2[pos2]
                    assignment2[pos2] = temp
                    
                    # Update solution
                    neighbor[project_idx] = tuple(assignment1)
                    neighbor[other_idx] = tuple(assignment2)
            
            neighbors.append(neighbor)
        
        return neighbors
        
    def _generate_disruptive_move(self, solution: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """Generate a more disruptive move for escaping local optima."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        
        # Copy current solution
        neighbor = solution.copy()
        
        # Select multiple projects to modify
        num_projects_to_modify = random.randint(2, max(2, len(neighbor) // 5))
        projects_to_modify = random.sample(range(len(neighbor)), num_projects_to_modify)
        
        for project_idx in projects_to_modify:
            # Completely reassign this project
            project_id = project_ids[project_idx]
            project = self.projects[project_id]
            
            # Get professor indices for rule compliance
            professor_indices = [i for i, id in enumerate(instructor_ids) 
                               if self.instructors[id].get("type") == "professor"]
            
            # Select responsible (must be professor for final projects)
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
                
            neighbor[project_idx] = (responsible_idx, assistant1_idx, assistant2_idx)
        
        return neighbor
        
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
