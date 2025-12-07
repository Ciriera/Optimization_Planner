"""
NSGA-II Algorithm - Multi-Objective Academic Project Exam/Jury Scheduling System

This module implements a complete NSGA-II (Non-dominated Sorting Genetic Algorithm II)
for academic project jury scheduling with the following objectives:

OBJECTIVES (3 Main Objectives):
1. H2 - Workload Uniformity: Keep instructor workloads within AvgLoad ±2 band
2. H1 - Continuity: Maximize back-to-back task blocks for instructors
3. H3 - Class Change: Minimize unnecessary class switches for instructors

SINGLE-PHASE SOLUTION:
- All decisions optimized simultaneously in one chromosome
- No intermediate phases, no post-processing
- Final plan includes: Class, Order, PS, J1, J2 (placeholder)

HARD CONSTRAINTS:
- PS is fixed per project
- J1 ≠ PS
- J1 must be an instructor (not assistant)
- At most 1 duty per instructor per timeslot
- No gaps within class schedule (back-to-back)
- All projects must be assigned
- Priority mode constraints (ARA_ONCE, BITIRME_ONCE, ESIT)

Author: Optimization Planner System
"""

from typing import Dict, Any, List, Tuple, Set, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import copy
import random
import math
import time
import logging

from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION ENUMS
# ============================================================================

class PriorityMode(str, Enum):
    """Project type priority mode."""
    ARA_ONCE = "ARA_ONCE"           # All ARA (interim) projects before BITIRME (final)
    BITIRME_ONCE = "BITIRME_ONCE"   # All BITIRME projects before ARA
    ESIT = "ESIT"                   # No priority constraint


class TimePenaltyMode(str, Enum):
    """Time/gap penalty calculation mode."""
    BINARY = "BINARY"                       # Non-consecutive = 1 penalty
    GAP_PROPORTIONAL = "GAP_PROPORTIONAL"   # Penalty = gap slot count


class WorkloadConstraintMode(str, Enum):
    """Workload constraint mode."""
    SOFT_ONLY = "SOFT_ONLY"           # Only penalty (H2)
    SOFT_AND_HARD = "SOFT_AND_HARD"   # Penalty + hard constraint (B_max)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class NSGA2Config:
    """NSGA-II Algorithm configuration parameters."""
    
    # Population and generations
    population_size: int = 100
    max_generations: int = 200
    stagnation_limit: int = 30  # Stop if no improvement for this many generations
    
    # Class count settings
    class_count: int = 7
    auto_class_count: bool = True  # Try 5, 6, 7 and pick best
    
    # Genetic operators
    crossover_rate: float = 0.9
    mutation_rate: float = 0.3
    tournament_size: int = 3
    
    # Priority mode
    priority_mode: PriorityMode = PriorityMode.ESIT
    
    # Time penalty mode
    time_penalty_mode: TimePenaltyMode = TimePenaltyMode.GAP_PROPORTIONAL
    
    # Workload constraint mode
    workload_constraint_mode: WorkloadConstraintMode = WorkloadConstraintMode.SOFT_ONLY
    workload_hard_limit: int = 4  # B_max for SOFT_AND_HARD mode
    workload_soft_band: int = 2   # ±2 tolerance
    
    # Objective weights for final solution selection
    # Higher weight = more important
    weight_h1: float = 2.5   # Continuity weight (INCREASED)
    weight_h2: float = 3.0   # Workload weight (MOST IMPORTANT)
    weight_h3: float = 1.5   # Class change weight
    weight_h4: float = 2.0   # Class load balance weight
    
    # Slot duration in hours
    slot_duration: float = 0.5  # 30 minutes
    
    # Tolerance for time comparisons
    time_tolerance: float = 0.001


@dataclass
class Project:
    """Project data structure."""
    id: int
    title: str
    type: str  # "interim" (ARA) or "final" (BITIRME)
    responsible_id: int  # Project Supervisor (PS) - fixed, cannot be changed
    is_makeup: bool = False
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Project):
            return self.id == other.id
        return False


@dataclass
class Instructor:
    """Instructor data structure."""
    id: int
    name: str
    type: str  # "instructor" or "assistant"
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Instructor):
            return self.id == other.id
        return False


@dataclass
class ProjectAssignment:
    """Single project assignment in chromosome."""
    project_id: int
    class_id: int
    order_in_class: int
    ps_id: int      # Project Supervisor (fixed)
    j1_id: int      # Jury 1 (decision variable)
    j2_id: int = -1  # Jury 2 (always placeholder: [Araştırma Görevlisi])
    
    def __hash__(self):
        return hash(self.project_id)
    
    def copy(self) -> 'ProjectAssignment':
        return ProjectAssignment(
            project_id=self.project_id,
            class_id=self.class_id,
            order_in_class=self.order_in_class,
            ps_id=self.ps_id,
            j1_id=self.j1_id,
            j2_id=self.j2_id
        )


@dataclass
class Individual:
    """
    NSGA-II Individual (Chromosome).
    
    Contains complete solution:
    - Project → Class assignment
    - Order within class
    - J1 assignments
    """
    assignments: List[ProjectAssignment] = field(default_factory=list)
    class_count: int = 7
    
    # Objective values (to be computed)
    objectives: List[float] = field(default_factory=list)  # [H1, H2, H3]
    
    # NSGA-II specific
    rank: int = 0
    crowding_distance: float = 0.0
    
    # Feasibility
    is_feasible: bool = True
    constraint_violations: int = 0
    
    def copy(self) -> 'Individual':
        """Deep copy of individual."""
        new_ind = Individual(
            assignments=[a.copy() for a in self.assignments],
            class_count=self.class_count,
            objectives=self.objectives.copy() if self.objectives else [],
            rank=self.rank,
            crowding_distance=self.crowding_distance,
            is_feasible=self.is_feasible,
            constraint_violations=self.constraint_violations
        )
        return new_ind
    
    def get_class_projects(self, class_id: int) -> List[ProjectAssignment]:
        """Get all projects assigned to a specific class, sorted by order."""
        projects = [a for a in self.assignments if a.class_id == class_id]
        return sorted(projects, key=lambda x: x.order_in_class)
    
    def get_class_order(self, class_id: int) -> List[int]:
        """Get project IDs in order for a class."""
        return [a.project_id for a in self.get_class_projects(class_id)]


@dataclass
class ObjectiveValues:
    """Objective function values."""
    h1_continuity: float = 0.0      # Continuity penalty (minimize)
    h2_workload: float = 0.0        # Workload uniformity penalty (minimize)
    h3_class_change: float = 0.0    # Class change penalty (minimize)
    h4_class_load: float = 0.0      # Class load balance penalty (minimize)
    
    def to_list(self) -> List[float]:
        """Convert to list for NSGA-II processing."""
        return [self.h1_continuity, self.h2_workload, self.h3_class_change, self.h4_class_load]
    
    def weighted_sum(self, config: NSGA2Config) -> float:
        """Calculate weighted sum for final solution selection."""
        return (
            config.weight_h1 * self.h1_continuity +
            config.weight_h2 * self.h2_workload +
            config.weight_h3 * self.h3_class_change +
            config.weight_h4 * self.h4_class_load
        )


# ============================================================================
# OBJECTIVE CALCULATOR
# ============================================================================

class NSGA2ObjectiveCalculator:
    """
    Calculates all objective functions for NSGA-II.
    
    Objectives:
    - H1: Continuity penalty (blocks - 1 per instructor per class)
    - H2: Workload uniformity penalty (deviation from AvgLoad ±2)
    - H3: Class change penalty (classes visited > 2)
    - H4: Class load balance penalty (deviation from target)
    """
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: NSGA2Config
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Only real instructors (not assistants)
        self.faculty = {
            i.id: i for i in instructors
            if i.type == "instructor"
        }
        
        # Calculate average workload
        num_projects = len(projects)
        num_faculty = len(self.faculty)
        self.total_workload = 2 * num_projects  # PS + J1 per project
        self.avg_workload = self.total_workload / num_faculty if num_faculty > 0 else 0
        
        logger.debug(f"ObjectiveCalculator: {num_projects} projects, {num_faculty} faculty")
        logger.debug(f"Average workload: {self.avg_workload:.2f}")
    
    def evaluate(self, individual: Individual) -> ObjectiveValues:
        """
        Evaluate all objectives for an individual.
        
        Returns ObjectiveValues with all penalties calculated.
        """
        h1 = self._calculate_h1_continuity(individual)
        h2 = self._calculate_h2_workload(individual)
        h3 = self._calculate_h3_class_change(individual)
        h4 = self._calculate_h4_class_load(individual)
        
        return ObjectiveValues(
            h1_continuity=h1,
            h2_workload=h2,
            h3_class_change=h3,
            h4_class_load=h4
        )
    
    def _calculate_h1_continuity(self, individual: Individual) -> float:
        """
        H1: Continuity penalty.
        
        For each instructor in each class, count activity blocks.
        Penalty = max(0, blocks - 1)
        
        Also penalizes gaps between consecutive tasks.
        """
        total_penalty = 0.0
        
        for instructor_id in self.faculty.keys():
            for class_id in range(individual.class_count):
                blocks = self._count_blocks(individual, instructor_id, class_id)
                if blocks > 1:
                    # Linear penalty for extra blocks
                    penalty = blocks - 1
                    # Quadratic penalty for multiple blocks (more aggressive)
                    penalty += (blocks - 1) ** 2 * 10
                    total_penalty += penalty
        
        # Also add gap penalty within classes
        instructor_tasks = self._build_instructor_task_matrix(individual)
        
        for instructor_id, tasks in instructor_tasks.items():
            if len(tasks) <= 1:
                continue
            
            # Sort by order (time)
            tasks.sort(key=lambda x: (x['order'], x['class_id']))
            
            for i in range(len(tasks) - 1):
                curr = tasks[i]
                next_task = tasks[i + 1]
                
                # Same timeslot = same time (no gap)
                if curr['order'] == next_task['order']:
                    gap = 0
                elif curr['class_id'] == next_task['class_id']:
                    # Same class, different slots
                    gap = next_task['order'] - curr['order'] - 1
                else:
                    # Different classes - check slot difference
                    gap = abs(next_task['order'] - curr['order']) - 1
                    if gap < 0:
                        gap = 0
                
                if gap > 0:
                    if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                        total_penalty += gap * 2
                    else:  # GAP_PROPORTIONAL
                        total_penalty += gap * gap * 2
        
        return total_penalty
    
    def _calculate_h2_workload(self, individual: Individual) -> float:
        """
        H2: Workload uniformity penalty.
        
        Load(h) = PS duties + J1 duties
        Penalty(h) = max(0, |Load(h) - AvgLoad| - 2)
        H2 = Σ Penalty(h)
        """
        total_penalty = 0.0
        workload = self._calculate_instructor_workloads(individual)
        
        for instructor_id in self.faculty.keys():
            load = workload.get(instructor_id, 0)
            deviation = abs(load - self.avg_workload)
            
            # Soft penalty: beyond ±2 band
            penalty = max(0, deviation - self.config.workload_soft_band)
            total_penalty += penalty
            
            # Additional penalty for hard constraint violation
            if self.config.workload_constraint_mode == WorkloadConstraintMode.SOFT_AND_HARD:
                if deviation > self.config.workload_hard_limit:
                    total_penalty += 1000  # Large penalty
        
        return total_penalty
    
    def _calculate_h3_class_change(self, individual: Individual) -> float:
        """
        H3: Class change penalty.
        
        ClassCount(h) = number of different classes instructor h appears in
        Penalty = max(0, ClassCount(h) - 2)
        H3 = Σ Penalty(h)
        """
        total_penalty = 0.0
        instructor_classes = defaultdict(set)
        
        for assignment in individual.assignments:
            instructor_classes[assignment.ps_id].add(assignment.class_id)
            instructor_classes[assignment.j1_id].add(assignment.class_id)
        
        for instructor_id in self.faculty.keys():
            class_count = len(instructor_classes.get(instructor_id, set()))
            if class_count > 2:
                # Quadratic penalty for too many classes
                penalty = (class_count - 2) ** 2 * 5
                total_penalty += penalty
        
        return total_penalty
    
    def _calculate_h4_class_load(self, individual: Individual) -> float:
        """
        H4: Class load balance penalty.
        
        Target = num_projects / class_count
        Penalty = |ClassLoad(s) - Target|
        H4 = Σ Penalty(s)
        """
        total_penalty = 0.0
        class_loads = defaultdict(int)
        
        for assignment in individual.assignments:
            class_loads[assignment.class_id] += 1
        
        num_projects = len(individual.assignments)
        target = num_projects / individual.class_count
        
        for class_id in range(individual.class_count):
            load = class_loads.get(class_id, 0)
            if load == 0:
                # Empty class is very bad
                total_penalty += 1000
            else:
                total_penalty += abs(load - target)
        
        return total_penalty
    
    def _count_blocks(
        self,
        individual: Individual,
        instructor_id: int,
        class_id: int
    ) -> int:
        """
        Count activity blocks for instructor in class.
        
        A block is a consecutive sequence of duties.
        Count 0→1 transitions in presence array.
        """
        class_projects = individual.get_class_projects(class_id)
        
        if not class_projects:
            return 0
        
        # Build binary presence array
        presence = []
        for assignment in class_projects:
            is_present = (assignment.ps_id == instructor_id or 
                         assignment.j1_id == instructor_id)
            presence.append(1 if is_present else 0)
        
        if sum(presence) == 0:
            return 0
        
        # Count 0→1 transitions (block starts)
        blocks = 0
        for i in range(len(presence)):
            if presence[i] == 1:
                if i == 0 or presence[i - 1] == 0:
                    blocks += 1
        
        return blocks
    
    def _build_instructor_task_matrix(
        self,
        individual: Individual
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Build task matrix for each instructor."""
        instructor_tasks = defaultdict(list)
        
        for assignment in individual.assignments:
            task_info = {
                'project_id': assignment.project_id,
                'class_id': assignment.class_id,
                'order': assignment.order_in_class
            }
            
            instructor_tasks[assignment.ps_id].append(task_info.copy())
            instructor_tasks[assignment.j1_id].append(task_info.copy())
        
        return instructor_tasks
    
    def _calculate_instructor_workloads(
        self,
        individual: Individual
    ) -> Dict[int, int]:
        """Calculate workload for each instructor."""
        workload = defaultdict(int)
        
        for assignment in individual.assignments:
            workload[assignment.ps_id] += 1
            workload[assignment.j1_id] += 1
        
        return workload


# ============================================================================
# CONSTRAINT CHECKER
# ============================================================================

class NSGA2ConstraintChecker:
    """
    Checks and validates hard constraints for NSGA-II individuals.
    
    Hard Constraints:
    - PS cannot be changed (fixed)
    - J1 ≠ PS
    - J1 must be an instructor
    - At most 1 duty per instructor per timeslot
    - No gaps within class schedule
    - All projects assigned
    - Priority mode constraints
    """
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: NSGA2Config
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Only real instructors
        self.faculty_ids = {
            i.id for i in instructors
            if i.type == "instructor"
        }
        
        # Separate by type
        self.ara_project_ids = {
            p.id for p in projects
            if str(p.type).lower() in ["interim", "ara", "ara proje"]
        }
        self.bitirme_project_ids = {
            p.id for p in projects
            if str(p.type).lower() in ["final", "bitirme", "bitirme proje"]
        }
    
    def check_feasibility(self, individual: Individual) -> Tuple[bool, int]:
        """
        Check if individual is feasible.
        
        Returns:
            (is_feasible, violation_count)
        """
        violations = 0
        
        # Check J1 ≠ PS
        for assignment in individual.assignments:
            if assignment.j1_id == assignment.ps_id:
                violations += 1
        
        # Check J1 is instructor
        for assignment in individual.assignments:
            if assignment.j1_id not in self.faculty_ids:
                violations += 1
        
        # Check timeslot conflicts
        violations += self._check_timeslot_conflicts(individual)
        
        # Check all projects assigned
        assigned_projects = {a.project_id for a in individual.assignments}
        missing = set(self.projects.keys()) - assigned_projects
        violations += len(missing)
        
        # Check priority mode
        violations += self._check_priority_mode(individual)
        
        # Check no gaps within classes
        violations += self._check_class_gaps(individual)
        
        return violations == 0, violations
    
    def _check_timeslot_conflicts(self, individual: Individual) -> int:
        """Check for timeslot conflicts (instructor at multiple places same time)."""
        conflicts = 0
        
        # Build instructor schedule
        instructor_schedule = defaultdict(set)  # instructor_id -> set of (order)
        
        for assignment in individual.assignments:
            slot = assignment.order_in_class
            
            # Check PS
            if slot in instructor_schedule[assignment.ps_id]:
                conflicts += 1
            else:
                instructor_schedule[assignment.ps_id].add(slot)
            
            # Check J1
            if slot in instructor_schedule[assignment.j1_id]:
                conflicts += 1
            else:
                instructor_schedule[assignment.j1_id].add(slot)
        
        return conflicts
    
    def _check_priority_mode(self, individual: Individual) -> int:
        """Check priority mode constraints."""
        if self.config.priority_mode == PriorityMode.ESIT:
            return 0
        
        violations = 0
        
        # Get max slot for ARA and min slot for BITIRME
        ara_max_slot = -1
        bitirme_min_slot = float('inf')
        
        for assignment in individual.assignments:
            slot = assignment.class_id * 1000 + assignment.order_in_class
            
            if assignment.project_id in self.ara_project_ids:
                ara_max_slot = max(ara_max_slot, slot)
            elif assignment.project_id in self.bitirme_project_ids:
                bitirme_min_slot = min(bitirme_min_slot, slot)
        
        if self.config.priority_mode == PriorityMode.ARA_ONCE:
            # All ARA before all BITIRME
            if ara_max_slot > bitirme_min_slot and bitirme_min_slot != float('inf'):
                violations += 1
        elif self.config.priority_mode == PriorityMode.BITIRME_ONCE:
            # All BITIRME before all ARA
            if bitirme_min_slot != float('inf') and ara_max_slot != -1:
                if bitirme_min_slot > ara_max_slot:
                    violations += 1
        
        return violations
    
    def _check_class_gaps(self, individual: Individual) -> int:
        """Check for gaps within class schedules."""
        violations = 0
        
        for class_id in range(individual.class_count):
            projects = individual.get_class_projects(class_id)
            if not projects:
                continue
            
            # Check for gaps
            orders = sorted([p.order_in_class for p in projects])
            if orders:
                # Should start from 0 and be consecutive
                expected_orders = list(range(len(orders)))
                if orders != expected_orders:
                    violations += 1
        
        return violations


# ============================================================================
# GENETIC OPERATORS
# ============================================================================

class NSGA2GeneticOperators:
    """
    NSGA-II genetic operators: Selection, Crossover, Mutation.
    
    All operators maintain constraint feasibility.
    """
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: NSGA2Config
    ):
        self.projects = {p.id: p for p in projects}
        self.project_list = list(projects)
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Only real instructors for J1 assignment
        self.faculty_ids = [
            i.id for i in instructors
            if i.type == "instructor"
        ]
        
        # Project types
        self.ara_projects = [
            p for p in projects
            if str(p.type).lower() in ["interim", "ara", "ara proje"]
        ]
        self.bitirme_projects = [
            p for p in projects
            if str(p.type).lower() in ["final", "bitirme", "bitirme proje"]
        ]
    
    def tournament_selection(
        self,
        population: List[Individual],
        tournament_size: int = 3
    ) -> Individual:
        """
        Tournament selection based on rank and crowding distance.
        
        Returns the best individual from tournament.
        """
        tournament = random.sample(population, min(tournament_size, len(population)))
        
        # Sort by rank (ascending), then crowding distance (descending)
        tournament.sort(key=lambda x: (x.rank, -x.crowding_distance))
        
        return tournament[0].copy()
    
    def crossover(
        self,
        parent1: Individual,
        parent2: Individual
    ) -> Tuple[Individual, Individual]:
        """
        Crossover operator.
        
        Performs multi-point crossover on:
        1. Class assignments
        2. J1 assignments
        
        Returns two children.
        """
        if random.random() > self.config.crossover_rate:
            return parent1.copy(), parent2.copy()
        
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        # Create mapping for quick lookup
        p1_map = {a.project_id: a for a in parent1.assignments}
        p2_map = {a.project_id: a for a in parent2.assignments}
        
        # Crossover points
        n = len(child1.assignments)
        if n < 2:
            return child1, child2
        
        cx_point1 = random.randint(0, n - 1)
        cx_point2 = random.randint(cx_point1, n - 1)
        
        # Swap class and J1 assignments between crossover points
        for i in range(cx_point1, cx_point2 + 1):
            pid1 = child1.assignments[i].project_id
            pid2 = child2.assignments[i].project_id
            
            if pid1 in p2_map and pid2 in p1_map:
                # Swap class assignments
                child1.assignments[i].class_id = p2_map[pid1].class_id
                child2.assignments[i].class_id = p1_map[pid2].class_id
                
                # Swap J1 assignments
                child1.assignments[i].j1_id = p2_map[pid1].j1_id
                child2.assignments[i].j1_id = p1_map[pid2].j1_id
        
        # Repair children
        self._repair_individual(child1)
        self._repair_individual(child2)
        
        return child1, child2
    
    def mutate(self, individual: Individual) -> Individual:
        """
        Mutation operator.
        
        Applies one or more mutations:
        1. Move project to different class
        2. Swap order within class
        3. Change J1 assignment
        4. Block merge mutation (for continuity)
        """
        if random.random() > self.config.mutation_rate:
            return individual
        
        mutated = individual.copy()
        
        # Choose mutation type
        mutation_type = random.choice([
            'move_class',
            'swap_order',
            'change_j1',
            'block_merge',
            'j1_rebalance'
        ])
        
        if mutation_type == 'move_class':
            self._mutate_move_class(mutated)
        elif mutation_type == 'swap_order':
            self._mutate_swap_order(mutated)
        elif mutation_type == 'change_j1':
            self._mutate_change_j1(mutated)
        elif mutation_type == 'block_merge':
            self._mutate_block_merge(mutated)
        elif mutation_type == 'j1_rebalance':
            self._mutate_j1_rebalance(mutated)
        
        # Repair after mutation
        self._repair_individual(mutated)
        
        return mutated
    
    def _mutate_move_class(self, individual: Individual) -> None:
        """Move a random project to a different class."""
        if not individual.assignments:
            return
        
        assignment = random.choice(individual.assignments)
        old_class = assignment.class_id
        new_class = random.randint(0, individual.class_count - 1)
        
        if new_class != old_class:
            assignment.class_id = new_class
    
    def _mutate_swap_order(self, individual: Individual) -> None:
        """Swap order of two projects in the same class."""
        if len(individual.assignments) < 2:
            return
        
        # Pick a class with at least 2 projects
        class_projects = defaultdict(list)
        for a in individual.assignments:
            class_projects[a.class_id].append(a)
        
        valid_classes = [c for c, projects in class_projects.items() if len(projects) >= 2]
        if not valid_classes:
            return
        
        class_id = random.choice(valid_classes)
        projects = class_projects[class_id]
        
        # Swap two random projects
        p1, p2 = random.sample(projects, 2)
        p1.order_in_class, p2.order_in_class = p2.order_in_class, p1.order_in_class
    
    def _mutate_change_j1(self, individual: Individual) -> None:
        """Change J1 for a random project."""
        if not individual.assignments:
            return
        
        assignment = random.choice(individual.assignments)
        
        # Choose new J1 (not PS)
        valid_j1s = [f for f in self.faculty_ids if f != assignment.ps_id]
        if valid_j1s:
            assignment.j1_id = random.choice(valid_j1s)
    
    def _mutate_block_merge(self, individual: Individual) -> None:
        """
        Block merge mutation for continuity improvement.
        
        Tries to move instructor's tasks closer together.
        """
        if not individual.assignments:
            return
        
        # Pick a random instructor
        instructor_id = random.choice(self.faculty_ids)
        
        # Find all assignments where this instructor is involved
        instructor_assignments = [
            a for a in individual.assignments
            if a.ps_id == instructor_id or a.j1_id == instructor_id
        ]
        
        if len(instructor_assignments) < 2:
            return
        
        # Try to move one assignment closer to another
        a1, a2 = random.sample(instructor_assignments, 2)
        if a1.class_id != a2.class_id:
            # Move to same class
            a1.class_id = a2.class_id
    
    def _mutate_j1_rebalance(self, individual: Individual) -> None:
        """
        Rebalance J1 assignments based on workload.
        
        Assigns J1 to least-loaded instructor.
        """
        if not individual.assignments:
            return
        
        # Calculate current workloads
        workload = defaultdict(int)
        for a in individual.assignments:
            workload[a.ps_id] += 1
            workload[a.j1_id] += 1
        
        # Find overloaded and underloaded instructors
        avg = sum(workload.values()) / len(self.faculty_ids) if self.faculty_ids else 0
        
        overloaded = [f for f in self.faculty_ids if workload.get(f, 0) > avg + 2]
        underloaded = [f for f in self.faculty_ids if workload.get(f, 0) < avg - 2]
        
        if not overloaded or not underloaded:
            return
        
        # Find a project where overloaded is J1 and can be replaced
        for assignment in individual.assignments:
            if assignment.j1_id in overloaded:
                # Find valid replacement from underloaded
                valid = [u for u in underloaded if u != assignment.ps_id]
                if valid:
                    assignment.j1_id = random.choice(valid)
                    return
    
    def _repair_individual(self, individual: Individual) -> None:
        """
        Repair individual to satisfy constraints.
        
        Fixes:
        1. J1 = PS violations
        2. J1 not instructor violations
        3. Timeslot conflicts
        4. Class gaps
        5. Priority mode violations
        """
        # Fix J1 = PS
        for assignment in individual.assignments:
            if assignment.j1_id == assignment.ps_id:
                valid_j1s = [f for f in self.faculty_ids if f != assignment.ps_id]
                if valid_j1s:
                    assignment.j1_id = random.choice(valid_j1s)
        
        # Fix J1 not instructor
        for assignment in individual.assignments:
            if assignment.j1_id not in self.faculty_ids:
                valid_j1s = [f for f in self.faculty_ids if f != assignment.ps_id]
                if valid_j1s:
                    assignment.j1_id = random.choice(valid_j1s)
        
        # Reorder classes (no gaps)
        self._reorder_all_classes(individual)
        
        # Fix timeslot conflicts
        self._fix_timeslot_conflicts(individual)
    
    def _reorder_all_classes(self, individual: Individual) -> None:
        """Reorder all classes to remove gaps."""
        for class_id in range(individual.class_count):
            projects = [a for a in individual.assignments if a.class_id == class_id]
            projects.sort(key=lambda x: x.order_in_class)
            
            for i, project in enumerate(projects):
                project.order_in_class = i
    
    def _fix_timeslot_conflicts(self, individual: Individual) -> None:
        """Fix timeslot conflicts by shifting assignments."""
        max_iterations = 100
        iteration = 0
        
        while iteration < max_iterations:
            conflicts = self._find_conflicts(individual)
            if not conflicts:
                break
            
            # Fix first conflict
            assignment, conflict_type = conflicts[0]
            
            if conflict_type == 'timeslot':
                # Move to different timeslot
                assignment.order_in_class += 1
            
            iteration += 1
        
        # Final reorder
        self._reorder_all_classes(individual)
    
    def _find_conflicts(self, individual: Individual) -> List[Tuple[ProjectAssignment, str]]:
        """Find conflicting assignments."""
        conflicts = []
        instructor_schedule = defaultdict(list)
        
        for assignment in individual.assignments:
            slot = assignment.order_in_class
            
            # Check PS
            for existing in instructor_schedule[assignment.ps_id]:
                if existing[0] == slot:
                    conflicts.append((assignment, 'timeslot'))
            instructor_schedule[assignment.ps_id].append((slot, assignment))
            
            # Check J1
            for existing in instructor_schedule[assignment.j1_id]:
                if existing[0] == slot:
                    conflicts.append((assignment, 'timeslot'))
            instructor_schedule[assignment.j1_id].append((slot, assignment))
        
        return conflicts


# ============================================================================
# POPULATION INITIALIZER
# ============================================================================

class NSGA2PopulationInitializer:
    """
    Initializes NSGA-II population.
    
    Creates individuals with:
    - Balanced class distribution
    - Same-PS projects grouped
    - Continuity-friendly ordering
    - Workload-balanced J1 assignments
    """
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: NSGA2Config
    ):
        self.projects = list(projects)
        self.project_map = {p.id: p for p in projects}
        self.instructors = list(instructors)
        self.config = config
        
        # Only real instructors
        self.faculty = [
            i for i in instructors
            if i.type == "instructor"
        ]
        self.faculty_ids = [i.id for i in self.faculty]
        
        # Separate by type
        self.ara_projects = [
            p for p in projects
            if str(p.type).lower() in ["interim", "ara", "ara proje"]
        ]
        self.bitirme_projects = [
            p for p in projects
            if str(p.type).lower() in ["final", "bitirme", "bitirme proje"]
        ]
        
        logger.info(f"PopulationInitializer: {len(projects)} projects, {len(self.faculty)} faculty")
    
    def create_population(
        self,
        size: int,
        class_count: int
    ) -> List[Individual]:
        """Create initial population."""
        population = []
        
        for i in range(size):
            if i == 0:
                # First individual: greedy balanced
                individual = self._create_greedy_individual(class_count)
            elif i < size // 3:
                # First third: continuity-focused
                individual = self._create_continuity_focused(class_count)
            elif i < 2 * size // 3:
                # Second third: workload-focused
                individual = self._create_workload_focused(class_count)
            else:
                # Last third: random
                individual = self._create_random_individual(class_count)
            
            population.append(individual)
        
        return population
    
    def _create_greedy_individual(self, class_count: int) -> Individual:
        """Create greedy balanced individual."""
        individual = Individual(class_count=class_count)
        
        # Order projects by priority mode
        ordered_projects = self._order_projects_by_priority()
        
        # Distribute to classes
        class_loads = [0] * class_count
        workloads = defaultdict(int)
        
        for project in ordered_projects:
            # Find class with minimum load
            min_class = min(range(class_count), key=lambda c: class_loads[c])
            
            # Find J1 with minimum workload (not PS)
            valid_j1s = [f for f in self.faculty_ids if f != project.responsible_id]
            if not valid_j1s:
                valid_j1s = self.faculty_ids
            
            j1_id = min(valid_j1s, key=lambda f: workloads[f])
            
            assignment = ProjectAssignment(
                project_id=project.id,
                class_id=min_class,
                order_in_class=class_loads[min_class],
                ps_id=project.responsible_id,
                j1_id=j1_id,
                j2_id=-1
            )
            
            individual.assignments.append(assignment)
            class_loads[min_class] += 1
            workloads[project.responsible_id] += 1
            workloads[j1_id] += 1
        
        return individual
    
    def _create_continuity_focused(self, class_count: int) -> Individual:
        """Create individual focused on continuity (same PS grouped)."""
        individual = Individual(class_count=class_count)
        
        # Group projects by PS
        ps_projects = defaultdict(list)
        for project in self.projects:
            ps_projects[project.responsible_id].append(project)
        
        # Assign each PS's projects to same class
        class_loads = [0] * class_count
        workloads = defaultdict(int)
        current_class = 0
        
        for ps_id, projects in ps_projects.items():
            # Order by priority
            projects = self._order_projects_by_priority(projects)
            
            for project in projects:
                # Find J1
                valid_j1s = [f for f in self.faculty_ids if f != ps_id]
                if not valid_j1s:
                    valid_j1s = self.faculty_ids
                j1_id = min(valid_j1s, key=lambda f: workloads[f])
                
                assignment = ProjectAssignment(
                    project_id=project.id,
                    class_id=current_class,
                    order_in_class=class_loads[current_class],
                    ps_id=ps_id,
                    j1_id=j1_id,
                    j2_id=-1
                )
                
                individual.assignments.append(assignment)
                class_loads[current_class] += 1
                workloads[ps_id] += 1
                workloads[j1_id] += 1
            
            # Move to next class (round-robin)
            current_class = (current_class + 1) % class_count
        
        return individual
    
    def _create_workload_focused(self, class_count: int) -> Individual:
        """Create individual focused on workload balance."""
        individual = Individual(class_count=class_count)
        
        ordered_projects = self._order_projects_by_priority()
        
        # Track workloads
        workloads = defaultdict(int)
        class_loads = [0] * class_count
        
        for project in ordered_projects:
            # Find class with minimum load
            min_class = min(range(class_count), key=lambda c: class_loads[c])
            
            # Find J1 that balances workload best
            ps_id = project.responsible_id
            valid_j1s = [f for f in self.faculty_ids if f != ps_id]
            if not valid_j1s:
                valid_j1s = self.faculty_ids
            
            # Target: average workload
            avg = sum(workloads.values()) / len(self.faculty_ids) if self.faculty_ids else 0
            
            # Pick J1 that brings total closest to average
            j1_id = min(valid_j1s, key=lambda f: abs(workloads[f] + 1 - avg))
            
            assignment = ProjectAssignment(
                project_id=project.id,
                class_id=min_class,
                order_in_class=class_loads[min_class],
                ps_id=ps_id,
                j1_id=j1_id,
                j2_id=-1
            )
            
            individual.assignments.append(assignment)
            class_loads[min_class] += 1
            workloads[ps_id] += 1
            workloads[j1_id] += 1
        
        return individual
    
    def _create_random_individual(self, class_count: int) -> Individual:
        """Create random individual."""
        individual = Individual(class_count=class_count)
        
        projects = self._order_projects_by_priority()
        random.shuffle(projects)
        
        class_loads = [0] * class_count
        
        for project in projects:
            class_id = random.randint(0, class_count - 1)
            
            valid_j1s = [f for f in self.faculty_ids if f != project.responsible_id]
            if not valid_j1s:
                valid_j1s = self.faculty_ids
            j1_id = random.choice(valid_j1s)
            
            assignment = ProjectAssignment(
                project_id=project.id,
                class_id=class_id,
                order_in_class=class_loads[class_id],
                ps_id=project.responsible_id,
                j1_id=j1_id,
                j2_id=-1
            )
            
            individual.assignments.append(assignment)
            class_loads[class_id] += 1
        
        return individual
    
    def _order_projects_by_priority(
        self,
        projects: Optional[List[Project]] = None
    ) -> List[Project]:
        """Order projects according to priority mode."""
        if projects is None:
            projects = self.projects
        
        if self.config.priority_mode == PriorityMode.ARA_ONCE:
            # ARA first, then BITIRME
            ara = [p for p in projects if p in self.ara_projects]
            bitirme = [p for p in projects if p in self.bitirme_projects]
            other = [p for p in projects if p not in self.ara_projects and p not in self.bitirme_projects]
            return ara + bitirme + other
        
        elif self.config.priority_mode == PriorityMode.BITIRME_ONCE:
            # BITIRME first, then ARA
            ara = [p for p in projects if p in self.ara_projects]
            bitirme = [p for p in projects if p in self.bitirme_projects]
            other = [p for p in projects if p not in self.ara_projects and p not in self.bitirme_projects]
            return bitirme + ara + other
        
        else:  # ESIT
            # Random order
            result = list(projects)
            random.shuffle(result)
            return result


# ============================================================================
# NSGA-II CORE ALGORITHM
# ============================================================================

class NSGA2Core:
    """
    Core NSGA-II algorithm implementation.
    
    Features:
    - Non-dominated sorting
    - Crowding distance calculation
    - Elitism
    """
    
    def __init__(self, config: NSGA2Config):
        self.config = config
    
    def fast_non_dominated_sort(
        self,
        population: List[Individual]
    ) -> List[List[Individual]]:
        """
        Fast non-dominated sorting algorithm.
        
        Returns list of fronts (front 0 is Pareto front).
        """
        fronts = [[]]
        
        for p in population:
            p.dominated_solutions = []
            p.domination_count = 0
            
            for q in population:
                if self._dominates(p, q):
                    p.dominated_solutions.append(q)
                elif self._dominates(q, p):
                    p.domination_count += 1
            
            if p.domination_count == 0:
                p.rank = 0
                fronts[0].append(p)
        
        i = 0
        while fronts[i]:
            next_front = []
            for p in fronts[i]:
                for q in p.dominated_solutions:
                    q.domination_count -= 1
                    if q.domination_count == 0:
                        q.rank = i + 1
                        next_front.append(q)
            i += 1
            fronts.append(next_front)
        
        return fronts[:-1]  # Remove empty last front
    
    def calculate_crowding_distance(self, front: List[Individual]) -> None:
        """
        Calculate crowding distance for individuals in a front.
        """
        if len(front) == 0:
            return
        
        n = len(front)
        num_objectives = len(front[0].objectives)
        
        for ind in front:
            ind.crowding_distance = 0.0
        
        for m in range(num_objectives):
            # Sort by objective m
            front.sort(key=lambda x: x.objectives[m])
            
            # Boundary points get infinite distance
            front[0].crowding_distance = float('inf')
            front[-1].crowding_distance = float('inf')
            
            # Calculate distance for others
            obj_range = front[-1].objectives[m] - front[0].objectives[m]
            if obj_range == 0:
                continue
            
            for i in range(1, n - 1):
                front[i].crowding_distance += (
                    (front[i + 1].objectives[m] - front[i - 1].objectives[m]) / obj_range
                )
    
    def _dominates(self, p: Individual, q: Individual) -> bool:
        """Check if p dominates q (all objectives <= and at least one <)."""
        if not p.objectives or not q.objectives:
            return False
        
        at_least_one_better = False
        
        for i in range(len(p.objectives)):
            if p.objectives[i] > q.objectives[i]:
                return False
            if p.objectives[i] < q.objectives[i]:
                at_least_one_better = True
        
        return at_least_one_better
    
    def select_next_generation(
        self,
        population: List[Individual],
        offspring: List[Individual],
        pop_size: int
    ) -> List[Individual]:
        """
        Select next generation using elitism.
        
        Combines population and offspring, then selects best.
        """
        combined = population + offspring
        
        # Non-dominated sorting
        fronts = self.fast_non_dominated_sort(combined)
        
        new_population = []
        front_idx = 0
        
        while len(new_population) + len(fronts[front_idx]) <= pop_size:
            # Calculate crowding distance
            self.calculate_crowding_distance(fronts[front_idx])
            
            # Add entire front
            new_population.extend(fronts[front_idx])
            front_idx += 1
            
            if front_idx >= len(fronts):
                break
        
        # Add remaining from last front
        if len(new_population) < pop_size and front_idx < len(fronts):
            self.calculate_crowding_distance(fronts[front_idx])
            
            # Sort by crowding distance (descending)
            fronts[front_idx].sort(key=lambda x: -x.crowding_distance)
            
            remaining = pop_size - len(new_population)
            new_population.extend(fronts[front_idx][:remaining])
        
        return new_population


# ============================================================================
# MAIN NSGA-II SCHEDULER
# ============================================================================

class NSGA2Scheduler(OptimizationAlgorithm):
    """
    NSGA-II Scheduler for Academic Project Jury Assignment.
    
    Single-phase multi-objective optimization that produces:
    - Project → Class assignment
    - Order within class
    - J1 assignment
    - PS (fixed)
    - J2 (placeholder: [Araştırma Görevlisi])
    """
    
    # J2 Placeholder constant
    J2_PLACEHOLDER = "[Araştırma Görevlisi]"
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.name = "NSGA-II Multi-Objective Scheduler"
        self.description = (
            "Multi-objective genetic algorithm for academic project scheduling "
            "with workload balance, continuity, and class change optimization."
        )
        
        self.config = NSGA2Config()
        self.projects: List[Project] = []
        self.instructors: List[Instructor] = []
        self.classrooms: List[Dict] = []
        
        # Components
        self.objective_calculator: Optional[NSGA2ObjectiveCalculator] = None
        self.constraint_checker: Optional[NSGA2ConstraintChecker] = None
        self.genetic_operators: Optional[NSGA2GeneticOperators] = None
        self.population_initializer: Optional[NSGA2PopulationInitializer] = None
        self.nsga2_core: Optional[NSGA2Core] = None
        
        logger.info("NSGA2Scheduler initialized")
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """Initialize algorithm with input data."""
        logger.info("=" * 60)
        logger.info("NSGA-II INITIALIZATION")
        logger.info("=" * 60)
        
        # Parse configuration
        self._parse_config(data)
        
        # Parse input data
        self._parse_input_data(data)
        
        # Initialize components
        self._initialize_components()
        
        logger.info(f"Projects: {len(self.projects)}")
        logger.info(f"Instructors: {len(self.instructors)} (Faculty: {len([i for i in self.instructors if i.type == 'instructor'])})")
        logger.info(f"Classrooms: {len(self.classrooms)}")
        logger.info(f"Class count: {self.config.class_count}")
        logger.info(f"Priority mode: {self.config.priority_mode.value}")
        logger.info(f"Population size: {self.config.population_size}")
        logger.info(f"Max generations: {self.config.max_generations}")
    
    def optimize(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run NSGA-II optimization.
        
        Returns final schedule with all assignments.
        """
        logger.info("=" * 60)
        logger.info("NSGA-II OPTIMIZATION START")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Run optimization for configured class count
        if self.config.auto_class_count:
            # Try different class counts
            best_solution = None
            best_score = float('inf')
            
            for class_count in [5, 6, 7]:
                if class_count > len(self.classrooms):
                    continue
                
                logger.info(f"\n--- Trying class_count = {class_count} ---")
                solution, score = self._run_nsga2(class_count)
                
                if score < best_score:
                    best_score = score
                    best_solution = solution
                    logger.info(f"New best score: {best_score:.2f} with {class_count} classes")
        else:
            # Use configured class count
            best_solution, best_score = self._run_nsga2(self.config.class_count)
        
        elapsed = time.time() - start_time
        
        # Convert to output format
        result = self._convert_to_output(best_solution)
        result['execution_time'] = elapsed
        result['best_score'] = best_score
        
        logger.info("=" * 60)
        logger.info(f"NSGA-II COMPLETE - Time: {elapsed:.2f}s, Score: {best_score:.2f}")
        logger.info("=" * 60)
        
        return result
    
    def _run_nsga2(self, class_count: int) -> Tuple[Individual, float]:
        """
        Run NSGA-II for given class count.
        
        Returns (best_individual, weighted_score).
        """
        logger.info(f"Running NSGA-II with {class_count} classes")
        
        # Update config
        self.config.class_count = class_count
        
        # Initialize population
        population = self.population_initializer.create_population(
            self.config.population_size,
            class_count
        )
        
        # Evaluate initial population
        for individual in population:
            self._evaluate_individual(individual)
        
        # Non-dominated sorting
        fronts = self.nsga2_core.fast_non_dominated_sort(population)
        for front in fronts:
            self.nsga2_core.calculate_crowding_distance(front)
        
        # Track best
        best_individual = None
        best_score = float('inf')
        stagnation_counter = 0
        
        # Main loop
        for generation in range(self.config.max_generations):
            # Create offspring
            offspring = []
            
            while len(offspring) < self.config.population_size:
                # Selection
                parent1 = self.genetic_operators.tournament_selection(
                    population,
                    self.config.tournament_size
                )
                parent2 = self.genetic_operators.tournament_selection(
                    population,
                    self.config.tournament_size
                )
                
                # Crossover
                child1, child2 = self.genetic_operators.crossover(parent1, parent2)
                
                # Mutation
                child1 = self.genetic_operators.mutate(child1)
                child2 = self.genetic_operators.mutate(child2)
                
                offspring.extend([child1, child2])
            
            # Trim to population size
            offspring = offspring[:self.config.population_size]
            
            # Evaluate offspring
            for individual in offspring:
                self._evaluate_individual(individual)
            
            # Select next generation
            population = self.nsga2_core.select_next_generation(
                population,
                offspring,
                self.config.population_size
            )
            
            # Find best in current population
            current_best = min(population, key=lambda x: self._weighted_score(x))
            current_score = self._weighted_score(current_best)
            
            if current_score < best_score:
                best_score = current_score
                best_individual = current_best.copy()
                stagnation_counter = 0
                
                if generation % 10 == 0:
                    logger.info(f"Gen {generation}: New best score = {best_score:.2f}")
                else:
                    stagnation_counter += 1
            
            # Check stagnation
            if stagnation_counter >= self.config.stagnation_limit:
                logger.info(f"Stopping at generation {generation} due to stagnation")
                break
                
        return best_individual, best_score
    
    def _evaluate_individual(self, individual: Individual) -> None:
        """Evaluate objectives and feasibility for individual."""
        # Check feasibility
        is_feasible, violations = self.constraint_checker.check_feasibility(individual)
        individual.is_feasible = is_feasible
        individual.constraint_violations = violations
        
        # Calculate objectives
        objectives = self.objective_calculator.evaluate(individual)
        
        # Add penalty for constraint violations
        if not is_feasible:
            penalty = violations * 10000
            objectives.h1_continuity += penalty
            objectives.h2_workload += penalty
            objectives.h3_class_change += penalty
        
        individual.objectives = objectives.to_list()
    
    def _weighted_score(self, individual: Individual) -> float:
        """Calculate weighted score for final selection."""
        if not individual.objectives:
            return float('inf')
        
        return (
            self.config.weight_h1 * individual.objectives[0] +
            self.config.weight_h2 * individual.objectives[1] +
            self.config.weight_h3 * individual.objectives[2] +
            self.config.weight_h4 * individual.objectives[3]
        )
    
    def _convert_to_output(self, individual: Individual) -> Dict[str, Any]:
        """Convert individual to output format."""
        if individual is None:
            return self._create_empty_output()
        
        # Build instructor lookup
        instructor_map = {i.id: i for i in self.instructors}
        
        # Build classroom lookup
        classroom_map = {i: self.classrooms[i] if i < len(self.classrooms) else {'id': i + 1, 'name': f'Class{i + 1}'} 
                        for i in range(individual.class_count)}
        
        assignments = []
        
        for assignment in individual.assignments:
            # Get classroom
            classroom = classroom_map.get(assignment.class_id, {'id': assignment.class_id + 1, 'name': f'D{105 + assignment.class_id}'})
            
            # Build instructor list
            instructors = [
                assignment.ps_id,
                assignment.j1_id,
                {
                    'id': -1,
                    'name': self.J2_PLACEHOLDER,
                    'is_placeholder': True
                }
            ]
            
            # Timeslot = order + 1 (1-indexed)
            timeslot_id = assignment.order_in_class + 1
            
            assignments.append({
                'project_id': assignment.project_id,
                'classroom_id': classroom.get('id', assignment.class_id + 1),
                'timeslot_id': timeslot_id,
                'instructors': instructors,
                'is_makeup': False
            })
        
        # Calculate final scores
        objectives = self.objective_calculator.evaluate(individual)
        
        return {
            'assignments': assignments,
            'stats': {
                'total_projects': len(assignments),
                'class_count': individual.class_count,
                'h1_continuity': objectives.h1_continuity,
                'h2_workload': objectives.h2_workload,
                'h3_class_change': objectives.h3_class_change,
                'h4_class_load': objectives.h4_class_load,
                'weighted_score': objectives.weighted_sum(self.config)
            }
        }
    
    def _create_empty_output(self) -> Dict[str, Any]:
        """Create empty output for error cases."""
        return {
            'assignments': [],
            'stats': {
                'total_projects': 0,
                'class_count': 0,
                'error': 'No valid solution found'
            }
        }
    
    def _parse_config(self, data: Dict[str, Any]) -> None:
        """Parse configuration from data."""
        config = data.get('config', {})
        
        # Population and generations
        if 'population_size' in config:
            self.config.population_size = config['population_size']
        if 'max_generations' in config:
            self.config.max_generations = config['max_generations']
        
        # Class count
        if 'classroom_count' in data:
            self.config.class_count = data['classroom_count']
            self.config.auto_class_count = False
        elif 'class_count' in config:
            self.config.class_count = config['class_count']
            self.config.auto_class_count = False
        
        # Priority mode
        if 'priority_mode' in config:
            try:
                self.config.priority_mode = PriorityMode(config['priority_mode'])
            except ValueError:
                pass
        
        # Time penalty mode
        if 'time_penalty_mode' in config:
            try:
                self.config.time_penalty_mode = TimePenaltyMode(config['time_penalty_mode'])
            except ValueError:
                pass
        
        # Workload mode
        if 'workload_constraint_mode' in config:
            try:
                self.config.workload_constraint_mode = WorkloadConstraintMode(config['workload_constraint_mode'])
            except ValueError:
                pass
        
        # Weights
        if 'weight_h1' in config:
            self.config.weight_h1 = config['weight_h1']
        if 'weight_h2' in config:
            self.config.weight_h2 = config['weight_h2']
        if 'weight_h3' in config:
            self.config.weight_h3 = config['weight_h3']
        if 'weight_h4' in config:
            self.config.weight_h4 = config['weight_h4']
    
    def _parse_input_data(self, data: Dict[str, Any]) -> None:
        """Parse projects, instructors, classrooms from data."""
        # Parse projects
        self.projects = []
        for p in data.get('projects', []):
            proj_type = str(p.get('type', p.get('project_type', 'interim'))).lower()
            if proj_type in ['ara', 'ara proje']:
                proj_type = 'interim'
            elif proj_type in ['bitirme', 'bitirme proje']:
                proj_type = 'final'
            
            project = Project(
                id=p.get('id', 0),
                title=p.get('title', f"Project {p.get('id', 0)}"),
                type=proj_type,
                responsible_id=p.get('instructor_id', p.get('responsible_instructor_id', p.get('responsible_id', 0))),
                is_makeup=p.get('is_makeup', False)
            )
            self.projects.append(project)
        
        # Parse instructors
        self.instructors = []
        for i in data.get('instructors', []):
            instructor = Instructor(
                id=i.get('id', 0),
                name=i.get('name', f"Instructor {i.get('id', 0)}"),
                type=i.get('type', 'instructor')
            )
            self.instructors.append(instructor)
        
        # Parse classrooms
        self.classrooms = data.get('classrooms', [])
        
        # Update class count based on available classrooms
        if self.classrooms and self.config.auto_class_count:
            self.config.class_count = min(len(self.classrooms), 7)
    
    def _initialize_components(self) -> None:
        """Initialize algorithm components."""
        self.objective_calculator = NSGA2ObjectiveCalculator(
            self.projects,
            self.instructors,
            self.config
        )
        
        self.constraint_checker = NSGA2ConstraintChecker(
            self.projects,
            self.instructors,
            self.config
        )
        
        self.genetic_operators = NSGA2GeneticOperators(
            self.projects,
            self.instructors,
            self.config
        )
        
        self.population_initializer = NSGA2PopulationInitializer(
            self.projects,
            self.instructors,
            self.config
        )
        
        self.nsga2_core = NSGA2Core(self.config)


# ============================================================================
# ALGORITHM FACTORY REGISTRATION
# ============================================================================

def create_nsga2_scheduler(params: Optional[Dict[str, Any]] = None) -> NSGA2Scheduler:
    """Factory function to create NSGA2Scheduler."""
    return NSGA2Scheduler(params)


# Export main class
__all__ = [
    'NSGA2Scheduler',
    'NSGA2Config',
    'PriorityMode',
    'TimePenaltyMode',
    'WorkloadConstraintMode',
    'create_nsga2_scheduler'
]

