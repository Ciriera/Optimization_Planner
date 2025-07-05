import numpy as np
from typing import Dict, Any, List, Tuple
from app.algorithms.base import BaseAlgorithm

try:
    from ortools.sat.python import cp_model
except ImportError:
    cp_model = None

class CPSATSolver(BaseAlgorithm):
    """CP-SAT constraint programming solver implementation."""
    
    def __init__(
        self,
        projects=None,
        instructors=None,
        time_limit_seconds=60,
        num_search_workers=4,
        rule_weight=100,
        load_weight=10,
        classroom_weight=5
    ):
        super().__init__(projects, instructors, {
            'time_limit_seconds': time_limit_seconds,
            'num_search_workers': num_search_workers,
            'rule_weight': rule_weight,
            'load_weight': load_weight,
            'classroom_weight': classroom_weight
        })
        
    def validate_parameters(self) -> bool:
        """Validate algorithm parameters."""
        if not self.parameters:
            return False
            
        required_params = ['time_limit_seconds', 'num_search_workers',
                          'rule_weight', 'load_weight', 'classroom_weight']
        for param in required_params:
            if param not in self.parameters:
                return False
                
            # Check numeric parameters are positive
            if self.parameters[param] <= 0:
                return False
                
        # Check if OR-Tools CP-SAT is available
        if cp_model is None:
            return False
                
        return True
        
    def optimize(self) -> Dict[str, Any]:
        """Run CP-SAT optimization algorithm."""
        if not self.projects or not self.instructors:
            return {"error": "No projects or instructors provided"}
            
        if cp_model is None:
            return {"error": "OR-Tools CP-SAT solver not available. Please install ortools package."}
        
        # Create CP-SAT model
        model = cp_model.CpModel()
        
        # Get project and instructor IDs
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        
        # Identify professors
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        # Get classrooms
        all_classrooms = set()
        for project_id, project in self.projects.items():
            if project.get("classroom"):
                all_classrooms.add(project.get("classroom"))
        classroom_ids = list(all_classrooms)
        
        # Create variables
        # For each project, we need to assign responsible, assistant1, and assistant2
        assignments = {}
        for p, project_id in enumerate(project_ids):
            assignments[p] = {
                'responsible': model.NewIntVar(0, len(instructor_ids) - 1, f'responsible_{p}'),
                'assistant1': model.NewIntVar(0, len(instructor_ids) - 1, f'assistant1_{p}'),
                'assistant2': model.NewIntVar(0, len(instructor_ids) - 1, f'assistant2_{p}')
            }
        
        # Create instructor load variables
        instructor_loads = {}
        for i in range(len(instructor_ids)):
            instructor_loads[i] = model.NewIntVar(0, len(project_ids) * 3, f'load_{i}')
        
        # Create classroom assignment variables
        instructor_in_classroom = {}
        for i in range(len(instructor_ids)):
            for c, classroom in enumerate(classroom_ids):
                instructor_in_classroom[(i, c)] = model.NewBoolVar(f'instr_{i}_in_class_{c}')
        
        # Create classroom change variables
        classroom_changes = {}
        for i in range(len(instructor_ids)):
            classroom_changes[i] = model.NewIntVar(0, len(classroom_ids), f'changes_{i}')
        
        # Add constraints
        
        # 1. Constraint: For final projects, responsible must be professor
        for p, project_id in enumerate(project_ids):
            project = self.projects[project_id]
            if project.get("type") == "final":
                # Create a list of allowed values (professor indices)
                model.AddAllowedAssignments([assignments[p]['responsible']], [(idx,) for idx in professor_indices])
        
        # 2. Constraint: For final projects, at least 2 professors must be assigned
        for p, project_id in enumerate(project_ids):
            project = self.projects[project_id]
            if project.get("type") == "final":
                # Create variables to track if each position is filled by a professor
                is_resp_prof = model.NewBoolVar(f'is_resp_prof_{p}')
                is_asst1_prof = model.NewBoolVar(f'is_asst1_prof_{p}')
                is_asst2_prof = model.NewBoolVar(f'is_asst2_prof_{p}')
                
                # Add constraints to set these variables
                for prof_idx in professor_indices:
                    model.Add(assignments[p]['responsible'] == prof_idx).OnlyEnforceIf(is_resp_prof)
                    model.Add(assignments[p]['assistant1'] == prof_idx).OnlyEnforceIf(is_asst1_prof)
                    model.Add(assignments[p]['assistant2'] == prof_idx).OnlyEnforceIf(is_asst2_prof)
                
                # Ensure at least 2 professors
                model.Add(is_resp_prof + is_asst1_prof + is_asst2_prof >= 2)
        
        # 3. Constraint: Calculate instructor loads
        for i in range(len(instructor_ids)):
            # Count assignments for this instructor
            load_terms = []
            for p in range(len(project_ids)):
                resp_is_i = model.NewBoolVar(f'resp_{p}_is_{i}')
                asst1_is_i = model.NewBoolVar(f'asst1_{p}_is_{i}')
                asst2_is_i = model.NewBoolVar(f'asst2_{p}_is_{i}')
                
                model.Add(assignments[p]['responsible'] == i).OnlyEnforceIf(resp_is_i)
                model.Add(assignments[p]['responsible'] != i).OnlyEnforceIf(resp_is_i.Not())
                model.Add(assignments[p]['assistant1'] == i).OnlyEnforceIf(asst1_is_i)
                model.Add(assignments[p]['assistant1'] != i).OnlyEnforceIf(asst1_is_i.Not())
                model.Add(assignments[p]['assistant2'] == i).OnlyEnforceIf(asst2_is_i)
                model.Add(assignments[p]['assistant2'] != i).OnlyEnforceIf(asst2_is_i.Not())
                
                load_terms.extend([resp_is_i, asst1_is_i, asst2_is_i])
            
            model.Add(instructor_loads[i] == sum(load_terms))
        
        # 4. Constraint: Track classroom assignments
        for i in range(len(instructor_ids)):
            for c, classroom in enumerate(classroom_ids):
                # Instructor i is in classroom c if they're assigned to any project in that classroom
                classroom_terms = []
                for p, project_id in enumerate(project_ids):
                    project = self.projects[project_id]
                    if project.get("classroom") == classroom:
                        resp_is_i = model.NewBoolVar(f'resp_{p}_is_{i}_for_class')
                        asst1_is_i = model.NewBoolVar(f'asst1_{p}_is_{i}_for_class')
                        asst2_is_i = model.NewBoolVar(f'asst2_{p}_is_{i}_for_class')
                        
                        model.Add(assignments[p]['responsible'] == i).OnlyEnforceIf(resp_is_i)
                        model.Add(assignments[p]['responsible'] != i).OnlyEnforceIf(resp_is_i.Not())
                        model.Add(assignments[p]['assistant1'] == i).OnlyEnforceIf(asst1_is_i)
                        model.Add(assignments[p]['assistant1'] != i).OnlyEnforceIf(asst1_is_i.Not())
                        model.Add(assignments[p]['assistant2'] == i).OnlyEnforceIf(asst2_is_i)
                        model.Add(assignments[p]['assistant2'] != i).OnlyEnforceIf(asst2_is_i.Not())
                        
                        classroom_terms.extend([resp_is_i, asst1_is_i, asst2_is_i])
                
                if classroom_terms:
                    # Instructor is in classroom if any of the terms are true
                    model.AddMaxEquality(instructor_in_classroom[(i, c)], classroom_terms)
                else:
                    model.Add(instructor_in_classroom[(i, c)] == 0)
        
        # 5. Constraint: Calculate classroom changes
        for i in range(len(instructor_ids)):
            model.Add(classroom_changes[i] == sum(instructor_in_classroom[(i, c)] for c in range(len(classroom_ids))))
            # Subtract 1 if instructor is in at least one classroom (to get number of changes)
            any_classroom = model.NewBoolVar(f'instr_{i}_any_classroom')
            model.Add(sum(instructor_in_classroom[(i, c)] for c in range(len(classroom_ids))) >= 1).OnlyEnforceIf(any_classroom)
            model.Add(sum(instructor_in_classroom[(i, c)] for c in range(len(classroom_ids))) == 0).OnlyEnforceIf(any_classroom.Not())
            
            # If instructor is in any classroom, subtract 1 from classroom_changes
            model.Add(classroom_changes[i] == sum(instructor_in_classroom[(i, c)] for c in range(len(classroom_ids))) - any_classroom)
        
        # Objective function
        # 1. Minimize load imbalance (standard deviation)
        # We can't directly minimize standard deviation, so we'll minimize the sum of squared differences from mean
        avg_load = model.NewIntVar(0, len(project_ids) * 3, 'avg_load')
        model.Add(avg_load * len(instructor_ids) == sum(instructor_loads[i] for i in range(len(instructor_ids))))
        
        # Create variables for squared differences
        sq_diffs = []
        for i in range(len(instructor_ids)):
            diff = model.NewIntVar(-len(project_ids) * 3, len(project_ids) * 3, f'diff_{i}')
            sq_diff = model.NewIntVar(0, (len(project_ids) * 3) ** 2, f'sq_diff_{i}')
            
            model.Add(diff == instructor_loads[i] - avg_load)
            # Approximate squared difference using piecewise linear function
            model.AddMultiplicationEquality(sq_diff, [diff, diff])
            sq_diffs.append(sq_diff)
        
        # 2. Minimize classroom changes
        # For professors, classroom changes have higher weight
        weighted_changes = []
        for i in range(len(instructor_ids)):
            if i in professor_indices:
                # Double weight for professors
                weighted_change = model.NewIntVar(0, len(classroom_ids) * 2, f'weighted_change_{i}')
                model.Add(weighted_change == classroom_changes[i] * 2)
                weighted_changes.append(weighted_change)
            else:
                weighted_changes.append(classroom_changes[i])
        
        # Combined objective: minimize load imbalance and classroom changes
        model.Minimize(
            self.parameters['load_weight'] * sum(sq_diffs) + 
            self.parameters['classroom_weight'] * sum(weighted_changes)
        )
        
        # Create solver and solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.parameters['time_limit_seconds']
        solver.parameters.num_search_workers = self.parameters['num_search_workers']
        status = solver.Solve(model)
        
        # Process solution
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            # Extract solution
            solution = []
            for p in range(len(project_ids)):
                responsible_idx = solver.Value(assignments[p]['responsible'])
                assistant1_idx = solver.Value(assignments[p]['assistant1'])
                assistant2_idx = solver.Value(assignments[p]['assistant2'])
                solution.append((responsible_idx, assistant1_idx, assistant2_idx))
            
            # Convert solution to assignments
            result_assignments = self._solution_to_assignments(solution)
            
            # Calculate metrics
            metrics = self._calculate_metrics(solution)
            
            return {
                "assignments": result_assignments,
                "metrics": metrics,
                "status": "optimal" if status == cp_model.OPTIMAL else "feasible"
            }
        else:
            # If no solution found, use a heuristic approach
            solution = self._generate_heuristic_solution()
            result_assignments = self._solution_to_assignments(solution)
            metrics = self._calculate_metrics(solution)
            
            return {
                "assignments": result_assignments,
                "metrics": metrics,
                "status": "heuristic"
            }
    
    def _generate_heuristic_solution(self) -> List[Tuple[int, int, int]]:
        """Generate a heuristic solution if CP-SAT fails."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        solution = []
        instructor_counts = [0] * len(instructor_ids)
        
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
