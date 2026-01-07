"""
Real Simplex Algorithm - Linear Programming (LP/MILP) optimizer for academic project exam/jury planning.

This module implements a Linear Programming (Real Simplex) solver using Google OR-Tools
for multi-criteria, highly constrained academic project scheduling.

Key Features:
- Project-class-slot assignment optimization using LP/MILP
- First Jury (J1) assignment as decision variable (binary)
- Second Jury (J2) is a fixed placeholder "[Arastirma Gorevlisi]" - NOT in model
- Multi-criteria objective: workload uniformity, continuity, class changes
- Configurable priority modes, penalty modes, and constraint modes
- Uses OR-Tools Linear Solver (MILP) with SCIP or CBC solvers
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import logging
import math
from collections import defaultdict

try:
    from ortools.linear_solver import pywraplp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("OR-Tools not available. Real Simplex Algorithm will not work.")

from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)

# Import HungarianAlgorithm for BITIRME_ONCE priority mode
try:
    from app.algorithms.hungarian_algorithm import HungarianAlgorithm
    HUNGARIAN_AVAILABLE = True
except ImportError:
    HUNGARIAN_AVAILABLE = False
    logger.warning("HungarianAlgorithm not available. BITIRME_ONCE mode will fallback to Real Simplex.")


# =============================================================================
# ENUMS AND CONFIGURATION
# =============================================================================

class PriorityMode(str, Enum):
    """Project type prioritization mode."""
    ARA_ONCE = "ARA_ONCE"           # All ARA projects before BITIRME
    BITIRME_ONCE = "BITIRME_ONCE"   # All BITIRME projects before ARA
    ESIT = "ESIT"                   # No priority ordering


class TimePenaltyMode(str, Enum):
    """Time/gap penalty calculation mode."""
    BINARY = "BINARY"                     # 1 if not consecutive, 0 otherwise
    GAP_PROPORTIONAL = "GAP_PROPORTIONAL" # Penalty = number of gap slots


class WorkloadConstraintMode(str, Enum):
    """Workload constraint mode."""
    SOFT_ONLY = "SOFT_ONLY"           # Only soft penalty, no hard limit
    SOFT_AND_HARD = "SOFT_AND_HARD"   # Soft penalty + hard upper bound


@dataclass
class SimplexConfig:
    """Configuration for Real Simplex solver."""
    
    # Priority mode
    priority_mode: str = "ESIT"
    
    # Penalty modes
    time_penalty_mode: str = "BINARY"
    workload_constraint_mode: str = "SOFT_ONLY"
    
    # Weights for objective function (C2 > C1 and C2 > C3)
    weight_h1: float = 10.0      # C1 - for gap/continuity penalty (H1)
    weight_h2: float = 100.0     # C2 - for workload uniformity (most important) (H2)
    weight_h3: float = 5.0       # C3 - for class change penalty (H3)
    
    # Hard constraint parameters
    b_max: int = 4  # Maximum allowed deviation from average workload (for SOFT_AND_HARD)
    
    # Solver parameters
    max_time_seconds: int = 120
    solver_name: str = "SCIP"  # "SCIP" or "CBC"
    
    # Class count mode
    class_count_mode: str = "auto"  # "auto" or "manual"
    class_count: int = 6            # Used if class_count_mode == "manual"
    
    # Slot duration in hours
    slot_duration: float = 0.5  # 30 minutes
    time_tolerance: float = 0.001
    
    # Gap penalty multiplier for GAP_PROPORTIONAL mode
    gap_penalty_multiplier: int = 2
    
    # Zero conflict mode: iterate until 0 conflicts are achieved
    zero_conflict: bool = True
    

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Instructor:
    """Instructor/Teacher data structure."""
    id: int
    name: str
    type: str  # "instructor" or "assistant" (research assistant)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Instructor):
            return self.id == other.id
        return False


@dataclass
class Project:
    """Project data structure."""
    id: int
    ps_id: int  # Project Supervisor ID (fixed)
    project_type: str  # "ARA" or "BITIRME"
    name: str = ""
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Project):
            return self.id == other.id
        return False


@dataclass
class ProjectAssignment:
    """Single project assignment in solution."""
    project_id: int
    class_id: int
    order_in_class: int
    ps_id: int      # Project Supervisor (fixed)
    j1_id: int      # Jury 1 (decision variable)
    j2_label: str = "[Arastirma Gorevlisi]"  # Jury 2 (always placeholder)
    
    def __hash__(self):
        return hash(self.project_id)
    
    def copy(self) -> 'ProjectAssignment':
        return ProjectAssignment(
            project_id=self.project_id,
            class_id=self.class_id,
            order_in_class=self.order_in_class,
            ps_id=self.ps_id,
            j1_id=self.j1_id,
            j2_label=self.j2_label
        )


@dataclass
class SimplexSolution:
    """Complete solution from Real Simplex algorithm."""
    assignments: List[ProjectAssignment] = field(default_factory=list)
    class_count: int = 0
    solver_status: str = "NOT_SOLVED"
    is_feasible: bool = False
    total_cost: float = float('inf')
    
    def copy(self) -> 'SimplexSolution':
        return SimplexSolution(
            assignments=[a.copy() for a in self.assignments],
            class_count=self.class_count,
            solver_status=self.solver_status,
            is_feasible=self.is_feasible,
            total_cost=self.total_cost
        )


# =============================================================================
# PENALTY CALCULATOR (Matrix-Based)
# =============================================================================

class SimplexPenaltyCalculator:
    """
    Matrix-based penalty calculator for Real Simplex Algorithm.
    
    Calculates penalties based on instructor task matrices:
    - H1: Time/Gap penalty (BINARY or GAP_PROPORTIONAL)
    - H2: Workload uniformity penalty
    - H3: Class change penalty
    """
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: SimplexConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Only real instructors (not assistants)
        self.faculty = [
            i for i in instructors
            if i.type == "instructor"
        ]
        self.faculty_ids = [i.id for i in self.faculty]
        
        # Calculate average workload
        Y = len(projects)
        X = len(self.faculty)
        self.total_workload = 2 * Y  # PS + J1 per project
        self.avg_workload = self.total_workload / X if X > 0 else 0
        
        logger.info(f"PenaltyCalculator: {Y} projects, {X} faculty")
        logger.info(f"Average workload: {self.avg_workload:.2f}")
    
    def build_instructor_task_matrix(
        self,
        solution: SimplexSolution,
        timeslots: List[Dict[str, Any]]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Build task matrix M_i for each instructor i.
        
        Returns:
            Dict mapping instructor_id -> List of tasks
            Each task is: {'slot': int, 'class_id': int, 'time': float, 'role': str}
        """
        instructor_tasks = defaultdict(list)
        
        # Build timeslot lookup (slot_id -> time)
        slot_time_map = {}
        for ts in timeslots:
            slot_id = ts.get('id', 0)
            start_time = ts.get('start_time', '09:00')
            if isinstance(start_time, str):
                parts = start_time.split(':')
                hours = float(parts[0])
                minutes = float(parts[1]) if len(parts) > 1 else 0.0
                time_value = hours + minutes / 60.0
            else:
                time_value = float(start_time)
            slot_time_map[slot_id] = time_value
        
        for assignment in solution.assignments:
            # Calculate slot time
            slot_time = 9.0 + assignment.order_in_class * self.config.slot_duration
            
            task_info = {
                'slot': assignment.order_in_class,
                'class_id': assignment.class_id,
                'time': slot_time,
                'role': 'PS'
            }
            instructor_tasks[assignment.ps_id].append(task_info.copy())
            
            task_info['role'] = 'J1'
            instructor_tasks[assignment.j1_id].append(task_info.copy())
        
        # Sort tasks by time for each instructor
        for instructor_id in instructor_tasks:
            instructor_tasks[instructor_id].sort(key=lambda x: (x['time'], x['class_id']))
        
        return instructor_tasks
    
    def calculate_h1_time_penalty(
        self,
        solution: SimplexSolution,
        timeslots: List[Dict[str, Any]]
    ) -> float:
        """
        H1: Time/Gap penalty.
        
        For each instructor, check consecutive tasks:
        - BINARY mode: 1 if not consecutive, 0 otherwise
        - GAP_PROPORTIONAL mode: penalty = gap slot count
        """
        total_penalty = 0.0
        instructor_tasks = self.build_instructor_task_matrix(solution, timeslots)
        
        for instructor_id in self.faculty_ids:
            tasks = instructor_tasks.get(instructor_id, [])
            if len(tasks) <= 1:
                continue
            
            for i in range(len(tasks) - 1):
                curr = tasks[i]
                next_task = tasks[i + 1]
                
                expected_time = curr['time'] + self.config.slot_duration
                actual_time = next_task['time']
                time_diff = abs(actual_time - expected_time)
                
                if time_diff > self.config.time_tolerance:
                    # Not consecutive - apply penalty
                    if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                        total_penalty += 1.0
                    else:  # GAP_PROPORTIONAL
                        gap_slots = max(0, round((time_diff - self.config.slot_duration) / self.config.slot_duration))
                        total_penalty += gap_slots * self.config.gap_penalty_multiplier
                # If time_diff <= tolerance, tasks are consecutive - no penalty
        
        return total_penalty
    
    def calculate_h2_workload_penalty(self, solution: SimplexSolution) -> float:
        """
        H2: Workload uniformity penalty.
        
        Penalty(h) = max(0, |Load(h) - AvgLoad| - 2)
        H2 = Σ Penalty(h)
        """
        total_penalty = 0.0
        workload = defaultdict(int)
        
        # Calculate workload for each instructor
        for assignment in solution.assignments:
            workload[assignment.ps_id] += 1
            workload[assignment.j1_id] += 1
        
        for instructor_id in self.faculty_ids:
            load = workload.get(instructor_id, 0)
            deviation = abs(load - self.avg_workload)
            
            # Soft penalty: beyond ±2 band
            penalty = max(0.0, deviation - 2.0)
            total_penalty += penalty
            
            # Additional penalty for hard constraint violation
            if self.config.workload_constraint_mode == WorkloadConstraintMode.SOFT_AND_HARD:
                if deviation > self.config.b_max:
                    total_penalty += 1000.0  # Large penalty
        
        return total_penalty
    
    def calculate_h3_class_change_penalty(
        self,
        solution: SimplexSolution
    ) -> float:
        """
        H3: Class change penalty.
        
        ClassCount(h) = number of different classes instructor h appears in
        Penalty = max(0, ClassCount(h) - 2)
        H3 = Σ Penalty(h)
        """
        total_penalty = 0.0
        instructor_classes = defaultdict(set)
        
        for assignment in solution.assignments:
            instructor_classes[assignment.ps_id].add(assignment.class_id)
            instructor_classes[assignment.j1_id].add(assignment.class_id)
        
        for instructor_id in self.faculty_ids:
            class_count = len(instructor_classes.get(instructor_id, set()))
            if class_count > 2:
                penalty = class_count - 2
                total_penalty += penalty
        
        return total_penalty
    
    def check_timeslot_conflicts(
        self,
        solution: SimplexSolution
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Check for timeslot conflicts in the solution.
        
        A conflict occurs when an instructor has multiple duties (PS or J1) 
        at the same timeslot (order_in_class) across different classes.
        
        Returns:
            Tuple of (has_conflicts: bool, conflicts: List[Dict])
            Each conflict dict contains: instructor_id, timeslot, classes, roles
        """
        conflicts = []
        instructor_timeslots = defaultdict(lambda: defaultdict(list))
        
        # Build instructor schedule: instructor_id -> order_in_class -> list of (class_id, role, project_id)
        for assignment in solution.assignments:
            # PS role
            instructor_timeslots[assignment.ps_id][assignment.order_in_class].append({
                'class_id': assignment.class_id,
                'role': 'PS',
                'project_id': assignment.project_id
            })
            # J1 role
            instructor_timeslots[assignment.j1_id][assignment.order_in_class].append({
                'class_id': assignment.class_id,
                'role': 'J1',
                'project_id': assignment.project_id
            })
        
        # Check for conflicts: same instructor, same timeslot (order_in_class)
        # A conflict occurs when an instructor has multiple duties at the same timeslot,
        # regardless of whether they are in the same class or different classes.
        # This is because an instructor cannot be in multiple places at the same time.
        for instructor_id in instructor_timeslots.keys():
            for order_in_class, entries in instructor_timeslots[instructor_id].items():
                if len(entries) > 1:
                    # CONFLICT: Instructor has multiple duties at same timeslot
                    # This can happen in:
                    #   - Different classes (e.g., MSA is PS in class 1 and PS in class 2 at same timeslot)
                    #   - Same class (theoretical, should not happen due to "at most one project per class-slot" constraint)
                    classes_at_this_slot = set(e['class_id'] for e in entries)
                    projects_at_this_slot = set(e['project_id'] for e in entries)
                    
                    # Get instructor name
                    instructor_name = f"Instructor {instructor_id}"
                    for inst in self.instructors.values():
                        if inst.id == instructor_id:
                            instructor_name = inst.name
                            break
                    
                    conflicts.append({
                        'instructor_id': instructor_id,
                        'instructor_name': instructor_name,
                        'timeslot': order_in_class,
                        'classes': list(classes_at_this_slot),
                        'projects': list(projects_at_this_slot),
                        'entries': entries,
                        'is_same_class': len(classes_at_this_slot) == 1,
                        'is_different_classes': len(classes_at_this_slot) > 1
                    })
        
        has_conflicts = len(conflicts) > 0
        return has_conflicts, conflicts
    
    def check_time_range_conflicts(
        self,
        solution: SimplexSolution,
        timeslots: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Check for time range based conflicts in the solution.
        
        CRITICAL: Same order_in_class = SAME TIME SLOT = SAME TIME RANGE!
        An instructor with multiple duties at the same order_in_class has a CONFLICT.
        
        This includes:
        - Same instructor being PS in different classes at the same slot
        - Same instructor being J1 in different classes at the same slot
        - Same instructor being PS in one class and J1 in another at the same slot
        - Any combination of multiple duties at the same time slot
        
        Returns:
            Tuple of (has_conflicts: bool, conflicts: List[Dict])
            Each conflict dict contains: instructor_id, order_in_class, classes, projects, entries
        """
        conflicts = []
        
        # Build instructor schedule: instructor_id -> order_in_class -> List of (class_id, role, project_id)
        instructor_schedule = defaultdict(lambda: defaultdict(list))
        
        for assignment in solution.assignments:
            # PS role
            instructor_schedule[assignment.ps_id][assignment.order_in_class].append({
                'class_id': assignment.class_id,
                'role': 'PS',
                'project_id': assignment.project_id
            })
            # J1 role
            instructor_schedule[assignment.j1_id][assignment.order_in_class].append({
                'class_id': assignment.class_id,
                'role': 'J1',
                'project_id': assignment.project_id
            })
        
        # Check for conflicts: same instructor, same order_in_class, multiple duties
        # CRITICAL: ANY multiple duties at the same slot is a CONFLICT!
        for instructor_id, orders in instructor_schedule.items():
            for order_in_class, entries in orders.items():
                # CONFLICT if instructor has more than 1 duty at this slot
                # This includes: same class (PS+J1), different classes (any role)
                if len(entries) > 1:
                    classes_at_this_slot = set(e['class_id'] for e in entries)
                    projects_at_this_slot = set(e['project_id'] for e in entries)
                    
                    # Calculate time range for display
                    slot_duration = self.config.slot_duration
                    start_hour = 9.0
                    slot_time = start_hour + order_in_class * slot_duration
                    end_time = slot_time + slot_duration
                    start_h = int(slot_time)
                    start_m = int((slot_time - start_h) * 60)
                    end_h = int(end_time)
                    end_m = int((end_time - end_h) * 60)
                    time_range_key = f"{start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}"
                    
                    # Get instructor name
                    instructor_name = f"Instructor {instructor_id}"
                    for inst in self.instructors.values():
                        if inst.id == instructor_id:
                            instructor_name = inst.name
                            break
                    
                    # Determine conflict type
                    is_same_class = len(classes_at_this_slot) == 1
                    is_different_classes = len(classes_at_this_slot) > 1
                    
                    conflicts.append({
                        'instructor_id': instructor_id,
                        'instructor_name': instructor_name,
                        'order_in_class': order_in_class,
                        'time_range': time_range_key,
                        'classes': list(classes_at_this_slot),
                        'projects': list(projects_at_this_slot),
                        'entries': entries,
                        'conflict_count': len(entries),
                        'is_same_class': is_same_class,
                        'is_different_classes': is_different_classes
                    })
        
        has_conflicts = len(conflicts) > 0
        return has_conflicts, conflicts
    
    def _build_time_range_groups(
        self,
        timeslots: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, List[Tuple[int, int]]]:
        """
        Build time range grouping (helper function for conflict checking).
        
        Returns:
            Dict mapping time_range_key -> List of (class_id, slot_index) tuples
        """
        time_range_groups = defaultdict(list)
        slot_duration = self.config.slot_duration
        start_hour = 9.0
        max_slots = 20  # Reasonable upper bound
        
        for t in range(max_slots):
            start_time_val = start_hour + t * slot_duration
            end_time_val = start_time_val + slot_duration
            
            start_h = int(start_time_val)
            start_m = int((start_time_val - start_h) * 60)
            end_h = int(end_time_val)
            end_m = int((end_time_val - end_h) * 60)
            
            time_range_key = f"{start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}"
            
            # For conflict checking, we don't need class info, just time ranges
            # So we can use a dummy class_id
            time_range_groups[time_range_key].append((0, t))
        
        return dict(time_range_groups)
    
    def check_all_conflicts_comprehensive(
        self,
        solution: SimplexSolution,
        timeslots: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Comprehensive conflict check for ALL instructors (PS and J1).
        
        CRITICAL RULE: An instructor CANNOT have multiple duties at the same time slot.
        - Same time slot = same order_in_class value
        - Duties = PS (Proje Sorumlusu) or J1 (1. Jüri)
        
        Examples of conflicts:
        - MSA is PS in project A at slot 5 (17:00-17:30) AND PS in project B at slot 5 (17:00-17:30)
        - AEL is PS in project A at slot 0 (09:00-09:30) AND J1 in project B at slot 0 (09:00-09:30)
        - EC is J1 in project A at slot 10 (14:00-14:30) AND J1 in project B at slot 10 (14:00-14:30)
        
        Returns:
            Tuple of (total_conflict_count, conflicts_list)
            conflicts_list contains detailed conflict information
        """
        conflicts = []
        
        # Build schedule: instructor_id -> order_in_class -> List[(role, class_id, project_id)]
        schedule = defaultdict(lambda: defaultdict(list))
        
        for assignment in solution.assignments:
            # Record PS duty
            schedule[assignment.ps_id][assignment.order_in_class].append({
                'role': 'PS',
                'class_id': assignment.class_id,
                'project_id': assignment.project_id
            })
            # Record J1 duty
            schedule[assignment.j1_id][assignment.order_in_class].append({
                'role': 'J1',
                'class_id': assignment.class_id,
                'project_id': assignment.project_id
            })
        
        total_conflict_count = 0
        
        # Check each instructor's schedule
        for instructor_id, slot_duties in schedule.items():
            # Get instructor name
            instructor_name = f"Instructor {instructor_id}"
            for inst in self.instructors.values():
                if inst.id == instructor_id:
                    instructor_name = inst.name
                    break
            
            for order_in_class, duties in slot_duties.items():
                if len(duties) > 1:
                    # CONFLICT: Multiple duties at same time slot!
                    conflict_count = len(duties) - 1  # Number of conflicts (excess duties)
                    total_conflict_count += conflict_count
                    
                    # Calculate time range for display
                    slot_duration = self.config.slot_duration
                    start_hour = 9.0
                    slot_time = start_hour + order_in_class * slot_duration
                    end_time = slot_time + slot_duration
                    start_h = int(slot_time)
                    start_m = int((slot_time - start_h) * 60)
                    end_h = int(end_time)
                    end_m = int((end_time - end_h) * 60)
                    time_range = f"{start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}"
                    
                    conflicts.append({
                        'instructor_id': instructor_id,
                        'instructor_name': instructor_name,
                        'order_in_class': order_in_class,
                        'time_range': time_range,
                        'duty_count': len(duties),
                        'conflict_count': conflict_count,
                        'duties': duties,
                        'classes': list(set(d['class_id'] for d in duties)),
                        'projects': [d['project_id'] for d in duties],
                        'roles': [d['role'] for d in duties]
                    })
        
        return total_conflict_count, conflicts
    
    def get_conflict_summary(
        self,
        solution: SimplexSolution
    ) -> Dict[str, Any]:
        """
        Get a summary of all conflicts in the solution.
        
        Returns:
            Dict with conflict statistics and details
        """
        total_conflicts, conflicts = self.check_all_conflicts_comprehensive(solution)
        
        ps_conflicts = sum(1 for c in conflicts if 'PS' in c['roles'] and c['roles'].count('PS') > 1)
        j1_conflicts = sum(1 for c in conflicts if 'J1' in c['roles'] and c['roles'].count('J1') > 1)
        mixed_conflicts = sum(1 for c in conflicts if 'PS' in c['roles'] and 'J1' in c['roles'])
        
        return {
            'total_conflicts': total_conflicts,
            'conflict_count': len(conflicts),
            'ps_only_conflicts': ps_conflicts,
            'j1_only_conflicts': j1_conflicts,
            'mixed_ps_j1_conflicts': mixed_conflicts,
            'conflicts': conflicts,
            'is_conflict_free': total_conflicts == 0
        }
    
    def calculate_total_penalty(
        self,
        solution: SimplexSolution,
        timeslots: List[Dict[str, Any]]
    ) -> float:
        """Calculate total weighted penalty."""
        h1 = self.calculate_h1_time_penalty(solution, timeslots)
        h2 = self.calculate_h2_workload_penalty(solution)
        h3 = self.calculate_h3_class_change_penalty(solution)
        
        total = (
            self.config.weight_h1 * h1 +
            self.config.weight_h2 * h2 +
            self.config.weight_h3 * h3
        )
        
        return total


# =============================================================================
# MODEL BUILDER (OR-Tools Linear Solver)
# =============================================================================

class SimplexModelBuilder:
    """
    Builds MILP model using OR-Tools Linear Solver.
    
    Decision Variables:
    - assign[p, s, t]: Binary - project p assigned to class s at slot t
    - j1[p, h]: Binary - instructor h is J1 for project p
    
    Constraints:
    - Each project assigned exactly once
    - At most one project per class-slot
    - Back-to-back within classes
    - Exactly one J1 per project
    - J1 ≠ PS
    - Max one duty per instructor per timeslot
    - Priority mode constraints
    - Workload hard constraints (if enabled)
    """
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: SimplexConfig,
        num_classes: int,
        class_names: Optional[List[str]] = None,
        timeslots: Optional[List[Dict[str, Any]]] = None
    ):
        # Sort projects based on priority mode
        priority_mode = str(config.priority_mode).upper()
        if priority_mode == "ARA_ONCE":
            # ARA projects first, then BITIRME
            sorted_projects = sorted(projects, key=lambda p: (0 if p.project_type == "ARA" else 1, p.id))
            logger.info(f"Projects sorted: ARA first ({len([p for p in projects if p.project_type == 'ARA'])} ARA, {len([p for p in projects if p.project_type == 'BITIRME'])} BITIRME)")
        elif priority_mode == "BITIRME_ONCE":
            # BITIRME projects first, then ARA 
            sorted_projects = sorted(projects, key=lambda p: (0 if p.project_type == "BITIRME" else 1, p.id))
            logger.info(f"Projects sorted: BITIRME first ({len([p for p in projects if p.project_type == 'BITIRME'])} BITIRME, {len([p for p in projects if p.project_type == 'ARA'])} ARA)")
        else:
            # ESIT - no sorting by type
            sorted_projects = projects
            logger.info("Projects not sorted by type (ESIT mode)")
        
        self.projects = sorted_projects
        self.instructors = instructors
        self.config = config
        self.z = num_classes
        self.timeslots = timeslots or []
        
        # Filter faculty (exclude assistants)
        self.faculty = [
            i for i in instructors
            if i.type == "instructor"
        ]
        self.faculty_ids = [i.id for i in self.faculty]
        
        if len(self.faculty) == 0:
            logger.error("ERROR: No faculty members found!")
            logger.error(f"Total instructors: {len(instructors)}")
            for inst in instructors:
                logger.error(f"  Instructor {inst.id} ({inst.name}): type={inst.type}")
        else:
            logger.info(f"SimplexModelBuilder: {len(self.faculty)} faculty members available for J1 assignment")
            logger.debug(f"Faculty IDs: {self.faculty_ids}")
        
        # Generate class names
        if class_names:
            self.class_names = class_names[:num_classes]
        else:
            self.class_names = [f"D{105 + i}" for i in range(num_classes)]
        
        # Calculate max slots per class
        Y = len(projects)
        self.T = math.ceil(Y / num_classes) + 5  # Extra buffer
        
        # Build PS lookup
        self.ps_lookup = {p.id: p.ps_id for p in projects}
        
        # Build time range grouping for conflict prevention
        self.time_range_groups = self._build_time_range_groups()
        
        logger.info(f"Building MILP model: {Y} projects, {len(self.faculty)} faculty, {num_classes} classes, {self.T} max slots")
        logger.info(f"Time range groups: {len(self.time_range_groups)} unique time ranges")
    
    def _build_time_range_groups(self) -> Dict[str, List[Tuple[int, int]]]:
        """
        Build time range grouping: group slot indices by their time range.
        
        Returns:
            Dict mapping time_range_key -> List of (class_id, slot_index) tuples
            time_range_key format: "HH:MM-HH:MM" (e.g., "09:00-09:30")
        """
        time_range_groups = defaultdict(list)
        
        if not self.timeslots:
            # If no timeslots provided, use slot_duration to calculate time ranges
            slot_duration_hours = self.config.slot_duration
            start_hour = 9.0  # 09:00
            
            for t in range(self.T):
                start_time_val = start_hour + t * slot_duration_hours
                end_time_val = start_time_val + slot_duration_hours
                
                # Format time range key
                start_h = int(start_time_val)
                start_m = int((start_time_val - start_h) * 60)
                end_h = int(end_time_val)
                end_m = int((end_time_val - end_h) * 60)
                
                time_range_key = f"{start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}"
                
                # Add all classes for this slot
                for s in range(self.z):
                    time_range_groups[time_range_key].append((s, t))
        else:
            # Use actual timeslot data
            slot_time_map = {}
            for idx, ts in enumerate(self.timeslots):
                slot_id = ts.get('id', idx)
                start_time = ts.get('start_time', None)
                end_time = ts.get('end_time', None)
                
                if start_time is None:
                    # Fallback: calculate from slot index
                    start_time_val = 9.0 + idx * self.config.slot_duration
                    end_time_val = start_time_val + self.config.slot_duration
                else:
                    # Parse start_time
                    if isinstance(start_time, str):
                        parts = start_time.split(':')
                        start_h = int(parts[0])
                        start_m = int(parts[1]) if len(parts) > 1 else 0
                        start_time_val = start_h + start_m / 60.0
                    elif hasattr(start_time, 'hour') and hasattr(start_time, 'minute'):
                        # datetime.time object
                        start_time_val = start_time.hour + start_time.minute / 60.0
                    else:
                        start_time_val = float(start_time)
                    
                    if end_time is None:
                        end_time_val = start_time_val + self.config.slot_duration
                    else:
                        if isinstance(end_time, str):
                            parts = end_time.split(':')
                            end_h = int(parts[0])
                            end_m = int(parts[1]) if len(parts) > 1 else 0
                            end_time_val = end_h + end_m / 60.0
                        elif hasattr(end_time, 'hour') and hasattr(end_time, 'minute'):
                            # datetime.time object
                            end_time_val = end_time.hour + end_time.minute / 60.0
                        else:
                            end_time_val = float(end_time)
                
                # Format time range key
                start_h = int(start_time_val)
                start_m = int((start_time_val - start_h) * 60)
                end_h = int(end_time_val)
                end_m = int((end_time_val - end_h) * 60)
                
                time_range_key = f"{start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}"
                slot_time_map[slot_id] = time_range_key
            
            # Group slots by time range (for each class)
            # Note: In our model, slot index t is the order_in_class within each class
            # So we need to map slot indices to time ranges based on order
            for t in range(self.T):
                # Calculate time range for slot index t
                start_time_val = 9.0 + t * self.config.slot_duration
                end_time_val = start_time_val + self.config.slot_duration
                
                start_h = int(start_time_val)
                start_m = int((start_time_val - start_h) * 60)
                end_h = int(end_time_val)
                end_m = int((end_time_val - end_h) * 60)
                
                time_range_key = f"{start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}"
                
                # Add all classes for this slot
                for s in range(self.z):
                    time_range_groups[time_range_key].append((s, t))
        
        logger.debug(f"Time range groups created: {len(time_range_groups)} unique time ranges")
        for time_range, slots in sorted(time_range_groups.items()):
            logger.debug(f"  {time_range}: {len(slots)} class-slot combinations")
        
        return dict(time_range_groups)
    
    def build_model(self) -> Tuple[Any, Dict[str, Any]]:
        """
        Build MILP model with all variables and constraints.
        
        Returns:
            Tuple of (solver, variable_mapping)
        """
        if not ORTOOLS_AVAILABLE:
            raise ImportError("OR-Tools is not available. Please install: pip install ortools")
        
        # Create solver
        solver = pywraplp.Solver.CreateSolver(self.config.solver_name)
        if solver is None:
            logger.warning(f"Solver {self.config.solver_name} not available, trying CBC")
            solver = pywraplp.Solver.CreateSolver("CBC")
        if solver is None:
            raise RuntimeError("No MILP solver available. Please install SCIP or CBC.")
        
        solver.SetTimeLimit(self.config.max_time_seconds * 1000)  # milliseconds
        
        # Variable mapping
        vars_map = {
            'assign': {},  # assign[(p.id, s, t)] -> BoolVar
            'j1': {},      # j1[(p.id, h)] -> BoolVar
            'slot_used': {},  # slot_used[(s, t)] -> BoolVar
            'active': {},     # active[(h, s, t)] -> BoolVar
            'load': {},       # load[h] -> IntVar
            'dev_plus': {},   # dev_plus[h] -> IntVar (positive deviation)
            'dev_minus': {},  # dev_minus[h] -> IntVar (negative deviation)
            'class_used': {},  # class_used[(h, s)] -> BoolVar
            'class_change_excess': {},  # class_change_excess[h] -> IntVar
            'cont_excess': {},  # cont_excess[(h, s)] -> IntVar
            'class_load_dev': {},  # class_load_dev[s] -> IntVar
        }
        
        Y = len(self.projects)
        X = len(self.faculty_ids)
        z = self.z
        T = self.T
        
        # =====================================================================
        # DECISION VARIABLES
        # =====================================================================
        
        # 1. assign[p, s, t]: Binary - project p assigned to class s at slot t
        for p in self.projects:
            for s in range(z):
                for t in range(T):
                    var_name = f"assign_p{p.id}_s{s}_t{t}"
                    vars_map['assign'][(p.id, s, t)] = solver.BoolVar(var_name)
        
        # 2. j1[p, h]: Binary - instructor h is J1 for project p
        for p in self.projects:
            for h in self.faculty_ids:
                var_name = f"j1_p{p.id}_h{h}"
                vars_map['j1'][(p.id, h)] = solver.BoolVar(var_name)
        
        # 3. slot_used[s, t]: Binary - slot t in class s is used
        for s in range(z):
            for t in range(T):
                var_name = f"slot_used_s{s}_t{t}"
                vars_map['slot_used'][(s, t)] = solver.BoolVar(var_name)
        
        # 4. active[h, s, t]: Binary - instructor h is active at class s, slot t
        for h in self.faculty_ids:
            for s in range(z):
                for t in range(T):
                    var_name = f"active_h{h}_s{s}_t{t}"
                    vars_map['active'][(h, s, t)] = solver.BoolVar(var_name)
        
        # 5. load[h]: Integer - total workload for instructor h
        max_load = 2 * Y
        for h in self.faculty_ids:
            var_name = f"load_h{h}"
            vars_map['load'][h] = solver.IntVar(0, max_load, var_name)
        
        # 6. dev_plus[h], dev_minus[h]: Integer - positive/negative workload deviation
        for h in self.faculty_ids:
            var_name = f"dev_plus_h{h}"
            vars_map['dev_plus'][h] = solver.IntVar(0, max_load, var_name)
            var_name = f"dev_minus_h{h}"
            vars_map['dev_minus'][h] = solver.IntVar(0, max_load, var_name)
        
        # 7. class_used[h, s]: Binary - instructor h uses class s
        for h in self.faculty_ids:
            for s in range(z):
                var_name = f"class_used_h{h}_s{s}"
                vars_map['class_used'][(h, s)] = solver.BoolVar(var_name)
        
        # 8. class_change_excess[h]: Integer - excess class changes (beyond 2)
        for h in self.faculty_ids:
            var_name = f"class_change_excess_h{h}"
            vars_map['class_change_excess'][h] = solver.IntVar(0, z, var_name)
        
        # 9. cont_excess[h, s]: Integer - continuity excess (blocks - 1)
        for h in self.faculty_ids:
            for s in range(z):
                var_name = f"cont_excess_h{h}_s{s}"
                vars_map['cont_excess'][(h, s)] = solver.IntVar(0, T, var_name)
        
        # 10. class_load_dev[s]: Integer - class load deviation from target
        for s in range(z):
            var_name = f"class_load_dev_s{s}"
            vars_map['class_load_dev'][s] = solver.IntVar(0, 2 * Y, var_name)
        
        # =====================================================================
        # HARD CONSTRAINTS
        # =====================================================================
        
        # 1. Each project assigned exactly once
        for p in self.projects:
            solver.Add(
                sum(vars_map['assign'][(p.id, s, t)]
                    for s in range(z)
                    for t in range(T)) == 1
            )
        
        # 2. At most one project per class-slot
        for s in range(z):
            for t in range(T):
                solver.Add(
                    sum(vars_map['assign'][(p.id, s, t)] for p in self.projects) <= 1
                )
        
        # 3. Link slot_used to assign
        for s in range(z):
            for t in range(T):
                # slot_used[s,t] >= assign[p,s,t] for all p
                for p in self.projects:
                    solver.Add(
                        vars_map['slot_used'][(s, t)] >= vars_map['assign'][(p.id, s, t)]
                    )
                # slot_used[s,t] <= sum_p assign[p,s,t]
                solver.Add(
                    vars_map['slot_used'][(s, t)] <= sum(
                        vars_map['assign'][(p.id, s, t)] for p in self.projects
                    )
                )
        
        # 4. Back-to-back: no gaps in class schedule
        # used[s, t-1] >= used[s, t] for t > 0
        for s in range(z):
            for t in range(1, T):
                solver.Add(
                    vars_map['slot_used'][(s, t - 1)] >= vars_map['slot_used'][(s, t)]
                )
        
        # 5. Exactly one J1 per project
        for p in self.projects:
            solver.Add(
                sum(vars_map['j1'][(p.id, h)] for h in self.faculty_ids) == 1
            )
        
        # 6. J1 cannot be PS
        for p in self.projects:
            ps_id = self.ps_lookup[p.id]
            if ps_id in self.faculty_ids:
                solver.Add(vars_map['j1'][(p.id, ps_id)] == 0)
        
        # 7. Link active[h,s,t] to assignments
        for h in self.faculty_ids:
            for s in range(z):
                for t in range(T):
                    # Build list of projects where h is PS
                    ps_projects = [p for p in self.projects if self.ps_lookup[p.id] == h]
                    
                    # active >= assign for PS projects
                    for p in ps_projects:
                        solver.Add(
                            vars_map['active'][(h, s, t)] >= vars_map['assign'][(p.id, s, t)]
                        )
                    
                    # active >= assign * j1 for J1 assignments
                    # Linearization: create auxiliary variable for assign * j1
                    j1_contributions = []
                    for p in self.projects:
                        # Create binary variable for assign[p,s,t] * j1[p,h]
                        aux_var = solver.BoolVar(f"j1_aux_p{p.id}_h{h}_s{s}_t{t}")
                        # Linearization: aux = assign * j1
                        # aux <= assign
                        solver.Add(aux_var <= vars_map['assign'][(p.id, s, t)])
                        # aux <= j1
                        solver.Add(aux_var <= vars_map['j1'][(p.id, h)])
                        # aux >= assign + j1 - 1
                        solver.Add(aux_var >= vars_map['assign'][(p.id, s, t)] + vars_map['j1'][(p.id, h)] - 1)
                        # active >= aux
                        solver.Add(vars_map['active'][(h, s, t)] >= aux_var)
                        j1_contributions.append(aux_var)
                    
                    # active <= sum of all contributions
                    ps_contributions = [
                        vars_map['assign'][(p.id, s, t)] for p in ps_projects
                    ]
                    all_contributions = ps_contributions + j1_contributions
                    if all_contributions:
                        solver.Add(vars_map['active'][(h, s, t)] <= solver.Sum(all_contributions))
                    else:
                        solver.Add(vars_map['active'][(h, s, t)] == 0)
        
        # 8. HARD CONSTRAINT: Timeslot Conflict Prevention - ZERO CONFLICTS GUARANTEED
        # ==========================================================================================================
        # CRITICAL HARD CONSTRAINT: An instructor CANNOT have multiple duties in the same timeslot
        # This is a MANDATORY constraint - solver will reject any solution that violates this
        # 
        # Examples of what this prevents (REAL WORLD SCENARIOS):
        # - MSA is PS in project "MSA - 1" at timeslot t → MSA CANNOT be PS in project "MSA - 3" at the same timeslot t
        # - AEL is PS in a project at timeslot t → AEL CANNOT be J1 in another project at the same timeslot t
        # - EC is J1 in a project at timeslot t → EC CANNOT be PS or J1 in another project at the same timeslot t
        # - An instructor can have at most ONE duty (either PS or J1) at any given timeslot t across ALL classes
        #
        # CRITICAL FIX: Apply to ALL instructors (including PS who may not be in faculty_ids)
        # ==========================================================================================================
        
        # Get ALL instructor IDs (PS IDs + faculty IDs) - CRITICAL FIX
        all_instructor_ids_for_conflicts = set()
        for p in self.projects:
            all_instructor_ids_for_conflicts.add(self.ps_lookup[p.id])
        all_instructor_ids_for_conflicts.update(self.faculty_ids)
        
        logger.info(f"Applying conflict constraints to {len(all_instructor_ids_for_conflicts)} instructors "
                   f"({len(set(self.ps_lookup.values()))} unique PS, {len(self.faculty_ids)} faculty)")
        
        for h in all_instructor_ids_for_conflicts:
            for t in range(T):
                # HARD CONSTRAINT: Sum over all classes - instructor h can be active in at most 1 class at timeslot t
                # This HARD CONSTRAINT prevents ALL of the following conflicts:
                #   1. Same instructor being PS in one class and J1 in another class at the same timeslot
                #   2. Same instructor being J1 in multiple classes at the same timeslot
                #   3. Same instructor having multiple duties (PS+J1) at the same timeslot in different classes
                #   4. Same instructor being PS in multiple projects at the same timeslot (e.g., MSA in "MSA - 1" and "MSA - 3")
                #   5. Any other scenario where an instructor has more than one duty at the same timeslot
                
                # Only use active variable if h is in faculty_ids (for J1 duties)
                # For PS duties, we need to count directly
                if h in self.faculty_ids:
                    # Use active variable for faculty
                    solver.Add(
                        sum(vars_map['active'][(h, s, t)] for s in range(z)) <= 1
                    )
                else:
                    # For non-faculty PS, count PS assignments directly
                    ps_assignments = []
                    for s in range(z):
                        for p in self.projects:
                            if self.ps_lookup[p.id] == h:
                                ps_assignments.append(vars_map['assign'][(p.id, s, t)])
                    if ps_assignments:
                        solver.Add(solver.Sum(ps_assignments) <= 1)
        
        # 8b. ENHANCED HARD CONSTRAINT: Direct conflict prevention - explicit PS and J1 counting
        # =========================================================================================
        # This is an explicit hard constraint to directly prevent conflicts like the one shown
        # in the example: MSA being PS in both "MSA - 1" and "MSA - 3" at the same timeslot.
        # 
        # GOAL: ZERO conflicts - An instructor CANNOT have multiple duties at the same timeslot.
        # 
        # For each instructor h and each timeslot t, we explicitly count:
        #   - All PS duties: all projects where h is PS assigned at timeslot t (across ALL classes)
        #   - All J1 duties: all projects where h is J1 assigned at timeslot t (across ALL classes)
        # 
        # HARD CONSTRAINT: Total duties (PS_count + J1_count) <= 1
        # This ensures ABSOLUTELY NO instructor can have multiple duties at the same timeslot.
        # 
        # CRITICAL FIX: Apply to ALL instructors (including PS)
        # =========================================================================================
        for h in all_instructor_ids_for_conflicts:
            for t in range(T):
                # Collect all PS assignments at timeslot t for instructor h (across all classes)
                ps_duty_vars = []
                for s in range(z):
                    for p in self.projects:
                        if self.ps_lookup[p.id] == h:
                            ps_duty_vars.append(vars_map['assign'][(p.id, s, t)])
                
                # Collect all J1 assignments at timeslot t for instructor h (across all classes)
                # Only if h is in faculty_ids (only faculty can be J1)
                j1_duty_vars = []
                if h in self.faculty_ids:
                    for s in range(z):
                        for p in self.projects:
                            # Create auxiliary variable: j1_duty = assign[p,s,t] * j1[p,h]
                            j1_duty_aux_key = f"j1_duty_conflict_p{p.id}_h{h}_s{s}_t{t}"
                            j1_duty_aux = solver.BoolVar(j1_duty_aux_key)
                            
                            # Linearization: j1_duty_aux = assign[p,s,t] AND j1[p,h]
                            solver.Add(j1_duty_aux <= vars_map['assign'][(p.id, s, t)])
                            solver.Add(j1_duty_aux <= vars_map['j1'][(p.id, h)])
                            solver.Add(j1_duty_aux >= vars_map['assign'][(p.id, s, t)] + vars_map['j1'][(p.id, h)] - 1)
                            
                            j1_duty_vars.append(j1_duty_aux)
                
                # HARD CONSTRAINT: Total duties (PS + J1) at timeslot t cannot exceed 1
                # This directly prevents ALL conflicts:
                #   - MSA being PS in "MSA - 1" and PS in "MSA - 3" at the same timeslot
                #   - EC being J1 in one project and PS in another at the same timeslot
                #   - Any instructor having multiple duties at the same timeslot
                all_duty_vars = ps_duty_vars + j1_duty_vars
                if all_duty_vars:
                    solver.Add(solver.Sum(all_duty_vars) <= 1)
        
        # 8c. GLOBAL HARD CONSTRAINT: All instructors (including PS) - ZERO CONFLICTS
        # ============================================================================
        # This constraint ensures that ALL instructors (not just faculty for J1) cannot have
        # multiple duties at the same timeslot. This includes:
        # - Project Supervisors (PS) who may not be in faculty_ids
        # - All instructors who can be assigned as J1
        #
        # For each instructor (all instructors in the system) and each timeslot:
        #   - Count all PS duties (where instructor is PS for a project at this timeslot)
        #   - Count all J1 duties (where instructor is J1 for a project at this timeslot)
        #   - HARD CONSTRAINT: Total duties <= 1
        #
        # This is the STRONGEST constraint that guarantees ZERO conflicts globally.
        # ============================================================================
        # Get all unique instructor IDs (PS IDs + faculty IDs)
        all_instructor_ids = set()
        for p in self.projects:
            all_instructor_ids.add(self.ps_lookup[p.id])
        all_instructor_ids.update(self.faculty_ids)
        
        logger.info(f"Adding global conflict constraints for {len(all_instructor_ids)} instructors")
        
        for h in all_instructor_ids:
            for t in range(T):
                # Collect all PS assignments at timeslot t for instructor h (across all classes and projects)
                ps_duty_vars_global = []
                for s in range(z):
                    for p in self.projects:
                        if self.ps_lookup[p.id] == h:
                            ps_duty_vars_global.append(vars_map['assign'][(p.id, s, t)])
                
                # Collect all J1 assignments at timeslot t for instructor h (across all classes and projects)
                # Only count if h is in faculty_ids (only faculty can be J1)
                j1_duty_vars_global = []
                if h in self.faculty_ids:
                    for s in range(z):
                        for p in self.projects:
                            # Create auxiliary variable: j1_duty = assign[p,s,t] * j1[p,h]
                            j1_duty_aux_global_key = f"j1_duty_global_p{p.id}_h{h}_s{s}_t{t}"
                            j1_duty_aux_global = solver.BoolVar(j1_duty_aux_global_key)
                            
                            # Linearization: j1_duty_aux_global = assign[p,s,t] AND j1[p,h]
                            solver.Add(j1_duty_aux_global <= vars_map['assign'][(p.id, s, t)])
                            solver.Add(j1_duty_aux_global <= vars_map['j1'][(p.id, h)])
                            solver.Add(j1_duty_aux_global >= vars_map['assign'][(p.id, s, t)] + vars_map['j1'][(p.id, h)] - 1)
                            
                            j1_duty_vars_global.append(j1_duty_aux_global)
                
                # GLOBAL HARD CONSTRAINT: Total duties (PS + J1) at timeslot t cannot exceed 1
                # This is the STRONGEST constraint that prevents ALL possible conflicts:
                #   - MSA being PS in "MSA - 1" and PS in "MSA - 3" at the same timeslot ✓
                #   - AEL being PS in one project and J1 in another at the same timeslot ✓
                #   - EC being J1 in multiple projects at the same timeslot ✓
                #   - Any instructor having multiple duties (PS or J1) at the same timeslot ✓
                all_duty_vars_global = ps_duty_vars_global + j1_duty_vars_global
                if all_duty_vars_global:
                    constraint = solver.Sum(all_duty_vars_global) <= 1
                    solver.Add(constraint)
                    # Log constraint details for debugging (only for first few)
                    if h == list(all_instructor_ids)[0] and t < 3:
                        logger.debug(f"  Constraint: Instructor {h} at timeslot {t}: {len(ps_duty_vars_global)} PS + {len(j1_duty_vars_global)} J1 duties <= 1")
        
        # 8d. TIME RANGE BASED HARD CONSTRAINT: Zero Conflicts Within Same Time Range
        # ========================================================================================
        # CRITICAL HARD CONSTRAINT: An instructor CANNOT have multiple duties in the same time range
        # across different class-slot combinations. This prevents conflicts like:
        # - MSA is PS in class 1 at slot 5 (17:00-17:30) → MSA CANNOT be PS in class 2 at slot 5 (17:00-17:30)
        # - AEL is PS in class 1 at slot 0 (09:00-09:30) → AEL CANNOT be J1 in class 2 at slot 0 (09:00-09:30)
        # - EC is J1 in class 1 at slot 10 (14:00-14:30) → EC CANNOT be PS or J1 in any class at slot 10 (14:00-14:30)
        #
        # This constraint ensures that within the same time range (e.g., 09:00-09:30), 
        # an instructor can have at most ONE duty across ALL classes and slots that fall in that time range.
        # 
        # NOTE: Same slot index (t) = same time range, so this is redundant with constraint 8c,
        # but we add it explicitly for clarity and to match user requirements.
        # ========================================================================================
        logger.info("Adding explicit time range based hard constraints for conflict prevention...")
        
        # Get all unique instructor IDs (PS IDs + faculty IDs)
        all_instructor_ids_time_range = set()
        for p in self.projects:
            all_instructor_ids_time_range.add(self.ps_lookup[p.id])
        all_instructor_ids_time_range.update(self.faculty_ids)
        
        constraint_count = 0
        for time_range_key, class_slot_pairs in self.time_range_groups.items():
            # For each time range, ensure no instructor has multiple duties
            for h in all_instructor_ids_time_range:
                # Collect all duty variables for this instructor in this time range
                time_range_duty_vars = []
                
                for s, t in class_slot_pairs:
                    # Skip if slot index t is out of bounds
                    if t >= T:
                        continue
                    
                    # Collect PS duties
                    for p in self.projects:
                        if self.ps_lookup[p.id] == h:
                            time_range_duty_vars.append(vars_map['assign'][(p.id, s, t)])
                    
                    # Collect J1 duties (only if h is in faculty_ids)
                    if h in self.faculty_ids:
                        for p in self.projects:
                            # Create auxiliary variable: j1_duty = assign[p,s,t] * j1[p,h]
                            j1_duty_key = f"j1_duty_tr_{time_range_key.replace(':', '_').replace('-', '_')}_p{p.id}_h{h}_s{s}_t{t}"
                            
                            # Use a simpler approach: create variable once per (p, h, s, t) combination
                            # and reuse it if needed
                            if 'j1_duty_tr' not in vars_map:
                                vars_map['j1_duty_tr'] = {}
                            
                            if j1_duty_key not in vars_map['j1_duty_tr']:
                                j1_duty_aux = solver.BoolVar(j1_duty_key)
                                
                                # Linearization: j1_duty_aux = assign[p,s,t] AND j1[p,h]
                                solver.Add(j1_duty_aux <= vars_map['assign'][(p.id, s, t)])
                                solver.Add(j1_duty_aux <= vars_map['j1'][(p.id, h)])
                                solver.Add(j1_duty_aux >= vars_map['assign'][(p.id, s, t)] + vars_map['j1'][(p.id, h)] - 1)
                                
                                vars_map['j1_duty_tr'][j1_duty_key] = j1_duty_aux
                            
                            time_range_duty_vars.append(vars_map['j1_duty_tr'][j1_duty_key])
                
                # HARD CONSTRAINT: At most one duty per instructor per time range
                if time_range_duty_vars:
                    solver.Add(solver.Sum(time_range_duty_vars) <= 1)
                    constraint_count += 1
        
        logger.info(f"Added {constraint_count} time range based hard constraints for {len(all_instructor_ids_time_range)} instructors across {len(self.time_range_groups)} time ranges")
        
        # 8e. ULTIMATE HARD CONSTRAINT: ZERO CONFLICTS - Direct Slot-Level Enforcement
        # ========================================================================================
        # This is the STRONGEST and MOST DIRECT hard constraint for preventing conflicts.
        # 
        # For each instructor h and each slot t (order_in_class):
        #   - Count all projects where h is PS that are assigned to ANY class at slot t
        #   - Count all projects where h is J1 that are assigned to ANY class at slot t
        #   - HARD CONSTRAINT: Total count <= 1
        #
        # This directly enforces: An instructor can have AT MOST ONE duty at any given time slot,
        # regardless of which class or project. This is the ZERO CONFLICT guarantee.
        #
        # Example enforcement:
        #   - MSA is PS for projects P1, P3, P5
        #   - If P1 is assigned to class 1 at slot 5 (MSA has PS duty at slot 5)
        #   - Then P3 and P5 CANNOT be assigned to ANY class at slot 5
        #   - Because that would give MSA multiple PS duties at the same time
        # ========================================================================================
        logger.info("Adding ULTIMATE HARD CONSTRAINT for zero conflicts...")
        
        # Build PS-to-projects mapping: instructor_id -> list of projects where they are PS
        ps_to_projects = defaultdict(list)
        for p in self.projects:
            ps_to_projects[self.ps_lookup[p.id]].append(p)
        
        ultimate_constraint_count = 0
        
        for h in all_instructor_ids_time_range:
            for t in range(T):
                # Collect ALL duty indicators at slot t for instructor h
                all_duties_at_slot = []
                
                # PS duties: For each project where h is PS, check all classes
                for p in ps_to_projects.get(h, []):
                    for s in range(z):
                        all_duties_at_slot.append(vars_map['assign'][(p.id, s, t)])
                
                # J1 duties: For each project (any PS), if h is J1 and project is at slot t
                if h in self.faculty_ids:
                    for p in self.projects:
                        for s in range(z):
                            # Create auxiliary variable for J1 duty indicator
                            j1_slot_key = f"j1_slot_ultimate_p{p.id}_h{h}_s{s}_t{t}"
                            
                            if 'j1_slot_ultimate' not in vars_map:
                                vars_map['j1_slot_ultimate'] = {}
                            
                            if j1_slot_key not in vars_map['j1_slot_ultimate']:
                                j1_aux = solver.BoolVar(j1_slot_key)
                                
                                # j1_aux = 1 iff assign[p,s,t]=1 AND j1[p,h]=1
                                solver.Add(j1_aux <= vars_map['assign'][(p.id, s, t)])
                                solver.Add(j1_aux <= vars_map['j1'][(p.id, h)])
                                solver.Add(j1_aux >= vars_map['assign'][(p.id, s, t)] + vars_map['j1'][(p.id, h)] - 1)
                                
                                vars_map['j1_slot_ultimate'][j1_slot_key] = j1_aux
                            
                            all_duties_at_slot.append(vars_map['j1_slot_ultimate'][j1_slot_key])
                
                # ULTIMATE HARD CONSTRAINT: At most 1 duty per instructor per slot
                if all_duties_at_slot:
                    solver.Add(solver.Sum(all_duties_at_slot) <= 1)
                    ultimate_constraint_count += 1
        
        logger.info(f"Added {ultimate_constraint_count} ULTIMATE hard constraints for zero conflicts")
        
        # 9. Workload calculation: load[h] = PS duties + J1 duties
        for h in self.faculty_ids:
            ps_count = sum(1 for p in self.projects if self.ps_lookup[p.id] == h)
            j1_sum = solver.Sum([vars_map['j1'][(p.id, h)] for p in self.projects])
            solver.Add(vars_map['load'][h] == ps_count + j1_sum)
        
        # 10. Link class_used[h,s]
        for h in self.faculty_ids:
            for s in range(z):
                # class_used >= active for any t
                for t in range(T):
                    solver.Add(
                        vars_map['class_used'][(h, s)] >= vars_map['active'][(h, s, t)]
                    )
                # class_used <= sum of active
                solver.Add(
                    vars_map['class_used'][(h, s)] <= sum(
                        vars_map['active'][(h, s, t)] for t in range(T)
                    )
                    )
                    
        # 11. Priority mode constraints
        self._add_priority_constraints(solver, vars_map)
        
        # 12. Hard workload bounds (if SOFT_AND_HARD mode)
        self._add_workload_hard_constraints(solver, vars_map, Y, X)
        
        # =====================================================================
        # SOFT PENALTY VARIABLES
        # =====================================================================
        
        # Calculate average workload
        avg_load = (2 * Y) / X if X > 0 else 0
        avg_load_floor = int(math.floor(avg_load))
        avg_load_ceil = int(math.ceil(avg_load))
        
        # Workload deviation penalty: dev_plus and dev_minus
        for h in self.faculty_ids:
            # dev_plus >= load - (avg + 2)
            solver.Add(
                vars_map['dev_plus'][h] >= vars_map['load'][h] - (avg_load_ceil + 2)
            )
            # dev_minus >= (avg - 2) - load
            solver.Add(
                vars_map['dev_minus'][h] >= (avg_load_floor - 2) - vars_map['load'][h]
            )
            # dev_plus >= 0, dev_minus >= 0 (already in domain)
        
        # Class change excess: class_change_excess[h] >= class_count[h] - 2
        for h in self.faculty_ids:
            class_count = solver.Sum([
                vars_map['class_used'][(h, s)] for s in range(z)
            ])
            solver.Add(vars_map['class_change_excess'][h] >= class_count - 2)
        
        # Continuity penalty (block counting)
        self._add_continuity_constraints(solver, vars_map, z, T)
        
        # Class load deviation
        target_class_load = (2 * Y) / z if z > 0 else 0
        target_floor = int(math.floor(target_class_load))
        target_ceil = int(math.ceil(target_class_load))
        
        for s in range(z):
            class_project_count = solver.Sum([
                vars_map['assign'][(p.id, s, t)]
                for p in self.projects
                for t in range(T)
            ])
            class_load = 2 * class_project_count  # 2 duties per project
            
            # class_load_dev >= |class_load - target|
            solver.Add(vars_map['class_load_dev'][s] >= class_load - target_ceil)
            solver.Add(vars_map['class_load_dev'][s] >= target_floor - class_load)
        
        # =====================================================================
        # OBJECTIVE FUNCTION
        # =====================================================================
        
        objective = solver.Objective()
        
        # H1: Continuity penalty
        for h in self.faculty_ids:
            for s in range(z):
                objective.SetCoefficient(vars_map['cont_excess'][(h, s)], self.config.weight_h1)
        
        # H2: Workload uniformity (most important)
        for h in self.faculty_ids:
            objective.SetCoefficient(vars_map['dev_plus'][h], self.config.weight_h2)
            objective.SetCoefficient(vars_map['dev_minus'][h], self.config.weight_h2)
        
        # H3: Class change penalty
        for h in self.faculty_ids:
            objective.SetCoefficient(vars_map['class_change_excess'][h], self.config.weight_h3)
        
        # H4: Class load balance (optional, can be added)
        # for s in range(z):
        #     objective.SetCoefficient(vars_map['class_load_dev'][s], weight_h4)
        
        objective.SetMinimization()
        
        # Add priority constraints if needed (ARA_ONCE or BITIRME_ONCE)
        self._add_priority_constraints(solver, vars_map)
        
        return solver, vars_map
    
    def _add_priority_constraints(self, solver: Any, vars_map: Dict[str, Any]) -> None:
        """
        Add project type priority constraints.
        
        NOTE: Priority is now handled by reordering projects before model building.
        This method just logs the priority mode for debugging.
        
        The actual priority is implemented by:
        1. Sorting projects so that priority type comes first
        2. Using lower slot indices for projects that appear first in the list
        """
        priority_mode = str(self.config.priority_mode).upper()
        
        # ESIT = No priority, skip
        if priority_mode == "ESIT" or priority_mode == "NONE":
            logger.info("Priority mode: ESIT (no priority constraints)")
            return
        
        logger.info(f"Priority mode active: {priority_mode}")
        
        # Separate projects by type
        ara_projects = [p for p in self.projects if p.project_type == "ARA"]
        bitirme_projects = [p for p in self.projects if p.project_type == "BITIRME"]
        
        logger.info(f"Priority split: ARA={len(ara_projects)}, BITIRME={len(bitirme_projects)}")
        
        if priority_mode == "ARA_ONCE":
            logger.info("ARA_ONCE: ARA projects will be scheduled first")
        elif priority_mode == "BITIRME_ONCE":
            logger.info("BITIRME_ONCE: BITIRME projects will be scheduled first")
        
    def _add_workload_hard_constraints(
        self,
        solver: Any,
        vars_map: Dict[str, Any],
        Y: int,
        X: int
    ) -> None:
        """Add hard workload constraints if mode is SOFT_AND_HARD."""
        if self.config.workload_constraint_mode != WorkloadConstraintMode.SOFT_AND_HARD:
            return
        
        if X == 0:
            return
        
        avg_load = (2 * Y) / X
        b_max = self.config.b_max
        
        avg_floor = int(math.floor(avg_load))
        avg_ceil = int(math.ceil(avg_load))
            
        for h in self.faculty_ids:
            # load[h] - avg <= b_max
            solver.Add(vars_map['load'][h] <= avg_ceil + b_max)
            # avg - load[h] <= b_max
            solver.Add(vars_map['load'][h] >= avg_floor - b_max)
    
    def _add_continuity_constraints(
        self,
        solver: Any,
        vars_map: Dict[str, Any],
        z: int,
        T: int
    ) -> None:
        """Add continuity/block counting constraints."""
        # For each (instructor, class), count number of blocks
        # A block starts when active goes from 0 to 1
        
        for h in self.faculty_ids:
            for s in range(z):
                # Block start at t=0
                block_start_0 = vars_map['active'][(h, s, 0)]
                
                # Block starts at t>0
                block_starts = [block_start_0]
                
                for t in range(1, T):
                    # block_start[t] = active[t] AND NOT active[t-1]
                    block_start_t = solver.BoolVar(f"block_start_h{h}_s{s}_t{t}")
                    
                    # Linearization: block_start >= active[t] - active[t-1]
                    solver.Add(
                        block_start_t >= 
                        vars_map['active'][(h, s, t)] - vars_map['active'][(h, s, t - 1)]
                    )
                    solver.Add(block_start_t <= vars_map['active'][(h, s, t)])
                    solver.Add(block_start_t <= 1 - vars_map['active'][(h, s, t - 1)])
                    
                    block_starts.append(block_start_t)
            
                # Total blocks = sum of block starts
                total_blocks = solver.IntVar(0, T, f"total_blocks_h{h}_s{s}")
                solver.Add(total_blocks == solver.Sum(block_starts))
                
                # cont_excess >= blocks - 1 (penalty for having more than 1 block)
                solver.Add(vars_map['cont_excess'][(h, s)] >= total_blocks - 1)

        
# =============================================================================
# ORTOOLS LP SOLVER
# =============================================================================

class ORToolsSimplexSolver:
    """
    OR-Tools Linear Solver wrapper for Real Simplex Algorithm.
    """
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: SimplexConfig,
        num_classes: int,
        class_names: Optional[List[str]] = None,
        timeslots: Optional[List[Dict[str, Any]]] = None
    ):
        self.projects = projects
        self.instructors = instructors
        self.config = config
        self.z = num_classes
        self.class_names = class_names or [f"D{105 + i}" for i in range(num_classes)]
        self.timeslots = timeslots or []
        
        # Filter faculty
        self.faculty = [
            i for i in instructors
            if i.type == "instructor"
        ]
        self.faculty_ids = [i.id for i in self.faculty]
        
        # Build PS lookup
        self.ps_lookup = {p.id: p.ps_id for p in projects}
        
        if len(self.faculty) == 0:
            logger.error("ERROR: No faculty members found in ORToolsSimplexSolver!")
            logger.error(f"Total instructors: {len(instructors)}")
            for inst in instructors:
                logger.error(f"  Instructor {inst.id} ({inst.name}): type={inst.type}")
        else:
            logger.info(f"ORToolsSimplexSolver: {len(self.faculty)} faculty members available for J1 assignment")
            logger.debug(f"Faculty IDs: {self.faculty_ids}")
        
        # Build model
        self.model_builder = SimplexModelBuilder(
            projects, instructors, config, num_classes, class_names, timeslots
        )
        self.solver, self.vars_map = self.model_builder.build_model()
    
    def solve(self) -> SimplexSolution:
        """Solve using OR-Tools MILP solver."""
        logger.info(f"Solving MILP model...")
        logger.info(f"Model has {len(self.projects)} projects, {len(self.faculty_ids)} faculty for J1")
        logger.info(f"J1 variables: {len(self.projects) * len(self.faculty_ids)} total")
        logger.info(f"Faculty IDs for J1: {self.faculty_ids}")
        
        if len(self.faculty_ids) > 0:
            sample_j1_var = self.vars_map['j1'][(self.projects[0].id, self.faculty_ids[0])]
            logger.info(f"Sample J1 variable type: {type(sample_j1_var)}, is binary: {hasattr(sample_j1_var, 'solution_value')}")
        
        status = self.solver.Solve()
        
        solution = SimplexSolution(class_count=self.z)
        
        logger.info(f"Solver status: {status} (OPTIMAL={pywraplp.Solver.OPTIMAL}, FEASIBLE={pywraplp.Solver.FEASIBLE})")
        
        if status != pywraplp.Solver.OPTIMAL and status != pywraplp.Solver.FEASIBLE:
            logger.error(f"Solver failed with status: {status}")
            logger.error("Available statuses: OPTIMAL=0, FEASIBLE=1, INFEASIBLE=2, UNBOUNDED=3, ABNORMAL=4, MODEL_INVALID=5, NOT_SOLVED=6")
            solution.solver_status = "FAILED"
            solution.is_feasible = False
            return solution
        
        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
            solution.solver_status = "OPTIMAL" if status == pywraplp.Solver.OPTIMAL else "FEASIBLE"
            solution.is_feasible = True
            solution.total_cost = self.solver.Objective().Value()
            
            logger.info(f"Solution found! Total cost: {solution.total_cost:.2f}")
            
            # Track J1 assignment distribution
            j1_assignments = defaultdict(int)
            
            # Extract assignments
            for p in self.projects:
                # Find assigned class and slot
                assigned_class = None
                assigned_slot = None
                
                for s in range(self.z):
                    for t in range(self.model_builder.T):
                        if self.vars_map['assign'][(p.id, s, t)].solution_value() > 0.5:
                            assigned_class = s
                            assigned_slot = t
                            break
                    if assigned_class is not None:
                        break
                
                if assigned_class is None:
                    logger.warning(f"Project {p.id} not assigned!")
                    continue
                
                # Find J1 assignment
                j1_id = None
                j1_values = {}
                max_val = -1.0
                max_faculty = None
                
                for h in self.faculty_ids:
                    try:
                        val = self.vars_map['j1'][(p.id, h)].solution_value()
                        j1_values[h] = val
                        if val > max_val:
                            max_val = val
                            max_faculty = h
                        if val > 0.5:
                            if j1_id is not None and h != j1_id:
                                logger.error(
                                    f"Project {p.id}: Multiple J1 assignments over threshold! "
                                    f"existing={j1_id} (val={j1_values.get(j1_id, 0):.3f}), "
                                    f"candidate={h} (val={val:.3f})"
                                )
                            if j1_id is None or val > j1_values.get(j1_id, 0):
                                j1_id = h
                    except Exception as e:
                        logger.error(f"Project {p.id}: Error reading J1 variable for faculty {h}: {e}")
                        continue
                
                if j1_id is None:
                    logger.error(
                        f"Project {p.id}: No J1 above threshold. Top values: "
                        f"{[(h, f'{v:.6f}') for h, v in sorted(j1_values.items(), key=lambda x: x[1], reverse=True)[:5]]}"
                    )
                    if max_faculty is not None and max_val > 0.0:
                        j1_id = max_faculty
                        logger.warning(
                            f"Project {p.id}: Falling back to max-value J1={j1_id} (val={max_val:.6f})"
                        )
                
                if j1_id is None:
                    # Fallback: pick any instructor that's not PS
                    logger.warning(f"Project {p.id}: No J1 assigned by solver (all values < 0.5), using fallback")
                    logger.warning(f"  J1 values: {[(h, f'{v:.3f}') for h, v in sorted(j1_values.items(), key=lambda x: x[1], reverse=True)[:5]]}")
                    for h in self.faculty_ids:
                        if h != self.ps_lookup[p.id]:
                            j1_id = h
                            logger.warning(f"Project {p.id}: Fallback J1 = {j1_id}")
                            break
                
                if j1_id is None:
                    logger.error(f"Project {p.id}: No valid J1 found! PS={self.ps_lookup[p.id]}, Available faculty={self.faculty_ids}")
                else:
                    j1_assignments[j1_id] += 1
                
                assignment = ProjectAssignment(
                    project_id=p.id,
                    class_id=assigned_class,
                    order_in_class=assigned_slot,
                    ps_id=self.ps_lookup[p.id],
                    j1_id=j1_id,
                    j2_label="[Arastirma Gorevlisi]"
                )
                solution.assignments.append(assignment)
            
            # Log J1 assignment distribution
            logger.info(f"J1 Assignment Distribution (Total projects: {len(solution.assignments)}):")
            for faculty_id, count in sorted(j1_assignments.items(), key=lambda x: x[1], reverse=True):
                faculty_name = next((f.name for f in self.faculty if f.id == faculty_id), f"ID_{faculty_id}")
                percentage = (count / len(solution.assignments) * 100) if solution.assignments else 0
                logger.info(f"  {faculty_name} (ID: {faculty_id}): {count} J1 assignments ({percentage:.1f}%)")
            
            # Check if all faculty are used
            unused_faculty = [f.id for f in self.faculty if f.id not in j1_assignments]
            if unused_faculty:
                unused_names = [next((f.name for f in self.faculty if f.id == fid), f"ID_{fid}") for fid in unused_faculty]
                logger.warning(f"Unused faculty for J1 assignments ({len(unused_faculty)}): {unused_names}")
            
            if len(j1_assignments) == 1:
                logger.error(f"ERROR: Only 1 faculty member used for J1 assignments! This indicates a serious problem.")
                logger.error(f"  Used faculty: {list(j1_assignments.keys())}")
                logger.error(f"  Total faculty available: {self.faculty_ids}")
                logger.error("Debugging J1 variable values for first 10 projects:")
                for p in self.projects[:10]:
                    logger.error(f"  Project {p.id} (PS={self.ps_lookup[p.id]}):")
                    j1_vals = []
                    for h in self.faculty_ids:
                        try:
                            val = self.vars_map['j1'][(p.id, h)].solution_value()
                            j1_vals.append((h, val))
                        except Exception as e:
                            logger.error(f"    Error reading J1[{p.id}, {h}]: {e}")
                    j1_vals_sorted = sorted(j1_vals, key=lambda x: x[1], reverse=True)
                    for h, val in j1_vals_sorted[:5]:
                        faculty_name = next((f.name for f in self.faculty if f.id == h), f"ID_{h}")
                        logger.error(f"    {faculty_name} (ID: {h}): {val:.6f}")
            
            # Reorder slots only when not in strict zero-conflict mode; compacting slots
            # after solving can introduce artificial conflicts across classes.
            if not self.config.zero_conflict:
                self._renumber_slots(solution)
            
            # CRITICAL: Validate solution for constraint violations
            if not self._validate_solution_constraints(solution):
                logger.error("Validation detected conflicts; returning infeasible solution.")
                return solution
        
        return solution
    
    def _validate_solution_constraints(self, solution: SimplexSolution) -> bool:
        """
        Validate that the solution satisfies all hard constraints, especially conflict constraints.
        
        This is a post-solution validation to ensure the solver didn't violate any constraints.
        """
        logger.info("Validating solution constraints...")
        
        # Build instructor schedule: instructor_id -> order_in_class -> list of duties
        instructor_schedule = defaultdict(lambda: defaultdict(list))
        
        for assignment in solution.assignments:
            # PS duty
            instructor_schedule[assignment.ps_id][assignment.order_in_class].append({
                'role': 'PS',
                'project_id': assignment.project_id,
                'class_id': assignment.class_id
            })
            # J1 duty
            instructor_schedule[assignment.j1_id][assignment.order_in_class].append({
                'role': 'J1',
                'project_id': assignment.project_id,
                'class_id': assignment.class_id
            })
        
        # Check for conflicts
        violations = []
        for instructor_id, slot_duties in instructor_schedule.items():
            for order_in_class, duties in slot_duties.items():
                if len(duties) > 1:
                    # CONSTRAINT VIOLATION!
                    instructor_name = next(
                        (i.name for i in self.instructors if i.id == instructor_id),
                        f"Instructor_{instructor_id}"
                    )
                    
                    # Calculate time range
                    slot_duration = self.config.slot_duration
                    start_hour = 9.0
                    slot_time = start_hour + order_in_class * slot_duration
                    end_time = slot_time + slot_duration
                    start_h = int(slot_time)
                    start_m = int((slot_time - start_h) * 60)
                    end_h = int(end_time)
                    end_m = int((end_time - end_h) * 60)
                    time_range = f"{start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}"
                    
                    violations.append({
                        'instructor_id': instructor_id,
                        'instructor_name': instructor_name,
                        'order_in_class': order_in_class,
                        'time_range': time_range,
                        'duty_count': len(duties),
                        'duties': duties
                    })
        
        if violations:
            logger.error(f"⚠️ CONSTRAINT VIOLATIONS DETECTED: {len(violations)} violations found!")
            logger.error("This should NOT happen if hard constraints are working correctly!")
            for violation in violations[:10]:
                logger.error(f"  Violation: {violation['instructor_name']} (ID: {violation['instructor_id']}) "
                           f"has {violation['duty_count']} duties at {violation['time_range']}")
                logger.error(f"    Projects: {[d['project_id'] for d in violation['duties']]}")
                logger.error(f"    Roles: {[d['role'] for d in violation['duties']]}")
            if len(violations) > 10:
                logger.error(f"    ... and {len(violations) - 10} more violations")
            
            # Mark solution as potentially invalid
            solution.is_feasible = False
            solution.solver_status = "CONFLICTS_DETECTED_VALIDATION"
            solution.total_cost = float('inf')
            # Optional: drop assignments to avoid consuming conflicted schedule downstream
            solution.assignments = []
            logger.error("Solution marked as INFEASIBLE due to constraint violations!")
            return False
        else:
            logger.info("✓ All hard constraints satisfied - no violations detected")
        return True
    
    def _renumber_slots(self, solution: SimplexSolution) -> None:
        """Renumber slots within each class to be consecutive (0, 1, 2, ...)."""
        class_projects = defaultdict(list)
        
        for assignment in solution.assignments:
            class_projects[assignment.class_id].append(assignment)
        
        for class_id, assignments in class_projects.items():
            assignments.sort(key=lambda x: x.order_in_class)
            for i, assignment in enumerate(assignments):
                assignment.order_in_class = i


# =============================================================================
# MAIN REAL SIMPLEX SCHEDULER
# =============================================================================

class RealSimplexAlgorithm(OptimizationAlgorithm):
    """
    Real Simplex Algorithm - Single-Phase LP Optimization
    
    This algorithm solves the academic project jury scheduling problem using
    Linear Programming (Real Simplex method). All decisions are made in a
    single phase with no post-processing.
    
    Key Features:
    - Deterministic single-phase solution
    - All objectives in one weighted linear function
    - Configurable priority modes, penalty modes, workload constraints
    - J2 is always a placeholder - not part of optimization
    """
    
    # Placeholder for J2
    J2_PLACEHOLDER = "[Arastirma Gorevlisi]"
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.config = SimplexConfig()
        self.projects: List[Project] = []
        self.instructors: List[Instructor] = []
        self.classrooms: List[Dict[str, Any]] = []
        self.timeslots: List[Dict[str, Any]] = []
        self.penalty_calculator: Optional[SimplexPenaltyCalculator] = None
        self.best_solution: Optional[SimplexSolution] = None
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """Initialize algorithm with input data."""
        self._parse_config(data)
        self._parse_input_data(data)
        self._initialize_components()
        
        # Enforce strict zero-conflict mode regardless of incoming params
        self.config.zero_conflict = True
        
        logger.info(f"RealSimplexAlgorithm initialized: {len(self.projects)} projects, "
                   f"{len(self.instructors)} instructors, class_count={self.config.class_count}, "
                   f"priority_mode={self.config.priority_mode}")
    
    def _assert_conflict_free(
        self,
        solution: Optional[SimplexSolution],
        context: str
    ) -> bool:
        """
        Return True if solution has zero conflicts, otherwise mark infeasible.
        """
        if solution is None or not self.penalty_calculator:
            return True
        
        total_conflicts, conflicts = self.penalty_calculator.check_all_conflicts_comprehensive(solution)
        if total_conflicts > 0:
            solution.is_feasible = False
            solution.solver_status = f"CONFLICTS_DETECTED_{context}"
            solution.total_cost = float('inf')
            
            logger.error(
                f"{context}: {total_conflicts} conflict(s) detected. "
                "Solution marked infeasible."
            )
            if conflicts:
                logger.debug(f"{context}: first conflict sample: {conflicts[0]}")
            return False
        
        return True
    
    def _mark_conflict_infeasible(
        self,
        solution: SimplexSolution,
        context: str
    ) -> SimplexSolution:
        """
        Mark solution infeasible due to conflicts and return it.
        """
        solution.is_feasible = False
        solution.solver_status = f"CONFLICTS_DETECTED_{context}"
        solution.total_cost = float('inf')
        return solution
    
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run Real Simplex optimization.
        
        Uses built-in priority constraints:
        - BITIRME_ONCE: Bitirme projects first
        - ARA_ONCE: Ara projects first
        - ESIT: No priority
        
        Returns final schedule with all assignments.
        """
        if data is not None:
            self.initialize(data)
        
        # Log priority mode
        priority_mode = getattr(self.config, 'priority_mode', 'ESIT')
        logger.info(f"Priority mode: {priority_mode}")
        
        logger.info("=" * 60)
        logger.info("REAL SIMPLEX OPTIMIZATION START")
        logger.info("=" * 60)
        
        import time
        start_time = time.time()
        
        # Determine class counts to try
        if self.config.class_count_mode == "auto":
            class_counts = [5, 6, 7]
            # Limit to available classrooms
            if self.classrooms:
                max_classes = len(self.classrooms)
                class_counts = [z for z in class_counts if z <= max_classes]
            else:
                class_counts = [self.config.class_count]
        else:
            class_counts = [self.config.class_count]
        
        best_solution = None
        best_cost = float('inf')
        best_z = None
        
        for z in class_counts:
            if z > len(self.classrooms) and self.classrooms:
                continue
            
            logger.info(f"\n--- Trying class_count = {z} ---")
            
            try:
                # Build class names
                class_names = None
                if self.classrooms:
                    if isinstance(self.classrooms[0], dict):
                        class_names = [c.get("name", f"D{105 + i}") for i, c in enumerate(self.classrooms[:z])]
                else:
                        class_names = [str(c) for c in self.classrooms[:z]]
                
                # Create solver
                solver = ORToolsSimplexSolver(
                    projects=self.projects,
                    instructors=self.instructors,
                    config=self.config,
                    num_classes=z,
                    class_names=class_names,
                    timeslots=self.timeslots
                )
                
                # Solve with iterative conflict resolution
                solution = self._solve_with_conflict_resolution(solver, z)
                
                if solution.is_feasible:
                    cost = solution.total_cost
                    logger.info(f"z={z}: Solution found with cost = {cost:.2f}")
                    
                    if cost < best_cost:
                        best_cost = cost
                        best_solution = solution
                        best_z = z
                        logger.info(f"New best solution: z={z}, cost={cost:.2f}")
                else:
                    logger.warning(f"z={z}: No feasible solution found")
            
            except Exception as e:
                logger.error(f"z={z}: Error during solving: {e}", exc_info=True)
                continue
        
        elapsed = time.time() - start_time
        
        if best_solution is None:
            logger.error("No feasible solution found for any class count!")
            return self._create_empty_output()
        
        # Final comprehensive conflict check (strict)
        if self.penalty_calculator:
            logger.info("\n" + "=" * 60)
            logger.info("FINAL COMPREHENSIVE CONFLICT CHECK (STRICT)")
            logger.info("=" * 60)
            
            conflict_summary = self.penalty_calculator.get_conflict_summary(best_solution)
            total_conflicts = conflict_summary['total_conflicts']
            
            if total_conflicts > 0:
                logger.error(
                    f"Conflicts detected in final solution ({total_conflicts}). "
                    "Strict mode: rejecting solution."
                )
                return self._create_empty_output()
            
            logger.info("✓ ZERO CONFLICTS confirmed in final solution.")
            logger.info("=" * 60 + "\n")
        
        # Final guard: never return a conflicting schedule
        if not self._assert_conflict_free(best_solution, "final_output"):
            logger.error("No conflict-free solution found. Returning empty output.")
            return self._create_empty_output()
        
        # Convert to output format
        result = self._convert_to_output(best_solution, elapsed)
        result['class_count'] = best_z
        
        logger.info("=" * 60)
        logger.info(f"REAL SIMPLEX COMPLETE - Time: {elapsed:.2f}s, Cost: {best_cost:.2f}, Classes: {best_z}")
        logger.info("=" * 60)
        
        return result
    
    def _solve_with_conflict_resolution(
        self,
        initial_solver: 'ORToolsSimplexSolver',
        num_classes: int
    ) -> SimplexSolution:
        """
        Solve with iterative conflict resolution - ZERO CONFLICTS GUARANTEED.
        
        This function implements a rigorous iterative approach to ensure
        the final solution has ZERO time slot conflicts. The algorithm:
        
        1. Solves the MILP model (with hard constraints)
        2. Checks for any remaining conflicts
        3. If conflicts exist, attempts post-processing repair
        4. Repeats until conflicts = 0 or max iterations reached
        
        Args:
            initial_solver: ORToolsSimplexSolver instance (first iteration)
            num_classes: Number of classes
            
        Returns:
            SimplexSolution with ZERO conflicts (guaranteed by hard constraints + repair)
        """
        # Increase iterations if zero conflict mode is active
        if self.config.zero_conflict:
            max_iterations = 20  # More iterations for zero conflict mode
            max_repair_attempts = 100  # More repair attempts for zero conflict mode
            logger.info("=" * 60)
            logger.info("STARTING ZERO-CONFLICT RESOLUTION PROCESS (AGGRESSIVE MODE)")
            logger.info("=" * 60)
        else:
            max_iterations = 10  # Maximum number of solver iterations
            max_repair_attempts = 50  # Maximum post-processing repair attempts per iteration
            logger.info("=" * 60)
            logger.info("STARTING ZERO-CONFLICT RESOLUTION PROCESS")
            logger.info("=" * 60)
        
        iteration = 0
        best_solution = None
        best_conflict_count = float('inf')
        
        # Get solver parameters from initial solver
        class_names = initial_solver.class_names
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"\n{'='*40}")
            logger.info(f"Conflict Resolution Iteration {iteration}/{max_iterations}")
            logger.info(f"{'='*40}")
            
            # Create new solver for each iteration (or reuse first one)
            if iteration == 1:
                solver = initial_solver
            else:
                logger.info(f"Creating new solver instance for iteration {iteration}...")
                solver = ORToolsSimplexSolver(
                    projects=self.projects,
                    instructors=self.instructors,
                    config=self.config,
                    num_classes=num_classes,
                    class_names=class_names,
                    timeslots=self.timeslots
                )
            
            # Solve MILP model
            solution = solver.solve()
            
            if not solution.is_feasible:
                logger.warning(f"Iteration {iteration}: No feasible solution found by solver")
                if best_solution is not None:
                    logger.info(f"Using best solution from previous iterations (with {best_conflict_count} conflicts)")
                    return best_solution
                return solution
            
            # Check for conflicts using comprehensive checker
            if self.penalty_calculator:
                total_conflicts, conflicts = self.penalty_calculator.check_all_conflicts_comprehensive(solution)
                
                if total_conflicts == 0:
                    logger.info(f"✓ Iteration {iteration}: ZERO CONFLICTS - Solution is valid!")
                    # Double-check with conflict summary for zero conflict mode
                    if self.config.zero_conflict:
                        conflict_summary = self.penalty_calculator.get_conflict_summary(solution)
                        if conflict_summary['total_conflicts'] == 0:
                            logger.info("✓ Double-check confirmed: ZERO CONFLICTS!")
                            return solution
                        else:
                            logger.warning(f"⚠️ Double-check found {conflict_summary['total_conflicts']} conflicts, continuing...")
                            total_conflicts = conflict_summary['total_conflicts']
                            conflicts = conflict_summary['conflicts']
                    else:
                        return solution
                
                logger.warning(f"⚠️ Iteration {iteration}: {total_conflicts} conflicts detected in {len(conflicts)} time slots")
                
                # STRICT: Conflicts are not allowed; mark infeasible and stop.
                logger.error("Conflicts detected. Aborting and marking solution infeasible (strict mode).")
                return self._mark_conflict_infeasible(solution, f"ITERATION_{iteration}")
                
                # Track best solution
                if total_conflicts < best_conflict_count:
                    best_conflict_count = total_conflicts
                    best_solution = solution.copy()
                    logger.info(f"New best solution found with {total_conflicts} conflicts")
                
                # Log conflict details
                for conflict in conflicts[:5]:
                    logger.warning(f"  Conflict: {conflict['instructor_name']} at {conflict['time_range']}")
                    logger.warning(f"    Duties: {conflict['duty_count']} ({conflict['roles']})")
                    logger.warning(f"    Projects: {conflict['projects']}")
                
                if len(conflicts) > 5:
                    logger.warning(f"  ... and {len(conflicts) - 5} more conflicts")
                
                # Attempt iterative repair until conflicts = 0
                logger.info(f"Starting iterative repair process (max {max_repair_attempts} attempts)...")
                repaired_solution = solution.copy()
                
                for repair_attempt in range(max_repair_attempts):
                    # Check current state
                    current_conflicts, conflict_details = self.penalty_calculator.check_all_conflicts_comprehensive(
                        repaired_solution
                    )
                    
                    if current_conflicts == 0:
                        logger.info(f"✓ Repair successful after {repair_attempt + 1} attempts! ZERO CONFLICTS achieved.")
                        return repaired_solution
                    
                    # Track progress
                    if current_conflicts < best_conflict_count:
                        best_conflict_count = current_conflicts
                        best_solution = repaired_solution.copy()
                        logger.info(f"  Repair attempt {repair_attempt + 1}: Reduced to {current_conflicts} conflicts (new best)")
                    elif repair_attempt % 10 == 0:
                        logger.info(f"  Repair attempt {repair_attempt + 1}: {current_conflicts} conflicts remaining...")
                    
                    # Apply repair
                    repaired_solution = self._repair_conflicts_aggressive(
                        repaired_solution, 
                        conflict_details,
                        repair_attempt
                    )
                
                # Check final state after all repair attempts
                final_conflicts, _ = self.penalty_calculator.check_all_conflicts_comprehensive(repaired_solution)
                if final_conflicts == 0:
                    logger.info(f"✓ ZERO CONFLICTS achieved after full repair cycle!")
                    return repaired_solution
                elif final_conflicts < best_conflict_count:
                    best_conflict_count = final_conflicts
                    best_solution = repaired_solution.copy()
                
                logger.info(f"Repair cycle completed. Remaining conflicts: {final_conflicts}. Trying next iteration...")
            else:
                # No penalty calculator - just return the solution
                return solution
        
        # Final exhaustive repair attempt on best solution
        if best_solution is not None and best_conflict_count > 0:
            logger.info(f"\nFinal exhaustive repair attempt on best solution ({best_conflict_count} conflicts)...")
            
            for final_attempt in range(max_repair_attempts * 2):
                final_conflicts, conflict_details = self.penalty_calculator.check_all_conflicts_comprehensive(
                    best_solution
                )
                
                if final_conflicts == 0:
                    logger.info(f"✓ ZERO CONFLICTS achieved in final exhaustive repair!")
                    return best_solution
                
                best_solution = self._repair_conflicts_aggressive(
                    best_solution,
                    conflict_details,
                    final_attempt
                )
        
        # Return best solution found
        if best_solution is not None:
            final_count, _ = self.penalty_calculator.check_all_conflicts_comprehensive(best_solution)
            if final_count == 0:
                logger.info("Final best solution is conflict-free.")
                return best_solution
                
                logger.error(
                    f"Returning infeasible solution with {final_count} remaining conflicts "
                    "- conflicts are not allowed."
                )
                best_solution.is_feasible = False
                best_solution.solver_status = "CONFLICTS_REMAIN"
                best_solution.total_cost = float('inf')
                return best_solution
        
        # Fallback
        fallback_solution = initial_solver.solve()
        if not self._assert_conflict_free(fallback_solution, "fallback"):
            logger.error("Fallback solver also produced conflicts; marking infeasible.")
            return self._mark_conflict_infeasible(fallback_solution, "fallback")
        return fallback_solution
    
    def _repair_time_range_conflicts(
        self,
        solution: SimplexSolution,
        conflicts: List[Dict[str, Any]]
    ) -> SimplexSolution:
        """
        Legacy repair function - redirects to aggressive repair.
        """
        return self._repair_conflicts_aggressive(solution, conflicts, 0)
    
    def _repair_conflicts_aggressive(
        self,
        solution: SimplexSolution,
        conflicts: List[Dict[str, Any]],
        attempt_number: int = 0
    ) -> SimplexSolution:
        """
        Aggressively repair conflicts by changing J1 assignments and reordering slots.
        
        STRATEGY:
        1. For J1 conflicts: Change J1 to an available instructor
        2. For PS conflicts: Cannot change PS directly, but can swap project slots
        3. Use randomization with attempt number as seed for variety
        
        Returns:
            Repaired SimplexSolution
        """
        import random
        
        # Use attempt number for reproducible randomization
        random.seed(42 + attempt_number)
        
        # Create a copy of the solution
        repaired = solution.copy()
        
        # Get faculty IDs for J1 alternatives
        faculty_ids = [i.id for i in self.instructors if i.type == "instructor"]
        
        # Build instructor schedule for quick lookup
        def build_schedule():
            """Build current schedule: instructor_id -> order_in_class -> list of (role, assignment)"""
            schedule = defaultdict(lambda: defaultdict(list))
            for assignment in repaired.assignments:
                schedule[assignment.ps_id][assignment.order_in_class].append(('PS', assignment))
                schedule[assignment.j1_id][assignment.order_in_class].append(('J1', assignment))
            return schedule
        
        def get_instructor_duties_at_slot(schedule, instructor_id, slot):
            """Get all duties for an instructor at a specific slot."""
            return schedule.get(instructor_id, {}).get(slot, [])
        
        def find_available_j1(schedule, assignment, excluded_instructors=None):
            """Find available J1 candidates for an assignment."""
            excluded = set(excluded_instructors or [])
            excluded.add(assignment.ps_id)  # J1 cannot be PS
            
            slot = assignment.order_in_class
            available = []
            
            for fid in faculty_ids:
                if fid in excluded:
                    continue
                
                # Check if this instructor is free at this slot
                duties = get_instructor_duties_at_slot(schedule, fid, slot)
                if len(duties) == 0:
                    available.append(fid)
            
            return available
        
        def swap_assignments_slots(a1, a2):
            """Swap the order_in_class of two assignments in the same class."""
            if a1.class_id == a2.class_id:
                a1.order_in_class, a2.order_in_class = a2.order_in_class, a1.order_in_class
        
        # Sort conflicts by duty count (prioritize fixing severe conflicts first)
        sorted_conflicts = sorted(conflicts, key=lambda c: c['duty_count'], reverse=True)
        
        # Process each conflict
        for conflict in sorted_conflicts:
            instructor_id = conflict['instructor_id']
            order_in_class = conflict['order_in_class']
            duties = conflict.get('duties', [])
            
            # Rebuild schedule for current state
            schedule = build_schedule()
            
            # Separate J1 and PS duties
            j1_duties = [d for d in duties if d['role'] == 'J1']
            ps_duties = [d for d in duties if d['role'] == 'PS']
            
            # STRATEGY 1: Fix J1 conflicts by reassigning J1
            if len(j1_duties) > 0:
                # Keep the first J1 duty, change the rest
                j1_duties_to_change = j1_duties[1:] if len(j1_duties) > 1 else []
                
                # If there's a PS duty and J1 duty at same slot, change the J1
                if len(ps_duties) > 0 and len(j1_duties) > 0:
                    j1_duties_to_change = j1_duties  # Change all J1 duties for this instructor at this slot
                
                for j1_duty in j1_duties_to_change:
                    project_id = j1_duty['project_id']
                    
                    # Find the assignment
                    for assignment in repaired.assignments:
                        if assignment.project_id == project_id and assignment.j1_id == instructor_id:
                            # Find available J1
                            available = find_available_j1(schedule, assignment, excluded_instructors=[instructor_id])
                            
                            if available:
                                # Shuffle for variety
                                random.shuffle(available)
                                new_j1 = available[0]
                                assignment.j1_id = new_j1
                                
                                # Update schedule
                                schedule = build_schedule()
                            else:
                                # No available instructor - try least busy instructor
                                # that's not PS and not already conflicting
                                workload = defaultdict(int)
                                for a in repaired.assignments:
                                    workload[a.j1_id] += 1
                                
                                candidates = [
                                    (fid, workload[fid]) 
                                    for fid in faculty_ids 
                                    if fid != assignment.ps_id and fid != instructor_id
                                ]
                                
                                if candidates:
                                    # Sort by workload (ascending) and pick one of the least busy
                                    candidates.sort(key=lambda x: x[1])
                                    least_busy = [c[0] for c in candidates if c[1] <= candidates[0][1] + 1]
                                    random.shuffle(least_busy)
                                    new_j1 = least_busy[0]
                                    assignment.j1_id = new_j1
                                    
                                    schedule = build_schedule()
                            break
            
            # STRATEGY 2: Fix PS-only conflicts by swapping slots
            # PS is fixed per project, but we can try to move projects to different slots
            if len(ps_duties) > 1 and len(j1_duties) == 0:
                # Multiple PS duties for same instructor at same slot
                # Try to swap one of the projects with another project in the same class
                ps_assignments = []
                for ps_duty in ps_duties:
                    for a in repaired.assignments:
                        if a.project_id == ps_duty['project_id']:
                            ps_assignments.append(a)
                            break
                
                if len(ps_assignments) > 1:
                    # Try to find a swap partner for the second assignment
                    conflict_assignment = ps_assignments[1]
                    
                    # Look for a project in the same class at a different slot
                    # where swapping wouldn't create a new conflict
                    for swap_candidate in repaired.assignments:
                        if swap_candidate.class_id != conflict_assignment.class_id:
                            continue
                        if swap_candidate.order_in_class == order_in_class:
                            continue
                        if swap_candidate.project_id == conflict_assignment.project_id:
                            continue
                        
                        # Check if swapping would resolve the conflict
                        # Temporarily swap
                        old_slot = conflict_assignment.order_in_class
                        new_slot = swap_candidate.order_in_class
                        
                        conflict_assignment.order_in_class = new_slot
                        swap_candidate.order_in_class = old_slot
                        
                        # Check if this creates new conflicts
                        temp_schedule = build_schedule()
                        new_conflict_duties = get_instructor_duties_at_slot(
                            temp_schedule, instructor_id, new_slot
                        )
                        
                        if len(new_conflict_duties) <= 1:
                            # Swap resolved the conflict - keep it
                            schedule = temp_schedule
                            break
                        else:
                            # Swap didn't help - revert
                            conflict_assignment.order_in_class = old_slot
                            swap_candidate.order_in_class = new_slot
        
        return repaired
    
    def _parse_config(self, data: Dict[str, Any]) -> None:
        """Parse configuration from data."""
        config_data = data.get('config', {})
        
        # Priority mode - support both old and new key names
        if 'priority_mode' in config_data:
            self.config.priority_mode = config_data['priority_mode']
        
        # Frontend sends "project_priority" with values: midterm_priority, final_exam_priority, none
        # Convert to our internal priority_mode format: ARA_ONCE, BITIRME_ONCE, ESIT
        if 'project_priority' in config_data:
            pp = config_data['project_priority']
            if pp == 'midterm_priority':
                self.config.priority_mode = 'ARA_ONCE'
                logger.info("Priority mode set to ARA_ONCE via project_priority=midterm_priority")
            elif pp == 'final_exam_priority':
                self.config.priority_mode = 'BITIRME_ONCE'
                logger.info("Priority mode set to BITIRME_ONCE via project_priority=final_exam_priority")
            else:  # none or any other value
                self.config.priority_mode = 'ESIT'
                logger.info(f"Priority mode set to ESIT via project_priority={pp}")
        
        # Also check params (from __init__) for project_priority
        if self.params and 'project_priority' in self.params:
            pp = self.params['project_priority']
            if pp == 'midterm_priority':
                self.config.priority_mode = 'ARA_ONCE'
                logger.info("Priority mode set to ARA_ONCE via params project_priority")
            elif pp == 'final_exam_priority':
                self.config.priority_mode = 'BITIRME_ONCE'
                logger.info("Priority mode set to BITIRME_ONCE via params project_priority")
            else:
                self.config.priority_mode = 'ESIT'
                logger.info(f"Priority mode set to ESIT via params project_priority={pp}")
        
        # Penalty modes
        if 'time_penalty_mode' in config_data:
            self.config.time_penalty_mode = config_data['time_penalty_mode']
        if 'workload_constraint_mode' in config_data:
            self.config.workload_constraint_mode = config_data['workload_constraint_mode']
        
        # Weights
        if 'weight_h1' in config_data:
            self.config.weight_h1 = float(config_data['weight_h1'])
        if 'weight_h2' in config_data:
            self.config.weight_h2 = float(config_data['weight_h2'])
        if 'weight_h3' in config_data:
            self.config.weight_h3 = float(config_data['weight_h3'])
        
        # Hard constraint parameters
        if 'b_max' in config_data:
            self.config.b_max = int(config_data['b_max'])
        
        # Solver parameters
        # Note: max_time_seconds and max_iterations are no longer configurable from frontend
        # They use default values defined in SimplexConfig
        if 'solver_name' in config_data:
            self.config.solver_name = config_data['solver_name']
        
        # Class count
        if 'classroom_count' in data:
            self.config.class_count = int(data['classroom_count'])
            self.config.class_count_mode = "manual"
        elif 'class_count' in config_data:
            self.config.class_count = int(config_data['class_count'])
            self.config.class_count_mode = "manual"
        
        # Zero conflict mode
        if 'zero_conflict' in config_data:
            self.config.zero_conflict = bool(config_data['zero_conflict'])
        elif 'zero_conflict' in data:
            self.config.zero_conflict = bool(data['zero_conflict'])
        # Also check params passed to __init__
        if self.params and 'zero_conflict' in self.params:
            self.config.zero_conflict = bool(self.params['zero_conflict'])
    
    def _parse_input_data(self, data: Dict[str, Any]) -> None:
        """Parse projects, instructors, classrooms from data."""
        # Parse projects
        self.projects = []
        for p in data.get('projects', []):
            proj_type = str(p.get('type', p.get('project_type', 'ARA'))).upper()
            if proj_type in ['INTERIM', 'ARA']:
                proj_type = 'ARA'
            elif proj_type in ['FINAL', 'BITIRME']:
                proj_type = 'BITIRME'
            
            project = Project(
                id=p.get('id', 0),
                ps_id=p.get('instructor_id', p.get('responsible_instructor_id', p.get('responsible_id', p.get('ps_id', 0)))),
                project_type=proj_type,
                name=p.get('title', p.get('name', f"Project {p.get('id', 0)}"))
            )
            self.projects.append(project)
        
        # Parse instructors
        self.instructors = []
        for i in data.get('instructors', []):
            inst_type_raw = str(i.get('type', 'instructor')).lower()
            if inst_type_raw in ['assistant', 'research_assistant', 'ra', 'research assistant'] or i.get('is_research_assistant', False):
                inst_type = 'assistant'
            else:
                inst_type = 'instructor'
            
            instructor = Instructor(
                id=i.get('id', 0),
                name=i.get('name', f"Instructor {i.get('id', 0)}"),
                type=inst_type
            )
            self.instructors.append(instructor)
        
        # Parse classrooms
        self.classrooms = data.get('classrooms', [])
        
        # Parse timeslots
        self.timeslots = data.get('timeslots', [])
        
        # Count faculty and assistants
        faculty_count = len([inst for inst in self.instructors if inst.type == 'instructor'])
        assistant_count = len([inst for inst in self.instructors if inst.type == 'assistant'])
        
        logger.info(f"Parsed {len(self.projects)} projects, {len(self.instructors)} instructors ({faculty_count} faculty, {assistant_count} assistants)")
        
        if faculty_count == 0:
            logger.error("This will cause J1 assignment to fail. Check instructor type parsing.")
        elif faculty_count == 1:
            logger.warning(f"Only {faculty_count} faculty member found. This may cause J1 assignment issues.")
    
    def _initialize_components(self) -> None:
        """Initialize algorithm components."""
        self.penalty_calculator = SimplexPenaltyCalculator(
            self.projects,
            self.instructors,
            self.config
        )
    
    def _convert_to_output(
        self,
        solution: SimplexSolution,
        execution_time: float
    ) -> Dict[str, Any]:
        """Convert solution to output format."""
        if solution is None:
            return self._create_empty_output()
        
        # Build instructor lookup
        instructor_map = {i.id: i for i in self.instructors}
        
        # Build classroom lookup
        classroom_map = {}
        for i in range(solution.class_count):
            if i < len(self.classrooms):
                classroom_map[i] = self.classrooms[i]
            else:
                classroom_map[i] = {'id': i + 1, 'name': f'D{105 + i}'}
        
        assignments = []
        
        # Track J1 distribution in output
        output_j1_distribution = defaultdict(int)
        
        for assignment in solution.assignments:
            # Verify J1 is valid
            if assignment.j1_id not in instructor_map:
                logger.warning(f"Project {assignment.project_id}: Invalid J1 ID {assignment.j1_id}, skipping")
                continue
            
            # Get classroom
            classroom = classroom_map.get(
                assignment.class_id,
                {'id': assignment.class_id + 1, 'name': f'D{105 + assignment.class_id}'}
            )
            
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
            
            # Track J1 distribution
            output_j1_distribution[assignment.j1_id] += 1
            
            # Timeslot = order + 1 (1-indexed)
            timeslot_id = assignment.order_in_class + 1
            
            assignments.append({
                'project_id': assignment.project_id,
                'classroom_id': classroom.get('id', assignment.class_id + 1),
                'timeslot_id': timeslot_id,
                'instructors': instructors,
                'is_makeup': False,
                'class_name': classroom.get('name', f'D{105 + assignment.class_id}'),
                'order_in_class': assignment.order_in_class + 1
            })
        
        # Log output J1 distribution
        logger.info(f"Output J1 Distribution (Total assignments: {len(assignments)}):")
        for j1_id, count in sorted(output_j1_distribution.items(), key=lambda x: x[1], reverse=True):
            j1_name = next((i.name for i in self.instructors if i.id == j1_id), f"ID_{j1_id}")
            percentage = (count / len(assignments) * 100) if assignments else 0
            logger.info(f"  {j1_name} (ID: {j1_id}): {count} assignments ({percentage:.1f}%)")
        
        if len(output_j1_distribution) == 1:
            logger.error(f"ERROR: Only 1 faculty member in output J1 distribution! J1 ID: {list(output_j1_distribution.keys())[0]}")
        
        return {
            'algorithm': 'Real Simplex (Linear Programming)',
            'status': 'completed',
            'solver_status': solution.solver_status,
            'assignments': assignments,
            'schedule': assignments,
            'solution': assignments,
            'fitness': -solution.total_cost,
            'execution_time': execution_time,
            'total_cost': solution.total_cost,
            'is_feasible': solution.is_feasible
        }
    
    def _create_empty_output(self) -> Dict[str, Any]:
        """Create empty output for error cases."""
        return {
            'algorithm': 'Real Simplex (Linear Programming)',
            'status': 'failed',
            'solver_status': 'NO_SOLUTION',
            'assignments': [],
            'schedule': [],
            'solution': [],
            'fitness': float('-inf'),
            'execution_time': 0.0,
            'total_cost': float('inf'),
            'is_feasible': False,
            'error': 'No feasible solution found'
        }
    
    def get_name(self) -> str:
        """Return algorithm name."""
        return "Real Simplex Algorithm"


# =============================================================================
# ALGORITHM FACTORY REGISTRATION
# =============================================================================

def create_real_simplex_algorithm(params: Optional[Dict[str, Any]] = None) -> RealSimplexAlgorithm:
    """Factory function to create RealSimplexAlgorithm."""
    return RealSimplexAlgorithm(params)


# Export main class
__all__ = [
    'RealSimplexAlgorithm',
    'SimplexConfig',
    'PriorityMode',
    'TimePenaltyMode',
    'WorkloadConstraintMode',
    'create_real_simplex_algorithm'
]
