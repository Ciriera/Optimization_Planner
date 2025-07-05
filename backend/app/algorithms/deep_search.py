import heapq
import time
import numpy as np
from typing import Dict, Any, List, Tuple, Set
from app.algorithms.base import BaseAlgorithm

class DeepSearch(BaseAlgorithm):
    """Deep Search algorithm with beam search and iterative deepening."""
    
    def __init__(
        self,
        projects=None,
        instructors=None,
        beam_width=10,
        max_depth=None,  # If None, will be set to number of projects
        time_limit_seconds=60,
        rule_weight=100,
        load_weight=10,
        classroom_weight=5
    ):
        super().__init__(projects, instructors, {
            'beam_width': beam_width,
            'max_depth': max_depth,
            'time_limit_seconds': time_limit_seconds,
            'rule_weight': rule_weight,
            'load_weight': load_weight,
            'classroom_weight': classroom_weight
        })
        
    def validate_parameters(self) -> bool:
        """Validate algorithm parameters."""
        if not self.parameters:
            return False
            
        required_params = ['beam_width', 'time_limit_seconds',
                          'rule_weight', 'load_weight', 'classroom_weight']
        for param in required_params:
            if param not in self.parameters:
                return False
                
            # Check numeric parameters are positive
            if self.parameters[param] <= 0:
                return False
                
        # max_depth can be None
        if self.parameters.get('max_depth') is not None and self.parameters['max_depth'] <= 0:
            return False
                
        return True
        
    def optimize(self) -> Dict[str, Any]:
        """Run Deep Search optimization algorithm."""
        if not self.projects or not self.instructors:
            return {"error": "No projects or instructors provided"}
            
        # Set max_depth to number of projects if not specified
        if self.parameters.get('max_depth') is None:
            self.parameters['max_depth'] = len(self.projects)
        
        # Get project and instructor IDs
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        
        # Identify professors
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        # Order projects by type (final projects first)
        ordered_projects = []
        for i, project_id in enumerate(project_ids):
            project = self.projects[project_id]
            if project.get("type") == "final":
                ordered_projects.append((i, project_id))
        for i, project_id in enumerate(project_ids):
            project = self.projects[project_id]
            if project.get("type") != "final":
                ordered_projects.append((i, project_id))
        
        # Start timer
        start_time = time.time()
        
        # Iterative deepening
        best_solution = None
        best_fitness = float('-inf')
        
        # Start with a small depth and gradually increase
        for depth in range(1, min(self.parameters['max_depth'] + 1, len(ordered_projects) + 1)):
            # Check if time limit is reached
            if time.time() - start_time > self.parameters['time_limit_seconds']:
                break
                
            # Run beam search with current depth
            solution, fitness = self._beam_search(
                ordered_projects[:depth],
                professor_indices,
                start_time
            )
            
            if solution and (best_solution is None or fitness > best_fitness):
                best_solution = solution
                best_fitness = fitness
        
        # If no solution found or time ran out before completing first depth,
        # generate a heuristic solution
        if best_solution is None:
            best_solution = self._generate_heuristic_solution(ordered_projects)
            best_fitness = self._evaluate_fitness(best_solution)
        
        # Convert best solution to assignments
        assignments = self._solution_to_assignments(best_solution)
        
        # Calculate metrics
        metrics = self._calculate_metrics(best_solution)
        
        return {
            "assignments": assignments,
            "metrics": metrics,
            "fitness": best_fitness
        }
        
    def _beam_search(
        self, 
        ordered_projects: List[Tuple[int, int]], 
        professor_indices: List[int],
        start_time: float
    ) -> Tuple[List[Tuple[int, int, int]], float]:
        """Run beam search to find optimal solution up to a certain depth."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        
        # Initialize beam with empty solution
        beam = [(0, [])]  # (fitness, partial_solution)
        
        # Process each project in order
        for project_idx, project_id in ordered_projects:
            project = self.projects[project_id]
            
            # Check if time limit is reached
            if time.time() - start_time > self.parameters['time_limit_seconds']:
                # Return best solution found so far
                if beam:
                    best_fitness, best_partial = max(beam, key=lambda x: x[0])
                    return best_partial, best_fitness
                return None, float('-inf')
            
            # Generate candidates for next beam
            candidates = []
            
            for fitness, partial_solution in beam:
                # Calculate instructor loads based on partial solution
                instructor_loads = [0] * len(instructor_ids)
                for resp_idx, asst1_idx, asst2_idx in partial_solution:
                    instructor_loads[resp_idx] += 1
                    instructor_loads[asst1_idx] += 1
                    instructor_loads[asst2_idx] += 1
                
                # Generate possible assignments for this project
                possible_assignments = self._generate_possible_assignments(
                    project, 
                    instructor_loads, 
                    professor_indices
                )
                
                # Add each possible assignment to candidates
                for resp_idx, asst1_idx, asst2_idx in possible_assignments:
                    new_solution = partial_solution + [(resp_idx, asst1_idx, asst2_idx)]
                    new_fitness = self._evaluate_partial_fitness(new_solution, len(ordered_projects))
                    candidates.append((new_fitness, new_solution))
            
            # Select top-k candidates for next beam
            beam = heapq.nlargest(self.parameters['beam_width'], candidates, key=lambda x: x[0])
            
            # If beam is empty, no valid solutions found
            if not beam:
                return None, float('-inf')
        
        # Return best solution from final beam
        best_fitness, best_solution = max(beam, key=lambda x: x[0])
        return best_solution, best_fitness
        
    def _generate_possible_assignments(
        self, 
        project: Dict, 
        instructor_loads: List[int], 
        professor_indices: List[int]
    ) -> List[Tuple[int, int, int]]:
        """Generate possible assignments for a project based on constraints."""
        instructor_ids = list(self.instructors.keys())
        possible_assignments = []
        
        # For final projects, responsible must be professor
        if project.get("type") == "final" and professor_indices:
            responsible_candidates = professor_indices
        else:
            responsible_candidates = list(range(len(instructor_ids)))
        
        # Sort responsible candidates by load (prefer less loaded)
        responsible_candidates.sort(key=lambda i: instructor_loads[i])
        
        # Limit number of candidates to consider for efficiency
        max_responsible = min(5, len(responsible_candidates))
        
        for resp_idx in responsible_candidates[:max_responsible]:
            # Update loads for assistants
            temp_loads = instructor_loads.copy()
            temp_loads[resp_idx] += 1
            
            # Candidates for assistant1 (exclude responsible)
            asst1_candidates = [i for i in range(len(instructor_ids)) if i != resp_idx]
            
            # For final projects, prefer professors for assistant1 if responsible is professor
            if project.get("type") == "final" and professor_indices:
                # Sort by professor status first, then by load
                asst1_candidates.sort(key=lambda i: (i not in professor_indices, temp_loads[i]))
            else:
                # Sort by load only
                asst1_candidates.sort(key=lambda i: temp_loads[i])
            
            # Limit number of candidates
            max_asst1 = min(3, len(asst1_candidates))
            
            for asst1_idx in asst1_candidates[:max_asst1]:
                # Update loads for assistant2
                temp_loads2 = temp_loads.copy()
                temp_loads2[asst1_idx] += 1
                
                # Candidates for assistant2 (exclude responsible and assistant1)
                asst2_candidates = [i for i in range(len(instructor_ids)) 
                                  if i != resp_idx and i != asst1_idx]
                
                # For final projects, check if we need another professor
                if project.get("type") == "final" and professor_indices:
                    professor_count = 0
                    if resp_idx in professor_indices:
                        professor_count += 1
                    if asst1_idx in professor_indices:
                        professor_count += 1
                    
                    if professor_count < 2:
                        # Need another professor
                        asst2_candidates = [i for i in asst2_candidates if i in professor_indices]
                        if not asst2_candidates:
                            # No professors available, skip this combination
                            continue
                
                # Sort by load
                asst2_candidates.sort(key=lambda i: temp_loads2[i])
                
                # Limit number of candidates
                max_asst2 = min(2, len(asst2_candidates))
                
                for asst2_idx in asst2_candidates[:max_asst2]:
                    possible_assignments.append((resp_idx, asst1_idx, asst2_idx))
        
        return possible_assignments
        
    def _evaluate_partial_fitness(self, partial_solution: List[Tuple[int, int, int]], total_projects: int) -> float:
        """Evaluate fitness of a partial solution."""
        # Calculate metrics for the partial solution
        rule_violations = self._calculate_rule_violations(partial_solution)
        load_imbalance = self._calculate_load_imbalance(partial_solution)
        classroom_changes = self._calculate_classroom_changes(partial_solution)
        
        # Calculate weighted fitness (negative because lower violations/imbalance/changes is better)
        fitness = -(
            rule_violations * self.parameters['rule_weight'] +
            load_imbalance * self.parameters['load_weight'] +
            classroom_changes * self.parameters['classroom_weight']
        )
        
        # Add heuristic value for remaining projects
        remaining_projects = total_projects - len(partial_solution)
        if remaining_projects > 0:
            # Estimate future fitness based on current average
            if len(partial_solution) > 0:
                avg_fitness_per_project = fitness / len(partial_solution)
                heuristic = avg_fitness_per_project * remaining_projects
                fitness += heuristic
        
        return fitness
        
    def _generate_heuristic_solution(self, ordered_projects: List[Tuple[int, int]]) -> List[Tuple[int, int, int]]:
        """Generate a heuristic solution."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        solution = []
        instructor_counts = [0] * len(instructor_ids)
        
        for project_idx, project_id in ordered_projects:
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
        
    def _evaluate_fitness(self, solution: List[Tuple[int, int, int]]) -> float:
        """Evaluate fitness of a complete solution (higher is better)."""
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
            if i >= len(project_ids):
                break  # Partial solution may be shorter than project_ids
                
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
            if i >= len(project_ids):
                break  # Partial solution may be shorter than project_ids
                
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
            if i >= len(project_ids):
                break  # Partial solution may be shorter than project_ids
                
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
