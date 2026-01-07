"""
Dynamic Programming Algorithm - Multi-Criteria Optimization
Aligned with Simulated Annealing constraint structure

OBJECTIVE FUNCTION:
    min Z = C1*H1(n) + C2*H2(n) + C3*H3(n) + C4*H4(n) + C5*H5(n) + C6*H6(n) + C7*H7(n)
    
    Where C2 > C1, C2 > C3 (workload uniformity is most important)

PENALTY FUNCTIONS:
    H1: Time/Gap penalty (consecutive scheduling)
    H2: Workload uniformity penalty (±2 band)
    H3: Class change penalty
    H4: Class load balance penalty
    H5: Continuity penalty
    H6: Timeslot conflict penalty (HARD - proactive prevention)
    H7: Unused class penalty (HARD)

HARD CONSTRAINTS (enforced proactively):
    1. Back-to-back placement (no gaps between projects in same class)
    2. Single-duty per timeslot (instructor can't be in multiple places)
    3. J1 != PS (jury member cannot be project supervisor)
    4. Exact class count (all classes must be used)
    5. J2 is placeholder (-1), excluded from all calculations

SOFT CONSTRAINTS:
    1. Workload uniformity within ±2 band (can be hard with SOFT_AND_HARD mode)
    2. Minimize class changes for instructors
    3. Consecutive grouping preference

CONFIGURATION:
    - priority_mode: ARA_ONCE, BITIRME_ONCE, ESIT
    - time_penalty_mode: BINARY, GAP_PROPORTIONAL
    - workload_constraint_mode: SOFT_ONLY, SOFT_AND_HARD
"""

from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import random
import numpy as np
import time
import logging
from collections import defaultdict
from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# =============================================================================
# ENUMS FOR CONFIGURATION
# =============================================================================

class PriorityMode(Enum):
    """Project type prioritization mode"""
    ARA_ONCE = "ARA_ONCE"           # Interim projects first
    BITIRME_ONCE = "BITIRME_ONCE"   # Final projects first
    ESIT = "ESIT"                   # No priority


class TimePenaltyMode(Enum):
    """Time/gap penalty calculation mode"""
    BINARY = "BINARY"                       # 0 or 1 penalty
    GAP_PROPORTIONAL = "GAP_PROPORTIONAL"   # Penalty proportional to gap size


class WorkloadConstraintMode(Enum):
    """Workload constraint enforcement mode"""
    SOFT_ONLY = "SOFT_ONLY"           # Only soft penalty
    SOFT_AND_HARD = "SOFT_AND_HARD"   # Soft penalty + hard limit


# =============================================================================
# CONFIGURATION DATACLASS
# =============================================================================

@dataclass
class DPConfig:
    """Configuration for Dynamic Programming algorithm"""
    
    # Class count
    class_count: int = 6
    auto_class_count: bool = True
    
    # Priority and penalty modes
    priority_mode: PriorityMode = PriorityMode.ESIT
    time_penalty_mode: TimePenaltyMode = TimePenaltyMode.GAP_PROPORTIONAL
    workload_constraint_mode: WorkloadConstraintMode = WorkloadConstraintMode.SOFT_ONLY
    workload_hard_limit: int = 4  # B_max - maximum workload per instructor
    
    # Penalty weights (C1, C2, C3, C4, C5, C6, C7)
    weight_h1: float = 1.0    # Time/Gap penalty
    weight_h2: float = 2.0    # Workload uniformity penalty (most important)
    weight_h3: float = 3.0    # Class change penalty
    weight_h4: float = 0.5    # Class load balance penalty
    weight_h5: float = 5.0    # Continuity penalty
    weight_h6: float = 1000.0 # Timeslot conflict penalty (HARD)
    weight_h7: float = 10000.0 # Unused class penalty (HARD)
    
    # DP-specific parameters
    beam_width: int = 10      # Number of best solutions to keep
    max_iterations: int = 1000
    tolerance: float = 0.001


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Project:
    """Project data structure"""
    id: int
    name: str
    type: str  # "INTERIM" or "FINAL"
    responsible_id: int  # PS (advisor) - fixed


@dataclass
class Instructor:
    """Instructor data structure"""
    id: int
    name: str
    type: str  # "instructor" or "research_assistant"


@dataclass
class ProjectAssignment:
    """Assignment of a single project"""
    project_id: int
    class_id: int
    order_in_class: int
    ps_id: int      # Fixed advisor
    j1_id: int      # Jury 1 (decision variable)
    j2_id: int = -1  # Placeholder for RA (excluded from calculations)


@dataclass
class DPState:
    """DP solution state"""
    assignments: List[ProjectAssignment] = field(default_factory=list)
    class_count: int = 6
    cost: float = float('inf')
    
    def copy(self) -> 'DPState':
        """Create a deep copy of this state"""
        new_state = DPState(class_count=self.class_count, cost=self.cost)
        new_state.assignments = [
            ProjectAssignment(
                project_id=a.project_id,
                class_id=a.class_id,
                order_in_class=a.order_in_class,
                ps_id=a.ps_id,
                j1_id=a.j1_id,
                j2_id=a.j2_id
            )
            for a in self.assignments
        ]
        return new_state
    
    def get_project_assignment(self, project_id: int) -> Optional[ProjectAssignment]:
        """Get assignment for a specific project"""
        for a in self.assignments:
            if a.project_id == project_id:
                return a
        return None


# =============================================================================
# PENALTY CALCULATOR
# =============================================================================

class DPPenaltyCalculator:
    """
    Calculate all penalty values for DP cost function.
    
    Implements:
    - H1: Time/Gap penalty
    - H2: Workload uniformity penalty (±2 band)
    - H3: Class change penalty
    - H4: Class load balance penalty
    - H5: Continuity penalty
    - H6: Timeslot conflict penalty (hard)
    - H7: Unused class penalty (hard)
    """
    
    def __init__(
        self, 
        projects: List[Project], 
        instructors: List[Instructor], 
        config: DPConfig
    ):
        self.projects = {p.id: p for p in projects}
        self.instructors = {i.id: i for i in instructors}
        self.config = config
        
        # Filter real faculty (not research assistants)
        self.faculty_instructors = {
            i.id: i for i in instructors 
            if i.type == "instructor"
        }
        
        # Calculate average workload
        num_projects = len(projects)
        num_faculty = len(self.faculty_instructors)
        self.avg_workload = (2 * num_projects) / num_faculty if num_faculty > 0 else 0
    
    def calculate_total_cost(self, state: DPState) -> float:
        """
        Calculate total cost (penalty) for a state.
        
        Cost = C1*H1 + C2*H2 + C3*H3 + C4*H4 + C5*H5 + C6*H6 + C7*H7
        """
        h1 = self.calculate_h1_time_penalty(state)
        h2 = self.calculate_h2_workload_penalty(state)
        h3 = self.calculate_h3_class_change_penalty(state)
        h4 = self.calculate_h4_class_load_penalty(state)
        h5 = self.calculate_h5_continuity_penalty(state)
        h6 = self.calculate_h6_timeslot_conflict_penalty(state)
        h7 = self.calculate_h7_unused_class_penalty(state)
        
        total = (
            self.config.weight_h1 * h1 +
            self.config.weight_h2 * h2 +
            self.config.weight_h3 * h3 +
            self.config.weight_h4 * h4 +
            self.config.weight_h5 * h5 +
            self.config.weight_h6 * h6 +
            self.config.weight_h7 * h7
        )
        
        return total
    
    def calculate_h1_time_penalty(self, state: DPState) -> float:
        """
        H1: Time/Gap penalty for non-consecutive tasks.
        
        Binary mode: 1 if not consecutive, 0 otherwise
        GAP_PROPORTIONAL mode: gap size as penalty
        """
        total_penalty = 0.0
        
        # Build task matrix for each instructor
        instructor_tasks = self._build_instructor_task_matrix(state)
        
        for instructor_id, tasks in instructor_tasks.items():
            if len(tasks) <= 1:
                continue
            
            # Sort by timeslot (class_id * 100 + order)
            tasks.sort(key=lambda x: x['class_id'] * 100 + x['order'])
            
            # Calculate gap penalties between consecutive tasks
            for i in range(len(tasks) - 1):
                current = tasks[i]
                next_task = tasks[i + 1]
                
                # Check if same class and consecutive
                if current['class_id'] == next_task['class_id']:
                    gap = next_task['order'] - current['order'] - 1
                    if gap > 0:
                        if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                            total_penalty += 1
                        else:  # GAP_PROPORTIONAL
                            total_penalty += gap
                else:
                    # Different class - always penalty
                    if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                        total_penalty += 1
                    else:
                        # Calculate equivalent gap
                        total_penalty += 2  # Cross-class penalty
        
        return total_penalty
    
    def calculate_h2_workload_penalty(self, state: DPState) -> float:
        """
        H2: Workload uniformity penalty.
        
        For each instructor:
        penalty = max(0, |Load(h) - AvgLoad| - 2)
        
        The ±2 band means deviations within 2 are acceptable.
        """
        total_penalty = 0.0
        
        # Count workload per instructor
        workloads = defaultdict(int)
        for assignment in state.assignments:
            workloads[assignment.ps_id] += 1  # PS role
            workloads[assignment.j1_id] += 1  # J1 role
            # J2 is placeholder, excluded from calculations
        
        # Calculate penalty for each faculty member
        for instructor_id in self.faculty_instructors.keys():
            load = workloads.get(instructor_id, 0)
            deviation = abs(load - self.avg_workload)
            penalty = max(0, deviation - 2)  # ±2 band tolerance
            total_penalty += penalty
        
        return total_penalty
    
    def calculate_h3_class_change_penalty(self, state: DPState) -> float:
        """
        H3: Class change penalty.
        
        For each instructor:
        penalty = max(0, NumberOfClasses(h) - 2)^2 * 5
        """
        total_penalty = 0.0
        
        # Find classes used by each instructor
        instructor_classes = defaultdict(set)
        for assignment in state.assignments:
            instructor_classes[assignment.ps_id].add(assignment.class_id)
            instructor_classes[assignment.j1_id].add(assignment.class_id)
        
        for instructor_id in self.faculty_instructors.keys():
            class_count = len(instructor_classes.get(instructor_id, set()))
            if class_count > 2:
                # Squared penalty for excessive class changes
                penalty = (class_count - 2) ** 2 * 5
                total_penalty += penalty
        
        return total_penalty
    
    def calculate_h4_class_load_penalty(self, state: DPState) -> float:
        """
        H4: Class load balance penalty.
        
        Each class should have approximately equal number of projects.
        """
        total_penalty = 0.0
        
        num_projects = len(state.assignments)
        if num_projects == 0:
            return 0.0
        
        target_per_class = num_projects / state.class_count
        
        # Count projects per class
        class_loads = defaultdict(int)
        for assignment in state.assignments:
            class_loads[assignment.class_id] += 1
        
        # Calculate penalty for each class
        for class_id in range(state.class_count):
            load = class_loads.get(class_id, 0)
            if load > 0:
                penalty = abs(load - target_per_class)
                total_penalty += penalty
        
        return total_penalty
    
    def calculate_h5_continuity_penalty(self, state: DPState) -> float:
        """
        H5: Continuity penalty.
        
        Penalizes instructors who have fragmented schedules
        (multiple separate blocks instead of continuous tasks).
        """
        total_penalty = 0.0
        
        # Build task matrix
        instructor_tasks = self._build_instructor_task_matrix(state)
        
        for instructor_id, tasks in instructor_tasks.items():
            if len(tasks) <= 1:
                continue
            
            # Group tasks by class
            tasks_by_class = defaultdict(list)
            for task in tasks:
                tasks_by_class[task['class_id']].append(task)
            
            # Count blocks per class
            for class_id, class_tasks in tasks_by_class.items():
                if len(class_tasks) <= 1:
                    continue
                
                # Sort by order
                class_tasks.sort(key=lambda x: x['order'])
                
                # Count separate blocks
                blocks = 1
                for i in range(len(class_tasks) - 1):
                    if class_tasks[i + 1]['order'] - class_tasks[i]['order'] > 1:
                        blocks += 1
                
                # Penalty for extra blocks
                if blocks > 1:
                    total_penalty += (blocks - 1) ** 2 * 10
        
        return total_penalty
    
    def calculate_h6_timeslot_conflict_penalty(self, state: DPState) -> float:
        """
        H6: Timeslot conflict penalty (HARD constraint).
        
        Penalizes instructors who have multiple tasks in the same timeslot.
        CRITICAL: Same order_in_class across different classes = SAME TIMESLOT!
        """
        total_penalty = 0.0
        
        # Build instructor schedule: instructor_id -> order -> list of class_ids
        instructor_schedule = defaultdict(lambda: defaultdict(list))
        
        for assignment in state.assignments:
            # PS role
            instructor_schedule[assignment.ps_id][assignment.order_in_class].append(assignment.class_id)
            # J1 role
            instructor_schedule[assignment.j1_id][assignment.order_in_class].append(assignment.class_id)
        
        # Find conflicts: multiple assignments at same timeslot (order)
        for instructor_id, orders in instructor_schedule.items():
            for order, classes in orders.items():
                if len(classes) > 1:
                    # Check if they are in DIFFERENT classes (real conflict)
                    unique_classes = set(classes)
                    if len(unique_classes) > 1:
                        # CONFLICT: Instructor in multiple classes at same time
                        total_penalty += (len(unique_classes) - 1) * 1.0
        
        return total_penalty
    
    def calculate_h7_unused_class_penalty(self, state: DPState) -> float:
        """
        H7: Unused class penalty (HARD constraint).
        
        All specified classes must be used.
        """
        used_classes = set()
        for assignment in state.assignments:
            used_classes.add(assignment.class_id)
        
        unused_count = state.class_count - len(used_classes)
        if unused_count > 0:
            return unused_count * unused_count * 100.0  # Squared penalty
        return 0.0
    
    def count_conflicts(self, state: DPState) -> int:
        """Count the number of timeslot conflicts in the state."""
        conflict_count = 0
        
        # Build instructor schedule: instructor_id -> order -> set of class_ids
        instructor_schedule = defaultdict(lambda: defaultdict(set))
        
        for assignment in state.assignments:
            # PS role
            instructor_schedule[assignment.ps_id][assignment.order_in_class].add(assignment.class_id)
            # J1 role
            instructor_schedule[assignment.j1_id][assignment.order_in_class].add(assignment.class_id)
        
        # Count conflicts
        for instructor_id, orders in instructor_schedule.items():
            for order, classes in orders.items():
                if len(classes) > 1:
                    conflict_count += len(classes) - 1
        
        return conflict_count
    
    def _build_instructor_task_matrix(self, state: DPState) -> Dict[int, List[Dict]]:
        """Build task matrix for each instructor"""
        instructor_tasks = defaultdict(list)
        
        for assignment in state.assignments:
            # PS task
            instructor_tasks[assignment.ps_id].append({
                'project_id': assignment.project_id,
                'class_id': assignment.class_id,
                'order': assignment.order_in_class,
                'role': 'PS'
            })
            
            # J1 task
            instructor_tasks[assignment.j1_id].append({
                'project_id': assignment.project_id,
                'class_id': assignment.class_id,
                'order': assignment.order_in_class,
                'role': 'J1'
            })
        
        return instructor_tasks


# =============================================================================
# SOLUTION BUILDER WITH PROACTIVE CONFLICT PREVENTION
# =============================================================================

class DPSolutionBuilder:
    """
    Build DP solutions with PROACTIVE conflict prevention.
    
    Key principle: conflict-free solutions by design, not by repair.
    Uses instructor_schedule as the central component to track all assignments.
    """
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: DPConfig,
        penalty_calculator: DPPenaltyCalculator
    ):
        self.projects = projects
        self.projects_dict = {p.id: p for p in projects}
        self.instructors = instructors
        self.config = config
        self.penalty_calculator = penalty_calculator
        
        # Faculty IDs (not research assistants)
        self.faculty_ids = [
            i.id for i in instructors 
            if i.type == "instructor"
        ]
        
        # Track projects by instructor
        self.projects_by_instructor = defaultdict(list)
        for p in projects:
            self.projects_by_instructor[p.responsible_id].append(p)
        
        # Average workload
        num_projects = len(projects)
        num_faculty = len(self.faculty_ids)
        self.avg_workload = (2 * num_projects) / num_faculty if num_faculty > 0 else 0
        
        # CENTRAL COMPONENT: Instructor schedule tracking
        # Key: (class_id, order_in_class) -> set of instructor_ids busy at this slot
        self.instructor_schedule: Dict[Tuple[int, int], Set[int]] = {}
    
    def _reset_schedule(self) -> None:
        """Reset the instructor schedule for new solution building."""
        self.instructor_schedule = {}
    
    def _is_instructor_available(self, instructor_id: int, class_id: int, slot: int) -> bool:
        """
        Check if an instructor is available at a given timeslot.
        
        CRITICAL: Same slot across ANY class = same timeslot.
        An instructor busy at slot X in class A cannot be at slot X in class B.
        """
        # Check all classes at this slot
        for c in range(self.config.class_count):
            key = (c, slot)
            if key in self.instructor_schedule:
                if instructor_id in self.instructor_schedule[key]:
                    return False
        return True
    
    def _mark_instructor_busy(self, instructor_id: int, class_id: int, slot: int) -> None:
        """Mark an instructor as busy at a specific timeslot."""
        key = (class_id, slot)
        if key not in self.instructor_schedule:
            self.instructor_schedule[key] = set()
        self.instructor_schedule[key].add(instructor_id)
    
    def _get_available_j1_candidates(
        self, 
        ps_id: int, 
        class_id: int, 
        slot: int
    ) -> List[int]:
        """
        Get list of J1 candidates who are:
        1. Not the PS (J1 != PS)
        2. Not busy at this timeslot (no conflict)
        """
        candidates = []
        for fid in self.faculty_ids:
            if fid == ps_id:
                continue  # J1 != PS
            if not self._is_instructor_available(fid, class_id, slot):
                continue  # Already busy at this slot
            candidates.append(fid)
        return candidates
    
    def _select_best_j1(
        self, 
        ps_id: int, 
        class_id: int, 
        slot: int, 
        workloads: Dict[int, int]
    ) -> int:
        """
        Select the best J1 based on:
        1. Availability (no conflict)
        2. Lowest workload (load balancing)
        3. Random tie-breaking among equals
        
        Returns -1 if no J1 is available.
        """
        candidates = self._get_available_j1_candidates(ps_id, class_id, slot)
        
        if not candidates:
            return -1  # No available J1 at this slot
        
        # Sort by workload (ascending)
        candidates.sort(key=lambda x: workloads.get(x, 0))
        
        # Find all candidates with minimum workload
        min_workload = workloads.get(candidates[0], 0)
        best_candidates = [c for c in candidates if workloads.get(c, 0) == min_workload]
        
        # Random tie-breaking
        return random.choice(best_candidates)
    
    def build_initial_solution(self) -> DPState:
        """
        Build an initial solution with PROACTIVE conflict prevention.
        
        Strategy:
        1. Sort projects by priority (if configured)
        2. For each project, find a slot where both PS and J1 can be assigned without conflict
        3. Distribute evenly across all classes to satisfy H7 (all classes used)
        """
        self._reset_schedule()
        
        state = DPState(class_count=self.config.class_count)
        
        # Sort projects by priority
        sorted_projects = self._sort_projects_by_priority()
        
        # Track workloads for load balancing
        workloads = defaultdict(int)
        
        # Track class loads for even distribution
        class_loads = defaultdict(int)
        
        # Calculate target projects per class
        projects_per_class = len(sorted_projects) // self.config.class_count
        extra_projects = len(sorted_projects) % self.config.class_count
        
        # Build class order for round-robin distribution
        class_order = list(range(self.config.class_count))
        random.shuffle(class_order)
        
        # Assign each project
        for proj_idx, project in enumerate(sorted_projects):
            ps_id = project.responsible_id
            
            # Find best class and slot for this project
            best_class_id, best_slot, best_j1 = self._find_best_placement(
                ps_id, proj_idx, class_loads, workloads, projects_per_class, extra_projects
            )
            
            if best_j1 == -1:
                # Fallback: force assignment (should be rare)
                logger.warning(f"No conflict-free slot found for project {project.id}, using fallback")
                best_j1 = self._force_j1_selection(ps_id, best_class_id, best_slot, workloads)
            
            # Create assignment
            assignment = ProjectAssignment(
                project_id=project.id,
                class_id=best_class_id,
                order_in_class=best_slot,
                ps_id=ps_id,
                j1_id=best_j1,
                j2_id=-1  # Placeholder
            )
            
            # Mark instructors as busy
            self._mark_instructor_busy(ps_id, best_class_id, best_slot)
            self._mark_instructor_busy(best_j1, best_class_id, best_slot)
            
            # Update workloads
            workloads[ps_id] += 1
            workloads[best_j1] += 1
            
            # Update class loads
            class_loads[best_class_id] += 1
            
            state.assignments.append(assignment)
        
        # Reorder assignments within each class
        self._reorder_class_assignments(state)
        
        # Calculate cost
        state.cost = self.penalty_calculator.calculate_total_cost(state)
        
        # Verify no conflicts
        conflict_count = self.penalty_calculator.count_conflicts(state)
        if conflict_count > 0:
            logger.warning(f"Initial solution has {conflict_count} conflicts - applying repair")
            self._repair_conflicts(state)
        
        logger.info(f"Initial solution built: cost={state.cost:.2f}, conflicts={conflict_count}")
        
        return state
    
    def _sort_projects_by_priority(self) -> List[Project]:
        """Sort projects based on priority mode."""
        projects = list(self.projects)
        
        if self.config.priority_mode == PriorityMode.ARA_ONCE:
            # Interim projects first
            projects.sort(key=lambda p: (0 if p.type == "INTERIM" else 1, p.id))
        elif self.config.priority_mode == PriorityMode.BITIRME_ONCE:
            # Final projects first
            projects.sort(key=lambda p: (0 if p.type == "FINAL" else 1, p.id))
        else:
            # Random order for diversity
            random.shuffle(projects)
        
        return projects
    
    def _find_best_placement(
        self,
        ps_id: int,
        proj_idx: int,
        class_loads: Dict[int, int],
        workloads: Dict[int, int],
        projects_per_class: int,
        extra_projects: int
    ) -> Tuple[int, int, int]:
        """
        Find the best class_id, slot, and J1 for a project.
        
        Strategy:
        1. Prioritize classes with low load (for even distribution)
        2. Find a slot where both PS and J1 are available
        3. Select J1 with lowest workload
        """
        # Sort classes by current load
        sorted_classes = sorted(range(self.config.class_count), key=lambda c: class_loads.get(c, 0))
        
        for class_id in sorted_classes:
            current_load = class_loads.get(class_id, 0)
            target = projects_per_class + (1 if class_id < extra_projects else 0)
            
            if current_load >= target * 1.5:  # Allow some overflow
                continue
            
            # Find an available slot in this class
            slot = current_load  # Next available slot
            
            # Check if PS is available at this slot
            if not self._is_instructor_available(ps_id, class_id, slot):
                # Try other slots
                for alt_slot in range(max(0, slot - 2), slot + 10):
                    if self._is_instructor_available(ps_id, class_id, alt_slot):
                        slot = alt_slot
                        break
                else:
                    continue  # No available slot for PS in this class
            
            # Find available J1
            j1 = self._select_best_j1(ps_id, class_id, slot, workloads)
            
            if j1 != -1:
                return class_id, slot, j1
        
        # Fallback: use first class with any available slot
        for class_id in range(self.config.class_count):
            for slot in range(100):  # Check many slots
                if self._is_instructor_available(ps_id, class_id, slot):
                    j1 = self._select_best_j1(ps_id, class_id, slot, workloads)
                    if j1 != -1:
                        return class_id, slot, j1
        
        # Last resort: return first class, next slot, with J1 = -1 (will be forced)
        return 0, class_loads.get(0, 0), -1
    
    def _force_j1_selection(
        self,
        ps_id: int,
        class_id: int,
        slot: int,
        workloads: Dict[int, int]
    ) -> int:
        """
        Force J1 selection when no conflict-free option exists.
        Select the least loaded instructor (even if it creates a conflict).
        """
        candidates = [fid for fid in self.faculty_ids if fid != ps_id]
        if not candidates:
            # Extreme fallback - use PS itself (will be repaired)
            return ps_id
        
        # Sort by workload
        candidates.sort(key=lambda x: workloads.get(x, 0))
        return candidates[0]
    
    def _reorder_class_assignments(self, state: DPState) -> None:
        """Reorder assignments within each class to be consecutive."""
        for class_id in range(state.class_count):
            class_assignments = [a for a in state.assignments if a.class_id == class_id]
            class_assignments.sort(key=lambda a: a.order_in_class)
            
            for i, assignment in enumerate(class_assignments):
                assignment.order_in_class = i
    
    def _repair_conflicts(self, state: DPState) -> None:
        """
        Repair any remaining conflicts in the state.
        
        This is a backup mechanism - ideally, solutions should be conflict-free by design.
        """
        max_iterations = 100
        
        for iteration in range(max_iterations):
            conflicts = self._find_conflicts(state)
            if not conflicts:
                return
            
            for conflict in conflicts:
                self._resolve_conflict(state, conflict)
                break  # Re-check after each resolution
    
    def _find_conflicts(self, state: DPState) -> List[Dict]:
        """Find all timeslot conflicts in the state."""
        conflicts = []
        
        # Build instructor schedule
        instructor_schedule = defaultdict(lambda: defaultdict(list))
        
        for assignment in state.assignments:
            instructor_schedule[assignment.ps_id][assignment.order_in_class].append({
                'assignment': assignment,
                'class_id': assignment.class_id,
                'role': 'PS'
            })
            instructor_schedule[assignment.j1_id][assignment.order_in_class].append({
                'assignment': assignment,
                'class_id': assignment.class_id,
                'role': 'J1'
            })
        
        # Find conflicts
        for instructor_id, orders in instructor_schedule.items():
            for order, entries in orders.items():
                if len(entries) > 1:
                    classes = set(e['class_id'] for e in entries)
                    if len(classes) > 1:
                        conflicts.append({
                            'instructor_id': instructor_id,
                            'order': order,
                            'entries': entries,
                            'classes': classes
                        })
        
        return conflicts
    
    def _resolve_conflict(self, state: DPState, conflict: Dict) -> None:
        """Resolve a single timeslot conflict."""
        instructor_id = conflict['instructor_id']
        entries = conflict['entries']
        order = conflict['order']
        
        # Build a map of who is busy at this slot
        busy_at_slot = set()
        for a in state.assignments:
            if a.order_in_class == order:
                busy_at_slot.add(a.ps_id)
                busy_at_slot.add(a.j1_id)
        
        # Keep first entry, fix others
        for entry in entries[1:]:
            assignment = entry['assignment']
            role = entry['role']
            
            if role == 'J1':
                # Try to reassign J1 to someone who is NOT busy at this slot
                workloads = defaultdict(int)
                for a in state.assignments:
                    workloads[a.ps_id] += 1
                    workloads[a.j1_id] += 1
                
                # Find alternative J1 who is NOT busy at this slot
                available = []
                for fid in self.faculty_ids:
                    if fid == assignment.ps_id:
                        continue  # J1 != PS
                    if fid == instructor_id:
                        continue  # This is the conflicting instructor
                    if fid in busy_at_slot:
                        # Check if this is busy only for the current assignment
                        is_only_current = True
                        for a in state.assignments:
                            if a.order_in_class == order and a.project_id != assignment.project_id:
                                if a.ps_id == fid or a.j1_id == fid:
                                    is_only_current = False
                                    break
                        if not is_only_current:
                            continue  # Busy for another project at this slot
                    available.append(fid)
                
                if available:
                    # Select least loaded
                    available.sort(key=lambda x: workloads.get(x, 0))
                    assignment.j1_id = available[0]
                    logger.debug(f"Conflict resolved: reassigned J1 to {available[0]} for project {assignment.project_id}")
                    return
            
            # If J1 reassignment failed or role is PS, move project to different slot
            # Find a slot where the conflicting instructor is NOT busy
            class_loads = defaultdict(int)
            for a in state.assignments:
                class_loads[a.class_id] += 1
            
            for attempt_class in range(state.class_count):
                for attempt_slot in range(20):  # Try various slots
                    # Check if PS and J1 are available at this new slot
                    ps_busy = False
                    j1_busy = False
                    
                    for a in state.assignments:
                        if a.project_id == assignment.project_id:
                            continue  # Skip current assignment
                        if a.order_in_class == attempt_slot:
                            if a.ps_id == assignment.ps_id or a.j1_id == assignment.ps_id:
                                ps_busy = True
                            if a.ps_id == assignment.j1_id or a.j1_id == assignment.j1_id:
                                j1_busy = True
                    
                    if not ps_busy and not j1_busy:
                        # Found a conflict-free slot!
                        assignment.class_id = attempt_class
                        assignment.order_in_class = attempt_slot
                        logger.debug(f"Conflict resolved: moved project {assignment.project_id} to class {attempt_class}, slot {attempt_slot}")
                        self._reorder_class_assignments(state)
                        return
            
            # Last resort: move to least loaded class at next available slot
            min_class = min(range(state.class_count), key=lambda c: class_loads.get(c, 0))
            assignment.class_id = min_class
            assignment.order_in_class = class_loads.get(min_class, 0)
            logger.warning(f"Conflict fallback: moved project {assignment.project_id} to class {min_class}")
            
            # Reorder
            self._reorder_class_assignments(state)


# =============================================================================
# MAIN DYNAMIC PROGRAMMING ALGORITHM
# =============================================================================

class DynamicProgramming(OptimizationAlgorithm):
    """
    Dynamic Programming Algorithm for Multi-Criteria Optimization
    
    Features:
    - Proactive conflict prevention (conflict-free by design)
    - Multi-criteria objective function (H1-H7)
    - Configurable priority modes and penalty weights
    - Workload balancing with ±2 band
    - Single-phase operation
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.name = "Dynamic Programming Algorithm"
        self.description = "Multi-criteria optimization with proactive conflict prevention and workload balancing"
        
        # Initialize configuration
        self.config = DPConfig()
        if params:
            self._apply_params(params)
        
        # Data storage
        self.projects: List[Project] = []
        self.instructors: List[Instructor] = []
        self.classrooms: List[Dict] = []  # Store classroom data
        self.timeslots: List[Dict] = []   # Store timeslot data
        self.penalty_calculator: Optional[DPPenaltyCalculator] = None
        self.solution_builder: Optional[DPSolutionBuilder] = None
    
    def _apply_params(self, params: Dict[str, Any]) -> None:
        """Apply parameters to configuration."""
        if 'class_count' in params:
            self.config.class_count = params['class_count']
        
        if 'priority_mode' in params:
            mode = params['priority_mode']
            if isinstance(mode, str):
                self.config.priority_mode = PriorityMode[mode.upper()]
            elif isinstance(mode, PriorityMode):
                self.config.priority_mode = mode
        
        if 'time_penalty_mode' in params:
            mode = params['time_penalty_mode']
            if isinstance(mode, str):
                self.config.time_penalty_mode = TimePenaltyMode[mode.upper()]
            elif isinstance(mode, TimePenaltyMode):
                self.config.time_penalty_mode = mode
        
        if 'workload_constraint_mode' in params:
            mode = params['workload_constraint_mode']
            if isinstance(mode, str):
                self.config.workload_constraint_mode = WorkloadConstraintMode[mode.upper()]
            elif isinstance(mode, WorkloadConstraintMode):
                self.config.workload_constraint_mode = mode
        
        if 'workload_hard_limit' in params:
            self.config.workload_hard_limit = params['workload_hard_limit']
        
        # Penalty weights
        for key in ['weight_h1', 'weight_h2', 'weight_h3', 'weight_h4', 
                    'weight_h5', 'weight_h6', 'weight_h7']:
            if key in params:
                setattr(self.config, key, params[key])
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """Initialize the algorithm with input data."""
        # Parse projects
        self.projects = []
        for p in data.get('projects', []):
            if isinstance(p, dict):
                self.projects.append(Project(
                    id=p.get('id', 0),
                    name=p.get('name', p.get('title', '')),
                    type=p.get('type', p.get('project_type', 'INTERIM')).upper(),
                    responsible_id=p.get('responsible_instructor_id') or p.get('advisor_id') or p.get('instructor_id', 0)
                ))
            elif isinstance(p, Project):
                self.projects.append(p)
            elif hasattr(p, 'id'):
                self.projects.append(Project(
                    id=p.id,
                    name=getattr(p, 'name', getattr(p, 'title', '')),
                    type=getattr(p, 'type', 'INTERIM').upper(),
                    responsible_id=getattr(p, 'responsible_instructor_id', None) or getattr(p, 'advisor_id', 0)
                ))
        
        # Parse instructors
        self.instructors = []
        for i in data.get('instructors', []):
            if isinstance(i, dict):
                self.instructors.append(Instructor(
                    id=i.get('id', 0),
                    name=i.get('name', ''),
                    type=i.get('type', 'instructor')
                ))
            elif isinstance(i, Instructor):
                self.instructors.append(i)
            elif hasattr(i, 'id'):
                self.instructors.append(Instructor(
                    id=i.id,
                    name=getattr(i, 'name', ''),
                    type=getattr(i, 'type', 'instructor')
                ))
        
        # Store classrooms and timeslots for ID mapping
        self.classrooms = data.get('classrooms', [])
        self.timeslots = data.get('timeslots', [])
        
        # Update class count based on available classrooms (like SA)
        if self.classrooms:
            available_class_count = len(self.classrooms)
            if self.config.auto_class_count or self.config.class_count == 6:
                self.config.class_count = available_class_count
                logger.info(f"DP: Class count set to {available_class_count} based on available classrooms")
            elif self.config.class_count > available_class_count:
                logger.warning(f"DP: Requested class count ({self.config.class_count}) > available ({available_class_count}). Using available.")
                self.config.class_count = available_class_count
        elif self.config.auto_class_count:
            # Fallback auto class count based on projects
            num_projects = len(self.projects)
            if num_projects <= 6:
                self.config.class_count = 2
            elif num_projects <= 12:
                self.config.class_count = 3
            elif num_projects <= 24:
                self.config.class_count = 4
            elif num_projects <= 36:
                self.config.class_count = 5
            else:
                self.config.class_count = 6
        
        # Initialize penalty calculator and solution builder
        self.penalty_calculator = DPPenaltyCalculator(
            self.projects, self.instructors, self.config
        )
        self.solution_builder = DPSolutionBuilder(
            self.projects, self.instructors, self.config, self.penalty_calculator
        )
        
        logger.info(f"DP initialized: {len(self.projects)} projects, "
                   f"{len(self.instructors)} instructors, "
                   f"{self.config.class_count} classes, "
                   f"{len(self.classrooms)} classrooms, "
                   f"{len(self.timeslots)} timeslots")
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the Dynamic Programming optimization.
        
        Returns a dictionary with:
        - 'assignments': List of project assignments
        - 'schedule': Same as assignments (for compatibility)
        - 'solution': Same as assignments (for compatibility)
        - 'statistics': Statistics about the solution
        """
        start_time = time.time()
        logger.info("Dynamic Programming optimization starting...")
        
        # Initialize from data
        self.initialize(data)
        
        # Build initial solution
        best_state = self.solution_builder.build_initial_solution()
        
        # Improve solution using beam search / DP transitions
        best_state = self._improve_solution(best_state)
        
        # Final repair if needed
        self._final_repair(best_state)
        
        # Convert to output format
        assignments = self._convert_to_output_format(best_state)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Calculate statistics
        statistics = self._calculate_statistics(best_state)
        statistics['execution_time'] = execution_time
        
        result = {
            'assignments': assignments,
            'schedule': assignments,
            'solution': assignments,
            'schedules': assignments,  # For backward compatibility
            'statistics': statistics,
            'algorithm_info': {
                'name': self.name,
                'description': self.description,
                'class_count': self.config.class_count,
                'priority_mode': self.config.priority_mode.value,
                'final_cost': best_state.cost,
                'execution_time': execution_time
            }
        }
        
        logger.info(f"DP optimization complete: cost={best_state.cost:.2f}, "
                   f"time={execution_time:.2f}s")
        
        return result
    
    def _improve_solution(self, state: DPState) -> DPState:
        """
        Improve the solution using DP-style transitions.
        
        Tries local improvements:
        - J1 reassignment
        - Class moves
        - Order swaps
        """
        best_state = state.copy()
        best_cost = best_state.cost
        
        no_improve = 0
        max_no_improve = 500
        
        for iteration in range(self.config.max_iterations):
            # Generate neighbor
            neighbor = self._generate_neighbor(best_state)
            
            if neighbor is None:
                continue
            
            # Calculate cost
            neighbor.cost = self.penalty_calculator.calculate_total_cost(neighbor)
            
            # CRITICAL: Check for conflicts - reject if conflicts introduced
            neighbor_conflicts = self.penalty_calculator.count_conflicts(neighbor)
            current_conflicts = self.penalty_calculator.count_conflicts(best_state)
            
            # Only accept if: (no new conflicts AND better cost) OR (fewer conflicts)
            if neighbor_conflicts > current_conflicts:
                # Reject - this move introduced conflicts
                no_improve += 1
                continue
            
            # Check for improvement (prefer conflict-free solutions)
            accept = False
            if neighbor_conflicts < current_conflicts:
                # Always accept if it reduces conflicts
                accept = True
            elif neighbor.cost < best_cost:
                accept = True
            
            if accept:
                best_state = neighbor
                best_cost = neighbor.cost
                no_improve = 0
                
                if iteration % 100 == 0:
                    logger.debug(f"Iteration {iteration}: improved to cost={best_cost:.2f}, conflicts={neighbor_conflicts}")
            else:
                no_improve += 1
            
            # Early termination
            if no_improve >= max_no_improve:
                logger.info(f"Early termination at iteration {iteration}")
                break
        
        return best_state
    
    def _generate_neighbor(self, state: DPState) -> Optional[DPState]:
        """Generate a neighbor solution using random move."""
        neighbor = state.copy()
        
        if not neighbor.assignments:
            return None
        
        # Choose move type
        move_type = random.choice(['j1_reassign', 'class_move', 'order_swap'])
        
        if move_type == 'j1_reassign':
            return self._move_j1_reassign(neighbor)
        elif move_type == 'class_move':
            return self._move_class_move(neighbor)
        else:
            return self._move_order_swap(neighbor)
    
    def _move_j1_reassign(self, state: DPState) -> Optional[DPState]:
        """Reassign J1 for a random project."""
        if not state.assignments:
            return None
        
        # Pick random assignment
        assignment = random.choice(state.assignments)
        slot = assignment.order_in_class
        
        # Build a map of which instructors are busy at each slot
        # CRITICAL: slot is the same across ALL classes (same timeslot)
        busy_at_slot: Dict[int, Set[int]] = defaultdict(set)  # slot -> set of busy instructor_ids
        
        for a in state.assignments:
            busy_at_slot[a.order_in_class].add(a.ps_id)
            busy_at_slot[a.order_in_class].add(a.j1_id)
        
        # Find available J1s (not busy at this slot, not PS)
        faculty_ids = [i.id for i in self.instructors if i.type == "instructor"]
        available = []
        
        for fid in faculty_ids:
            if fid == assignment.ps_id:
                continue  # J1 != PS
            if fid == assignment.j1_id:
                continue  # Already assigned as J1
            if fid in busy_at_slot[slot]:
                # This instructor is already busy at this slot (same timeslot across any class)
                # But we need to check if they're busy for a DIFFERENT project
                # (they could be busy for this very project if they're the current J1/PS)
                # Find the assignments that make this instructor busy at this slot
                is_own_assignment = False
                for a in state.assignments:
                    if a.order_in_class == slot and (a.ps_id == fid or a.j1_id == fid):
                        if a.project_id == assignment.project_id:
                            # This is the current assignment - J1 can be changed
                            is_own_assignment = True
                        else:
                            # Busy for another project at the same slot - conflict!
                            is_own_assignment = False
                            break
                
                if not is_own_assignment:
                    continue  # This instructor is busy at this slot for another project
            
            available.append(fid)
        
        if not available:
            return None
        
        # Select best J1 (lowest workload)
        workloads = defaultdict(int)
        for a in state.assignments:
            workloads[a.ps_id] += 1
            workloads[a.j1_id] += 1
        
        available.sort(key=lambda x: workloads.get(x, 0))
        assignment.j1_id = available[0]
        
        return state
    
    def _move_class_move(self, state: DPState) -> Optional[DPState]:
        """
        Move a project to a different class.
        
        After moving, need to find new slot and potentially new J1 to avoid conflicts.
        """
        if not state.assignments:
            return None
        
        # Pick random assignment
        assignment = random.choice(state.assignments)
        old_class = assignment.class_id
        
        # Pick new class
        new_class = random.choice([c for c in range(state.class_count) if c != old_class])
        
        # Update assignment
        assignment.class_id = new_class
        
        # Reorder
        self._reorder_assignments(state)
        
        return state
    
    def _move_order_swap(self, state: DPState) -> Optional[DPState]:
        """Swap order of two projects in the same class."""
        if not state.assignments:
            return None
        
        # Pick random class
        class_id = random.randint(0, state.class_count - 1)
        class_assignments = [a for a in state.assignments if a.class_id == class_id]
        
        if len(class_assignments) < 2:
            return None
        
        # Pick two random assignments
        a1, a2 = random.sample(class_assignments, 2)
        
        # Swap orders
        a1.order_in_class, a2.order_in_class = a2.order_in_class, a1.order_in_class
        
        return state
    
    def _reorder_assignments(self, state: DPState) -> None:
        """Reorder assignments within each class to be consecutive."""
        for class_id in range(state.class_count):
            class_assignments = [a for a in state.assignments if a.class_id == class_id]
            class_assignments.sort(key=lambda a: a.order_in_class)
            
            for i, assignment in enumerate(class_assignments):
                assignment.order_in_class = i
    
    def _final_repair(self, state: DPState) -> None:
        """Final repair to ensure all constraints are satisfied."""
        # Repair conflicts (iterate until none remain)
        max_repair_iterations = 20
        for repair_iter in range(max_repair_iterations):
            conflict_count = self.penalty_calculator.count_conflicts(state)
            if conflict_count == 0:
                break
            
            logger.info(f"Final repair iteration {repair_iter + 1}: {conflict_count} conflicts detected")
            self.solution_builder._repair_conflicts(state)
        
        # Check if conflicts remain after all iterations
        final_conflicts = self.penalty_calculator.count_conflicts(state)
        if final_conflicts > 0:
            logger.error(f"CRITICAL: {final_conflicts} conflicts could not be resolved!")
        else:
            logger.info("All conflicts resolved successfully")
        
        # Ensure all classes are used
        used_classes = set(a.class_id for a in state.assignments)
        unused_classes = [c for c in range(state.class_count) if c not in used_classes]
        
        if unused_classes:
            logger.info(f"Final repair: {len(unused_classes)} unused classes")
            self._repair_unused_classes(state, unused_classes)
        
        # Recalculate cost
        state.cost = self.penalty_calculator.calculate_total_cost(state)
    
    def _repair_unused_classes(self, state: DPState, unused_classes: List[int]) -> None:
        """Move projects to unused classes to ensure all classes are used."""
        # Find class with most projects
        class_loads = defaultdict(int)
        for a in state.assignments:
            class_loads[a.class_id] += 1
        
        for unused_class in unused_classes:
            if not class_loads:
                break
            
            # Find most loaded class
            max_class = max(class_loads.keys(), key=lambda c: class_loads[c])
            
            if class_loads[max_class] <= 1:
                continue  # Can't move if only 1 project
            
            # Find assignment to move
            assignments_in_max = [a for a in state.assignments if a.class_id == max_class]
            if assignments_in_max:
                # Move last assignment
                assignment = assignments_in_max[-1]
                assignment.class_id = unused_class
                assignment.order_in_class = 0
                
                class_loads[max_class] -= 1
                class_loads[unused_class] = 1
        
        # Reorder
        self._reorder_assignments(state)
    
    def _convert_to_output_format(self, state: DPState) -> List[Dict[str, Any]]:
        """
        Convert DPState to output format expected by the application.
        
        CRITICAL: Maps class_id to actual classroom_id from database,
        and order_in_class to actual timeslot_id from database.
        """
        result = []
        
        for assignment in state.assignments:
            project = self.solution_builder.projects_dict.get(assignment.project_id)
            ps_instructor = next((i for i in self.instructors if i.id == assignment.ps_id), None)
            j1_instructor = next((i for i in self.instructors if i.id == assignment.j1_id), None)
            
            # Map class_id to actual classroom_id
            class_id = assignment.class_id
            classroom = None
            if class_id < len(self.classrooms):
                classroom = self.classrooms[class_id]
            
            # Map order_in_class to actual timeslot_id
            order = assignment.order_in_class
            timeslot = None
            if order < len(self.timeslots):
                timeslot = self.timeslots[order]
            
            # Get actual IDs (fall back to indices if not available)
            actual_classroom_id = classroom.get('id') if classroom else class_id
            actual_timeslot_id = timeslot.get('id') if timeslot else order
            classroom_name = classroom.get('name', f'D{105+class_id}') if classroom else f'D{105+class_id}'
            
            result.append({
                'project_id': assignment.project_id,
                'project_name': project.name if project else f"Project {assignment.project_id}",
                'project_type': project.type if project else "INTERIM",
                'class_id': class_id,
                'classroom_id': actual_classroom_id,
                'classroom_name': classroom_name,
                'order_in_class': order,
                'timeslot_id': actual_timeslot_id,
                'timeslot': timeslot if timeslot else {'id': order},
                'ps_id': assignment.ps_id,
                'j1_id': assignment.j1_id,
                'j2_id': assignment.j2_id,  # Placeholder (-1)
                'instructors': [assignment.ps_id, assignment.j1_id],
                'instructor_names': [
                    ps_instructor.name if ps_instructor else f"Instructor {assignment.ps_id}",
                    j1_instructor.name if j1_instructor else f"Instructor {assignment.j1_id}"
                ]
            })
        
        # Sort by class and order
        result.sort(key=lambda x: (x['class_id'], x['order_in_class']))
        
        return result
    
    def _calculate_statistics(self, state: DPState) -> Dict[str, Any]:
        """Calculate statistics for the solution."""
        # Workload distribution
        workloads = defaultdict(int)
        for a in state.assignments:
            workloads[a.ps_id] += 1
            workloads[a.j1_id] += 1
        
        workload_values = list(workloads.values()) if workloads else [0]
        
        # Class distribution
        class_counts = defaultdict(int)
        for a in state.assignments:
            class_counts[a.class_id] += 1
        
        # Conflict count
        conflict_count = self.penalty_calculator.count_conflicts(state)
        
        return {
            'total_projects': len(state.assignments),
            'class_count': state.class_count,
            'total_cost': state.cost,
            'conflict_count': conflict_count,
            'workload_min': min(workload_values),
            'workload_max': max(workload_values),
            'workload_avg': sum(workload_values) / len(workload_values) if workload_values else 0,
            'workload_std': float(np.std(workload_values)) if len(workload_values) > 1 else 0,
            'class_distribution': dict(class_counts),
            'used_classes': len(class_counts),
            'unused_classes': state.class_count - len(class_counts),
            'penalty_breakdown': {
                'h1_time': self.penalty_calculator.calculate_h1_time_penalty(state),
                'h2_workload': self.penalty_calculator.calculate_h2_workload_penalty(state),
                'h3_class_change': self.penalty_calculator.calculate_h3_class_change_penalty(state),
                'h4_class_load': self.penalty_calculator.calculate_h4_class_load_penalty(state),
                'h5_continuity': self.penalty_calculator.calculate_h5_continuity_penalty(state),
                'h6_conflict': self.penalty_calculator.calculate_h6_timeslot_conflict_penalty(state),
                'h7_unused': self.penalty_calculator.calculate_h7_unused_class_penalty(state)
            }
        }
    
    def evaluate_fitness(self, assignments: List[Dict[str, Any]]) -> float:
        """
        Evaluate the fitness of a given schedule.
        
        Args:
            assignments: List of schedule assignments
            
        Returns:
            float: Fitness score (higher is better, so we use negative cost)
        """
        # Convert to DPState
        state = DPState(class_count=self.config.class_count)
        
        for a in assignments:
            state.assignments.append(ProjectAssignment(
                project_id=a.get('project_id', 0),
                class_id=a.get('class_id', 0),
                order_in_class=a.get('order_in_class', 0),
                ps_id=a.get('ps_id', 0),
                j1_id=a.get('j1_id', 0),
                j2_id=a.get('j2_id', -1)
            ))
        
        # Calculate cost
        if self.penalty_calculator:
            cost = self.penalty_calculator.calculate_total_cost(state)
        else:
            cost = 0.0
        
        # Return negative cost as fitness (higher is better)
        return -cost


# Alias for backward compatibility with factory.py
DynamicProgrammingAlgorithm = DynamicProgramming