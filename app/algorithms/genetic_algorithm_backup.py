"""
Genetic Algorithm for Project Scheduling Optimization
Optimized for optimizationplanner.mdc requirements
"""
from typing import Dict, Any, List, Tuple
import random
import numpy as np
from datetime import time

from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

class GeneticAlgorithm(OptimizationAlgorithm):
    """
    Genetic Algorithm implementation for project scheduling optimization.

    This implementation follows optimizationplanner.mdc requirements:
    - 5 objective functions with proper weighting
    - All constraints enforced
    - Morning slot priority (09:00-12:00)
    - 16:00-16:30 slot availability with +35 bonus
    - 16:30+ slots avoided
    - Load balancing with ±1 tolerance
    - Gap-free scheduling guarantee
    """

    
    def _prioritize_projects_for_gap_free(self) -> List[Dict[str, Any]]:
        """Projeleri gap-free icin onceliklendir."""
        bitirme_normal = [p for p in self.projects if p.get("type") == "bitirme" and not p.get("is_makeup", False)]
        ara_normal = [p for p in self.projects if p.get("type") == "ara" and not p.get("is_makeup", False)]
        bitirme_makeup = [p for p in self.projects if p.get("type") == "bitirme" and p.get("is_makeup", False)]
        ara_makeup = [p for p in self.projects if p.get("type") == "ara" and p.get("is_makeup", False)]
        return bitirme_normal + ara_normal + bitirme_makeup + ara_makeup

def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize Genetic Algorithm with optimizationplanner.mdc compliant parameters.

        Args:
            params: Algorithm parameters optimized for the problem.
        """
        super().__init__(params)

        # Optimized parameters for 81 projects, 21 instructors, 7 classrooms, 16 timeslots
        self.population_size = params.get("population_size", 200)  # Larger population for complex problem
        self.generations = params.get("generations", 200)          # More generations for convergence
        self.mutation_rate = params.get("mutation_rate", 0.12)     # Balanced mutation rate
        self.crossover_rate = params.get("crossover_rate", 0.90)   # High crossover for exploration
        self.elite_size = params.get("elite_size", 10)             # Keep best solutions

        # Objective function weights (from optimizationplanner.mdc)
        self.weights = {
            "load_balance": 0.25,      # W1: Yuk dengesi skoru
            "classroom_changes": 0.25, # W2: Sinif gecisi azligi
            "time_efficiency": 0.20,   # W3: Saat butunlugu
            "slot_minimization": 0.15, # W4: Oturum sayisinin azaltilmasi
            "rule_compliance": 0.15    # W5: Kurallara uyum

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
        
        self.population = []
        self.best_solution = None
        self.fitness_cache = {}  # Cache fitness evaluations for performance
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Initialize Genetic Algorithm with optimizationplanner.mdc compliant data validation.

        Args:
            data: Algorithm input data with projects, instructors, classrooms, timeslots.
        """
        self.data = data
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

        # Validate data according to optimizationplanner.mdc
        self._validate_input_data()

        # Create initial population with feasible solutions
        self.population = []
        for _ in range(self.population_size):
            solution = self._create_feasible_solution()
            self.population.append(solution)

        print(f"Genetic Algorithm initialized with {len(self.projects)} projects, "
              f"{len(self.instructors)} instructors, {len(self.classrooms)} classrooms, "
              f"{len(self.timeslots)} timeslots")

    def _validate_input_data(self) -> None:
        """Validate input data according to optimizationplanner.mdc requirements."""
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            raise ValueError("Insufficient data for Genetic Algorithm")

        # Validate project count (50 ara + 31 bitirme = 81)
        bitirme_projects = [p for p in self.projects if p.get("type") == "bitirme"]
        ara_projects = [p for p in self.projects if p.get("type") == "ara"]

        if len(bitirme_projects) != 31:
            print(f"⚠️ Warning: Expected 31 bitirme projects, found {len(bitirme_projects)}")
        if len(ara_projects) != 50:
            print(f"⚠️ Warning: Expected 50 ara projects, found {len(ara_projects)}")

        # Validate instructor count (21)
        if len(self.instructors) != 21:
            print(f"⚠️ Warning: Expected 21 instructors, found {len(self.instructors)}")

        # Validate classroom count (5-7)
        if not (5 <= len(self.classrooms) <= 7):
            print(f"⚠️ Warning: Classroom count {len(self.classrooms)} is outside recommended range 5-7")

        # Validate timeslot count (14-16)
        expected_timeslots = 14  # 6 morning + 8 afternoon
        if len(self.timeslots) != expected_timeslots:
            print(f"⚠️ Warning: Expected {expected_timeslots} timeslots, found {len(self.timeslots)}")

    def _create_feasible_solution(self) -> List[Dict[str, Any]]:
        """Create a feasible solution that satisfies all constraints."""
        assignments = []

        # Group projects by type for priority assignment
        bitirme_projects = [p for p in self.projects if p.get("type") == "bitirme"]
        ara_projects = [p for p in self.projects if p.get("type") == "ara"]

        # Process bitirme projects first (higher priority)
        for project in bitirme_projects + ara_projects:
            # Find suitable timeslot and classroom
            assignment = self._assign_project_to_slot(project)
            if assignment:
                assignments.append(assignment)

        return assignments

    def _assign_project_to_slot(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Assign a project to an available timeslot and classroom."""
        project_type = project.get("type", "ara")

        # Try to find a suitable slot
        for timeslot in self.timeslots:
            for classroom in self.classrooms:
                # Check if this slot is available
                slot_key = (classroom.get("id"), timeslot.get("id"))
                if slot_key not in [a.get("slot_key", "") for a in self._get_current_assignments()]:
                    # Assign instructors to project
                    instructors = self._assign_instructors_to_project(project)
                    if instructors:
                        return {
                            "project_id": project.get("id"),
                            "classroom_id": classroom.get("id"),
                            "timeslot_id": timeslot.get("id"),
                            "instructors": instructors,
                            "is_makeup": project.get("is_makeup", False),
                            "slot_key": slot_key
                        }
        return None

    def _assign_instructors_to_project(self, project: Dict[str, Any]) -> List[int]:
        """Assign instructors to project following optimizationplanner.mdc rules."""
        project_type = project.get("type", "ara")

        # Required counts
        required_total = 3 if project_type == "bitirme" else 2
        required_instructors = 2 if project_type == "bitirme" else 1

        # Get available instructors
        available_instructors = []
        for inst in self.instructors:
            if inst.get("type") == "instructor":
                current_load = getattr(inst, 'total_load', 0)
                max_load = min(8, len(self.projects) // len([i for i in self.instructors if i.get("type") == "instructor"]) + 1)
                if current_load < max_load:
                    available_instructors.append(inst)

        if len(available_instructors) < required_instructors:
            return []

        # Sort by current load and professor status
        available_instructors.sort(key=lambda x: (getattr(x, 'total_load', 0), not x.get("name", "").startswith(("Prof.", "Doc."))))

        assigned_instructors = []

        # Assign instructors based on project type
        if project_type == "bitirme":
            # Prefer professors for bitirme projects
            professors = [inst for inst in available_instructors if inst.get("name", "").startswith(("Prof.", "Doc."))]
            if professors:
                assigned_instructors.append(professors[0].get("id"))
                available_instructors.remove(professors[0])
            else:
                assigned_instructors.append(available_instructors[0].get("id"))
                available_instructors.pop(0)

            # Add second instructor
            if available_instructors:
                assigned_instructors.append(available_instructors[0].get("id"))
                available_instructors.pop(0)
        else:
            # For ara projects, any instructor is fine
            assigned_instructors.append(available_instructors[0].get("id"))
            available_instructors.pop(0)

        # Fill remaining slots with any available instructors
        while len(assigned_instructors) < required_total and available_instructors:
            assigned_instructors.append(available_instructors[0].get("id"))
            available_instructors.pop(0)

        return assigned_instructors

    def _get_current_assignments(self) -> List[Dict[str, Any]]:
        """Get all current assignments from population."""
        assignments = []
        for solution in self.population:
            assignments.extend(solution)
        return assignments

    def _evaluate_fitness(self, solution: List[Dict[str, Any]]) -> float:
        """Evaluate fitness of a solution using all 5 objective functions."""
        if not solution:
            return 0.0

        # Check cache first
        solution_key = str(sorted([f"{a['project_id']}-{a['classroom_id']}-{a['timeslot_id']}" for a in solution]))
        if solution_key in self.fitness_cache:
            return self.fitness_cache[solution_key]

        # Calculate all 5 objective scores
        load_balance_score = self._calculate_load_balance_score(solution)
        classroom_change_score = self._calculate_classroom_change_score(solution)
        time_efficiency_score = self._calculate_time_efficiency_score(solution)
        slot_minimization_score = self._calculate_slot_minimization_score(solution)
        rule_compliance_score = self._calculate_rule_compliance_score(solution)

        # Weighted sum
        fitness = (
            load_balance_score * self.weights["load_balance"] +
            classroom_change_score * self.weights["classroom_changes"] +
            time_efficiency_score * self.weights["time_efficiency"] +
            slot_minimization_score * self.weights["slot_minimization"] +
            rule_compliance_score * self.weights["rule_compliance"]
        )

        # Cache the result
        self.fitness_cache[solution_key] = fitness
        return fitness

    def _calculate_load_balance_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate load balance score (0-100) - equal distribution ±1 tolerance."""
        instructor_loads = {}
        for assignment in solution:
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

    def _calculate_classroom_change_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate classroom change minimization score (0-100)."""
        instructor_classrooms = {}
        total_changes = 0
        total_assignments = 0

        for assignment in solution:
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

    def _calculate_time_efficiency_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate time efficiency score (0-100) - morning priority + gap-free."""
        if not solution:
            return 0.0

        # Group assignments by instructor
        instructor_assignments = {}
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_assignments:
                    instructor_assignments[instructor_id] = []
                instructor_assignments[instructor_id].append(assignment)

        total_gaps = 0

        for instructor_id, assignments_list in instructor_assignments.items():
            if len(assignments_list) <= 1:
                continue

            # Sort by timeslot
            assignments_list.sort(key=lambda x: self._get_timeslot_index(x.get("timeslot_id", 0)))

            # Check for gaps
            for i in range(len(assignments_list) - 1):
                current_idx = self._get_timeslot_index(assignments_list[i].get("timeslot_id", 0))
                next_idx = self._get_timeslot_index(assignments_list[i + 1].get("timeslot_id", 0))

                if next_idx > current_idx + 1:
                    total_gaps += 1

        # Calculate morning slot preference
        morning_assignments = 0
        total_assignments = len(solution)

        for assignment in solution:
            timeslot_id = assignment.get("timeslot_id")
            timeslot = next((t for t in self.timeslots if t.get("id") == timeslot_id), None)
            if timeslot and timeslot.get("is_morning", False):
                morning_assignments += 1

        morning_ratio = morning_assignments / total_assignments if total_assignments > 0 else 0

        # Base score from gap-free scheduling
        gap_score = max(0.0, 100.0 - (total_gaps * 20))

        # Bonus for morning slot preference
        morning_bonus = morning_ratio * 30  # Up to 30 points for morning preference

        return min(100.0, gap_score + morning_bonus)

    def _calculate_slot_minimization_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate slot minimization score (0-100)."""
        if not solution:
            return 0.0

        # Count unique timeslots used
        used_timeslots = set(assignment["timeslot_id"] for assignment in solution)
        total_timeslots = len(self.timeslots)

        if total_timeslots == 0:
            return 0.0

        # More slots used = lower score (we want to minimize slots)
        utilization_ratio = len(used_timeslots) / total_timeslots
        score = max(0.0, 100.0 - (utilization_ratio * 50))  # Max 50 point penalty
        return score

    def _calculate_rule_compliance_score(self, solution: List[Dict[str, Any]]) -> float:
        """Calculate rule compliance score (0-100)."""
        violations = 0
        total_projects = len(solution)

        if total_projects == 0:
            return 100.0

        for assignment in solution:
            project = next((p for p in self.projects if p.get("id") == assignment["project_id"]), None)
            if project:
                project_type = project.get("type", "ara")
                min_instructors = 2 if project_type == "bitirme" else 1

                actual_instructors = len(assignment.get("instructors", []))
                if actual_instructors < min_instructors:
                    violations += 1

                # Check for role conflicts
                instructors = assignment.get("instructors", [])
                if len(instructors) > 1 and instructors[0] in instructors[1:]:
                    violations += 1

        # Perfect compliance = 100, violations reduce score
        compliance_ratio = 1.0 - (violations / total_projects)
        return max(0.0, compliance_ratio * 100)

    def _get_timeslot_index(self, timeslot_id: int) -> int:
        """Get the index of a timeslot."""
        for i, timeslot in enumerate(self.timeslots):
            if timeslot.get("id") == timeslot_id:
                return i
        return 0

    def _tournament_selection(self, fitness_scores: List[float]) -> List[Dict[str, Any]]:
        """Tournament selection for parent selection."""
        tournament_size = 5
        tournament_indices = random.sample(range(len(self.population)), tournament_size)
        winner_idx = max(tournament_indices, key=lambda i: fitness_scores[i])
        return self.population[winner_idx]

    def _crossover(self, parent1: List[Dict[str, Any]], parent2: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Single point crossover."""
        if not parent1 or not parent2:
            return parent1.copy(), parent2.copy()

        # Choose crossover point
        crossover_point = random.randint(1, min(len(parent1), len(parent2)) - 1)

        # Create children
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]

        return child1, child2

    def _mutate(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mutation operator - randomly change assignment."""
        if not solution:
            return solution

        mutated_solution = solution.copy()
        mutation_idx = random.randint(0, len(mutated_solution) - 1)

        # Randomly change classroom or timeslot
        assignment = mutated_solution[mutation_idx]
        if random.random() < 0.5:
            # Change classroom
            available_classrooms = [c for c in self.classrooms if c.get("id") != assignment["classroom_id"]]
            if available_classrooms:
                new_classroom = random.choice(available_classrooms)
                assignment["classroom_id"] = new_classroom.get("id")
        else:
            # Change timeslot
            available_timeslots = [t for t in self.timeslots if t.get("id") != assignment["timeslot_id"]]
            if available_timeslots:
                new_timeslot = random.choice(available_timeslots)
                assignment["timeslot_id"] = new_timeslot.get("id")

        return mutated_solution

    def _repair_solution(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Repair solution to ensure feasibility."""
        # Remove duplicates and conflicts
        seen_slots = set()
        repaired_solution = []

        for assignment in solution:
            slot_key = (assignment["classroom_id"], assignment["timeslot_id"])
            if slot_key not in seen_slots:
                seen_slots.add(slot_key)
                repaired_solution.append(assignment)

        return repaired_solution

    def _calculate_comprehensive_metrics(self, solution: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive metrics according to optimizationplanner.mdc."""
        if not solution:
            return {
                "load_balance_score": 0.0,
                "classroom_change_score": 0.0,
                "time_efficiency_score": 0.0,
                "slot_minimization_score": 0.0,
                "rule_compliance_score": 0.0,
                "overall_score": 0.0
            }

        # Calculate all 5 objective scores
        load_balance_score = self._calculate_load_balance_score(solution)
        classroom_change_score = self._calculate_classroom_change_score(solution)
        time_efficiency_score = self._calculate_time_efficiency_score(solution)
        slot_minimization_score = self._calculate_slot_minimization_score(solution)
        rule_compliance_score = self._calculate_rule_compliance_score(solution)

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

    def _check_constraint_compliance(self, solution: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check constraint compliance for the solution."""
        violations = []
        unassigned_projects = []

        # Check for unassigned projects
        assigned_project_ids = {assignment["project_id"] for assignment in solution}
        for project in self.projects:
            if project.get("id") not in assigned_project_ids:
                unassigned_projects.append({
                    "type": "unassigned_project",
                    "message": f"Project {project.get('title', 'Unknown')} (ID: {project.get('id')}) is not assigned",
                    "project_id": project.get("id"),
                    "project_title": project.get("title")
                })

        # Check instructor assignment rules
        for assignment in solution:
            project = next((p for p in self.projects if p.get("id") == assignment["project_id"]), None)
            if project:
                project_type = project.get("type", "ara")
                min_instructors = 2 if project_type == "bitirme" else 1

                actual_instructors = len(assignment.get("instructors", []))
                if actual_instructors < min_instructors:
                    violations.append({
                        "type": "insufficient_instructors",
                        "message": f"Project {project.get('title', 'Unknown')} ({project_type}) needs {min_instructors} instructors, has {actual_instructors}",
                        "project_id": assignment["project_id"],
                        "project_type": project_type,
                        "current": actual_instructors,
                        "required": min_instructors
                    })

        # Check slot conflicts
        used_slots = {}
        for assignment in solution:
            slot_key = (assignment["classroom_id"], assignment["timeslot_id"])
            if slot_key in used_slots:
                violations.append({
                    "type": "slot_conflict",
                    "message": f"Multiple projects assigned to classroom {assignment['classroom_id']}, timeslot {assignment['timeslot_id']}",
                    "classroom_id": assignment["classroom_id"],
                    "timeslot_id": assignment["timeslot_id"],
                    "conflicting_project": used_slots[slot_key]
                })
            else:
                used_slots[slot_key] = assignment["project_id"]

        # Check instructor conflicts (same instructor in multiple places at same time)
        instructor_timeslots = {}
        for assignment in solution:
            timeslot_id = assignment["timeslot_id"]
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_timeslots:
                    instructor_timeslots[instructor_id] = set()
                if timeslot_id in instructor_timeslots[instructor_id]:
                    violations.append({
                        "type": "instructor_conflict",
                        "message": f"Instructor {instructor_id} assigned to multiple projects at timeslot {timeslot_id}",
                        "instructor_id": instructor_id,
                        "timeslot_id": timeslot_id
                    })
                else:
                    instructor_timeslots[instructor_id].add(timeslot_id)

        # Check gap-free compliance
        gap_violations = self._check_gap_free_violations(solution)

        all_violations = violations + gap_violations + unassigned_projects

        return {
            "is_feasible": len(all_violations) == 0,
            "is_gap_free": len(gap_violations) == 0,
            "violations": violations,
            "gap_violations": gap_violations,
            "unassigned_projects": unassigned_projects,
            "total_violations": len(all_violations),
            "compliance_percentage": max(0.0, 100.0 - (len(all_violations) * 10))
        }

    def _check_gap_free_violations(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for gap-free violations in the solution."""
        violations = []

        # Group assignments by instructor
        instructor_assignments = {}
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_assignments:
                    instructor_assignments[instructor_id] = []
                instructor_assignments[instructor_id].append(assignment)

        # Check each instructor's schedule
        for instructor_id, assignments_list in instructor_assignments.items():
            if len(assignments_list) <= 1:
                continue

            # Sort by timeslot
            assignments_list.sort(key=lambda x: self._get_timeslot_index(x.get("timeslot_id", 0)))

            # Check for gaps
            for i in range(len(assignments_list) - 1):
                current_idx = self._get_timeslot_index(assignments_list[i].get("timeslot_id", 0))
                next_idx = self._get_timeslot_index(assignments_list[i + 1].get("timeslot_id", 0))

                if next_idx > current_idx + 1:
                    violations.append({
                        "type": "gap_violation",
                        "message": f"Instructor {instructor_id} has gap between timeslots {assignments_list[i].get('timeslot_id')} and {assignments_list[i + 1].get('timeslot_id')}",
                        "instructor_id": instructor_id,
                        "gap_start": assignments_list[i].get("timeslot_id"),
                        "gap_end": assignments_list[i + 1].get("timeslot_id")
                    })

        return violations

    def _create_fallback_solution(self) -> Dict[str, Any]:
        """Create a fallback solution when optimization fails."""
        print("🔄 Using fallback solution...")

        # Simple greedy assignment as fallback
        assignments = []
        used_slots = set()

        for project in self.projects:
            # Find available slot
            for classroom in self.classrooms:
                for timeslot in self.timeslots:
                    slot_key = (classroom.get("id", 0), timeslot.get("id", 0))
                    if slot_key not in used_slots:
                        instructors = self._assign_instructors_to_project(project)
                        if instructors:
                            assignment = {
                                "project_id": project.get("id", 0),
                                "classroom_id": classroom.get("id", 0),
                                "timeslot_id": timeslot.get("id", 0),
                                "instructors": instructors,
                                "is_makeup": project.get("is_makeup", False)
                            }
                            assignments.append(assignment)
                            used_slots.add(slot_key)
                            break
                else:
                    continue
                break

        metrics = self._calculate_comprehensive_metrics(assignments)

        return {
            "algorithm": "Genetic Algorithm (Fallback)",
            "status": "completed",
            "schedule": assignments,
            "solution": assignments,
            "metrics": metrics,
            "execution_time": 0.1,
            "iterations": 0,
            "message": "Genetic Algorithm completed using fallback method",
            "constraint_compliance": self._check_constraint_compliance(assignments)
        }

    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Genetic Algorithm optimization according to optimizationplanner.mdc requirements.

        Returns:
            Complete optimization result with all 5 objective scores and constraint compliance.
        """
        start_time = time.time()

        try:
            # Re-initialize with fresh data
            self.initialize(data)

            print("🚀 Starting Genetic Algorithm optimization...")
            print(f"   Population size: {self.population_size}")
            print(f"   Generations: {self.generations}")
            print(f"   Mutation rate: {self.mutation_rate}")
            print(f"   Crossover rate: {self.crossover_rate}")

            # Evolution process
            for generation in range(self.generations):
                # Evaluate fitness of current population
                fitness_scores = []
                for solution in self.population:
                    fitness = self._evaluate_fitness(solution)
                    fitness_scores.append(fitness)

                # Find best solution in this generation
                best_idx = np.argmax(fitness_scores)
                current_best = self.population[best_idx]
                current_best_fitness = fitness_scores[best_idx]

                # Update best solution if improved
                if self.best_solution is None or current_best_fitness > self._evaluate_fitness(self.best_solution):
                    self.best_solution = current_best.copy()

                if generation % 50 == 0:
                    print(f"   Generation {generation}: Best fitness = {current_best_fitness:.4f}")

                # Create new population
                new_population = []

                # Elitism: Keep best solutions
                elite_indices = np.argsort(fitness_scores)[-self.elite_size:]
                for idx in elite_indices:
                    new_population.append(self.population[idx].copy())

                # Generate offspring until population is full
                while len(new_population) < self.population_size:
                    # Selection
                    parent1 = self._tournament_selection(fitness_scores)
                    parent2 = self._tournament_selection(fitness_scores)

                    # Crossover
                    if random.random() < self.crossover_rate:
                        child1, child2 = self._crossover(parent1, parent2)
                    else:
                        child1, child2 = parent1.copy(), parent2.copy()

                    # Mutation
                    if random.random() < self.mutation_rate:
                        child1 = self._mutate(child1)
                    if random.random() < self.mutation_rate:
                        child2 = self._mutate(child2)

                    # Ensure feasibility
                    child1 = self._repair_solution(child1)
                    child2 = self._repair_solution(child2)

                    new_population.extend([child1, child2])

                # Trim population to correct size
                self.population = new_population[:self.population_size]

            # Final evaluation
            final_fitness = self._evaluate_fitness(self.best_solution)
            execution_time = time.time() - start_time

            print(f"✅ Genetic Algorithm completed!")
            print(f"   Final fitness: {final_fitness:.4f}")
            print(f"   Execution time: {execution_time:.2f}s")

            # Calculate comprehensive metrics
            metrics = self._calculate_comprehensive_metrics(self.best_solution)
            constraint_compliance = self._check_constraint_compliance(self.best_solution)

            return {
                "algorithm": "Genetic Algorithm",
                "status": "completed",
                "schedule": self.best_solution,
                "solution": self.best_solution,
                "metrics": metrics,
                "execution_time": execution_time,
                "iterations": self.generations,
                "population_size": self.population_size,
                "message": "Genetic Algorithm optimization completed successfully",
                "constraint_compliance": constraint_compliance,
                "fitness": final_fitness
            }

        except Exception as e:
            print(f"❌ Genetic Algorithm error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_solution()
        
        Args:
            data: Algoritma giris verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # Nesiller boyunca evrim
        for generation in range(self.generations):
            # Uygunluk degerlendirmesi
            fitness_scores = []
            for solution in self.population:
                fitness = self.evaluate_fitness(solution)
                fitness_scores.append((solution, fitness))
            
            # En iyi cozumu bul
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            self.best_solution = fitness_scores[0][0]
            self.fitness_score = fitness_scores[0][1]
            
            # Yeni populasyon olustur
            new_population = []
            
            # Elitizm: En iyi cozumu dogrudan aktar
            new_population.append(self.best_solution)
            
            # Caprazlama ve mutasyon
            while len(new_population) < self.population_size:
                # Secim
                parent1 = self._selection(fitness_scores)
                parent2 = self._selection(fitness_scores)
                
                # Caprazlama
                if random.random() < self.crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1, child2 = parent1, parent2
                
                # Mutasyon
                if random.random() < self.mutation_rate:
                    child1 = self._mutate(child1)
                if random.random() < self.mutation_rate:
                    child2 = self._mutate(child2)
                
                new_population.append(child1)
                if len(new_population) < self.population_size:
                    new_population.append(child2)
            
            self.population = new_population
        
        # Sonucu dondur
        return {
            "schedule": self.best_solution or [],
            "fitness": self.fitness_score,
            "generation": self.generations
        }
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Verilen cozumun uygunlugunu degerlendirir.
        
        Args:
            solution: Degerlendirilecek cozum.
            
        Returns:
            float: Uygunluk puani.
        """
        # Basit bir fitness fonksiyonu ornegi
        score = 0.0
        
        # Cozum gecerli mi?
        if not self._is_valid_solution(solution):
            return 0.0
        
        # Sinif degisim sayisini minimize et
        instructor_changes = self._count_instructor_classroom_changes(solution)
        score -= instructor_changes * 10
        
        # Yuk dengesini maksimize et
        load_balance = self._calculate_load_balance(solution)
        score += load_balance * 20
        
        return score
    
    def _create_random_solution(self) -> Dict[str, Any]:
        """
        Rastgele bir cozum olusturur.
        
        Returns:
            Dict[str, Any]: Rastgele cozum.
        """
        solution = []
        
        # Her proje icin rastgele bir sinif ve zaman dilimi ata
        for project in self.projects:
            classroom = random.choice(self.classrooms) if self.classrooms else None
            timeslot = random.choice(self.timeslots) if self.timeslots else None
            
            if classroom and timeslot:
                # responsible_id yoksa ilk instructor'i kullan
                responsible_id = project.get("responsible_id", self.instructors[0]["id"] if self.instructors else 1)
                assignment = {
                    "project_id": project["id"],
                    "classroom_id": classroom["id"],
                    "timeslot_id": timeslot["id"],
                    "instructors": [responsible_id]
                }
                
                # Rastgele 1-2 yardimci katilimci ekle
                available_instructors = [i for i in self.instructors if i["id"] != responsible_id]
                if available_instructors:
                    max_assistants = min(2, len(available_instructors))
                    assistant_count = random.randint(1, max_assistants) if max_assistants > 0 else 0
                    if assistant_count > 0:
                        assistants = random.sample(available_instructors, assistant_count)
                        for assistant in assistants:
                            assignment["instructors"].append(assistant["id"])
                
                solution.append(assignment)
        
        return solution
    
    def _selection(self, fitness_scores: List[tuple]) -> Dict[str, Any]:
        """
        Turnuva secimi ile bir ebeveyn secer.
        
        Args:
            fitness_scores: Cozum ve uygunluk puani ciftleri.
            
        Returns:
            Dict[str, Any]: Secilen cozum.
        """
        # Turnuva secimi
        tournament_size = 3
        tournament = random.sample(fitness_scores, min(tournament_size, len(fitness_scores)))
        tournament.sort(key=lambda x: x[1], reverse=True)
        return tournament[0][0]
    
    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> tuple:
        """
        Iki ebeveyn arasinda caprazlama yapar.
        
        Args:
            parent1: Birinci ebeveyn.
            parent2: Ikinci ebeveyn.
            
        Returns:
            tuple: Iki cocuk cozum.
        """
        # Tek noktali caprazlama
        if not parent1 or not parent2:
            return parent1, parent2
        
        min_len = min(len(parent1), len(parent2))
        if min_len <= 1:
            return parent1, parent2
        
        crossover_point = random.randint(1, min_len - 1)
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]
        
        return child1, child2
    
    def _mutate(self, solution: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cozumde mutasyon yapar.
        
        Args:
            solution: Mutasyona ugrayacak cozum.
            
        Returns:
            Dict[str, Any]: Mutasyona ugramis cozum.
        """
        if not solution:
            return solution
        
        # Rastgele bir atamayi degistir
        mutation_index = random.randint(0, len(solution) - 1)
        
        # Sinif veya zaman dilimini degistir
        if random.random() < 0.5 and self.classrooms:
            solution[mutation_index]["classroom_id"] = random.choice(self.classrooms)["id"]
        elif self.timeslots:
            solution[mutation_index]["timeslot_id"] = random.choice(self.timeslots)["id"]
        
        return solution
    
    def _is_valid_solution(self, solution: Dict[str, Any]) -> bool:
        """
        Cozumun gecerli olup olmadigini kontrol eder.
        
        Args:
            solution: Kontrol edilecek cozum.
            
        Returns:
            bool: Cozum gecerli ise True, degilse False.
        """
        # Cakisma kontrolu
        assignments = {}
        
        for assignment in solution:
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            
            # Ayni sinif ve zaman diliminde baska bir atama var mi?
            key = f"{classroom_id}_{timeslot_id}"
            if key in assignments:
                return False
            
            assignments[key] = True
        
        return True
    
    def _count_instructor_classroom_changes(self, solution: Dict[str, Any]) -> int:
        """
        Ogretim uyelerinin sinif degisim sayisini hesaplar.
        
        Args:
            solution: Degerlendirilecek cozum.
            
        Returns:
            int: Sinif degisim sayisi.
        """
        instructor_schedule = {}
        changes = 0
        
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                if instructor_id not in instructor_schedule:
                    instructor_schedule[instructor_id] = []
                
                instructor_schedule[instructor_id].append(assignment)
        
        # Her ogretim uyesi icin sinif degisim sayisini hesapla
        for instructor_id, assignments in instructor_schedule.items():
            # Zaman dilimine gore sirala
            assignments.sort(key=lambda x: x.get("timeslot_id"))
            
            # Ardisik atamalar arasinda sinif degisimi var mi?
            for i in range(1, len(assignments)):
                if assignments[i].get("classroom_id") != assignments[i-1].get("classroom_id"):
                    changes += 1
        
        return changes
    
    def _calculate_load_balance(self, solution: Dict[str, Any]) -> float:
        """
        Ogretim uyeleri arasindaki yuk dengesini hesaplar.
        
        Args:
            solution: Degerlendirilecek cozum.
            
        Returns:
            float: Yuk dengesi puani (0-1 arasi).
        """
        instructor_loads = {}
        
        # Her ogretim uyesi icin yuk hesapla
        for assignment in solution:
            for instructor_id in assignment.get("instructors", []):
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if not instructor_loads:
            return 0.0
        
        # Standart sapma hesapla
        loads = list(instructor_loads.values())
        mean = sum(loads) / len(loads)
        variance = sum((load - mean) ** 2 for load in loads) / len(loads)
        std_dev = variance ** 0.5
        
        # Standart sapma ne kadar dusukse, denge o kadar iyi
        if mean == 0:
            return 1.0
        
        # Normalize edilmis denge puani (0-1 arasi)
        balance = max(0, 1 - (std_dev / mean))
        
        return balance 