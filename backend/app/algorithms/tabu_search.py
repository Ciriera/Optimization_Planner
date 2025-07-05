import random
import numpy as np
from typing import Dict, Any, List, Tuple, Set
from collections import deque
from app.algorithms.base import BaseAlgorithm

class TabuSearchAlgorithm(BaseAlgorithm):
    """Tabu Search algorithm implementation."""
    
    def __init__(
        self,
        projects=None,
        instructors=None,
        iterations=100,
        tabu_tenure=10,
        neighborhood_size=20,
        aspiration_factor=1.1,
        rule_weight=100,
        load_weight=10,
        classroom_weight=5
    ):
        super().__init__(projects, instructors, {
            'iterations': iterations,
            'tabu_tenure': tabu_tenure,
            'neighborhood_size': neighborhood_size,
            'aspiration_factor': aspiration_factor,
            'rule_weight': rule_weight,
            'load_weight': load_weight,
            'classroom_weight': classroom_weight
        })
        
    def validate_parameters(self) -> bool:
        """Validate algorithm parameters."""
        if not self.parameters:
            return False
            
        required_params = ['iterations', 'tabu_tenure', 'neighborhood_size', 
                          'aspiration_factor', 'rule_weight', 'load_weight', 'classroom_weight']
        for param in required_params:
            if param not in self.parameters:
                return False
                
            # Check numeric parameters are positive
            if self.parameters[param] <= 0:
                return False
                
        return True
        
    def optimize(self) -> Dict[str, Any]:
        """Run Tabu Search optimization algorithm."""
        if not self.projects or not self.instructors:
            return {"error": "No projects or instructors provided"}
            
        # Generate initial solution
        current_solution = self._generate_initial_solution()
        current_fitness = self._evaluate_fitness(current_solution)
        
        # Best solution found so far
        best_solution = current_solution.copy()
        best_fitness = current_fitness
        
        # Initialize tabu list
        tabu_list = deque(maxlen=self.parameters['tabu_tenure'])
        
        # Track iterations without improvement for diversification
        stagnation_counter = 0
        
        # Main tabu search loop
        for iteration in range(self.parameters['iterations']):
            # Generate neighborhood
            neighbors, move_keys = self._generate_neighborhood(current_solution)
            
            # Find best non-tabu neighbor
            best_neighbor = None
            best_neighbor_fitness = float('-inf')
            best_move_key = None
            
            for i, neighbor in enumerate(neighbors):
                move_key = move_keys[i]
                fitness = self._evaluate_fitness(neighbor)
                
                # Check if move is tabu
                is_tabu = move_key in tabu_list
                
                # Apply aspiration criterion - accept tabu move if it's better than the best solution
                if is_tabu and fitness <= best_fitness * self.parameters['aspiration_factor']:
                    continue
                
                # Update best neighbor
                if best_neighbor is None or fitness > best_neighbor_fitness:
                    best_neighbor = neighbor
                    best_neighbor_fitness = fitness
                    best_move_key = move_key
            
            # If no valid move found, perform diversification
            if best_neighbor is None:
                current_solution = self._diversify(current_solution)
                current_fitness = self._evaluate_fitness(current_solution)
                stagnation_counter = 0
                continue
            
            # Update current solution
            current_solution = best_neighbor
            current_fitness = best_neighbor_fitness
            
            # Add move to tabu list
            tabu_list.append(best_move_key)
            
            # Update best solution if improved
            if current_fitness > best_fitness:
                best_solution = current_solution.copy()
                best_fitness = current_fitness
                stagnation_counter = 0
            else:
                stagnation_counter += 1
            
            # Diversification strategy if no improvement for a while
            if stagnation_counter >= 20:
                current_solution = self._diversify(best_solution)
                current_fitness = self._evaluate_fitness(current_solution)
                stagnation_counter = 0
        
        # Convert best solution to assignments
        assignments = self._solution_to_assignments(best_solution)
        
        # Calculate metrics
        metrics = self._calculate_metrics(best_solution)
        
        return {
            "assignments": assignments,
            "metrics": metrics,
            "fitness": best_fitness
        }
        
    def _generate_initial_solution(self) -> List[Tuple[int, int, int]]:
        """Generate initial solution with greedy approach."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        
        # Get professor indices for rule compliance
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                            if self.instructors[id].get("type") == "professor"]
        
        # Track instructor assignments for load balancing
        instructor_counts = [0] * len(instructor_ids)
        
        solution = []
        
        for project_idx in range(len(project_ids)):
            project_id = project_ids[project_idx]
            project = self.projects[project_id]
            
            # For final projects, ensure responsible is professor
            if project.get("type") == "final" and professor_indices:
                # Select professor with lowest load
                professor_loads = [(i, instructor_counts[i]) for i in professor_indices]
                responsible_idx = min(professor_loads, key=lambda x: x[1])[0]
                
                # For final projects, ensure at least one more professor if possible
                remaining_professors = [i for i in professor_indices if i != responsible_idx]
                
                if remaining_professors:
                    # Select professor with lowest load as first assistant
                    professor_loads = [(i, instructor_counts[i]) for i in remaining_professors]
                    assistant1_idx = min(professor_loads, key=lambda x: x[1])[0]
                    
                    # Select any instructor with lowest load as second assistant
                    remaining_instructors = [i for i in range(len(instructor_ids)) 
                                           if i != responsible_idx and i != assistant1_idx]
                    if remaining_instructors:
                        instructor_loads = [(i, instructor_counts[i]) for i in remaining_instructors]
                        assistant2_idx = min(instructor_loads, key=lambda x: x[1])[0]
                    else:
                        assistant2_idx = assistant1_idx
                else:
                    # If not enough professors, select instructors with lowest load
                    remaining_instructors = [i for i in range(len(instructor_ids)) if i != responsible_idx]
                    if len(remaining_instructors) >= 2:
                        instructor_loads = [(i, instructor_counts[i]) for i in remaining_instructors]
                        instructor_loads.sort(key=lambda x: x[1])
                        assistant1_idx = instructor_loads[0][0]
                        assistant2_idx = instructor_loads[1][0]
                    elif len(remaining_instructors) == 1:
                        assistant1_idx = remaining_instructors[0]
                        assistant2_idx = assistant1_idx
                    else:
                        assistant1_idx = responsible_idx
                        assistant2_idx = responsible_idx
            else:
                # For other projects, prefer professors but balance load
                instructor_loads = [(i, instructor_counts[i]) for i in range(len(instructor_ids))]
                # Sort by load, then prefer professors for responsible
                instructor_loads.sort(key=lambda x: (x[1], 0 if x[0] in professor_indices else 1))
                
                responsible_idx = instructor_loads[0][0]
                
                # Select assistants with lowest load
                remaining_instructors = [i for i, _ in instructor_loads if i != responsible_idx]
                if len(remaining_instructors) >= 2:
                    assistant1_idx = remaining_instructors[0]
                    assistant2_idx = remaining_instructors[1]
                elif len(remaining_instructors) == 1:
                    assistant1_idx = remaining_instructors[0]
                    assistant2_idx = assistant1_idx
                else:
                    assistant1_idx = responsible_idx
                    assistant2_idx = responsible_idx
            
            # Update instructor counts
            instructor_counts[responsible_idx] += 1
            instructor_counts[assistant1_idx] += 1
            instructor_counts[assistant2_idx] += 1
            
            solution.append((responsible_idx, assistant1_idx, assistant2_idx))
        
        return solution
        
    def _generate_neighborhood(self, solution: List[Tuple[int, int, int]]) -> Tuple[List[List[Tuple[int, int, int]]], List[str]]:
        """Generate neighborhood of current solution with move keys for tabu list."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        neighbors = []
        move_keys = []
        
        # Generate different types of moves
        move_types = ["swap", "replace", "reassign"]
        
        for _ in range(self.parameters['neighborhood_size']):
            # Copy current solution
            neighbor = solution.copy()
            
            # Select move type
            move_type = random.choice(move_types)
            
            if move_type == "swap":
                # Swap instructors between two projects
                if len(neighbor) > 1:
                    # Select two different projects
                    project1_idx = random.randrange(len(neighbor))
                    project2_idx = random.randrange(len(neighbor))
                    while project2_idx == project1_idx:
                        project2_idx = random.randrange(len(neighbor))
                    
                    # Select positions to swap
                    pos1 = random.randint(0, 2)  # 0=responsible, 1=assistant1, 2=assistant2
                    pos2 = random.randint(0, 2)
                    
                    # Get current assignments
                    assignment1 = list(neighbor[project1_idx])
                    assignment2 = list(neighbor[project2_idx])
                    
                    # Check if swap would violate constraints for final projects
                    project1_id = project_ids[project1_idx]
                    project2_id = project_ids[project2_idx]
                    
                    can_swap = True
                    
                    # For final projects, responsible must be professor
                    if pos1 == 0 and self.projects[project1_id].get("type") == "final":
                        if assignment2[pos2] not in professor_indices:
                            can_swap = False
                            
                    if pos2 == 0 and self.projects[project2_id].get("type") == "final":
                        if assignment1[pos1] not in professor_indices:
                            can_swap = False
                    
                    if can_swap:
                        # Swap instructors
                        temp = assignment1[pos1]
                        assignment1[pos1] = assignment2[pos2]
                        assignment2[pos2] = temp
                        
                        # Update solution
                        neighbor[project1_idx] = tuple(assignment1)
                        neighbor[project2_idx] = tuple(assignment2)
                        
                        # Create move key
                        move_key = f"swap:{project1_idx}:{pos1}:{project2_idx}:{pos2}"
                        
                        neighbors.append(neighbor)
                        move_keys.append(move_key)
                        continue
            
            elif move_type == "replace":
                # Replace an instructor in a project
                project_idx = random.randrange(len(neighbor))
                project_id = project_ids[project_idx]
                project = self.projects[project_id]
                
                # Select position to replace
                pos = random.randint(0, 2)
                
                # Get current assignment
                assignment = list(neighbor[project_idx])
                old_instructor = assignment[pos]
                
                # Select new instructor
                if pos == 0 and project.get("type") == "final":
                    # For responsible in final projects, must be professor
                    if professor_indices:
                        available_professors = [i for i in professor_indices if i != old_instructor]
                        if available_professors:
                            new_instructor = random.choice(available_professors)
                            assignment[pos] = new_instructor
                            
                            # Update solution
                            neighbor[project_idx] = tuple(assignment)
                            
                            # Create move key
                            move_key = f"replace:{project_idx}:{pos}:{old_instructor}:{new_instructor}"
                            
                            neighbors.append(neighbor)
                            move_keys.append(move_key)
                            continue
                else:
                    # For other positions, can be any instructor
                    available_instructors = [i for i in range(len(instructor_ids)) if i != old_instructor]
                    if available_instructors:
                        new_instructor = random.choice(available_instructors)
                        assignment[pos] = new_instructor
                        
                        # Update solution
                        neighbor[project_idx] = tuple(assignment)
                        
                        # Create move key
                        move_key = f"replace:{project_idx}:{pos}:{old_instructor}:{new_instructor}"
                        
                        neighbors.append(neighbor)
                        move_keys.append(move_key)
                        continue
            
            elif move_type == "reassign":
                # Completely reassign a project
                project_idx = random.randrange(len(neighbor))
                project_id = project_ids[project_idx]
                project = self.projects[project_id]
                
                old_assignment = neighbor[project_idx]
                
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
                    
                new_assignment = (responsible_idx, assistant1_idx, assistant2_idx)
                
                # Check if this actually changes the assignment
                if new_assignment != old_assignment:
                    neighbor[project_idx] = new_assignment
                    
                    # Create move key
                    move_key = f"reassign:{project_idx}:{old_assignment[0]}:{old_assignment[1]}:{old_assignment[2]}:{new_assignment[0]}:{new_assignment[1]}:{new_assignment[2]}"
                    
                    neighbors.append(neighbor)
                    move_keys.append(move_key)
                    continue
        
        # If we couldn't generate enough neighbors, fill with random solutions
        while len(neighbors) < self.parameters['neighborhood_size']:
            random_solution = self._generate_random_solution()
            move_key = f"random:{random.randint(0, 1000000)}"
            neighbors.append(random_solution)
            move_keys.append(move_key)
        
        return neighbors, move_keys
        
    def _generate_random_solution(self) -> List[Tuple[int, int, int]]:
        """Generate a random solution that respects basic constraints."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        solution = []
        
        for project_idx in range(len(project_ids)):
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
                
            solution.append((responsible_idx, assistant1_idx, assistant2_idx))
        
        return solution
        
    def _diversify(self, solution: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """Diversify the solution to escape local optima."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        
        # Copy current solution
        new_solution = solution.copy()
        
        # Select a subset of projects to reassign
        num_to_reassign = max(1, len(new_solution) // 4)
        projects_to_reassign = random.sample(range(len(new_solution)), num_to_reassign)
        
        for project_idx in projects_to_reassign:
            # Generate a new random assignment for this project
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
                
            new_solution[project_idx] = (responsible_idx, assistant1_idx, assistant2_idx)
        
        return new_solution
        
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
