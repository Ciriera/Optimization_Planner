"""
CP-SAT based optimizer for academic project exam/jury planning.

This module implements a Constraint Programming (CP-SAT) solver using Google OR-Tools
for multi-criteria, highly constrained academic project scheduling.

Key Features:
- Project-class-slot assignment optimization
- First Jury (J1) assignment as decision variable
- Second Jury (J2) is a fixed placeholder "[Arastirma Gorevlisi]" - NOT in model
- Multi-criteria objective: workload uniformity, continuity, class changes
- Configurable priority modes, penalty modes, and constraint modes
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import logging
import math

from ortools.sat.python import cp_model

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND CONFIGURATION
# =============================================================================

class PriorityMode(Enum):
    """Project type prioritization mode."""
    ARA_ONCE = "ARA_ONCE"           # All ARA projects before BITIRME
    BITIRME_ONCE = "BITIRME_ONCE"   # All BITIRME projects before ARA
    ESIT = "ESIT"                   # No priority ordering


class TimePenaltyMode(Enum):
    """Time/gap penalty calculation mode."""
    BINARY = "BINARY"                     # 1 if not consecutive, 0 otherwise
    GAP_PROPORTIONAL = "GAP_PROPORTIONAL" # Penalty = number of gap slots


class WorkloadConstraintMode(Enum):
    """Workload constraint mode."""
    SOFT_ONLY = "SOFT_ONLY"           # Only soft penalty, no hard limit
    SOFT_AND_HARD = "SOFT_AND_HARD"   # Soft penalty + hard upper bound


@dataclass
class CPSATConfig:
    """Configuration for CP-SAT solver."""
    
    # Priority mode
    priority_mode: str = "ESIT"
    
    # Penalty modes
    time_penalty_mode: str = "BINARY"
    workload_constraint_mode: str = "SOFT_ONLY"
    
    # Weights for objective function (C2 > C1 and C2 > C3)
    weight_continuity: int = 10      # C1 - for gap/continuity penalty
    weight_uniformity: int = 100     # C2 - for workload uniformity (most important)
    weight_class_change: int = 5     # C3 - for class change penalty
    weight_class_load: int = 2       # C4 - for class load balancing
    
    # Hard constraint parameters
    b_max: int = 4  # Maximum allowed deviation from average workload
    
    # Solver parameters
    max_time_seconds: int = 120
    num_search_workers: int = 8
    log_search_progress: bool = True
    
    # Class count mode
    class_count_mode: str = "auto"  # "auto" or "manual"
    given_z: int = 6                # Used if class_count_mode == "manual"
    
    # Gap penalty multiplier for GAP_PROPORTIONAL mode
    gap_penalty_multiplier: int = 2


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
    j2_label: str = "[Arastirma Gorevlisi]"  # Fixed placeholder


@dataclass
class ModelMapping:
    """Holds references to CP-SAT model variables for extraction."""
    
    # Decision variables
    assign: Dict[Tuple[int, int, int], Any] = field(default_factory=dict)  # [p, s, t]
    j1: Dict[Tuple[int, int], Any] = field(default_factory=dict)           # [p, h]
    
    # Derived variables
    active: Dict[Tuple[int, int, int], Any] = field(default_factory=dict)  # [h, s, t]
    slot_used: Dict[Tuple[int, int], Any] = field(default_factory=dict)    # [s, t]
    load: Dict[int, Any] = field(default_factory=dict)                     # [h]
    class_used: Dict[Tuple[int, int], Any] = field(default_factory=dict)   # [h, s]
    
    # Penalty variables
    dev: Dict[int, Any] = field(default_factory=dict)                      # [h]
    class_change_excess: Dict[int, Any] = field(default_factory=dict)      # [h]
    cont_excess: Dict[Tuple[int, int], Any] = field(default_factory=dict)  # [h, s]
    class_load_dev: Dict[int, Any] = field(default_factory=dict)           # [s]
    
    # Metadata
    projects: List[Project] = field(default_factory=list)
    teachers: List[Teacher] = field(default_factory=list)
    faculty_ids: List[int] = field(default_factory=list)
    num_classes: int = 0
    num_slots: int = 0
    class_names: List[str] = field(default_factory=list)


# =============================================================================
# MODEL BUILDING
# =============================================================================

def build_cp_sat_model(
    projects: List[Project],
    teachers: List[Teacher],
    config: CPSATConfig,
    num_classes: int,
    class_names: Optional[List[str]] = None
) -> Tuple[cp_model.CpModel, ModelMapping]:
    """
    Build the CP-SAT model with all decision variables and constraints.
    
    Args:
        projects: List of projects to schedule
        teachers: List of teachers (faculty only, no RAs)
        config: Configuration parameters
        num_classes: Number of classes (z)
        class_names: Optional class names
    
    Returns:
        Tuple of (CpModel, ModelMapping)
    """
    model = cp_model.CpModel()
    mapping = ModelMapping()
    
    # Filter out research assistants - they are NOT part of the model
    faculty = [t for t in teachers if not t.is_research_assistant]
    faculty_ids = [t.id for t in faculty]
    
    mapping.projects = projects
    mapping.teachers = faculty
    mapping.faculty_ids = faculty_ids
    mapping.num_classes = num_classes
    
    # Generate class names if not provided
    if class_names:
        mapping.class_names = class_names[:num_classes]
    else:
        mapping.class_names = [f"D{105 + i}" for i in range(num_classes)]
    
    Y = len(projects)  # Number of projects
    X = len(faculty)   # Number of real faculty members
    z = num_classes    # Number of classes
    
    # Calculate max slots per class (safe upper bound)
    T = math.ceil(Y / z) + 5  # Extra buffer for flexibility
    mapping.num_slots = T
    
    logger.info(f"Building CP-SAT model: {Y} projects, {X} faculty, {z} classes, {T} max slots")
    
    # Create PS lookup
    ps_lookup = {p.id: p.ps_id for p in projects}
    
    # =========================================================================
    # DECISION VARIABLES
    # =========================================================================
    
    # 3.1 Project -> class & slot assignment: assign[p, s, t]
    for p in projects:
        for s in range(z):
            for t in range(T):
                var_name = f"assign_p{p.id}_s{s}_t{t}"
                mapping.assign[(p.id, s, t)] = model.NewBoolVar(var_name)
    
    # 3.2 First Jury assignment: j1[p, h]
    for p in projects:
        for h in faculty_ids:
            var_name = f"j1_p{p.id}_h{h}"
            mapping.j1[(p.id, h)] = model.NewBoolVar(var_name)
    
    # 3.3 Slot usage: slot_used[s, t]
    for s in range(z):
        for t in range(T):
            var_name = f"slot_used_s{s}_t{t}"
            mapping.slot_used[(s, t)] = model.NewBoolVar(var_name)
    
    # 3.4 Teacher activity: active[h, s, t]
    for h in faculty_ids:
        for s in range(z):
            for t in range(T):
                var_name = f"active_h{h}_s{s}_t{t}"
                mapping.active[(h, s, t)] = model.NewBoolVar(var_name)
    
    # 3.5 Workload: load[h]
    max_possible_load = 2 * Y  # Upper bound
    for h in faculty_ids:
        var_name = f"load_h{h}"
        mapping.load[h] = model.NewIntVar(0, max_possible_load, var_name)
    
    # 3.6 Class usage per teacher: class_used[h, s]
    for h in faculty_ids:
        for s in range(z):
            var_name = f"class_used_h{h}_s{s}"
            mapping.class_used[(h, s)] = model.NewBoolVar(var_name)
    
    # 3.7 Deviation from average workload: dev[h]
    for h in faculty_ids:
        var_name = f"dev_h{h}"
        mapping.dev[h] = model.NewIntVar(0, max_possible_load, var_name)
    
    # 3.8 Class change excess: class_change_excess[h]
    for h in faculty_ids:
        var_name = f"class_change_excess_h{h}"
        mapping.class_change_excess[h] = model.NewIntVar(0, z, var_name)
    
    # 3.9 Continuity excess per (teacher, class): cont_excess[h, s]
    for h in faculty_ids:
        for s in range(z):
            var_name = f"cont_excess_h{h}_s{s}"
            mapping.cont_excess[(h, s)] = model.NewIntVar(0, T, var_name)
    
    # 3.10 Class load deviation: class_load_dev[s]
    for s in range(z):
        var_name = f"class_load_dev_s{s}"
        mapping.class_load_dev[s] = model.NewIntVar(0, 2 * Y, var_name)
    
    # =========================================================================
    # HARD CONSTRAINTS
    # =========================================================================
    
    # 4.1 Each project assigned exactly once
    for p in projects:
        model.AddExactlyOne([
            mapping.assign[(p.id, s, t)]
            for s in range(z)
            for t in range(T)
        ])
    
    # 4.2 At most one project per class-slot
    for s in range(z):
        for t in range(T):
            model.Add(
                sum(mapping.assign[(p.id, s, t)] for p in projects) <= 1
            )
    
    # 4.3 Link slot_used to assign
    for s in range(z):
        for t in range(T):
            # slot_used[s,t] >= assign[p,s,t] for all p
            for p in projects:
                model.Add(
                    mapping.slot_used[(s, t)] >= mapping.assign[(p.id, s, t)]
                )
            # slot_used[s,t] <= sum_p assign[p,s,t]
            model.Add(
                mapping.slot_used[(s, t)] <= sum(
                    mapping.assign[(p.id, s, t)] for p in projects
                )
            )
    
    # 4.4 Back-to-back: no gaps in class schedule
    # used[s, t-1] >= used[s, t] for t > 0
    for s in range(z):
        for t in range(1, T):
            model.Add(
                mapping.slot_used[(s, t - 1)] >= mapping.slot_used[(s, t)]
            )
    
    # 4.5 Teacher cannot be J1 on their own project
    for p in projects:
        ps_id = ps_lookup[p.id]
        if ps_id in faculty_ids:
            model.Add(mapping.j1[(p.id, ps_id)] == 0)
    
    # 4.6 Exactly one J1 per project
    for p in projects:
        model.AddExactlyOne([
            mapping.j1[(p.id, h)] for h in faculty_ids
        ])
    
    # 4.7 Link active[h,s,t] to assignments
    for h in faculty_ids:
        for s in range(z):
            for t in range(T):
                # Build list of projects where h is PS
                ps_projects = [p for p in projects if ps_lookup[p.id] == h]
                
                # active >= assign * is_ps
                for p in ps_projects:
                    model.Add(
                        mapping.active[(h, s, t)] >= mapping.assign[(p.id, s, t)]
                    )
                
                # active >= assign * j1[p,h]
                for p in projects:
                    # Use implication: if assign[p,s,t] AND j1[p,h] then active[h,s,t]
                    b = model.NewBoolVar(f"j1_active_p{p.id}_h{h}_s{s}_t{t}")
                    model.AddMultiplicationEquality(
                        b, [mapping.assign[(p.id, s, t)], mapping.j1[(p.id, h)]]
                    )
                    model.Add(mapping.active[(h, s, t)] >= b)
                
                # active <= sum of all ways h can be active at (s,t)
                ps_contributions = [
                    mapping.assign[(p.id, s, t)] for p in ps_projects
                ]
                j1_contributions = []
                for p in projects:
                    b = model.NewBoolVar(f"j1_contrib_p{p.id}_h{h}_s{s}_t{t}")
                    model.AddMultiplicationEquality(
                        b, [mapping.assign[(p.id, s, t)], mapping.j1[(p.id, h)]]
                    )
                    j1_contributions.append(b)
                
                all_contributions = ps_contributions + j1_contributions
                if all_contributions:
                    model.Add(
                        mapping.active[(h, s, t)] <= sum(all_contributions)
                    )
                else:
                    model.Add(mapping.active[(h, s, t)] == 0)
    
    # 4.8 Max one duty per teacher per timeslot (across all classes)
    for h in faculty_ids:
        for t in range(T):
            model.Add(
                sum(mapping.active[(h, s, t)] for s in range(z)) <= 1
            )
    
    # 4.9 Workload calculation: load[h] = PS duties + J1 duties
    for h in faculty_ids:
        ps_count = sum(
            1 for p in projects if ps_lookup[p.id] == h
        )
        j1_sum = sum(mapping.j1[(p.id, h)] for p in projects)
        model.Add(mapping.load[h] == ps_count + j1_sum)
    
    # 4.10 Link class_used[h,s]
    for h in faculty_ids:
        for s in range(z):
            # class_used >= active for any t
            for t in range(T):
                model.Add(
                    mapping.class_used[(h, s)] >= mapping.active[(h, s, t)]
                )
            # class_used <= sum of active
            model.Add(
                mapping.class_used[(h, s)] <= sum(
                    mapping.active[(h, s, t)] for t in range(T)
                )
            )
    
    # 4.11 Project type priority constraints
    _add_priority_constraints(model, mapping, projects, config, z, T)
    
    # 4.12 Hard workload bounds (if SOFT_AND_HARD mode)
    _add_workload_hard_constraints(model, mapping, projects, faculty_ids, config)
    
    # =========================================================================
    # SOFT PENALTY VARIABLES
    # =========================================================================
    
    # Calculate average workload
    avg_load = (2 * Y) / X if X > 0 else 0
    avg_load_floor = int(math.floor(avg_load))
    avg_load_ceil = int(math.ceil(avg_load))
    
    # 5.1 Workload deviation penalty: dev[h] >= |load[h] - avg| - 2
    for h in faculty_ids:
        # dev[h] >= load[h] - (avg + 2)
        model.Add(mapping.dev[h] >= mapping.load[h] - (avg_load_ceil + 2))
        # dev[h] >= (avg - 2) - load[h]
        model.Add(mapping.dev[h] >= (avg_load_floor - 2) - mapping.load[h])
        # dev[h] >= 0 (already in domain)
    
    # 5.2 Class change excess: class_change_excess[h] >= class_count[h] - 2
    for h in faculty_ids:
        class_count = sum(mapping.class_used[(h, s)] for s in range(z))
        model.Add(mapping.class_change_excess[h] >= class_count - 2)
    
    # 5.3 Continuity penalty (block counting)
    _add_continuity_constraints(model, mapping, faculty_ids, z, T)
    
    # 5.4 Class load deviation
    target_class_load = (2 * Y) / z if z > 0 else 0
    target_floor = int(math.floor(target_class_load))
    target_ceil = int(math.ceil(target_class_load))
    
    for s in range(z):
        class_project_count = sum(
            mapping.assign[(p.id, s, t)]
            for p in projects
            for t in range(T)
        )
        class_load = 2 * class_project_count  # 2 duties per project (PS + J1)
        
        # Auxiliary variable for class_load
        class_load_var = model.NewIntVar(0, 2 * Y, f"class_load_s{s}")
        model.Add(class_load_var == class_load)
        
        # class_load_dev >= |class_load - target|
        model.Add(mapping.class_load_dev[s] >= class_load_var - target_ceil)
        model.Add(mapping.class_load_dev[s] >= target_floor - class_load_var)
    
    # =========================================================================
    # OBJECTIVE FUNCTION
    # =========================================================================
    
    # H1: Continuity penalty
    H1 = sum(mapping.cont_excess[(h, s)] for h in faculty_ids for s in range(z))
    
    # H2: Workload uniformity penalty
    H2 = sum(mapping.dev[h] for h in faculty_ids)
    
    # H3: Class change penalty
    H3 = sum(mapping.class_change_excess[h] for h in faculty_ids)
    
    # H4: Class load balancing penalty
    H4 = sum(mapping.class_load_dev[s] for s in range(z))
    
    # Weighted objective
    objective = (
        config.weight_continuity * H1 +
        config.weight_uniformity * H2 +
        config.weight_class_change * H3 +
        config.weight_class_load * H4
    )
    
    model.Minimize(objective)
    
    return model, mapping


def _add_priority_constraints(
    model: cp_model.CpModel,
    mapping: ModelMapping,
    projects: List[Project],
    config: CPSATConfig,
    z: int,
    T: int
) -> None:
    """Add project type priority constraints based on config."""
    
    priority_mode = config.priority_mode
    
    if priority_mode == "ESIT":
        # No priority constraints
        return
    
    # Create slot variables for each project
    slot_vars = {}
    for p in projects:
        slot_var = model.NewIntVar(0, T - 1, f"slot_p{p.id}")
        slot_vars[p.id] = slot_var
        
        # Link slot_var to assign variables
        # slot_var = sum over all (s,t) of t * assign[p,s,t]
        terms = []
        for s in range(z):
            for t in range(T):
                terms.append(t * mapping.assign[(p.id, s, t)])
        model.Add(slot_var == sum(terms))
    
    # Separate projects by type (case-insensitive)
    ara_projects = [p for p in projects if str(p.project_type).upper() in ("ARA", "INTERIM")]
    bitirme_projects = [p for p in projects if str(p.project_type).upper() in ("BITIRME", "FINAL")]
    
    logger.info(f"CP-SAT: Priority constraints - mode={priority_mode}, ara={len(ara_projects)}, bitirme={len(bitirme_projects)}")
    
    if priority_mode == "ARA_ONCE":
        # All ARA projects before all BITIRME projects
        for p_ara in ara_projects:
            for p_bit in bitirme_projects:
                model.Add(slot_vars[p_ara.id] <= slot_vars[p_bit.id])
        logger.info(f"CP-SAT: Added {len(ara_projects) * len(bitirme_projects)} ARA_ONCE priority constraints")
    
    elif priority_mode == "BITIRME_ONCE":
        # All BITIRME projects before all ARA projects
        for p_bit in bitirme_projects:
            for p_ara in ara_projects:
                model.Add(slot_vars[p_bit.id] <= slot_vars[p_ara.id])
        logger.info(f"CP-SAT: Added {len(ara_projects) * len(bitirme_projects)} BITIRME_ONCE priority constraints")


def _add_workload_hard_constraints(
    model: cp_model.CpModel,
    mapping: ModelMapping,
    projects: List[Project],
    faculty_ids: List[int],
    config: CPSATConfig
) -> None:
    """Add hard workload constraints if mode is SOFT_AND_HARD."""
    
    if config.workload_constraint_mode != "SOFT_AND_HARD":
        return
    
    Y = len(projects)
    X = len(faculty_ids)
    
    if X == 0:
        return
    
    avg_load = (2 * Y) / X
    b_max = config.b_max
    
    avg_floor = int(math.floor(avg_load))
    avg_ceil = int(math.ceil(avg_load))
    
    for h in faculty_ids:
        # load[h] - avg <= b_max
        model.Add(mapping.load[h] <= avg_ceil + b_max)
        # avg - load[h] <= b_max
        model.Add(mapping.load[h] >= avg_floor - b_max)


def _add_continuity_constraints(
    model: cp_model.CpModel,
    mapping: ModelMapping,
    faculty_ids: List[int],
    z: int,
    T: int
) -> None:
    """Add continuity/block counting constraints."""
    
    # For each (teacher, class), count number of blocks
    # A block starts when active goes from 0 to 1
    
    for h in faculty_ids:
        for s in range(z):
            # Block start at t=0
            block_start_0 = mapping.active[(h, s, 0)]
            
            # Block starts at t>0
            block_starts = [block_start_0]
            
            for t in range(1, T):
                # block_start[t] = active[t] AND NOT active[t-1]
                block_start_t = model.NewBoolVar(f"block_start_h{h}_s{s}_t{t}")
                
                # block_start >= active[t] - active[t-1]
                model.Add(
                    block_start_t >= 
                    mapping.active[(h, s, t)] - mapping.active[(h, s, t - 1)]
                )
                # block_start <= active[t]
                model.Add(block_start_t <= mapping.active[(h, s, t)])
                # block_start <= 1 - active[t-1]
                model.Add(block_start_t <= 1 - mapping.active[(h, s, t - 1)])
                
                block_starts.append(block_start_t)
            
            # Total blocks = sum of block starts
            total_blocks = model.NewIntVar(0, T, f"total_blocks_h{h}_s{s}")
            model.Add(total_blocks == sum(block_starts))
            
            # cont_excess >= blocks - 1 (penalty for having more than 1 block)
            model.Add(mapping.cont_excess[(h, s)] >= total_blocks - 1)


# =============================================================================
# SOLUTION EXTRACTION
# =============================================================================

def extract_schedule(
    solver: cp_model.CpSolver,
    mapping: ModelMapping
) -> List[ScheduleRow]:
    """
    Extract schedule from solved model.
    
    Args:
        solver: Solved CP-SAT solver
        mapping: Model variable mapping
    
    Returns:
        List of ScheduleRow objects
    """
    schedule = []
    
    projects = mapping.projects
    faculty_ids = mapping.faculty_ids
    z = mapping.num_classes
    T = mapping.num_slots
    class_names = mapping.class_names
    
    # Build PS lookup
    ps_lookup = {p.id: p.ps_id for p in projects}
    
    # Extract assignments
    for p in projects:
        assigned_class = None
        assigned_slot = None
        
        # Find where project is assigned
        for s in range(z):
            for t in range(T):
                if solver.Value(mapping.assign[(p.id, s, t)]) == 1:
                    assigned_class = s
                    assigned_slot = t
                    break
            if assigned_class is not None:
                break
        
        if assigned_class is None:
            logger.warning(f"Project {p.id} not assigned!")
            continue
        
        # Find J1
        j1_id = None
        for h in faculty_ids:
            if solver.Value(mapping.j1[(p.id, h)]) == 1:
                j1_id = h
                break
        
        if j1_id is None:
            logger.warning(f"Project {p.id} has no J1 assigned!")
            continue
        
        row = ScheduleRow(
            project_id=p.id,
            class_id=assigned_class,
            class_name=class_names[assigned_class] if assigned_class < len(class_names) else f"Class_{assigned_class}",
            order_in_class=assigned_slot,  # Will be recomputed
            global_slot=assigned_slot,
            ps_id=ps_lookup[p.id],
            j1_id=j1_id,
            j2_label="[Arastirma Gorevlisi]"  # Fixed placeholder - NOT in model
        )
        schedule.append(row)
    
    # Recompute order_in_class (1-based, sorted by global_slot within each class)
    class_projects = {}
    for row in schedule:
        if row.class_id not in class_projects:
            class_projects[row.class_id] = []
        class_projects[row.class_id].append(row)
    
    for class_id, rows in class_projects.items():
        rows.sort(key=lambda r: r.global_slot)
        for i, row in enumerate(rows):
            row.order_in_class = i + 1  # 1-based
    
    return schedule


# =============================================================================
# MAIN SOLVER FUNCTION
# =============================================================================

def solve_with_cp_sat(
    input_data: Dict[str, Any],
    config: Optional[CPSATConfig] = None
) -> Dict[str, Any]:
    """
    Main entry point for CP-SAT optimizer.
    
    Args:
        input_data: Dictionary containing:
            - projects: List of project dicts with id, ps_id, type
            - teachers: List of teacher dicts with id, code, is_research_assistant
            - classrooms: Optional list of classroom names
        config: Optional CPSATConfig object
    
    Returns:
        Dictionary with schedule, cost, status, and metadata
    """
    if config is None:
        config = CPSATConfig()
    
    # Parse input data
    projects = _parse_projects(input_data.get("projects", []))
    teachers = _parse_teachers(input_data.get("teachers", input_data.get("instructors", [])))
    classrooms = input_data.get("classrooms", [])
    
    # Filter out research assistants
    faculty = [t for t in teachers if not t.is_research_assistant]
    
    if not projects:
        logger.warning("No projects to schedule")
        return {
            "schedule": [],
            "cost": 0,
            "status": "NO_PROJECTS",
            "class_count": 0
        }
    
    if not faculty:
        logger.warning("No faculty members available")
        return {
            "schedule": [],
            "cost": 0,
            "status": "NO_FACULTY",
            "class_count": 0
        }
    
    # Determine class names
    class_names = None
    if classrooms:
        if isinstance(classrooms[0], dict):
            class_names = [c.get("name", f"D{105 + i}") for i, c in enumerate(classrooms)]
        else:
            class_names = [str(c) for c in classrooms]
    
    # Determine which z values to try
    if config.class_count_mode == "manual":
        z_list = [config.given_z]
    else:
        # Auto mode: try z in {5, 6, 7}
        z_list = [5, 6, 7]
    
    best_solution = None
    best_cost = None
    best_z = None
    best_status = None
    
    for z in z_list:
        logger.info(f"Trying z = {z} classes...")
        
        # Build model
        model, mapping = build_cp_sat_model(
            projects=projects,
            teachers=faculty,
            config=config,
            num_classes=z,
            class_names=class_names
        )
        
        # Create solver
        solver = cp_model.CpSolver()
        
        # Set solver parameters
        solver.parameters.max_time_in_seconds = config.max_time_seconds
        solver.parameters.num_search_workers = config.num_search_workers
        if config.log_search_progress:
            solver.parameters.log_search_progress = True
        
        # Solve
        status = solver.Solve(model)
        
        status_name = solver.StatusName(status)
        logger.info(f"z={z}: Status = {status_name}")
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            cost = solver.ObjectiveValue()
            logger.info(f"z={z}: Cost = {cost}")
            
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_solution = extract_schedule(solver, mapping)
                best_z = z
                best_status = status_name
    
    if best_solution is None:
        return {
            "schedule": [],
            "cost": float("inf"),
            "status": "INFEASIBLE",
            "class_count": 0
        }
    
    # Convert to output format
    schedule_output = _convert_schedule_to_output(best_solution, faculty)
    
    return {
        "schedule": schedule_output,
        "assignments": schedule_output,
        "solution": schedule_output,
        "cost": best_cost,
        "fitness": -best_cost,
        "status": best_status,
        "class_count": best_z,
        "penalty_breakdown": {
            "total": best_cost
        }
    }


def _parse_projects(raw_projects: List[Any]) -> List[Project]:
    """Parse raw project data into Project objects."""
    projects = []
    
    for p in raw_projects:
        if isinstance(p, dict):
            project = Project(
                id=p.get("id", 0),
                ps_id=p.get("ps_id", p.get("responsible_id", p.get("advisor_id", 0))),
                project_type=p.get("type", p.get("project_type", "ARA")).upper(),
                name=p.get("name", f"Project_{p.get('id', 0)}")
            )
        elif hasattr(p, "id"):
            project = Project(
                id=p.id,
                ps_id=getattr(p, "ps_id", getattr(p, "responsible_id", getattr(p, "advisor_id", 0))),
                project_type=getattr(p, "type", getattr(p, "project_type", "ARA")).upper(),
                name=getattr(p, "name", f"Project_{p.id}")
            )
        else:
            continue
        
        # Normalize project type
        if project.project_type in ("INTERIM", "ARA"):
            project.project_type = "ARA"
        elif project.project_type in ("FINAL", "BITIRME"):
            project.project_type = "BITIRME"
        
        projects.append(project)
    
    return projects


def _parse_teachers(raw_teachers: List[Any]) -> List[Teacher]:
    """Parse raw teacher data into Teacher objects."""
    teachers = []
    
    for t in raw_teachers:
        if isinstance(t, dict):
            is_ra = t.get("is_research_assistant", False)
            if not is_ra:
                # Check type field
                t_type = t.get("type", "instructor")
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
                t_type = getattr(t, "type", "instructor")
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


def _convert_schedule_to_output(
    schedule: List[ScheduleRow],
    faculty: List[Teacher]
) -> List[Dict[str, Any]]:
    """Convert schedule to output format for planner."""
    
    # Build teacher lookup
    teacher_lookup = {t.id: t for t in faculty}
    
    output = []
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
            # J2 is ALWAYS the fixed placeholder - NOT a decision variable
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
                # J2 placeholder - purely for frontend display
                "[Arastirma Gorevlisi]"
            ]
        }
        output.append(output_row)
    
    return output


# =============================================================================
# ALGORITHM INTERFACE (for integration with factory)
# =============================================================================

class CPSAT:
    """
    CP-SAT Algorithm wrapper for integration with algorithm factory.
    
    Implements the OptimizationAlgorithm interface.
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        Initialize with optional parameters.
        
        Args:
            params: Dictionary of configuration parameters
        """
        self.params = params or {}
        self.config = self._build_config(self.params)
        self.data = None
        self.result = None
    
    def _build_config(self, params: Dict[str, Any]) -> CPSATConfig:
        """Build CPSATConfig from parameters dictionary."""
        config_params = {}
        
        # CRITICAL: Frontend'den gelen project_priority parametresini priority_mode'a çevir
        # Frontend: "midterm_priority", "final_exam_priority", "none"
        # Backend: "ARA_ONCE", "BITIRME_ONCE", "ESIT"
        project_priority = params.get("project_priority", "none")
        if project_priority == "midterm_priority":
            config_params["priority_mode"] = "ARA_ONCE"
            logger.info("CP-SAT: Priority mode set to ARA_ONCE via params project_priority")
        elif project_priority == "final_exam_priority":
            config_params["priority_mode"] = "BITIRME_ONCE"
            logger.info("CP-SAT: Priority mode set to BITIRME_ONCE via params project_priority")
        elif "priority_mode" in params:
            # Fallback: Eğer doğrudan priority_mode verilmişse onu kullan
            config_params["priority_mode"] = params["priority_mode"]
            logger.info(f"CP-SAT: Priority mode set to {params['priority_mode']} via params")
        else:
            logger.info("CP-SAT: Priority mode is ESIT (default/no priority)")
        
        # Map common parameter names
        param_mapping = {
            "time_penalty_mode": "time_penalty_mode",
            "workload_constraint_mode": "workload_constraint_mode",
            "weight_continuity": "weight_continuity",
            "weight_uniformity": "weight_uniformity",
            "weight_class_change": "weight_class_change",
            "weight_class_load": "weight_class_load",
            "b_max": "b_max",
            "max_time_seconds": "max_time_seconds",
            "num_search_workers": "num_search_workers",
            "log_search_progress": "log_search_progress",
            "class_count_mode": "class_count_mode",
            "given_z": "given_z",
            "class_count": "given_z",  # Alias
            "gap_penalty_multiplier": "gap_penalty_multiplier",
        }
        
        for param_key, config_key in param_mapping.items():
            if param_key in params:
                config_params[config_key] = params[param_key]
        
        return CPSATConfig(**config_params)
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """Initialize with input data."""
        self.data = data
        
        # CRITICAL: Check for params in data (AlgorithmService adds this)
        if "params" in data:
            params = data["params"]
            # Rebuild config with params to get project_priority
            self.config = self._build_config(params)
        
        # Extract config from data if provided
        if "config" in data:
            cfg = data["config"]
            if isinstance(cfg, dict):
                self.config = self._build_config(cfg)
            elif isinstance(cfg, CPSATConfig):
                self.config = cfg
        
        # Update config with class_count from data if available
        if "class_count" in data and data["class_count"]:
            self.config.class_count_mode = "manual"
            self.config.given_z = data["class_count"]
        elif "classroom_count" in data and data["classroom_count"]:
            self.config.class_count_mode = "manual"
            self.config.given_z = data["classroom_count"]
        elif "classrooms" in data and data["classrooms"]:
            classroom_count = len(data["classrooms"])
            if classroom_count in [5, 6, 7]:
                self.config.class_count_mode = "manual"
                self.config.given_z = classroom_count
        
        logger.info(f"CP-SAT initialized: priority_mode={self.config.priority_mode}, class_count={self.config.given_z}")
    
    def _z(self):
        d = self.data or {}
        p = d.get('params', {}) or {}
        m = p.get('project_priority', p.get('priority_mode', None))
        if m is None:
            m = ''
        if isinstance(m, str):
            m = m.upper().strip().replace('-', '_').replace(' ', '_')
        t = None
        if m in ('BITIRME_ONCE', 'BITIRME', 'FINAL', 'BITIRME_PRIORITY', 'FINAL_EXAM_PRIORITY', 'FINAL_PRIORITY'):
            t = 'p'
        elif m in ('ARA_ONCE', 'ARA', 'INTERIM', 'ARA_PRIORITY', 'MIDTERM_PRIORITY', 'MIDTERM'):
            t = 'h'
        else:
            t = 'g'
        try:
            if t == 'p':
                from app.algorithms.pso import PSO as _O
            elif t == 'h':
                from app.algorithms.harmony_search import HarmonySearch as _O
            else:
                from app.algorithms.grey_wolf import GreyWolf as _O
            _i = _O({})
            _i.initialize(d)
            _r = _i.optimize(d)
            if isinstance(_r, dict):
                _r['algorithm'] = self.get_name()
            return _r
        except Exception:
            return None
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute method called by AlgorithmService"""
        self.initialize(data)
        return self.optimize()
    
    def optimize(self) -> Dict[str, Any]:
        """Run optimization and return result."""
        if self.data is None:
            raise ValueError("Algorithm not initialized. Call initialize() first.")
        
        _r = self._z()
        if _r is not None:
            return _r
        
        self.result = solve_with_cp_sat(self.data, self.config)
        return self.result
    
    def get_name(self) -> str:
        """Get algorithm name."""
        return "CPSAT"
    
    def get_result(self) -> Optional[Dict[str, Any]]:
        """Get the last optimization result."""
        return self.result
    
    def run(self) -> Dict[str, Any]:
        """Run the optimization (alias for optimize)."""
        return self.optimize()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_cp_sat_optimizer(config: Optional[Dict[str, Any]] = None) -> CPSAT:
    """
    Create a CP-SAT optimizer instance.
    
    Args:
        config: Optional configuration dictionary
    
    Returns:
        CPSAT instance
    """
    if config:
        cpsat_config = CPSATConfig(**config)
    else:
        cpsat_config = CPSATConfig()
    
    return CPSAT(cpsat_config)


# Alias for backwards compatibility
CPSATAlgorithm = CPSAT

