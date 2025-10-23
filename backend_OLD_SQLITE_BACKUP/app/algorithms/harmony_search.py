import random
import numpy as np
from typing import Dict, Any, List, Tuple
from app.algorithms.base import BaseAlgorithm

class HarmonySearch(BaseAlgorithm):
    """Harmony Search algorithm implementation."""
    
    def __init__(
        self,
        projects=None,
        instructors=None,
        harmony_memory_size=30,
        iterations=100,
        harmony_memory_considering_rate=0.9,
        pitch_adjusting_rate=0.3,
        bandwidth=0.1,
        rule_weight=100,
        load_weight=10,
        classroom_weight=5
    ):
        super().__init__(projects, instructors, {
            'harmony_memory_size': harmony_memory_size,
            'iterations': iterations,
            'harmony_memory_considering_rate': harmony_memory_considering_rate,
            'pitch_adjusting_rate': pitch_adjusting_rate,
            'bandwidth': bandwidth,
            'rule_weight': rule_weight,
            'load_weight': load_weight,
            'classroom_weight': classroom_weight
        })
        
    def validate_parameters(self) -> bool:
        """Validate algorithm parameters."""
        if not self.parameters:
            return False
            
        required_params = ['harmony_memory_size', 'iterations', 
                          'harmony_memory_considering_rate', 'pitch_adjusting_rate',
                          'bandwidth', 'rule_weight', 'load_weight', 'classroom_weight']
        for param in required_params:
            if param not in self.parameters:
                return False
                
            # Check numeric parameters are positive
            if self.parameters[param] <= 0:
                return False
                
        # Check rates are between 0 and 1
        if not (0 <= self.parameters['harmony_memory_considering_rate'] <= 1):
            return False
        if not (0 <= self.parameters['pitch_adjusting_rate'] <= 1):
            return False
            
        return True
    
    def _evaluate_fitness_with_rules(self, harmony):
        """Kurallara uygun fitness hesaplama"""
        fitness = 0.0
        project_ids = list(self.projects.keys())
        
        # 1. Proje türü kuralları kontrolü (büyük bonus)
        for i, (responsible, assistant1, assistant2) in enumerate(harmony):
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
        for assignment in harmony:
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
        for i, (responsible, assistant1, assistant2) in enumerate(harmony):
            for instructor_id in [responsible, assistant1, assistant2]:
                if instructor_id in timeslot_usage:
                    conflict_penalty += 50
                timeslot_usage[instructor_id] = True
        
        fitness -= conflict_penalty
        
        return fitness
        
    def optimize(self) -> Dict[str, Any]:
        """Run Harmony Search optimization algorithm - Kurallara uygun"""
        if not self.projects or not self.instructors:
            return {"error": "No projects or instructors provided"}
        
        # Her çalıştırmada farklı sonuç için random seed
        import time
        random.seed(int(time.time() * 1000) % 2**32)
        np.random.seed(int(time.time() * 1000) % 2**32)
            
        # Initialize harmony memory
        harmony_memory = self._initialize_harmony_memory()
        
        # Evaluate harmony memory with rules
        harmony_fitness = [self._evaluate_fitness_with_rules(h) for h in harmony_memory]
        
        # Main optimization loop - Harmony Search prensiplerine göre
        for iteration in range(self.parameters['iterations']):
            # Improvise a new harmony - Harmony Search formülü
            new_harmony = self._improvise_new_harmony(harmony_memory)
            
            # Evaluate new harmony with rules
            new_fitness = self._evaluate_fitness_with_rules(new_harmony)
            
            # Update harmony memory if new harmony is better than the worst harmony
            worst_idx = np.argmin(harmony_fitness)
            if new_fitness > harmony_fitness[worst_idx]:
                harmony_memory[worst_idx] = new_harmony
                harmony_fitness[worst_idx] = new_fitness
        
        # Find best harmony
        best_idx = np.argmax(harmony_fitness)
        best_harmony = harmony_memory[best_idx]
        best_fitness = harmony_fitness[best_idx]
        
        # Convert best harmony to assignments
        assignments = self._solution_to_assignments(best_harmony)
        
        return {
            "assignments": assignments,
            "fitness": best_fitness,
            "iterations": self.parameters['iterations']
        }
        
    def _initialize_harmony_memory(self) -> List[List[Tuple[int, int, int]]]:
        """Initialize harmony memory with random solutions."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        harmony_memory = []
        
        for _ in range(self.parameters['harmony_memory_size']):
            harmony = []
            
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
                
                harmony.append((responsible_idx, assistant1_idx, assistant2_idx))
            
            harmony_memory.append(harmony)
        
        return harmony_memory
        
    def _improvise_new_harmony(self, harmony_memory: List[List[Tuple[int, int, int]]]) -> List[Tuple[int, int, int]]:
        """Improvise a new harmony based on harmony memory."""
        project_ids = list(self.projects.keys())
        instructor_ids = list(self.instructors.keys())
        professor_indices = [i for i, id in enumerate(instructor_ids) 
                           if self.instructors[id].get("type") == "professor"]
        
        new_harmony = []
        
        for project_idx in range(len(project_ids)):
            project_id = project_ids[project_idx]
            project = self.projects[project_id]
            
            # Decide whether to use harmony memory
            if random.random() < self.parameters['harmony_memory_considering_rate']:
                # Select a random harmony from memory
                random_harmony_idx = random.randrange(len(harmony_memory))
                responsible_idx, assistant1_idx, assistant2_idx = harmony_memory[random_harmony_idx][project_idx]
                
                # Apply pitch adjustment to responsible
                if random.random() < self.parameters['pitch_adjusting_rate']:
                    responsible_idx = self._adjust_pitch(responsible_idx, project, "responsible", professor_indices)
                
                # Apply pitch adjustment to assistant1
                if random.random() < self.parameters['pitch_adjusting_rate']:
                    assistant1_idx = self._adjust_pitch(assistant1_idx, project, "assistant1", professor_indices)
                
                # Apply pitch adjustment to assistant2
                if random.random() < self.parameters['pitch_adjusting_rate']:
                    assistant2_idx = self._adjust_pitch(assistant2_idx, project, "assistant2", professor_indices)
            else:
                # Generate new values randomly
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
            
            new_harmony.append((responsible_idx, assistant1_idx, assistant2_idx))
        
        return new_harmony
        
    def _adjust_pitch(self, instructor_idx: int, project: Dict, position: str, professor_indices: List[int]) -> int:
        """Adjust pitch (instructor index) based on bandwidth."""
        instructor_ids = list(self.instructors.keys())
        
        # Different adjustment strategies based on position and project type
        if position == "responsible" and project.get("type") == "final" and professor_indices:
            # For responsible position in final projects, must be professor
            if instructor_idx not in professor_indices:
                return random.choice(professor_indices)
            else:
                # Adjust within professors
                if len(professor_indices) > 1:
                    candidates = [i for i in professor_indices if i != instructor_idx]
                    return random.choice(candidates)
                return instructor_idx
        else:
            # For other positions, adjust based on bandwidth
            # Convert discrete index to continuous value
            continuous_value = instructor_idx + random.uniform(-self.parameters['bandwidth'], self.parameters['bandwidth'])
            
            # Map back to valid instructor index
            new_idx = round(continuous_value)
            new_idx = max(0, min(new_idx, len(instructor_ids) - 1))
            
            return new_idx
        
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
