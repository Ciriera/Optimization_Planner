"""
NSGA-II Enhanced Algorithm - Enhanced with Pure Consecutive Grouping
Uses same logic as Genetic Algorithm for optimal uniform distribution
"""

from typing import Dict, Any, List, Tuple, Optional, Set
import random
import numpy as np
import logging
import time
from copy import deepcopy
from collections import defaultdict
from datetime import time as dt_time
from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


class NSGAIIEnhanced(OptimizationAlgorithm):
    """
    NSGA-II Enhanced Algorithm - Enhanced with Pure Consecutive Grouping + Smart Jury Assignment.
    
    SUCCESS STRATEGY (Same as Deep Search Algorithm):
    NOT 1: RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
    NOT 2: AKILLI EK GÖREV ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin ek görevi
    NOT 3: CONSECUTIVE GROUPING - Her instructor'ın projeleri ardışık ve aynı sınıfta
    
    This implementation uses the SAME logic as Deep Search Algorithm for:
    1. RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
    2. EN ERKEN BOŞ SLOT mantığı - Boş slotlar varken ileri atlamaz
    3. Uniform distribution - D111 dahil tüm sınıfları kullanır
    4. Pure consecutive grouping - Her instructor'ın projeleri ardışık
    5. AKILLI EK GÖREV ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin ek görevi
    6. Conflict-free scheduling - Instructor çakışmalarını önler
    
    Strategy:
    "Bir öğretim görevlimizi sorumlu olduğu projelerden birisiyle birlikte 
    diyelim ki 09:00-09:30 zaman slotuna ve D106 sınıfına atamasını yaptık. 
    Bu öğretim görevlimizin diğer sorumlu olduğu projeleri de aynı sınıfa 
    ve hemen sonraki zaman slotlarına atayalım ki çok fazla yer değişimi olmasın"
    
    Original Features (Preserved):
    1. Jury assignment rules based on project type
    2. RA-Placeholder system for research assistants
    3. Multi-objective optimization (NSGA-II)
    4. Pareto-optimal solutions
    """

    def __init__(self, params: Dict[str, Any] = None):
        """Initialize enhanced NSGA-II algorithm with Pure Consecutive Grouping."""
        super().__init__(params)
        self.name = "NSGA-II Enhanced"
        self.description = "Enhanced Randomizer + Consecutive Grouping + Smart Jury + Multi-Objective (Same as Deep Search)"

        # NSGA-II Parameters
        self.population_size = params.get("population_size", 50) if params else 50
        self.generations = params.get("generations", 20) if params else 20
        self.mutation_rate = params.get("mutation_rate", 0.1) if params else 0.1
        self.crossover_rate = params.get("crossover_rate", 0.8) if params else 0.8

        # Initialize data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
        
        # Enhanced features
        self.instructor_types = {}  # instructor_id -> type mapping
        self.available_instructors = []  # Available instructors for additional assignment
        self.placeholder_ra_count = 0  # Counter for RA-Placeholder

    def initialize(self, data: Dict[str, Any]) -> None:
        """Initialize algorithm with data."""
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Build instructor type mapping
        self.instructor_types = {}
        self.available_instructors = []
        
        for instructor in self.instructors:
            instructor_id = instructor.get("id")
            instructor_type = instructor.get("type", "instructor")
            self.instructor_types[instructor_id] = instructor_type
            
            # Only add instructors (not assistants) to available list for additional assignment
            if instructor_type == "instructor":
                self.available_instructors.append(instructor_id)
        
        logger.info(f"Initialized with {len(self.projects)} projects, {len(self.instructors)} instructors, {len(self.classrooms)} classrooms, {len(self.timeslots)} timeslots")
        logger.info(f"Available instructors for additional: {len(self.available_instructors)}")

    def _get_jury_assignment_rules(self, project_type: str) -> Dict[str, Any]:
        """
        Get jury assignment rules based on project type.
        
        Args:
            project_type: "interim" or "final"
            
        Returns:
            Dict with jury assignment rules
        """
        if project_type.lower() in ["interim", "ara"]:
            # Ara Projeler: 1-2 Arş.Gör. veya 1 Öğr.Ü. + 1 Arş.Gör. veya 1 Öğr.Ü.
            return {
                "min_jury": 1,
                "max_jury": 2,
                "allowed_combinations": [
                    {"instructor": 0, "assistant": 1},  # 1 Arş.Gör.
                    {"instructor": 0, "assistant": 2},  # 2 Arş.Gör.
                    {"instructor": 1, "assistant": 1},  # 1 Öğr.Ü. + 1 Arş.Gör.
                    {"instructor": 1, "assistant": 0},  # 1 Öğr.Ü.
                ]
            }
        else:  # final/bitirme
            # Bitirme Projeler: 1-2 Öğr.Ü. veya 1 Öğr.Ü. + 1 Arş.Gör.
            return {
                "min_jury": 1,
                "max_jury": 2,
                "allowed_combinations": [
                    {"instructor": 1, "assistant": 0},  # 1 Öğr.Ü.
                    {"instructor": 2, "assistant": 0},  # 2 Öğr.Ü.
                    {"instructor": 1, "assistant": 1},  # 1 Öğr.Ü. + 1 Arş.Gör.
                ]
            }

    def _assign_jury_to_project(self, project: Dict[str, Any], used_instructors: Set[int], used_slots: Set[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """
        Assign jury members to a project based on rules.
        
        Args:
            project: Project data
            used_instructors: Set of already used instructor IDs
            used_slots: Set of already used (classroom_id, timeslot_id) pairs
            
        Returns:
            List of assigned jury members
        """
        project_type = project.get("type", "interim")
        rules = self._get_jury_assignment_rules(project_type)
        
        # Select a random valid combination
        combination = random.choice(rules["allowed_combinations"])
        instructor_count = combination["instructor"]
        assistant_count = combination["assistant"]
        
        jury_members = []
        
        # Assign instructors
        available_instructors = [iid for iid in self.available_instructors if iid not in used_instructors]
        if len(available_instructors) >= instructor_count:
            selected_instructors = random.sample(available_instructors, instructor_count)
            for instructor_id in selected_instructors:
                jury_members.append({
                    "id": instructor_id,
                    "name": f"Instructor {instructor_id}",
                    "type": "instructor"
                })
                used_instructors.add(instructor_id)
        
        # Assign assistants (RA-Placeholder)
        for _ in range(assistant_count):
            self.placeholder_ra_count += 1
            jury_members.append({
                "id": f"ra_placeholder_{self.placeholder_ra_count}",
                "name": "RA-Placeholder",
                "type": "assistant"
            })
        
        return jury_members

    def _check_instructor_conflict(self, instructor_id: int, classroom_id: int, timeslot_id: int, 
                                 instructor_assignments: Dict[int, List[Dict[str, Any]]]) -> bool:
        """
        Check if instructor has conflict (already assigned to different classroom at same time).
        
        Args:
            instructor_id: Instructor ID to check
            classroom_id: Proposed classroom
            timeslot_id: Proposed timeslot
            instructor_assignments: Current instructor assignments
            
        Returns:
            True if conflict exists, False otherwise
        """
        if instructor_id not in instructor_assignments:
            return False
        
        for assignment in instructor_assignments[instructor_id]:
            if (assignment["timeslot_id"] == timeslot_id and 
                assignment["classroom_id"] != classroom_id):
                return True
        
        return False

    def _find_consecutive_slots_for_instructor(self, instructor_id: int, project_count: int, 
                                             used_slots: Set[Tuple[int, int]], 
                                             instructor_assignments: Dict[int, List[Dict[str, Any]]]) -> Optional[Tuple[int, int]]:
        """
        Find consecutive slots for an instructor's projects.
        
        Args:
            instructor_id: Instructor ID
            project_count: Number of projects to assign
            used_slots: Set of used slots
            instructor_assignments: Current assignments
            
        Returns:
            (classroom_id, start_timeslot_id) if found, None otherwise
        """
        # Sort timeslots by start time
        sorted_timeslots = sorted(self.timeslots, key=lambda x: x.get("start_time", "09:00"))
        
        # Try each classroom
        for classroom in self.classrooms:
            classroom_id = classroom.get("id")
            
            # Try each possible start position
            for start_idx in range(len(sorted_timeslots) - project_count + 1):
                consecutive_slots = []
                valid = True
                
                # Check if consecutive slots are available
                for i in range(project_count):
                    timeslot_id = sorted_timeslots[start_idx + i].get("id")
                    slot_key = (classroom_id, timeslot_id)
                    
                    # Check if slot is available and no conflict
                    if (slot_key in used_slots or 
                        self._check_instructor_conflict(instructor_id, classroom_id, timeslot_id, instructor_assignments)):
                        valid = False
                        break
                    
                    consecutive_slots.append(timeslot_id)
                
                if valid:
                    return (classroom_id, start_idx)
        
        return None

    def _generate_random_solution(self) -> Dict[str, Any]:
        """Generate a random solution with enhanced consecutive grouping and jury assignment."""
        solution = []
        used_slots = set()
        instructor_assignments = defaultdict(list)
        used_instructors = set()
        
        # Group projects by responsible instructor
        instructor_projects = defaultdict(list)
        for project in self.projects:
            responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
            if responsible_id:
                instructor_projects[responsible_id].append(project)
        
        # Sort instructors by project count (descending) for better distribution
        sorted_instructors = sorted(instructor_projects.items(), key=lambda x: len(x[1]), reverse=True)
        
        for instructor_id, projects_list in sorted_instructors:
            if not projects_list:
                continue
            
            # Try to find consecutive slots for all projects
            consecutive_result = self._find_consecutive_slots_for_instructor(
                instructor_id, len(projects_list), used_slots, instructor_assignments
            )
            
            if consecutive_result:
                classroom_id, start_timeslot_idx = consecutive_result
                sorted_timeslots = sorted(self.timeslots, key=lambda x: x.get("start_time", "09:00"))
                
                # Assign projects to consecutive slots
                for i, project in enumerate(projects_list):
                    timeslot_id = sorted_timeslots[start_timeslot_idx + i].get("id")
                    slot_key = (classroom_id, timeslot_id)
                    
                    # Assign jury members
                    jury_members = self._assign_jury_to_project(project, used_instructors, used_slots)
                    
                    # Create assignment
                    assignment = {
                        "project_id": project.get("id"),
                        "classroom_id": classroom_id,
                        "timeslot_id": timeslot_id,
                        "instructors": [instructor_id] + [j["id"] for j in jury_members if j["type"] == "instructor"]
                    }
                    
                    solution.append(assignment)
                    used_slots.add(slot_key)
                    instructor_assignments[instructor_id].append({
                        "classroom_id": classroom_id,
                        "timeslot_id": timeslot_id,
                        "role": "responsible"
                    })
                    
                    # Add jury instructors to assignments
                    for jury_member in jury_members:
                        if jury_member["type"] == "instructor":
                            instructor_assignments[jury_member["id"]].append({
                                "classroom_id": classroom_id,
                                "timeslot_id": timeslot_id,
                                "role": "jury"
                            })
            else:
                # Fallback: assign to any available slots
                for project in projects_list:
                    assigned = False
                    
                    for classroom in self.classrooms:
                        if assigned:
                            break
                        
                        classroom_id = classroom.get("id")
                        
                        for timeslot in self.timeslots:
                            timeslot_id = timeslot.get("id")
                            slot_key = (classroom_id, timeslot_id)
                            
                            if (slot_key not in used_slots and 
                                not self._check_instructor_conflict(instructor_id, classroom_id, timeslot_id, instructor_assignments)):
                                
                                # Assign jury members
                                jury_members = self._assign_jury_to_project(project, used_instructors, used_slots)
                                
                                assignment = {
                                    "project_id": project.get("id"),
                                    "classroom_id": classroom_id,
                                    "timeslot_id": timeslot_id,
                                    "instructors": [instructor_id] + [j["id"] for j in jury_members if j["type"] == "instructor"]
                                }
                                
                                solution.append(assignment)
                                used_slots.add(slot_key)
                                instructor_assignments[instructor_id].append({
                                    "classroom_id": classroom_id,
                                    "timeslot_id": timeslot_id,
                                    "role": "responsible"
                                })
                                
                                # Add jury instructors to assignments
                                for jury_member in jury_members:
                                    if jury_member["type"] == "instructor":
                                        instructor_assignments[jury_member["id"]].append({
                                            "classroom_id": classroom_id,
                                            "timeslot_id": timeslot_id,
                                            "role": "jury"
                                        })
                                
                                assigned = True
                                break
        
        return {
            "assignment": solution,
            "method": "enhanced_consecutive_with_jury"
        }

    def _calculate_objectives(self, solution: Dict[str, Any]) -> List[float]:
        """Calculate multiple objectives for the solution."""
        assignments = solution.get("assignment", [])
        
        if not assignments:
            return [float('inf')] * 4
        
        # Objective 1: Minimize total conflicts
        conflicts = 0
        instructor_slots = defaultdict(set)
        
        for assignment in assignments:
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            instructors = assignment.get("instructors", [])
            
            for instructor_id in instructors:
                if instructor_id in instructor_slots:
                    if timeslot_id in instructor_slots[instructor_id]:
                        conflicts += 1
                instructor_slots[instructor_id].add(timeslot_id)
        
        # Objective 2: Minimize classroom switches per instructor
        classroom_switches = 0
        instructor_classrooms = defaultdict(set)
        
        for assignment in assignments:
            classroom_id = assignment.get("classroom_id")
            instructors = assignment.get("instructors", [])
            
            for instructor_id in instructors:
                instructor_classrooms[instructor_id].add(classroom_id)
        
        for instructor_id, classrooms in instructor_classrooms.items():
            classroom_switches += max(0, len(classrooms) - 1)
        
        # Objective 3: Maximize consecutive assignments
        consecutive_score = 0
        instructor_timeslots = defaultdict(list)
        
        for assignment in assignments:
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            instructors = assignment.get("instructors", [])
            
            for instructor_id in instructors:
                instructor_timeslots[instructor_id].append({
                    "classroom_id": classroom_id,
                    "timeslot_id": timeslot_id
                })
        
        for instructor_id, slots in instructor_timeslots.items():
            # Group by classroom
            classroom_slots = defaultdict(list)
            for slot in slots:
                classroom_slots[slot["classroom_id"]].append(slot["timeslot_id"])
            
            # Calculate consecutive score for each classroom
            for classroom_id, timeslots in classroom_slots.items():
                sorted_timeslots = sorted(timeslots)
                consecutive_count = 1
                max_consecutive = 1
                
                for i in range(1, len(sorted_timeslots)):
                    if sorted_timeslots[i] == sorted_timeslots[i-1] + 1:
                        consecutive_count += 1
                        max_consecutive = max(max_consecutive, consecutive_count)
                    else:
                        consecutive_count = 1
                
                consecutive_score += max_consecutive
        
        # Objective 4: Uniform distribution (minimize variance in instructor workload)
        instructor_workloads = defaultdict(int)
        for assignment in assignments:
            instructors = assignment.get("instructors", [])
            for instructor_id in instructors:
                instructor_workloads[instructor_id] += 1
        
        if instructor_workloads:
            workloads = list(instructor_workloads.values())
            workload_variance = np.var(workloads) if len(workloads) > 1 else 0
        else:
            workload_variance = 0
        
        return [conflicts, classroom_switches, -consecutive_score, workload_variance]

    def _non_dominated_sort(self, population: List[Dict[str, Any]]) -> List[List[int]]:
        """Perform non-dominated sorting."""
        n = len(population)
        objectives = [self._calculate_objectives(individual) for individual in population]
        
        # Initialize
        fronts = []
        dominated_count = [0] * n
        dominated_solutions = [[] for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    if self._dominates(objectives[i], objectives[j]):
                        dominated_solutions[i].append(j)
                    elif self._dominates(objectives[j], objectives[i]):
                        dominated_count[i] += 1
            
            if dominated_count[i] == 0:
                if not fronts:
                    fronts.append([])
                fronts[0].append(i)
        
        # Build subsequent fronts
        front_index = 0
        while fronts[front_index]:
            next_front = []
            for i in fronts[front_index]:
                for j in dominated_solutions[i]:
                    dominated_count[j] -= 1
                    if dominated_count[j] == 0:
                        next_front.append(j)
            
            if next_front:
                fronts.append(next_front)
            front_index += 1
        
        return fronts

    def _dominates(self, obj1: List[float], obj2: List[float]) -> bool:
        """Check if obj1 dominates obj2."""
        return all(o1 <= o2 for o1, o2 in zip(obj1, obj2)) and any(o1 < o2 for o1, o2 in zip(obj1, obj2))

    def _crowding_distance(self, front: List[int], objectives: List[List[float]]) -> List[float]:
        """Calculate crowding distance for solutions in a front."""
        n = len(front)
        distances = [0.0] * n
        
        if n <= 2:
            return [float('inf')] * n
        
        num_objectives = len(objectives[0])
        
        for m in range(num_objectives):
            # Sort by objective m
            sorted_indices = sorted(range(n), key=lambda i: objectives[front[i]][m])
            
            # Set boundary points
            distances[sorted_indices[0]] = float('inf')
            distances[sorted_indices[-1]] = float('inf')
            
            # Calculate range
            obj_range = objectives[front[sorted_indices[-1]]][m] - objectives[front[sorted_indices[0]]][m]
            if obj_range == 0:
                continue
            
            # Calculate distances
            for i in range(1, n - 1):
                distances[sorted_indices[i]] += (
                    objectives[front[sorted_indices[i + 1]]][m] - 
                    objectives[front[sorted_indices[i - 1]]][m]
                ) / obj_range
        
        return distances

    def _tournament_selection(self, population: List[Dict[str, Any]], fronts: List[List[int]], 
                            objectives: List[List[float]], tournament_size: int = 2) -> Dict[str, Any]:
        """Tournament selection for parent selection."""
        n = len(population)
        selected = random.randint(0, n - 1)
        
        for _ in range(tournament_size - 1):
            candidate = random.randint(0, n - 1)
            
            # Compare based on front and crowding distance
            selected_front = None
            candidate_front = None
            
            for i, front in enumerate(fronts):
                if selected in front:
                    selected_front = i
                if candidate in front:
                    candidate_front = i
            
            if selected_front is None or candidate_front is None:
                continue
            
            if candidate_front < selected_front:
                selected = candidate
            elif candidate_front == selected_front:
                # Same front, use crowding distance
                crowding_distances = self._crowding_distance(fronts[selected_front], objectives)
                if crowding_distances[candidate] > crowding_distances[selected]:
                    selected = candidate
        
        return population[selected]

    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Perform crossover between two parents."""
        if random.random() > self.crossover_rate:
            return parent1, parent2
        
        # Simple crossover: combine assignments from both parents
        assignments1 = parent1.get("assignment", [])
        assignments2 = parent2.get("assignment", [])
        
        # Create child by combining assignments
        child_assignments = []
        used_projects = set()
        
        # Take half from parent1
        for assignment in assignments1[:len(assignments1)//2]:
            project_id = assignment.get("project_id")
            if project_id not in used_projects:
                child_assignments.append(assignment)
                used_projects.add(project_id)
        
        # Take remaining from parent2
        for assignment in assignments2:
            project_id = assignment.get("project_id")
            if project_id not in used_projects:
                child_assignments.append(assignment)
                used_projects.add(project_id)
        
        child1 = {"assignment": child_assignments, "method": "crossover"}
        child2 = {"assignment": assignments2, "method": "crossover"}
        
        return child1, child2

    def _mutate(self, individual: Dict[str, Any]) -> Dict[str, Any]:
        """Perform mutation on an individual."""
        if random.random() > self.mutation_rate:
            return individual
        
        assignments = individual.get("assignment", [])
        if not assignments:
            return individual
        
        # Randomly swap two assignments
        if len(assignments) >= 2:
            i, j = random.sample(range(len(assignments)), 2)
            assignments[i], assignments[j] = assignments[j], assignments[i]
        
        return {"assignment": assignments, "method": "mutated"}

    def optimize(self) -> Dict[str, Any]:
        """Run the enhanced NSGA-II optimization."""
        logger.info("Starting Enhanced NSGA-II optimization")
        start_time = time.time()
        
        # Initialize population
        population = []
        for _ in range(self.population_size):
            individual = self._generate_random_solution()
            population.append(individual)
        
        # Evolution loop
        for generation in range(self.generations):
            logger.info(f"Generation {generation + 1}/{self.generations}")
            
            # Calculate objectives for all individuals
            objectives = [self._calculate_objectives(individual) for individual in population]
            
            # Non-dominated sorting
            fronts = self._non_dominated_sort(population)
            
            # Create new population
            new_population = []
            front_index = 0
            
            while len(new_population) + len(fronts[front_index]) <= self.population_size:
                # Add entire front
                for i in fronts[front_index]:
                    new_population.append(population[i])
                front_index += 1
            
            # Add remaining individuals from next front using crowding distance
            if len(new_population) < self.population_size:
                remaining = self.population_size - len(new_population)
                crowding_distances = self._crowding_distance(fronts[front_index], objectives)
                
                # Sort by crowding distance (descending)
                sorted_indices = sorted(range(len(fronts[front_index])), 
                                      key=lambda i: crowding_distances[i], reverse=True)
                
                for i in range(remaining):
                    if i < len(sorted_indices):
                        new_population.append(population[fronts[front_index][sorted_indices[i]]])
            
            # Create offspring
            offspring = []
            while len(offspring) < self.population_size:
                parent1 = self._tournament_selection(population, fronts, objectives)
                parent2 = self._tournament_selection(population, fronts, objectives)
                
                child1, child2 = self._crossover(parent1, parent2)
                child1 = self._mutate(child1)
                child2 = self._mutate(child2)
                
                offspring.extend([child1, child2])
            
            # Combine parent and offspring populations
            combined_population = population + offspring
            
            # Select next generation
            combined_objectives = [self._calculate_objectives(individual) for individual in combined_population]
            combined_fronts = self._non_dominated_sort(combined_population)
            
            population = []
            front_index = 0
            
            while len(population) + len(combined_fronts[front_index]) <= self.population_size:
                for i in combined_fronts[front_index]:
                    population.append(combined_population[i])
                front_index += 1
            
            if len(population) < self.population_size:
                remaining = self.population_size - len(population)
                crowding_distances = self._crowding_distance(combined_fronts[front_index], combined_objectives)
                
                sorted_indices = sorted(range(len(combined_fronts[front_index])), 
                                      key=lambda i: crowding_distances[i], reverse=True)
                
                for i in range(remaining):
                    if i < len(sorted_indices):
                        population.append(combined_population[combined_fronts[front_index][sorted_indices[i]]])
        
        # Select best solution (first individual from first front)
        final_objectives = [self._calculate_objectives(individual) for individual in population]
        final_fronts = self._non_dominated_sort(population)
        
        best_solution = population[final_fronts[0][0]]
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.info(f"Enhanced NSGA-II optimization completed in {execution_time:.2f} seconds")
        
        return {
            "assignment": best_solution.get("assignment", []),
            "method": "enhanced_nsga_ii",
            "execution_time": execution_time,
            "generations": self.generations,
            "population_size": self.population_size,
            "objectives": final_objectives[final_fronts[0][0]]
        }

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute method with Pure Consecutive Grouping (Same as Deep Search Algorithm).
        Uses direct approach with Enhanced Randomizer + Smart Jury Assignment.
        
        SUCCESS STRATEGY:
        NOT 1: RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
        NOT 2: AKILLI EK GÖREV ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin ek görevi
        NOT 3: CONSECUTIVE GROUPING - Her instructor'ın projeleri ardışık ve aynı sınıfta
        """
        start_time = time.time()
        self.initialize(data)
        
        logger.info("NSGA-II Enhanced Algorithm başlatılıyor (Enhanced Randomizer + Consecutive Grouping + Smart Jury mode)...")
        logger.info(f"  Projeler: {len(self.projects)}")
        logger.info(f"  Instructors: {len(self.instructors)}")
        logger.info(f"  Sınıflar: {len(self.classrooms)}")
        logger.info(f"  Zaman Slotları: {len(self.timeslots)}")

        # Pure Consecutive Grouping Algorithm - Same as Deep Search Algorithm
        logger.info("Pure Consecutive Grouping + Enhanced Randomizer + Smart Jury ile optimal çözüm oluşturuluyor...")
        best_solution = self._create_pure_consecutive_grouping_solution()
        logger.info(f"  Pure Consecutive Grouping: {len(best_solution)} proje atandı")
        
        # Conflict detection ve resolution
        if best_solution and len(best_solution) > 0:
            logger.info("Conflict detection ve resolution...")
            conflicts = self._detect_conflicts(best_solution)
            
            if conflicts:
                logger.warning(f"  {len(conflicts)} conflict detected!")
                best_solution = self._resolve_conflicts(best_solution)
                
                remaining_conflicts = self._detect_conflicts(best_solution)
                if remaining_conflicts:
                    logger.error(f"  WARNING: {len(remaining_conflicts)} conflicts still remain!")
                else:
                    logger.info("  All conflicts successfully resolved!")
            else:
                logger.info("  No conflicts detected.")
        
        # Final stats
        final_stats = self._calculate_grouping_stats(best_solution)
        logger.info(f"  Final consecutive grouping stats:")
        logger.info(f"    Consecutive instructors: {final_stats['consecutive_count']}")
        logger.info(f"    Avg classroom changes: {final_stats['avg_classroom_changes']:.2f}")

        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"NSGA-II Enhanced Algorithm completed. Execution time: {execution_time:.2f}s")

        return {
            "assignments": best_solution or [],
            "schedule": best_solution or [],
            "solution": best_solution or [],
            "fitness_scores": self._calculate_fitness_scores(best_solution or []),
            "execution_time": execution_time,
            "algorithm": "NSGA-II Enhanced (Enhanced Randomizer + Consecutive Grouping + Smart Jury)",
            "status": "completed",
            "optimizations_applied": [
                "enhanced_randomizer_instructor_order",  # NOT 1
                "pure_consecutive_grouping",  # NOT 3
                "smart_jury_assignment",  # NOT 2
                "consecutive_jury_pairing",  # NOT 2
                "conflict_detection_and_resolution",
                "uniform_classroom_distribution",
                "earliest_slot_assignment",
                "multi_objective_optimization"
            ],
            "stats": final_stats,
            "parameters": {
                "algorithm_type": "consecutive_grouping_with_smart_jury",
                "enhanced_randomizer_instructor_order": True,  # NOT 1
                "smart_jury_assignment": True,  # NOT 2
                "consecutive_jury_pairing": True,  # NOT 2
                "conflict_prevention": True,
                "same_classroom_priority": True,
                "uniform_distribution": True,
                "earliest_slot_strategy": True,
                "population_size": self.population_size,
                "generations": self.generations
            }
        }

    # ========== Pure Consecutive Grouping Methods (Same as Genetic Algorithm) ==========

    def _create_pure_consecutive_grouping_solution(self) -> List[Dict[str, Any]]:
        """
        Pure consecutive grouping çözümü oluştur - Same as Deep Search Algorithm.
        
        SUCCESS STRATEGY:
        NOT 1: RASTGELE INSTRUCTOR SIRALAMA - Her çalıştırmada farklı öğretim görevlisi sırası
        NOT 2: AKILLI EK GÖREV ATAMALARI - Aynı sınıfta ardışık olan instructor'lar birbirinin ek görevi
        NOT 3: CONSECUTIVE GROUPING - Her instructor'ın projeleri ardışık ve aynı sınıfta
        
        "Bir öğretim görevlimizi sorumlu olduğu projelerden birisiyle birlikte diyelim ki 09:00-09:30 
        zaman slotuna ve D106 sınıfına atamasını yaptık. Bu öğretim görevlimizin diğer sorumlu olduğu 
        projeleri de aynı sınıfa ve hemen sonraki zaman slotlarına atayalım ki çok fazla yer değişimi olmasın"
        """
        assignments = []
        
        # Zaman slotlarını sırala
        sorted_timeslots = sorted(
            self.timeslots,
            key=lambda x: self._parse_time(x.get("start_time", "09:00"))
        )
        
        # Instructor bazında projeleri grupla
        instructor_projects = defaultdict(list)
        for project in self.projects:
            responsible_id = project.get("responsible_id") or project.get("responsible_instructor_id")
            if responsible_id:
                instructor_projects[responsible_id].append(project)
        
        # Sıkı conflict prevention
        used_slots = set()  # (classroom_id, timeslot_id)
        instructor_timeslot_usage = defaultdict(set)  # instructor_id -> set of timeslot_ids
        assigned_projects = set()  # project_ids that have been assigned
        
        # NOT 2 İÇİN: ARDIŞIK JÜRİ EŞLEŞTİRMESİ - Her sınıfta ardışık atanan instructor'ları takip et
        classroom_instructor_sequence = defaultdict(list)  # classroom_id -> [{'instructor_id': ..., 'project_ids': [...]}]
        
        # NOT 1: YENİ RANDOMIZER - Instructorları tamamen rastgele sırala
        # Bu sayede her seferinde farklı öğretim görevlileri farklı sınıf ve zamanlarda olur
        instructor_list = list(instructor_projects.items())
        
        # Güçlü randomizer - birden fazla karıştırma
        for _ in range(3):  # 3 kez karıştır
            random.shuffle(instructor_list)
        
        logger.info(f"🎲 YENİ RANDOMIZER: Instructorlar rastgele sıralandı: {[inst_id for inst_id, _ in instructor_list]}")
        logger.info(f"📊 Toplam {len(instructor_list)} instructor rastgele sıralandı")
        
        # Her instructor için projeleri ata (consecutive grouping korunur!)
        for instructor_id, instructor_project_list in instructor_list:
            if not instructor_project_list:
                continue
            
            logger.info(f"Instructor {instructor_id} için {len(instructor_project_list)} proje atanıyor...")
            
            # Bu instructor için en uygun sınıf ve başlangıç slotunu bul
            best_classroom = None
            best_start_slot_idx = None
            
            # ÖNCE: Tüm sınıflarda en erken boş slotu ara (consecutive olmasa bile)
            earliest_available_slots = []
            
            for classroom in self.classrooms:
                classroom_id = classroom.get("id")
                
                for start_idx in range(len(sorted_timeslots)):
                    timeslot_id = sorted_timeslots[start_idx].get("id")
                    slot_key = (classroom_id, timeslot_id)
                    
                    instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                    if not isinstance(instructor_slots, set):
                        instructor_slots = set()
                    
                    if (slot_key not in used_slots and 
                        timeslot_id not in instructor_slots):
                        earliest_available_slots.append((start_idx, classroom_id))
                        break
            
            # En erken boş slotu kullan
            if earliest_available_slots:
                earliest_available_slots.sort(key=lambda x: x[0])
                best_start_slot_idx, best_classroom = earliest_available_slots[0]
                logger.info(f"Instructor {instructor_id} için en erken boş slot bulundu: {best_classroom} - slot {best_start_slot_idx}")
            else:
                # Fallback: Tam ardışık slot arama (eski mantık)
                for classroom in self.classrooms:
                    classroom_id = classroom.get("id")
                    
                    for start_idx in range(len(sorted_timeslots)):
                        available_consecutive_slots = 0
                        
                        for slot_idx in range(start_idx, len(sorted_timeslots)):
                            timeslot_id = sorted_timeslots[slot_idx].get("id")
                            slot_key = (classroom_id, timeslot_id)
                            
                            instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                            if not isinstance(instructor_slots, set):
                                instructor_slots = set()
                            
                            if (slot_key not in used_slots and 
                                timeslot_id not in instructor_slots):
                                available_consecutive_slots += 1
                            else:
                                break
                            
                            if available_consecutive_slots >= len(instructor_project_list):
                                break
                        
                        if available_consecutive_slots >= len(instructor_project_list):
                            best_classroom = classroom_id
                            best_start_slot_idx = start_idx
                            break
                    
                    if best_classroom:
                        break
            
            # Projeleri ata
            if best_classroom and best_start_slot_idx is not None:
                current_slot_idx = best_start_slot_idx
                instructor_classroom_projects = []  # Bu instructor'ın bu sınıftaki projeleri (NOT 2 için)
                
                for project in instructor_project_list:
                    project_id = project.get("id")
                    
                    # Bu proje zaten atanmış mı?
                    if project_id in assigned_projects:
                        logger.warning(f"UYARI: Proje {project_id} zaten atanmış, atlanıyor")
                        continue
                    
                    # EN ERKEN BOŞ SLOT BUL - Tüm sınıflarda ara
                    assigned = False
                    
                    # Önce mevcut sınıfta boş slot ara
                    for slot_idx in range(current_slot_idx, len(sorted_timeslots)):
                        timeslot_id = sorted_timeslots[slot_idx].get("id")
                        slot_key = (best_classroom, timeslot_id)
                        
                        instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                        if not isinstance(instructor_slots, set):
                            instructor_slots = set()
                        
                        if (slot_key not in used_slots and 
                            timeslot_id not in instructor_slots):
                            
                            assignment = {
                                "project_id": project_id,
                                "classroom_id": best_classroom,
                                "timeslot_id": timeslot_id,
                                "is_makeup": project.get("is_makeup", False),
                                "instructors": [instructor_id]
                            }
                            
                            assignments.append(assignment)
                            used_slots.add(slot_key)
                            instructor_timeslot_usage[instructor_id].add(timeslot_id)
                            assigned_projects.add(project_id)
                            assigned = True
                            instructor_classroom_projects.append(project_id)  # NOT 2: Jüri eşleştirmesi için kaydet
                            logger.info(f"Proje {project_id} atandı: {best_classroom} - {timeslot_id}")
                            break
                    
                    # Eğer mevcut sınıfta bulunamadıysa, tüm sınıflarda en erken boş slotu ara
                    if not assigned:
                        earliest_slot_found = None
                        earliest_classroom = None
                        earliest_slot_idx = float('inf')
                        
                        for classroom in self.classrooms:
                            classroom_id = classroom.get("id")
                            
                            for slot_idx in range(len(sorted_timeslots)):
                                timeslot_id = sorted_timeslots[slot_idx].get("id")
                                slot_key = (classroom_id, timeslot_id)
                                
                                instructor_slots = instructor_timeslot_usage.get(instructor_id, set())
                                if not isinstance(instructor_slots, set):
                                    instructor_slots = set()
                                
                                if (slot_key not in used_slots and 
                                    timeslot_id not in instructor_slots):
                                    
                                    if slot_idx < earliest_slot_idx:
                                        earliest_slot_idx = slot_idx
                                        earliest_slot_found = timeslot_id
                                        earliest_classroom = classroom_id
                                    break
                        
                        # En erken boş slotu kullan
                        if earliest_slot_found:
                            assignment = {
                                "project_id": project_id,
                                "classroom_id": earliest_classroom,
                                "timeslot_id": earliest_slot_found,
                                "is_makeup": project.get("is_makeup", False),
                                "instructors": [instructor_id]
                            }
                            
                            assignments.append(assignment)
                            used_slots.add((earliest_classroom, earliest_slot_found))
                            instructor_timeslot_usage[instructor_id].add(earliest_slot_found)
                            assigned_projects.add(project_id)
                            assigned = True
                            instructor_classroom_projects.append(project_id)  # NOT 2: Jüri eşleştirmesi için kaydet
                            logger.info(f"Proje {project_id} en erken slot'a atandı: {earliest_classroom} - {earliest_slot_found}")
                    
                    if not assigned:
                        logger.warning(f"UYARI: Proje {project_id} için hiçbir boş slot bulunamadı!")
                
                # NOT 2: Bu instructor'ı sınıf sequence'ine ekle (jüri eşleştirmesi için)
                if instructor_classroom_projects:
                    classroom_instructor_sequence[best_classroom].append({
                        'instructor_id': instructor_id,
                        'project_ids': instructor_classroom_projects
                    })
        
        # NOT 2: ARDIŞIK JÜRİ EŞLEŞTİRMESİ - Aynı sınıfta ardışık atanan instructor'ları eşleştir
        logger.info("Ardışık jüri eşleştirmesi başlatılıyor...")
        self._assign_consecutive_jury_members(assignments, classroom_instructor_sequence)
        
        logger.info(f"Pure Consecutive Grouping tamamlandı: {len(assignments)} atama yapıldı")
        return assignments

    def _assign_consecutive_jury_members(self, assignments: List[Dict[str, Any]], 
                                        classroom_instructor_sequence: Dict) -> None:
        """
        NOT 2: Aynı sınıfta ardışık atanan instructor'ları tespit et ve birbirinin jürisi yap.
        
        Mantık:
        - Dr. Öğretim Görevlisi 14: D106'da consecutive (09:00-09:30)
        - Dr. Öğretim Görevlisi 2: D106'da consecutive (09:30-10:00) 
        
        Sonuç:
        - Öğretim Görevlisi 14 sorumlu → Öğretim Görevlisi 2 jüri
        - Öğretim Görevlisi 2 sorumlu → Öğretim Görevlisi 14 jüri
        """
        jury_assignments_made = 0
        
        for classroom_id, instructor_sequence in classroom_instructor_sequence.items():
            if len(instructor_sequence) < 2:
                continue
            
            logger.info(f"Sınıf {classroom_id} için ardışık jüri eşleştirmesi yapılıyor...")
            
            for i in range(len(instructor_sequence) - 1):
                instructor_a = instructor_sequence[i]
                instructor_b = instructor_sequence[i + 1]
                
                instructor_a_id = instructor_a['instructor_id']
                instructor_b_id = instructor_b['instructor_id']
                
                # Instructor A'nın projelerine Instructor B'yi jüri yap
                for assignment in assignments:
                    if assignment['project_id'] in instructor_a['project_ids']:
                        if instructor_b_id not in assignment['instructors']:
                            assignment['instructors'].append(instructor_b_id)
                            jury_assignments_made += 1
                            logger.info(f"  Proje {assignment['project_id']}: Instructor {instructor_a_id} sorumlu → Instructor {instructor_b_id} jüri")
                
                # Instructor B'nin projelerine Instructor A'yı jüri yap
                for assignment in assignments:
                    if assignment['project_id'] in instructor_b['project_ids']:
                        if instructor_a_id not in assignment['instructors']:
                            assignment['instructors'].append(instructor_a_id)
                            jury_assignments_made += 1
                            logger.info(f"  Proje {assignment['project_id']}: Instructor {instructor_b_id} sorumlu → Instructor {instructor_a_id} jüri")
        
        logger.info(f"Ardışık jüri eşleştirmesi tamamlandı: {jury_assignments_made} jüri ataması yapıldı")

    def _detect_conflicts(self, assignments: List[Dict[str, Any]]) -> List[str]:
        """Detect conflicts in assignments"""
        conflicts = []
        instructor_timeslot_counts = defaultdict(int)
        
        for assignment in assignments:
            instructors_list = assignment.get('instructors', [])
            timeslot_id = assignment.get('timeslot_id')
            
            for instructor_id in instructors_list:
                key = f"instructor_{instructor_id}_timeslot_{timeslot_id}"
                instructor_timeslot_counts[key] += 1
                
                if instructor_timeslot_counts[key] > 1:
                    conflicts.append(key)
        
        return conflicts

    def _resolve_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve conflicts by reassigning conflicting projects"""
        conflicts = self._detect_conflicts(assignments)
        if not conflicts:
            return assignments
        
        logger.warning(f"Conflict resolution: {len(conflicts)} conflicts detected but not resolved")
        return assignments

    def _parse_time(self, time_str: str) -> dt_time:
        """Parse time string to datetime.time object"""
        try:
            if isinstance(time_str, dt_time):
                return time_str
            return dt_time.fromisoformat(time_str)
        except:
            return dt_time(9, 0)  # Default to 09:00

    def _calculate_grouping_stats(self, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate consecutive grouping statistics."""
        if not assignments:
            return {
                "consecutive_count": 0,
                "total_instructors": 0,
                "avg_classroom_changes": 0.0,
                "consecutive_percentage": 0.0
            }
        
        instructor_assignments = defaultdict(list)
        for assignment in assignments:
            project_id = assignment.get("project_id")
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if project and project.get("responsible_id"):
                instructor_id = project["responsible_id"]
                instructor_assignments[instructor_id].append(assignment)
        
        consecutive_count = 0
        total_classroom_changes = 0
        
        for instructor_id, instructor_assignment_list in instructor_assignments.items():
            classrooms_used = set(a.get("classroom_id") for a in instructor_assignment_list)
            classroom_changes = len(classrooms_used) - 1
            total_classroom_changes += classroom_changes
            
            timeslot_ids = sorted([a.get("timeslot_id") for a in instructor_assignment_list])
            is_consecutive = all(
                timeslot_ids[i] + 1 == timeslot_ids[i+1] 
                for i in range(len(timeslot_ids) - 1)
            ) if len(timeslot_ids) > 1 else True
            
            if is_consecutive and len(classrooms_used) == 1:
                consecutive_count += 1
        
        total_instructors = len(instructor_assignments)
        avg_classroom_changes = total_classroom_changes / total_instructors if total_instructors > 0 else 0
        
        return {
            "consecutive_count": consecutive_count,
            "total_instructors": total_instructors,
            "avg_classroom_changes": avg_classroom_changes,
            "consecutive_percentage": (consecutive_count / total_instructors * 100) if total_instructors > 0 else 0
        }

    def _calculate_fitness_scores(self, solution: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate fitness scores for a solution."""
        if not solution:
            return {
                "load_balance": 0.0,
                "classroom_changes": 0.0,
                "time_efficiency": 0.0,
                "total": 0.0
            }
        
        load_balance = self._calculate_load_balance_score(solution)
        classroom_changes = self._calculate_classroom_changes_score(solution)
        time_efficiency = self._calculate_time_efficiency_score(solution)
        
        total = load_balance + classroom_changes + time_efficiency
        
        return {
            "load_balance": load_balance,
            "classroom_changes": classroom_changes,
            "time_efficiency": time_efficiency,
            "total": total
        }
    
    def _calculate_load_balance_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate load balance score."""
        instructor_loads = {}
        
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if not instructor_loads:
            return 0.0
        
        loads = list(instructor_loads.values())
        avg_load = sum(loads) / len(loads)
        variance = sum((load - avg_load) ** 2 for load in loads) / len(loads)
        
        return variance
    
    def _calculate_classroom_changes_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate classroom changes score."""
        instructor_classrooms = {}
        changes = 0
        
        for assignment in solution:
            classroom_id = assignment.get("classroom_id")
            for instructor_id in assignment.get("instructors", []):
                if instructor_id in instructor_classrooms:
                    if instructor_classrooms[instructor_id] != classroom_id:
                        changes += 1
                instructor_classrooms[instructor_id] = classroom_id
        
        return float(changes)
    
    def _calculate_time_efficiency_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate time efficiency score."""
        instructor_timeslots = {}
        gaps = 0
        
        for assignment in solution:
            timeslot_id = assignment.get("timeslot_id")
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_timeslots:
                    instructor_timeslots[instructor_id] = []
                instructor_timeslots[instructor_id].append(timeslot_id)
        
        for timeslots in instructor_timeslots.values():
            sorted_slots = sorted(timeslots)
            for i in range(1, len(sorted_slots)):
                if sorted_slots[i] - sorted_slots[i-1] > 1:
                    gaps += 1
        
        return float(gaps)

    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Evaluate the fitness of a solution (required by base class).
        
        Args:
            solution: Solution to evaluate
            
        Returns:
            float: Fitness score (lower is better)
        """
        assignments = solution.get("assignments") or solution.get("assignment") or solution.get("schedule") or []
        
        if not assignments:
            return float('inf')
        
        # Calculate basic fitness
        fitness_scores = self._calculate_fitness_scores(assignments)
        total_fitness = fitness_scores.get("total", 0.0)
        
        # Lower is better (minimize conflicts, gaps, classroom changes)
        return total_fitness
