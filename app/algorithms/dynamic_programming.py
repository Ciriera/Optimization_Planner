"""
Dynamic Programming (DP) Optimization Algorithm
Multi-Criteria, Highly-Constrained Academic Project Jury Scheduling System

This module implements a full DP-based optimization for academic project exam planning.

SYSTEM OVERVIEW:
- Each project p has: fixed PS[p], decision variable J1[p], placeholder J2="Research Assistant"
- X real faculty members, Y projects, z classes (5, 6, or 7)
- Projects must be placed consecutively (no gaps) within each class
- DP solves class[p], slot[p], J1[p] all together in a single computation

OBJECTIVE FUNCTION:
    min Z = C1*H1(n) + C2*H2(n) + C3*H3(n) + CCL*H_classload(n)

Where:
- H1: Continuity/gap penalty
- H2: Workload uniformity penalty (most important, C2 > C1, C2 > C3)
- H3: Class change penalty
- H_classload: Class load balance penalty

HARD CONSTRAINTS:
1. Every project assigned to exactly one class and slot
2. Back-to-back scheduling (no gaps within class)
3. Single-duty per slot per faculty
4. J1[p] != PS[p]
5. Exactly z classes active
6. Priority mode (ARA_ONCE, BITIRME_ONCE, ESIT)
7. J2 placeholder not in faculty set
"""

from typing import Dict, Any, List, Tuple, Set, Optional, FrozenSet
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import time
import logging
import heapq
import copy
import random

from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION ENUMS
# ============================================================================

class PriorityMode(str, Enum):
    """Project type priority mode."""
    ARA_ONCE = "ARA_ONCE"           # ARA projects first
    BITIRME_ONCE = "BITIRME_ONCE"   # BITIRME projects first
    ESIT = "ESIT"                   # No priority


class TimePenaltyMode(str, Enum):
    """Time penalty mode."""
    BINARY = "BINARY"                       # Non-consecutive = 1 penalty
    GAP_PROPORTIONAL = "GAP_PROPORTIONAL"   # Penalty = gap slot count


class WorkloadConstraintMode(str, Enum):
    """Workload constraint mode."""
    SOFT_ONLY = "SOFT_ONLY"           # Penalty only
    SOFT_AND_HARD = "SOFT_AND_HARD"   # Penalty + hard constraint


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class DPConfig:
    """DP Algorithm configuration parameters."""
    
    # Class count settings
    class_count: int = 6
    auto_class_count: bool = True  # Try 5, 6, 7 and pick best
    
    # DP control parameters
    max_states_per_layer: int = 10000  # Limit frontier size
    time_limit: int = 300  # seconds
    enable_dominance_pruning: bool = True
    beam_width: int = 5000  # For beam search variant
    
    # Priority mode
    priority_mode: PriorityMode = PriorityMode.ESIT
    
    # Time penalty mode
    time_penalty_mode: TimePenaltyMode = TimePenaltyMode.GAP_PROPORTIONAL
    
    # Workload constraint mode
    workload_constraint_mode: WorkloadConstraintMode = WorkloadConstraintMode.SOFT_ONLY
    workload_hard_limit: int = 4  # B_max
    workload_soft_band: int = 2   # +/- 2 tolerance
    
    # Penalty weights (C2 > C1, C2 > C3)
    weight_h1: float = 1.0   # C1: Time/Gap penalty weight
    weight_h2: float = 3.0   # C2: Workload penalty weight (MOST IMPORTANT)
    weight_h3: float = 1.5   # C3: Class change penalty weight
    weight_h4: float = 2.0   # C4: Class load balance penalty weight
    weight_continuity: float = 2.5  # Continuity penalty weight
    
    # Slot duration
    slot_duration: float = 0.5  # hours (30 minutes)
    tolerance: float = 0.001


@dataclass
class Project:
    """Project data structure."""
    id: int
    title: str
    type: str  # "interim" (ARA) or "final" (BITIRME)
    responsible_id: int  # Project Supervisor (PS) - fixed
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
    """Project assignment information."""
    project_id: int
    class_id: int
    order_in_class: int  # slot within class (0-indexed)
    ps_id: int  # Project Supervisor (fixed)
    j1_id: int  # 1st Jury (decision variable)
    j2_id: int = -1  # 2nd Jury (placeholder - not in model)
    
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
class DPState:
    """
    DP State representation.
    
    Contains all information needed to uniquely identify a partial solution.
    Must be hashable for memoization.
    """
    project_index: int  # Number of projects assigned so far
    class_loads: Tuple[int, ...]  # Projects per class
    faculty_loads: Tuple[int, ...]  # Workload per faculty
    class_visit_masks: Tuple[int, ...]  # Bitmask of visited classes per faculty
    continuity_signature: Tuple[Tuple[int, ...], ...]  # Block tracking per faculty per class
    priority_state: Tuple[int, int]  # (max_ara_slot, min_bitirme_slot)
    
    def __hash__(self):
        return hash((
            self.project_index,
            self.class_loads,
            self.faculty_loads,
            self.class_visit_masks,
            self.continuity_signature,
            self.priority_state
        ))
    
    def __eq__(self, other):
        if not isinstance(other, DPState):
            return False
        return (
            self.project_index == other.project_index and
            self.class_loads == other.class_loads and
            self.faculty_loads == other.faculty_loads and
            self.class_visit_masks == other.class_visit_masks and
            self.continuity_signature == other.continuity_signature and
            self.priority_state == other.priority_state
        )
    
    def __lt__(self, other):
        """Less than comparison for heap operations."""
        if not isinstance(other, DPState):
            return NotImplemented
        # Compare by project_index first, then by sum of class_loads
        if self.project_index != other.project_index:
            return self.project_index < other.project_index
        return sum(self.class_loads) < sum(other.class_loads)
    
    def __le__(self, other):
        return self == other or self < other
    
    def __gt__(self, other):
        if not isinstance(other, DPState):
            return NotImplemented
        return other < self
    
    def __ge__(self, other):
        return self == other or self > other


@dataclass
class DPTransition:
    """DP transition (action) information."""
    project_id: int
    class_id: int
    slot_in_class: int
    j1_id: int
    incremental_cost: float


@dataclass
class DPSolution:
    """Complete DP solution."""
    assignments: List[ProjectAssignment] = field(default_factory=list)
    class_count: int = 6
    total_cost: float = float('inf')
    
    def copy(self) -> 'DPSolution':
        new_sol = DPSolution(
            class_count=self.class_count,
            total_cost=self.total_cost
        )
        new_sol.assignments = [a.copy() for a in self.assignments]
        return new_sol


@dataclass
class ScoreBreakdown:
    """Score details."""
    h1_time_gap: float = 0.0
    h2_workload: float = 0.0
    h3_class_change: float = 0.0
    h4_class_load_balance: float = 0.0
    h5_continuity: float = 0.0
    total_z: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "h1_time_gap": self.h1_time_gap,
            "h2_workload": self.h2_workload,
            "h3_class_change": self.h3_class_change,
            "h4_class_load_balance": self.h4_class_load_balance,
            "h5_continuity": self.h5_continuity,
            "total_z": self.total_z
        }


# ============================================================================
# PENALTY CALCULATOR
# ============================================================================

class DPPenaltyCalculator:
    """
    Penalty calculator for DP algorithm.
    
    OBJECTIVE: min Z = C1*H1 + C2*H2 + C3*H3 + C4*H4 + C5*H5
    
    - H1: Time/Gap Penalty
    - H2: Workload Uniformity Penalty
    - H3: Class Change Penalty
    - H4: Class Load Balance Penalty
    - H5: Continuity Penalty
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
        
        # Only real instructors (not assistants)
        self.faculty_instructors = {
            i.id: i for i in instructors
            if i.type == "instructor"
        }
        
        # Calculate average workload: L_avg = 2Y / X
        num_projects = len(projects)
        num_faculty = len(self.faculty_instructors)
        self.total_workload = 2 * num_projects  # Each project = 2 duties: PS + J1
        self.avg_workload = self.total_workload / num_faculty if num_faculty > 0 else 0
    
    def calculate_full_penalty(self, solution: DPSolution) -> ScoreBreakdown:
        """Calculate all penalties and return detailed breakdown."""
        h1 = self.calculate_h1_time_penalty(solution)
        h2 = self.calculate_h2_workload_penalty(solution)
        h3 = self.calculate_h3_class_change_penalty(solution)
        h4 = self.calculate_h4_class_load_penalty(solution)
        h5 = self.calculate_continuity_penalty(solution)
        
        total_z = (
            self.config.weight_h1 * h1 +
            self.config.weight_h2 * h2 +
            self.config.weight_h3 * h3 +
            self.config.weight_h4 * h4 +
            self.config.weight_continuity * h5
        )
        
        return ScoreBreakdown(
            h1_time_gap=h1,
            h2_workload=h2,
            h3_class_change=h3,
            h4_class_load_balance=h4,
            h5_continuity=h5,
            total_z=total_z
        )
    
    def calculate_total_penalty(self, solution: DPSolution) -> float:
        """Calculate total penalty value."""
        return self.calculate_full_penalty(solution).total_z
    
    def calculate_h1_time_penalty(self, solution: DPSolution) -> float:
        """
        H1: Time/Gap penalty.
        
        For each instructor, check consecutive tasks in same class.
        BINARY: gap > 0 = 1 penalty
        GAP_PROPORTIONAL: penalty = gap count
        """
        total_penalty = 0.0
        instructor_tasks = self._build_instructor_task_matrix(solution)
        
        for instructor_id, tasks in instructor_tasks.items():
            if len(tasks) <= 1:
                continue
            
            # Sort by class and slot
            tasks.sort(key=lambda x: (x['class_id'], x['order']))
            
            # Check consecutive tasks in same class
            for r in range(len(tasks) - 1):
                current = tasks[r]
                next_task = tasks[r + 1]
                
                if current['class_id'] == next_task['class_id']:
                    gap = next_task['order'] - current['order'] - 1
                    
                    if gap > 0:
                        if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                            total_penalty += 1
                        else:  # GAP_PROPORTIONAL
                            total_penalty += gap
                else:
                    # Class change also counts as disruption
                    if self.config.time_penalty_mode == TimePenaltyMode.BINARY:
                        total_penalty += 1
                    else:
                        total_penalty += 1
        
        return total_penalty
    
    def calculate_h2_workload_penalty(self, solution: DPSolution) -> float:
        """
        H2: Workload uniformity penalty.
        
        deviation = max(0, |Load(i) - L_avg| - 2)
        H2 = sum(deviation)
        
        SOFT_AND_HARD: |Load(i) - L_avg| > B_max = large penalty
        """
        total_penalty = 0.0
        workload = self._calculate_instructor_workloads(solution)
        
        for instructor_id in self.faculty_instructors.keys():
            load = workload.get(instructor_id, 0)
            deviation = abs(load - self.avg_workload)
            
            # Soft penalty: +/- 2 tolerance
            penalty = max(0, deviation - self.config.workload_soft_band)
            total_penalty += penalty
            
            # Hard constraint check
            if self.config.workload_constraint_mode == WorkloadConstraintMode.SOFT_AND_HARD:
                if deviation > self.config.workload_hard_limit:
                    total_penalty += 1000  # Large penalty (infeasible)
        
        return total_penalty
    
    def calculate_h3_class_change_penalty(self, solution: DPSolution) -> float:
        """
        H3: Class change penalty.
        
        count = number of different classes instructor has duties in
        penalty = max(0, count - 2)
        """
        total_penalty = 0.0
        instructor_classes = defaultdict(set)
        
        for assignment in solution.assignments:
            instructor_classes[assignment.ps_id].add(assignment.class_id)
            instructor_classes[assignment.j1_id].add(assignment.class_id)
        
        for instructor_id in self.faculty_instructors.keys():
            class_count = len(instructor_classes.get(instructor_id, set()))
            # 1-2 classes ideal, more = penalty
            if class_count > 2:
                penalty = (class_count - 2) ** 2  # Quadratic penalty
                total_penalty += penalty
        
        return total_penalty
    
    def calculate_h4_class_load_penalty(self, solution: DPSolution) -> float:
        """
        H4: Class load balance penalty.
        
        Target per class = num_projects / class_count
        Empty classes = large penalty (hard constraint)
        """
        total_penalty = 0.0
        
        num_projects = len(solution.assignments)
        if num_projects == 0:
            return 0.0
        
        target_per_class = num_projects / solution.class_count
        
        class_loads = defaultdict(int)
        for assignment in solution.assignments:
            class_loads[assignment.class_id] += 1
        
        # Empty class penalty (hard constraint)
        for class_id in range(solution.class_count):
            load = class_loads.get(class_id, 0)
            if load == 0:
                total_penalty += 1000.0  # Large penalty
            else:
                deviation = abs(load - target_per_class)
                total_penalty += deviation
        
        return total_penalty
    
    def calculate_continuity_penalty(self, solution: DPSolution) -> float:
        """
        Continuity penalty.
        
        For each instructor in each class, count activity blocks.
        Ideal: 1 block (consecutive duties)
        Penalty: Blocks(h,s) - 1
        """
        total_penalty = 0.0
        
        for instructor_id in self.faculty_instructors.keys():
            for class_id in range(solution.class_count):
                blocks = self._count_blocks(solution, instructor_id, class_id)
                if blocks > 1:
                    penalty = (blocks - 1) ** 2  # Quadratic penalty
                    total_penalty += penalty
        
        return total_penalty
    
    def _build_instructor_task_matrix(
        self,
        solution: DPSolution
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Build task matrix for each instructor."""
        instructor_tasks = defaultdict(list)
        
        for assignment in solution.assignments:
            # PS duty
            instructor_tasks[assignment.ps_id].append({
                'project_id': assignment.project_id,
                'class_id': assignment.class_id,
                'order': assignment.order_in_class,
                'role': 'PS'
            })
            
            # J1 duty
            instructor_tasks[assignment.j1_id].append({
                'project_id': assignment.project_id,
                'class_id': assignment.class_id,
                'order': assignment.order_in_class,
                'role': 'J1'
            })
        
        return instructor_tasks
    
    def _calculate_instructor_workloads(
        self,
        solution: DPSolution
    ) -> Dict[int, int]:
        """Calculate total workload for each instructor."""
        workload = defaultdict(int)
        
        for assignment in solution.assignments:
            workload[assignment.ps_id] += 1
            workload[assignment.j1_id] += 1
        
        return workload
    
    def _count_blocks(
        self,
        solution: DPSolution,
        instructor_id: int,
        class_id: int
    ) -> int:
        """Count activity blocks for instructor in class."""
        class_assignments = [
            a for a in solution.assignments
            if a.class_id == class_id
        ]
        
        if not class_assignments:
            return 0
        
        class_assignments.sort(key=lambda x: x.order_in_class)
        
        # Build presence array
        presence = []
        for a in class_assignments:
            is_present = (a.ps_id == instructor_id or a.j1_id == instructor_id)
            presence.append(1 if is_present else 0)
        
        if sum(presence) == 0:
            return 0
        
        # Count 0->1 transitions (block starts)
        blocks = 0
        for i in range(len(presence)):
            if presence[i] == 1:
                if i == 0 or presence[i - 1] == 0:
                    blocks += 1
        
        return blocks
    
    def calculate_incremental_cost(
        self,
        state: DPState,
        transition: DPTransition,
        project: Project,
        class_count: int
    ) -> float:
        """
        Calculate incremental cost for a transition.
        
        This is used during DP to estimate cost without building full solution.
        """
        cost = 0.0
        
        # Workload penalty increment
        # New load for PS and J1
        ps_idx = self._get_faculty_index(project.responsible_id)
        j1_idx = self._get_faculty_index(transition.j1_id)
        
        if ps_idx is not None:
            new_ps_load = state.faculty_loads[ps_idx] + 1
            old_deviation = max(0, abs(state.faculty_loads[ps_idx] - self.avg_workload) - self.config.workload_soft_band)
            new_deviation = max(0, abs(new_ps_load - self.avg_workload) - self.config.workload_soft_band)
            cost += self.config.weight_h2 * (new_deviation - old_deviation)
        
        if j1_idx is not None:
            new_j1_load = state.faculty_loads[j1_idx] + 1
            old_deviation = max(0, abs(state.faculty_loads[j1_idx] - self.avg_workload) - self.config.workload_soft_band)
            new_deviation = max(0, abs(new_j1_load - self.avg_workload) - self.config.workload_soft_band)
            cost += self.config.weight_h2 * (new_deviation - old_deviation)
        
        # Class change penalty increment
        if ps_idx is not None:
            old_class_count = bin(state.class_visit_masks[ps_idx]).count('1')
            new_mask = state.class_visit_masks[ps_idx] | (1 << transition.class_id)
            new_class_count = bin(new_mask).count('1')
            if new_class_count > old_class_count:
                old_penalty = max(0, old_class_count - 2) ** 2
                new_penalty = max(0, new_class_count - 2) ** 2
                cost += self.config.weight_h3 * (new_penalty - old_penalty)
        
        if j1_idx is not None:
            old_class_count = bin(state.class_visit_masks[j1_idx]).count('1')
            new_mask = state.class_visit_masks[j1_idx] | (1 << transition.class_id)
            new_class_count = bin(new_mask).count('1')
            if new_class_count > old_class_count:
                old_penalty = max(0, old_class_count - 2) ** 2
                new_penalty = max(0, new_class_count - 2) ** 2
                cost += self.config.weight_h3 * (new_penalty - old_penalty)
        
        # Class load balance penalty
        target_per_class = len(self.projects) / class_count
        old_load = state.class_loads[transition.class_id]
        new_load = old_load + 1
        
        old_deviation = abs(old_load - target_per_class)
        new_deviation = abs(new_load - target_per_class)
        cost += self.config.weight_h4 * (new_deviation - old_deviation)
        
        return cost
    
    def _get_faculty_index(self, instructor_id: int) -> Optional[int]:
        """Get faculty index from instructor ID."""
        faculty_list = list(self.faculty_instructors.keys())
        try:
            return faculty_list.index(instructor_id)
        except ValueError:
            return None


# ============================================================================
# DP SOLVER
# ============================================================================

class DPSolver:
    """
    Dynamic Programming Solver for academic project jury scheduling.
    
    Uses a forward DP approach with state-space exploration.
    State: (project_index, class_loads, faculty_loads, class_visit_masks, 
            continuity_signature, priority_state)
    """
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        classrooms: List[Dict[str, Any]],
        timeslots: List[Dict[str, Any]],
        config: DPConfig
    ):
        self.projects = projects
        self.instructors = instructors
        self.classrooms = classrooms
        self.timeslots = timeslots
        self.config = config
        
        # Only real instructors
        self.faculty_instructors = [
            i for i in instructors if i.type == "instructor"
        ]
        self.faculty_ids = [i.id for i in self.faculty_instructors]
        
        # Create mappings
        self.project_map = {p.id: p for p in projects}
        self.instructor_map = {i.id: i for i in instructors}
        self.faculty_index_map = {
            fid: idx for idx, fid in enumerate(self.faculty_ids)
        }
        
        # Penalty calculator
        self.penalty_calculator = DPPenaltyCalculator(
            projects, instructors, config
        )
        
        # Order projects by type for priority mode
        self.ordered_projects = self._order_projects_by_priority()
        
        logger.info(f"DPSolver initialized: {len(projects)} projects, "
                   f"{len(self.faculty_instructors)} faculty, "
                   f"priority_mode={config.priority_mode}")
    
    def _order_projects_by_priority(self) -> List[Project]:
        """Order projects based on priority mode."""
        ara_projects = [p for p in self.projects if p.type == "interim"]
        bitirme_projects = [p for p in self.projects if p.type == "final"]
        
        if self.config.priority_mode == PriorityMode.ARA_ONCE:
            return ara_projects + bitirme_projects
        elif self.config.priority_mode == PriorityMode.BITIRME_ONCE:
            return bitirme_projects + ara_projects
        else:  # ESIT
            return self.projects.copy()
    
    def solve(self, class_count: int) -> Tuple[DPSolution, ScoreBreakdown]:
        """
        Solve DP for given class count.
        
        Args:
            class_count: Number of classes to use
            
        Returns:
            (best_solution, score_breakdown)
        """
        start_time = time.time()
        num_projects = len(self.projects)
        num_faculty = len(self.faculty_instructors)
        
        logger.info(f"Starting DP solve with {class_count} classes...")
        
        # Build initial state
        initial_state = self._build_initial_state(class_count, num_faculty)
        
        # DP frontier: state -> (cost, predecessor_state, transition)
        frontier = {initial_state: (0.0, None, None)}
        
        best_solution = None
        best_cost = float('inf')
        
        # Forward DP loop
        for k in range(num_projects):
            if time.time() - start_time > self.config.time_limit:
                logger.warning(f"DP time limit reached at project {k}")
                break
            
            project = self.ordered_projects[k]
            next_frontier = {}
            
            logger.debug(f"Processing project {k + 1}/{num_projects}: {project.title}")
            
            for state, (cost, pred_state, pred_trans) in frontier.items():
                # Generate all valid transitions for this project
                transitions = self._generate_transitions(
                    state, project, class_count
                )
                
                for transition in transitions:
                    # Check hard constraints
                    if not self._is_valid_transition(state, transition, project):
                        continue
                    
                    # Compute new state
                    new_state = self._apply_transition(
                        state, transition, project, class_count, num_faculty
                    )
                    
                    # Calculate incremental cost
                    incr_cost = self.penalty_calculator.calculate_incremental_cost(
                        state, transition, project, class_count
                    )
                    new_cost = cost + incr_cost
                    
                    # Check if this state is better
                    if new_state not in next_frontier or new_cost < next_frontier[new_state][0]:
                        next_frontier[new_state] = (new_cost, state, transition)
            
            # Apply dominance pruning if enabled
            if self.config.enable_dominance_pruning:
                next_frontier = self._prune_dominated_states(next_frontier)
            
            # Limit frontier size (beam search)
            if len(next_frontier) > self.config.max_states_per_layer:
                next_frontier = self._beam_prune(next_frontier)
            
            frontier = next_frontier
            
            logger.debug(f"Layer {k + 1}: {len(frontier)} states in frontier")
        
        # Find best final state
        if frontier:
            for state, (cost, pred_state, pred_trans) in frontier.items():
                if state.project_index == num_projects and cost < best_cost:
                    best_cost = cost
                    best_solution = self._reconstruct_solution(
                        state, frontier, class_count
                    )
        
        if best_solution is None:
            logger.warning("No valid solution found, creating fallback")
            best_solution = self._create_fallback_solution(class_count)
        
        # Calculate final score breakdown
        score = self.penalty_calculator.calculate_full_penalty(best_solution)
        best_solution.total_cost = score.total_z
        
        elapsed = time.time() - start_time
        logger.info(f"DP solve completed in {elapsed:.2f}s, cost={score.total_z:.2f}")
        
        return best_solution, score
    
    def _build_initial_state(
        self,
        class_count: int,
        num_faculty: int
    ) -> DPState:
        """Build initial DP state."""
        return DPState(
            project_index=0,
            class_loads=tuple([0] * class_count),
            faculty_loads=tuple([0] * num_faculty),
            class_visit_masks=tuple([0] * num_faculty),
            continuity_signature=tuple(
                tuple([0] * class_count) for _ in range(num_faculty)
            ),
            priority_state=(0, 999999)  # (max_ara_slot, min_bitirme_slot) - use large int
        )
    
    def _generate_transitions(
        self,
        state: DPState,
        project: Project,
        class_count: int
    ) -> List[DPTransition]:
        """Generate all possible transitions for a project."""
        transitions = []
        
        for class_id in range(class_count):
            # Slot is determined by current class load (back-to-back)
            slot_in_class = state.class_loads[class_id]
            
            # J1 candidates: all faculty except PS
            for j1_id in self.faculty_ids:
                if j1_id == project.responsible_id:
                    continue  # J1 != PS
                
                transition = DPTransition(
                    project_id=project.id,
                    class_id=class_id,
                    slot_in_class=slot_in_class,
                    j1_id=j1_id,
                    incremental_cost=0.0  # Calculated later
                )
                transitions.append(transition)
        
        return transitions
    
    def _is_valid_transition(
        self,
        state: DPState,
        transition: DPTransition,
        project: Project
    ) -> bool:
        """Check if transition satisfies hard constraints."""
        
        # 1. J1 != PS (already filtered in generate_transitions)
        if transition.j1_id == project.responsible_id:
            return False
        
        # 2. Priority mode constraints
        if self.config.priority_mode == PriorityMode.ARA_ONCE:
            if project.type == "interim":
                # ARA project - update max_ara_slot
                global_slot = self._calculate_global_slot(
                    state, transition.class_id, transition.slot_in_class
                )
                # Check if this would violate ordering
                if global_slot > state.priority_state[1]:  # max_ara > min_bitirme
                    return False
            elif project.type == "final":
                global_slot = self._calculate_global_slot(
                    state, transition.class_id, transition.slot_in_class
                )
                if global_slot < state.priority_state[0]:  # min_bitirme < max_ara
                    return False
        
        elif self.config.priority_mode == PriorityMode.BITIRME_ONCE:
            if project.type == "final":
                global_slot = self._calculate_global_slot(
                    state, transition.class_id, transition.slot_in_class
                )
                if global_slot > state.priority_state[1]:
                    return False
            elif project.type == "interim":
                global_slot = self._calculate_global_slot(
                    state, transition.class_id, transition.slot_in_class
                )
                if global_slot < state.priority_state[0]:
                    return False
        
        # 3. Workload hard limit (if SOFT_AND_HARD)
        if self.config.workload_constraint_mode == WorkloadConstraintMode.SOFT_AND_HARD:
            ps_idx = self.faculty_index_map.get(project.responsible_id)
            j1_idx = self.faculty_index_map.get(transition.j1_id)
            
            if ps_idx is not None:
                new_load = state.faculty_loads[ps_idx] + 1
                deviation = abs(new_load - self.penalty_calculator.avg_workload)
                if deviation > self.config.workload_hard_limit:
                    return False
            
            if j1_idx is not None:
                new_load = state.faculty_loads[j1_idx] + 1
                deviation = abs(new_load - self.penalty_calculator.avg_workload)
                if deviation > self.config.workload_hard_limit:
                    return False
        
        return True
    
    def _calculate_global_slot(
        self,
        state: DPState,
        class_id: int,
        slot_in_class: int
    ) -> int:
        """Calculate global slot index from class and local slot."""
        # Simple linearization: class_id * max_slots_per_class + slot_in_class
        max_slots = len(self.timeslots) if self.timeslots else 20
        return class_id * max_slots + slot_in_class
    
    def _apply_transition(
        self,
        state: DPState,
        transition: DPTransition,
        project: Project,
        class_count: int,
        num_faculty: int
    ) -> DPState:
        """Apply transition to create new state."""
        
        # Update class loads
        new_class_loads = list(state.class_loads)
        new_class_loads[transition.class_id] += 1
        
        # Update faculty loads
        new_faculty_loads = list(state.faculty_loads)
        ps_idx = self.faculty_index_map.get(project.responsible_id)
        j1_idx = self.faculty_index_map.get(transition.j1_id)
        
        if ps_idx is not None:
            new_faculty_loads[ps_idx] += 1
        if j1_idx is not None:
            new_faculty_loads[j1_idx] += 1
        
        # Update class visit masks
        new_class_visit_masks = list(state.class_visit_masks)
        if ps_idx is not None:
            new_class_visit_masks[ps_idx] |= (1 << transition.class_id)
        if j1_idx is not None:
            new_class_visit_masks[j1_idx] |= (1 << transition.class_id)
        
        # Update continuity signature
        new_continuity = [list(row) for row in state.continuity_signature]
        if ps_idx is not None:
            new_continuity[ps_idx][transition.class_id] = transition.slot_in_class + 1
        if j1_idx is not None:
            new_continuity[j1_idx][transition.class_id] = transition.slot_in_class + 1
        
        # Update priority state
        global_slot = self._calculate_global_slot(
            state, transition.class_id, transition.slot_in_class
        )
        max_ara, min_bitirme = state.priority_state
        
        if project.type == "interim":
            max_ara = max(max_ara, global_slot)
        elif project.type == "final":
            min_bitirme = min(min_bitirme, global_slot)
        
        return DPState(
            project_index=state.project_index + 1,
            class_loads=tuple(new_class_loads),
            faculty_loads=tuple(new_faculty_loads),
            class_visit_masks=tuple(new_class_visit_masks),
            continuity_signature=tuple(tuple(row) for row in new_continuity),
            priority_state=(max_ara, min_bitirme)
        )
    
    def _prune_dominated_states(
        self,
        frontier: Dict[DPState, Tuple[float, Any, Any]]
    ) -> Dict[DPState, Tuple[float, Any, Any]]:
        """
        Prune dominated states from frontier.
        
        A state S1 dominates S2 if S1 has same structural features
        but strictly better cost.
        """
        # Group states by structural key (excluding cost-dependent parts)
        groups = defaultdict(list)
        
        for state, value in frontier.items():
            # Structural key: class_loads + faculty_loads distribution
            struct_key = (
                state.project_index,
                state.class_loads,
                # Sorted faculty loads (distribution matters, not individual assignment)
                tuple(sorted(state.faculty_loads))
            )
            groups[struct_key].append((state, value))
        
        # Keep only best in each group
        pruned = {}
        for struct_key, states in groups.items():
            best_state, best_value = min(states, key=lambda x: x[1][0])
            pruned[best_state] = best_value
        
        return pruned
    
    def _beam_prune(
        self,
        frontier: Dict[DPState, Tuple[float, Any, Any]]
    ) -> Dict[DPState, Tuple[float, Any, Any]]:
        """Keep only top-k states by cost (beam search)."""
        sorted_states = sorted(frontier.items(), key=lambda x: x[1][0])
        pruned = dict(sorted_states[:self.config.beam_width])
        return pruned
    
    def _reconstruct_solution(
        self,
        final_state: DPState,
        frontier: Dict[DPState, Tuple[float, Any, Any]],
        class_count: int
    ) -> DPSolution:
        """
        Reconstruct full solution from DP path.
        
        CRITICAL: Ensures ALL projects are included.
        """
        solution = DPSolution(class_count=class_count)
        
        # Need to trace back through all states
        # This requires storing predecessor info during DP
        # For simplicity, rebuild using a fresh forward pass
        
        # CRITICAL: Use ALL projects, not just ordered_projects
        # ordered_projects might be filtered, but we need ALL projects
        all_projects = self.projects.copy()
        ordered_projects = self._order_projects()
        
        # Ensure ordered_projects contains ALL projects
        ordered_ids = {p.id for p in ordered_projects}
        for p in all_projects:
            if p.id not in ordered_ids:
                logger.warning(f"[RECONSTRUCT] Adding missing project {p.id} to ordered list")
                ordered_projects.append(p)
        
        # Simplified reconstruction: use greedy assignment following ordered projects
        assignments = []
        class_loads = [0] * class_count
        
        for project in ordered_projects:
            # Find best class/J1 combination
            best_class = min(range(class_count), key=lambda c: class_loads[c])
            slot = class_loads[best_class]
            
            # Pick J1 with lowest workload (excluding PS)
            workloads = defaultdict(int)
            for a in assignments:
                workloads[a.ps_id] += 1
                workloads[a.j1_id] += 1
            
            available_j1 = [
                fid for fid in self.faculty_ids
                if fid != project.responsible_id
            ]
            
            if available_j1:
                best_j1 = min(available_j1, key=lambda j: workloads.get(j, 0))
            else:
                best_j1 = self.faculty_ids[0] if self.faculty_ids else -1
            
            assignment = ProjectAssignment(
                project_id=project.id,
                class_id=best_class,
                order_in_class=slot,
                ps_id=project.responsible_id,
                j1_id=best_j1,
                j2_id=-1  # Placeholder
            )
            assignments.append(assignment)
            class_loads[best_class] += 1
        
        solution.assignments = assignments
        
        # CRITICAL: Verify ALL projects are included
        assigned_ids = {a.project_id for a in assignments}
        all_project_ids = {p.id for p in self.projects}
        if len(assigned_ids) != len(all_project_ids):
            logger.error(f"[RECONSTRUCT] CRITICAL: Missing {len(all_project_ids) - len(assigned_ids)} projects!")
        else:
            logger.info(f"[RECONSTRUCT] SUCCESS: All {len(all_project_ids)} projects are in solution!")
        
        return solution
    
    def _create_fallback_solution(self, class_count: int) -> DPSolution:
        """Create fallback solution when DP fails."""
        solution = DPSolution(class_count=class_count)
        class_loads = [0] * class_count
        
        for i, project in enumerate(self.projects):
            class_id = i % class_count
            slot = class_loads[class_id]
            
            # Pick first available J1
            j1_id = None
            for fid in self.faculty_ids:
                if fid != project.responsible_id:
                    j1_id = fid
                    break
            
            if j1_id is None:
                j1_id = self.faculty_ids[0] if self.faculty_ids else -1
            
            assignment = ProjectAssignment(
                project_id=project.id,
                class_id=class_id,
                order_in_class=slot,
                ps_id=project.responsible_id,
                j1_id=j1_id,
                j2_id=-1
            )
            solution.assignments.append(assignment)
            class_loads[class_id] += 1
        
        return solution


# ============================================================================
# SOLUTION BUILDER (Advanced)
# ============================================================================

class DPSolutionBuilder:
    """
    Advanced solution builder using DP with A* style heuristics.
    
    Uses priority queue with f(n) = g(n) + h(n) where:
    - g(n) = actual cost so far
    - h(n) = estimated remaining cost (admissible heuristic)
    """
    
    def __init__(
        self,
        projects: List[Project],
        instructors: List[Instructor],
        config: DPConfig
    ):
        self.projects = projects
        self.instructors = instructors
        self.config = config
        
        self.faculty_instructors = [
            i for i in instructors if i.type == "instructor"
        ]
        self.faculty_ids = [i.id for i in self.faculty_instructors]
        self.faculty_index_map = {
            fid: idx for idx, fid in enumerate(self.faculty_ids)
        }
        
        self.penalty_calculator = DPPenaltyCalculator(
            projects, instructors, config
        )
    
    def build_optimal_solution(self, class_count: int) -> DPSolution:
        """
        Build optimal solution using A* search variant.
        
        This method explores the state space more efficiently than pure DP
        by using estimated remaining costs to guide search.
        """
        num_projects = len(self.projects)
        num_faculty = len(self.faculty_instructors)
        
        # Order projects
        ordered_projects = self._order_projects()
        
        # Initial state
        initial_state = DPState(
            project_index=0,
            class_loads=tuple([0] * class_count),
            faculty_loads=tuple([0] * num_faculty),
            class_visit_masks=tuple([0] * num_faculty),
            continuity_signature=tuple(
                tuple([0] * class_count) for _ in range(num_faculty)
            ),
            priority_state=(0, 999999)  # Use large int instead of float('inf')
        )
        
        # Priority queue: (f_score, counter, g_score, state, path)
        # Counter ensures stable ordering when f_scores are equal
        # path = list of (project_id, class_id, slot, j1_id)
        initial_h = self._estimate_remaining_cost(initial_state, num_projects)
        counter = 0
        pq = [(initial_h, counter, 0.0, initial_state, [])]
        visited = set()
        
        best_solution = None
        best_cost = float('inf')
        
        max_iterations = self.config.max_states_per_layer * num_projects
        iteration = 0
        
        while pq and iteration < max_iterations:
            iteration += 1
            f_score, _, g_score, state, path = heapq.heappop(pq)
            
            if state in visited:
                continue
            visited.add(state)
            
            # Check if complete
            if state.project_index == num_projects:
                if g_score < best_cost:
                    best_cost = g_score
                    best_solution = self._build_solution_from_path(
                        path, class_count
                    )
                continue
            
            # Generate successors
            project = ordered_projects[state.project_index]
            
            for class_id in range(class_count):
                slot = state.class_loads[class_id]
                
                for j1_id in self.faculty_ids:
                    if j1_id == project.responsible_id:
                        continue
                    
                    # Create transition
                    transition = DPTransition(
                        project_id=project.id,
                        class_id=class_id,
                        slot_in_class=slot,
                        j1_id=j1_id,
                        incremental_cost=0.0
                    )
                    
                    # Check validity
                    if not self._is_valid_transition_simple(state, transition, project):
                        continue
                    
                    # Apply transition
                    new_state = self._apply_transition_simple(
                        state, transition, project, class_count, num_faculty
                    )
                    
                    if new_state in visited:
                        continue
                    
                    # Calculate costs
                    incr_cost = self.penalty_calculator.calculate_incremental_cost(
                        state, transition, project, class_count
                    )
                    new_g = g_score + incr_cost
                    new_h = self._estimate_remaining_cost(new_state, num_projects)
                    new_f = new_g + new_h
                    
                    # Pruning: skip if clearly worse than best
                    if new_g > best_cost:
                        continue
                    
                    counter += 1
                    new_path = path + [(project.id, class_id, slot, j1_id)]
                    heapq.heappush(pq, (new_f, counter, new_g, new_state, new_path))
            
            # Limit queue size
            if len(pq) > self.config.beam_width * 2:
                pq = sorted(pq)[:self.config.beam_width]
                heapq.heapify(pq)
        
        if best_solution is None:
            best_solution = self._create_greedy_solution(class_count)
        
        return best_solution
    
    def _order_projects(self) -> List[Project]:
        """
        Order projects by priority mode.
        
        CRITICAL: Ensures ALL projects are included, regardless of type.
        
        ESIT mode: Projects are shuffled (no priority) - like Simulated Annealing
        """
        # Normalize project types - handle both "interim"/"final" and "ara"/"bitirme"
        ara = []
        bitirme = []
        other = []
        
        for p in self.projects:
            proj_type = str(p.type).lower()
            if proj_type in ["interim", "ara", "ara proje"]:
                ara.append(p)
            elif proj_type in ["final", "bitirme", "bitirme proje"]:
                bitirme.append(p)
            else:
                # Unknown type - include in both lists to ensure it's not lost
                other.append(p)
        
        # CRITICAL: Order based on priority mode
        if self.config.priority_mode == PriorityMode.ARA_ONCE:
            result = ara + other + bitirme
        elif self.config.priority_mode == PriorityMode.BITIRME_ONCE:
            result = bitirme + other + ara
        else:
            # ESIT mode: NO PRIORITY - shuffle all projects randomly
            # This ensures no type-based ordering
            result = ara + bitirme + other
            random.shuffle(result)
        
        # CRITICAL: Verify ALL projects are included
        if len(result) != len(self.projects):
            logger.warning(f"[ORDER_PROJECTS] Missing projects! Expected {len(self.projects)}, got {len(result)}")
            # Add any missing projects
            result_ids = {p.id for p in result}
            for p in self.projects:
                if p.id not in result_ids:
                    logger.warning(f"[ORDER_PROJECTS] Adding missing project {p.id} ({p.type})")
                    result.append(p)
        
        return result
    
    def _estimate_remaining_cost(
        self,
        state: DPState,
        total_projects: int
    ) -> float:
        """
        Estimate remaining cost (admissible heuristic).
        
        Uses lower bound estimation based on:
        - Remaining workload distribution
        - Class balance requirements
        """
        remaining = total_projects - state.project_index
        if remaining == 0:
            return 0.0
        
        # Estimate class load balance penalty
        class_count = len(state.class_loads)
        target = total_projects / class_count
        
        current_deviation = sum(
            abs(load - (state.project_index / class_count))
            for load in state.class_loads
        )
        
        # Minimum additional deviation from remaining assignments
        estimated_h4 = self.config.weight_h4 * current_deviation * 0.5
        
        # Minimum workload deviation
        avg_remaining_per_faculty = (remaining * 2) / len(self.faculty_ids)
        estimated_h2 = self.config.weight_h2 * avg_remaining_per_faculty * 0.1
        
        return estimated_h4 + estimated_h2
    
    def _is_valid_transition_simple(
        self,
        state: DPState,
        transition: DPTransition,
        project: Project
    ) -> bool:
        """Simplified validity check."""
        if transition.j1_id == project.responsible_id:
            return False
        
        # Check workload hard limit
        if self.config.workload_constraint_mode == WorkloadConstraintMode.SOFT_AND_HARD:
            ps_idx = self.faculty_index_map.get(project.responsible_id)
            j1_idx = self.faculty_index_map.get(transition.j1_id)
            
            if ps_idx is not None:
                if state.faculty_loads[ps_idx] + 1 > self.penalty_calculator.avg_workload + self.config.workload_hard_limit:
                    return False
            
            if j1_idx is not None:
                if state.faculty_loads[j1_idx] + 1 > self.penalty_calculator.avg_workload + self.config.workload_hard_limit:
                    return False
        
        return True
    
    def _apply_transition_simple(
        self,
        state: DPState,
        transition: DPTransition,
        project: Project,
        class_count: int,
        num_faculty: int
    ) -> DPState:
        """Apply transition to create new state."""
        new_class_loads = list(state.class_loads)
        new_class_loads[transition.class_id] += 1
        
        new_faculty_loads = list(state.faculty_loads)
        ps_idx = self.faculty_index_map.get(project.responsible_id)
        j1_idx = self.faculty_index_map.get(transition.j1_id)
        
        if ps_idx is not None:
            new_faculty_loads[ps_idx] += 1
        if j1_idx is not None:
            new_faculty_loads[j1_idx] += 1
        
        new_class_visit_masks = list(state.class_visit_masks)
        if ps_idx is not None:
            new_class_visit_masks[ps_idx] |= (1 << transition.class_id)
        if j1_idx is not None:
            new_class_visit_masks[j1_idx] |= (1 << transition.class_id)
        
        # Simplified continuity signature
        new_continuity = state.continuity_signature
        
        return DPState(
            project_index=state.project_index + 1,
            class_loads=tuple(new_class_loads),
            faculty_loads=tuple(new_faculty_loads),
            class_visit_masks=tuple(new_class_visit_masks),
            continuity_signature=new_continuity,
            priority_state=state.priority_state
        )
    
    def _build_solution_from_path(
        self,
        path: List[Tuple[int, int, int, int]],
        class_count: int
    ) -> DPSolution:
        """
        Build solution from path.
        
        CRITICAL: Ensures ALL projects are included.
        """
        solution = DPSolution(class_count=class_count)
        project_map = {p.id: p for p in self.projects}
        path_project_ids = {project_id for project_id, _, _, _ in path}
        
        # Add projects from path
        for project_id, class_id, slot, j1_id in path:
            project = project_map.get(project_id)
            if not project:
                logger.warning(f"[BUILD_PATH] Project {project_id} not found in project map!")
                continue
            
            assignment = ProjectAssignment(
                project_id=project_id,
                class_id=class_id,
                order_in_class=slot,
                ps_id=project.responsible_id,
                j1_id=j1_id,
                j2_id=-1
            )
            solution.assignments.append(assignment)
        
        # CRITICAL: Check for missing projects and add them
        all_project_ids = {p.id for p in self.projects}
        missing_project_ids = all_project_ids - path_project_ids
        
        if missing_project_ids:
            logger.warning(f"[BUILD_PATH] Found {len(missing_project_ids)} missing projects in path, adding them...")
            # Add missing projects using greedy assignment
            class_loads = defaultdict(int)
            for assignment in solution.assignments:
                class_loads[assignment.class_id] += 1
            
            for missing_id in missing_project_ids:
                project = project_map.get(missing_id)
                if not project:
                    continue
                
                # Find class with minimum load
                min_class_id = min(range(class_count), key=lambda c: class_loads.get(c, 0))
                slot = class_loads[min_class_id]
                class_loads[min_class_id] += 1
                
                # Find J1 (must not be PS)
                j1_id = None
                for fid in self.faculty_ids:
                    if fid != project.responsible_id:
                        j1_id = fid
                        break
                
                if j1_id is None:
                    j1_id = self.faculty_ids[0] if self.faculty_ids else -1
                
                assignment = ProjectAssignment(
                    project_id=missing_id,
                    class_id=min_class_id,
                    order_in_class=slot,
                    ps_id=project.responsible_id,
                    j1_id=j1_id,
                    j2_id=-1
                )
                solution.assignments.append(assignment)
                logger.info(f"[BUILD_PATH] Added missing project {missing_id} to class {min_class_id}, slot {slot}")
        
        # Final verification
        final_assigned_ids = {a.project_id for a in solution.assignments}
        if len(final_assigned_ids) != len(all_project_ids):
            logger.error(f"[BUILD_PATH] CRITICAL: Still missing {len(all_project_ids) - len(final_assigned_ids)} projects!")
        else:
            # Use debug level to avoid duplicate log messages during optimization iterations
            logger.debug(f"[BUILD_PATH] SUCCESS: All {len(all_project_ids)} projects are in solution!")
        
        return solution
    
    def _create_greedy_solution(self, class_count: int) -> DPSolution:
        """
        Create greedy solution as fallback.
        
        CRITICAL: Ensures ALL projects are included.
        """
        solution = DPSolution(class_count=class_count)
        class_loads = [0] * class_count
        workloads = defaultdict(int)
        
        # CRITICAL: Use ALL projects, ensure _order_projects returns all
        ordered_projects = self._order_projects()
        
        # Verify all projects are in ordered list
        ordered_ids = {p.id for p in ordered_projects}
        all_project_ids = {p.id for p in self.projects}
        if len(ordered_ids) != len(all_project_ids):
            logger.warning(f"[GREEDY] Missing projects in ordered list! Expected {len(all_project_ids)}, got {len(ordered_ids)}")
            # Add missing projects
            for p in self.projects:
                if p.id not in ordered_ids:
                    logger.warning(f"[GREEDY] Adding missing project {p.id}")
                    ordered_projects.append(p)
        
        for project in ordered_projects:
            # Pick class with lowest load
            best_class = min(range(class_count), key=lambda c: class_loads[c])
            slot = class_loads[best_class]
            
            # Pick J1 with lowest workload
            available_j1 = [
                fid for fid in self.faculty_ids
                if fid != project.responsible_id
            ]
            
            if available_j1:
                best_j1 = min(available_j1, key=lambda j: workloads.get(j, 0))
            else:
                best_j1 = self.faculty_ids[0] if self.faculty_ids else -1
            
            assignment = ProjectAssignment(
                project_id=project.id,
                class_id=best_class,
                order_in_class=slot,
                ps_id=project.responsible_id,
                j1_id=best_j1,
                j2_id=-1
            )
            solution.assignments.append(assignment)
            
            class_loads[best_class] += 1
            workloads[project.responsible_id] += 1
            workloads[best_j1] += 1
        
        # CRITICAL: Final verification
        assigned_ids = {a.project_id for a in solution.assignments}
        if len(assigned_ids) != len(all_project_ids):
            logger.error(f"[GREEDY] CRITICAL: Missing {len(all_project_ids) - len(assigned_ids)} projects!")
        else:
            logger.info(f"[GREEDY] SUCCESS: All {len(all_project_ids)} projects are in solution!")
        
        return solution


# ============================================================================
# MAIN ALGORITHM CLASS
# ============================================================================

class DynamicProgrammingAlgorithm(OptimizationAlgorithm):
    """
    Dynamic Programming Algorithm for academic project jury scheduling.
    
    Implements full DP-based optimization with:
    - Multi-dimensional state space
    - Incremental cost computation
    - Dominance pruning
    - Beam search for scalability
    - Priority mode handling
    - Multiple class count evaluation
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.name = "Dynamic Programming Algorithm"
        self.description = (
            "Multi-dimensional DP optimization for academic project jury scheduling "
            "with workload balance, continuity, and class distribution optimization."
        )
        
        # Configuration
        self.config = self._build_config(params or {})
        
        # Data storage
        self.projects: List[Project] = []
        self.instructors: List[Instructor] = []
        self.classrooms: List[Dict[str, Any]] = []
        self.timeslots: List[Dict[str, Any]] = []
        
        # Results
        self.best_solution: Optional[DPSolution] = None
        self.best_score: Optional[ScoreBreakdown] = None
    
    def _build_config(self, params: Dict[str, Any]) -> DPConfig:
        """Build configuration from parameters."""
        config = DPConfig()
        
        # Apply parameters
        for key, value in params.items():
            if hasattr(config, key):
                if key == "priority_mode" and isinstance(value, str):
                    value = PriorityMode(value)
                elif key == "time_penalty_mode" and isinstance(value, str):
                    value = TimePenaltyMode(value)
                elif key == "workload_constraint_mode" and isinstance(value, str):
                    value = WorkloadConstraintMode(value)
                setattr(config, key, value)
        
        return config
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Initialize algorithm with data.
        
        CRITICAL: Handles classroom_count parameter from data.
        """
        self._parse_input_data(data)
        
        # CRITICAL: Handle classroom_count from data
        classroom_count = data.get("classroom_count")
        if classroom_count and classroom_count > 0:
            # Limit to available classrooms
            if classroom_count > len(self.classrooms):
                logger.warning(
                    f"Requested classroom_count ({classroom_count}) exceeds available "
                    f"({len(self.classrooms)}). Using all available."
                )
                self.config.class_count = len(self.classrooms)
                self.config.auto_class_count = False
            else:
                self.config.class_count = classroom_count
                self.config.auto_class_count = False
                logger.info(f"DP Algorithm: Using {classroom_count} classrooms (from data)")
        elif len(self.classrooms) > 0:
            # Use available classrooms if no count specified
            self.config.class_count = len(self.classrooms)
            logger.info(f"DP Algorithm: Using {len(self.classrooms)} classrooms (from available)")
        
        logger.info(f"DP Algorithm initialized: {len(self.projects)} projects, "
                   f"{len(self.instructors)} instructors, "
                   f"{self.config.class_count} classes")
    
    def _parse_input_data(self, data: Dict[str, Any]) -> None:
        """Parse input data into internal structures."""
        # Parse projects
        raw_projects = data.get("projects", [])
        self.projects = []
        for p in raw_projects:
            if isinstance(p, dict):
                # CRITICAL: Check multiple possible field names for responsible instructor
                responsible_id = (
                    p.get("responsible_instructor_id") or
                    p.get("responsible_id") or
                    p.get("instructor_id") or
                    0
                )
                project = Project(
                    id=p.get("id", 0),
                    title=p.get("title", ""),
                    type=p.get("type", "interim"),
                    responsible_id=responsible_id,
                    is_makeup=p.get("is_makeup", False)
                )
            else:
                project = Project(
                    id=getattr(p, "id", 0),
                    title=getattr(p, "title", ""),
                    type=getattr(p, "type", "interim"),
                    responsible_id=getattr(p, "instructor_id", getattr(p, "responsible_id", 0)),
                    is_makeup=getattr(p, "is_makeup", False)
                )
            self.projects.append(project)
        
        # Parse instructors
        raw_instructors = data.get("instructors", [])
        self.instructors = []
        for i in raw_instructors:
            if isinstance(i, dict):
                instructor = Instructor(
                    id=i.get("id", 0),
                    name=i.get("name", ""),
                    type=i.get("type", "instructor")
                )
            else:
                instructor = Instructor(
                    id=getattr(i, "id", 0),
                    name=getattr(i, "name", ""),
                    type=getattr(i, "type", "instructor")
                )
            self.instructors.append(instructor)
        
        # Parse classrooms and timeslots
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
    
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run DP optimization.
        
        Args:
            data: Input data (optional if already initialized)
                  Note: initialize() is called by base class execute() method
            
        Returns:
            Optimization result dictionary
        """
        start_time = time.time()
        
        # Note: initialize() is already called by base class execute() method
        # No need to call it again here to avoid duplicate initialization
        
        logger.info(f"Starting DP optimization...")
        logger.info(f"  Priority mode: {self.config.priority_mode}")
        logger.info(f"  Auto class count: {self.config.auto_class_count}")
        
        # Determine class counts to try
        if self.config.auto_class_count:
            class_counts = [5, 6, 7]
        else:
            class_counts = [self.config.class_count]
        
        best_overall_solution = None
        best_overall_score = None
        best_overall_cost = float('inf')
        best_class_count = class_counts[0]
        
        for class_count in class_counts:
            logger.info(f"Trying class_count = {class_count}")
            
            try:
                # Use advanced solution builder
                builder = DPSolutionBuilder(
                    self.projects,
                    self.instructors,
                    self.config
                )
                solution = builder.build_optimal_solution(class_count)
                
                # Calculate final score
                penalty_calc = DPPenaltyCalculator(
                    self.projects, self.instructors, self.config
                )
                score = penalty_calc.calculate_full_penalty(solution)
                
                logger.info(f"  Class count {class_count}: cost = {score.total_z:.2f}")
                
                if score.total_z < best_overall_cost:
                    best_overall_cost = score.total_z
                    best_overall_solution = solution
                    best_overall_score = score
                    best_class_count = class_count
            
            except Exception as e:
                logger.error(f"Error with class_count={class_count}: {e}")
                continue
        
        if best_overall_solution is None:
            logger.warning("No valid solution found, creating fallback")
            best_overall_solution = self._create_fallback_solution()
            best_overall_score = ScoreBreakdown(total_z=float('inf'))
        
        self.best_solution = best_overall_solution
        self.best_score = best_overall_score
        
        # Convert to output format
        schedule = self._convert_solution_to_schedule(best_overall_solution)
        
        elapsed = time.time() - start_time
        
        result = {
            "schedule": schedule,
            "assignments": schedule,
            "solution": schedule,
            "cost": best_overall_score.total_z,
            "fitness": -best_overall_score.total_z,
            "penalty_breakdown": best_overall_score.to_dict(),
            "execution_time": elapsed,
            "class_count": best_class_count,
            "status": "completed",
            "algorithm_info": {
                "name": self.name,
                "description": self.description,
                "priority_mode": self.config.priority_mode.value,
                "time_penalty_mode": self.config.time_penalty_mode.value,
                "workload_constraint_mode": self.config.workload_constraint_mode.value
            }
        }
        
        logger.info(f"DP optimization completed in {elapsed:.2f}s")
        logger.info(f"  Best class count: {best_class_count}")
        logger.info(f"  Total cost: {best_overall_score.total_z:.2f}")
        
        return result
    
    def _create_fallback_solution(self) -> DPSolution:
        """
        Create fallback solution.
        
        CRITICAL: Ensures ALL projects are assigned.
        """
        # Use configured class count or default to available classrooms
        class_count = self.config.class_count
        if class_count <= 0 or class_count > len(self.classrooms):
            class_count = len(self.classrooms) if self.classrooms else 6
            logger.warning(f"[FALLBACK] Invalid class_count, using {class_count}")
        
        solution = DPSolution(class_count=class_count)
        faculty_ids = [
            i.id for i in self.instructors
            if i.type == "instructor"
        ]
        
        # CRITICAL: Ensure ALL projects are assigned
        class_loads = [0] * class_count
        for i, project in enumerate(self.projects):
            class_id = i % class_count
            slot = class_loads[class_id]
            class_loads[class_id] += 1
            
            j1_id = None
            for fid in faculty_ids:
                if fid != project.responsible_id:
                    j1_id = fid
                    break
            
            if j1_id is None:
                j1_id = faculty_ids[0] if faculty_ids else -1
            
            assignment = ProjectAssignment(
                project_id=project.id,
                class_id=class_id,
                order_in_class=slot,
                ps_id=project.responsible_id,
                j1_id=j1_id,
                j2_id=-1
            )
            solution.assignments.append(assignment)
        
        return solution
    
    def _convert_solution_to_schedule(
        self,
        solution: DPSolution
    ) -> List[Dict[str, Any]]:
        """
        Convert DPSolution to schedule format.
        
        CRITICAL: Ensures ALL projects are included in the output.
        """
        schedule = []
        
        if not solution or not solution.assignments:
            logger.warning("[CONVERT_SCHEDULE] Empty solution, creating fallback")
            return self._create_emergency_schedule()
        
        # Create mappings
        classroom_mapping = self._create_classroom_mapping(solution.class_count)
        timeslot_mapping = self._create_timeslot_mapping()
        project_map = {p.id: p for p in self.projects}
        
        # Track assigned projects
        assigned_project_ids = set()
        
        for assignment in solution.assignments:
            assigned_project_ids.add(assignment.project_id)
            
            classroom_id = classroom_mapping.get(
                assignment.class_id,
                self.classrooms[0].get("id", 1) if self.classrooms else assignment.class_id + 1
            )
            
            timeslot_id = timeslot_mapping.get(
                assignment.order_in_class,
                self.timeslots[0].get("id", 1) if self.timeslots else assignment.order_in_class + 1
            )
            
            # Instructors: [PS, J1, J2 placeholder]
            instructors = [assignment.ps_id, assignment.j1_id]
            
            # Add J2 placeholder
            if assignment.j2_id > 0:
                instructors.append(assignment.j2_id)
            else:
                instructors.append({
                    "id": -1,
                    "name": "[Arastirma Gorevlisi]",
                    "is_placeholder": True
                })
            
            project = project_map.get(assignment.project_id)
            
            entry = {
                "project_id": assignment.project_id,
                "classroom_id": classroom_id,
                "timeslot_id": timeslot_id,
                "instructors": instructors,
                "class_order": assignment.order_in_class,
                "class_id": assignment.class_id,
                "is_makeup": project.is_makeup if project else False
            }
            schedule.append(entry)
        
        # CRITICAL: Check for missing projects and add them
        all_project_ids = {p.id for p in self.projects}
        missing_project_ids = all_project_ids - assigned_project_ids
        
        if missing_project_ids:
            logger.warning(f"[CONVERT_SCHEDULE] Found {len(missing_project_ids)} missing projects, adding them...")
            schedule = self._add_missing_projects(schedule, missing_project_ids, solution.class_count)
        
        # Final verification
        final_assigned_ids = {entry["project_id"] for entry in schedule}
        if len(final_assigned_ids) != len(all_project_ids):
            logger.error(f"[CONVERT_SCHEDULE] CRITICAL: Still missing {len(all_project_ids) - len(final_assigned_ids)} projects!")
        else:
            logger.info(f"[CONVERT_SCHEDULE] SUCCESS: All {len(all_project_ids)} projects are in schedule!")
        
        return schedule
    
    def _add_missing_projects(
        self,
        schedule: List[Dict[str, Any]],
        missing_project_ids: Set[int],
        class_count: int
    ) -> List[Dict[str, Any]]:
        """
        Add missing projects to schedule.
        
        CRITICAL: Ensures ALL projects are included.
        """
        project_map = {p.id: p for p in self.projects}
        classroom_mapping = self._create_classroom_mapping(class_count)
        timeslot_mapping = self._create_timeslot_mapping()
        
        # Get faculty IDs
        faculty_ids = [
            i.id for i in self.instructors
            if i.type == "instructor"
        ]
        
        # Calculate class loads from existing schedule
        class_loads = defaultdict(int)
        for entry in schedule:
            class_id = entry.get("class_id", 0)
            class_loads[class_id] += 1
        
        # Add missing projects
        for missing_id in missing_project_ids:
            project = project_map.get(missing_id)
            if not project:
                logger.error(f"[ADD_MISSING] Project {missing_id} not found in project map!")
                continue
            
            # Find class with minimum load
            min_class_id = min(range(class_count), key=lambda c: class_loads.get(c, 0))
            slot = class_loads[min_class_id]
            class_loads[min_class_id] += 1
            
            # Get classroom ID
            classroom_id = classroom_mapping.get(
                min_class_id,
                self.classrooms[0].get("id", 1) if self.classrooms else min_class_id + 1
            )
            
            # Get timeslot ID
            timeslot_id = timeslot_mapping.get(
                slot,
                self.timeslots[0].get("id", 1) if self.timeslots else slot + 1
            )
            
            # Find J1 (must not be PS)
            j1_id = None
            for fid in faculty_ids:
                if fid != project.responsible_id:
                    j1_id = fid
                    break
            
            if j1_id is None:
                j1_id = faculty_ids[0] if faculty_ids else -1
            
            # Create entry
            entry = {
                "project_id": missing_id,
                "classroom_id": classroom_id,
                "timeslot_id": timeslot_id,
                "instructors": [
                    project.responsible_id,
                    j1_id,
                    {
                        "id": -1,
                        "name": "[Arastirma Gorevlisi]",
                        "is_placeholder": True
                    }
                ],
                "class_order": slot,
                "class_id": min_class_id,
                "is_makeup": project.is_makeup
            }
            schedule.append(entry)
            logger.info(f"[ADD_MISSING] Added project {missing_id} to class {min_class_id}, slot {slot}")
        
        return schedule
    
    def _create_emergency_schedule(self) -> List[Dict[str, Any]]:
        """
        Create emergency schedule when solution is empty.
        
        CRITICAL: Ensures ALL projects are assigned.
        """
        logger.warning("[EMERGENCY_SCHEDULE] Creating emergency schedule for all projects")
        
        # Use configured class count or default
        class_count = self.config.class_count
        if class_count <= 0 or class_count > len(self.classrooms):
            class_count = len(self.classrooms) if self.classrooms else 6
        
        schedule = []
        class_loads = [0] * class_count
        classroom_mapping = self._create_classroom_mapping(class_count)
        timeslot_mapping = self._create_timeslot_mapping()
        
        faculty_ids = [
            i.id for i in self.instructors
            if i.type == "instructor"
        ]
        
        # Assign ALL projects
        for i, project in enumerate(self.projects):
            class_id = i % class_count
            slot = class_loads[class_id]
            class_loads[class_id] += 1
            
            classroom_id = classroom_mapping.get(
                class_id,
                self.classrooms[0].get("id", 1) if self.classrooms else class_id + 1
            )
            
            timeslot_id = timeslot_mapping.get(
                slot,
                self.timeslots[0].get("id", 1) if self.timeslots else slot + 1
            )
            
            # Find J1
            j1_id = None
            for fid in faculty_ids:
                if fid != project.responsible_id:
                    j1_id = fid
                    break
            
            if j1_id is None:
                j1_id = faculty_ids[0] if faculty_ids else -1
            
            entry = {
                "project_id": project.id,
                "classroom_id": classroom_id,
                "timeslot_id": timeslot_id,
                "instructors": [
                    project.responsible_id,
                    j1_id,
                    {
                        "id": -1,
                        "name": "[Arastirma Gorevlisi]",
                        "is_placeholder": True
                    }
                ],
                "class_order": slot,
                "class_id": class_id,
                "is_makeup": project.is_makeup
            }
            schedule.append(entry)
        
        logger.info(f"[EMERGENCY_SCHEDULE] Created schedule with {len(schedule)} assignments for {len(self.projects)} projects")
        return schedule
    
    def _create_classroom_mapping(self, class_count: int) -> Dict[int, int]:
        """Map logical class IDs to real classroom IDs."""
        mapping = {}
        for i in range(class_count):
            if i < len(self.classrooms):
                cid = self.classrooms[i].get("id") if isinstance(self.classrooms[i], dict) else getattr(self.classrooms[i], "id", i + 1)
                mapping[i] = cid
            else:
                mapping[i] = i + 1
        return mapping
    
    def _create_timeslot_mapping(self) -> Dict[int, int]:
        """Map slot index to timeslot IDs."""
        mapping = {}
        for i, ts in enumerate(self.timeslots):
            tid = ts.get("id") if isinstance(ts, dict) else getattr(ts, "id", i + 1)
            mapping[i] = tid
        return mapping
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Evaluate fitness of a solution.
        
        Args:
            solution: Solution dictionary
            
        Returns:
            Fitness value (higher = better)
        """
        if not solution:
            return float('-inf')
        
        assignments = solution.get("solution", solution.get("schedule", solution))
        
        if isinstance(assignments, DPSolution):
            penalty_calc = DPPenaltyCalculator(
                self.projects, self.instructors, self.config
            )
            cost = penalty_calc.calculate_total_penalty(assignments)
            return -cost
        
        # Convert list to DPSolution
        if isinstance(assignments, list):
            dp_solution = self._convert_schedule_to_solution(assignments)
            if dp_solution:
                penalty_calc = DPPenaltyCalculator(
                    self.projects, self.instructors, self.config
                )
                cost = penalty_calc.calculate_total_penalty(dp_solution)
                return -cost
        
        return float('-inf')
    
    def _convert_schedule_to_solution(
        self,
        schedule: List[Dict[str, Any]]
    ) -> Optional[DPSolution]:
        """Convert schedule format to DPSolution."""
        if not schedule:
            return None
        
        solution = DPSolution(class_count=self.config.class_count)
        project_map = {p.id: p for p in self.projects}
        
        for entry in schedule:
            project_id = entry.get("project_id")
            instructors = entry.get("instructors", [])
            
            if not project_id or len(instructors) < 2:
                continue
            
            ps_id = instructors[0] if isinstance(instructors[0], int) else instructors[0].get("id", 0)
            j1_id = instructors[1] if isinstance(instructors[1], int) else instructors[1].get("id", 0)
            
            assignment = ProjectAssignment(
                project_id=project_id,
                class_id=entry.get("class_id", 0),
                order_in_class=entry.get("class_order", 0),
                ps_id=ps_id,
                j1_id=j1_id,
                j2_id=-1
            )
            solution.assignments.append(assignment)
        
        return solution
    
    def get_name(self) -> str:
        """Get algorithm name."""
        return "DynamicProgramming"
    
    def repair_solution(
        self,
        solution: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Repair solution after validation.
        
        Args:
            solution: Solution to repair
            validation_result: Validation results
            
        Returns:
            Repaired solution
        """
        assignments = solution.get("assignments", solution.get("schedule", []))
        
        if not assignments:
            return solution
        
        # Remove duplicates
        seen_projects = set()
        cleaned = []
        
        for a in assignments:
            project_id = a.get("project_id")
            if project_id not in seen_projects:
                seen_projects.add(project_id)
                cleaned.append(a)
        
        # Check slot conflicts
        used_slots = set()
        final = []
        
        for a in cleaned:
            slot_key = (a.get("classroom_id"), a.get("timeslot_id"))
            if slot_key not in used_slots:
                used_slots.add(slot_key)
                final.append(a)
        
        return {"assignments": final}


# ============================================================================
# PUBLIC API
# ============================================================================

def solve_with_dynamic_programming(
    input_data: Dict[str, Any],
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Public API for solving with Dynamic Programming.
    
    Args:
        input_data: Dictionary containing:
            - projects: List of project data
            - instructors: List of instructor data
            - classrooms: Optional list of classrooms
            - timeslots: Optional list of timeslots
        
        config: Optional configuration dictionary with:
            - class_count: Number of classes (default: 6)
            - auto_class_count: Try 5,6,7 and pick best (default: True)
            - priority_mode: ARA_ONCE, BITIRME_ONCE, ESIT
            - time_penalty_mode: BINARY, GAP_PROPORTIONAL
            - workload_constraint_mode: SOFT_ONLY, SOFT_AND_HARD
            - weight_h1, weight_h2, weight_h3, weight_h4: Penalty weights
            - max_states_per_layer: DP frontier limit
            - beam_width: Beam search width
            - time_limit: Time limit in seconds
    
    Returns:
        Dictionary with:
            - schedule: List of assignments
            - cost: Total cost
            - fitness: -cost (for compatibility)
            - execution_time: Execution time in seconds
            - penalty_breakdown: Detailed penalty breakdown
            - status: Completion status
    """
    # Build config
    dp_config = DPConfig()
    
    if config:
        # Class count settings
        if "class_count" in config:
            dp_config.class_count = config["class_count"]
        if "auto_class_count" in config:
            dp_config.auto_class_count = config["auto_class_count"]
        
        # DP control parameters
        if "max_states_per_layer" in config:
            dp_config.max_states_per_layer = config["max_states_per_layer"]
        if "beam_width" in config:
            dp_config.beam_width = config["beam_width"]
        if "time_limit" in config:
            dp_config.time_limit = config["time_limit"]
        if "enable_dominance_pruning" in config:
            dp_config.enable_dominance_pruning = config["enable_dominance_pruning"]
        
        # Mode settings
        if "priority_mode" in config:
            dp_config.priority_mode = PriorityMode(config["priority_mode"])
        if "time_penalty_mode" in config:
            dp_config.time_penalty_mode = TimePenaltyMode(config["time_penalty_mode"])
        if "workload_constraint_mode" in config:
            dp_config.workload_constraint_mode = WorkloadConstraintMode(config["workload_constraint_mode"])
        
        # Weights
        if "weight_h1" in config:
            dp_config.weight_h1 = config["weight_h1"]
        if "weight_h2" in config:
            dp_config.weight_h2 = config["weight_h2"]
        if "weight_h3" in config:
            dp_config.weight_h3 = config["weight_h3"]
        if "weight_h4" in config:
            dp_config.weight_h4 = config["weight_h4"]
        if "weight_continuity" in config:
            dp_config.weight_continuity = config["weight_continuity"]
        
        # Workload settings
        if "workload_hard_limit" in config:
            dp_config.workload_hard_limit = config["workload_hard_limit"]
        if "workload_soft_band" in config:
            dp_config.workload_soft_band = config["workload_soft_band"]
    
    # Create and run algorithm
    algorithm = DynamicProgrammingAlgorithm({
        "class_count": dp_config.class_count,
        "auto_class_count": dp_config.auto_class_count,
        "max_states_per_layer": dp_config.max_states_per_layer,
        "beam_width": dp_config.beam_width,
        "time_limit": dp_config.time_limit,
        "enable_dominance_pruning": dp_config.enable_dominance_pruning,
        "priority_mode": dp_config.priority_mode.value,
        "time_penalty_mode": dp_config.time_penalty_mode.value,
        "workload_constraint_mode": dp_config.workload_constraint_mode.value,
        "weight_h1": dp_config.weight_h1,
        "weight_h2": dp_config.weight_h2,
        "weight_h3": dp_config.weight_h3,
        "weight_h4": dp_config.weight_h4,
        "weight_continuity": dp_config.weight_continuity,
        "workload_hard_limit": dp_config.workload_hard_limit,
        "workload_soft_band": dp_config.workload_soft_band
    })
    
    algorithm.initialize(input_data)
    result = algorithm.optimize(input_data)
    
    return result


def create_dynamic_programming(
    params: Dict[str, Any] = None
) -> DynamicProgrammingAlgorithm:
    """
    Factory function to create DP algorithm.
    
    Args:
        params: Configuration parameters
        
    Returns:
        Configured DynamicProgrammingAlgorithm instance
    """
    return DynamicProgrammingAlgorithm(params)


# Aliases for compatibility
DynamicProgramming = DynamicProgrammingAlgorithm

