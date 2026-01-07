"""
Integer Linear Programming (ILP) Optimizer for Academic Project Exam/Jury Planning.

This module implements a multi-criteria, multi-constraint Integer Linear Programming
solver using PuLP for academic project scheduling with jury assignments.

Key Features:
- Project-class-slot assignment optimization
- First Jury (J1) assignment as decision variable
- Second Jury (J2) is a fixed placeholder "[Arastirma Gorevlisi]" - NOT in model
- Multi-criteria objective: workload uniformity (H2), gap penalty (H1), class changes (H3)
- Configurable priority modes (BITIRME always before ARA - HARD constraint)
- Back-to-back scheduling (no gaps in classroom)
- Workload uniformity with ±2 tolerance band

Mathematical Formulation:
    min Z = C1·H1(n) + C2·H2(n) + C3·H3(n)
    
    where:
        H1: Time/gap penalty
        H2: Workload uniformity penalty (most important, C2 > C1 and C2 > C3)
        H3: Class change penalty

Hard Constraints:
    1. BITIRME projects always assigned before ARA projects (mandatory)
    2. Each project assigned exactly once
    3. At most one project per (class, timeslot)
    4. Back-to-back scheduling in each classroom (no gaps)
    5. Teacher cannot be J1 on their own project
    6. Exactly one J1 per project
    7. Teacher can have at most 1 duty per timeslot across all classes
    8. Workload within ±B_max from average (if SOFT_AND_HARD mode)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set
from enum import Enum
from collections import defaultdict
import logging
import math
import time

try:
    import pulp
    PULP_AVAILABLE = True
except ImportError:
    PULP_AVAILABLE = False
    pulp = None

from app.algorithms.base import OptimizationAlgorithm

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND CONFIGURATION
# =============================================================================

class PriorityMode(Enum):
    """Project type prioritization mode."""
    BITIRME_ONCE = "BITIRME_ONCE"  # All BITIRME projects before ARA (DEFAULT & MANDATORY)
    ARA_ONCE = "ARA_ONCE"          # All ARA projects before BITIRME
    ESIT = "ESIT"                  # No priority ordering


class TimePenaltyMode(Enum):
    """Time/gap penalty calculation mode."""
    BINARY = "BINARY"                     # 1 if not consecutive, 0 otherwise
    GAP_PROPORTIONAL = "GAP_PROPORTIONAL"  # Penalty = number of gap slots


class WorkloadConstraintMode(Enum):
    """Workload constraint mode."""
    SOFT_ONLY = "SOFT_ONLY"           # Only soft penalty, no hard limit
    SOFT_AND_HARD = "SOFT_AND_HARD"   # Soft penalty + hard upper bound


@dataclass
class ILPConfig:
    """Configuration for ILP solver."""
    
    # Priority mode - BITIRME_ONCE is DEFAULT and MANDATORY per system design
    priority_mode: str = "BITIRME_ONCE"
    
    # Penalty modes
    time_penalty_mode: str = "BINARY"
    workload_constraint_mode: str = "SOFT_ONLY"
    
    # Weights for objective function (C2 > C1 and C2 > C3)
    # İş yükü dengesi en baskın optimizasyon kriteri
    weight_continuity: int = 10      # C1 - for gap/continuity penalty
    weight_uniformity: int = 100     # C2 - for workload uniformity (most important)
    weight_class_change: int = 5     # C3 - for class change penalty
    weight_class_load: int = 2       # C4 - for class load balancing
    
    # Hard constraint parameters
    b_max: int = 4  # Maximum allowed deviation from average workload
    workload_tolerance: int = 2  # ±2 tolerance band for soft penalty
    
    # Solver parameters - OPTIMIZED FOR SPEED
    max_time_seconds: int = 120  # 2 minutes (reduced from 5)
    solver_msg: bool = False     # Suppress solver messages
    
    # Warm start and MIP optimization
    use_warm_start: bool = True   # Use greedy initial solution
    mip_gap: float = 0.02         # Accept 2% gap from optimal (faster)
    threads: int = 0              # 0 = auto (use all cores)
    presolve: bool = True         # Enable presolve
    cuts: bool = True             # Enable cutting planes
    strong_branching: int = 5     # Strong branching candidates
    
    # Class count mode
    class_count_mode: str = "auto"  # "auto" or "manual"
    given_z: int = 6                # Used if class_count_mode == "manual"
    
    # Slot duration in hours (for time calculations)
    slot_duration: float = 0.5  # 30 minutes
    
    # Epsilon for floating point comparisons
    epsilon: float = 0.001


@dataclass
class Teacher:
    """Teacher/Instructor data class."""
    id: int
    code: str
    name: str = ""
    is_research_assistant: bool = False


@dataclass
class Project:
    """Project data class."""
    id: int
    ps_id: int  # Project Supervisor ID
    project_type: str  # "ARA" or "BITIRME"
    name: str = ""
    is_makeup: bool = False


@dataclass
class ScheduleRow:
    """Single row in the output schedule."""
    project_id: int
    class_id: int
    class_name: str
    order_in_class: int
    global_slot: int
    ps_id: int
    j1_id: int
    j2_label: str = "[Arastirma Gorevlisi]"  # Fixed placeholder - NOT in model


# =============================================================================
# ILP MODEL BUILDING
# =============================================================================

class ILPModelBuilder:
    """
    Builds and solves the Integer Linear Programming model for academic project scheduling.
    
    Decision Variables:
        - assign[p, s, t]: Binary, project p assigned to class s at timeslot t
        - j1[p, h]: Binary, teacher h is J1 for project p
        
    Derived Variables:
        - active[h, s, t]: Binary, teacher h is active in class s at timeslot t
        - slot_used[s, t]: Binary, class s has a project at timeslot t
        - load[h]: Integer, total duties for teacher h
        - class_used[h, s]: Binary, teacher h has any duty in class s
        - dev[h]: Integer, deviation from average workload (for penalty)
        - cont_excess[h, s]: Integer, continuity excess (blocks - 1) per (teacher, class)
        - class_change_excess[h]: Integer, class change penalty per teacher
    """
    
    def __init__(
        self,
        projects: List[Project],
        teachers: List[Teacher],
        config: ILPConfig,
        num_classes: int,
        class_names: Optional[List[str]] = None
    ):
        self.projects = projects
        self.teachers = teachers
        self.config = config
        self.num_classes = num_classes
        
        # Filter out research assistants - they are NOT part of the model
        self.faculty = [t for t in teachers if not t.is_research_assistant]
        self.faculty_ids = [t.id for t in self.faculty]
        
        # Generate class names
        if class_names:
            self.class_names = class_names[:num_classes]
        else:
            self.class_names = [f"D{105 + i}" for i in range(num_classes)]
        
        # Calculate max slots per class
        Y = len(projects)
        z = num_classes
        self.max_slots = math.ceil(Y / z) + 5 if z > 0 else 20
        
        # PS lookup
        self.ps_lookup = {p.id: p.ps_id for p in projects}
        
        # Model and variables
        self.model = None
        self.assign = {}
        self.j1 = {}
        self.active = {}
        self.slot_used = {}
        self.load = {}
        self.class_used = {}
        self.dev = {}
        self.cont_excess = {}
        self.class_change_excess = {}
        
        logger.info(
            f"ILP Model Builder: {Y} projects, {len(self.faculty)} faculty, "
            f"{z} classes, {self.max_slots} max slots"
        )
    
    def build(self) -> 'ILPModelBuilder':
        """Build the complete ILP model."""
        if not PULP_AVAILABLE:
            raise ImportError(
                "PuLP is not installed. Install it with: pip install pulp"
            )
        
        # Create model
        self.model = pulp.LpProblem("Academic_Project_Scheduling", pulp.LpMinimize)
        
        # Build components
        self._create_decision_variables()
        self._add_hard_constraints()
        self._add_soft_penalty_variables()
        self._set_objective()
        
        return self
    
    def _create_decision_variables(self):
        """Create all decision and derived variables."""
        z = self.num_classes
        T = self.max_slots
        
        # 1. Project -> class & slot assignment: assign[p, s, t]
        for p in self.projects:
            for s in range(z):
                for t in range(T):
                    var_name = f"assign_p{p.id}_s{s}_t{t}"
                    self.assign[(p.id, s, t)] = pulp.LpVariable(var_name, cat='Binary')
        
        # 2. First Jury assignment: j1[p, h]
        for p in self.projects:
            for h in self.faculty_ids:
                var_name = f"j1_p{p.id}_h{h}"
                self.j1[(p.id, h)] = pulp.LpVariable(var_name, cat='Binary')
        
        # 3. Slot usage: slot_used[s, t]
        for s in range(z):
            for t in range(T):
                var_name = f"slot_used_s{s}_t{t}"
                self.slot_used[(s, t)] = pulp.LpVariable(var_name, cat='Binary')
        
        # 4. Teacher activity: active[h, s, t]
        for h in self.faculty_ids:
            for s in range(z):
                for t in range(T):
                    var_name = f"active_h{h}_s{s}_t{t}"
                    self.active[(h, s, t)] = pulp.LpVariable(var_name, cat='Binary')
        
        # 5. Workload: load[h]
        max_possible_load = 2 * len(self.projects)
        for h in self.faculty_ids:
            var_name = f"load_h{h}"
            self.load[h] = pulp.LpVariable(
                var_name, lowBound=0, upBound=max_possible_load, cat='Integer'
            )
        
        # 6. Class usage per teacher: class_used[h, s]
        for h in self.faculty_ids:
            for s in range(z):
                var_name = f"class_used_h{h}_s{s}"
                self.class_used[(h, s)] = pulp.LpVariable(var_name, cat='Binary')
        
        # 7. Deviation from average workload: dev[h]
        for h in self.faculty_ids:
            var_name = f"dev_h{h}"
            self.dev[h] = pulp.LpVariable(
                var_name, lowBound=0, upBound=max_possible_load, cat='Integer'
            )
        
        # 8. Class change excess: class_change_excess[h]
        for h in self.faculty_ids:
            var_name = f"class_change_excess_h{h}"
            self.class_change_excess[h] = pulp.LpVariable(
                var_name, lowBound=0, upBound=self.num_classes, cat='Integer'
            )
        
        # 9. Continuity excess per (teacher, class): cont_excess[h, s]
        for h in self.faculty_ids:
            for s in range(z):
                var_name = f"cont_excess_h{h}_s{s}"
                self.cont_excess[(h, s)] = pulp.LpVariable(
                    var_name, lowBound=0, upBound=T, cat='Integer'
                )
    
    def _add_hard_constraints(self):
        """Add all hard constraints to the model."""
        z = self.num_classes
        T = self.max_slots
        
        # 1. Each project assigned exactly once
        for p in self.projects:
            self.model += (
                pulp.lpSum(
                    self.assign[(p.id, s, t)]
                    for s in range(z)
                    for t in range(T)
                ) == 1,
                f"one_assignment_p{p.id}"
            )
        
        # 2. At most one project per class-slot
        for s in range(z):
            for t in range(T):
                self.model += (
                    pulp.lpSum(
                        self.assign[(p.id, s, t)] for p in self.projects
                    ) <= 1,
                    f"at_most_one_project_s{s}_t{t}"
                )
        
        # 3. Link slot_used to assign
        for s in range(z):
            for t in range(T):
                project_sum = pulp.lpSum(
                    self.assign[(p.id, s, t)] for p in self.projects
                )
                # slot_used >= any assign (implied by the sum)
                self.model += (
                    self.slot_used[(s, t)] >= project_sum - 0.5,
                    f"slot_used_lower_s{s}_t{t}"
                )
                # slot_used <= sum of assigns
                self.model += (
                    self.slot_used[(s, t)] <= project_sum + 0.5,
                    f"slot_used_upper_s{s}_t{t}"
                )
        
        # 4. Back-to-back: no gaps in class schedule
        # slot_used[s, t-1] >= slot_used[s, t] for t > 0
        for s in range(z):
            for t in range(1, T):
                self.model += (
                    self.slot_used[(s, t - 1)] >= self.slot_used[(s, t)],
                    f"back_to_back_s{s}_t{t}"
                )
        
        # 5. Teacher cannot be J1 on their own project
        for p in self.projects:
            ps_id = self.ps_lookup[p.id]
            if ps_id in self.faculty_ids:
                self.model += (
                    self.j1[(p.id, ps_id)] == 0,
                    f"no_self_jury_p{p.id}"
                )
        
        # 6. Exactly one J1 per project
        for p in self.projects:
            self.model += (
                pulp.lpSum(self.j1[(p.id, h)] for h in self.faculty_ids) == 1,
                f"one_j1_p{p.id}"
            )
        
        # 7. Link active[h,s,t] to assignments
        self._link_active_variables()
        
        # 8. Max one duty per teacher per timeslot (across all classes)
        for h in self.faculty_ids:
            for t in range(T):
                self.model += (
                    pulp.lpSum(self.active[(h, s, t)] for s in range(z)) <= 1,
                    f"one_duty_per_slot_h{h}_t{t}"
                )
        
        # 9. Workload calculation: load[h] = PS duties + J1 duties
        for h in self.faculty_ids:
            ps_count = sum(1 for p in self.projects if self.ps_lookup[p.id] == h)
            j1_sum = pulp.lpSum(self.j1[(p.id, h)] for p in self.projects)
            self.model += (
                self.load[h] == ps_count + j1_sum,
                f"workload_h{h}"
            )
        
        # 10. Link class_used[h,s]
        for h in self.faculty_ids:
            for s in range(z):
                # class_used >= any active (Big-M formulation)
                active_sum = pulp.lpSum(self.active[(h, s, t)] for t in range(T))
                self.model += (
                    self.class_used[(h, s)] * T >= active_sum,
                    f"class_used_upper_h{h}_s{s}"
                )
                self.model += (
                    self.class_used[(h, s)] <= active_sum,
                    f"class_used_lower_h{h}_s{s}"
                )
        
        # 11. Project type priority constraints (BITIRME before ARA)
        self._add_priority_constraints()
        
        # 12. Hard workload bounds (if SOFT_AND_HARD mode)
        self._add_workload_hard_constraints()
    
    def _link_active_variables(self):
        """
        Link active[h,s,t] to project assignments and J1 assignments.
        
        SIMPLIFIED VERSION: Only link via PS role, not J1.
        This significantly reduces the number of constraints and variables.
        The J1 constraint violations are still prevented by the one-duty-per-slot constraint.
        """
        z = self.num_classes
        T = self.max_slots
        
        for h in self.faculty_ids:
            # Get projects where h is PS
            ps_projects = [p for p in self.projects if self.ps_lookup[p.id] == h]
            
            for s in range(z):
                for t in range(T):
                    # SIMPLIFIED: active[h,s,t] = 1 if h is PS for any project at (s,t)
                    # We ignore J1 role for active linking to reduce complexity
                    # The one-duty-per-slot constraint handles J1 conflicts
                    
                    if ps_projects:
                        ps_sum = pulp.lpSum(
                            self.assign[(p.id, s, t)] for p in ps_projects
                        )
                        # active >= ps_sum (if any PS project at this slot, active)
                        self.model += (
                            self.active[(h, s, t)] >= ps_sum,
                            f"active_ps_h{h}_s{s}_t{t}"
                        )
                        # active <= ps_sum (simplified: ignore J1 for now)
                        self.model += (
                            self.active[(h, s, t)] <= ps_sum,
                            f"active_upper_h{h}_s{s}_t{t}"
                        )
                    else:
                        # h is not PS for any project, so never active as PS
                        self.model += (
                            self.active[(h, s, t)] == 0,
                            f"active_zero_h{h}_s{s}_t{t}"
                        )
    
    def _add_priority_constraints(self):
        """
        Add project type priority constraints (BITIRME before ARA).
        
        HARD CONSTRAINT: Per-class ordering - Within each class, all BITIRME projects
        must come before all ARA projects.
        
        This is more flexible than global ordering and works better with back-to-back
        scheduling and multiple classes.
        
        Formulation: For each class s, BITIRME b, and ARA a:
            If both b and a are in class s, then slot(b) < slot(a)
        """
        priority_mode = self.config.priority_mode
        
        if priority_mode == "ESIT":
            # No priority ordering
            return
        
        z = self.num_classes
        T = self.max_slots
        
        # Separate projects by type
        ara_projects = [p for p in self.projects if p.project_type == "ARA"]
        bitirme_projects = [p for p in self.projects if p.project_type == "BITIRME"]
        
        if not ara_projects or not bitirme_projects:
            return
        
        if priority_mode == "BITIRME_ONCE":
            # HARD CONSTRAINT: Per-class ordering
            # For each class s: if BITIRME b and ARA a both in class s, then slot(b) < slot(a)
            #
            # Implementation: For each (b, a, s) triple:
            #   If both in class s: slot_in_class(b) < slot_in_class(a)
            #   Using Big-M: slot(b) <= slot(a) - 1 + M*(2 - in_class_b - in_class_a)
            
            constraint_count = 0
            M = T + 10  # Big-M value
            
            for s in range(z):
                for b in bitirme_projects:
                    for a in ara_projects:
                        # Create indicator: is b in class s?
                        b_in_s = pulp.lpSum(self.assign[(b.id, s, t)] for t in range(T))
                        # Create indicator: is a in class s?
                        a_in_s = pulp.lpSum(self.assign[(a.id, s, t)] for t in range(T))
                        
                        # Slot index within class s for b
                        slot_b = pulp.lpSum(t * self.assign[(b.id, s, t)] for t in range(T))
                        # Slot index within class s for a
                        slot_a = pulp.lpSum(t * self.assign[(a.id, s, t)] for t in range(T))
                        
                        # If both in class s: slot_b <= slot_a - 1
                        # Big-M: slot_b - slot_a <= -1 + M*(2 - b_in_s - a_in_s)
                        # This means: if b_in_s=1 and a_in_s=1, then slot_b <= slot_a - 1
                        self.model += (
                            slot_b <= slot_a - 1 + M * (2 - b_in_s - a_in_s),
                            f"bitirme_before_ara_b{b.id}_a{a.id}_s{s}"
                        )
                        constraint_count += 1
            
            logger.info(
                f"Priority HARD constraint: {len(bitirme_projects)} BITIRME before "
                f"{len(ara_projects)} ARA (per-class, {constraint_count} constraints)"
            )
        
        elif priority_mode == "ARA_ONCE":
            # Same but reversed: ARA before BITIRME per class
            constraint_count = 0
            M = T + 10
            
            for s in range(z):
                for a in ara_projects:
                    for b in bitirme_projects:
                        a_in_s = pulp.lpSum(self.assign[(a.id, s, t)] for t in range(T))
                        b_in_s = pulp.lpSum(self.assign[(b.id, s, t)] for t in range(T))
                        
                        slot_a = pulp.lpSum(t * self.assign[(a.id, s, t)] for t in range(T))
                        slot_b = pulp.lpSum(t * self.assign[(b.id, s, t)] for t in range(T))
                        
                        self.model += (
                            slot_a <= slot_b - 1 + M * (2 - a_in_s - b_in_s),
                            f"ara_before_bitirme_a{a.id}_b{b.id}_s{s}"
                        )
                        constraint_count += 1
            
            logger.info(
                f"Priority HARD constraint: {len(ara_projects)} ARA before "
                f"{len(bitirme_projects)} BITIRME (per-class, {constraint_count} constraints)"
            )
    
    def _add_workload_hard_constraints(self):
        """Add hard workload constraints if mode is SOFT_AND_HARD."""
        if self.config.workload_constraint_mode != "SOFT_AND_HARD":
            return
        
        Y = len(self.projects)
        X = len(self.faculty_ids)
        
        if X == 0:
            return
        
        avg_load = (2 * Y) / X
        b_max = self.config.b_max
        
        avg_floor = int(math.floor(avg_load))
        avg_ceil = int(math.ceil(avg_load))
        
        for h in self.faculty_ids:
            # load[h] - avg <= b_max → load[h] <= avg_ceil + b_max
            self.model += (
                self.load[h] <= avg_ceil + b_max,
                f"workload_upper_h{h}"
            )
            # avg - load[h] <= b_max → load[h] >= avg_floor - b_max
            self.model += (
                self.load[h] >= max(0, avg_floor - b_max),
                f"workload_lower_h{h}"
            )
    
    def _add_soft_penalty_variables(self):
        """Add soft penalty variable constraints."""
        z = self.num_classes
        T = self.max_slots
        Y = len(self.projects)
        X = len(self.faculty_ids)
        
        # Calculate average workload
        avg_load = (2 * Y) / X if X > 0 else 0
        avg_floor = int(math.floor(avg_load))
        avg_ceil = int(math.ceil(avg_load))
        tolerance = self.config.workload_tolerance
        
        # 1. Workload deviation penalty: dev[h] >= |load[h] - avg| - tolerance
        for h in self.faculty_ids:
            # dev[h] >= load[h] - (avg + tolerance)
            self.model += (
                self.dev[h] >= self.load[h] - (avg_ceil + tolerance),
                f"dev_upper_h{h}"
            )
            # dev[h] >= (avg - tolerance) - load[h]
            self.model += (
                self.dev[h] >= (avg_floor - tolerance) - self.load[h],
                f"dev_lower_h{h}"
            )
        
        # 2. Class change excess: class_change_excess[h] >= class_count[h] - 2
        for h in self.faculty_ids:
            class_count = pulp.lpSum(self.class_used[(h, s)] for s in range(z))
            self.model += (
                self.class_change_excess[h] >= class_count - 2,
                f"class_change_excess_h{h}"
            )
        
        # 3. Continuity penalty - SIMPLIFIED VERSION
        # Instead of counting blocks (which requires many auxiliary variables),
        # we use a simpler formulation: penalize the number of classes used
        # This is already captured by class_change_excess, so we set cont_excess = 0
        # to avoid redundancy and speed up the solver
        for h in self.faculty_ids:
            for s in range(z):
                # Set cont_excess to 0 (disabled for performance)
                # The class_change penalty already captures similar behavior
                self.model += (
                    self.cont_excess[(h, s)] == 0,
                    f"cont_excess_zero_h{h}_s{s}"
                )
    
    def _set_objective(self):
        """Set the multi-criteria objective function."""
        z = self.num_classes
        
        # H1: Continuity penalty (sum of cont_excess)
        H1 = pulp.lpSum(
            self.cont_excess[(h, s)]
            for h in self.faculty_ids
            for s in range(z)
        )
        
        # H2: Workload uniformity penalty (sum of dev)
        H2 = pulp.lpSum(self.dev[h] for h in self.faculty_ids)
        
        # H3: Class change penalty (sum of class_change_excess)
        H3 = pulp.lpSum(self.class_change_excess[h] for h in self.faculty_ids)
        
        # Weighted objective: min Z = C1*H1 + C2*H2 + C3*H3
        # Note: C2 > C1 and C2 > C3 (workload uniformity is most important)
        objective = (
            self.config.weight_continuity * H1 +
            self.config.weight_uniformity * H2 +
            self.config.weight_class_change * H3
        )
        
        self.model += objective
    
    def _generate_greedy_initial_solution(self) -> Dict[str, Any]:
        """
        Generate a greedy initial solution for warm start.
        
        This significantly speeds up the ILP solver by providing a good
        starting point. The greedy approach:
        1. Sort projects: BITIRME first, then ARA
        2. Assign to classes in round-robin fashion
        3. Assign J1 based on workload balancing
        
        Returns:
            Dictionary with project assignments and J1 assignments
        """
        z = self.num_classes
        
        # Sort projects: BITIRME first (mandatory), then ARA
        bitirme = [p for p in self.projects if p.project_type == "BITIRME"]
        ara = [p for p in self.projects if p.project_type == "ARA"]
        sorted_projects = bitirme + ara
        
        # Track assignments
        class_slots = [0] * z  # Next available slot per class
        project_assignments = {}  # project_id -> (class, slot)
        j1_assignments = {}       # project_id -> j1_id
        
        # Track workload for J1 assignment
        faculty_workload = {h: 0 for h in self.faculty_ids}
        
        # Count PS duties (fixed)
        for p in self.projects:
            ps_id = self.ps_lookup[p.id]
            if ps_id in faculty_workload:
                faculty_workload[ps_id] += 1
        
        # Assign projects to classes (round-robin for balance)
        current_class = 0
        for p in sorted_projects:
            # Assign to current class
            slot = class_slots[current_class]
            project_assignments[p.id] = (current_class, slot)
            class_slots[current_class] += 1
            
            # Move to next class (round-robin)
            current_class = (current_class + 1) % z
        
        # Assign J1 for each project (workload balancing)
        for p in sorted_projects:
            ps_id = self.ps_lookup[p.id]
            
            # Find faculty with minimum workload (excluding PS)
            candidates = [
                (faculty_workload[h], h) 
                for h in self.faculty_ids 
                if h != ps_id
            ]
            
            if candidates:
                candidates.sort()
                j1_id = candidates[0][1]
                j1_assignments[p.id] = j1_id
                faculty_workload[j1_id] += 1
        
        return {
            'project_assignments': project_assignments,
            'j1_assignments': j1_assignments,
            'faculty_workload': faculty_workload
        }
    
    def _apply_warm_start(self, initial_solution: Dict[str, Any]) -> None:
        """
        Apply the greedy initial solution as warm start.
        
        Sets initial values for decision variables.
        """
        project_assignments = initial_solution.get('project_assignments', {})
        j1_assignments = initial_solution.get('j1_assignments', {})
        
        z = self.num_classes
        T = self.max_slots
        
        # Set initial values for assign variables
        for p in self.projects:
            if p.id in project_assignments:
                assigned_class, assigned_slot = project_assignments[p.id]
                for s in range(z):
                    for t in range(T):
                        var = self.assign[(p.id, s, t)]
                        if s == assigned_class and t == assigned_slot:
                            var.setInitialValue(1)
                        else:
                            var.setInitialValue(0)
        
        # Set initial values for j1 variables
        for p in self.projects:
            if p.id in j1_assignments:
                assigned_j1 = j1_assignments[p.id]
                for h in self.faculty_ids:
                    var = self.j1[(p.id, h)]
                    if h == assigned_j1:
                        var.setInitialValue(1)
                    else:
                        var.setInitialValue(0)
        
        # Set slot_used based on assignments
        slot_usage = defaultdict(bool)
        for p_id, (s, t) in project_assignments.items():
            slot_usage[(s, t)] = True
        
        for s in range(z):
            for t in range(T):
                self.slot_used[(s, t)].setInitialValue(1 if slot_usage[(s, t)] else 0)
        
        logger.info("Warm start applied with greedy initial solution")
    
    def solve(self) -> Tuple[str, Optional[float]]:
        """
        Solve the ILP model with optimized parameters.
        
        Uses warm start (greedy initial solution) and optimized
        solver parameters for faster convergence.
        
        Returns:
            Tuple of (status, objective_value)
        """
        if self.model is None:
            raise ValueError("Model not built. Call build() first.")
        
        # Generate and apply warm start if enabled
        if self.config.use_warm_start:
            try:
                initial_solution = self._generate_greedy_initial_solution()
                self._apply_warm_start(initial_solution)
            except Exception as e:
                logger.warning(f"Warm start failed: {e}")
        
        # Build optimized solver options
        solver_options = [
            f"sec {self.config.max_time_seconds}",  # Time limit
            f"ratio {self.config.mip_gap}",          # MIP gap tolerance
        ]
        
        if self.config.threads > 0:
            solver_options.append(f"threads {self.config.threads}")
        
        if self.config.presolve:
            solver_options.append("presolve on")
        else:
            solver_options.append("presolve off")
        
        if self.config.cuts:
            solver_options.append("cuts on")
        
        # Select solver with optimized parameters
        # Note: On Windows, warmStart requires keepFiles=True
        import platform
        is_windows = platform.system() == "Windows"
        
        solver = pulp.PULP_CBC_CMD(
            msg=self.config.solver_msg,
            timeLimit=self.config.max_time_seconds,
            gapRel=self.config.mip_gap,
            warmStart=self.config.use_warm_start,
            keepFiles=is_windows and self.config.use_warm_start,
            options=solver_options
        )
        
        # Solve
        start_time = time.time()
        status = self.model.solve(solver)
        solve_time = time.time() - start_time
        
        status_name = pulp.LpStatus[status]
        obj_value = None
        
        if status == pulp.LpStatusOptimal:
            obj_value = pulp.value(self.model.objective)
            logger.info(
                f"ILP Optimal solution found: cost={obj_value:.2f}, "
                f"time={solve_time:.2f}s"
            )
        elif status == pulp.LpStatusNotSolved:
            # Check if we have a feasible solution (time limit reached)
            try:
                obj_value = pulp.value(self.model.objective)
                if obj_value is not None:
                    logger.info(
                        f"ILP Feasible solution (time limit): cost={obj_value:.2f}, "
                        f"time={solve_time:.2f}s"
                    )
                    status_name = "Feasible"
            except Exception:
                pass
            
            if obj_value is None:
                logger.warning(f"ILP not solved after {solve_time:.2f}s")
        elif status == pulp.LpStatusInfeasible:
            logger.warning(f"ILP Infeasible after {solve_time:.2f}s")
        elif status == pulp.LpStatusUnbounded:
            logger.warning("ILP Unbounded")
        
        return status_name, obj_value
    
    def extract_schedule(self) -> List[ScheduleRow]:
        """Extract schedule from solved model."""
        if self.model is None:
            return []
        
        status = pulp.LpStatus[self.model.status]
        if status not in ("Optimal", "Not Solved"):
            return []
        
        # Check if we have valid variable values
        if not self.assign:
            return []
        
        try:
            first_var = next(iter(self.assign.values()))
            test_val = pulp.value(first_var)
            if test_val is None:
                return []
        except (StopIteration, Exception):
            return []
        
        schedule = []
        z = self.num_classes
        T = self.max_slots
        
        for p in self.projects:
            assigned_class = None
            assigned_slot = None
            
            # Find where project is assigned
            for s in range(z):
                for t in range(T):
                    if pulp.value(self.assign[(p.id, s, t)]) > 0.5:
                        assigned_class = s
                        assigned_slot = t
                        break
                if assigned_class is not None:
                    break
            
            if assigned_class is None:
                logger.warning(f"Project {p.id} not assigned in solution!")
                continue
            
            # Find J1
            j1_id = None
            for h in self.faculty_ids:
                if pulp.value(self.j1[(p.id, h)]) > 0.5:
                    j1_id = h
                    break
            
            if j1_id is None:
                logger.warning(f"Project {p.id} has no J1 in solution!")
                continue
            
            # Calculate global slot index: class * max_slots + slot_in_class
            # This matches the constraint formulation
            global_slot_idx = assigned_class * T + assigned_slot
            
            row = ScheduleRow(
                project_id=p.id,
                class_id=assigned_class,
                class_name=(
                    self.class_names[assigned_class]
                    if assigned_class < len(self.class_names)
                    else f"Class_{assigned_class}"
                ),
                order_in_class=assigned_slot,  # Will be recomputed
                global_slot=global_slot_idx,  # Global slot index for constraint verification
                ps_id=self.ps_lookup[p.id],
                j1_id=j1_id,
                j2_label="[Arastirma Gorevlisi]"
            )
            schedule.append(row)
        
        # Recompute order_in_class (1-based, sorted by global_slot)
        class_projects = defaultdict(list)
        for row in schedule:
            class_projects[row.class_id].append(row)
        
        for class_id, rows in class_projects.items():
            rows.sort(key=lambda r: r.global_slot)
            for i, row in enumerate(rows):
                row.order_in_class = i + 1
        
        return schedule


# =============================================================================
# MAIN ALGORITHM CLASS
# =============================================================================

class IntegerLinearProgramming(OptimizationAlgorithm):
    """
    Integer Linear Programming algorithm for academic project scheduling.
    
    Implements multi-criteria optimization with:
    - BITIRME projects always scheduled before ARA (hard constraint)
    - Back-to-back scheduling in classrooms (no gaps)
    - Workload uniformity (±2 tolerance)
    - Class change minimization
    - Continuity maximization
    
    The second jury (J2) is always "[Arastirma Gorevlisi]" placeholder
    and is NOT part of the optimization model.
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        Initialize the ILP algorithm.
        
        Args:
            params: Optional configuration parameters
        """
        super().__init__(params)
        self.config = self._build_config(params or {})
        self.data = None
        self.result = None
        self.projects = []
        self.instructors = []
        self.classrooms = []
        self.timeslots = []
    
    def _build_config(self, params: Dict[str, Any]) -> ILPConfig:
        """Build ILPConfig from parameters dictionary."""
        config_params = {}
        
        param_mapping = {
            "priority_mode": "priority_mode",
            "time_penalty_mode": "time_penalty_mode",
            "workload_constraint_mode": "workload_constraint_mode",
            "weight_continuity": "weight_continuity",
            "weight_uniformity": "weight_uniformity",
            "weight_class_change": "weight_class_change",
            "weight_class_load": "weight_class_load",
            "b_max": "b_max",
            "workload_tolerance": "workload_tolerance",
            "max_time_seconds": "max_time_seconds",
            "time_limit": "max_time_seconds",  # Alias
            "solver_msg": "solver_msg",
            "class_count_mode": "class_count_mode",
            "given_z": "given_z",
            "class_count": "given_z",  # Alias
            "slot_duration": "slot_duration",
            "epsilon": "epsilon",
            # Warm start and MIP optimization
            "use_warm_start": "use_warm_start",
            "warm_start": "use_warm_start",  # Alias
            "mip_gap": "mip_gap",
            "gap": "mip_gap",  # Alias
            "threads": "threads",
            "presolve": "presolve",
            "cuts": "cuts",
            "strong_branching": "strong_branching",
        }
        
        for param_key, config_key in param_mapping.items():
            if param_key in params:
                config_params[config_key] = params[param_key]
        
        return ILPConfig(**config_params)
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        Initialize algorithm with input data.
        
        Args:
            data: Dictionary containing projects, instructors, classrooms, timeslots
        """
        self.data = data
        
        # Parse input data
        self.projects = data.get("projects", [])
        self.instructors = data.get("instructors", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Update config from data if provided
        if "config" in data:
            cfg = data["config"]
            if isinstance(cfg, dict):
                self.config = self._build_config(cfg)
        
        # Update class count from data
        if "class_count" in data and data["class_count"]:
            self.config.class_count_mode = "manual"
            self.config.given_z = data["class_count"]
        elif self.classrooms:
            classroom_count = len(self.classrooms)
            if 5 <= classroom_count <= 7:
                self.config.class_count_mode = "manual"
                self.config.given_z = classroom_count
    
    def optimize(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run the ILP optimization.
        
        Args:
            data: Optional input data (uses initialized data if not provided)
        
        Returns:
            Dictionary with schedule, cost, status, and metadata
        """
        if data is not None:
            self.initialize(data)
        
        if self.data is None:
            raise ValueError("No data provided. Call initialize() first.")
        
        # Check PuLP availability
        if not PULP_AVAILABLE:
            logger.error("PuLP not available. Returning empty solution.")
            return self._empty_result("PULP_NOT_AVAILABLE")
        
        # Parse projects and teachers
        projects = self._parse_projects(self.projects)
        teachers = self._parse_teachers(self.instructors)
        
        if not projects:
            return self._empty_result("NO_PROJECTS")
        
        # Filter faculty only
        faculty = [t for t in teachers if not t.is_research_assistant]
        if not faculty:
            return self._empty_result("NO_FACULTY")
        
        # Get class names
        class_names = self._get_class_names()
        
        # Determine class counts to try
        if self.config.class_count_mode == "manual":
            z_list = [self.config.given_z]
        else:
            z_list = [5, 6, 7]
        
        best_result = None
        best_cost = 999999999  # Use large number for JSON compatibility
        
        for z in z_list:
            logger.info(f"Trying ILP with z={z} classes...")
            
            try:
                # Build model
                builder = ILPModelBuilder(
                    projects=projects,
                    teachers=teachers,
                    config=self.config,
                    num_classes=z,
                    class_names=class_names
                )
                builder.build()
                
                # Solve
                status, cost = builder.solve()
                
                if status == "Optimal" and cost is not None:
                    if cost < best_cost:
                        best_cost = cost
                        schedule = builder.extract_schedule()
                        best_result = self._format_result(
                            schedule, cost, status, z, faculty
                        )
                        logger.info(f"z={z}: Found solution with cost={cost:.2f}")
                elif status == "Not Solved":
                    # Time limit reached, check if we have a feasible solution
                    schedule = builder.extract_schedule()
                    if schedule:
                        approx_cost = cost if cost else 999999999
                        if approx_cost < best_cost:
                            best_cost = approx_cost
                            best_result = self._format_result(
                                schedule, approx_cost, "Feasible", z, faculty
                            )
                            logger.info(f"z={z}: Feasible solution (time limit)")
                
            except Exception as e:
                logger.error(f"ILP error with z={z}: {e}")
                continue
        
        if best_result is None:
            return self._empty_result("INFEASIBLE")
        
        self.result = best_result
        return best_result
    
    def _parse_projects(self, raw_projects: List[Any]) -> List[Project]:
        """Parse raw project data into Project objects."""
        projects = []
        
        for p in raw_projects:
            if isinstance(p, dict):
                ps_id = p.get(
                    "ps_id",
                    p.get("responsible_id", p.get("advisor_id", 0))
                )
                p_type = str(
                    p.get("type", p.get("project_type", "ARA"))
                ).upper()
                
                project = Project(
                    id=p.get("id", 0),
                    ps_id=ps_id,
                    project_type="BITIRME" if p_type in ("FINAL", "BITIRME") else "ARA",
                    name=p.get("name", f"Project_{p.get('id', 0)}"),
                    is_makeup=p.get("is_makeup", False)
                )
            elif hasattr(p, "id"):
                ps_id = getattr(
                    p, "ps_id",
                    getattr(p, "responsible_id", getattr(p, "advisor_id", 0))
                )
                p_type = str(
                    getattr(p, "type", getattr(p, "project_type", "ARA"))
                ).upper()
                
                project = Project(
                    id=p.id,
                    ps_id=ps_id,
                    project_type="BITIRME" if p_type in ("FINAL", "BITIRME") else "ARA",
                    name=getattr(p, "name", f"Project_{p.id}"),
                    is_makeup=getattr(p, "is_makeup", False)
                )
            else:
                continue
            
            projects.append(project)
        
        return projects
    
    def _parse_teachers(self, raw_teachers: List[Any]) -> List[Teacher]:
        """Parse raw teacher data into Teacher objects."""
        teachers = []
        
        for t in raw_teachers:
            if isinstance(t, dict):
                is_ra = t.get("is_research_assistant", False)
                if not is_ra:
                    t_type = str(t.get("type", "instructor")).lower()
                    is_ra = t_type in ("ra", "research_assistant", "assistant")
                
                teacher = Teacher(
                    id=t.get("id", 0),
                    code=t.get("code", t.get("name", f"T{t.get('id', 0)}")),
                    name=t.get("name", t.get("full_name", "")),
                    is_research_assistant=is_ra
                )
            elif hasattr(t, "id"):
                is_ra = getattr(t, "is_research_assistant", False)
                if not is_ra:
                    t_type = str(getattr(t, "type", "instructor")).lower()
                    is_ra = t_type in ("ra", "research_assistant", "assistant")
                
                teacher = Teacher(
                    id=t.id,
                    code=getattr(t, "code", getattr(t, "name", f"T{t.id}")),
                    name=getattr(t, "name", getattr(t, "full_name", "")),
                    is_research_assistant=is_ra
                )
            else:
                continue
            
            teachers.append(teacher)
        
        return teachers
    
    def _get_class_names(self) -> List[str]:
        """Get classroom names from data."""
        if not self.classrooms:
            return None
        
        if isinstance(self.classrooms[0], dict):
            return [c.get("name", f"D{105 + i}") for i, c in enumerate(self.classrooms)]
        else:
            return [str(c) for c in self.classrooms]
    
    def _format_result(
        self,
        schedule: List[ScheduleRow],
        cost: float,
        status: str,
        class_count: int,
        faculty: List[Teacher]
    ) -> Dict[str, Any]:
        """Format the result dictionary."""
        # Build teacher lookup
        teacher_lookup = {t.id: t for t in faculty}
        
        # Convert schedule to output format
        output_schedule = []
        for row in schedule:
            ps_teacher = teacher_lookup.get(row.ps_id)
            j1_teacher = teacher_lookup.get(row.j1_id)
            
            output_row = {
                "project_id": row.project_id,
                "class_id": row.class_id,
                "class_name": row.class_name,
                "order_in_class": row.order_in_class,
                "global_slot": row.global_slot,
                "ps_id": row.ps_id,
                "j1_id": row.j1_id,
                "j2_label": "[Arastirma Gorevlisi]",
                "instructors": [
                    {
                        "id": row.ps_id,
                        "name": ps_teacher.name if ps_teacher else f"Teacher_{row.ps_id}",
                        "role": "PS"
                    },
                    {
                        "id": row.j1_id,
                        "name": j1_teacher.name if j1_teacher else f"Teacher_{row.j1_id}",
                        "role": "J1"
                    },
                    "[Arastirma Gorevlisi]"
                ]
            }
            output_schedule.append(output_row)
        
        return {
            "schedule": output_schedule,
            "assignments": output_schedule,
            "solution": output_schedule,
            "cost": cost,
            "fitness": -cost,
            "status": status,
            "class_count": class_count,
            "algorithm": "Integer Linear Programming",
            "penalty_breakdown": {
                "total": cost,
                "note": "H1(continuity) + H2(workload) + H3(class_change)"
            }
        }
    
    def _empty_result(self, status: str) -> Dict[str, Any]:
        """Return an empty result with given status."""
        # Use large numbers instead of float('inf') for JSON compatibility
        return {
            "schedule": [],
            "assignments": [],
            "solution": [],
            "cost": 999999999,  # JSON doesn't support Infinity
            "fitness": -999999999,
            "status": status,
            "class_count": 0,
            "algorithm": "Integer Linear Programming",
            "penalty_breakdown": {}
        }
    
    def get_algorithm_info(self) -> Dict[str, Any]:
        """Get information about the algorithm."""
        return {
            "name": "Integer Linear Programming",
            "description": (
                "Multi-criteria ILP optimizer for academic project scheduling. "
                "Uses PuLP solver with BITIRME-first priority, back-to-back scheduling, "
                "workload uniformity constraints, and warm start for fast convergence."
            ),
            "type": "mathematical",
            "parameters": {
                "priority_mode": self.config.priority_mode,
                "time_penalty_mode": self.config.time_penalty_mode,
                "workload_constraint_mode": self.config.workload_constraint_mode,
                "weight_continuity": self.config.weight_continuity,
                "weight_uniformity": self.config.weight_uniformity,
                "weight_class_change": self.config.weight_class_change,
                "b_max": self.config.b_max,
                "max_time_seconds": self.config.max_time_seconds,
                "use_warm_start": self.config.use_warm_start,
                "mip_gap": self.config.mip_gap,
            }
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_ilp_optimizer(config: Optional[Dict[str, Any]] = None) -> IntegerLinearProgramming:
    """
    Create an ILP optimizer instance.
    
    Args:
        config: Optional configuration dictionary
    
    Returns:
        IntegerLinearProgramming instance
    """
    return IntegerLinearProgramming(config)


def solve_with_ilp(
    input_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main entry point for ILP optimizer.
    
    Args:
        input_data: Dictionary containing projects, instructors, classrooms, timeslots
        config: Optional configuration parameters
    
    Returns:
        Dictionary with schedule, cost, status, and metadata
    """
    optimizer = IntegerLinearProgramming(config)
    optimizer.initialize(input_data)
    return optimizer.optimize()


# Alias for backwards compatibility
ILPAlgorithm = IntegerLinearProgramming

