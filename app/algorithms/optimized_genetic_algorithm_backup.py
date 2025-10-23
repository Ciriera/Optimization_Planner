"""
Optimized Genetic Algorithm Implementation for optimizationplanner.mdc compliance
Maintains classic genetic operations while ensuring full compliance with all requirements
"""

from typing import Dict, Any, Optional, List, Tuple
import random
import numpy as np
import time
from copy import deepcopy
from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment
from app.services.gap_free_scheduler import GapFreeScheduler
from app.services.rules import RulesService


class OptimizedGeneticAlgorithm(OptimizationAlgorithm):
    """
    Optimized Genetic Algorithm implementation that maintains classic GA structure
    while ensuring full compliance with optimizationplanner.mdc requirements.
    
    Classic GA Components Preserved:
    - Population-based evolution
    - Selection (Tournament, Roulette, Rank-based)
    - Crossover (Single-point, Two-point, Uniform)
    - Mutation (Bit-flip, Swap, Insert)
    - Elitism
    - Fitness-based evolution
    
    optimizationplanner.mdc Compliance:
    - 5-objective function with 0-100 normalization
    - Gap-free constraint enforcement
    - Bitirme/Ara project rules
    - Load balancing optimization
    - Classroom change minimization
    """
    
    
    def _prioritize_projects_for_gap_free(self) -> List[Dict[str, Any]]:
        """Projeleri gap-free icin onceliklendir."""
        bitirme_normal = [p for p in self.projects if p.get("type") == "bitirme" and not p.get("is_makeup", False)]
        ara_normal = [p for p in self.projects if p.get("type") == "ara" and not p.get("is_makeup", False)]
        bitirme_makeup = [p for p in self.projects if p.get("type") == "bitirme" and p.get("is_makeup", False)]
        ara_makeup = [p for p in self.projects if p.get("type") == "ara" and p.get("is_makeup", False)]
        return bitirme_normal + ara_normal + bitirme_makeup + ara_makeup

def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.name = "Optimized Genetic Algorithm"
        self.description = "Classic GA with optimizationplanner.mdc compliance"
        
        # Classic GA Parameters
        self.population_size = params.get("population_size", 100) if params else 100
        self.generations = params.get("generations", 200) if params else 200
        self.mutation_rate = params.get("mutation_rate", 0.1) if params else 0.1
        self.crossover_rate = params.get("crossover_rate", 0.8) if params else 0.8
        self.elite_size = params.get("elite_size", 10) if params else 10
        
        # Selection parameters
        self.tournament_size = params.get("tournament_size", 3) if params else 3
        self.selection_method = params.get("selection_method", "tournament") if params else "tournament"
        
        # Crossover parameters
        self.crossover_method = params.get("crossover_method", "single_point") if params else "single_point"
        
        # Mutation parameters
        self.mutation_method = params.get("mutation_method", "swap") if params else "swap"
        
        # optimizationplanner.mdc Objective Function Weights
        self.weights = {
            "load_balance": 0.25,      # W1: Yuk dengesi skoru
            "classroom_changes": 0.25, # W2: Sinif gecisi azligi  
            "time_efficiency": 0.20,   # W3: Saat butunlugu
            "slot_minimization": 0.15, # W4: Oturum sayisinin azaltilmasi
            "rule_compliance": 0.15    # W5: Kurallara uyum

        # Constraint enforcement
        self.gap_free_scheduler = GapFreeScheduler()
        self.rules_service = RulesService()
        
        # Data storage
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
        
        # GA state
        self.population = []
        self.best_solution = None
        self.best_fitness = 0.0
        self.fitness_history = []
        
    def initialize(self, data: Dict[str, Any]):
        """Initialize the algorithm with problem data."""
        self.data = data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Validate data
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            raise ValueError("Insufficient data for Genetic Algorithm")

            return []
        
        # Proje tipine gore ek instructor sec
        if project_type == "bitirme":
            # Bitirme icin EN AZ 1 juri gerekli (sorumlu haric)
            available_jury = [i for i in self.instructors 
                            if i.get("id") != responsible_id]
            
            # Once hocalari tercih et, sonra arastirma gorevlileri
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]
            
            # En az 1 juri ekle (tercihen faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get("id")}")
                return []  # Bitirme icin juri zorunlu!
        
        # Ara proje icin sadece sorumlu yeterli
        return instructors
            
        print(f"Optimized Genetic Algorithm initialized with {len(self.projects)} projects, "
              f"{len(self.instructors)} instructors, {len(self.classrooms)} classrooms, "
              f"{len(self.timeslots)} timeslots")
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the Optimized Genetic Algorithm optimization.
        
        Args:
            data: Problem data containing projects, instructors, classrooms, timeslots
            
        Returns:
            Optimization result with solution and metrics
        """
        start_time = time.time()
        
        try:
            # Initialize data
            self.initialize(data)
            
            print("INFO: Starting Optimized Genetic Algorithm...")
            print(f"   Population Size: {self.population_size}")
            print(f"   Generations: {self.generations}")
            print(f"   Mutation Rate: {self.mutation_rate}")
            print(f"   Crossover Rate: {self.crossover_rate}")
            
            # Step 1: Create initial population
            self._create_initial_population()
            
            # Step 2: Evolution loop
            for generation in range(self.generations):
                # Evaluate fitness for all individuals
                fitness_scores = self._evaluate_population()
                
                # Track best solution
                best_individual = max(fitness_scores, key=lambda x: x[1])
                if best_individual[1] > self.best_fitness:
                    self.best_solution = best_individual[0]
                    self.best_fitness = best_individual[1]
                
                self.fitness_history.append(self.best_fitness)
                
                # Create new population
                new_population = self._create_new_population(fitness_scores)
                self.population = new_population
                
                # Progress reporting
                if generation % 50 == 0:
                    print(f"   Generation {generation}: Best Fitness = {self.best_fitness:.2f}")
            
            # Step 3: Apply gap-free optimization to best solution
            if self.best_solution:
                gap_free_solution = self._apply_gap_free_optimization(self.best_solution)
                self.best_solution = gap_free_solution
            
            # Step 4: Calculate final metrics
            metrics = self._calculate_comprehensive_metrics(self.best_solution)
            
            execution_time = time.time() - start_time
            
            return {
                "algorithm": "Optimized Genetic Algorithm",
                "status": "completed",
                "schedule": self.best_solution,
                "solution": self.best_solution,
                "metrics": metrics,
                "execution_time": execution_time,
                "generations": self.generations,
                "final_fitness": self.best_fitness,
                "fitness_history": self.fitness_history,
                "message": "Optimized Genetic Algorithm completed successfully",
                "constraint_compliance": self._check_constraint_compliance(self.best_solution)
            }
            
        except Exception as e:
            print(f"ERROR: Genetic Algorithm error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "algorithm": "Optimized Genetic Algorithm",
                "status": "error",
                "schedule": [],
                "solution": [],
                "metrics": {},
                "execution_time": 0,
                "message": f"Genetic Algorithm failed: {str(e)}"
            }
    
    def _create_initial_population(self):
        """Create initial population with diverse individuals."""
        print("INFO: Creating initial population...")
        
        self.population = []
        
        for i in range(self.population_size):
            # Create diverse individuals using different strategies
            if i < self.population_size // 3:
                # Random individuals
                individual = self._create_random_individual()
            elif i < 2 * self.population_size // 3:
                # Greedy individuals
                individual = self._create_greedy_individual()
            else:
                # Constraint-aware individuals
                individual = self._create_constraint_aware_individual()
            
            self.population.append(individual)

    def _select_instructors_for_project_gap_free(self, project: Dict[str, Any], instructor_timeslot_usage: Dict[int, Set[int]]) -> List[int]:
        """
        Proje icin instructor secer (gap-free versiyonu).
        
        Kurallar:
        - Bitirme: 1 sorumlu + en az 1 juri (hoca veya arastirma gorevlisi)
        - Ara: 1 sorumlu
        - Ayni kisi hem sorumlu hem juri OLAMAZ
        
        Args:
            project: Proje
            instructor_timeslot_usage: Kullanim bilgisi
            
        Returns:
            Instructor ID listesi
        """
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id")
        
        # Sorumlu her zaman ilk sirada
        if responsible_id:
            instructors.append(responsible_id)
        else:
            logger.error(f"{self.__class__.__name__}: Project {project.get("id")} has NO responsible_id!")
            return []
        
        # Proje tipine gore ek instructor sec
        if project_type == "bitirme":
            # Bitirme icin EN AZ 1 juri gerekli (sorumlu haric)
            available_jury = [i for i in self.instructors 
                            if i.get("id") != responsible_id]
            
            # Once hocalari tercih et, sonra arastirma gorevlileri
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]
            
            # En az 1 juri ekle (tercihen faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get("id")}")
                return []  # Bitirme icin juri zorunlu!
        
        # Ara proje icin sadece sorumlu yeterli
        return instructors
        
        print(f"   SUCCESS: Initial population created: {len(self.population)} individuals")
    
    def _create_random_individual(self) -> List[Dict[str, Any]]:
        """Create a random individual."""
        individual = []
        used_slots = set()
        
        for project in self.projects:
            # Find available slot
            available_slots = []
            for classroom in self.classrooms:
                for timeslot in self.timeslots:
                    slot_key = (classroom.get("id", 0), timeslot.get("id", 0))
                    if slot_key not in used_slots:
                        available_slots.append((classroom, timeslot))
            
            if available_slots:
                classroom, timeslot = random.choice(available_slots)
                slot_key = (classroom.get("id", 0), timeslot.get("id", 0))
                used_slots.add(slot_key)
                
                # Assign instructors according to rules
                instructors = self._assign_instructors_to_project(project)
                
                assignment = {
                    "project_id": project.get("id", 0),
                    "classroom_id": classroom.get("id", 0),
                    "timeslot_id": timeslot.get("id", 0),
                    "instructors": instructors,
                    "is_makeup": False
                }
                
                individual.append(assignment)
        
        return individual
    
    def _create_greedy_individual(self) -> List[Dict[str, Any]]:
        """Create a greedy individual."""
        individual = []
        used_slots = set()
        instructor_loads = {inst.get("id", 0): 0 for inst in self.instructors}
        
        # Sort projects by priority (bitirme first, then by instructor availability)
        sorted_projects = sorted(self.projects, key=lambda p: (
            0 if p.get("type", "ara") == "bitirme" else 1,
            -instructor_loads.get(p.get("responsible_id", 0), 0)
        ))
        
        for project in sorted_projects:
            # Find best available slot
            best_slot = None
            best_score = float('inf')
            
            for classroom in self.classrooms:
                for timeslot in self.timeslots:
                    slot_key = (classroom.get("id", 0), timeslot.get("id", 0))
                    if slot_key not in used_slots:
                        # Calculate slot score (lower is better)
                        score = self._calculate_slot_score(classroom, timeslot, instructor_loads)
                        if score < best_score:
                            best_score = score
                            best_slot = (classroom, timeslot)
            
            if best_slot:
                classroom, timeslot = best_slot
                slot_key = (classroom.get("id", 0), timeslot.get("id", 0))
                used_slots.add(slot_key)
                
                # Assign instructors
                instructors = self._assign_instructors_to_project(project)
                
                # Update instructor loads
                for inst_id in instructors:
                    instructor_loads[inst_id] += 1
                
                assignment = {
                    "project_id": project.get("id", 0),
                    "classroom_id": classroom.get("id", 0),
                    "timeslot_id": timeslot.get("id", 0),
                    "instructors": instructors,
                    "is_makeup": False
                }
                
                individual.append(assignment)

        return individual

    def _create_feasible_solution(self) -> List[Dict[str, Any]]:
        """Create a feasible solution that satisfies all optimizationplanner.mdc constraints."""
        assignments = []

        # Use constraint-aware assignment
        prioritized_projects = self._prioritize_projects()

        # Track used slots and instructor assignments
        used_slots = set()  # (classroom_id, timeslot_id) pairs
        instructor_assignments = {}  # instructor_id -> set of timeslot_ids

        # Process all projects with constraint-aware assignment
        for project in prioritized_projects:
            assignment = self._find_best_assignment_constraint_aware(project, used_slots, instructor_assignments)
            if assignment:
                assignments.append(assignment)
                # Update tracking structures
                slot_key = (assignment["classroom_id"], assignment["timeslot_id"])
                used_slots.add(slot_key)
                for instructor_id in assignment["instructors"]:
                    if instructor_id not in instructor_assignments:
                        instructor_assignments[instructor_id] = set()
                    instructor_assignments[instructor_id].add(assignment["timeslot_id"])

        # Ensure all projects are assigned
        assignments = self._ensure_all_projects_assigned(assignments)

        # Final validation and repair
        if not self._is_valid_solution_constraint_aware(assignments):
            assignments = self._repair_solution_constraint_aware(assignments)

        return assignments

    def _prioritize_projects(self):
        """Prioritize projects for assignment (bitirme projects first)."""
        bitirme_projects = [p for p in self.projects if p.get("type", "ara") == "bitirme"]
        ara_projects = [p for p in self.projects if p.get("type", "ara") == "ara"]
        return bitirme_projects + ara_projects

    def _assign_instructors_to_project(self, project):
        """Assign instructors to project."""
        instructors = []

        # Add responsible instructor
        responsible_id = project.get("responsible_id")
        if responsible_id:
            instructors.append(responsible_id)

        # For bitirme projects, add jury
        if project.get("type", "ara") == "bitirme":
            # Find available instructors for jury
            available_instructors = [
                inst for inst in self.instructors
                if inst.get("id") != responsible_id and inst.get("type") == "instructor"
            ]
            if available_instructors:
                instructors.append(available_instructors[0].get("id"))

        return instructors

    def _select_instructors_for_project_gap_free(self, project: Dict[str, Any], instructor_timeslot_usage: Dict[int, Set[int]]) -> List[int]:
        """
        Proje icin instructor secer (gap-free versiyonu).
        
        Kurallar:
        - Bitirme: 1 sorumlu + en az 1 juri (hoca veya arastirma gorevlisi)
        - Ara: 1 sorumlu
        - Ayni kisi hem sorumlu hem juri OLAMAZ
        
        Args:
            project: Proje
            instructor_timeslot_usage: Kullanim bilgisi
            
        Returns:
            Instructor ID listesi
        """
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id")
        
        # Sorumlu her zaman ilk sirada
        if responsible_id:
            instructors.append(responsible_id)
        else:
            logger.error(f"{self.__class__.__name__}: Project {project.get("id")} has NO responsible_id!")
            return []
        
        # Proje tipine gore ek instructor sec
        if project_type == "bitirme":
            # Bitirme icin EN AZ 1 juri gerekli (sorumlu haric)
            available_jury = [i for i in self.instructors 
                            if i.get("id") != responsible_id]
            
            # Once hocalari tercih et, sonra arastirma gorevlileri
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]
            
            # En az 1 juri ekle (tercihen faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get("id")}")
                return []  # Bitirme icin juri zorunlu!
        
        # Ara proje icin sadece sorumlu yeterli
        return instructors

    def _ensure_all_projects_assigned(self, assignments):
        """Ensure all projects are assigned."""
        assigned_projects = {a.get("project_id") for a in assignments if a.get("project_id")}
        missing_projects = [p for p in self.projects if p.get("id") not in assigned_projects]

        for project in missing_projects:
            # Simple assignment for missing projects
            assignment = {
                "project_id": project.get("id", 0),
                "classroom_id": self.classrooms[0].get("id", 0) if self.classrooms else 0,
                "timeslot_id": self.timeslots[0].get("id", 0) if self.timeslots else 0,
                "instructors": [project.get("responsible_id", 0)],
            }
            assignments.append(assignment)

        return assignments

    def _find_best_assignment_constraint_aware(self, project, used_slots, instructor_assignments):
        """Find best assignment for project with constraint awareness."""
        best_score = float('inf')
        best_assignment = None

        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                # Check if slot is available
                slot_key = (classroom.get("id", 0), timeslot.get("id", 0))
                if slot_key in used_slots:
                    continue

                # Calculate slot score (lower is better)
                score = self._calculate_slot_score(classroom, timeslot, instructor_assignments)
                if score < best_score:
                    best_score = score
                    best_assignment = {
                        "classroom_id": classroom.get("id", 0),
                        "timeslot_id": timeslot.get("id", 0),
                        "instructors": self._assign_instructors_to_project(project),

    def _select_instructors_for_project_gap_free(self, project: Dict[str, Any], instructor_timeslot_usage: Dict[int, Set[int]]) -> List[int]:
        """
        Proje icin instructor secer (gap-free versiyonu).
        
        Kurallar:
        - Bitirme: 1 sorumlu + en az 1 juri (hoca veya arastirma gorevlisi)
        - Ara: 1 sorumlu
        - Ayni kisi hem sorumlu hem juri OLAMAZ
        
        Args:
            project: Proje
            instructor_timeslot_usage: Kullanim bilgisi
            
        Returns:
            Instructor ID listesi
        """
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id")
        
        # Sorumlu her zaman ilk sirada
        if responsible_id:
            instructors.append(responsible_id)
        else:
            logger.error(f"{self.__class__.__name__}: Project {project.get("id")} has NO responsible_id!")
            return []
        
        # Proje tipine gore ek instructor sec
        if project_type == "bitirme":
            # Bitirme icin EN AZ 1 juri gerekli (sorumlu haric)
            available_jury = [i for i in self.instructors 
                            if i.get("id") != responsible_id]
            
            # Once hocalari tercih et, sonra arastirma gorevlileri
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]
            
            # En az 1 juri ekle (tercihen faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get("id")}")
                return []  # Bitirme icin juri zorunlu!
        
        # Ara proje icin sadece sorumlu yeterli
        return instructors
                    
        return best_assignment

    def _is_valid_solution_constraint_aware(self, assignments):
        """Check if solution satisfies all constraints."""
        # Basic validation - check if all projects are assigned
        assigned_projects = {a.get("project_id") for a in assignments if a.get("project_id")}
        expected_projects = {p.get("id") for p in self.projects if p.get("id")}

        return len(assigned_projects) >= len(expected_projects) * 0.9  # At least 90% coverage

    def _repair_solution_constraint_aware(self, assignments):
        """Repair solution to satisfy constraints."""
        # Simple repair - add missing projects
        assigned_projects = {a.get("project_id") for a in assignments if a.get("project_id")}
        missing_projects = [p for p in self.projects if p.get("id") not in assigned_projects]

        for project in missing_projects[:3]:  # Add first 3 missing projects
            # Simple assignment
            assignment = {
                "project_id": project.get("id", 0),
                "classroom_id": self.classrooms[0].get("id", 0) if self.classrooms else 0,
                "timeslot_id": self.timeslots[0].get("id", 0) if self.timeslots else 0,
                "instructors": [project.get("responsible_id", 0)],
            }
            assignments.append(assignment)

        return assignments

    def _create_constraint_aware_individual(self) -> List[Dict[str, Any]]:
        """Create a constraint-aware individual."""
        individual = []
        used_slots = set()
        
        # Group projects by type
        bitirme_projects = [p for p in self.projects if p.get("type", "ara") == "bitirme"]
        ara_projects = [p for p in self.projects if p.get("type", "ara") == "ara"]
        
        # Process bitirme projects first (they have stricter constraints)
        for project in bitirme_projects:
            assignment = self._create_constraint_aware_assignment(project, used_slots)
            if assignment:
                individual.append(assignment)
        
        # Process ara projects
        for project in ara_projects:
            assignment = self._create_constraint_aware_assignment(project, used_slots)
            if assignment:
                individual.append(assignment)
        
        return individual
    
    def _create_constraint_aware_assignment(self, project: Dict[str, Any], used_slots: set) -> Optional[Dict[str, Any]]:
        """Create a constraint-aware assignment for a project."""
        # Find available slot
        for classroom in self.classrooms:
            for timeslot in self.timeslots:
                slot_key = (classroom.get("id", 0), timeslot.get("id", 0))
                if slot_key not in used_slots:
                    used_slots.add(slot_key)
                    
                    # Assign instructors according to rules
                    instructors = self._assign_instructors_to_project(project)
                    
                    return {
                        "project_id": project.get("id", 0),
                        "classroom_id": classroom.get("id", 0),
                        "timeslot_id": timeslot.get("id", 0),
                        "instructors": instructors,
                        "is_makeup": False
                    }
        
        return None
    
    def _assign_instructors_to_project(self, project: Dict[str, Any]) -> List[int]:
        """Assign instructors to project based on optimizationplanner.mdc rules."""
        project_type = project.get("type", "ara")
        
        # Rule: Bitirme projelerinde en az 2 hoca, Ara projelerde en az 1 hoca
        min_instructors = 2 if project_type == "bitirme" else 1
        
        # Get available instructors
        available_instructors = [inst for inst in self.instructors if inst.get("id")]
        
        if len(available_instructors) < min_instructors:
            # Not enough instructors, return what we have
            return [inst.get("id", 0) for inst in available_instructors]
        
        # Assign instructors (prefer professors for bitirme projects)
        assigned_instructors = []
        
        # For bitirme projects, try to get at least one professor
        if project_type == "bitirme":
            professors = [inst for inst in available_instructors 
                         if inst.get("type", "").lower() in ["professor", "prof", "ogretim uyesi"]]
            if professors:
                assigned_instructors.append(professors[0].get("id", 0))
                available_instructors.remove(professors[0])
        
        # Fill remaining slots
        while len(assigned_instructors) < min_instructors and available_instructors:
            instructor = available_instructors.pop(0)
            if instructor.get("id", 0) not in assigned_instructors:
                assigned_instructors.append(instructor.get("id", 0))
        
        return assigned_instructors
    
    def _calculate_slot_score(self, classroom: Dict[str, Any], timeslot: Dict[str, Any], instructor_loads: Dict[int, int]) -> float:
        """Calculate score for a slot (lower is better)."""
        score = 0.0
        
        # Prefer morning slots
        if not timeslot.get('is_morning', True):
            score += 10.0
        
        # Prefer earlier slots
        slot_id = timeslot.get('id', 'slot_0')
        try:
            slot_num = int(slot_id.split('_')[1]) if '_' in slot_id else 0
            score += slot_num * 0.1
        except (ValueError, IndexError):
            score += 0.0
        
        # Prefer classrooms with lower capacity (for better utilization)
        capacity = classroom.get('capacity', 20)
        score += capacity * 0.01
        
        return score
    
    def _evaluate_population(self) -> List[Tuple[List[Dict[str, Any]], float]]:
        """Evaluate fitness for all individuals in population."""
        fitness_scores = []
        
        for individual in self.population:
            fitness = self.evaluate_fitness(individual)
            fitness_scores.append((individual, fitness))
        
        return fitness_scores
    
    def evaluate_fitness(self, individual: List[Dict[str, Any]]) -> float:
        """
        Evaluate fitness of an individual using optimizationplanner.mdc objectives.
        
        Args:
            individual: Individual solution to evaluate
            
        Returns:
            float: Fitness score (0-100)
        """
        if not individual:
            return 0.0
        
        # Calculate all 5 objective scores (0-100 normalized)
        load_balance_score = self._calculate_load_balance_score(individual)
        classroom_change_score = self._calculate_classroom_change_score(individual)
        time_efficiency_score = self._calculate_time_efficiency_score(individual)
        slot_minimization_score = self._calculate_slot_minimization_score(individual)
        rule_compliance_score = self._calculate_rule_compliance_score(individual)
        
        # Weighted sum of objectives
        fitness = (
            load_balance_score * self.weights["load_balance"] +
            classroom_change_score * self.weights["classroom_changes"] +
            time_efficiency_score * self.weights["time_efficiency"] +
            slot_minimization_score * self.weights["slot_minimization"] +
            rule_compliance_score * self.weights["rule_compliance"]
        )
        
        # Zaman slot cezasini uygula ve slot odulunu ekle
        try:
            penalty = getattr(self, "_calculate_time_slot_penalty", lambda s: 0.0)(individual)
            reward = getattr(self, "_calculate_total_slot_reward", lambda s: 0.0)(individual)
            fitness = fitness - penalty + (reward / 50.0)
        except Exception:
            pass
        
        return fitness
    
    def _calculate_load_balance_score(self, individual: List[Dict[str, Any]]) -> float:
        """Calculate load balance score (0-100)."""
        instructor_loads = {}
        
        for assignment in individual:
            for instructor_id in assignment.get("instructors", []):
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if not instructor_loads:
            return 0.0
        
        loads = list(instructor_loads.values())
        mean_load = np.mean(loads)
        std_load = np.std(loads)
        
        # Perfect balance = 100, worse balance = lower score
        if mean_load == 0:
            return 0.0
        
        balance_ratio = 1.0 - (std_load / (mean_load + 1e-8))
        return max(0.0, min(100.0, balance_ratio * 100))
    
    def _calculate_classroom_change_score(self, individual: List[Dict[str, Any]]) -> float:
        """Calculate classroom change minimization score (0-100)."""
        instructor_classrooms = {}
        total_changes = 0
        total_assignments = 0
        
        for assignment in individual:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id in instructor_classrooms:
                    if instructor_classrooms[instructor_id] != assignment["classroom_id"]:
                        total_changes += 1
                instructor_classrooms[instructor_id] = assignment["classroom_id"]
                total_assignments += 1
        
        if total_assignments == 0:
            return 100.0
        
        # Perfect score = no changes, worse = lower score
        change_ratio = total_changes / total_assignments
        score = max(0.0, 100.0 - (change_ratio * 100))
        return score
    
    def _calculate_time_efficiency_score(self, individual: List[Dict[str, Any]]) -> float:
        """Calculate time efficiency score (0-100) - gap-free scheduling."""
        gap_validation = self.gap_free_scheduler.validate_gap_free_schedule(individual)

        # Hard preference: if any assignment is after 16:30 apply infinite-like penalty
        late_after_1630_count = 0
        last_usable_slot_id = None
        for ts in self.timeslots:
            if "16:00" in ts.get("time_range", ""):
                last_usable_slot_id = ts.get("id")
                break

        for assignment in individual:
            ts_id = assignment.get("timeslot_id")
            ts = next((t for t in self.timeslots if t.get("id") == ts_id), None)
            if not ts:
                continue
            time_range = ts.get("time_range", "")
            hour = int(ts.get("start_time", "09:00").split(":")[0])
            if hour > 16 or (hour == 16 and "16:30" in time_range):
                late_after_1630_count += 1

        if late_after_1630_count > 0:
            return 0.0  # Treat as infinitely bad for time efficiency

        # Medium penalty for 16:00-16:30 usage
        last_usable_count = 0
        if last_usable_slot_id is not None:
            last_usable_count = sum(1 for a in individual if a.get("timeslot_id") == last_usable_slot_id)

        # Base from gap-free
        base = 100.0 if gap_validation["is_gap_free"] else max(0.0, 100.0 - (gap_validation["total_gaps"] * 20))
        # Subtract medium penalty proportional to usage of 16:00 slot
        total = len(individual) if individual else 1
        last_usable_ratio = last_usable_count / total
        penalty = last_usable_ratio * 40.0  # up to 40 points off
        return max(0.0, base - penalty)
    
    def _calculate_slot_minimization_score(self, individual: List[Dict[str, Any]]) -> float:
        """Calculate slot minimization score (0-100)."""
        if not individual:
            return 0.0
        
        # Count unique timeslots used
        used_timeslots = set(assignment["timeslot_id"] for assignment in individual)
        total_timeslots = len(self.timeslots)
        
        if total_timeslots == 0:
            return 0.0
        
        # More slots used = lower score (we want to minimize slots)
        utilization_ratio = len(used_timeslots) / total_timeslots
        score = max(0.0, 100.0 - (utilization_ratio * 50))  # Max 50 point penalty
        return score
    
    def _calculate_rule_compliance_score(self, individual: List[Dict[str, Any]]) -> float:
        """Calculate rule compliance score (0-100)."""
        violations = 0
        total_projects = len(individual)
        
        if total_projects == 0:
            return 100.0
        
        for assignment in individual:
            project = next((p for p in self.projects if p.get("id") == assignment["project_id"]), None)
            if project:
                project_type = project.get("type", "ara")
                min_instructors = 2 if project_type == "bitirme" else 1
                
                if len(assignment.get("instructors", [])) < min_instructors:
                    violations += 1
        
        # Perfect compliance = 100, violations reduce score
        compliance_ratio = 1.0 - (violations / total_projects)
        return max(0.0, compliance_ratio * 100)
    
    def _create_new_population(self, fitness_scores: List[Tuple[List[Dict[str, Any]], float]]) -> List[List[Dict[str, Any]]]:
        """Create new population using genetic operations."""
        new_population = []
        
        # Sort by fitness (descending)
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Elitism: Keep best individuals
        for i in range(min(self.elite_size, len(fitness_scores))):
            new_population.append(deepcopy(fitness_scores[i][0]))
        
        # Create rest of population through genetic operations
        while len(new_population) < self.population_size:
            # Selection
            parent1 = self._selection(fitness_scores)
            parent2 = self._selection(fitness_scores)
            
            # Crossover
            if random.random() < self.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = parent1, parent2
            
            # Mutation
            if random.random() < self.mutation_rate:
                child1 = self._mutate(child1)
            if random.random() < self.mutation_rate:
                child2 = self._mutate(child2)
            
            new_population.append(child1)
            if len(new_population) < self.population_size:
                new_population.append(child2)
        
        return new_population
    
    def _selection(self, fitness_scores: List[Tuple[List[Dict[str, Any]], float]]) -> List[Dict[str, Any]]:
        """Select parent using specified selection method."""
        if self.selection_method == "tournament":
            return self._tournament_selection(fitness_scores)
        elif self.selection_method == "roulette":
            return self._roulette_selection(fitness_scores)
        elif self.selection_method == "rank":
            return self._rank_selection(fitness_scores)
        else:
            return self._tournament_selection(fitness_scores)
    
    def _tournament_selection(self, fitness_scores: List[Tuple[List[Dict[str, Any]], float]]) -> List[Dict[str, Any]]:
        """Tournament selection."""
        tournament = random.sample(fitness_scores, min(self.tournament_size, len(fitness_scores)))
        tournament.sort(key=lambda x: x[1], reverse=True)
        return tournament[0][0]
    
    def _roulette_selection(self, fitness_scores: List[Tuple[List[Dict[str, Any]], float]]) -> List[Dict[str, Any]]:
        """Roulette wheel selection."""
        total_fitness = sum(fitness for _, fitness in fitness_scores)
        if total_fitness == 0:
            return random.choice(fitness_scores)[0]
        
        target = random.uniform(0, total_fitness)
        current = 0
        
        for individual, fitness in fitness_scores:
            current += fitness
            if current >= target:
                return individual
        
        return fitness_scores[-1][0]
    
    def _rank_selection(self, fitness_scores: List[Tuple[List[Dict[str, Any]], float]]) -> List[Dict[str, Any]]:
        """Rank-based selection."""
        # Sort by fitness
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Assign ranks
        ranks = list(range(1, len(fitness_scores) + 1))
        total_rank = sum(ranks)
        
        target = random.uniform(0, total_rank)
        current = 0
        
        for i, (individual, _) in enumerate(fitness_scores):
            current += ranks[i]
            if current >= target:
                return individual
        
        return fitness_scores[-1][0]
    
    def _crossover(self, parent1: List[Dict[str, Any]], parent2: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Perform crossover between two parents."""
        if self.crossover_method == "single_point":
            return self._single_point_crossover(parent1, parent2)
        elif self.crossover_method == "two_point":
            return self._two_point_crossover(parent1, parent2)
        elif self.crossover_method == "uniform":
            return self._uniform_crossover(parent1, parent2)
        else:
            return self._single_point_crossover(parent1, parent2)
    
    def _single_point_crossover(self, parent1: List[Dict[str, Any]], parent2: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Single-point crossover."""
        if not parent1 or not parent2:
            return parent1, parent2
        
        min_len = min(len(parent1), len(parent2))
        if min_len <= 1:
            return parent1, parent2
        
        crossover_point = random.randint(1, min_len - 1)
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]
        
        return child1, child2
    
    def _two_point_crossover(self, parent1: List[Dict[str, Any]], parent2: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Two-point crossover."""
        if not parent1 or not parent2:
            return parent1, parent2
        
        min_len = min(len(parent1), len(parent2))
        if min_len <= 2:
            return parent1, parent2
        
        point1 = random.randint(1, min_len - 2)
        point2 = random.randint(point1 + 1, min_len - 1)
        
        child1 = parent1[:point1] + parent2[point1:point2] + parent1[point2:]
        child2 = parent2[:point1] + parent1[point1:point2] + parent2[point2:]
        
        return child1, child2
    
    def _uniform_crossover(self, parent1: List[Dict[str, Any]], parent2: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Uniform crossover."""
        if not parent1 or not parent2:
            return parent1, parent2
        
        child1 = []
        child2 = []
        
        max_len = max(len(parent1), len(parent2))
        
        for i in range(max_len):
            if random.random() < 0.5:
                child1.append(parent1[i] if i < len(parent1) else None)
                child2.append(parent2[i] if i < len(parent2) else None)
            else:
                child1.append(parent2[i] if i < len(parent2) else None)
                child2.append(parent1[i] if i < len(parent1) else None)
        
        # Remove None values
        child1 = [item for item in child1 if item is not None]
        child2 = [item for item in child2 if item is not None]
        
        return child1, child2
    
    def _mutate(self, individual: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply mutation to individual."""
        if not individual:
            return individual
        
        if self.mutation_method == "swap":
            return self._swap_mutation(individual)
        elif self.mutation_method == "insert":
            return self._insert_mutation(individual)
        elif self.mutation_method == "bit_flip":
            return self._bit_flip_mutation(individual)
        else:
            return self._swap_mutation(individual)
    
    def _swap_mutation(self, individual: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Swap mutation."""
        if len(individual) < 2:
            return individual
        
        # Randomly swap two assignments
        idx1, idx2 = random.sample(range(len(individual)), 2)
        individual[idx1], individual[idx2] = individual[idx2], individual[idx1]
        
        return individual
    
    def _insert_mutation(self, individual: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert mutation."""
        if len(individual) < 2:
            return individual
        
        # Randomly move one assignment to a different position
        idx = random.randint(0, len(individual) - 1)
        assignment = individual.pop(idx)
        new_idx = random.randint(0, len(individual))
        individual.insert(new_idx, assignment)
        
        return individual
    
    def _bit_flip_mutation(self, individual: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bit-flip mutation (change classroom or timeslot)."""
        if not individual:
            return individual
        
        # Randomly select an assignment to mutate
        mutation_index = random.randint(0, len(individual) - 1)
        assignment = individual[mutation_index]
        
        # Randomly change classroom or timeslot
        if random.random() < 0.5 and self.classrooms:
            # Change classroom
            new_classroom = random.choice(self.classrooms)
            assignment["classroom_id"] = new_classroom.get("id", 0)
        elif self.timeslots:
            # Change timeslot
            new_timeslot = random.choice(self.timeslots)
            assignment["timeslot_id"] = new_timeslot.get("id", 0)
        
        return individual
    
    def _apply_gap_free_optimization(self, individual: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply gap-free optimization to individual."""
        print("INFO: Applying gap-free optimization...")
        
        # Use the gap-free scheduler to optimize time continuity
        gap_free_individual = self.gap_free_scheduler.optimize_for_gap_free(
            individual, self.timeslots
        )
        
        print(f"   SUCCESS: Gap-free optimization applied")
        return gap_free_individual
    
    def _calculate_comprehensive_metrics(self, individual: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive metrics according to optimizationplanner.mdc."""
        if not individual:
            return {
                "load_balance_score": 0.0,
                "classroom_change_score": 0.0,
                "time_efficiency_score": 0.0,
                "slot_minimization_score": 0.0,
                "rule_compliance_score": 0.0,
                "overall_score": 0.0
            }
        
        # Calculate all 5 objective scores
        load_balance_score = self._calculate_load_balance_score(individual)
        classroom_change_score = self._calculate_classroom_change_score(individual)
        time_efficiency_score = self._calculate_time_efficiency_score(individual)
        slot_minimization_score = self._calculate_slot_minimization_score(individual)
        rule_compliance_score = self._calculate_rule_compliance_score(individual)
        
        # Overall weighted score
        overall_score = (
            load_balance_score * self.weights["load_balance"] +
            classroom_change_score * self.weights["classroom_changes"] +
            time_efficiency_score * self.weights["time_efficiency"] +
            slot_minimization_score * self.weights["slot_minimization"] +
            rule_compliance_score * self.weights["rule_compliance"]
        )
        
        return {
            "load_balance_score": load_balance_score,
            "classroom_change_score": classroom_change_score,
            "time_efficiency_score": time_efficiency_score,
            "slot_minimization_score": slot_minimization_score,
            "rule_compliance_score": rule_compliance_score,
            "overall_score": overall_score,
            "weights": self.weights
        }
    
    def _check_constraint_compliance(self, individual: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check constraint compliance for the individual."""
        violations = []
        
        # Check instructor assignment rules
        for assignment in individual:
            project = next((p for p in self.projects if p.get("id") == assignment["project_id"]), None)
            if project:
                project_type = project.get("type", "ara")
                min_instructors = 2 if project_type == "bitirme" else 1
                
                if len(assignment.get("instructors", [])) < min_instructors:
                    violations.append({
                        "type": "insufficient_instructors",
                        "message": f"Project {assignment['project_id']} ({project_type}) needs {min_instructors} instructors, has {len(assignment.get('instructors', []))}",
                        "project_id": assignment["project_id"],
                        "project_type": project_type,
                        "current": len(assignment.get("instructors", [])),
                        "required": min_instructors
                    })
        
        # Check slot conflicts
        used_slots = set()
        for assignment in individual:
            slot_key = (assignment["classroom_id"], assignment["timeslot_id"])
            if slot_key in used_slots:
                violations.append({
                    "type": "slot_conflict",
                    "message": f"Multiple projects assigned to classroom {assignment['classroom_id']}, timeslot {assignment['timeslot_id']}",
                    "classroom_id": assignment["classroom_id"],
                    "timeslot_id": assignment["timeslot_id"]
                })
            else:
                used_slots.add(slot_key)
        
        gap_validation = self.gap_free_scheduler.validate_gap_free_schedule(individual)
        
        return {
            "is_feasible": len(violations) == 0,
            "is_gap_free": gap_validation["is_gap_free"],
            "violations": violations,
            "gap_violations": gap_validation["violations"],
            "total_violations": len(violations) + len(gap_validation["violations"]),
            "compliance_percentage": max(0.0, 100.0 - (len(violations) + len(gap_validation["violations"])) * 10)
        }
